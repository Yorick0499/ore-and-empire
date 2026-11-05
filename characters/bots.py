"""Autonomous local players. Policies see immutable data and an action allowlist.

No policy receives ORM objects, resource grants or an administrator capability.
One tick performs one ordinary player action, or rests for real-time recovery.
"""
from dataclasses import dataclass
import math
from fractions import Fraction
from typing import Protocol
from uuid import uuid4
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from .bot_telemetry import record_decision
from .models import OwnedItem, ItemBluePrint, AdventureTemplate, StoreProduct, BossAttempt
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
    role: str = "hunter"
    skill_points: int = 0
    strength: int = 10
    health: int = 50
    max_health: int = 50
    premium: int = 0
    turn: int = 0
    camp: str = "NONE"
    camp_target: int = 1
    rank_target: int | None = None
    rank_action: str = ""
    needs_ore: bool = False
    training: str = "strength"
    training_needed: bool = False
    quest_mine: bool = False
    quest_hunt: bool = False
    boss_key: str | None = None
    hunt_key: str | None = None
    hunt_location: str | None = None
    adventure_id: int | None = None
    adventure_ready: bool = False
    template_id: int | None = None
    product_id: int | None = None
    product_urgent: bool = False
    upgrade_action: str = ""
    upgrade_id: int | None = None
    upgrade_cost: int = 0
    upgrade_gain: int = 0
    ore_reserve: int = 0
    disposal_id: int | None = None
    story_action: str = ""
    story_target: int | None = None
    story_recover: bool = False
    consume_id: int | None = None
    experience: int = 0
    magic_action: str = ""
    magic_target: int | None = None
    mana: int = 0
    magic_ready: bool = False
    magic_focused: bool = False
    camp_action: str = ""
    camp_target_id: int | None = None
    camp_upgrade_level: int = 0
    raid_action: str = ""
    raid_target: int | None = None
    personal_action: str = ""
    personal_target: int | None = None


class Policy(Protocol):
    def choose(self, observation: Observation) -> tuple[str, int | None]: ...


class BaselinePolicyV7:
    def choose(self, observation):
        o = observation
        if o.adventure_ready:
            return "adventure_claim", o.adventure_id
        if o.reward_ready:
            return "claim", None
        if o.busy:
            return "wait", None
        if o.consume_id:
            return "consume", o.consume_id
        if o.product_urgent and o.product_id:
            return "shop", o.product_id
        if o.health < 10:
            return ("adventure", o.template_id) if o.template_id else ("wait", None)
        # Preserve distinct starting jobs, then every role learns the full loop.
        if o.role == "miner" and o.turn == 0:
            return ("mine", None) if o.energy >= 10 else ("wait", None)
        if o.role == "trader" and o.turn <= 1 and o.inventory_id:
            return "list", o.inventory_id
        if o.turn >= 2 and o.camp == "NONE":
            return "camp", o.camp_target
        if o.rank_action and o.rank_target:
            return o.rank_action, o.rank_target
        if o.equip_id:
            return "equip", o.equip_id
        if o.disposal_id:
            return "sell", o.disposal_id
        if o.upgrade_action and o.upgrade_id:
            return o.upgrade_action, o.upgrade_id
        if o.training_needed and o.skill_points > 0 and o.ore >= 10:
            return "train", None
        if not o.armed:
            if o.offer_id:
                return "buy", o.offer_id
            if o.blueprint_id:
                return "stock", o.blueprint_id
        if o.story_action and o.story_target:
            return o.story_action, o.story_target
        if o.story_recover:
            return "wait", None
        if o.boss_key and o.energy >= 25:
            return "boss", None
        if (o.needs_ore or o.quest_mine) and o.energy >= 10:
            return "mine", None
        if o.quest_hunt and o.hunt_key and o.energy >= 15:
            return "hunt", None
        if o.product_id and not o.product_urgent:
            return "shop", o.product_id
        if o.role == "trader":
            if o.inventory_id:
                return "list", o.inventory_id
            if o.offer_id:
                return "buy", o.offer_id
            if o.template_id and o.turn % 4 == 3:
                return "adventure", o.template_id
            if o.blueprint_id:
                return "stock", o.blueprint_id
        if o.template_id and (o.turn % 5 == 4 or o.health < o.max_health // 2):
            return "adventure", o.template_id
        if o.ore < 50 and o.energy >= 10:
            return "mine", None
        if o.role == "miner" and o.turn % 4 == 0 and o.energy >= 10:
            return "mine", None
        if o.armed and o.hunt_key and o.energy >= 15:
            return "hunt", None
        if o.inventory_id:
            return "list", o.inventory_id
        if o.template_id:
            return "adventure", o.template_id
        if o.offer_id:
            return "buy", o.offer_id
        if o.blueprint_id:
            return "stock", o.blueprint_id
        if o.energy >= 10:
            return "mine", None
        return "wait", None


class BaselinePolicyV8(BaselinePolicyV7):
    def choose(self,observation):
        o=observation
        if not o.busy and not o.adventure_ready and not o.reward_ready and o.health>=10 and not o.consume_id and not o.product_urgent:
            if o.magic_action:return o.magic_action,o.magic_target
        return super().choose(o)


class BaselinePolicyV9(BaselinePolicyV8):
    def choose(self,o):
        if o.camp_action and not o.busy and not o.adventure_ready and not o.reward_ready and o.health>=10 and o.energy>=25 and not o.product_urgent:
            return o.camp_action,o.camp_target_id
        return super().choose(o)


class BaselinePolicyV10(BaselinePolicyV9):
    def choose(self,o):
        if o.raid_action and not o.busy and not o.adventure_ready and not o.reward_ready and not o.product_urgent:
            return o.raid_action,o.raid_target
        return super().choose(o)


class BaselinePolicy(BaselinePolicyV10):
    def choose(self,o):
        if o.personal_action and not o.busy and not o.adventure_ready and not o.reward_ready:
            return o.personal_action,o.personal_target
        return super().choose(o)


# Armed residents keep two training payments and reject marginal/expensive swaps.
UPGRADE_ORE_RESERVE = 20
MAX_ORE_PER_DAMAGE = 40


def choose_upgrade(stock, offers, damage, ore):
    candidates = []
    minimum_gain = max(3, math.ceil(damage / 10))
    for action, entries in (("stock", stock), ("buy", offers)):
        for entry in entries:
            weapon = entry if action == "stock" else entry.blueprint
            price = entry.base_value if action == "stock" else entry.market_price
            gain = weapon.damage - damage
            if (gain >= minimum_gain and 0 < price <= ore - UPGRADE_ORE_RESERVE
                    and price <= gain * MAX_ORE_PER_DAMAGE):
                candidates.append((Fraction(price, gain), -gain, price, action, entry.pk, entry))
    if not candidates:
        return None
    choice = min(candidates, key=lambda c: c[:5])
    return choice[3], choice[5], choice[2], -choice[1]


def health_needed(profile, monster, damage):
    rounds = math.ceil(monster["life"] / max(1, damage - monster["weapon_prot"]))
    incoming = max(1, monster["strength"] - profile.effective_protection(monster.get("damage_type", "weapon")))
    return (rounds - 1) * incoming + 10


def health_at_rest(profile,monster,damage):
    from .magic import combat_plan,survival_health
    plan=profile._bot_magic_plan if hasattr(profile,'_bot_magic_plan') else combat_plan(profile)
    return survival_health(profile,monster,plan,mana=profile.max_mana) if plan else health_needed(profile,monster,damage)


def safe_to_hunt(profile, monster, damage):
    from .magic import combat_plan,survival_health
    plan=profile._bot_magic_plan if hasattr(profile,'_bot_magic_plan') else combat_plan(profile)
    if profile.prepared_magic_id:
        return bool(plan and profile.current_mana>=plan.cost and profile.current_health>=survival_health(profile,monster,plan))
    return profile.current_health >= health_needed(profile, monster, damage)


@transaction.atomic
def tick_bot(profile, policy=None):
    from .camp_progression import RANKS, available_rank, quest_complete, accept_camp_quest, promote_in_camp
    from .locations import LOCATIONS
    from .economy import start_adventure, claim_adventure, purchase_product
    profile = type(profile).objects.select_for_update().get(pk=profile.pk)
    from .worlds import playable
    if not playable(profile):return "wait",False
    if not profile.is_bot:
        raise ValueError("Only designated bot profiles may run bot policies")
    profile.bot_last_tick = timezone.now()
    profile.save(update_fields=["bot_last_tick"])
    game.refresh_player(profile)
    from .story_quests import bot_story_plan, accept_story, activate_story, claim_story, choose_story, travel_story
    story = bot_story_plan(profile)
    combat_equipment = profile.bot_role != "trader" or any(kind in {"hunt", "boss"} for kind, _ in story.events)
    from .magic import combat_plan
    profile._bot_magic_plan=combat_plan(profile)
    inventory = list(profile.inventory.select_related("blueprint").order_by("pk"))
    equipped = next((item for item in inventory if item.is_equipped and item.equipped_slot == "weapon"), None)
    damage = equipped.blueprint.damage if equipped else 0
    spare = [item for item in inventory if not item.is_market_listed and not item.is_equipped and item.pk!=profile.prepared_magic_id and item.blueprint_id not in story.item_ids]
    item = spare[0] if spare else None
    equipment = max((item for item in spare if item.blueprint.kind == "weapon" and item.blueprint.required_strength <= profile.strength and item.blueprint.required_dexterity <= profile.dexterity and item.blueprint.damage > damage), key=lambda item: item.blueprint.damage, default=None)
    if not equipment:
        worn = next((i.blueprint.weapon_prot for i in inventory if i.is_equipped and i.equipped_slot == 'armor'), 0)
        from .equipment import allowed
        equipment = max((i for i in spare if i.blueprint.kind == 'armor' and i.blueprint.weapon_prot > worn and allowed(profile,i.blueprint)), key=lambda i:i.blueprint.weapon_prot, default=None)
    from .economic_ledger import refills_remaining
    energy_refills_left = refills_remaining(profile)
    consumable = next((i for i in spare if i.blueprint.kind == 'consumable' and ((i.blueprint.heal_amount and profile.current_health < profile.max_health // 2) or (i.blueprint.energy_amount and profile.current_energy < 15 and energy_refills_left))), None)
    stock = ItemBluePrint.objects.filter(merchant=True, kind='weapon', weapon_type__in=['onehand','twohand'], min_level__lte=profile.level, required_camp__in=['',profile.camp], min_camp_tier__lte=profile.camp_tier, required_dexterity__lte=profile.dexterity, base_value__gt=0, base_value__lte=profile.ore_balance, required_strength__lte=profile.strength)
    if combat_equipment:
        stock = stock.filter(damage__gt=damage)
    offers = OwnedItem.objects.filter(blueprint__kind='weapon', blueprint__weapon_type__in=['onehand','twohand'], blueprint__min_level__lte=profile.level, blueprint__required_camp__in=['',profile.camp], blueprint__min_camp_tier__lte=profile.camp_tier, is_market_listed=True, owner__world_id=profile.world_id, market_price__gt=0, market_price__lte=profile.ore_balance, blueprint__required_strength__lte=profile.strength).filter(market_price__lte=F("blueprint__base_value") * 1.2).exclude(owner=profile).select_related("blueprint")
    if combat_equipment:
        offers = offers.filter(blueprint__damage__gt=damage)
    upgrade = None
    if equipped and combat_equipment:
        upgrade = choose_upgrade(stock, offers, damage, profile.ore_balance)
        stock = upgrade[1] if upgrade and upgrade[0] == "stock" else None
        offer = upgrade[1] if upgrade and upgrade[0] == "buy" else None
    else:
        stock = stock.order_by("base_value", "pk").first()
        offer = offers.order_by("market_price", "pk").first()
    if len(inventory) >= 6:
        stock = offer = upgrade = None
    # Sell obsolete weapons through the same NPC service as a human player.
    # Keep stronger future gear, listed goods and the trader's merchandise.
    disposal = min((i for i in spare if i.blueprint.kind == "weapon" and i.blueprint.damage < damage),
                   key=lambda i: (i.blueprint.damage, i.pk), default=None) if equipped and combat_equipment else None
    if len(inventory) >= 5:
        disposal = next((i for i in spare if i.blueprint.kind in {'material','misc'} and i.blueprint.tradeable), disposal)
    run = profile.adventures.filter(claimed_at__isnull=True).first()
    template = AdventureTemplate.objects.filter(enabled=True, level__lte=profile.level, energy_cost__lte=profile.current_energy).order_by("-experience_reward", "duration_seconds", "pk").first()
    # Delivery stock is bought through the ordinary services and reserved from sale/equip.
    delivery_needed = False
    if story.missing_items and len(inventory) < 6:
        needed = ItemBluePrint.objects.filter(pk__in=story.missing_items).order_by('base_value', 'pk').first()
        if needed:
            delivery_needed = True
            if needed.base_value > 0 and needed.base_value <= profile.ore_balance:
                stock, offer, upgrade = needed, None, None
                story = type(story)('stock', needed.pk, story.goal, story.option, story.events, story.item_ids, story.missing_items)
    rank = None
    rank_action = ""
    quest_mine = any(kind == 'mine' for kind, _ in story.events)
    needs_ore = delivery_needed and not story.action
    hunt_goals = [key for kind, key in story.events if kind == 'hunt']
    boss_goals = [key for kind, key in story.events if kind == 'boss']
    training = "strength"
    training_needed = profile.skill_points > 0 and profile.strength < 15 + profile.level * 4
    quest = profile.camp_quests.filter(promoted_at__isnull=True).first()
    if quest:
        rank = next((r for r in RANKS if r.key == quest.rank_key and available_rank(profile, r)), None)
        if rank:
            if quest_complete(quest, rank):
                needs_ore = needs_ore or profile.ore_balance < rank.cost
                if getattr(profile, rank.attribute) < rank.attribute_value:
                    training, training_needed = rank.attribute, True
                elif profile.level >= rank.level and not needs_ore:
                    rank_action = "promote"
            for goal in rank.objectives:
                if quest.progress.get(goal.event, 0) >= goal.count:
                    continue
                kind, _, key = goal.event.partition(":")
                if kind == "mine": quest_mine = True
                elif kind == "hunt": hunt_goals.append(key)
                elif kind == "boss": boss_goals.append(key)
                elif kind == "train": training, training_needed = key, True
    elif profile.camp != "NONE" and profile.bot_turn >= 2:
        candidates=[r for r in RANKS if available_rank(profile,r)]
        from .magic import MAGE_RANKS
        wants_magic=profile.bot_role!='trader' and profile.pk%2==0
        rank=next((r for r in candidates if r.key in MAGE_RANKS),None) if wants_magic else None
        rank=rank or next(iter(candidates),None)
        if rank:
            rank_action = "accept"
    story_training = next((key for kind, key in story.events if kind == 'train'), None)
    if story_training:
        training, training_needed = story_training, True
    hunt_options = []
    for location in LOCATIONS:
        if location.route != "hunt_page" or not location.accessible(profile):
            continue
        for key in location.monsters:
            monster = game.BESTIARY[key]
            if safe_to_hunt(profile, monster, profile.strength + damage):
                hunt_options.append((key in hunt_goals, monster["exp_reward"], key, location.key))
    hunt = max(hunt_options, default=None)
    boss_key = None
    for key in boss_goals:
        boss = game.BOSSES[key]
        last = BossAttempt.objects.filter(profile=profile, boss_key=key).first()
        if profile.level >= boss.level and (not last or timezone.now() >= last.created_at + timezone.timedelta(minutes=boss.cooldown_minutes)) and safe_to_hunt(profile, boss.monster, profile.strength + damage):
            boss_key = key
            break
    # Rest toward a reachable story fight instead of spending each recovered point
    # on lower-value fallback hunts forever. Impossible-at-full-health fights still
    # permit training/leveling/gear upgrades rather than causing permanent rest.
    story_fights = []
    for kind, key in story.events:
        if kind == 'hunt' and any(loc.accessible(profile) and key in loc.monsters for loc in LOCATIONS):
            story_fights.append((game.BESTIARY[key], 15))
        elif kind == 'boss' and profile.level >= game.BOSSES[key].level:
            story_fights.append((game.BOSSES[key].monster, 25))
    story_recover = bool(story_fights) and not any(
        safe_to_hunt(profile, monster, profile.strength + damage) and profile.current_energy >= energy
        for monster, energy in story_fights
    ) and any(health_at_rest(profile, monster, profile.strength + damage) <= profile.max_health for monster, _ in story_fights)
    products = StoreProduct.objects.filter(enabled=True, level__lte=profile.level, price__lte=profile.premium_balance).select_related("blueprint").order_by("price", "pk")
    product = next((p for p in products if (p.kind == "health" and profile.current_health < max(10, profile.max_health // 2)) or (p.kind == "energy" and profile.current_energy < 15 and energy_refills_left)), None)
    urgent = product is not None
    if not product and len(inventory) < 6:
        product = next((p for p in products if p.kind == "weapon" and p.blueprint and p.blueprint.required_strength <= profile.strength and p.blueprint.damage > damage and not any(i.blueprint_id == p.blueprint_id for i in inventory)), None)
    camp_target = (profile.pk - 1) % 3 + 1
    from .magic import bot_magic_plan,combat_plan
    target_monster=next((game.BESTIARY[key] for key in hunt_goals if key in game.BESTIARY),None)
    magic_action,magic_target=bot_magic_plan(profile,inventory,target_monster)
    active_magic=combat_plan(profile)
    from .camp_guilds import guild_cards,UPGRADES
    camp_action="";camp_target_id=None;camp_upgrade_level=0
    if profile.camp!="NONE" and profile.bot_turn%17==0:
        card=guild_cards(profile)
        if card:
            camp_upgrade=next((row for row in card["upgrades"] if row["can_buy"]),None)
            if camp_upgrade:
                camp_action="camp_upgrade";camp_target_id=list(UPGRADES).index(camp_upgrade["key"])+1;camp_upgrade_level=camp_upgrade["level"]
            elif profile.ore_balance>=250 and card["guild"].treasury<100:
                camp_action="camp_donate"
    from .camp_raids import raid_card
    raid_action="";raid_target=None
    if profile.camp!="NONE" and profile.level>=3:
        raid_status=raid_card(profile)
        pending=next(iter(raid_status['rewards']),None)
        if pending:raid_action='raid_claim';raid_target=pending.pk
        elif profile.bot_turn%13==0:
            raid=raid_status['raid']
            if not raid:raid_action='raid_rally'
            elif raid_status['can_attack'] and profile.current_health>=min(profile.max_health,(raid.attack+10)*3+10) and (not profile.prepared_magic_id or (active_magic and profile.current_mana>=active_magic.cost)):
                raid_action='raid_strike';raid_target=raid.pk
    from .challenges import bot_personal_plan
    personal_action,personal_target=bot_personal_plan(profile)
    obs = Observation(
        energy=profile.current_energy, ore=profile.ore_balance, busy=profile.is_busy, experience=profile.experience,
        reward_ready=profile.action_end_time is not None and profile.action_end_time <= timezone.now(),
        offer_id=offer.pk if offer else None, inventory_id=item.pk if item else None,
        blueprint_id=stock.pk if stock else None, equip_id=equipment.pk if equipment else None,
        armed=equipped is not None, role=profile.bot_role, skill_points=profile.skill_points,
        strength=profile.strength, health=profile.current_health, max_health=profile.max_health,
        premium=profile.premium_balance, turn=profile.bot_turn, camp=profile.camp,
        camp_target=camp_target, rank_target=RANKS.index(rank) + 1 if rank else None,
        rank_action=rank_action, needs_ore=needs_ore, training=training,
        training_needed=training_needed, quest_mine=quest_mine,
        quest_hunt=bool(hunt and hunt[0]), boss_key=boss_key, hunt_key=hunt[2] if hunt else None, hunt_location=hunt[3] if hunt else None,
        adventure_id=run.pk if run else None, adventure_ready=bool(run and timezone.now() >= run.ends_at),
        template_id=template.pk if template else None, product_id=product.pk if product else None,
        product_urgent=urgent,
        upgrade_action=upgrade[0] if upgrade else "",
        upgrade_id=upgrade[1].pk if upgrade else None,
        upgrade_cost=upgrade[2] if upgrade else 0,
        upgrade_gain=upgrade[3] if upgrade else 0,
        ore_reserve=UPGRADE_ORE_RESERVE if equipped and combat_equipment else 0,
        disposal_id=disposal.pk if disposal else None,
        story_action=story.action, story_target=story.target, story_recover=story_recover,
        consume_id=consumable.pk if consumable else None,
        personal_action=personal_action,personal_target=personal_target,
        raid_action=raid_action,raid_target=raid_target,
        camp_action=camp_action,camp_target_id=camp_target_id,camp_upgrade_level=camp_upgrade_level,
        magic_action=magic_action,magic_target=magic_target,mana=profile.current_mana,magic_ready=bool(active_magic and profile.current_mana>=active_magic.cost),magic_focused=bool(profile.prepared_magic_id),
    )
    policy_version = "baseline-11" if policy is None or type(policy) is BaselinePolicy else "external-unknown"
    action, target = (policy or BaselinePolicy()).choose(obs)
    if not isinstance(action, str) or (target is not None and (type(target) is not int or target <= 0)):
        record_decision(profile, obs, "rejected", None, False, policy_version)
        return "rejected", False
    story_services = {'story_accept': accept_story, 'story_start': activate_story, 'story_claim': claim_story}
    from .magic import learn_circle,prepare_magic,purchase_magic
    from .camp_guilds import donate_to_camp,upgrade_camp,UPGRADES
    from .camp_raids import rally_camp_raid,strike_camp_raid,claim_camp_raid
    from .challenges import accept_challenge,claim_challenge,claim_achievement,ACHIEVEMENTS
    if action==obs.personal_action and target==obs.personal_target and action in {'challenge_accept','challenge_claim','achievement_claim'}:
        success=bool(accept_challenge(profile,('daily','weekly')[target-1]) if action=='challenge_accept' else claim_challenge(profile,target) if action=='challenge_claim' else claim_achievement(profile,list(ACHIEVEMENTS)[target-1]))
    elif action==obs.raid_action and target==obs.raid_target and action in {'raid_rally','raid_strike','raid_claim'}:
        success=bool(rally_camp_raid(profile) if action=='raid_rally' else strike_camp_raid(profile,target,uuid4()) if action=='raid_strike' else claim_camp_raid(profile,target))
    elif action=='camp_donate' and obs.camp_action==action and target is None:
        success=donate_to_camp(profile,10,uuid4())
    elif action=='camp_upgrade' and obs.camp_action==action and target==obs.camp_target_id:
        success=upgrade_camp(profile,list(UPGRADES)[target-1],obs.camp_upgrade_level)
    elif action==obs.magic_action and target==obs.magic_target and action in {'learn_circle','prepare_magic','buy_magic','clear_magic'}:
        success=bool(learn_circle(profile) if action=='learn_circle' else prepare_magic(profile,None) if action=='clear_magic' else prepare_magic(profile,target) if action=='prepare_magic' else purchase_magic(profile,target))
    elif action in story_services and action == story.action and target == story.target:
        success = bool(story_services[action](profile, target))
    elif action == 'story_talk' and action == story.action and target == story.target:
        success = choose_story(profile, target, story.goal, story.option)
    elif action == 'story_travel' and action == story.action and target == story.target:
        success = travel_story(profile, target, story.goal)
    elif action == "claim" and obs.reward_ready:
        success = game.claim_ore_reward(profile)
    elif action == "mine":
        success = game.start_mining(profile, 15)
    elif action == "equip" and equipment and target == equipment.pk:
        success = game.equip_item(profile, equipment)
    elif action == "consume" and consumable and target == consumable.pk:
        success = game.use_item(profile, consumable)
    elif action == "sell" and disposal and target == disposal.pk:
        success = game.sell_item_from_npc(profile, disposal)
    elif action == "train" and obs.training_needed:
        success = game.train_attribute(profile, training)
    elif action == "hunt" and hunt and target is None:
        success = game.execute_hunt(profile, hunt[2], hunt[3]) is not False
    elif action == "boss" and boss_key and target is None:
        success = game.execute_boss(profile, boss_key) is not False
    elif action == "camp" and target == camp_target:
        success = game.choose_camp(profile, ("OLD_CAMP", "NEW_CAMP", "SWAMP_CAMP")[camp_target - 1])
    elif action in ("accept", "promote") and action == rank_action and rank and target == obs.rank_target:
        success = (accept_camp_quest if action == "accept" else promote_in_camp)(profile, rank.key)
    elif action == "adventure" and template and target == template.pk:
        success = bool(start_adventure(profile, template.pk))
    elif action == "adventure_claim" and run and target == run.pk:
        success = claim_adventure(profile, run.pk)
    elif action == "shop" and product and target == product.pk:
        success = bool(purchase_product(profile, product.pk, uuid4()))
    elif action == "list" and item and target == item.pk:
        price = max(1, min(game.MAX_MARKET_PRICE, item.blueprint.base_value * 110 // 100))
        success = game.list_item_on_market(profile, item, price)
    elif action == "buy" and offer and target == offer.pk:
        success = game.buy_item_on_market(profile, offer)
    elif action == "stock" and stock and target == stock.pk:
        success = game.buy_item_from_npc(profile, stock)
    elif action == "wait":
        success = True
    else:
        record_decision(profile, obs, "rejected", None, False, policy_version)
        return "rejected", False
    if success and action != "wait":
        profile.refresh_from_db()
        profile.bot_turn += 1
        profile.save(update_fields=["bot_turn"])
    record_decision(profile, obs, action, target, success, policy_version)
    from .community import bot_conversation
    bot_conversation(profile)
    return action, success
