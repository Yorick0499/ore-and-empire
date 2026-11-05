"""Explicit local setup: no default password is stored in source or migrations."""
import json
import os
from pathlib import Path
import secrets
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Create a local superuser and write generated credentials to .admin-access.json (ignored by Git)."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="colony-admin")

    @transaction.atomic
    def handle(self, *args, **options):
        username = options["username"]
        if not username or len(username) > 150:
            raise CommandError("Invalid username")
        path = Path(settings.BASE_DIR) / ".admin-access.json"
        user = User.objects.filter(username=username).first()
        if user:
            try:
                saved = json.loads(path.read_text())
            except (OSError, ValueError):
                saved = {}
            if saved.get("username") != username or not user.is_superuser or not user.check_password(saved.get("password", "")):
                raise CommandError("Account already exists; no credentials were changed. Use Django changepassword if needed.")
            self.stdout.write(f"Administrator already configured. Credentials: {path}")
            return
        password = secrets.token_urlsafe(24)
        User.objects.create_superuser(username=username, password=password)
        # Exclusive creation prevents overwriting another administrator's file.
        try:
            with open(path, "x", opener=lambda name, flags: os.open(name, flags, 0o600)) as stream:
                json.dump({"username": username, "password": password}, stream)
        except FileExistsError as exc:
            raise CommandError("Credential file already exists; no account was created.") from exc
        self.stdout.write(self.style.SUCCESS(f"Administrator created. Read credentials at {path}; sign in at /konto/logowanie/ or /admin/."))
