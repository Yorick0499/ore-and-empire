from .barrier import source_games
from .faction_choice import equipment_camp_allowed
"""Derived equipment statistics never overwrite base attributes."""
from .models import OwnedItem

BONUSES = ('weapon_prot','arrow_prot','fire_prot','magic_prot','strength_bonus','dexterity_bonus','mana_bonus','life_bonus')


def replacement_slot(item, equipped, requested=None):
    """One shared rule for the preview and the real equip action."""
    if item.blueprint.kind == 'ring':
        if requested is not None:
            return requested if requested in {'ring1', 'ring2'} else None
        if item.is_equipped:
            return item.equipped_slot
        return next((slot for slot in ('ring1', 'ring2') if slot not in equipped), 'ring1')
    slot = {'weapon':'weapon', 'armor':'armor', 'amulet':'amulet','belt':'belt'}.get(item.blueprint.kind)
    return slot if requested is None or requested == slot else None


def compare_equipment(profile, item, requested=None):
    from .enhancements import STAT_FIELDS
    equipped = {owned.equipped_slot:owned for owned in profile.inventory.filter(is_equipped=True).select_related('blueprint')}
    slot = replacement_slot(item, equipped, requested)
    if not slot:
        return None
    old = equipped.get(slot)
    old_stats = old.effective_stats if old else dict.fromkeys(STAT_FIELDS, 0)
    new_stats = item.effective_stats
    if slot in {'armor','belt'}:
        current_armor=equipped['armor'].blueprint.catalog_key if 'armor' in equipped else None
        current_belt=equipped['belt'].blueprint if 'belt' in equipped else None
        before=protection_set_bonus(current_armor,current_belt)
        after=protection_set_bonus(item.blueprint.catalog_key if slot=='armor' else current_armor,item.blueprint if slot=='belt' else current_belt)
        for key in ('weapon_prot','arrow_prot','fire_prot','magic_prot'):
            old_stats[key]+=before;new_stats[key]+=after
    labels = {'damage':'Obrażenia broni', 'weapon_prot':'Ochrona przed bronią', 'arrow_prot':'Ochrona przed pociskami',
              'fire_prot':'Ochrona przed ogniem', 'magic_prot':'Ochrona przed magią', 'strength_bonus':'Bonus siły',
              'dexterity_bonus':'Bonus zręczności', 'mana_bonus':'Bonus many', 'life_bonus':'Bonus życia'}
    requirements = []
    if item.blueprint.source_game not in source_games(profile):requirements.append("Przedmiot pochodzi z innego świata.")
    bp = item.blueprint
    from .jarkendar import gear_allowed
    from .gothic2_content import gear_allowed as nk_allowed
    if not nk_allowed(profile,bp):requirements.append("Pozycja źródłowa bez obsługiwanej mechaniki." if bp.original_stats.get("runtime_supported") is False else "Wymagane połączenie światów oraz wskazana frakcja lub przeprawa do Jarkendaru.")
    if not gear_allowed(profile,bp):requirements.append("Najpierw odbierz zadanie Droga za portal po upadku Bariery.")
    if profile.level < bp.min_level:
        requirements.append(f'Poziom {bp.min_level} (masz {profile.level}).')
    if not equipment_camp_allowed(profile,bp.required_camp):
        from .models import PlayerProfile
        requirements.append('Obóz: ' + dict(PlayerProfile.CAMP_LIST).get(bp.required_camp, bp.required_camp) + '.')
    if profile.camp_tier < bp.min_camp_tier:
        requirements.append(f'Ranga obozowa co najmniej {bp.min_camp_tier} (masz {profile.camp_tier}).')
    if profile.strength < bp.required_strength:
        requirements.append(f'Bazowa siła {bp.required_strength} (masz {profile.strength}).')
    if profile.dexterity < bp.required_dexterity:
        requirements.append(f'Bazowa zręczność {bp.required_dexterity} (masz {profile.dexterity}).')
    if item.is_market_listed:
        requirements.append('Najpierw wycofaj ten egzemplarz z targu.')
    return {'slot':slot, 'slot_name':{'weapon':'Broń','armor':'Pancerz','amulet':'Amulet','ring1':'Pierścień I','ring2':'Pierścień II','belt':'Pas'}[slot],
            'old':old, 'requirements':requirements, 'can_equip':not requirements and not item.is_equipped,
            'rows':[{'label':labels[key], 'old':old_stats[key], 'new':new_stats[key],
                     'delta':new_stats[key]-old_stats[key], 'change':f'{new_stats[key]-old_stats[key]:+d}'} for key in STAT_FIELDS]}


def protection_set_bonus(armor,belt):
    bonus=belt.original_stats.get('browser_set_bonus',{}) if belt else {}
    if not isinstance(bonus,dict) or not isinstance(bonus.get('armor_keys'),list):return 0
    value=bonus.get('protection')
    return value if armor in bonus['armor_keys'] and type(value) is int and 0<=value<=20 else 0


def stats_for(profile):
    totals = dict.fromkeys(BONUSES, 0)
    equipped=list(profile.inventory.filter(is_equipped=True).select_related('blueprint'))
    for item in equipped:
        effective = item.effective_stats
        for key in totals:totals[key] += effective[key]
    armor=next((i.blueprint.catalog_key for i in equipped if i.equipped_slot=='armor'),None)
    belt=next((i.blueprint for i in equipped if i.equipped_slot=='belt'),None)
    bonus=protection_set_bonus(armor,belt)
    for key in ('weapon_prot','arrow_prot','fire_prot','magic_prot'):totals[key]+=bonus
    return totals


def allowed(profile, blueprint):
    from .jarkendar import gear_allowed
    from .gothic2_content import gear_allowed as nk_allowed
    return (nk_allowed(profile,blueprint) and gear_allowed(profile,blueprint) and blueprint.source_game in source_games(profile) and profile.level >= blueprint.min_level and
            equipment_camp_allowed(profile,blueprint.required_camp) and
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


def add_item(profile, blueprint, quantity=1, *, origin="legacy", rarity=0):
    if type(rarity) is not int or not 0 <= rarity <= 4 or (rarity and (not blueprint.equippable or quantity != 1)):
        raise ValueError("Nieprawidłowa rzadkość egzemplarza")
    if blueprint.stackable and rarity == 0:
        item = profile.inventory.filter(blueprint=blueprint, origin=origin, is_equipped=False, is_market_listed=False, is_protected=False, rarity=0, upgrade_level=0).order_by('pk').first()
        if item:
            item.quantity += quantity
            item.save(update_fields=['quantity'])
            return item
    return OwnedItem.objects.create(owner=profile, blueprint=blueprint, quantity=quantity, origin=origin, rarity=rarity)


def set_item_protection(profile, item_id, protected):
    """Set a desired state, rather than toggle it when a form is retried."""
    from .game_logic import player_action

    @player_action
    def change(profile):
        if type(protected) is not bool:
            return False
        item = profile.inventory.select_for_update().select_related('blueprint').filter(pk=item_id, is_market_listed=False).first()
        if not item or not item.blueprint.equippable:
            return False
        item.is_protected = protected
        item.save(update_fields=['is_protected'])
        return True

    return change(profile)


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


def physical_survival_health(profile, monster, damage=None):
    """Conservative no-critical forecast using the actual deterministic boss phases."""
    import math
    if damage is None:
        damage,skill,_=combat_values(profile)
        if skill>=100:damage*=2
    if monster.get('boss_key'):
        from .bosses import encounter_round
        kind = combat_values(profile)[2]
        health=monster['life'];incoming=0;turn=0
        while health>0:
            turn+=1
            _,protection,strength,incoming_kind,_=encounter_round(monster,health,turn)
            health-=max(1,damage-(protection if kind in {'weapon','arrow'} else monster.get(kind+'_prot',0)))
            if health<=0:break
            incoming+=max(1,strength-profile.effective_protection(incoming_kind))
        return incoming+10
    rounds = math.ceil(monster['life'] / max(1, damage - monster.get('forecast_protection',monster['weapon_prot'])))
    incoming = max(1,monster.get('forecast_strength',monster['strength'])-profile.effective_protection(monster.get('damage_type','weapon')))
    return (rounds-1)*incoming+10
