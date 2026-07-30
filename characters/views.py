from django.shortcuts import render
from .models import PlayerProfile, OwnedItem
from .game_logic import (
    BESTIARY,
    delist_item_from_market,
    execute_hunt,
    start_mining,
    claim_ore_reward,
    buy_item_on_market,
    list_item_on_market,
)
from django.shortcuts import render, redirect


def mine_view(request):
    profile = PlayerProfile.objects.get(id=1)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "mine":
            start_mining(profile, 15)
            return redirect(request.path)
        elif action == "claim":
            claim_ore_reward(profile)
            return redirect(request.path)
    return render(request, "characters/mine.html", {"profile": profile})


def hunt_view(request):
    profile = PlayerProfile.objects.get(id=1)
    combat_log = request.session.pop("combat_log", None)
    if request.method == "POST":
        monster = request.POST.get("monster_key")
        combat_log = execute_hunt(profile, monster)
        request.session["combat_log"] = combat_log
        return redirect(request.path)
    return render(
        request,
        "characters/hunt.html",
        {"profile": profile, "combat_log": combat_log, "BESTIARY": BESTIARY},
    )


def market_view(request):
    profile = PlayerProfile.objects.get(id=1)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "list":
            sell_item_id = request.POST.get("sell_item_id")
            price = request.POST.get("item_price")
            if not price:
                return redirect(request.path)
            sell_item = OwnedItem.objects.get(id=sell_item_id)
            item_price = int(price)
            if item_price <= 0:
                return redirect(request.path)
            list_item_on_market(profile, sell_item, item_price)
            return redirect(request.path)
        if action == "buy":
            buy_item_id = request.POST.get("buy_item_id")
            owned_item = OwnedItem.objects.get(id=buy_item_id)
            buy_item_on_market(profile, owned_item)
            return redirect(request.path)
        if action == "delist":
            sell_item_id = request.POST.get("delist_item_id")
            sell_item = OwnedItem.objects.get(id=sell_item_id)
            if sell_item.owner != profile:
                return redirect(request.path)
            delist_item_from_market(profile, sell_item)
            return redirect(request.path)
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
