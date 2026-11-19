"""Native PostgreSQL snapshots with a matching logical proof and isolated restore."""
import hashlib,io,json,os,re,shutil,subprocess,sys,tempfile
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
from django.conf import settings
from django.core.management import call_command
from django.db import connection,transaction
from .management.commands.import_sqlite_world import canonical,EXCLUDES
from .backups import sha, backups, restore_migrate, SUCCESSION_BASELINE, SUCCESSION_UPGRADE

def pg_env(config,database=None):
    env={**os.environ,'ORE_DATABASE_ENGINE':'postgresql','PGDATABASE':database or config['NAME'],'PGHOST':str(config.get('HOST','')),'PGPORT':str(config.get('PORT') or 5432),'PGUSER':config.get('USER',''),'PGPASSWORD':config.get('PASSWORD','')}
    env['DATABASE_URL']=''  # Do not let .env redirect a restore subprocess to the live URL.
    if config.get('OPTIONS',{}).get('sslmode'):env['PGSSLMODE']=config['OPTIONS']['sslmode']
    return env

def tool(name):
    folder=os.environ.get('PG_TOOLS_DIRECTORY')
    path=str(Path(folder)/name) if folder else shutil.which(name)
    if not path or not Path(path).is_file():raise ValueError('Zainstaluj klienta PostgreSQL zgodnego z wersją serwera.')
    return path

def logical_dump():
    out=io.StringIO();call_command('dumpdata',format='precise_json',use_base_manager=True,use_natural_foreign_keys=True,exclude=EXCLUDES,stdout=out)
    return canonical(out.getvalue())

def historical_release_dump():
    from django.db.migrations.executor import MigrationExecutor
    from .migration_testing import historical_fixture
    state = MigrationExecutor(connection).loader.project_state([SUCCESSION_BASELINE])
    return historical_fixture(state.apps, EXCLUDES)


def restored_dump(env, *, historical=False):
    if historical:
        command = ['shell', '--verbosity', '0', '-c',
                   'from characters.postgres_backups import historical_release_dump\nprint(historical_release_dump())']
    else:
        command = ['dumpdata', '--format', 'precise_json', '--all', '--natural-foreign',
                   *[arg for model in EXCLUDES for arg in ('--exclude', model)]]
    result = subprocess.run([sys.executable, str(settings.BASE_DIR/'manage.py'), *command],
                            cwd=settings.BASE_DIR, env=env, capture_output=True, timeout=300)
    if result.returncode:
        raise ValueError('Nie udało się zweryfikować osobnej kopii.')
    return result.stdout


def verify_manifest(raw, manifest, *, legacy_bot_arrivals=False):
    logical, counts = canonical(
        raw, legacy_equipment=manifest.get('inventory_schema', 1) == 1,
        legacy_adventures=not manifest.get('adventure_schema'), legacy_bots=not manifest.get('bot_schema'),
        legacy_characters=not manifest.get('character_schema'), legacy_realms=not manifest.get('realm_schema'),
        legacy_origins=not manifest.get('origin_schema'), legacy_barrier=not manifest.get('barrier_schema'),
        legacy_rank_paths=not manifest.get('rank_path_schema'), legacy_bot_arrivals=legacy_bot_arrivals,
    )
    if hashlib.sha256(logical).hexdigest() != manifest['logical_sha256'] or counts != manifest['models']:
        raise ValueError('Odtworzony zapis różni się od snapshotu.')
    return counts


def create_pg_backup(root,keep=7):
    if connection.vendor!='postgresql' or not 1<=keep<=365:raise ValueError('Wymagany PostgreSQL i retencja 1..365.')
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=True,mode=0o700);root.chmod(0o700)
    staging=Path(tempfile.mkdtemp(prefix='.partial-',dir=root));dump=staging/'world.pgdump'
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
                cursor.execute('SELECT pg_export_snapshot()');snapshot=cursor.fetchone()[0]
            logical,counts=logical_dump()
            result=subprocess.run([tool('pg_dump'),'--format=custom','--no-owner','--no-acl','--snapshot='+snapshot,'--file='+str(dump)],env=pg_env(settings.DATABASES['default']),capture_output=True,timeout=300)
            if result.returncode:raise ValueError('pg_dump nie powiódł się; nie opublikowano częściowej kopii.')
        dump.chmod(0o600)
        revision=subprocess.run(['git','rev-parse','HEAD'],cwd=settings.BASE_DIR,capture_output=True,text=True).stdout.strip()
        manifest={'schema':1,'inventory_schema':2,'adventure_schema':1,'bot_schema':1,'character_schema':1,'realm_schema':1,'origin_schema':1,'barrier_schema':1,'rank_path_schema':1,'engine':'postgresql','created_at':datetime.now(timezone.utc).isoformat(),'code_revision':revision,'database_sha256':sha(dump),'logical_sha256':hashlib.sha256(logical).hexdigest(),'models':counts,'excluded_ephemeral':EXCLUDES}
        manifest_path=staging/'manifest.json';manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2));manifest_path.chmod(0o600)
        dest=root/('world-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid4().hex[:8]);staging.rename(dest)
        for old in backups(root)[keep:]:shutil.rmtree(old)
        return dest
    except BaseException:
        if staging.exists():shutil.rmtree(staging)
        raise

def restore_pg_drill(backup,target):
    import psycopg
    from psycopg import sql
    config=settings.DATABASES['default'];backup=Path(backup).resolve()
    if connection.vendor!='postgresql' or not re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,62}',target) or target==config['NAME']:raise ValueError('Wymagana nowa, osobna nazwa bazy PostgreSQL.')
    manifest=json.loads((backup/'manifest.json').read_bytes());dump=backup/'world.pgdump'
    if manifest.get('engine')!='postgresql' or manifest.get('schema')!=1 or sha(dump)!=manifest['database_sha256']:raise ValueError('Niepoprawna lub uszkodzona kopia PostgreSQL.')
    kwargs={'dbname':config['NAME'],'user':config.get('USER'),'password':config.get('PASSWORD'),'host':config.get('HOST'),'port':config.get('PORT') or 5432,'connect_timeout':5}
    if config.get('OPTIONS',{}).get('sslmode'):kwargs['sslmode']=config['OPTIONS']['sslmode']
    created=False
    with psycopg.connect(**kwargs,autocommit=True) as admin:
        try:
            admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(target)));created=True
            env=pg_env(config,target)
            result=subprocess.run([tool('pg_restore'),'--exit-on-error','--single-transaction','--no-owner','--no-acl','--dbname='+target,str(dump)],env=env,capture_output=True,timeout=300)
            if result.returncode:raise ValueError('Odtworzenie nie powiodło się; żywa baza jest nienaruszona.')
            with psycopg.connect(**{**kwargs,'dbname':target},autocommit=True) as restored:
                applied = set(restored.execute('SELECT app, name FROM django_migrations WHERE app = %s',
                                               [SUCCESSION_UPGRADE[0]]).fetchall())
            legacy = SUCCESSION_UPGRADE not in applied
            if legacy:
                restore_migrate(env, settings.BASE_DIR, *SUCCESSION_BASELINE)
                baseline = restored_dump(env, historical=True)
                counts = verify_manifest(baseline, manifest, legacy_bot_arrivals=SUCCESSION_BASELINE not in applied)
            restore_migrate(env, settings.BASE_DIR)
            with psycopg.connect(**{**kwargs,'dbname':target},autocommit=True) as restored:
                restored.execute('DELETE FROM django_session')
                restored.execute('UPDATE characters_schedulerlease SET owner=NULL,expires_at=CURRENT_TIMESTAMP')
            facts = restored_dump(env, historical=legacy)
            if legacy:
                if canonical(facts, compare_reform=True) != canonical(baseline, compare_reform=True):
                    raise ValueError('Odtworzony zapis różni się po sukcesji.')
            else:
                counts = verify_manifest(facts, manifest)
            proof={'schema':1,'verified_at':datetime.now(timezone.utc).isoformat(),'engine':'postgresql','tables':len(counts),'database_sha256':sha(dump),'migration_applied':True,'target':target}
            tmp=backup/'.verification.tmp';tmp.write_text(json.dumps(proof,indent=2));tmp.chmod(0o600);tmp.replace(backup/'verification.json')
            return proof
        except BaseException:
            if created:admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(target)))
            raise
