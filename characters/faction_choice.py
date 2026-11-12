"""One permanent Brotherhood succession decision, shared by people and bots."""
from .factions import FACTIONS,RANK_NAMES,membership
from .game_logic import player_action
from .models import CampGuild,FactionChoice,FactionMembership

MAGICAL={'FIRE_ORDER','WATER_CIRCLE'}


def choice_for(profile):
    member=membership(profile)
    if not member:return None
    try:return member.choice
    except FactionChoice.DoesNotExist:return None


def allowed_factions(profile):
    if profile.guild in {'GURU','ARCH_GURU'}:return tuple(key for key,_ in FACTIONS if key in MAGICAL)
    return tuple(key for key,_ in FACTIONS)


def card(profile):
    member=membership(profile)
    if not member or member.faction!='PENDING':return None
    from .camp_progression import BY_RANK
    rank=BY_RANK.get(profile.guild)
    busy=profile.is_busy
    active=profile.camp_quests.filter(promoted_at__isnull=True).exists()
    return {'can_choose':not (busy or active),'busy':busy,'active_quest':active,
            'options':[{'key':key,'name':name,'rank':RANK_NAMES[key][rank.tier] if rank else 'Bez rangi'} for key,name in FACTIONS if key in allowed_factions(profile)]}


@player_action
def choose(profile,destination):
    from .barrier import joined
    if type(destination) is not str or destination not in dict(FACTIONS) or not joined(profile.world_id):return False
    member=FactionMembership.objects.select_for_update().filter(profile=profile).select_related('succession__race').first()
    if not member or profile.camp!='SWAMP_CAMP':return False
    prior=FactionChoice.objects.filter(membership=member).first()
    if prior:return prior.destination==destination
    if member.faction!='PENDING' or destination not in allowed_factions(profile) or profile.is_busy:return False
    if profile.camp_quests.filter(promoted_at__isnull=True).exists():return False
    race=member.succession.race
    target=CampGuild.objects.get(world_id=race.khorinis_id if destination in {'CITY_WATCH','FIRE_ORDER'} else race.colony_id,camp=destination)
    # The escrow row serializes choices by different characters. Lock order is
    # also shared with upgrades/donations, and player_action handles deadlocks.
    locked={g.pk:g for g in CampGuild.objects.select_for_update().filter(pk__in=[member.guild_id,target.pk]).order_by('pk')}
    source=locked[member.guild_id];target=locked[target.pk]
    pending=list(FactionMembership.objects.filter(succession=member.succession,faction='PENDING').order_by('profile_id').values_list('profile_id',flat=True))
    # Equal per-member weights, deterministic integer remainder; recalculated
    # against remaining escrow, including actual contributions since the join.
    position=pending.index(profile.pk);size=len(pending)
    ore=source.treasury//size+int(position<source.treasury%size)
    xp=source.experience//size+int(position<source.experience%size)
    source.treasury-=ore;source.experience-=xp
    target.treasury+=ore;target.experience+=xp
    target.level=max(target.level,source.level,min(10,1+target.experience//100))
    for field in ('training_level','supply_level','defense_level'):setattr(target,field,max(getattr(target,field),getattr(source,field)))
    source.save(update_fields=['treasury','experience'])
    target.save(update_fields=['treasury','experience','level','training_level','supply_level','defense_level'])
    event=FactionChoice.objects.create(membership=member,destination=destination,original_rank=profile.guild,source_guild=source,target_guild=target,ore=ore,experience=xp)
    member.faction=destination;member.guild=target;member.save(update_fields=['faction','guild'])
    member.choice=event;profile.faction_membership=member
    profile.__dict__.pop('_camp_perks',None)
    return True


def promotion_allowed(profile,rank):
    choice=choice_for(profile)
    if not choice:return True
    return rank.key not in ({'SWAMP_GUARD','TEMPLAR'} if choice.destination in MAGICAL else {'GURU','ARCH_GURU'})


def promotion_parents(profile,rank):
    choice=choice_for(profile)
    if choice and choice.destination in MAGICAL and rank.key=='ARCH_GURU' and profile.guild=='SWAMP_GUARD':return ('SWAMP_GUARD',)
    return None


def equipment_camps(profile):
    member=membership(profile)
    return {'',profile.camp}|({'CITY_WATCH':{'CITY_WATCH'},'FIRE_ORDER':{'OLD_CAMP','FIRE_ORDER'},'WATER_CIRCLE':{'NEW_CAMP'},'BANDITS':{'OLD_CAMP'},'MERCENARIES':{'NEW_CAMP','ONAR_MERCS'}}.get(member.faction,set()) if member else set())


def equipment_camp_allowed(profile,camp):return not camp or camp in equipment_camps(profile)
