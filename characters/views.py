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
    available = {key: BESTIARY[key] for key in location.monsters}
    combat_log = request.session.pop("combat_log", None)
    if request.method == "POST":
        monster = request.POST.get("monster_key")
        if monster not in available:
            messages.error(request, "Nie ma tutaj takiego przeciwnika.")
            return redirect(request.get_full_path())
        combat_log = execute_hunt(profile, monster)
        if combat_log is False:
            messages.error(request, "Brakuje energii lub trwa praca w kopalni.")
            combat_log = None
        request.session["combat_log"] = combat_log
        return redirect(request.get_full_path())
    return render(
        request,
        "characters/hunt.html",
        {
            "profile": profile,
            "combat_log": combat_log,
            "BESTIARY": available,
            "location": location,
        },
    )


@login_required
def market_view(request):
    profile = request.user.playerprofile
    refresh_player(profile)
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
        if action == "delist":
            sell_item_id = request.POST.get("delist_item_id")
            sell_item = get_object_or_404(
                OwnedItem, pk=positive_id(sell_item_id), owner=profile
            )
            if sell_item.owner != profile:
                return redirect(request.get_full_path())
            report_action(request, delist_item_from_market(profile, sell_item))
            return redirect(request.get_full_path())
    market_all_items = OwnedItem.objects.filter(is_market_listed=True)
    player_inventory = OwnedItem.objects.filter(owner=profile, is_market_listed=False)
    return render(
        request,
        "characters/market.html",
        {
            "profile": profile,
            "market_all_items": market_all_items,
            "player_inventory": player_inventory,
        },
    )


@login_required
def inventory_view(request):
    profile = request.user.playerprofile
    refresh_player(profile)
    if request.method == "POST":
        action = request.POST.get("action")
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
    player_inventory = OwnedItem.objects.filter(owner=profile, is_market_listed=False)
    equipped_weapon = OwnedItem.objects.filter(owner=profile, is_equipped=True).first()
    return render(
        request,
        "characters/inventory.html",
        {
            "profile": profile,
            "player_inventory": player_inventory,
            "equipped_weapon": equipped_weapon,
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
    player_inventory = OwnedItem.objects.filter(owner=profile, is_market_listed=False)
    merchant_inventory = ItemBluePrint.objects.all()
    return render(
        request,
        "characters/shop.html",
        {
            "profile": profile,
            "player_inventory": player_inventory,
            "shop_items": merchant_inventory,
        },
    )


@login_required
def train_view(request):
    profile = request.user.playerprofile
    refresh_player(profile)
    if request.method == "POST":
        attribute_name = request.POST.get("attribute")
        if attribute_name == "strength":
            report_action(request, train_attribute(profile, attribute_name))
            return redirect(request.get_full_path())
        if attribute_name == "dexterity":
            report_action(request, train_attribute(profile, attribute_name))
            return redirect(request.get_full_path())
        if attribute_name == "mana":
            report_action(request, train_attribute(profile, attribute_name))
            return redirect(request.get_full_path())
    return render(request, "characters/train.html", {"profile": profile})


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
            "Ta lokacja wymaga wyższego poziomu lub przynależności do obozu."
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
        # Initial allegiance is permanent through the UI; guild ranks come later.
        with transaction.atomic():
            locked = PlayerProfile.objects.select_for_update().get(pk=profile.pk)
            if locked.camp == "NONE" and camp in {"OLD_CAMP", "NEW_CAMP", "SWAMP_CAMP"}:
                locked.camp = camp
                locked.save(update_fields=["camp"])
                messages.success(request, "Obóz przyjął cię w swoje szeregi.")
            else:
                messages.error(request, "Nie możesz zmienić wybranego obozu.")
        return redirect("locations_page")
    cards = [
        {"location": loc, "unlocked": loc.accessible(profile)} for loc in LOCATIONS
    ]
    return render(
        request, "characters/locations.html", {"profile": profile, "cards": cards}
    )


@user_passes_test(lambda user: user.is_active and user.is_staff)
def market_monitor_view(request):
    trades = MarketTrade.objects.select_related(
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
    summary = trades.aggregate(
        count=Count("id"), volume=Sum("price"), average=Avg("price")
    )
    return render(
        request,
        "characters/market_monitor.html",
        {"summary": summary, "trades": trades[:100]},
    )
