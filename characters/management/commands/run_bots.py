from characters.world_clock import polish_day
import time
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction
from characters.models import PlayerProfile
from characters.bots import tick_bot


class Command(BaseCommand):
    help = "Run bounded bot rounds or an explicit continuous scheduler; no AI API is needed."

    def add_arguments(self, parser):
        parser.add_argument("--force-active",action="store_true",help="Test aktywnych tur bez sesji i symulowanych zakupów; tylko ograniczona liczba rund.")
        parser.add_argument("--loop", action="store_true", help="Run a continuous scheduler; do not combine with play.py bots.")
        parser.add_argument("--interval", type=float, default=5)
        parser.add_argument("--rounds", type=int, default=1, help="Bounded rounds when --loop is not set (1-100000).")
        parser.add_argument(
            "--create-only",
            action="store_true",
            help="Initialize bot accounts without running any actions.",
        )
        parser.add_argument(
            "--create",
            type=int,
            default=0,
            help="Create this many missing colony-bot-N accounts (max 100).",
        )
        parser.add_argument(
            "--limit", type=int, default=20, help="Maximum bots to tick (1-100)."
        )

    def handle(self, *args, **options):
        if not 0 <= options["create"] <= 100 or not 1 <= options["limit"] <= 100:
            raise CommandError("--create must be 0-100 and --limit 1-100")
        if not 1 <= options["interval"] <= 3600 or not 1 <= options["rounds"] <= 100000:
            raise CommandError("--interval must be 1-3600; --rounds must be 1-100000")
        if options["force_active"] and options["loop"]:raise CommandError("--force-active nie działa z --loop")
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
        from characters.bot_personalities import assignment
        for p in PlayerProfile.objects.filter(is_bot=True,bot_personality=''):
            p.bot_personality,p.bot_session_shift=assignment(p.pk,p.world_id)
            p.save(update_fields=['bot_personality','bot_session_shift'])
        if options["create_only"]:
            self.stdout.write("Bot population initialized without taking actions.")
            return
        from characters.scheduler_lease import SchedulerGuard,LeaseLost
        from characters.worlds import current_world
        guard=SchedulerGuard(current_world())
        try:guard.acquire()
        except LeaseLost as exc:raise CommandError(str(exc)) from exc
        from characters.world_events import ensure_world_events
        from django.utils import timezone
        event_day = None
        round_number = 0
        try:
            while options["loop"] or round_number < options["rounds"]:
                if event_day != polish_day():
                    with guard.work():ensure_world_events()
                    event_day = polish_day()
                from characters.worlds import current_world
                profiles = PlayerProfile.objects.filter(world=current_world(),is_bot=True, user__is_active=True).order_by("pk")[: options["limit"]]
                for profile in profiles:
                    try:
                        action, success = tick_bot(profile,lease=guard,force_active=options["force_active"])
                        self.stdout.write(f"{profile.user.username}: {action} {'ok' if success else 'denied'}")
                    except LeaseLost:
                        raise
                    except Exception as exc:
                        self.stderr.write(f"{profile.user.username}: bot skipped ({type(exc).__name__})")
                round_number += 1
                if options["loop"] or round_number < options["rounds"]:
                    time.sleep(options["interval"])
        except KeyboardInterrupt:
            self.stdout.write("Bot scheduler stopped; progress retained.")
        except LeaseLost as exc:
            raise CommandError(str(exc)) from exc
        finally:
            guard.release()
