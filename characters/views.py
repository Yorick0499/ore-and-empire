from django.shortcuts import render
from .models import PlayerProfile
from .game_logic import start_mining, claim_ore_reward
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
