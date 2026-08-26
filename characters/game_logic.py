from django.utils import timezone
from datetime import timedelta
import random


def start_mining(profile, duration_seconds):
    if profile.is_busy:
        return False
    if profile.current_energy < 10:
        return False
    profile.current_energy = profile.current_energy - 10
    profile.action_end_time = timezone.now() + timedelta(seconds=duration_seconds)
    profile.save()
    return True


def claim_ore_reward(profile):
    if not profile.action_end_time:
        return False
    if profile.action_end_time > timezone.now():
        return False
    ore_reward = random.randint(10, 25)
    profile.ore_balance = profile.ore_balance + ore_reward
    profile.action_end_time = None
    profile.save()
    return True


BESTIARY = {
    "scavenger": {
        "nazwa": "Ścierwojad",
        "level": 3,
        "life": 40,
        "strength": 20,
        "weapon_prot": 5,
        "exp_reward": 50,
    },
    "molerat": {
        "nazwa": "Kretoszczur",
        "level": 5,
        "life": 50,
        "strength": 25,
        "weapon_prot": 10,
        "exp_reward": 60,
    },
    "shadowbeast": {
        "nazwa": "Cieniostwór",
        "level": 25,
        "life": 400,
        "strength": 120,
        "weapon_prot": 60,
        "exp_reward": 400,
    },
}


def simulate_combat(profile, monster_key):
    monster = BESTIARY[monster_key]
    hunt_result = None

    temp_hero_life = profile.life
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
            hero_damage = profile.strength + weapon_damage
        else:
            hero_damage = weapon_damage
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

    return hunt_result, combat_log


def execute_hunt(profile, monster_key):
    if profile.current_energy < 15:
        return False
    profile.current_energy = profile.current_energy - 15

    win, log = simulate_combat(profile, monster_key)
    if win:
        monster = BESTIARY[monster_key]
        profile.experience = profile.experience + monster["exp_reward"]
        log.append(f"Zyskałeś {monster['exp_reward']} EXP.")
    else:
        log.append("Zyskałeś 0 EXP.")
        log.append(
            "Ledwo uszedłeś z życiem. Miałeś jednak dużo szczęścia - uratowali cię myśliwi polujący w tych terenach."
        )
    profile.save()
    return log


def list_item_on_market(seller_profile, owned_item, price):
    if owned_item.owner != seller_profile:
        return False
    if owned_item.is_equipped:
        return False
    if owned_item.is_market_listed:
        return False
    if price <= 0:
        return False
    owned_item.is_market_listed = True
    owned_item.market_price = price
    owned_item.save()
    return True


def buy_item_on_market(buyer_profile, owned_item):
    current_owner = owned_item.owner
    if not owned_item.is_market_listed:
        return False
    if owned_item.owner == buyer_profile:
        return False
    if owned_item.market_price > buyer_profile.ore_balance:
        return False
    buyer_profile.ore_balance = buyer_profile.ore_balance - owned_item.market_price
    current_owner.ore_balance = current_owner.ore_balance + owned_item.market_price
    owned_item.owner = buyer_profile
    owned_item.market_price = None
    owned_item.is_market_listed = False
    owned_item.save()
    buyer_profile.save()
    current_owner.save()
    return True


def delist_item_from_market(seller_profile, owned_item):
    if owned_item.owner != seller_profile:
        return False
    if not owned_item.is_market_listed:
        return False
    owned_item.is_market_listed = False
    owned_item.market_price = None
    owned_item.save()
    return True


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
