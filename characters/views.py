from django.shortcuts import render
from .models import PlayerProfile
from .game_logic import BESTIARY, execute_hunt, start_mining, claim_ore_reward
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
    combat_log = None
    if request.method == "POST":
        monster = request.POST.get("monster_key")
        combat_log = execute_hunt(profile, monster)
    return render(
        request,
        "characters/hunt.html",
        {"profile": profile, "combat_log": combat_log, "BESTIARY": BESTIARY},
    )
