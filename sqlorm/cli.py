"""
SQLORM CLI
==========

Command-line interface for migrations.

Usage:
    sqlorm makemigrations --models mymodels.py
    sqlorm migrate --models mymodels.py
"""

import argparse
import sys
from pathlib import Path


def _import_models(script_path: str):
    """Import user's model definitions."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("user_models", script_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules["user_models"] = module
        spec.loader.exec_module(module)


def _ensure_configured():
    """Ensure Django is configured."""
    import django
    from django.conf import settings

    if not settings.configured:
        from sqlorm.config import DEFAULT_SETTINGS

        settings.configure(
            **DEFAULT_SETTINGS,
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": "db.sqlite3",
                }
            },
        )

    if not django.apps.apps.ready:
        django.setup()


def makemigrations(app_label: str = "sqlorm_app", name: str = None, verbosity: int = 1):
    """Create new migrations."""
    _ensure_configured()
    from django.core.management import call_command

    kwargs = {"verbosity": verbosity, "interactive": False}
    if name:
        kwargs["name"] = name

    try:
        call_command("makemigrations", app_label, **kwargs)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def migrate(app_label: str = None, verbosity: int = 1):
    """Apply migrations."""
    _ensure_configured()
    from django.core.management import call_command

    args = [app_label] if app_label else []

    try:
        call_command("migrate", *args, verbosity=verbosity, interactive=False)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="sqlorm", description="SQLORM - Django ORM without the project structure"
    )
    parser.add_argument("--version", action="version", version="3.0.0")
    parser.add_argument("-v", "--verbosity", type=int, default=1, choices=[0, 1, 2])
    parser.add_argument(
        "--models", required=True, help="Python file with model definitions"
    )

    subparsers = parser.add_subparsers(dest="command")

    # makemigrations
    mm = subparsers.add_parser("makemigrations", help="Create migrations")
    mm.add_argument("-n", "--name", help="Migration name")

    # migrate
    subparsers.add_parser("migrate", help="Apply migrations")

    # showmigrations
    subparsers.add_parser("showmigrations", help="Show migrations")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Import user models
    _import_models(args.models)

    if args.command == "makemigrations":
        success = makemigrations(name=args.name, verbosity=args.verbosity)
    elif args.command == "migrate":
        success = migrate(verbosity=args.verbosity)
    elif args.command == "showmigrations":
        _ensure_configured()
        from django.core.management import call_command

        call_command("showmigrations", verbosity=args.verbosity)
        success = True
    else:
        parser.print_help()
        success = False

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
