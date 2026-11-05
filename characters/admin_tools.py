"""Superuser-only game-master operations with transactional audit records."""
from uuid import uuid4
from django import forms
from django.db import transaction
from django.utils import timezone
from .models import PlayerProfile, ItemBluePrint, OwnedItem, AdminAction
from .camp_progression import BY_RANK
from .economy import change_premium
from .game_logic import recover_energy


class ProfileStatsForm(forms.ModelForm):
    class Meta:
        model = PlayerProfile
        fields = ["level", "experience", "skill_points", "strength", "dexterity", "mana", "life", "current_health", "weapon_prot", "ore_balance", "current_energy", "max_energy", "camp", "guild", "arrow_prot", "fire_prot", "magic_prot", "onehand_skill", "twohand_skill", "bow_skill", "crossbow_skill", "lockpick_skill", "pickpock_skill", "magic_skill", "sneaking", "acrobatics"]
        labels = {"level": "Poziom", "experience": "Doświadczenie", "skill_points": "Punkty nauki", "strength": "Siła", "dexterity": "Zręczność", "mana": "Mana", "life": "Maksymalne zdrowie", "current_health": "Aktualne zdrowie", "weapon_prot": "Pancerz", "ore_balance": "Ruda", "current_energy": "Aktualna energia", "max_energy": "Maksymalna energia", "camp": "Obóz", "guild": "Kod rangi (NONE lub kod z drabinki)"}

    def clean(self):
        data = super().clean()
        for field, value in data.items():
            if type(value) is int and not 0 <= value <= 1_000_000_000:
                self.add_error(field, "Wartość musi mieścić się między 0 a miliardem.")
        for field in ("life", "max_energy"):
            if data.get(field, 1) < 1:
                self.add_error(field, "Maksimum musi być dodatnie.")
        if data.get("current_health", 0) > data.get("life", 0) + self.instance.equipment_health:
            self.add_error("current_health", "Zdrowie przekracza maksimum.")
        if data.get("current_energy", 0) > data.get("max_energy", 0):
            self.add_error("current_energy", "Energia przekracza maksimum.")
        rank = BY_RANK.get(data.get("guild"))
        if data.get("guild") != "NONE" and (not rank or rank.camp != data.get("camp")):
            self.add_error("guild", "Ranga musi należeć do wybranego obozu.")
        return data


@transaction.atomic
def administer_player(actor, profile_id, action, payload):
    if not actor.is_active or not actor.is_superuser:
        return False, "Brak uprawnień administratora."
    profile = PlayerProfile.objects.select_for_update().filter(pk=profile_id).first()
    if not profile:
        return False, "Nie znaleziono postaci."
    recover_energy(profile)
    details = {}
    if action == "restore":
        profile.current_energy = profile.max_energy
        profile.current_health = profile.max_health
        profile.energy_updated_at = profile.health_updated_at = timezone.now()
        profile.save()
    elif action == "item":
        try:
            quantity = int(payload.get("quantity", 1))
            blueprint_id = int(payload.get("blueprint", 0))
        except (ValueError, TypeError):
            return False, "Nieprawidłowy przedmiot lub liczba."
        blueprint = ItemBluePrint.objects.filter(pk=blueprint_id).first()
        if not blueprint or not 1 <= quantity <= 20:
            return False, "Wybierz przedmiot i liczbę od 1 do 20."
        OwnedItem.objects.bulk_create([OwnedItem(owner=profile, blueprint=blueprint) for _ in range(quantity)])
        details = {"blueprint_id": blueprint.pk, "quantity": quantity}
    elif action == "premium":
        try:
            amount = int(payload.get("amount", 0))
        except (ValueError, TypeError):
            return False, "Nieprawidłowa liczba odłamków."
        if not 1 <= amount <= 10000:
            return False, "Możesz przyznać od 1 do 10000 odłamków jednorazowo."
        change_premium(profile, amount, "Nadanie administratora", "admin:" + str(uuid4()))
        details = {"amount": amount}
    elif action == "stats":
        before = {field: getattr(profile, field) for field in ProfileStatsForm.Meta.fields}
        form = ProfileStatsForm(payload, instance=profile)
        if not form.is_valid():
            return False, " ".join(f"{field}: {', '.join(errors)}" for field, errors in form.errors.items())
        profile = form.save(commit=False)
        profile.energy_updated_at = profile.health_updated_at = timezone.now()
        profile.save()
        details = {"before": before, "after": form.cleaned_data}
    else:
        return False, "Nieznana operacja."
    AdminAction.objects.create(actor=actor, profile=profile, action=action, details=details)
    return True, "Zmiany zapisane w kronice administratora."
