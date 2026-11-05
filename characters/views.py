from django.views.decorators.debug import sensitive_post_parameters
from .worlds import current_world
from uuid import uuid4
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.db import transaction
from django.db.models import Count, Sum, Avg
from .locations import LOCATIONS, BY_KEY
from .models import MarketTrade
from .game_logic import refresh_player
from .models import ItemBluePrint, PlayerProfile, OwnedItem
from .game_logic import (
    BESTIARY,
    buy_item_from_npc,
    delist_item_from_market,
    equip_item,
    use_item,
    execute_hunt,
    sell_item_from_npc,
    start_mining,
    claim_ore_reward,
    buy_item_on_market,
    list_item_on_market,
    train_attribute,
    unequip_item,
)
from django.shortcuts import render, redirect, get_object_or_404


@login_required
def mine_view(request):
    profile = request.user.playerprofile
    refresh_player(profile)
    location = current_location(request, profile, "old_mine", "mine_page")
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "mine":
            report_action(request, start_mining(profile, 15))
            return redirect(request.get_full_path())
        elif action == "claim":
            report_action(request, claim_ore_reward(profile))
            return redirect(request.get_full_path())
    return render(
        request, "characters/mine.html", {"profile": profile, "location": location}
    )


@login_required
def hunt_view(request):
    profile = request.user.playerprofile
    refresh_player(profile)
    location = current_location(request, profile, "forest", "hunt_page")
    from .world_events import reward_snapshot
    xp_percent = reward_snapshot(0,100)[1]
    available = {key: {**BESTIARY[key], "current_reward":BESTIARY[key]["exp_reward"]*xp_percent//100} for key in location.monsters}
    combat_log = request.session.pop("combat_log", None)
    if request.method == "POST":
        monster = request.POST.get("monster_key")
        if monster not in available:
            messages.error(request, "Nie ma tutaj takiego przeciwnika.")
            return redirect(request.get_full_path())
        combat_log = execute_hunt(profile, monster, location.key, request.POST.get("request_key"))
        if combat_log is False:
            messages.error(request, "Potrzebujesz 15 energii i co najmniej 10 zdrowia. Zakończ też trwające zadanie.")
            combat_log = None
        request.session["combat_log"] = combat_log
        return redirect(request.get_full_path())
    return render(
        request,
        "characters/hunt.html",
        {
            "profile": profile,
            "combat_log": combat_log,
            "request_key": uuid4(),
            "BESTIARY": available,
            "location": location,
        },
    )


@login_required
def market_view(request):
    profile = request.user.playerprofile
    refresh_player(profile)
    current_location(request, profile, "old_camp", "market_page")
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "list":
            sell_item_id = request.POST.get("sell_item_id")
            price = request.POST.get("item_price")
            if not price:
                return redirect(request.get_full_path())
            sell_item = get_object_or_404(
                OwnedItem, pk=positive_id(sell_item_id), owner=profile
            )
            try:
                item_price = int(price)
            except (ValueError, TypeError):
                messages.error(request, "Podaj cenę w całych bryłkach rudy.")
                return redirect(request.get_full_path())
            if item_price <= 0:
                return redirect(request.get_full_path())
            report_action(request, list_item_on_market(profile, sell_item, item_price))
            return redirect(request.get_full_path())
        if action == "buy":
            buy_item_id = request.POST.get("buy_item_id")
            owned_item = get_object_or_404(
                OwnedItem, pk=positive_id(buy_item_id), is_market_listed=True
            )
            report_action(request, buy_item_on_market(profile, owned_item))
            return redirect(request.get_full_path())
        if action == "reprice":
            from .market_policy import reprice_listing
            item=get_object_or_404(OwnedItem,pk=positive_id(request.POST.get('item')),owner=profile,is_market_listed=True)
            try:price=int(request.POST.get('price'));expected=int(request.POST.get('expected'))
            except (TypeError,ValueError):price=0;expected=0
            report_action(request,reprice_listing(profile,item,price,expected))
            return redirect(request.get_full_path())
        if action == "delist":
            sell_item_id = request.POST.get("delist_item_id")
            sell_item = get_object_or_404(
                OwnedItem, pk=positive_id(sell_item_id), owner=profile
            )
            if sell_item.owner != profile:
                return redirect(request.get_full_path())
            report_action(request, delist_item_from_market(profile, sell_item))
            return redirect(request.get_full_path())
    market_all_items = OwnedItem.objects.filter(is_market_listed=True,owner__world=current_world()).select_related(
        "owner__user", "blueprint"
    )
    player_inventory = OwnedItem.objects.filter(owner=profile,is_equipped=False,blueprint__tradeable=True, is_market_listed=False)
    return render(
        request,
        "characters/market.html",
        {
            "profile": profile,
            "market_all_items": market_all_items,
            "my_offers":market_all_items.filter(owner=profile),
            "player_inventory": player_inventory,
        },
    )


@login_required
def inventory_view(request):
    profile = request.user.playerprofile
    refresh_player(profile)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "use":
            item = get_object_or_404(OwnedItem, pk=positive_id(request.POST.get("item_id")), owner=profile)
            report_action(request, use_item(profile,item))
            return redirect(request.get_full_path())
        if action == "equip":
            item_id = request.POST.get("item_id")
            item = get_object_or_404(OwnedItem, pk=positive_id(item_id), owner=profile)
            report_action(request, equip_item(profile, item))
            return redirect(request.get_full_path())
        if action == "unequip":
            item_id = request.POST.get("item_id")
            item = get_object_or_404(OwnedItem, pk=positive_id(item_id), owner=profile)
            report_action(request, unequip_item(profile, item))
            return redirect(request.get_full_path())
    player_inventory = OwnedItem.objects.filter(owner=profile,is_equipped=False, is_market_listed=False)
    equipped_weapon = OwnedItem.objects.filter(owner=profile, is_equipped=True, equipped_slot="weapon").first()
    return render(
        request,
        "characters/inventory.html",
        {
            "profile": profile,
            "player_inventory": player_inventory,
            "equipped_weapon": equipped_weapon,
            "equipped_items": profile.inventory.filter(is_equipped=True).select_related("blueprint"),
            "battles": profile.battles.all()[:10],
        },
    )


@login_required
def shop_view(request):
    profile = request.user.playerprofile
    refresh_player(profile)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "buy":
            item_id = request.POST.get("buy_item_id")
            item = get_object_or_404(ItemBluePrint, pk=positive_id(item_id))
            report_action(request, buy_item_from_npc(profile, item))
            return redirect(request.get_full_path())
        if action == "sell":
            item_id = request.POST.get("sell_item_id")
            item = get_object_or_404(OwnedItem, pk=positive_id(item_id), owner=profile)
            report_action(request, sell_item_from_npc(profile, item))
            return redirect(request.get_full_path())
    player_inventory = OwnedItem.objects.filter(owner=profile,is_equipped=False,blueprint__tradeable=True, is_market_listed=False)
    from django.core.paginator import Paginator
    merchant_inventory = ItemBluePrint.objects.filter(merchant=True, min_level__lte=profile.level, required_camp__in=["",profile.camp], min_camp_tier__lte=profile.camp_tier).order_by("kind","base_value","pk")
    return render(
        request,
        "characters/shop.html",
        {
            "profile": profile,
            "player_inventory": player_inventory,
            "shop_items": Paginator(merchant_inventory,30).get_page(request.GET.get("page")),
        },
    )


@login_required
def train_view(request):
    profile = request.user.playerprofile
    refresh_player(profile)
    location = current_location(request, profile, "new_camp", "train_page")
    if request.method == "POST":
        try:count=int(request.POST.get("count",1))
        except (TypeError,ValueError):count=0
        report_action(request, train_attribute(profile,request.POST.get("attribute"),count))
        return redirect(request.get_full_path())
    return render(request, "characters/train.html", {"profile": profile, "location": location, "attributes": [("strength", "Siła", profile.strength), ("dexterity", "Zręczność", profile.dexterity), ("mana", "Mana", profile.mana)]})


def positive_id(value):
    try:
        result = int(value)
    except (TypeError, ValueError):
        raise Http404("Nieprawidłowy przedmiot")
    if not 0 < result <= 9223372036854775807:
        raise Http404("Nieprawidłowy przedmiot")
    return result


def report_action(request, success):
    if success:
        messages.success(request, "Działanie zakończone.")
    else:
        messages.error(
            request,
            "Nie możesz teraz wykonać tej czynności. Sprawdź rudę, energię i wymagania.",
        )


def current_location(request, profile, default, route):
    key = request.GET.get("location", default)
    location = BY_KEY.get(key)
    if location is None or location.route != route:
        raise Http404("Nieznana lokacja")
    if not location.accessible(profile):
        raise PermissionDenied(
            "Ta lokacja wymaga wyższego poziomu, właściwego obozu lub rangi."
        )
    return location


def register_view(request):
    if request.user.is_authenticated:
        return redirect("locations_page")
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            user = form.save()
        login(request, user)
        return redirect("locations_page")
    return render(request, "registration/register.html", {"form": form})


@login_required
def locations_view(request):
    profile = request.user.playerprofile
    refresh_player(profile)
    if request.method == "POST":
        camp = request.POST.get("camp")
        from .game_logic import choose_camp
        report_action(request, choose_camp(profile, camp))
        return redirect("locations_page")
    cards = [
        {"location": loc, "unlocked": loc.accessible(profile)} for loc in LOCATIONS
    ]
    availability = request.GET.get("availability", "all")
    activity = request.GET.get("activity", "all")
    try:
        max_level = max(0, min(1000, int(request.GET.get("level", 1000))))
    except (ValueError, TypeError):
        max_level = 1000
    edition = request.GET.get("edition", str(profile.world.edition))
    cards = [card for card in cards if card["location"].level <= max_level
             and (availability == "all" or card["unlocked"] == (availability == "open"))
             and (activity == "all" or card["location"].route == activity)
             and edition == str(profile.world.edition)]
    return render(
        request,
        "characters/locations.html",
        {
            "profile": profile,
            "cards": cards,
            "population": PlayerProfile.objects.filter(
                world=current_world(),is_bot=True, user__is_active=True
            )
            .values("bot_role")
            .annotate(total=Count("pk")),
        },
    )


@user_passes_test(lambda user: user.is_active and user.is_staff)
def market_monitor_view(request):
    from .models import BotDecision

    decisions = BotDecision.objects.filter(profile__world=current_world())
    if request.GET.get("format") == "bots-csv":
        import csv
        import json

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="bot-decisions.csv"'
        writer = csv.writer(response)
        writer.writerow([
            "decision_id", "timestamp_utc", "schema_version", "profile_id",
            "role", "action", "target_id", "success", "ore_delta",
            "energy_delta", "health_delta", "premium_delta", "observation_json", "policy_version", "reason", "experience_delta",
        ])
        for decision in decisions.iterator():
            writer.writerow([
                decision.pk, decision.created_at.isoformat(), decision.schema_version,
                decision.profile_id, decision.role, decision.action, decision.target_id,
                decision.success, decision.ore_delta, decision.energy_delta, decision.health_delta, decision.premium_delta,
                json.dumps(decision.observation, sort_keys=True), decision.policy_version, decision.reason, decision.experience_delta,
            ])
        return response
    trades = MarketTrade.objects.filter(seller__world=current_world()).select_related(
        "blueprint", "seller__user", "buyer__user"
    )
    if request.GET.get("format") == "csv":
        import csv

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="market-trades.csv"'
        writer = csv.writer(response)
        writer.writerow(
            [
                "trade_id",
                "timestamp_utc",
                "blueprint_id",
                "seller_id",
                "buyer_id",
                "seller_is_bot",
                "buyer_is_bot",
                "price",
            ]
        )
        for trade in trades.iterator():
            writer.writerow(
                [
                    trade.pk,
                    trade.created_at.isoformat(),
                    trade.blueprint_id,
                    trade.seller_id,
                    trade.buyer_id,
                    trade.seller.is_bot,
                    trade.buyer.is_bot,
                    trade.price,
                ]
            )
        return response
    from .market_policy import market_effectiveness
    effectiveness=market_effectiveness(current_world())
    summary = trades.aggregate(
        count=Count("id"), volume=Sum("price"), average=Avg("price")
    )
    return render(
        request,
        "characters/market_monitor.html",
        {
            "summary": summary, "effectiveness":effectiveness,"trades": trades[:100],
            "bot_summary": decisions.values("role", "action", "success")
                .annotate(count=Count("id"), ore_delta=Sum("ore_delta"))
                .order_by("role", "action", "success"),
            "decisions": decisions[:50],
        },
    )


@login_required
def boss_view(request):
    from datetime import timedelta
    from django.utils import timezone
    from .bosses import BOSSES
    from .models import BossAttempt
    from .game_logic import execute_boss

    profile = request.user.playerprofile
    refresh_player(profile)
    location = current_location(request, profile, "crawler_nest", "boss_page")
    boss = BOSSES[location.key]
    from .world_events import reward_snapshot
    current_ore,current_xp,_,_ = reward_snapshot(boss.ore,boss.experience)
    from .bosses import MECHANICS
    from .finale import finale_ready
    if request.method == "POST":
        attempt = execute_boss(profile, boss.key, request.POST.get("request_key"))
        if attempt is False:
            messages.error(
                request,
                "Wyprawa niemożliwa. Sprawdź energię, pracę w kopalni i czas do kolejnej próby.",
            )
        else:
            messages.success(request, "Zapisano raport wyprawy.")
        return redirect(request.get_full_path())
    last = BossAttempt.objects.filter(profile=profile, boss_key=boss.key).first()
    next_attempt = (
        last.created_at + timedelta(minutes=boss.cooldown_minutes) if last else None
    )
    waiting = next_attempt is not None and timezone.now() < next_attempt
    return render(
        request,
        "characters/boss.html",
        {
            "profile": profile,
            "location": location,
            "boss": boss,
            "mechanics": MECHANICS[boss.key],
            "current_ore":current_ore,"current_xp":current_xp,
            "finale_gate": boss.key == "sleeper_sanctum" and not finale_ready(profile),
            "request_key": uuid4(),
            "last_attempt": last,
            "next_attempt": next_attempt if waiting else None,
            "can_fight": (boss.key != "sleeper_sanctum" or finale_ready(profile)) and not waiting
            and not profile.is_busy
            and profile.current_energy >= boss.energy_cost
            and profile.current_health >= 10,
        },
    )


def credits_view(request):
    import json
    from .gothic_assets import MANIFEST_PATH

    return render(request, "characters/credits.html", {
        "assets": json.loads(MANIFEST_PATH.read_text(encoding="utf-8")).values(),
    })


@login_required
def bestiary_view(request):
    from django.core.paginator import Paginator
    query = request.GET.get("q", "").strip()[:100]
    entries = []
    for key, monster in sorted(BESTIARY.items(), key=lambda entry: (entry[1]["level"], entry[1]["nazwa"])):
        if query.casefold() not in monster["nazwa"].casefold():
            continue
        habitats = [loc for loc in LOCATIONS if key in loc.monsters]
        entries.append({"key": key, "monster": monster, "habitats": habitats})
    return render(request, "characters/bestiary.html", {
        "page": Paginator(entries, 12).get_page(request.GET.get("page")),
        "query": query, "total": len(BESTIARY),
    })


@login_required
def camp_view(request):
    from .camp_progression import rank_cards, accept_camp_quest, abandon_camp_quest, promote_in_camp, CAMP_PATHS
    profile = request.user.playerprofile
    refresh_player(profile)
    if request.method == "POST":
        actions = {"accept": accept_camp_quest, "abandon": abandon_camp_quest, "promote": promote_in_camp}
        action = actions.get(request.POST.get("action"))
        report_action(request, action(profile, request.POST.get("rank")) if action else False)
        return redirect("camp_page")
    camps = dict(PlayerProfile.CAMP_LIST)
    selected = request.GET.get("camp", profile.camp if profile.camp != "NONE" else "OLD_CAMP")
    if selected not in camps or selected == "NONE":
        raise Http404("Nieznany obóz")
    return render(request, "characters/camp.html", {
        "profile": profile, "cards": rank_cards(profile, selected),
        "selected": selected, "camp_name": camps[selected], "paths": CAMP_PATHS[selected],
        "camps": [(key, name) for key, name in PlayerProfile.CAMP_LIST if key != "NONE"],
    })


@login_required
def adventures_view(request):
    from django.utils import timezone
    from .models import AdventureTemplate
    from .economy import start_adventure, claim_adventure
    from .world_events import reward_snapshot
    profile = request.user.playerprofile
    refresh_player(profile)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "start":
            result = start_adventure(profile, positive_id(request.POST.get("template")))
        elif action == "claim":
            result = claim_adventure(profile, positive_id(request.POST.get("run")))
        else:
            result = False
        report_action(request, result)
        return redirect("adventures_page")
    run = profile.adventures.filter(claimed_at__isnull=True).select_related("template").first()
    quests = []
    for quest in AdventureTemplate.objects.filter(enabled=True):
        ore, experience, premium, events = reward_snapshot(quest.ore_reward, quest.experience_reward, quest.premium_reward)
        quests.append({"quest": quest, "ore": ore, "experience": experience, "premium": premium, "events": events,
                      "available": profile.level >= quest.level and profile.current_energy >= quest.energy_cost and not run and profile.action_end_time is None})
    return render(request, "characters/adventures.html", {"profile": profile, "quests": quests, "run": run, "ready": run and timezone.now() >= run.ends_at, "history": profile.adventures.filter(claimed_at__isnull=False).select_related("template")[:10]})


@login_required
def itemshop_view(request):
    from uuid import uuid4
    from .models import StoreProduct
    from .economy import purchase_product
    profile = request.user.playerprofile
    refresh_player(profile)
    if request.method == "POST":
        report_action(request, purchase_product(profile, positive_id(request.POST.get("product")), request.POST.get("request_key")))
        return redirect("itemshop_page")
    from .economic_ledger import refills_remaining
    energy_left = refills_remaining(profile)
    products = [{"product": product, "request_key": uuid4()} for product in StoreProduct.objects.filter(enabled=True).select_related("blueprint")]
    return render(request, "characters/itemshop.html", {"energy_refills_left": energy_left,"profile": profile, "products": products, "entries": profile.premium_entries.all()[:15]})


def events_view(request):
    from django.utils import timezone
    from .models import WorldEvent
    from .world_events import active_events
    return render(request, "characters/events.html", {"active": active_events(), "upcoming": WorldEvent.objects.filter(world=current_world(),enabled=True, starts_at__gt=timezone.now())[:6]})


@login_required
def rankings_view(request):
    from django.core.paginator import Paginator
    populations = {"all": "Wszyscy", "humans": "Gracze", "bots": "Boty"}
    population = request.GET.get("population", "all")
    camp = request.GET.get("camp", "")
    camps = [(key, name) for key, name in PlayerProfile.CAMP_LIST if key != "NONE"]
    if population not in populations or camp not in {"", *(key for key, _ in camps)}:
        raise Http404("Nieznany ranking")
    profiles = PlayerProfile.objects.filter(world=current_world(),user__is_active=True, user__is_staff=False).select_related("user")
    if population != "all":
        profiles = profiles.filter(is_bot=population == "bots")
    totals = {row["camp"]: row for row in profiles.values("camp").annotate(players=Count("pk"), experience=Sum("experience"), average=Avg("level"))}
    camp_ranking = sorted([{"key": key, "name": name, **totals.get(key, {"players": 0, "experience": 0, "average": 0})} for key, name in camps], key=lambda row: (-row["experience"], -row["players"], row["key"]))
    if camp:
        profiles = profiles.filter(camp=camp)
    page = Paginator(profiles.order_by("-level", "-experience", "pk"), 50).get_page(request.GET.get("page"))
    return render(request, "characters/rankings.html", {"page": page, "camp_ranking": camp_ranking, "camps": camps, "populations": populations.items(), "population": population, "camp": camp})


@login_required
def game_master_view(request):
    from .admin_tools import ProfileStatsForm, administer_player
    from .models import AdminAction
    from .backups import backup_status
    from django.conf import settings
    if not request.user.is_superuser:
        raise PermissionDenied("Panel zarządcy wymaga konta administratora.")
    profiles = PlayerProfile.objects.filter(world=current_world()).select_related("user").order_by("user__username")
    selected = request.POST.get("profile") if request.method == "POST" else request.GET.get("profile")
    target = get_object_or_404(PlayerProfile, world=current_world(),pk=positive_id(selected)) if selected else profiles.first()
    if request.method == "POST":
        success, message = administer_player(request.user, target.pk, request.POST.get("action"), request.POST)
        (messages.success if success else messages.error)(request, message)
        return redirect(reverse_url("game_master") + "?profile=" + str(target.pk))
    return render(request, "characters/game_master.html", {"backup_status": backup_status(settings.BASE_DIR / "backups"), "profiles": profiles, "target": target, "stats_form": ProfileStatsForm(instance=target), "blueprints": ItemBluePrint.objects.all(), "audit": AdminAction.objects.select_related("actor", "profile__user")[:30]})


def reverse_url(name):
    from django.urls import reverse
    return reverse(name)


@login_required
def tavern_view(request):
    from django.core.paginator import Paginator
    from .community import post_message
    from .models import TavernTopic
    topic_id = request.GET.get('topic')
    topic = get_object_or_404(TavernTopic,author__world=current_world(), pk=positive_id(topic_id)) if topic_id else None
    if request.method == 'POST':
        try:
            posted = post_message(request.user.playerprofile, request.POST.get('body'), topic_id=topic.pk if topic else None, title=request.POST.get('title'))
            return redirect(f'{request.path}?topic={posted.pk}')
        except ValueError as exc:
            messages.error(request, str(exc))
    topics = Paginator(TavernTopic.objects.filter(author__world=current_world()).select_related('author__user'), 20).get_page(request.GET.get('page'))
    entries = Paginator(topic.messages.select_related('author__user').all(), 30).get_page(request.GET.get('messages')) if topic else None
    return render(request, 'characters/tavern.html', {'topic': topic, 'topics': topics, 'entries': entries})


@login_required
def colony_life_view(request):
    from datetime import timedelta
    from django.utils import timezone
    from .community import activity_rows
    now = timezone.now()
    residents = list(PlayerProfile.objects.filter(world=current_world(),is_bot=True, user__is_active=True).select_related('user').order_by('pk')[:100])
    for resident in residents:
        resident.scheduler_active = bool(resident.bot_last_tick and now - resident.bot_last_tick < timedelta(seconds=90))
    return render(request, 'characters/colony_life.html', {'residents': residents, 'activity': activity_rows(), 'active_count': sum(r.scheduler_active for r in residents)})


@login_required
def story_view(request):
    from .models import StoryQuest, StoryRun
    from django.utils import timezone
    from .gothic_campaign import CHAPTERS
    from .story_quests import (accept_story, activate_story, claim_story, choose_story,
                              travel_story, available, progress_for, ready)
    profile = request.user.playerprofile
    refresh_player(profile)
    if request.method == 'POST':
        target = positive_id(request.POST.get('target'))
        action = request.POST.get('action')
        services = {'accept': accept_story, 'start': activate_story, 'claim': claim_story}
        if action in services:
            success = services[action](profile, target)
        elif action == 'talk':
            success = choose_story(profile, target, request.POST.get('goal'), request.POST.get('option'))
        elif action == 'travel':
            success = travel_story(profile, target, request.POST.get('goal'))
        else:
            success = False
        report_action(request, bool(success))
        return redirect('story_page')
    run = profile.story_runs.exclude(status='claimed').first()
    goals = []
    if run:
        for goal in run.snapshot['objectives']:
            done = progress_for(profile, run, goal)
            total = 1 if goal['kind'] == 'wait' else goal.get('count', 1)
            ends_at = run.activated_at + timezone.timedelta(seconds=goal['seconds']) if goal['kind'] == 'wait' and run.activated_at else None
            goals.append({'goal': goal, 'done': done, 'total': total, 'complete': done >= total,
                          'choice': goal.get('options', {}).get(run.choices.get(goal['id'])), 'ends_at': ends_at})
    accepted_ids = profile.story_runs.values_list('quest_id', flat=True)
    quests = [q for q in StoryQuest.objects.filter(enabled=True).exclude(pk__in=accepted_ids) if available(profile, q)] if not run else []
    history = list(profile.story_runs.filter(status='claimed')[:50])
    for entry in history:
        entry.decision_labels = [g.get('options', {}).get(entry.choices[g['id']], entry.choices[g['id']]) for g in entry.snapshot['objectives'] if g['id'] in entry.choices]
    chapter = run.snapshot['chapter'] if run else max((r.snapshot['chapter'] for r in history), default=1)
    chapter_rows = [{'number': number, 'name': name, 'art': art, 'current': number == chapter} for number, name, art in CHAPTERS]
    return render(request, 'characters/story.html', {'profile': profile, 'run': run, 'goals': goals, 'ready': bool(run and ready(profile, run)), 'quests': quests, 'history': history, 'chapters': chapter_rows, 'chapter_art': next((c['art'] for c in chapter_rows if c['current']), 'exchange'), 'finale_ready': any(r.snapshot['key'] == 'ritual-ready' for r in history)})


@login_required
def item_catalog_view(request):
    from django.core.paginator import Paginator
    from django.db.models import Q
    from .models import ContentPack
    items=ItemBluePrint.objects.filter(source_game='GOTHIC_I').exclude(catalog_key__startswith='g1-bab-armor-').order_by('kind','name','catalog_key')
    query=request.GET.get('q','').strip()[:100]
    kind=request.GET.get('kind','')
    if query:items=items.filter(Q(name__icontains=query)|Q(catalog_key__icontains=query))
    if kind in {c[0] for c in ItemBluePrint._meta.get_field('kind').choices}:items=items.filter(kind=kind)
    if request.GET.get('verified')=='1':items=items.filter(original_stats__verified=True)
    return render(request,'characters/item_catalog.html',{'items':Paginator(items,24).get_page(request.GET.get('page')),'query':query,'kind':kind,'verified':request.GET.get('verified')=='1','packs':ContentPack.objects.filter(game='GOTHIC_I').order_by('-version')[:1],'kinds':[(k,ItemBluePrint(kind=k).kind_name) for k,_ in ItemBluePrint._meta.get_field('kind').choices]})


@login_required
@user_passes_test(lambda user:user.is_active and user.is_superuser)
def economy_balance_view(request):
    from .economic_ledger import summary
    from .economy_simulation import rates
    data=summary()
    return render(request,'characters/economy_balance.html',{'balance':data,'rates':rates()})


@login_required
def world_monitor_view(request):
    if not request.user.is_superuser:raise PermissionDenied('Raport świata wymaga administratora.')
    from .world_monitor import world_report
    from .bot_telemetry import replay_decision
    from .models import BotDecision
    import json
    try:days=int(request.GET.get('days',7))
    except (TypeError,ValueError):days=7
    report=world_report(days)
    if request.GET.get('format')=='json':
        response=HttpResponse(json.dumps(report,default=str,ensure_ascii=False),content_type='application/json')
        response['Content-Disposition']='attachment; filename="world-report-schema-1.json"'
        return response
    replay=None
    if request.GET.get('decision'):
        fact=get_object_or_404(BotDecision,profile__world=current_world(),pk=positive_id(request.GET.get('decision')))
        replay={'id':fact.pk,**replay_decision(fact)}
    return render(request,'characters/world_monitor.html',{'report':report,'replay':replay})


@login_required
def magic_view(request):
    from .magic import SCHOOLS,BY_CODE,offers,combat_plan,learn_circle,prepare_magic,purchase_magic,circle_cap
    profile=request.user.playerprofile
    refresh_player(profile)
    if request.method=='POST':
        action=request.POST.get('action')
        if action=='learn':result=learn_circle(profile)
        elif action=='buy':result=purchase_magic(profile,positive_id(request.POST.get('blueprint')))
        elif action=='prepare':result=prepare_magic(profile,positive_id(request.POST.get('item')))
        elif action=='clear':result=prepare_magic(profile,None)
        else:result=False
        (messages.success if result else messages.error)(request,'Wiedza i wyposażenie zapisane.' if result else 'Nie spełniasz wymagań: sprawdź krąg, szkołę, poziom, zasoby i trwające zadania.')
        return redirect('magic_page')
    inventory=[{'item':item,'spell':BY_CODE[item.blueprint.catalog_key][0]} for item in profile.inventory.filter(is_market_listed=False,blueprint__catalog_key__in=BY_CODE).select_related('blueprint')]
    next_circle=profile.magic_skill+1
    return render(request,'characters/magic.html',{'profile':profile,'school':SCHOOLS.get(profile.camp,('','Bez szkoły — dostępne zwoje'))[1],'plan':combat_plan(profile),'circle_cap':circle_cap(profile),'next_circle':next_circle,'circle_lp':5*next_circle,'circle_ore':50*next_circle,'circle_level':next_circle*2,'can_learn':not profile.is_busy and next_circle<=circle_cap(profile) and profile.level>=next_circle*2 and profile.skill_points>=5*next_circle and profile.ore_balance>=50*next_circle,'inventory':inventory,'offers':offers(profile)})


@login_required
def camp_guild_view(request):
    from .camp_guilds import guild_cards,donate_to_camp,upgrade_camp
    from .camp_raids import rally_camp_raid,strike_camp_raid,claim_camp_raid,raid_card
    profile=request.user.playerprofile
    refresh_player(profile)
    if request.method=='POST':
        try:amount=int(request.POST.get('amount',0));expected=int(request.POST.get('expected_level',-1))
        except (TypeError,ValueError):amount=0;expected=-1
        action=request.POST.get('action')
        if action=='rally':result=rally_camp_raid(profile)
        elif action=='strike':result=strike_camp_raid(profile,positive_id(request.POST.get('raid')),request.POST.get('request_key'))
        elif action=='claim_raid':result=claim_camp_raid(profile,positive_id(request.POST.get('raid')))
        else:result=donate_to_camp(profile,amount,request.POST.get('request_key')) if action=='donate' else upgrade_camp(profile,request.POST.get('upgrade'),expected) if action=='upgrade' else False
        (messages.success if result else messages.error)(request,'Wspólnota zapisała twój wkład.' if result else 'Nie udało się wykonać działania. Sprawdź rudę, poziom obozu i stan ulepszenia.')
        return redirect('camp_guild')
    return render(request,'characters/camp_guild.html',{'profile':profile,'card':guild_cards(profile),'raid_card':raid_card(profile),'request_key':uuid4()})


@sensitive_post_parameters("password")
def world_setup_view(request):
    from django.contrib.auth.models import User
    from .world_management import WorldSetupForm,initialize_world
    from django.core.exceptions import ValidationError
    if request.META.get('REMOTE_ADDR') not in {'127.0.0.1','::1'}:raise PermissionDenied('Pierwszą inicjalizację uruchom lokalnie.')
    if User.objects.filter(is_superuser=True).exists():
        if request.user.is_authenticated and request.user.is_superuser:return redirect('world_control')
        return redirect('login')
    form=WorldSetupForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        try:admin=initialize_world(**form.cleaned_data)
        except ValidationError as exc:form.add_error(None,exc)
        else:login(request,admin);return redirect('world_control')
    return render(request,'characters/world_setup.html',{'form':form})


@login_required
@sensitive_post_parameters("password")
def world_control_view(request):
    if not request.user.is_active or not request.user.is_superuser:raise PermissionDenied('Tylko administrator może zarządzać światem.')
    from .world_management import WorldResetForm,WorldSettingsForm,reset_world
    from django.core.exceptions import ValidationError
    from django.contrib.auth import logout
    world=current_world()
    configuring=request.method=='POST' and request.POST.get('action')=='configure'
    config_form=WorldSettingsForm(request.POST if configuring else None,auto_id='config_%s',initial={'name':world.name,'bot_count':world.bot_count})
    if configuring and config_form.is_valid():
        from django.core.management import call_command
        from io import StringIO
        with transaction.atomic():
            world.name=config_form.cleaned_data['name'];world.bot_count=config_form.cleaned_data['bot_count'];world.configured=True;world.save()
            if world.bot_count:call_command('run_bots',create=world.bot_count,create_only=True,limit=world.bot_count,stdout=StringIO())
        messages.success(request,'Zapisano nazwę i liczbę aktywnych botów bez resetu.');return redirect('world_control')
    form=WorldResetForm(request.POST if request.method=='POST' and not configuring else None,auto_id='reset_%s',initial={'name':world.name,'bot_count':world.bot_count,'expected_world':world.pk})
    if request.method=='POST' and not configuring and form.is_valid():
        values=dict(form.cleaned_data);values.pop('acknowledge')
        try:fresh,backup=reset_world(request.user,**values)
        except (ValidationError,PermissionDenied) as exc:form.add_error(None,str(exc))
        except OSError:form.add_error(None,'Nie udało się utworzyć kopii. Świat nie został wyczyszczony.')
        else:
            logout(request);messages.success(request,'Nowy świat utworzony. Zaloguj się tym samym kontem administratora.');return redirect('login')
    return render(request,'characters/world_control.html',{'world':world,'form':form,'config_form':config_form})


@login_required
def characters_view(request):
    from .worlds import profile_for
    profile=profile_for(request.user)
    if request.method=='POST':
        selected=get_object_or_404(PlayerProfile,pk=positive_id(request.POST.get('profile')),user=request.user,world=current_world())
        request.session['active_character']=selected.pk
        return redirect('locations_page')
    return render(request,'characters/characters.html',{'profile':profile,'characters':request.user.characters.select_related('world').all()})


@login_required
def challenges_view(request):
    from .challenges import cards,accept_challenge,claim_challenge,claim_achievement
    profile=request.user.playerprofile;refresh_player(profile)
    if request.method=='POST':
        action=request.POST.get('action')
        result=accept_challenge(profile,request.POST.get('cadence')) if action=='accept' else claim_challenge(profile,positive_id(request.POST.get('challenge'))) if action=='claim' else claim_achievement(profile,request.POST.get('key')) if action=='achievement' else False
        report_action(request,bool(result));return redirect('challenges_page')
    return render(request,'characters/challenges.html',{'profile':profile,**cards(profile)})


@login_required
def crafting_view(request):
    from .crafting import recipe_cards,learn_craft,buy_craft_material,craft_item
    profile=request.user.playerprofile;refresh_player(profile)
    if request.method=='POST':
        action=request.POST.get('action')
        result=learn_craft(profile,request.POST.get('discipline')) if action=='learn' else buy_craft_material(profile,positive_id(request.POST.get('blueprint'))) if action=='material' else craft_item(profile,positive_id(request.POST.get('recipe')),request.POST.get('request_key')) if action=='craft' else False
        report_action(request,bool(result));return redirect('crafting_page')
    return render(request,'characters/crafting.html',{'profile':profile,'cards':recipe_cards(profile),'request_key':uuid4(),'history':profile.crafts.select_related('recipe').order_by('-pk')[:20]})


@login_required
def journal_view(request):
    from django.core.paginator import Paginator
    from .models import JournalNotice, BattleRecord, EconomicEntry
    from .journal import sync_notices
    profile = request.user.playerprofile
    sync_notices(profile)
    if request.method == "POST":
        from django.utils import timezone
        JournalNotice.objects.filter(profile=profile, read_at__isnull=True).update(read_at=timezone.now())
        return redirect("journal_page")
    kind = request.GET.get("kind", "battles")
    if kind not in ("battles", "rewards", "notices"):
        kind = "battles"
    sources = {"battles": BattleRecord.objects.filter(profile=profile),
               "rewards": EconomicEntry.objects.filter(profile=profile).order_by("-created_at", "-pk"),
               "notices": JournalNotice.objects.filter(profile=profile)}
    page = Paginator(sources[kind], 20).get_page(request.GET.get("page"))
    return render(request, "characters/journal.html", {"profile":profile,"page":page,"kind":kind})


@login_required
def battle_detail_view(request, battle_id):
    from django.shortcuts import get_object_or_404
    from .models import BattleRecord
    battle = get_object_or_404(BattleRecord,pk=battle_id,profile=request.user.playerprofile)
    return render(request,"characters/battle_detail.html",{"battle":battle})


@login_required
def hall_view(request):
    from .models import CampaignCompletion, EditionConclusion
    from .finale import conclude_edition
    from django.core.exceptions import ValidationError
    world = current_world()
    if request.method == "POST":
        if not request.user.is_superuser:raise PermissionDenied
        try:
            conclude_edition(request.user,positive_id(request.POST.get("world")),request.POST.get("confirmation"))
            messages.success(request,"Zapisano podsumowanie edycji. Gra pozostaje otwarta.")
        except ValidationError as exc:messages.error(request," ".join(exc.messages))
        return redirect("hall_page")
    return render(request,"characters/hall.html",{"finishers":CampaignCompletion.objects.filter(profile__world=world).order_by("created_at","pk"),"conclusion":EditionConclusion.objects.filter(world=world).first()})
