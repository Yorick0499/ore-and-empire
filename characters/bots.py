"""Bounded baseline bot policy. Future AI policies implement choose(observation).

Policies receive immutable observations, return an allowlisted action and never
receive ORM objects or permission to mint ore. Every action uses game_logic.
"""

from dataclasses import dataclass
from typing import Protocol
from .models import OwnedItem, ItemBluePrint
from . import game_logic as game


@dataclass(frozen=True)
class Observation:
    energy: int
    ore: int
    busy: bool
    reward_ready: bool
    offer_id: int | None
    inventory_id: int | None
    blueprint_id: int | None
    equip_id: int | None
    armed: bool


class Policy(Protocol):
    def choose(self, observation: Observation) -> tuple[str, int | None]: ...


class BaselinePolicy:
    def choose(self, observation):
        if observation.reward_ready:
            return "claim", None
        if observation.busy:
            return "wait", None
        if observation.equip_id is not None:
            return "equip", observation.equip_id
        if observation.armed and observation.energy >= 15 and observation.ore >= 50:
            return "hunt", None
        if observation.armed and observation.ore < 50 and observation.energy >= 10:
            return "mine", None
        if observation.inventory_id is not None:
            return "list", observation.inventory_id
        if observation.offer_id is not None:
            return "buy", observation.offer_id
        if observation.blueprint_id is not None:
            return "stock", observation.blueprint_id
        if observation.energy >= 10:
            return "mine", None
        return "wait", None


def tick_bot(profile, policy=None):
    if not profile.is_bot:
        raise ValueError("Only designated bot profiles may run bot policies")
    game.refresh_player(profile)
    offer = (
        OwnedItem.objects.filter(
            is_market_listed=True,
            market_price__gt=0,
            market_price__lte=profile.ore_balance,
        )
        .exclude(owner=profile)
        .select_related("blueprint")
        .order_by("market_price", "pk")
    )
    # Never pay over 120% of the NPC price under this baseline policy.
    from django.db.models import F

    offer = offer.filter(market_price__lte=F("blueprint__base_value") * 1.2).first()
    item = (
        profile.inventory.filter(is_market_listed=False, is_equipped=False)
        .order_by("pk")
        .first()
    )
    stock = (
        ItemBluePrint.objects.filter(
            base_value__gt=0, base_value__lte=profile.ore_balance
        )
        .order_by("base_value", "pk")
        .first()
    )
    armed = profile.inventory.filter(is_equipped=True).exists()
    equipment = (
        profile.inventory.filter(
            is_market_listed=False,
            is_equipped=False,
            blueprint__required_strength__lte=profile.strength,
        )
        .order_by("pk")
        .first()
        if not armed
        else None
    )
    # Keep inventories bounded; bots cannot accumulate unlimited listed stock.
    if profile.inventory.count() >= 3:
        stock = None
        offer = None
    obs = Observation(
        profile.current_energy,
        profile.ore_balance,
        profile.is_busy,
        profile.action_end_time is not None and not profile.is_busy,
        offer.pk if offer else None,
        item.pk if item else None,
        stock.pk if stock else None,
        equipment.pk if equipment else None,
        armed,
    )
    action, target = (policy or BaselinePolicy()).choose(obs)
    # Execute only the offered target; a policy cannot act on arbitrary objects.
    if action == "claim":
        success = game.claim_ore_reward(profile)
    elif action == "mine":
        success = game.start_mining(profile, 15)
    elif action == "equip" and equipment and target == equipment.pk:
        success = game.equip_item(profile, equipment)
    elif action == "hunt":
        success = game.execute_hunt(profile, "young_scavenger") is not False
    elif action == "list" and item and target == item.pk:
        price = max(1, min(game.MAX_MARKET_PRICE, int(item.blueprint.base_value * 1.1)))
        success = game.list_item_on_market(profile, item, price)
    elif action == "buy" and offer and target == offer.pk:
        success = game.buy_item_on_market(profile, offer)
    elif action == "stock" and stock and target == stock.pk:
        success = game.buy_item_from_npc(profile, stock)
    elif action == "wait":
        success = True
    else:
        return "rejected", False
    return action, success
