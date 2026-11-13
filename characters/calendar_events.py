"""Stable calendar identities and conservative upgrades of generated event text."""
from datetime import datetime, timedelta, timezone as utc
import hashlib
import re
from .event_narratives import STAGES, global_text
from .world_clock import POLISH_TIME

ANNUAL = {
    'miners': ('Święto Kopaczy', 'seasonal', (10, 25), (11, 8), 125, 110, 1),
    'winter': ('Zimowe ogniska kolonii', 'holiday', (12, 20), (1, 6), 110, 125, 1),
    'spring': ('Przebudzenie lasu', 'seasonal', (3, 20), (3, 28), 100, 130, 1),
    'harvest': ('Święto Plonów', 'holiday', (9, 22), (9, 29), 120, 115, 0),
    'solstice': ('Noc Tysiąca Ognisk', 'holiday', (6, 20), (6, 25), 110, 120, 0),
    'balance': ('Dni Równowagi', 'holiday', (3, 20), (3, 23), 115, 120, 0),
}
OLD_MONTHLY = (
    'Szlaki pod szronem', 'Warty przy zimowych ogniskach', 'Roztopy na trakcie',
    'Wiosenne zbiory ziół', 'Przeprawy przez wezbrane strumienie', 'Letnie karawany',
    'Długie patrole lata', 'Zbiory na polach ryżowych', 'Jesienne transporty rudy',
    'Zapasy przed chłodem', 'Mgły nad doliną', 'Pierwsze zimowe warty',
)
OLD_ANNUAL_DESCRIPTION = 'Premie do nagród za polowania, wydobycie i wyprawy. Odłamki bonusowe dotyczą wypraw czasowych.'
OLD_MONTHLY_DESCRIPTION = 'Sezonowe prace mieszkańców. Premie nie sumują się: obowiązuje najwyższa dla danego zasobu. Wszystkie szlaki pozostają dostępne.'
OLD_RANDOM_DESCRIPTION = 'Kopacze odkryli bogate złoże. Przez cztery godziny nagrody w rudzie są większe.'


def prefix(world_id):
    return '' if world_id == 1 else f'world-{world_id}-'


def annual_spec(world_id, key, year):
    name, kind, start, end, ore, xp, shards = ANNUAL[key]
    return dict(key=prefix(world_id)+f'{key}-{year}', world_id=world_id,
                starts_at=datetime(year, *start, tzinfo=POLISH_TIME),
                ends_at=datetime(year+(key=='winter'), *end, tzinfo=POLISH_TIME),
                kind=kind, ore_percent=ore, experience_percent=xp, premium_bonus=shards,
                category='annual', index=key, old=(name, OLD_ANNUAL_DESCRIPTION))


def monthly_spec(world_id, year, month):
    return dict(key=prefix(world_id)+f'season-window-{year}-{month}', world_id=world_id,
                starts_at=datetime(year, month, 5, tzinfo=POLISH_TIME),
                ends_at=datetime(year, month, 9, tzinfo=POLISH_TIME), kind='seasonal',
                ore_percent=115 if month%2 else 110, experience_percent=110 if month%2 else 115,
                premium_bonus=0, category='monthly', index=month,
                old=(OLD_MONTHLY[month-1], OLD_MONTHLY_DESCRIPTION))


def random_spec(world_id, day):
    draw = int(hashlib.sha256(('ore-empire-events-v1:'+day.isoformat()).encode()).hexdigest()[:8], 16)
    if draw%4:
        return None
    start=datetime(day.year, day.month, day.day, draw%20, tzinfo=POLISH_TIME)
    return dict(key=prefix(world_id)+'random-'+day.isoformat(), world_id=world_id,
                starts_at=start, ends_at=start.astimezone(utc.utc)+timedelta(hours=4), kind='random',
                ore_percent=150, experience_percent=100, premium_bonus=0,
                category='random', index=(draw//4)%3,
                old=('Szczęśliwa żyła rudy', OLD_RANDOM_DESCRIPTION))


def specs(world_id, now):
    rows=[annual_spec(world_id,key,year) for year in (now.year-1,now.year,now.year+1) for key in ANNUAL]
    rows += [monthly_spec(world_id,year,month) for year in (now.year-1,now.year,now.year+1) for month in range(1,13)]
    if random := random_spec(world_id,now.date()):
        rows.append(random)
    return rows


def spec_for(event):
    key=event.key.removeprefix(prefix(event.world_id))
    if match := re.fullmatch(r'(miners|winter|spring|harvest|solstice|balance)-(\d{4})',key):
        year=int(match[2])
        return annual_spec(event.world_id,match[1],year) if 1<=year<9999 else None
    if match := re.fullmatch(r'season-window-(\d{4})-(\d{1,2})',key):
        year,month=map(int,match.groups())
        return monthly_spec(event.world_id,year,month) if 1<=year<=9999 and 1<=month<=12 else None
    if key.startswith('random-'):
        try:
            return random_spec(event.world_id,datetime.strptime(key[7:],'%Y-%m-%d').date())
        except ValueError:
            return None
    return None


def managed(event, spec=None):
    """A familiar key alone never makes an operator's event an automatic one."""
    spec=spec or spec_for(event)
    if not spec or event.region or event.activity or event.targets or event.art_key or event.rule_version!=1:
        return False
    if any(getattr(event,key)!=value for key,value in spec.items() if key not in {'key','category','index','old'}):
        return False
    pairs={spec['old'], *(global_text(stage,spec['category'],spec['index']) for stage in STAGES)}
    return (event.name,event.description) in pairs


def seed_calendar(world, stage, now):
    from .models import WorldEvent
    rows=specs(world.pk,now)
    existing={e.key:e for e in WorldEvent.objects.select_for_update().filter(key__in=[s['key'] for s in rows]).order_by('pk')}
    additions=[];updates=[]
    for spec in rows:
        name,description=global_text(stage,spec['category'],spec['index'])
        release='foundations' if stage.key in {'colony','island'} else stage.key
        values={key:value for key,value in spec.items() if key not in {'category','index','old'}}
        event=existing.get(spec['key'])
        if event is None:
            additions.append(WorldEvent(**values,name=name,description=description,release_key=release))
        elif event.enabled and event.ends_at>now and managed(event,spec) and (event.name,event.description,event.release_key)!=(name,description,release):
            event.name=name;event.description=description;event.release_key=release;updates.append(event)
    WorldEvent.objects.bulk_create(additions,ignore_conflicts=True)
    if updates:
        WorldEvent.objects.bulk_update(updates,['name','description','release_key'])


def retire_joined_duplicates(world, ids, now):
    """Keep historical rows/receipts and manual events; retire only default copies."""
    from .models import WorldEvent
    rows=WorldEvent.objects.select_for_update().filter(world_id__in=ids,enabled=True,region='',ends_at__gt=now).exclude(world=world).order_by('pk')
    keys=[event.pk for event in rows if managed(event)]
    if keys:
        WorldEvent.objects.filter(pk__in=keys).update(enabled=False)
