from django.core.management.base import BaseCommand
from django.db import transaction
from characters.models import ItemBluePrint


class Command(BaseCommand):
    help = "Create missing starter merchant stock without resetting existing prices or players."

    @transaction.atomic
    def handle(self, *args, **options):
        for name, damage, strength, value in [
            ("Zardzewiały miecz", 12, 10, 25),
            ("Miecz kopacza", 20, 15, 80),
            ("Miecz strażnika", 35, 30, 240),
            ("Ostrze najemnika", 50, 45, 500),
        ]:
            if ItemBluePrint.objects.filter(name=name).exists():
                continue
            ItemBluePrint.objects.create(
                name=name,
                **{
                    "damage": damage,
                    "required_strength": strength,
                    "base_value": value,
                },
            )
        self.stdout.write(
            self.style.SUCCESS(
                "Starter stock ready; existing items and players preserved."
            )
        )
