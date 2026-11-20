"""Named, persistent updates driven by real community discoveries, not fake grants."""
from datetime import timedelta

from django.db.models import Min
from django.utils import timezone
from .models import World,WorldRelease,StoryRun,SleeperRace,BarrierEvent
from .barrier import region_ids

RELEASES=(
 ('foundations','1.0','Kroniki dwóch krain','Życie obozów Kolonii i mieszkańców Khorinis. Osobne historie przed Barierą.','old_camp',''),
 ('barrier','2.0','Pęknięcie Bariery','Jeden serwer, wspólne frakcje, rynek i podróże. Dawny dorobek pozostaje.','nk_region_valley',''),
 ('jarkendar','2.1','Zaginiona Dolina','Publiczny Jarkendar: bagna, kanion, kamienni strażnicy i wyprawa przeciw Krukowi. Każda postać nadal zdobywa portal.','jark_swamp','jark-portal'),
 ('night','2.2','Cienie nad Khorinis','Kontrakty NK, Poszukiwacze, kamienne tablice i zagrożenia wspólnych szlaków.','k2_dark_forest','nk-scouts'),
 ('dragons','2.3','Przebudzenie smoków','Cztery smocze wyprawy i dalszy rozwój sześciu frakcji. Obowiązują osobiste przydziały.','g2nk_dragon_fire','nk-eye'),
 ('irdorath','2.4','Żagle ku Irdorath','Przeprawa i finał mieszkańca na Irdorath; każdy zdobywa własne prawo rejsu.','nk_region_irdorath','nk-sailing'),
 ('orc-war','2.5','Orkowie u bram','Po finale świat walczy dalej: orkowe patrole regionalne i co piąty tydzień wspólny orkowy wódz w tygodniowym celu gildii.','g2nk_orcelite_rest','nk-undead'),
)
MILESTONES={r[-1] for r in RELEASES if r[-1]}

# Minimum duration after the preceding public release. The earned discovery
# remains a separate requirement, and opening the Barrier keeps its own rules.
MINIMUM_DAYS = {'jarkendar': 2, 'night': 1, 'dragons': 1, 'irdorath': 2, 'orc-war': 1}
MILESTONE_RELEASE = {row[-1]: row[0] for row in RELEASES if row[-1]}
PREVIOUS_RELEASE = {row[0]: RELEASES[index - 1][0] for index, row in enumerate(RELEASES) if index}


def _joined_event(world_ids):
    return BarrierEvent.objects.filter(race__colony_id__in=world_ids, race__state='joined', kind='joined').first()


def milestone_wait(world, quest_key, now=None):
    """Return waiting seconds, or None when the preceding stage is unannounced."""
    key = MILESTONE_RELEASE.get(quest_key)
    if key is None:
        return 0
    ids = region_ids(world)
    if not _joined_event(ids):
        return 0
    rows = dict(WorldRelease.objects.filter(world_id__in=ids, key__in=[key, PREVIOUS_RELEASE[key]])
                .values_list('key', 'released_at'))
    if key in rows:
        return 0
    previous = rows.get(PREVIOUS_RELEASE[key])
    if previous is None:
        return None
    now = now or timezone.now()
    return max(0, (previous + timedelta(days=MINIMUM_DAYS[key]) - now).total_seconds())


def sync_releases(world,now=None):
    """Called by worker/seeding and successful milestone claims, never by GET."""
    now=now or timezone.now();ids=region_ids(world)
    worlds=list(World.objects.filter(pk__in=ids));canonical=next((w for w in worlds if w.is_current),worlds[0])
    joined=len(ids)>1
    existing = dict(WorldRelease.objects.filter(world=canonical).values_list('key', 'released_at'))
    paced = joined and bool(_joined_event(ids))
    needed=[r[-1] for r in RELEASES if r[-1] and r[0] not in existing]
    milestones=dict(StoryRun.objects.filter(profile__world_id__in=ids,status='claimed',snapshot__key__in=needed).values('snapshot__key').annotate(first=Min('claimed_at')).values_list('snapshot__key','first')) if joined and needed else {}
    race=SleeperRace.objects.filter(colony=canonical,state='joined').values_list('joined_at',flat=True).first() if joined and 'barrier' not in existing else None
    for key,version,title,notes,art,milestone in RELEASES:
        if key in existing or (key!='foundations' and not joined) or (milestone and milestone not in milestones):continue
        if milestone and paced:
            previous = existing.get(PREVIOUS_RELEASE[key])
            if previous is None or now < previous + timedelta(days=MINIMUM_DAYS[key]):
                continue
        stamp=(milestones.get(milestone) if milestone else race if key=='barrier' else canonical.created_at) or now
        if milestone and paced:
            stamp = now
        row, created = WorldRelease.objects.get_or_create(world=canonical,key=key,defaults={'released_at':stamp,'snapshot':{'version':version,'title':title,'notes':notes,'art':art,'milestone':milestone,'source':'community' if milestone else 'barrier' if key=='barrier' else 'foundation'}})
        existing[key] = row.released_at
        if created and key != 'foundations':
            from .barrier import clear_region_cache
            from .market_intelligence import invalidate

            clear_region_cache()
            invalidate(canonical.pk)
    return set(existing)

def release_cards(world):
    ids = region_ids(world)
    canonical = World.objects.filter(pk__in=ids, is_current=True).first()
    rows = {row.key: row for row in WorldRelease.objects.filter(world_id__in=[canonical.pk] if canonical else ids)}
    paced = bool(_joined_event(ids)) if len(ids) > 1 else False
    labels = {
        'jark-portal': 'Pierwszy mieszkaniec otwiera portal',
        'nk-scouts': 'Pierwszy meldunek zwiadowców NK',
        'nk-eye': 'Pierwszy mieszkaniec odbiera Oko Innosa',
        'nk-sailing': 'Pierwsza ukończona przeprawa',
        'nk-undead': 'Pierwszy ukończony finał NK',
    }
    cards = []
    for key, version, title, notes, art, milestone in RELEASES:
        row = rows.get(key)
        snapshot = row.snapshot if row else {}
        previous = rows.get(PREVIOUS_RELEASE.get(key))
        earliest = previous.released_at + timedelta(days=MINIMUM_DAYS[key]) if paced and milestone and previous and not row else None
        cards.append({
            'key': key, 'version': snapshot.get('version', version), 'title': snapshot.get('title', title),
            'notes': snapshot.get('notes', notes), 'art': snapshot.get('art', art),
            'released_at': row.released_at if row else None, 'available': bool(row),
            'bot_arrivals': row.bot_arrivals if row else None, 'earliest': earliest,
            'requirement': labels.get(milestone, 'Upadek Bariery'),
        })
    return cards
