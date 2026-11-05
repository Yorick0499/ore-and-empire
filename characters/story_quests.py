"""Versioned story objectives. All people and bot actions use these services."""
from copy import deepcopy
from dataclasses import dataclass
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import StoryQuest, StoryRun, OwnedItem, ItemBluePrint
from .game_logic import player_action, check_level_up

UNIVERSE = 'GOTHIC_I'  # Server-owned scope until the realm model in #15 exists.
EVENT_KINDS = {'hunt', 'boss', 'mine', 'train', 'travel'}
KINDS = EVENT_KINDS | {'item', 'talk', 'wait'}


def bounded_int(value, low=0, high=1_000_000):
    return type(value) is int and low <= value <= high


def validate_definition(quest):
    from .locations import BY_KEY
    from .game_logic import BESTIARY, BOSSES
    def invalid():
        raise ValidationError('Niepoprawna definicja zadania: sprawdź cele, nagrody i zależności.')
    if not bounded_int(quest.version, 1) or not bounded_int(quest.energy_cost, 0, 100):
        invalid()
    if not isinstance(quest.prerequisites, list) or any(not isinstance(k, str) or k == quest.key for k in quest.prerequisites):
        invalid()
    if not isinstance(quest.any_prerequisites, list) or any(not isinstance(k, str) or k == quest.key for k in quest.any_prerequisites): invalid()
    if len(set(quest.prerequisites)) != len(quest.prerequisites): invalid()
    graph = {key: deps + any_deps for key, deps, any_deps in StoryQuest.objects.values_list('key', 'prerequisites', 'any_prerequisites')}
    graph[quest.key] = quest.prerequisites + quest.any_prerequisites
    def cycle(key, path):
        if key in path: return True
        return any(cycle(child, path | {key}) for child in graph.get(key, []) if isinstance(child, str))
    if cycle(quest.key, set()): invalid()
    if not isinstance(quest.required_choices, dict):
        invalid()
    for key, decisions in quest.required_choices.items():
        if key not in quest.prerequisites or not isinstance(decisions, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in decisions.items()):
            invalid()
    if not isinstance(quest.objectives, list) or not 1 <= len(quest.objectives) <= 12:
        invalid()
    ids = set()
    item_targets = set()
    for goal in quest.objectives:
        if not isinstance(goal, dict): invalid()
        kind, key = goal.get('kind'), goal.get('id')
        if not isinstance(kind, str) or kind not in KINDS or not isinstance(key, str) or not key or len(key) > 40 or key in ids or not isinstance(goal.get('label'), str):
            invalid()
        ids.add(key)
        target = goal.get('target')
        if kind in {'hunt', 'boss', 'travel', 'train'} and not isinstance(target, str): invalid()
        if not bounded_int(goal.get('count', 1), 1, 1000): invalid()
        if kind == 'hunt' and target not in BESTIARY: invalid()
        if kind == 'boss' and target not in BOSSES: invalid()
        if kind == 'travel' and target not in BY_KEY: invalid()
        if kind == 'train' and target not in {'strength', 'dexterity', 'mana'}: invalid()
        if kind == 'item' and (not bounded_int(target, 1) or not ItemBluePrint.objects.filter(pk=target).exists()): invalid()
        if kind == 'item':
            if target in item_targets: invalid()
            item_targets.add(target)
        if kind == 'wait' and not bounded_int(goal.get('seconds'), 1, 86400): invalid()
        if kind == 'talk':
            options = goal.get('options')
            if not isinstance(options, dict) or not 1 <= len(options) <= 6 or any(not isinstance(k, str) or not k or not isinstance(v, str) or not v for k, v in options.items()): invalid()
            if goal.get('count', 1) != 1: invalid()
    rewards = quest.rewards
    if not isinstance(rewards, dict) or set(rewards) - {'ore', 'experience', 'premium', 'items'}: invalid()
    if any(not bounded_int(rewards.get(k, 0)) for k in ('ore', 'experience', 'premium')): invalid()
    items = rewards.get('items', [])
    if not isinstance(items, list) or len(items) > 6: invalid()
    for item in items:
        if not isinstance(item, dict) or not bounded_int(item.get('blueprint'), 1) or not bounded_int(item.get('count', 1), 1, 6) or not ItemBluePrint.objects.filter(pk=item['blueprint']).exists(): invalid()


def available(profile, quest):
    if not quest.enabled or quest.universe != profile.world.universe or profile.level < quest.level or (quest.camp and profile.camp != quest.camp):
        return False
    completed = {run.snapshot['key']: run for run in profile.story_runs.filter(status='claimed')}
    if quest.any_prerequisites and not any(key in completed for key in quest.any_prerequisites):
        return False
    if any(key not in completed for key in quest.prerequisites):
        return False
    return all(all(completed[key].choices.get(goal) == option for goal, option in decisions.items()) for key, decisions in quest.required_choices.items() if key in completed)


@player_action
def accept_story(profile, quest_id):
    quest = StoryQuest.objects.filter(pk=quest_id).first()
    if not quest or profile.story_runs.exclude(status='claimed').exists() or profile.story_runs.filter(quest=quest).exists() or not available(profile, quest):
        return False
    try:
        validate_definition(quest)
    except ValidationError:
        return False
    fields = ('key', 'version', 'title', 'description', 'chapter', 'level', 'camp', 'universe', 'prerequisites', 'any_prerequisites', 'required_choices', 'objectives', 'rewards', 'energy_cost')
    return StoryRun.objects.create(profile=profile, quest=quest, snapshot=deepcopy({key: getattr(quest, key) for key in fields}))


def progress_for(profile, run, goal):
    kind = goal['kind']
    if not run.activated_at:
        return 0
    if kind == 'wait':
        return int(timezone.now() >= run.activated_at + timedelta(seconds=goal['seconds']))
    if kind == 'item':
        from django.db.models import Sum
        return min(goal.get('count', 1), profile.inventory.filter(blueprint_id=goal['target'], is_equipped=False, is_market_listed=False).aggregate(total=Sum('quantity'))['total'] or 0)
    if kind == 'talk':
        return int(goal['id'] in run.choices)
    return run.progress.get(goal['id'], 0)


def ready(profile, run):
    return bool(run.activated_at and all(progress_for(profile, run, g) >= (1 if g['kind'] == 'wait' else g.get('count', 1)) for g in run.snapshot['objectives']))


def update_status(profile, run):
    if run.status not in ('accepted', 'claimed'):
        run.status = 'ready' if ready(profile, run) else 'active'
        run.save(update_fields=['status'])


def owned_run(profile, run_id):
    return StoryRun.objects.select_for_update().filter(pk=run_id, profile=profile).exclude(status='claimed').first()


@player_action
def activate_story(profile, run_id):
    run = owned_run(profile, run_id)
    if not run or run.status != 'accepted' or profile.is_busy or profile.current_energy < run.snapshot['energy_cost']:
        return False
    profile.current_energy -= run.snapshot['energy_cost']
    profile.save(update_fields=['current_energy'])
    run.activated_at = timezone.now()
    run.status = 'active'
    run.save(update_fields=['status', 'activated_at'])
    update_status(profile, run)
    return True


def record_story_event(profile, kind, target='', amount=1):
    """Only successful domain services emit events, inside their transaction."""
    for run in profile.story_runs.select_for_update().filter(status__in=['active', 'ready']):
        for goal in run.snapshot['objectives']:
            if goal['kind'] == kind and goal.get('target', '') == target and kind in EVENT_KINDS:
                run.progress[goal['id']] = min(goal.get('count', 1), run.progress.get(goal['id'], 0) + amount)
        run.save(update_fields=['progress'])
        update_status(profile, run)


@player_action
def choose_story(profile, run_id, goal_id, option):
    run = owned_run(profile, run_id)
    if not run or run.status not in ('active', 'ready'): return False
    goal = next((g for g in run.snapshot['objectives'] if g['id'] == goal_id and g['kind'] == 'talk'), None)
    if not goal or option not in goal['options'] or goal_id in run.choices: return False
    run.choices[goal_id] = option
    run.save(update_fields=['choices'])
    update_status(profile, run)
    return True


@player_action
def travel_story(profile, run_id, goal_id):
    from .locations import BY_KEY
    run = owned_run(profile, run_id)
    if not run or run.status != 'active' or profile.is_busy: return False
    goal = next((g for g in run.snapshot['objectives'] if g['id'] == goal_id and g['kind'] == 'travel'), None)
    if not goal or progress_for(profile, run, goal) >= goal.get('count', 1): return False
    location = BY_KEY.get(goal['target'])
    if not location or not location.accessible(profile) or profile.current_energy < 2: return False
    profile.current_energy -= 2
    profile.save(update_fields=['current_energy'])
    record_story_event(profile, 'travel', location.key)
    return True


@player_action
def claim_story(profile, run_id):
    from .economy import change_premium
    run = owned_run(profile, run_id)
    if not run or not ready(profile, run): return False
    # Lock and recheck the exact physical items before consuming any or granting rewards.
    deliveries = {}
    for goal in run.snapshot['objectives']:
        if goal['kind'] != 'item': continue
        needed = goal.get('count', 1)
        items = profile.inventory.select_for_update().filter(blueprint_id=goal['target'], is_equipped=False, is_market_listed=False).order_by('pk')
        for item in items:
            used = min(needed, item.quantity - deliveries.get(item.pk, 0))
            if used > 0:
                deliveries[item.pk] = deliveries.get(item.pk, 0) + used
                needed -= used
            if not needed:break
        if needed:return False
    rewards = run.snapshot['rewards']
    for item in rewards.get('items', []):
        blueprint = ItemBluePrint.objects.get(pk=item['blueprint'])
        for _ in range(item.get('count', 1)):
            OwnedItem.objects.create(owner=profile, blueprint=blueprint)
    from .market_policy import record_market_event
    for item in profile.inventory.select_for_update().filter(pk__in=deliveries):
        count = deliveries[item.pk]
        record_market_event(profile,item,"consumption",quantity=count,reason="story_delivery")
        if count == item.quantity:item.delete()
        else:
            item.quantity -= count
            item.save(update_fields=['quantity'])
    profile.ore_balance += rewards.get('ore', 0)
    profile.experience += rewards.get('experience', 0)
    profile.save(update_fields=['ore_balance', 'experience'])
    check_level_up(profile)
    if rewards.get('premium', 0):
        change_premium(profile, rewards['premium'], 'Fabuła: ' + run.snapshot['title'][:90], f'story:{run.pk}')
    run.claimed_at = timezone.now()
    run.status = 'claimed'
    run.save(update_fields=['claimed_at', 'status'])
    return True


@dataclass(frozen=True)
class StoryPlan:
    action: str = ''
    target: int | None = None
    goal: str = ''
    option: str = ''
    events: tuple = ()
    item_ids: tuple = ()
    missing_items: tuple = ()


def bot_story_plan(profile):
    run = profile.story_runs.exclude(status='claimed').first()
    if not run:
        for quest in StoryQuest.objects.filter(enabled=True, universe=UNIVERSE):
            try:
                validate_definition(quest)
            except ValidationError:
                continue
            if not profile.story_runs.filter(quest=quest).exists() and available(profile, quest):
                return StoryPlan('story_accept', quest.pk)
        return StoryPlan()
    item_ids = tuple(g['target'] for g in run.snapshot['objectives'] if g['kind'] == 'item')
    if run.status == 'accepted':
        return StoryPlan('story_start', run.pk, item_ids=item_ids) if profile.current_energy >= run.snapshot['energy_cost'] and not profile.is_busy else StoryPlan(item_ids=item_ids)
    if ready(profile, run): return StoryPlan('story_claim', run.pk, item_ids=item_ids)
    missing = [g for g in run.snapshot['objectives'] if progress_for(profile, run, g) < (1 if g['kind'] == 'wait' else g.get('count', 1))]
    events = tuple((g['kind'], g.get('target', '')) for g in missing if g['kind'] in EVENT_KINDS)
    missing_items = tuple(g['target'] for g in missing if g['kind'] == 'item')
    for goal in missing:
        if goal['kind'] == 'talk':
            return StoryPlan('story_talk', run.pk, goal['id'], next(iter(goal['options'])), events, item_ids, missing_items)
        if goal['kind'] == 'travel':
            from .locations import BY_KEY
            if BY_KEY[goal['target']].accessible(profile) and profile.current_energy >= 2:
                return StoryPlan('story_travel', run.pk, goal['id'], '', events, item_ids, missing_items)
    return StoryPlan(events=events, item_ids=item_ids, missing_items=missing_items)
