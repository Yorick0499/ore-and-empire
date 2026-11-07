"""Derived equipment statistics never overwrite base attributes."""
from .models import OwnedItem

BONUSES = ('weapon_prot','arrow_prot','fire_prot','magic_prot','strength_bonus','dexterity_bonus','mana_bonus','life_bonus')


def stats_for(profile):
    totals = dict.fromkeys(BONUSES, 0)
    for item in profile.inventory.filter(is_equipped=True).select_related('blueprint'):
        effective = item.effective_stats
        for key in totals:
            totals[key] += effective[key]
    return totals


def allowed(profile, blueprint):
    return (profile.level >= blueprint.min_level and
            (not blueprint.required_camp or profile.camp == blueprint.required_camp) and
            profile.camp_tier >= blueprint.min_camp_tier)


def sync_health(profile):
    if hasattr(profile, '_gear_stats_cache'): del profile._gear_stats_cache
    profile.equipment_health = profile.equipment_stats['life_bonus']
    profile.equipment_mana = profile.equipment_stats['mana_bonus']
    profile.current_mana = min(profile.current_mana,profile.max_mana)
    profile.current_health = min(profile.current_health, profile.max_health)
    profile.save(update_fields=['equipment_health','current_health','equipment_mana','current_mana'])


def weapon_for(profile):
    item = profile.inventory.filter(is_equipped=True, equipped_slot='weapon').select_related('blueprint').first()
    return item.blueprint if item else None


def combat_values(profile):
    owned = profile.inventory.filter(is_equipped=True, equipped_slot='weapon').select_related('blueprint').first()
    weapon = owned.blueprint if owned else None
    bonuses = profile.equipment_stats
    ranged = weapon and weapon.weapon_type in {'bow','crossbow'}
    attribute = profile.dexterity + bonuses['dexterity_bonus'] if ranged else profile.strength + bonuses['strength_bonus']
    damage = attribute + (owned.effective_stats['damage'] if owned else 0)
    skill = getattr(profile, (weapon.weapon_type if weapon else 'onehand') + '_skill')
    return damage, min(100, skill), weapon.damage_type if weapon else 'weapon'


def add_item(profile, blueprint, quantity=1, *, origin="legacy"):
    if blueprint.stackable:
        item = profile.inventory.filter(blueprint=blueprint, origin=origin, is_equipped=False, is_market_listed=False).order_by('pk').first()
        if item:
            item.quantity += quantity
            item.save(update_fields=['quantity'])
            return item
    return OwnedItem.objects.create(owner=profile, blueprint=blueprint, quantity=quantity, origin=origin)


def consume_ammo(profile):
    weapon = weapon_for(profile)
    if not weapon or weapon.weapon_type not in {'bow','crossbow'}: return True
    kind = 'arrow' if weapon.weapon_type == 'bow' else 'bolt'
    item = profile.inventory.select_for_update().filter(blueprint__kind='ammo', blueprint__original_stats__ammo_type=kind, is_market_listed=False).order_by('pk').first()
    if not item: return False
    if item.quantity == 1: item.delete()
    else:
        item.quantity -= 1
        item.save(update_fields=['quantity'])
    return True
