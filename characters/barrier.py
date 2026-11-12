"""Region identities survive the Barrier; only access and social scopes change."""
from django.db.models import Q
from .models import World


def region_ids(world):
    from .realms import _union_cache
    pk=getattr(world,'pk',world);cache=_union_cache.get()
    if cache is not None and pk in cache:return cache[pk]
    union=World.objects.filter(pk=pk).values_list('union_key',flat=True).first()
    ids=list(World.objects.filter(union_key=union).values_list('pk',flat=True)) if union else [pk]
    if cache is not None:
        for key in ids:cache[key]=ids
    return ids


def joined(world):return len(region_ids(world))>1


def source_games(profile):return ['adaptation','GOTHIC_I','GOTHIC_II'] if joined(profile.world_id) else ['adaptation',profile.world.universe]


def region(profile):return profile.visiting_world if profile.visiting_world_id else profile.world


def creation_worlds():
    from .realms import open_worlds
    return open_worlds().filter(Q(union_key__isnull=True)|Q(is_current=True))


def same_world(a,b):return getattr(b,'pk',b) in region_ids(a)


from .game_logic import player_action
@player_action
def travel(profile,destination):
    if profile.is_busy or not joined(profile.world_id) or destination not in region_ids(profile.world_id):return False
    profile.visiting_world_id=destination;profile.save(update_fields=['visiting_world'])
    return True


def guild_identity(profile):
    from .factions import membership
    member=membership(profile)
    if member is None and joined(profile.world_id):
        # A long-lived actor may predate the global transaction. Reads of the
        # social guild must resolve its newly created membership as well.
        from .models import FactionMembership
        member=FactionMembership.objects.filter(profile_id=profile.pk).first()
        if member:profile.faction_membership=member
    if member:return {'pk':member.guild_id}
    if profile.camp in {'NEW_CAMP','ONAR_MERCS'} and joined(profile.world_id):
        colony=World.objects.get(pk__in=region_ids(profile.world_id),universe='GOTHIC_I')
        return {'world_id':colony.pk,'camp':'NEW_CAMP'}
    return {'world_id':profile.world_id,'camp':profile.camp}


def guild_for(profile,lock=False):
    from .models import CampGuild
    rows=CampGuild.objects.select_for_update() if lock else CampGuild.objects
    return rows.filter(**guild_identity(profile)).first()


def raid_guild_ids(profile):
    from .factions import membership
    member=membership(profile)
    if member:return {member.guild_id}
    from .models import CampGuild
    own=CampGuild.objects.filter(world_id=profile.world_id,camp=profile.camp).values_list('pk',flat=True).first()
    shared=guild_for(profile)
    return {pk for pk in (own,shared.pk if shared else None) if pk}


def alliance_card(profile):
    member=profile.camp in {'NEW_CAMP','ONAR_MERCS'} and joined(profile.world_id)
    from .factions import membership
    current=membership(profile)
    if current:member=False  # New members use the four earned faction advances.
    tier=profile.camp_tier;next_tier=tier+1
    quest='barrier-fire-dragon' if next_tier==4 else 'barrier-new-road'
    fee=500*max(1,next_tier-2);level=20+5*next_tier
    ready=member and 2<=tier<4 and profile.level>=level and profile.ore_balance>=fee and profile.story_runs.filter(status='claimed',quest__key=quest).exists() and not profile.is_busy
    names=('Robotnik wspólnoty','Zbrojny','Najemnik','Weteran szlaków','Dowódca Związku')
    return {'member':member,'rank':names[min(4,tier)],'can_promote':ready,'fee':fee,'level':level,'next_tier':next_tier,'quest':quest}


@player_action
def promote_alliance(profile,expected_rank):
    if type(expected_rank)is not int or profile.camp_tier!=expected_rank:return False
    card=alliance_card(profile)
    if not card['can_promote']:return False
    profile.ore_balance-=card['fee'];profile.alliance_rank=card['next_tier'];profile.save(update_fields=['ore_balance','alliance_rank'])
    return True
