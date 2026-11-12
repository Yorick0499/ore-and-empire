"""Four earned ranks per joined faction, using the existing promotion ledger."""
from django.utils import timezone
from .camp_progression import Rank,obj,quest_complete
from .factions import FACTIONS,RANK_NAMES,membership
from .models import CampQuest,FactionRankProgress


def build_ranks():
    result=[]
    goals=(
        (obj('mine',3,'Odbierz trzy zmiany dla nowej wspólnoty'),obj('hunt:orc_scout',5,'Pokonaj orkowych zwiadowców w Górniczej Dolinie')),
        (obj('hunt:orc_veteran',5,'Pokonaj orkowych wiarusów'),obj('boss:k2_dragon_fire',1,'Pokonaj smoka ognia na wspólnym szlaku')),
        (obj('hunt:demon',6,'Pokonaj pomniejsze demony'),obj('boss:k2_dragon_fire',1,'Ponownie zabezpiecz szlak przed smokiem ognia')),
        (obj('hunt:temple_guardian',8,'Pokonaj opiekunów świątyni'),obj('boss:k2_dragon_fire',2,'Dwukrotnie zwycięż smoka ognia'),obj('mine',10,'Zabezpiecz dziesięć zmian wydobycia')),
    )
    for faction,label in FACTIONS:
        magic=faction in {'FIRE_ORDER','WATER_CIRCLE'}
        for n,tier in enumerate(range(4,8)):
            key=f'ADV_{faction}_{tier}'
            result.append(Rank(key,RANK_NAMES[faction][tier],faction,(f'ADV_{faction}_{tier-1}',) if tier>4 else ('BASE_4',),tier,30+5*n,'mana' if magic else 'martial',(50 if magic else 70)+20*n,(500,1000,1500,2500)[n],f'Służba wspólnoty: {RANK_NAMES[faction][tier]}',f'{label}: zdobądź zaufanie pracą i rzeczywistymi zwycięstwami. To służba mieszkańca wspólnego świata, nie rola Bezimiennego.',goals[n]))
    return tuple(result)


RANKS=build_ranks()
BY_KEY={r.key:r for r in RANKS}


def advanced_tier(profile):
    member=membership(profile)
    if not member or member.faction not in dict(FACTIONS):return None
    try:return member.rank_progress.tier
    except FactionRankProgress.DoesNotExist:
        # Old tier4 was a paid fifth rank, earned at level40 after a dragon.
        # Relabel that achievement; the Barrier never grants it to a new actor.
        if profile.camp in {'NEW_CAMP','ONAR_MERCS'} and profile.alliance_rank>=4:return 4
        return None


def current_tier(profile):
    advanced=advanced_tier(profile)
    if advanced is not None:return advanced
    from .camp_progression import BY_RANK
    native=BY_RANK.get(profile.guild)
    tier=native.tier if native and native.camp==profile.camp else -1
    if membership(profile) and profile.camp in {'NEW_CAMP','ONAR_MERCS'} and profile.alliance_rank==3:tier=max(tier,3)
    return tier


def eligible(profile,rank):
    from .barrier import joined
    member=membership(profile)
    return bool(member and member.faction==rank.camp and joined(profile.world_id) and current_tier(profile)==rank.tier-1)


def accept_locked(profile,key):
    """Only called inside the existing accept_camp_quest player action."""
    rank=BY_KEY[key]
    if profile.is_busy or not eligible(profile,rank) or profile.camp_quests.filter(promoted_at__isnull=True).exists():return False
    CampQuest.objects.create(profile=profile,rank_key=key)
    return True


def promote_locked(profile,key):
    """Only called inside promote_in_camp; one wallet ledger and one debit."""
    rank=BY_KEY[key]
    if profile.is_busy or not eligible(profile,rank):return False
    quest=CampQuest.objects.select_for_update().filter(profile=profile,rank_key=key,promoted_at__isnull=True).first()
    if not quest or not quest_complete(quest,rank) or profile.level<rank.level or getattr(profile,rank.attribute)<rank.attribute_value or profile.ore_balance<rank.cost:return False
    member=membership(profile)
    state,_=FactionRankProgress.objects.update_or_create(membership=member,defaults={'tier':rank.tier})
    member.rank_progress=state
    profile.ore_balance-=rank.cost;profile.save(update_fields=['ore_balance'])
    quest.promoted_at=timezone.now();quest.save(update_fields=['promoted_at'])
    profile.__dict__.pop('_camp_perks',None)
    return True


def cards(profile):
    member=membership(profile)
    if not member or member.faction not in dict(FACTIONS):return []
    quests={q.rank_key:q for q in profile.camp_quests.all()}
    active=any(q.promoted_at is None for q in quests.values())
    result=[]
    for rank in RANKS:
        if rank.camp!=member.faction:continue
        quest=quests.get(rank.key);ready=bool(quest and quest_complete(quest,rank));allowed=eligible(profile,rank)
        result.append({'rank':rank,'ordinal':rank.tier+1,'quest':quest,'current':current_tier(profile)==rank.tier,
            'legacy':bool(rank.tier==4 and profile.alliance_rank>=4 and not quest),
            'can_accept':allowed and not active and not profile.is_busy,'can_promote':allowed and ready and not profile.is_busy and profile.level>=rank.level and profile.ore_balance>=rank.cost and getattr(profile,rank.attribute)>=rank.attribute_value,
            'attribute_name':'Mana' if rank.attribute=='mana' else 'Siła lub Zręczność','attribute_current':getattr(profile,rank.attribute),
            'goals':[{'label':g.label,'count':g.count,'progress':quest.progress.get(g.event,0) if quest else 0} for g in rank.objectives]})
    result.sort(key=lambda card:0 if card['quest'] and card['quest'].promoted_at is None else 1 if card['can_accept'] else 2 if card['current'] else 3)
    return result
