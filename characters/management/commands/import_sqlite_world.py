"""Copy and verify a save into an EMPTY PostgreSQL database, never in place."""
import hashlib,io,json,os,sqlite3,subprocess,sys,tempfile
from collections import Counter
from pathlib import Path
from django.apps import apps
from django.conf import settings
from django.core.management import BaseCommand,CommandError,call_command
from django.core.management.color import no_style
from django.db import connection,transaction
from ore_empire.database import sqlite_environment

EXCLUDES=['contenttypes','auth.permission','sessions.session','characters.schedulerlease']

def canonical(raw, *, legacy_equipment=False, legacy_adventures=False, legacy_bots=False, legacy_characters=False, legacy_realms=False, legacy_origins=False):
    rows=json.loads(raw)
    if legacy_origins:
        for row in rows:
            if row['model']=='characters.playerprofile':row['fields'].pop('origin_world',None)
    if legacy_realms:
        for row in rows:
            if row['model']=='characters.world':row['fields'].pop('is_open',None)
            elif row['model']=='characters.adventuretemplate':row['fields'].pop('universe',None)
    if legacy_equipment:
        for row in rows:
            if row['model']=='characters.owneditem':
                fields=row['fields'];fields['upgrade_level']+=2*fields.pop('rarity',0)
    if legacy_adventures:
        for row in rows:
            fields=row['fields']
            if row['model']=='characters.adventuretemplate':
                for key in ('category','place','success_text'):fields.pop(key,None)
            elif row['model']=='characters.adventurerun':fields.pop('briefing',None)
    if legacy_bots:
        added={'characters.playerprofile':('bot_personality','bot_session_shift'),'characters.world':('bot_personality_cycles','bot_simulated_purchases'),'characters.storepurchase':('kind_snapshot',),'characters.markettrade':('rarity','upgrade_level')}
        for row in rows:
            for field in added.get(row['model'],()):row['fields'].pop(field,None)
    if legacy_characters:
        for row in rows:
            if row['model']=='characters.playerprofile':
                for field in ('slot','name','name_key','is_draft'):row['fields'].pop(field,None)
    rows.sort(key=lambda row:(row['model'],str(row['pk'])))
    return json.dumps(rows,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode(),dict(Counter(row['model'] for row in rows))

def clear_migration_scaffold():
    """A fresh migration creates three empty guilds and a default world; accept only that exact scaffold."""
    from django.contrib.auth.models import User,Group
    from characters.models import World,CampGuild
    models=[*apps.get_app_config('characters').get_models(),User,Group]
    if any(m.objects.exists() for m in models if m not in {World,CampGuild}):raise CommandError('Baza docelowa zawiera dane. Import odmówiony bez nadpisywania.')
    worlds=list(World.objects.all())
    if len(worlds)>1:raise CommandError('Baza docelowa zawiera światy.')
    for world in worlds:
        # Historical migrations create an empty six-bot placeholder. Changing the
        # runtime default must not make that exact empty scaffold unimportable.
        mismatch=any(getattr(world,f.attname)!=f.get_default() for f in World._meta.fields if f.name not in {'id','created_at','is_current','bot_count'})
        if mismatch or world.bot_count not in {6,World._meta.get_field('bot_count').get_default()} or not world.is_current:raise CommandError('Docelowy świat został skonfigurowany; import odmówiony.')
    for guild in CampGuild.objects.all():
        if not worlds or guild.world_id!=worlds[0].pk or guild.camp not in {'OLD_CAMP','NEW_CAMP','SWAMP_CAMP'} or any(getattr(guild,f.attname)!=f.get_default() for f in CampGuild._meta.fields if f.name not in {'id','world','camp'}):raise CommandError('Obozy docelowe zawierają postęp; import odmówiony.')
    CampGuild.objects.all().delete();World.objects.all().delete()

class Command(BaseCommand):
    help='Offline SQLite → empty PostgreSQL import, with full logical data verification.'
    def add_arguments(self,parser):
        parser.add_argument('--source',required=True,type=Path)
        parser.add_argument('--report',required=True,type=Path)
        parser.add_argument('--confirm-empty-target',action='store_true')
    def handle(self,*args,**opts):
        if connection.vendor!='postgresql' or not opts['confirm_empty_target']:raise CommandError('Wymagany pusty PostgreSQL oraz --confirm-empty-target. Zatrzymaj serwer i scheduler bazy docelowej.')
        source=opts['source'].resolve();report=opts['report'].resolve()
        if not source.is_file() or report.exists():raise CommandError('Źródło musi istnieć, a plik raportu musi być nowy.')
        with tempfile.TemporaryDirectory(prefix='ore-private-pg-import-') as tmp:
            snapshot=Path(tmp)/'source.sqlite3';fixture=Path(tmp)/'save.json'
            try:
                with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as src,sqlite3.connect(snapshot) as dst:src.backup(dst)
                snapshot.chmod(0o600)
                source_digest=hashlib.sha256(snapshot.read_bytes()).hexdigest()
                env=sqlite_environment(snapshot)
                migrated=subprocess.run([sys.executable,str(settings.BASE_DIR/'manage.py'),'migrate','--noinput'],env=env,cwd=settings.BASE_DIR,capture_output=True)
                if migrated.returncode:raise CommandError('Nie udało się zmigrować prywatnej kopii SQLite; źródło pozostaje bez zmian.')
                with open(fixture,'xb') as stream:
                    os.chmod(fixture,0o600)
                    result=subprocess.run([sys.executable,str(settings.BASE_DIR/'manage.py'),'dumpdata','--format','precise_json','--all','--natural-foreign',*[arg for item in EXCLUDES for arg in ('--exclude',item)]],env=env,cwd=settings.BASE_DIR,stdout=stream,stderr=subprocess.PIPE)
                if result.returncode:raise CommandError('Eksport prywatnej kopii nie powiódł się; nie zmieniono bazy docelowej.')
                expected,counts=canonical(fixture.read_bytes())
                with transaction.atomic():
                    # Import is an offline operation: protect the empty target from concurrent writes.
                    with connection.cursor() as cursor:
                        tables=[connection.ops.quote_name(m._meta.db_table) for m in apps.get_models()]
                        cursor.execute('LOCK TABLE '+','.join(tables)+' IN SHARE ROW EXCLUSIVE MODE')
                    clear_migration_scaffold()
                    call_command('loaddata',str(fixture),stdout=io.StringIO(),verbosity=0)
                    with connection.cursor() as cursor:
                        for sql in connection.ops.sequence_reset_sql(no_style(),apps.get_models()):cursor.execute(sql)
                    actual=io.StringIO();call_command('dumpdata',format='precise_json',use_base_manager=True,use_natural_foreign_keys=True,exclude=EXCLUDES,stdout=actual)
                    logical,_=canonical(actual.getvalue())
                    if logical!=expected:raise CommandError('Niezgodność danych po imporcie: cofnięto całą transakcję.')
                    connection.check_constraints()
                proof={'schema':1,'engine':'postgresql','verified':True,'source_snapshot_sha256':source_digest,'logical_sha256':hashlib.sha256(expected).hexdigest(),'models':counts,'records':sum(counts.values()),'excluded_ephemeral':['sessions','scheduler leases'],'source_unchanged':True}
                report.parent.mkdir(parents=True,exist_ok=True)
                with open(report,'x',opener=lambda p,f:os.open(p,f,0o600)) as stream:json.dump(proof,stream,ensure_ascii=False,indent=2)
            except CommandError:raise
            except Exception as exc:raise CommandError('Import nie powiódł się; szczegóły połączenia i dane prywatne nie są wypisywane.') from exc
        self.stdout.write('Zweryfikowano pełny zapis w PostgreSQL. Źródłowy SQLite pozostał nienaruszony.')
