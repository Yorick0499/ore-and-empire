from characters.models import OwnedItem, PlayerProfile, MarketTrade, BossAttempt
from .bosses import BOSSES
from django.db import transaction
from functools import wraps
from django.utils import timezone
from datetime import timedelta
import random
from dataclasses import dataclass


ENERGY_INTERVAL_SECONDS = 60
MAX_MARKET_PRICE = 1_000_000


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
    if profile.current_health >= profile.life:
        profile.current_health = profile.life
        profile.health_updated_at = now
    elif health_points:
        profile.current_health = min(profile.life, profile.current_health + health_points)
        profile.health_updated_at += timedelta(seconds=health_points * ENERGY_INTERVAL_SECONDS)
        if profile.current_health == profile.life:
            profile.health_updated_at = now
    profile.save(update_fields=["current_energy", "energy_updated_at", "current_health", "health_updated_at"])


def player_action(fn):
    """Refresh stale objects and serialize actions on the same player/item.

    PostgreSQL honors row locks; SQLite is for local development only.
    """

    @wraps(fn)
    def wrapped(profile, *args, **kwargs):
        with transaction.atomic():
            ids = {profile.pk}
            if fn.__name__ == "buy_item_on_market" and args:
                owner_id = (
                    OwnedItem.objects.filter(pk=args[0].pk)
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
            recover_energy(profile)
            for arg in args:
                if isinstance(arg, OwnedItem):
                    fresh = (
                        OwnedItem.objects.select_for_update().filter(pk=arg.pk).first()
                    )
                    if fresh is None:
                        return False
                    arg.refresh_from_db()
                    # A listing changed owner while locks were being acquired.
                    if fn.__name__ == "buy_item_on_market" and arg.owner_id not in ids:
                        return False
            return fn(profile, *args, **kwargs)

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
    ore_reward = reward_snapshot(random.randint(10, 25), 0)[0]
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

    def __iter__(self):
        yield self.won
        yield self.log


def simulate_combat(profile, monster_key, *, monster=None):
    monster = BESTIARY[monster_key] if monster is None else monster
    hunt_result = None

    temp_hero_life = profile.current_health
    temp_monster_life = monster["life"]

    combat_log = []
    equipped_item = profile.inventory.filter(is_equipped=True).first()
    weapon_damage = None
    if equipped_item:
        weapon_damage = equipped_item.blueprint.damage
    else:
        weapon_damage = 0

    while temp_hero_life > 0 and temp_monster_life > 0:
        # hero turn
        critical_chance = random.randint(1, 100)
        if critical_chance <= profile.onehand_skill:
            hero_damage = 2 * (profile.strength + weapon_damage)
        else:
            hero_damage = profile.strength + weapon_damage
        hero_damage = max(1, hero_damage - monster["weapon_prot"])
        temp_monster_life = temp_monster_life - hero_damage

        combat_log.append(f"{profile.user} zadaje {hero_damage} obrażeń.")
        combat_log.append(f"{monster['nazwa']} pozostało {temp_monster_life} HP")

        if temp_monster_life <= 0:
            combat_log.append(f"{profile.user} zwyciężył.")
            break

        # monster turn
        monster_damage = max(1, monster["strength"] - profile.weapon_prot)

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

    return CombatResult(hunt_result, combat_log, max(1, temp_hero_life))


@player_action
def execute_hunt(profile, monster_key, location_key="forest"):
    from .locations import BY_KEY

    location = BY_KEY.get(location_key)
    if location is None or not location.accessible(profile) or monster_key not in location.monsters:
        return False
    if monster_key not in BESTIARY or profile.is_busy:
        return False
    if profile.current_energy < 15 or profile.current_health < 10:
        return False
    profile.current_energy = profile.current_energy - 15

    result = simulate_combat(profile, monster_key)
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
    return log


@player_action
def list_item_on_market(seller_profile, owned_item, price):
    if owned_item.owner != seller_profile:
        return False
    if owned_item.is_equipped:
        return False
    if owned_item.is_market_listed:
        return False
    if type(price) is not int or not 1 <= price <= MAX_MARKET_PRICE:
        return False
    owned_item.is_market_listed = True
    owned_item.market_price = price
    owned_item.save()
    return True


@player_action
def buy_item_on_market(buyer_profile, owned_item):
    current_owner = owned_item.owner
    if not owned_item.is_market_listed:
        return False
    if owned_item.owner == buyer_profile:
        return False
    if owned_item.market_price is None or owned_item.market_price <= 0:
        return False
    if owned_item.market_price > buyer_profile.ore_balance:
        return False
    MarketTrade.objects.create(
        blueprint=owned_item.blueprint,
        seller=current_owner,
        buyer=buyer_profile,
        price=owned_item.market_price,
    )
    buyer_profile.ore_balance = buyer_profile.ore_balance - owned_item.market_price
    current_owner.ore_balance = current_owner.ore_balance + owned_item.market_price
    owned_item.owner = buyer_profile
    owned_item.market_price = None
    owned_item.is_market_listed = False
    owned_item.save()
    buyer_profile.save()
    current_owner.save()
    return True


@player_action
def delist_item_from_market(seller_profile, owned_item):
    if owned_item.owner != seller_profile:
        return False
    if not owned_item.is_market_listed:
        return False
    owned_item.is_market_listed = False
    owned_item.market_price = None
    owned_item.save()
    return True


@player_action
def equip_item(profile, owned_item):
    if owned_item.is_equipped:
        return False
    if owned_item.owner != profile:
        return False
    if owned_item.is_market_listed:
        return False
    if owned_item.blueprint.required_strength > profile.strength:
        return False
    profile.inventory.filter(is_equipped=True).update(is_equipped=False)
    owned_item.is_equipped = True
    owned_item.save()
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
    return True


@player_action
def buy_item_from_npc(profile, item):
    if item.base_value < 0:
        return False
    if profile.ore_balance < item.base_value:
        return False
    profile.ore_balance = profile.ore_balance - item.base_value
    OwnedItem.objects.create(owner=profile, blueprint=item)
    profile.save()
    return True


@player_action
def sell_item_from_npc(profile, item):
    if item.owner != profile:
        return False
    if item.is_equipped:
        return False
    if item.is_market_listed:
        return False
    profile.ore_balance = profile.ore_balance + int(item.blueprint.base_value * 0.5)
    item.delete()
    profile.save()
    return True


def check_level_up(profile):
    if profile.experience < profile.required_exp:
        return False
    while profile.experience >= profile.required_exp:
        profile.level += 1
        profile.skill_points += 10
        profile.life += 12
    profile.save()
    return True


@player_action
def train_attribute(profile, attribute_name):
    if attribute_name not in {"strength", "dexterity", "mana"}:
        return False
    if profile.skill_points < 1:
        return False
    if profile.ore_balance < 10:
        return False
    current_value = getattr(profile, attribute_name)
    setattr(profile, attribute_name, current_value + 1)
    profile.ore_balance = profile.ore_balance - 10
    profile.skill_points = profile.skill_points - 1
    profile.save()
    from .camp_progression import record_camp_event
    record_camp_event(profile, "train:" + attribute_name)
    return True


@player_action
def execute_boss(profile, boss_key):
    from .locations import BY_KEY
    location = BY_KEY.get(boss_key)
    if location is None or not location.accessible(profile):
        return False
    boss = BOSSES.get(boss_key)
    if boss is None or profile.level < boss.level or profile.is_busy:
        return False
    if profile.current_energy < boss.energy_cost or profile.current_health < 10:
        return False
    now = timezone.now()
    last = BossAttempt.objects.filter(profile=profile, boss_key=boss_key).first()
    if last and now < last.created_at + timedelta(minutes=boss.cooldown_minutes):
        return False
    result = simulate_combat(profile, boss_key, monster=boss.monster)
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
    return BossAttempt.objects.create(
        profile=profile,
        boss_key=boss_key,
        created_at=now,
        won=won,
        experience_reward=experience,
        ore_reward=ore,
        combat_log=combat_log,
    )


@player_action
def choose_camp(profile, camp):
    if profile.camp != "NONE" or camp not in {"OLD_CAMP", "NEW_CAMP", "SWAMP_CAMP"}:
        return False
    profile.camp = camp
    profile.save(update_fields=["camp"])
    return True
