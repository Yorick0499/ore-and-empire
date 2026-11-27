#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
# See NOTICE for the attribution terms under section 7(b).
"""Local entry point. Use the project's virtual environment Python."""
import os
from pathlib import Path
import secrets
import sys


def main():
    root = Path(__file__).resolve().parent
    os.chdir(root)
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        raise SystemExit(
            "Install dependencies first: python -m pip install -r requirements.txt"
        )
    path = root / ".env"
    if not path.exists():
        try:
            with open(
                path, "x", opener=lambda name, flags: os.open(name, flags, 0o600)
            ) as stream:
                stream.write(
                    "SECRET_KEY=" + secrets.token_urlsafe(64) + "\nDEBUG=True\n"
                )
        except FileExistsError:
            pass
    os.environ.setdefault("ORE_SQLITE_WAL", "1")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ore_empire.settings")
    execute_from_command_line([sys.argv[0], "run_colony", *sys.argv[1:]])


if __name__ == "__main__":
    main()
