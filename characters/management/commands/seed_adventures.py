from django.core.management.base import BaseCommand
from django.db import transaction
from characters.adventures import ADVENTURES
from characters.models import AdventureTemplate, ItemBluePrint, StoreProduct
from characters.world_events import ensure_world_events


class Command(BaseCommand):
    help = "Add missing quests, shard-shop stock and event schedules, preserving admin edits."

    @transaction.atomic
    def handle(self, *args, **options):
        for key, name, description, level, duration, energy, ore, experience, premium in ADVENTURES:
            AdventureTemplate.objects.get_or_create(key=key, defaults=dict(name=name, description=description, level=level, duration_seconds=duration, energy_cost=energy, ore_reward=ore, experience_reward=experience, premium_reward=premium))
        blade, _ = ItemBluePrint.objects.get_or_create(name="Miecz runiczny", defaults=dict(damage=42, required_strength=30, base_value=320))
        staff, _ = ItemBluePrint.objects.get_or_create(name="Pałka z kolcami", defaults=dict(damage=22, required_strength=15, base_value=90))
        for key, name, description, kind, price, level, effect, blueprint, art in (
            ("rice_spirit", "Ryżówka", "Łyk mocnego napoju: odnawia do 25 energii.", "energy", 3, 0, 25, None, "rice_spirit"),
            ("healing_essence", "Esencja lecznicza", "Od razu odnawia do 60 punktów zdrowia.", "health", 2, 0, 60, None, "healing_essence"),
            ("battle_staff", "Pałka z kolcami", "Solidny oręż na początek służby w kolonii. Obrażenia 22, wymagana siła 15.", "weapon", 8, 3, 0, staff, "battle_staff"),
            ("rune_sword", "Miecz runiczny", "Ostrze dla doświadczonego wojownika. Obrażenia 42, wymagana siła 30.", "weapon", 18, 8, 0, blade, "rune_sword"),
        ):
            StoreProduct.objects.get_or_create(key=key, defaults=dict(name=name, description=description, kind=kind, price=price, level=level, effect=effect, blueprint=blueprint, art_key=art))
        ensure_world_events()
        self.stdout.write(self.style.SUCCESS("Quest pool, shard shop and event calendar ready; existing edits retained."))
