from characters.world_clock import polish_day
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
        parser.add_argument("--history-days",type=int,default=30,help="Retain raw bot decisions for this many complete UTC days; daily aggregates remain.")

    def handle(self, *args, **options):
        if not 1 <= options["history_days"] <= 3650:
            raise CommandError("--history-days must be 1-3650")
        if not 0 <= options["bots"] <= 100:
            raise CommandError("--bots must be 0-100")
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
            call_command("seed_equipment", stdout=self.stdout)
            call_command("seed_catalog", stdout=self.stdout)
            call_command("seed_crafting", stdout=self.stdout)
            call_command("seed_adventures", stdout=self.stdout)
            call_command("seed_story", stdout=self.stdout)
            from characters.worlds import current_world
            world=current_world()
            if not world.configured:
                world.bot_count=options["bots"];world.save(update_fields=["bot_count"])
            active_bots=world.bot_count
            if options["setup_admin"]:
                call_command("create_game_admin", stdout=self.stdout)
            if active_bots:
                call_command(
                    "run_bots",
                    create=active_bots,
                    create_only=True,
                    limit=active_bots,
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
            from characters.bot_scheduler import BotScheduler
            scheduler=BotScheduler(options['interval'],clock=time.monotonic)
            event_day=None
            refresh_at=0
            def run_one(pk):
                profile=PlayerProfile.objects.select_related('user').filter(pk=pk,is_bot=True,user__is_active=True).first()
                if not profile:return 'wait',False
                try:
                    action,success=tick_bot(profile)
                except Exception as exc:
                    self.stderr.write(f"{profile.user.username}: bot skipped ({type(exc).__name__})")
                    return 'wait',False
                if action!='wait':self.stdout.write(f"{profile.user.username}: {action} {'ok' if success else 'denied'}")
                return action,success
            try:
                while True:
                    now=time.monotonic()
                    if now>=refresh_at:
                        world=current_world()
                        scheduler.population(PlayerProfile.objects.filter(is_bot=True,user__is_active=True,world=world).order_by('pk').values_list('pk',flat=True)[:world.bot_count])
                        refresh_at=now+5
                        from characters.world_events import ensure_world_events
                        if event_day!=polish_day():
                            ensure_world_events()
                            try:call_command('archive_bot_history',days=options['history_days'],stdout=self.stdout)
                            except Exception as exc:self.stderr.write(f"History archival skipped ({type(exc).__name__}); raw records retained.")
                            event_day=polish_day()
                    server.timeout=scheduler.timeout()
                    server.handle_request()
                    scheduler.step(run_one)
            except KeyboardInterrupt:
                self.stdout.write("Colony stopped. Saved progress retained.")
