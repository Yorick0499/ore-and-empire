from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction
from characters.models import PlayerProfile
from characters.bots import tick_bot


class Command(BaseCommand):
    help = "Run one bounded action per bot. No background loop or AI API is started."

    def add_arguments(self, parser):
        parser.add_argument(
            "--create-only",
            action="store_true",
            help="Initialize bot accounts without running any actions.",
        )
        parser.add_argument(
            "--create",
            type=int,
            default=0,
            help="Create this many missing colony-bot-N accounts (max 20).",
        )
        parser.add_argument(
            "--limit", type=int, default=20, help="Maximum bots to tick (1-100)."
        )

    def handle(self, *args, **options):
        if not 0 <= options["create"] <= 20 or not 1 <= options["limit"] <= 100:
            raise CommandError("--create must be 0-20 and --limit 1-100")
        with transaction.atomic():
            for number in range(1, options["create"] + 1):
                username = f"colony-bot-{number}"
                user, created = User.objects.get_or_create(username=username)
                if not created and not user.playerprofile.is_bot:
                    raise CommandError(
                        f"{username} belongs to a human; refusing to convert it"
                    )
                if created:
                    user.set_unusable_password()
                    user.save(update_fields=["password"])
                    PlayerProfile.objects.filter(user=user).update(
                        is_bot=True,
                        bot_role=("hunter", "trader", "miner")[(number - 1) % 3],
                    )
        if options["create_only"]:
            self.stdout.write("Bot population initialized without taking actions.")
            return
        profiles = PlayerProfile.objects.filter(
            is_bot=True, user__is_active=True
        ).order_by("pk")[: options["limit"]]
        for profile in profiles:
            action, success = tick_bot(profile)
            self.stdout.write(
                f"{profile.user.username}: {action} {'ok' if success else 'denied'}"
            )
