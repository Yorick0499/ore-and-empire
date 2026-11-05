"""Single-process local world: HTTP requests and bot rounds never overlap."""

import time
from wsgiref.simple_server import make_server

from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.management import BaseCommand, CommandError, call_command
from django.core.wsgi import get_wsgi_application
from characters.bots import tick_bot
from characters.models import PlayerProfile


class Command(BaseCommand):
    help = (
        "Start a local/LAN game and a living bot population. Not a production server."
    )

    def add_arguments(self, parser):
        parser.add_argument("--setup-admin", action="store_true", help="Create the local administrator and a private credential file.")
        parser.add_argument("--host", default="127.0.0.1")
        parser.add_argument("--port", type=int, default=8000)
        parser.add_argument("--bots", type=int, default=6)
        parser.add_argument("--interval", type=float, default=5)

    def handle(self, *args, **options):
        if not 0 <= options["bots"] <= 20:
            raise CommandError("--bots must be 0-20")
        if not 1 <= options["port"] <= 65535:
            raise CommandError("--port must be 1-65535")
        if not 1 <= options["interval"] <= 3600:
            raise CommandError("--interval must be 1-3600 seconds")
        # Bind first: a busy port must not create accounts or change the world.
        try:
            server = make_server(
                options["host"],
                options["port"],
                StaticFilesHandler(get_wsgi_application()),
            )
        except OSError as exc:
            raise CommandError(f"Cannot start local server: {exc}") from exc
        with server:
            call_command("migrate", interactive=False, stdout=self.stdout)
            call_command("seed_world", stdout=self.stdout)
            call_command("seed_adventures", stdout=self.stdout)
            call_command("seed_story", stdout=self.stdout)
            if options["setup_admin"]:
                call_command("create_game_admin", stdout=self.stdout)
            if options["bots"]:
                call_command(
                    "run_bots",
                    create=options["bots"],
                    create_only=True,
                    limit=options["bots"],
                    stdout=self.stdout,
                )
            self.stdout.write(
                self.style.SUCCESS(
                    "Colony started. Register a character in your browser. Ctrl+C stops the game and bots; progress is saved."
                )
            )
            self.stdout.write(
                f"Listening on {options['host']}:{options['port']}; bot interval {options['interval']}s"
            )
            if options["host"] != "127.0.0.1":
                self.stdout.write(
                    "LAN mode: configure ALLOWED_HOSTS with your machine's LAN address. This server is for trusted local networks, not public hosting."
                )
            event_day = None
            next_round = time.monotonic() + options["interval"]
            server.timeout = min(1, options["interval"])
            try:
                while True:
                    server.handle_request()
                    if time.monotonic() >= next_round:
                        from django.utils import timezone
                        from characters.world_events import ensure_world_events
                        if event_day != timezone.now().date():
                            ensure_world_events()
                            event_day = timezone.now().date()
                        profiles = PlayerProfile.objects.filter(
                            is_bot=True, user__is_active=True
                        ).order_by("pk")[: options["bots"]]
                        for profile in profiles:
                            try:
                                action, success = tick_bot(profile)
                            except Exception as exc:
                                # A broken policy must not take down the local game.
                                self.stderr.write(
                                    f"{profile.user.username}: bot skipped ({type(exc).__name__})"
                                )
                                continue
                            if action != "wait":
                                self.stdout.write(
                                    f"{profile.user.username}: {action} {'ok' if success else 'denied'}"
                                )
                        next_round = time.monotonic() + options["interval"]
            except KeyboardInterrupt:
                self.stdout.write("Colony stopped. Saved progress retained.")
