from .barrier import source_games,region_ids,joined,region
"""Autonomous local players. Policies see immutable data and an action allowlist.

No policy receives ORM objects, resource grants or an administrator capability.
One tick performs one ordinary player action, or rests for real-time recovery.
"""
from dataclasses import dataclass, replace
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
    craft_action: str = ""
    craft_target: int | None = None
    market_action: str = ""
    market_target: int | None = None
    market_price: int = 0
    forge_action: str = ""
    forge_target: int | None = None
    forge_level: int = 0
    patrol_depth: int | None = None
    ammo_id: int | None = None
    ammo_blocked: bool = False
    resupply_ready: bool = False
    membership_ready: bool = True
    personality: str = ""
    finance_id: int | None = None
    finance_old_id: int | None = None
    finance_price: int = 0


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


class BaselinePolicyV11(BaselinePolicyV10):
    def choose(self,o):
        if o.personal_action and not o.busy and not o.adventure_ready and not o.reward_ready:
            return o.personal_action,o.personal_target
        return super().choose(o)


class BaselinePolicyV12(BaselinePolicyV11):
    def choose(self,o):
        if o.craft_action and not o.busy and not o.adventure_ready and not o.reward_ready:
            return o.craft_action,o.craft_target
        return super().choose(o)


class BaselinePolicyV13(BaselinePolicyV12):
    def choose(self,o):
        if o.market_action and not o.busy and not o.adventure_ready and not o.reward_ready:
            return o.market_action,o.market_target
        return super().choose(o)


class BaselinePolicyV14(BaselinePolicyV13):
    pass


class BaselinePolicyV15(BaselinePolicyV14):
    def choose(self,o):
        if (o.forge_action or o.patrol_depth) and not o.busy and not o.adventure_ready and not o.reward_ready:
            if o.consume_id:return 'consume',o.consume_id
            if o.equip_id:return 'equip',o.equip_id
            if o.forge_action:return o.forge_action,o.forge_target
            if o.patrol_depth and o.energy>=20:return 'patrol',o.patrol_depth
        return super().choose(o)


class BaselinePolicyV16(BaselinePolicyV15):
    def choose(self,o):
        if o.ammo_id and not o.busy and not o.adventure_ready and not o.reward_ready and o.health>=10 and not o.consume_id and not o.product_urgent:
            return 'ammo',o.ammo_id
        return super().choose(o)


class BaselinePolicyV17(BaselinePolicyV16):
    def choose(self,o):
        # Optional patrols must not starve an unfinished personal story.
        if o.story_recover or (o.turn % 5 and (o.story_action or o.quest_hunt or o.quest_mine or o.boss_key)):
            o = replace(o,patrol_depth=None)
        return super().choose(o)


class BaselinePolicyV18(BaselinePolicyV17):
    def choose(self,o):
        if o.training_needed and o.skill_points>0:o=replace(o,patrol_depth=None)
        return super().choose(o)


class BaselinePolicyV19(BaselinePolicyV18):
    def choose(self,o):
        if not o.busy and not o.adventure_ready and not o.reward_ready and o.health>=10 and not o.consume_id and not o.product_urgent:
            if o.equip_id:return 'equip',o.equip_id
            if o.finance_id:return 'finance',o.finance_id
            if o.inventory_id and not o.story_recover:return 'list',o.inventory_id
        return super().choose(o)

class BaselinePolicyV20(BaselinePolicyV19):
    def choose(self,o):
        choice=super().choose(o)
        safe=not o.busy and not o.adventure_ready and not o.reward_ready and not o.consume_id and not o.story_recover
        # Premium-focused residents actually use their useful purchases during a campaign.
        if safe and o.personality=='patron' and o.product_id and o.turn%3==1 and choice[0] not in {'equip','camp','accept','promote'}:return 'shop',o.product_id
        if safe and o.personality in {'casual','adventurer','social'} and o.turn%11==5 and o.template_id and choice[0] in {'story_accept','story_start','story_talk','story_travel'}:return 'adventure',o.template_id
        if choice[0] in {'mine','hunt','adventure'} and safe and not (o.story_action or o.quest_hunt or o.quest_mine or o.boss_key or o.needs_ore):
            if o.personality=='prospector' and o.energy>=10 and o.turn%3!=2:return 'mine',None
            if o.personality in {'casual','adventurer','social'} and o.template_id:return 'adventure',o.template_id
            if o.personality=='grinder' and o.armed and o.hunt_key and o.energy>=15:return 'hunt',None
        return choice

class BaselinePolicyV21(BaselinePolicyV20):
    def choose(self,o):
        if o.resupply_ready and not (o.busy or o.adventure_ready or o.reward_ready or o.consume_id):return 'camp_supply',None
        if o.camp=='NONE' and not o.membership_ready:
            # Continue the prologue through ordinary services before choosing a camp.
            return super().choose(replace(o,camp='PROLOGUE_PENDING'))
        return super().choose(o)

class BaselinePolicyV22(BaselinePolicyV21):
    def choose(self,o):
        safe=not (o.busy or o.adventure_ready or o.reward_ready or o.consume_id or o.product_urgent) and o.health>=10
        if safe and o.camp_action=='choose_faction':return o.camp_action,o.camp_target_id
        if safe and o.rank_action and o.rank_target:return o.rank_action,o.rank_target
        return super().choose(o)


class BaselinePolicy(BaselinePolicyV22):pass


# Armed residents keep two training payments and reject marginal/expensive swaps.
UPGRADE_ORE_RESERVE = 20
MAX_ORE_PER_DAMAGE = 40


def choose_upgrade(stock, offers, damage, ore, profile=None):
    candidates = []
    minimum_gain = max(3, math.ceil(damage / (30 if profile else 10)))
    for action, entries in (("stock", stock), ("buy", offers)):
        for entry in entries:
            weapon = entry if action == "stock" else entry.blueprint
            price = entry.base_value if action == "stock" else entry.market_price
            from .market_intelligence import score
            gain = (score(profile,entry) if profile else entry.effective_stats["damage"] if action == "buy" else weapon.damage) - damage
            if (gain >= minimum_gain and 0 < price <= ore - UPGRADE_ORE_RESERVE
                    and price <= gain * MAX_ORE_PER_DAMAGE):
                candidates.append((Fraction(price, gain), -gain, price, action, entry.pk, entry))
    if not candidates:
        return None
    choice = min(candidates, key=lambda c: c[:5])
    return choice[3], choice[5], choice[2], -choice[1]


def health_needed(profile, monster, damage):
    from .equipment import physical_survival_health
    return physical_survival_health(profile,monster,damage)


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


from .realms import profile_scope,camps as realm_camps

@profile_scope
def tick_bot(profile, policy=None, *, lease=None, force_active=False):
    from .camp_progression import RANKS, available_rank, quest_complete, accept_camp_quest, promote_in_camp
    from .faction_advancement import RANKS as ADVANCED_RANKS
    RANKS=RANKS+ADVANCED_RANKS
    from .locations import LOCATIONS
    from .economy import start_adventure, claim_adventure, purchase_product
    profile = type(profile).objects.select_related('world').get(pk=profile.pk)
    from .worlds import playable
    if not playable(profile):return "wait",False
    if not profile.is_bot:
        raise ValueError("Only designated bot profiles may run bot policies")
    from .bot_personalities import due,in_session,simulate_purchase
    if not force_active:
        if profile.world.bot_personality_cycles and not in_session(profile):return "offline",True
        if not due(profile):return "idle",True
        with transaction.atomic():
            if lease is not None:lease.fence()
            simulate_purchase(profile)
    game.refresh_player(profile)
    from .story_quests import bot_story_plan, accept_story, activate_story, claim_story, choose_story, travel_story
    story = bot_story_plan(profile)
    from .finale import finale_ready
    final_goal = finale_ready(profile) and not hasattr(profile, "campaign_completion")
    combat_equipment = True
    from .magic import combat_plan
    profile._bot_magic_plan=combat_plan(profile)
    inventory = list(profile.inventory.exclude(blueprint__kind="quest",blueprint__tradeable=False).select_related("blueprint").order_by("pk"))
    equipped = next((item for item in inventory if item.is_equipped and item.equipped_slot == "weapon"), None)
    damage = equipped.effective_stats['damage'] if equipped else 0
    from .equipment import combat_values,allowed
    combat_damage=combat_values(profile)[0]
    ammo_blocked=False;ammo_stock=None;ammo_kind=None
    if equipped and equipped.blueprint.weapon_type in {'bow','crossbow'}:
        ammo_kind='arrow' if equipped.blueprint.weapon_type=='bow' else 'bolt'
        ammo_blocked=not profile.prepared_magic_id and not any(i.blueprint.kind=='ammo' and i.blueprint.original_stats.get('ammo_type')==ammo_kind and not i.is_market_listed for i in inventory)
        if ammo_blocked:
            choices=ItemBluePrint.objects.filter(kind='ammo',merchant=True,original_stats__ammo_type=ammo_kind,base_value__gte=0,base_value__lte=profile.ore_balance).order_by('base_value','pk')
            ammo_stock=next((bp for bp in choices if allowed(profile,bp)),None)
    from .models import CraftRecipe
    from .crafting import valid_recipe,interested
    reserved_materials={i['blueprint'] for r in CraftRecipe.objects.filter(enabled=True) if valid_recipe(r) and getattr(profile,r.discipline+'_skill')>=r.skill and interested(profile,r) for i in r.ingredients} if profile.smithing_skill or profile.alchemy_skill else set()
    reserved_materials.update(i.blueprint_id for i in inventory if ammo_kind and i.blueprint.kind=='ammo' and i.blueprint.original_stats.get('ammo_type')==ammo_kind)
    spare = [item for item in inventory if not item.is_market_listed and not item.is_equipped and item.pk!=profile.prepared_magic_id and item.blueprint_id not in story.item_ids and item.blueprint_id not in reserved_materials and item.blueprint.catalog_key!='rune-dust']
    from .market_intelligence import state,sale_candidate,retention,score,usable,fists
    market=state(profile.world_id)
    retained=retention(profile,inventory,set(story.item_ids)|reserved_materials)
    item=sale_candidate(profile,inventory,set(story.item_ids)|reserved_materials,market)
    equipment=None
    for candidate in sorted(spare,key=lambda i:score(profile,i),reverse=True):
        if not candidate.blueprint.equippable or not usable(profile,candidate.blueprint):continue
        worn=[i for i in inventory if i.is_equipped and i.blueprint.kind==candidate.blueprint.kind]
        slots=2 if candidate.blueprint.kind=='ring' else 1
        baseline=min((score(profile,i) for i in worn),default=fists(profile) if candidate.blueprint.kind=='weapon' else 0)
        if (len(worn)<slots and candidate.blueprint.kind!='weapon') or score(profile,candidate)>baseline:
            equipment=candidate;break
    from .economic_ledger import refills_remaining
    energy_refills_left = refills_remaining(profile)
    consumable = next((i for i in spare if i.blueprint.kind == 'consumable' and ((i.blueprint.heal_amount and profile.current_health < profile.max_health // 2) or (i.blueprint.energy_amount and profile.current_energy < 15 and energy_refills_left))), None)
    from .faction_choice import equipment_camps
    equipment_factions=equipment_camps(profile)
    stock = ItemBluePrint.objects.filter(source_game__in=source_games(profile),merchant=True, kind='weapon', weapon_type__in=([equipped.blueprint.weapon_type] if equipped and equipped.blueprint.weapon_type in {'bow','crossbow'} else ['onehand','twohand']), min_level__lte=profile.level, required_camp__in=equipment_factions, min_camp_tier__lte=profile.camp_tier, required_dexterity__lte=profile.dexterity, base_value__gt=0, base_value__lte=profile.ore_balance, required_strength__lte=profile.strength)
    if combat_equipment:
        stock = stock.filter(damage__gt=damage)
    offers = OwnedItem.objects.filter(blueprint__kind='weapon', blueprint__weapon_type__in=([equipped.blueprint.weapon_type] if equipped and equipped.blueprint.weapon_type in {'bow','crossbow'} else ['onehand','twohand']), blueprint__min_level__lte=profile.level, blueprint__required_camp__in=equipment_factions, blueprint__min_camp_tier__lte=profile.camp_tier, is_market_listed=True, owner__user__is_active=True, owner__world_id__in=region_ids(profile.world_id), market_price__gt=0, market_price__lte=profile.ore_balance, blueprint__required_strength__lte=profile.strength,blueprint__required_dexterity__lte=profile.dexterity).exclude(owner=profile).select_related("blueprint","owner")
    offers=[o for o in offers if o.market_price<=market.quote(o.owner,o).price]
    upgrade = None
    if equipped and combat_equipment:
        upgrade = choose_upgrade(stock, offers, score(profile,equipped), profile.ore_balance,profile)
        stock = upgrade[1] if upgrade and upgrade[0] == "stock" else None
        offer = upgrade[1] if upgrade and upgrade[0] == "buy" else None
    else:
        stock = next((b for b in stock.order_by("base_value", "pk") if score(profile,b)>=fists(profile)+5),None)
        offer = min((o for o in offers if score(profile,o)>=fists(profile)+5),key=lambda o:(o.market_price,o.pk),default=None)
    if len(inventory) >= 6:
        stock = offer = upgrade = None
    # Sell obsolete weapons through the same NPC service as a human player.
    # Keep stronger future gear, listed goods and the trader's merchandise.
    disposal = min((i for i in spare if i.pk not in retained and (not item or i.pk!=item.pk) and i.blueprint.tradeable and i.blueprint.kind == "weapon" and not i.is_protected and i.effective_stats["damage"] < damage),
                   key=lambda i: (i.effective_stats["damage"], i.pk), default=None) if equipped and combat_equipment else None
    if len(inventory) >= 5:
        disposal = next((i for i in spare if i.pk not in retained and (not item or i.pk!=item.pk) and i.blueprint.kind in {'material','misc','ammo'} and i.blueprint.tradeable and not i.is_protected), disposal)
    run = profile.adventures.filter(claimed_at__isnull=True).first()
    from .adventures import choose_adventure
    template = choose_adventure(profile)
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
    if final_goal:boss_goals.append('sleeper_sanctum')
    training = "mana" if profile.camp=="FIRE_ORDER" and profile.camp_tier>=1 else "strength"
    training_needed = profile.skill_points > 0 and getattr(profile,training) < 15 + profile.level * 4
    quest = profile.camp_quests.filter(promoted_at__isnull=True).first()
    if quest:
        rank = next((r for r in RANKS if r.key == quest.rank_key and available_rank(profile, r)), None)
        if rank:
            if quest_complete(quest, rank):
                needs_ore = needs_ore or profile.ore_balance < rank.cost
                if getattr(profile, rank.attribute) < rank.attribute_value:
                    training, training_needed = ("dexterity" if profile.dexterity>profile.strength else "strength") if rank.attribute=="martial" else rank.attribute, True
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
        advanced_candidates=[r for r in candidates if r.key.startswith('ADV_')]
        if advanced_candidates:candidates=advanced_candidates
        from .magic import MAGE_RANKS
        wants_magic=profile.bot_role!='trader' and profile.pk%2==0
        rank=next((r for r in candidates if r.key in MAGE_RANKS),None) if wants_magic else None
        rank=rank or next(iter(candidates),None)
        if rank:
            rank_action = "accept"
    # Optional veteran lessons use earned points without delaying the campaign.
    if hasattr(profile,'campaign_completion') and not training_needed and profile.skill_points and equipped and profile.bot_turn % 7 == 0:
        skill=equipped.blueprint.weapon_type+'_skill'
        if getattr(profile,skill) < min(60,profile.level*2):
            training=skill;training_needed=True
    story_training = next((key for kind, key in story.events if kind == 'train'), None)
    if story_training:
        training, training_needed = story_training, True
    if final_goal and health_at_rest(profile,game.BOSSES["sleeper_sanctum"].monster,combat_damage) > profile.max_health:
        training, training_needed = "strength", True
        needs_ore = needs_ore or bool(profile.skill_points and profile.ore_balance < 10)
    hunt_options = []
    for location in LOCATIONS:
        if location.route != "hunt_page" or not location.accessible(profile):
            continue
        for key in location.monsters:
            monster = game.BESTIARY[key]
            if safe_to_hunt(profile, monster, combat_damage):
                hunt_options.append((key in hunt_goals, monster["exp_reward"], key, location.key))
    hunt = max(hunt_options, default=None)
    boss_key = None
    for key in boss_goals:
        boss = game.BOSSES[key]
        last = BossAttempt.objects.filter(profile=profile, boss_key=key).first()
        if profile.level >= boss.level and (not last or timezone.now() >= last.created_at + timezone.timedelta(minutes=boss.cooldown_minutes)) and safe_to_hunt(profile, boss.monster, combat_damage):
            boss_key = key
            break
    if ammo_blocked:
        hunt=None;boss_key=None
    # Rest toward a reachable story fight instead of spending each recovered point
    # on lower-value fallback hunts forever. Impossible-at-full-health fights still
    # permit training/leveling/gear upgrades rather than causing permanent rest.
    story_fights = [(game.BOSSES["sleeper_sanctum"].monster,25)] if final_goal else []
    for kind, key in story.events:
        if kind == 'hunt' and any(loc.accessible(profile) and key in loc.monsters for loc in LOCATIONS):
            story_fights.append((game.BESTIARY[key], 15))
        elif kind == 'boss' and profile.level >= game.BOSSES[key].level:
            story_fights.append((game.BOSSES[key].monster, 25))
    story_recover = not ammo_blocked and bool(story_fights) and not any(
        safe_to_hunt(profile, monster, combat_damage) and profile.current_energy >= energy
        for monster, energy in story_fights
    ) and any(health_at_rest(profile, monster, combat_damage) <= profile.max_health for monster, _ in story_fights)
    products = StoreProduct.objects.filter(enabled=True, level__lte=profile.level, price__lte=profile.premium_balance).select_related("blueprint").order_by("price", "pk")
    from .itemshop_rules import choose
    product,urgent=choose(profile,inventory,products,energy_refills_left)
    camp_target = (profile.pk - 1) % 3 + 1
    from .magic import bot_magic_plan,combat_plan
    target_monster=game.BOSSES[boss_goals[0]].monster if boss_goals else next((game.BESTIARY[key] for key in hunt_goals if key in game.BESTIARY),None)
    magic_action,magic_target=bot_magic_plan(profile,inventory,target_monster)
    active_magic=combat_plan(profile)
    from .camp_guilds import guild_cards,UPGRADES
    camp_action="";camp_target_id=None;camp_upgrade_level=0
    if profile.camp!="NONE" and profile.bot_turn%(7 if profile.bot_personality=='social' else 17)==0:
        card=guild_cards(profile)
        if card:
            camp_upgrade=next((row for row in card["upgrades"] if row["can_buy"]),None)
            if camp_upgrade:
                camp_action="camp_upgrade";camp_target_id=list(UPGRADES).index(camp_upgrade["key"])+1;camp_upgrade_level=camp_upgrade["level"]
            elif profile.ore_balance>=250 and card["guild"].treasury<100:
                camp_action="camp_donate"
    from .faction_choice import card as faction_card
    from .factions import FACTIONS
    faction_choice=faction_card(profile)
    if faction_choice and faction_choice['can_choose']:
        selected=faction_choice['options'][(profile.pk-1)%len(faction_choice['options'])]['key']
        camp_action='choose_faction';camp_target_id=[key for key,_ in FACTIONS].index(selected)+1
    from .camp_raids import raid_card
    raid_action="";raid_target=None
    if profile.camp!="NONE" and profile.level>=3:
        raid_status=raid_card(profile)
        pending=next(iter(raid_status['rewards']),None)
        if pending:raid_action='raid_claim';raid_target=pending.pk
        elif profile.bot_turn%(7 if profile.bot_personality=='social' else 13)==0:
            raid=raid_status['raid']
            if not raid:
                from .camp_privileges import privileges
                if privileges(profile)['can_rally']:raid_action='raid_rally'
            elif raid_status['can_attack'] and profile.current_health>=min(profile.max_health,(raid.attack+10)*3+10) and (not profile.prepared_magic_id or (active_magic and profile.current_mana>=active_magic.cost)):
                raid_action='raid_strike';raid_target=raid.pk
    if profile.level>=30 and profile.camp in {'OLD_CAMP','NEW_CAMP','SWAMP_CAMP'} and profile.bot_turn%13==0:
        from .sleeper import card as sleeper_card
        from .models import SleeperReward
        sc=sleeper_card(profile)
        if sc['race'] and sc['race'].state=='joined' and sc['race'].winner and sc['race'].winner.camp==profile.camp and not SleeperReward.objects.filter(race=sc['race'],account_id=profile.user_id).exists():
            if sc['siege'] and sc['siege'].strikes.filter(account_id=profile.user_id,damage__gt=0).exists():raid_action='sleeper_claim';raid_target=None
        elif sc['eligible'] and sc['guild_ready']:
            if not sc['siege']:raid_action='sleeper_rally';raid_target=None
            elif sc['can_strike'] and profile.current_health>=min(profile.max_health,460):raid_action='sleeper_strike';raid_target=sc['siege'].pk
    if joined(profile.world_id) and not profile.is_busy:
        from .barrier import alliance_card
        if alliance_card(profile)['can_promote']:raid_action='alliance_promote';raid_target=None
        from .locations import BY_KEY
        desired=next((BY_KEY.get(key) for kind,key in (*story.events,*(('boss',key) for key in boss_goals)) if kind in {'boss','travel'} and BY_KEY.get(key) and BY_KEY[key].universe!=region(profile).universe),None)
        if not desired and quest and quest.rank_key.startswith('ADV_'):
            desired=next((loc for loc in LOCATIONS if loc.universe!=region(profile).universe and any(key in loc.monsters for key in hunt_goals) and profile.level>=loc.level and profile.camp_tier>=loc.min_tier),None)
        if desired:
            from .models import World
            destination=World.objects.filter(pk__in=region_ids(profile.world_id),universe=desired.universe).first()
            if destination:raid_action='region_travel';raid_target=destination.pk
    from .challenges import bot_personal_plan
    personal_action,personal_target=bot_personal_plan(profile)
    from .crafting import bot_craft_plan
    craft_action,craft_target=bot_craft_plan(profile)
    from .market_policy import bot_market_plan
    market_action,market_target,market_price=bot_market_plan(profile,set(story.item_ids)|reserved_materials|{i.blueprint_id for i in inventory if i.blueprint.catalog_key=='rune-dust'},inventory=inventory,market=market)
    forge_action='';forge_target=None;forge_level=0;patrol_depth=None
    if not profile.is_busy:
        from .enhancements import upgrade_cost
        dust=sum(i.quantity for i in inventory if i.blueprint.catalog_key=='rune-dust' and not i.is_market_listed)
        for worn in (i for i in inventory if i.is_equipped):
            cost=upgrade_cost(worn)
            if cost and profile.ore_balance>=cost['ore']+20 and dust>=cost['dust']:
                forge_action='improve';forge_target=worn.pk;forge_level=worn.upgrade_level;break
        obsolete=next((i for i in spare if i.pk not in retained and (not item or i.pk!=item.pk) and i.can_salvage and (i.blueprint.kind!='weapon' or i.effective_stats['damage']<=damage)),None)
        if not forge_action and obsolete:forge_action='salvage';forge_target=obsolete.pk
        from .frontier import enemy,COOLDOWN,frontier_unlocked
        from .models import FrontierProgress
        progress=FrontierProgress.objects.filter(profile=profile).first() if frontier_unlocked(profile) else None
        if frontier_unlocked(profile) and not ammo_blocked and (not progress or not progress.last_attempt_at or timezone.now()>=progress.last_attempt_at+COOLDOWN):
            # Farm an easier unlocked challenge when the next guardian is unsafe.
            base_damage=combat_damage
            for depth in range(progress.unlocked if progress else 1,0,-1):
                foe=enemy(depth)
                if safe_to_hunt(profile,foe,base_damage):patrol_depth=depth;break
    if not forge_action and len(inventory)>=8 and not profile.is_busy:
        excess=next((i for i in spare if i.pk not in retained and (not item or i.pk!=item.pk) and i.can_salvage and (not equipment or i.pk!=equipment.pk)),None)
        if excess:forge_action='salvage';forge_target=excess.pk
    from .weapon_finance import plan as finance_plan
    financed=finance_plan(profile,inventory,market.merchants) if not upgrade and not equipment else None
    from .camp_privileges import resupply_available
    from .story_gates import missing as story_missing
    obs = Observation(
        resupply_ready=profile.ore_balance>=30 and (profile.current_energy<30 or profile.current_health<profile.max_health//2) and resupply_available(profile),
        membership_ready=not story_missing(profile),
        finance_id=financed.pk if financed else None,finance_old_id=equipped.pk if financed else None,finance_price=financed.base_value if financed else 0,
        personality=profile.bot_personality,
        ammo_id=ammo_stock.pk if ammo_stock else None,ammo_blocked=ammo_blocked,
        forge_action=forge_action,forge_target=forge_target,forge_level=forge_level,patrol_depth=patrol_depth,
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
        market_action=market_action,market_target=market_target,market_price=market_price,
        craft_action=craft_action,craft_target=craft_target,
        personal_action=personal_action,personal_target=personal_target,
        raid_action=raid_action,raid_target=raid_target,
        camp_action=camp_action,camp_target_id=camp_target_id,camp_upgrade_level=camp_upgrade_level,
        magic_action=magic_action,magic_target=magic_target,mana=profile.current_mana,magic_ready=bool(active_magic and profile.current_mana>=active_magic.cost),magic_focused=bool(profile.prepared_magic_id),
    )
    policy_version = "baseline-22" if policy is None or type(policy) is BaselinePolicy else "external-unknown"
    from .bot_policies import OllamaPolicy
    if isinstance(policy,OllamaPolicy) and obs.camp=="NONE" and not obs.membership_ready:
        policy=None;policy_version="baseline-22"
    action, target = (policy or BaselinePolicy()).choose(obs)
    policy_snapshot=policy.last_details if isinstance(policy,OllamaPolicy) else {}
    if isinstance(policy,OllamaPolicy):policy_version=policy.version
    with transaction.atomic():
        if lease is not None:lease.fence()
        if not isinstance(action, str) or (target is not None and (type(target) is not int or target <= 0)):
            record_decision(profile, obs, "rejected", None, False, policy_version,policy_snapshot)
            return "rejected", False
        story_services = {'story_accept': accept_story, 'story_start': activate_story, 'story_claim': claim_story}
        from .magic import learn_circle,prepare_magic,purchase_magic
        from .camp_guilds import donate_to_camp,upgrade_camp,UPGRADES
        from .camp_raids import rally_camp_raid,strike_camp_raid,claim_camp_raid
        from .challenges import accept_challenge,claim_challenge,claim_achievement,ACHIEVEMENTS
        from .crafting import learn_craft,buy_craft_material,craft_item
        from .market_policy import reprice_listing,observe_legacy_listing
        if action=='ammo' and ammo_stock and target==obs.ammo_id:
            success=game.buy_item_from_npc(profile,ammo_stock)
        elif action in {'improve','salvage'} and action==obs.forge_action and target==obs.forge_target:
            from .enhancements import improve_item,salvage_item
            success=bool(improve_item(profile,target,obs.forge_level,uuid4()) if action=='improve' else salvage_item(profile,target,uuid4()))
        elif action=='patrol' and target==obs.patrol_depth:
            from .frontier import patrol
            success=bool(patrol(profile,target,uuid4()))
        elif action==obs.market_action and target==obs.market_target and action in {'market_observe','market_reprice','market_cancel','market_sell','market_buy'}:
            market_item=OwnedItem.objects.filter(pk=target).first()
            success=bool(market_item and (observe_legacy_listing(profile,market_item) if action=='market_observe' else reprice_listing(profile,market_item,obs.market_price,market_item.market_price) if action=='market_reprice' else game.delist_item_from_market(profile,market_item,'stale') if action=='market_cancel' else game.sell_item_from_npc(profile,market_item) if action=='market_sell' else game.buy_item_on_market(profile,market_item,obs.market_price)))
        elif action==obs.craft_action and target==obs.craft_target and action in {'craft_learn','craft_material','craft'}:
            success=bool(learn_craft(profile,('smithing','alchemy')[target-1]) if action=='craft_learn' else buy_craft_material(profile,target) if action=='craft_material' else craft_item(profile,target,uuid4()))
        elif action==obs.personal_action and target==obs.personal_target and action in {'challenge_accept','challenge_claim','achievement_claim'}:
            success=bool(accept_challenge(profile,('daily','weekly')[target-1]) if action=='challenge_accept' else claim_challenge(profile,target) if action=='challenge_claim' else claim_achievement(profile,list(ACHIEVEMENTS)[target-1]))
        elif action==obs.raid_action and target==obs.raid_target and action in {'raid_rally','raid_strike','raid_claim','sleeper_rally','sleeper_strike','sleeper_claim','region_travel','alliance_promote'}:
            if action.startswith('sleeper_'):
                from .sleeper import rally,strike,claim_reward
                success=bool(rally(profile) if action=='sleeper_rally' else strike(profile,target,uuid4()) if action=='sleeper_strike' else claim_reward(profile))
            elif action=='alliance_promote':
                from .barrier import promote_alliance
                success=bool(promote_alliance(profile,profile.camp_tier))
            elif action=='region_travel':
                from .barrier import travel
                success=bool(travel(profile,target))
            else:success=bool(rally_camp_raid(profile) if action=='raid_rally' else strike_camp_raid(profile,target,uuid4()) if action=='raid_strike' else claim_camp_raid(profile,target))
        elif action=='choose_faction' and obs.camp_action==action and target==obs.camp_target_id:
            from .faction_choice import choose
            success=choose(profile,FACTIONS[target-1][0])
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
        elif action=="camp_supply" and obs.resupply_ready and target is None:
            from .camp_privileges import claim_resupply
            success=bool(claim_resupply(profile,uuid4()))
        elif action == "finance" and financed and target==financed.pk:
            from .weapon_finance import finance
            success=finance(profile,obs.finance_old_id,target,obs.finance_price)
        elif action == "equip" and equipment and target == equipment.pk:
            worn=sorted((i for i in inventory if i.is_equipped and i.blueprint.kind==equipment.blueprint.kind),key=lambda i:score(profile,i))
            slot=worn[0].equipped_slot if equipment.blueprint.kind=="ring" and len(worn)==2 else None
            success = game.equip_item(profile, equipment,slot=slot)
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
            from .factions import recruitment_camps
            choices=recruitment_camps(profile)
            success = game.choose_camp(profile, choices[(camp_target - 1)%len(choices)])
        elif action in ("accept", "promote") and action == rank_action and rank and target == obs.rank_target:
            success = (accept_camp_quest if action == "accept" else promote_in_camp)(profile, rank.key)
        elif action == "adventure" and template and target == template.pk:
            success = bool(start_adventure(profile, template.pk))
        elif action == "adventure_claim" and run and target == run.pk:
            success = claim_adventure(profile, run.pk)
        elif action == "shop" and product and target == product.pk:
            success = bool(purchase_product(profile, product.pk, uuid4()))
        elif action == "list" and item and target == item.pk:
            from .market_policy import list_bot_surplus
            success = list_bot_surplus(profile,item,set(story.item_ids)|reserved_materials)
        elif action == "buy" and offer and target == offer.pk:
            success = game.buy_item_on_market(profile, offer,offer.market_price)
        elif action == "stock" and stock and target == stock.pk:
            success = game.buy_item_from_npc(profile, stock)
        elif action == "wait":
            success = True
        else:
            record_decision(profile, obs, "rejected", None, False, policy_version,policy_snapshot)
            return "rejected", False
        if success and action != "wait":
            profile.refresh_from_db()
            profile.bot_turn += 1
            profile.save(update_fields=["bot_turn"])
        profile.bot_last_tick=timezone.now()
        profile.save(update_fields=["bot_last_tick"])
        record_decision(profile, obs, action, target, success, policy_version,policy_snapshot)
        from .community import bot_conversation
        bot_conversation(profile)
        return action, success
