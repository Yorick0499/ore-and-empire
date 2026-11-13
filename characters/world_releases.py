"""Named, persistent updates driven by real community discoveries, not fake grants."""
from django.db.models import Min
from django.utils import timezone
from .models import World,WorldRelease,StoryRun,SleeperRace
from .barrier import region_ids

RELEASES=(
 ('foundations','1.0','Kroniki dwóch krain','Życie obozów Kolonii i mieszkańców Khorinis. Osobne historie przed Barierą.','old_camp',''),
 ('barrier','2.0','Pęknięcie Bariery','Jeden serwer, wspólne frakcje, rynek i podróże. Dawny dorobek pozostaje.','nk_region_valley',''),
 ('jarkendar','2.1','Zaginiona Dolina','Publiczny Jarkendar: bagna, kanion, kamienni strażnicy i wyprawa przeciw Krukowi. Każda postać nadal zdobywa portal.','jark_swamp','jark-portal'),
 ('night','2.2','Cienie nad Khorinis','Kontrakty NK, Poszukiwacze, kamienne tablice i zagrożenia wspólnych szlaków.','k2_dark_forest','nk-scouts'),
 ('dragons','2.3','Przebudzenie smoków','Cztery smocze wyprawy i dalszy rozwój pięciu frakcji. Obowiązują osobiste przydziały.','g2nk_dragon_fire','nk-eye'),
 ('irdorath','2.4','Żagle ku Irdorath','Przeprawa i finał mieszkańca na Irdorath; każdy zdobywa własne prawo rejsu.','nk_region_irdorath','nk-sailing'),
 ('orc-war','2.5','Orkowie u bram','Po finale świat walczy dalej: orkowe patrole regionalne i co piąty tydzień wspólny orkowy wódz w tygodniowym celu gildii.','g2nk_orcelite_rest','nk-undead'),
)
MILESTONES={r[-1] for r in RELEASES if r[-1]}

def sync_releases(world,now=None):
    """Called by worker/seeding and successful milestone claims, never by GET."""
    now=now or timezone.now();ids=region_ids(world)
    worlds=list(World.objects.filter(pk__in=ids));canonical=next((w for w in worlds if w.is_current),worlds[0])
    joined=len(ids)>1
    existing=set(WorldRelease.objects.filter(world=canonical).values_list('key',flat=True))
    needed=[r[-1] for r in RELEASES if r[-1] and r[0] not in existing]
    milestones=dict(StoryRun.objects.filter(profile__world_id__in=ids,status='claimed',snapshot__key__in=needed).values('snapshot__key').annotate(first=Min('claimed_at')).values_list('snapshot__key','first')) if joined and needed else {}
    race=SleeperRace.objects.filter(colony=canonical,state='joined').values_list('joined_at',flat=True).first() if joined and 'barrier' not in existing else None
    for key,version,title,notes,art,milestone in RELEASES:
        if key in existing or (key!='foundations' and not joined) or (milestone and milestone not in milestones):continue
        stamp=(milestones.get(milestone) if milestone else race if key=='barrier' else canonical.created_at) or now
        WorldRelease.objects.get_or_create(world=canonical,key=key,defaults={'released_at':stamp,'snapshot':{'version':version,'title':title,'notes':notes,'art':art,'milestone':milestone,'source':'community' if milestone else 'barrier' if key=='barrier' else 'foundation'}})
    return set(WorldRelease.objects.filter(world=canonical).values_list('key',flat=True))

def release_cards(world):
    ids=region_ids(world)
    canonical=World.objects.filter(pk__in=ids,is_current=True).first()
    rows={r.key:r for r in WorldRelease.objects.filter(world_id__in=[canonical.pk] if canonical else ids).order_by('released_at','pk')}
    return [{'key':key,'version':row.snapshot.get('version',version) if (row:=rows.get(key)) else version,'title':row.snapshot.get('title',title) if row else title,'notes':row.snapshot.get('notes',notes) if row else notes,'art':row.snapshot.get('art',art) if row else art,'released_at':row.released_at if row else None,'available':bool(row),'requirement':'Upadek Bariery' if not milestone else {'jark-portal':'Pierwszy mieszkaniec otwiera portal','nk-scouts':'Pierwszy meldunek zwiadowców NK','nk-eye':'Pierwszy mieszkaniec odbiera Oko Innosa','nk-sailing':'Pierwsza ukończona przeprawa','nk-undead':'Pierwszy ukończony finał NK'}.get(milestone,'Rozwój świata')} for key,version,title,notes,art,milestone in RELEASES]
