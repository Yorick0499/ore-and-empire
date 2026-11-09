from characters.models import OwnedItem, ItemBluePrint, PlayerProfile, MarketTrade, BossAttempt
from .bosses import BOSSES
from django.db import transaction,OperationalError,connection
from django.core.exceptions import ObjectDoesNotExist
from functools import wraps
from django.utils import timezone
from datetime import timedelta
import random
from uuid import uuid4
from dataclasses import dataclass


ENERGY_INTERVAL_SECONDS = 60
MAX_MARKET_PRICE = 1_000_000
WEAPON_SKILLS = {"onehand_skill":"Broń jednoręczna", "twohand_skill":"Broń dwuręczna", "bow_skill":"Łuki", "crossbow_skill":"Kusze"}


def recover_energy(profile):
    now = timezone.now()
    elapsed = max(0, int((now - profile.energy_updated_at).total_seconds()))
    points = elapsed // ENERGY_INTERVAL_SECONDS
    if profile.current_energy >= profile.max_energy:
        profile.energy_updated_at = now
    elif points:
        profile.current_energy = min(
            profile.max_energy, profile.current_energy + points
        )
        profile.energy_updated_at += timedelta(seconds=points * ENERGY_INTERVAL_SECONDS)
        if profile.current_energy == profile.max_energy:
            profile.energy_updated_at = now
    elapsed_health = max(0, int((now - profile.health_updated_at).total_seconds()))
    health_points = elapsed_health // ENERGY_INTERVAL_SECONDS
    if profile.current_health >= profile.max_health:
        profile.current_health = profile.max_health
        profile.health_updated_at = now
    elif health_points:
        profile.current_health = min(profile.max_health, profile.current_health + health_points)
        profile.health_updated_at += timedelta(seconds=health_points * ENERGY_INTERVAL_SECONDS)
        if profile.current_health == profile.max_health:
            profile.health_updated_at = now
    mana_elapsed=max(0,int((now-profile.mana_updated_at).total_seconds()))
    mana_points=mana_elapsed//30
    if profile.current_mana>=profile.max_mana:
        profile.current_mana=profile.max_mana;profile.mana_updated_at=now
    elif mana_points:
        profile.current_mana=min(profile.max_mana,profile.current_mana+mana_points)
        profile.mana_updated_at+=timedelta(seconds=mana_points*30)
        if profile.current_mana==profile.max_mana:profile.mana_updated_at=now
    profile.save(update_fields=["current_energy", "energy_updated_at", "current_health", "health_updated_at", "current_mana", "mana_updated_at"])


def player_action(fn):
    """Refresh stale objects and serialize actions on the same player/item.

    PostgreSQL honors row locks; SQLite is for local development only.
    """

    from .realms import profile_scope
    @profile_scope
    @wraps(fn)
    def wrapped(profile, *args, **kwargs):
        try:return locked_action(profile,*args,**kwargs)
        except OperationalError as exc:
            code=getattr(exc.__cause__,'sqlstate',None)
            if connection.vendor!='postgresql' or code not in {'40P01','40001','55P03'}:raise
            # The transaction/savepoint has rolled back; the caller may retry explicitly.
            profile.refresh_from_db()
            if hasattr(profile,'_gear_stats_cache'):del profile._gear_stats_cache
            return False

    def locked_action(profile,*args,**kwargs):
        with transaction.atomic():
            from .worlds import playable
            profile.refresh_from_db()
            if not playable(profile):return False
            ids = {profile.pk}
            # Named calls must obey the same locks and refresh rules as positional calls.
            action_arguments = (*args, *kwargs.values())
            market_item = args[0] if args else kwargs.get("owned_item")
            if fn.__name__ == "buy_item_on_market" and isinstance(market_item, OwnedItem):
                owner_id = (
                    OwnedItem.objects.filter(pk=market_item.pk)
                    .values_list("owner_id", flat=True)
                    .first()
                )
                if owner_id is not None:
                    ids.add(owner_id)
            list(
                PlayerProfile.objects.select_for_update()
                .filter(pk__in=ids)
                .order_by("pk")
            )
            profile.refresh_from_db()
            if hasattr(profile, '_gear_stats_cache'): del profile._gear_stats_cache
            recover_energy(profile)
            for arg in action_arguments:
                if isinstance(arg, (OwnedItem, ItemBluePrint)):
                    try:
                        arg.refresh_from_db(from_queryset=type(arg).objects.select_for_update())
                    except ObjectDoesNotExist:
                        return False
                    # A listing changed owner while locks were being acquired.
                    if fn.__name__ == "buy_item_on_market" and isinstance(arg, OwnedItem) and arg.owner_id not in ids:
                        return False
            from .economic_ledger import balances, record_changes
            before = balances(ids)
            result = fn(profile, *args, **kwargs)
            record_changes(before, fn.__name__)
            return result

    return wrapped


@player_action
def refresh_player(profile):
    return profile


@player_action
def start_mining(profile, duration_seconds):
    if not isinstance(duration_seconds, int) or not 1 <= duration_seconds <= 3600:
        return False
    if profile.action_end_time is not None or profile.adventures.filter(claimed_at__isnull=True).exists():
        return False
    if profile.current_energy < 10:
        return False
    profile.current_energy = profile.current_energy - 10
    profile.action_end_time = timezone.now() + timedelta(seconds=duration_seconds)
    profile.save()
    return True


@player_action
def claim_ore_reward(profile):
    if not profile.action_end_time:
        return False
    if profile.action_end_time > timezone.now():
        return False
    from .world_events import reward_snapshot
    ore_reward = reward_snapshot(random.randint(10, 25), 0)[0]+profile.camp_perks["supply_level"]
    profile.ore_balance = profile.ore_balance + ore_reward
    profile.action_end_time = None
    profile.save()
    from .camp_progression import record_camp_event
    record_camp_event(profile, "mine")
    return True


from .bestiary import BESTIARY


@dataclass(frozen=True)
class CombatResult:
    won: bool
    log: list
    remaining_health: int
    remaining_mana: int | None = None
    spell_casts: int = 0

    def __iter__(self):
        yield self.won
        yield self.log


def simulate_combat(profile, monster_key, *, monster=None, magic_plan=None):
    monster = BESTIARY[monster_key] if monster is None else monster
    hunt_result = None

    temp_hero_life = profile.current_health
    temp_monster_life = monster["life"]

    combat_log = []
    from .equipment import combat_values
    base_damage, critical_skill, damage_type = combat_values(profile)

    mana=profile.current_mana
    casts=0
    turn = 0
    previous_stage = 0
    while temp_hero_life > 0 and temp_monster_life > 0:
        turn += 1
        protection = monster["weapon_prot"]
        strength = monster["strength"]
        incoming_type = monster.get("damage_type", "weapon")
        if monster.get("boss_key"):
            from .bosses import encounter_round
            stage, protection, strength, incoming_type, warnings = encounter_round(monster, temp_monster_life, turn)
            if stage != previous_stage:
                combat_log.append(f"Faza {stage}: {monster['nazwa']}.")
                previous_stage = stage
            combat_log.extend(warnings)
        # hero turn
        casting=bool(magic_plan and mana>=magic_plan.cost and (not magic_plan.scroll or casts<magic_plan.quantity))
        if casting:
            spell=magic_plan.spell;mana-=magic_plan.cost;casts+=1
            hero_damage=max(1,spell.damage-monster.get(spell.damage_type+'_prot',0))
            if monster.get("boss_key")=="crawler_nest" and spell.damage_type=="fire":hero_damage=hero_damage*120//100
            combat_log.append(f"{spell.name}: koszt {magic_plan.cost} many.")
        else:
            # Magical focus falls back to fists; no free ranged attacks/ammunition.
            physical=profile.strength+profile.equipment_stats['strength_bonus'] if magic_plan else base_damage
            critical_chance=random.randint(1,100)
            hero_damage=physical*(2 if not magic_plan and critical_chance<=critical_skill else 1)
            kind='weapon' if magic_plan else damage_type
            hero_damage=max(1,hero_damage-(protection if monster.get('boss_key') and kind in ('weapon','arrow') else monster.get(kind+'_prot',monster['weapon_prot'] if kind=='arrow' else 0)))
        temp_monster_life = temp_monster_life - hero_damage

        combat_log.append(f"{profile.user} zadaje {hero_damage} obrażeń.")
        combat_log.append(f"{monster['nazwa']} pozostało {temp_monster_life} HP")

        if temp_monster_life <= 0:
            combat_log.append(f"{profile.user} zwyciężył.")
            break

        # monster turn
        monster_damage = max(1, strength - profile.effective_protection(incoming_type))

        if casting:
            if spell.stagger_every and casts%spell.stagger_every==0:
                monster_damage=0;combat_log.append('Przeciwnik traci turę pod wpływem zaklęcia.')
            elif spell.mitigation:
                monster_damage=max(1,monster_damage*(100-spell.mitigation)//100)
        temp_hero_life = temp_hero_life - monster_damage

        combat_log.append(f"{monster['nazwa']} zadaje {monster_damage} obrażeń")
        combat_log.append(f"{profile.user} pozostało {temp_hero_life} HP")

        if temp_hero_life <= 0:
            combat_log.append(f"{monster['nazwa']} zwyciężył")
            break

    # check hunt_result
    if temp_hero_life <= 0:
        hunt_result = False

    if temp_monster_life <= 0:
        hunt_result = True

    return CombatResult(hunt_result, combat_log, max(1, temp_hero_life),mana,casts)


@player_action
def execute_hunt(profile, monster_key, location_key="forest", request_key=None):
    from .locations import BY_KEY
    from .loot import battle_request, save_battle
    prior, request_key, valid = battle_request(profile, request_key, monster_key, location_key)
    if not valid: return False
    if prior: return prior.combat_log

    location = BY_KEY.get(location_key)
    if location is None or not location.accessible(profile) or monster_key not in location.monsters:
        return False
    if monster_key not in BESTIARY or profile.is_busy:
        return False
    if profile.current_energy < 15 or profile.current_health < 10:
        return False
    from .equipment import consume_ammo
    from .magic import combat_plan,apply_combat_magic
    plan=combat_plan(profile)
    if profile.prepared_magic_id and (not plan or profile.current_mana<plan.cost):return False
    if not plan and not consume_ammo(profile): return False
    profile.current_energy = profile.current_energy - 15
    before_exp = profile.experience

    result = simulate_combat(profile, monster_key, magic_plan=plan)
    if isinstance(result,CombatResult):apply_combat_magic(profile,plan,result)
    win, log = result
    profile.current_health = getattr(result, "remaining_health", profile.current_health)
    profile.health_updated_at = timezone.now()
    if win:
        monster = BESTIARY[monster_key]
        from .world_events import reward_snapshot
        experience = reward_snapshot(0, monster["exp_reward"])[1]
        profile.experience += experience
        log.append(f"Zyskałeś {experience} EXP.")
        check_level_up(profile)
        from .camp_progression import record_camp_event
        record_camp_event(profile, "hunt:" + monster_key)
    else:
        log.append("Zyskałeś 0 EXP.")
        log.append(
            "Ledwo uszedłeś z życiem. Miałeś jednak dużo szczęścia - uratowali cię myśliwi polujący w tych terenach."
        )
    profile.save()
    save_battle(profile, request_key, monster_key, location_key, win, log, profile.experience - before_exp, details={"magic":plan.spell.key if plan else None,"casts":getattr(result,"spell_casts",0),"mana_after":profile.current_mana})
    return log


@player_action
def list_item_on_market(seller_profile, owned_item, price):
    if owned_item.is_protected:
        return False
    if owned_item.owner != seller_profile or not owned_item.blueprint.tradeable:
        return False
    if owned_item.is_equipped or seller_profile.prepared_magic_id==owned_item.pk:
        return False
    if owned_item.is_market_listed:
        return False
    if type(price) is not int or not 1 <= price <= MAX_MARKET_PRICE:
        return False
    owned_item.listed_at = timezone.now()
    owned_item.is_market_listed = True
    owned_item.market_price = price
    owned_item.save()
    from .market_policy import record_market_event
    record_market_event(seller_profile,owned_item,"listing",price)
    return True


@player_action
def buy_item_on_market(buyer_profile, owned_item, expected_price=None):
    if expected_price is not None and (type(expected_price) is not int or expected_price != owned_item.market_price):
        return False
    current_owner = owned_item.owner
    if current_owner.world_id!=buyer_profile.world_id:return False
    if not owned_item.is_market_listed:
        return False
    if owned_item.owner == buyer_profile:
        return False
    if owned_item.market_price is None or owned_item.market_price <= 0:
        return False
    if owned_item.market_price > buyer_profile.ore_balance:
        return False
    MarketTrade.objects.create(rarity=owned_item.rarity,upgrade_level=owned_item.upgrade_level,created_at=timezone.now(),
        blueprint=owned_item.blueprint,
        seller=current_owner,
        buyer=buyer_profile,
        price=owned_item.market_price,
        quantity=owned_item.quantity,
    )
    from .market_policy import record_market_event
    record_market_event(buyer_profile,owned_item,"sale",owned_item.market_price)
    buyer_profile.ore_balance = buyer_profile.ore_balance - owned_item.market_price
    current_owner.ore_balance = current_owner.ore_balance + owned_item.market_price
    owned_item.owner = buyer_profile
    owned_item.market_price = None
    owned_item.listed_at = None
    owned_item.is_market_listed = False
    owned_item.save()
    buyer_profile.save()
    current_owner.save()
    return True


@player_action
def delist_item_from_market(seller_profile, owned_item, reason="manual"):
    if owned_item.owner != seller_profile:
        return False
    if not owned_item.is_market_listed:
        return False
    from .market_policy import record_market_event
    record_market_event(seller_profile,owned_item,"cancellation",owned_item.market_price,reason=reason)
    owned_item.listed_at = None
    owned_item.is_market_listed = False
    owned_item.market_price = None
    owned_item.save()
    return True


@player_action
def equip_item(profile, owned_item, slot=None):
    if owned_item.is_equipped:
        return False
    if owned_item.owner != profile:
        return False
    if owned_item.is_market_listed:
        return False
    from .equipment import allowed, sync_health, replacement_slot
    bp = owned_item.blueprint
    if not bp.equippable or not allowed(profile, bp) or bp.required_strength > profile.strength or bp.required_dexterity > profile.dexterity:
        return False
    equipped = {item.equipped_slot:item for item in profile.inventory.filter(is_equipped=True)}
    slot = replacement_slot(owned_item, equipped, slot)
    if not slot:
        return False
    profile.inventory.filter(is_equipped=True, equipped_slot=slot).update(is_equipped=False, equipped_slot='')
    owned_item.is_equipped = True
    owned_item.equipped_slot = slot
    owned_item.save()
    sync_health(profile)
    return True


@player_action
def unequip_item(profile, owned_item):
    if not owned_item.is_equipped:
        return False
    if owned_item.owner != profile:
        return False
    if owned_item.is_market_listed:
        return False
    owned_item.is_equipped = False
    owned_item.save()
    from .equipment import sync_health
    sync_health(profile)
    return True


@player_action
def buy_item_from_npc(profile, item, quantity=1):
    from .equipment import allowed, add_item
    if type(quantity) is not int or not 1<=quantity<=100 or (quantity>1 and (not item.stackable or item.equippable)):
        return False
    if not item.merchant or not allowed(profile, item) or item.base_value < 0:
        return False
    if profile.ore_balance < item.base_value*quantity:
        return False
    profile.ore_balance = profile.ore_balance - item.base_value*quantity
    add_item(profile, item, quantity, origin="merchant")
    profile.save()
    return True


@player_action
def sell_item_from_npc(profile, item):
    if item.is_protected:
        return False
    if item.owner != profile or not item.blueprint.tradeable:
        return False
    if item.is_equipped or profile.prepared_magic_id==item.pk:
        return False
    if item.is_market_listed:
        return False
    profile.ore_balance = profile.ore_balance + int(item.blueprint.base_value * 0.5) * item.quantity
    item.delete()
    profile.save()
    return True


def check_level_up(profile):
    if profile.experience < profile.required_exp:
        return False
    previous_level=profile.level
    while profile.experience >= profile.required_exp:
        profile.level += 1
        profile.skill_points += 10
        profile.life += 12
    profile.save()
    from .models import JournalNotice
    gained=profile.level-previous_level
    JournalNotice.objects.get_or_create(profile=profile,key=f'level:{profile.level}',defaults={
        'title':f'Poziom {profile.level}! +{gained*10} PN i +{gained*12} maksymalnego zdrowia.',
        'destination':'train_page'})
    return True


@player_action
def train_attribute(profile, attribute_name, count=1):
    if attribute_name not in {"strength", "dexterity", "mana", *WEAPON_SKILLS}:
        return False
    if type(count) is not int or not 1 <= count <= 10 or profile.skill_points < count:
        return False
    if attribute_name in WEAPON_SKILLS and getattr(profile,attribute_name)+count > 100:
        return False
    cost=10-profile.camp_perks["training_level"]
    if profile.ore_balance < cost * count:
        return False
    current_value = getattr(profile, attribute_name)
    setattr(profile, attribute_name, current_value + count)
    profile.ore_balance = profile.ore_balance - cost * count
    profile.skill_points = profile.skill_points - count
    profile.save()
    from .camp_progression import record_camp_event
    for _ in range(count):record_camp_event(profile, "train:" + attribute_name)
    return True


@player_action
def execute_boss(profile, boss_key, request_key=None):
    from .loot import battle_request, save_battle
    prior, request_key, valid = battle_request(profile, request_key, boss_key, boss_key)
    if not valid: return False
    if prior: return prior.boss_attempt if prior.boss_attempt_id else False
    from .locations import BY_KEY
    location = BY_KEY.get(boss_key)
    if location is None or not location.accessible(profile):
        return False
    boss = BOSSES.get(boss_key)
    if boss is None or profile.level < boss.level or profile.is_busy:
        return False
    from .finale import finale_ready
    if boss_key == "sleeper_sanctum" and not finale_ready(profile):return False
    if profile.current_energy < boss.energy_cost or profile.current_health < 10:
        return False
    now = timezone.now()
    last = BossAttempt.objects.filter(profile=profile, boss_key=boss_key).first()
    if last and now < last.created_at + timedelta(minutes=boss.cooldown_minutes):
        return False
    from .equipment import consume_ammo
    from .magic import combat_plan,apply_combat_magic
    plan=combat_plan(profile)
    if profile.prepared_magic_id and (not plan or profile.current_mana<plan.cost):return False
    if not plan and not consume_ammo(profile): return False
    result = simulate_combat(profile, boss_key, monster=boss.monster, magic_plan=plan)
    if isinstance(result,CombatResult):apply_combat_magic(profile,plan,result)
    won, combat_log = result
    profile.current_health = getattr(result, "remaining_health", profile.current_health)
    profile.health_updated_at = now
    profile.current_energy -= boss.energy_cost
    experience = boss.experience if won else 0
    ore = boss.ore if won else 0
    if won:
        from .world_events import reward_snapshot
        ore, experience, _, _ = reward_snapshot(ore, experience)
    if won:
        profile.experience += experience
        profile.ore_balance += ore
        check_level_up(profile)
        from .camp_progression import record_camp_event
        record_camp_event(profile, "boss:" + boss_key)
        combat_log.append(f"Nagroda: {experience} PD i {ore} bryłek rudy.")
    else:
        combat_log.append(
            "Wycofujesz się bez łupu. Przygotuj lepszy oręż przed kolejną próbą."
        )
    profile.save()
    attempt = BossAttempt.objects.create(
        profile=profile,
        boss_key=boss_key,
        created_at=now,
        won=won,
        experience_reward=experience,
        ore_reward=ore,
        combat_log=combat_log,
    )

    save_battle(profile, request_key, boss_key, boss_key, won, combat_log, experience, ore, attempt, details={"magic":plan.spell.key if plan else None,"casts":getattr(result,"spell_casts",0),"mana_after":profile.current_mana})
    if won and boss_key == "sleeper_sanctum":
        from .finale import record_completion
        record_completion(profile, attempt)
    return attempt


@player_action
def choose_camp(profile, camp):
    from .story_gates import missing
    if missing(profile):return False
    from .realms import camps
    if profile.camp != "NONE" or camp not in camps(profile.world):
        return False
    profile.camp = camp
    profile.save(update_fields=["camp"])
    return True


@player_action
def use_item(profile, item):
    if item.owner != profile or item.is_market_listed or item.is_equipped or item.blueprint.kind != 'consumable': return False
    bp = item.blueprint
    health = min(bp.heal_amount, profile.max_health - profile.current_health)
    energy = min(bp.energy_amount, profile.max_energy - profile.current_energy)
    if health <= 0 and energy <= 0: return False
    if energy:
        from .economic_ledger import refills_remaining
        from .models import EnergyRefill
        if not refills_remaining(profile): return False
        EnergyRefill.objects.create(profile=profile, created_at=timezone.now(), reference='item:' + str(uuid4()))
    profile.current_health += health
    profile.current_energy += energy
    if health: profile.health_updated_at = timezone.now()
    if energy: profile.energy_updated_at = timezone.now()
    profile.save()
    from .market_policy import record_market_event
    record_market_event(profile,item,"consumption",quantity=1)
    if item.quantity == 1: item.delete()
    else:
        item.quantity -= 1
        item.save(update_fields=['quantity'])
    return True
