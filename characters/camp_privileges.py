"""Personal earned ranks unlock responsibilities and modest daily support."""
from uuid import UUID,uuid4
from django.utils import timezone
from .world_clock import polish_day
from .game_logic import player_action

def privileges(profile):
    tier=profile.camp_tier
    return {'tier':tier,'training':min(2,(tier+1)//2),'supply':tier,'defense':tier//2,
            'upgrade_limit':min(3,tier),'can_rally':tier>=1,'can_resupply':tier>=2,
            'energy':10+5*tier,'health':20+5*tier}

@player_action
def claim_resupply(profile,request_key):
    from .models import CampSupplyUse,EnergyRefill
    from .economic_ledger import refills_remaining
    try:key=UUID(str(request_key))
    except (TypeError,ValueError,AttributeError):return False
    perks=privileges(profile);day=polish_day()
    if not perks['can_resupply'] or profile.is_busy:return False
    previous=CampSupplyUse.objects.filter(profile=profile,request_key=key).first()
    if previous:return previous
    if CampSupplyUse.objects.filter(profile=profile,day=day).exists():return False
    energy=min(perks['energy'],profile.max_energy-profile.current_energy) if refills_remaining(profile) else 0
    health=min(perks['health'],profile.max_health-profile.current_health)
    if profile.ore_balance<10 or not (energy or health):return False
    profile.ore_balance-=10;profile.current_energy+=energy;profile.current_health+=health
    now=timezone.now()
    if energy:
        profile.energy_updated_at=now
    if health:profile.health_updated_at=now
    profile.save()
    entry=CampSupplyUse.objects.create(profile=profile,day=day,request_key=key,energy=energy,health=health)
    if energy:EnergyRefill.objects.create(profile=profile,created_at=now,reference='camp:'+str(entry.pk))
    return entry


def resupply_available(profile):
    from .models import CampSupplyUse
    from .economic_ledger import refills_remaining
    return (privileges(profile)['can_resupply'] and profile.ore_balance>=10
        and not profile.is_busy and (profile.current_health<profile.max_health or (profile.current_energy<profile.max_energy and refills_remaining(profile)))
        and not CampSupplyUse.objects.filter(profile=profile,day=polish_day()).exists())
