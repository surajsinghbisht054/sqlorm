"""
SQLORM CLI Module
=================

Command-line interface for SQLORM that provides Django-like migration commands
without requiring manage.py or a Django project structure.

Commands:
    sqlorm makemigrations [app_label] - Create new migrations
    sqlorm migrate [app_label] - Apply migrations
    sqlorm showmigrations - Show migration status
    sqlorm sqlmigrate <app_label> <migration_name> - Show SQL for a migration
    sqlorm shell - Open interactive Python shell with models loaded
    sqlorm dbshell - Open database shell
    sqlorm createsuperuser - Create admin user (if using auth)
    sqlorm inspectdb - Generate models from existing database

Usage:
    # In your script, first define models then run CLI:
    $ python -c "import mymodels" && sqlorm makemigrations
    $ sqlorm migrate

    # Or use the programmatic interface:
    >>> from sqlorm.cli import makemigrations, migrate
    >>> makemigrations()
    >>> migrate()
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional


def _ensure_django_configured():
    """Ensure Django is configured before running commands."""
    import django
    from django.conf import settings

    if not settings.configured:
        # Set up minimal configuration
        from sqlorm.config import DEFAULT_SETTINGS, _current_settings

        if _current_settings:
            settings.configure(**_current_settings)
        else:
            # Default SQLite configuration
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


def _discover_models(script_path: Optional[str] = None):
    """
    Discover and import models from user scripts.

    This function looks for Python files in the current directory
    that might contain SQLORM model definitions.
    """
    if script_path:
        # Import specific script
        import importlib.util

        spec = importlib.util.spec_from_file_location("user_models", script_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules["user_models"] = module
            spec.loader.exec_module(module)
        return

    # Look for common model file patterns
    cwd = Path.cwd()
    model_patterns = ["models.py", "*_models.py", "model*.py"]

    for pattern in model_patterns:
        for path in cwd.glob(pattern):
            if path.is_file() and not path.name.startswith("_"):
                try:
                    import importlib.util

                    spec = importlib.util.spec_from_file_location(path.stem, str(path))
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[path.stem] = module
                        spec.loader.exec_module(module)
                except Exception as e:
                    print(f"Warning: Could not import {path}: {e}")


def makemigrations(
    app_label: str = "sqlorm_models",
    name: Optional[str] = None,
    dry_run: bool = False,
    merge: bool = False,
    empty: bool = False,
    verbosity: int = 1,
) -> bool:
    """
    Create new migrations based on model changes.

    Args:
        app_label: App label (default: sqlorm_models)
        name: Custom migration name
        dry_run: Don't actually write migrations
        merge: Merge conflicting migrations
        empty: Create an empty migration
        verbosity: Output verbosity level

    Returns:
        True if successful
    """
    _ensure_django_configured()

    from django.core.management import call_command

    args = [app_label]
    kwargs = {
        "verbosity": verbosity,
        "dry_run": dry_run,
        "merge": merge,
        "empty": empty,
        "interactive": False,
    }

    if name:
        kwargs["name"] = name

    try:
        call_command("makemigrations", *args, **kwargs)
        return True
    except Exception as e:
        if verbosity > 0:
            print(f"Error creating migrations: {e}")
        return False


def migrate(
    app_label: Optional[str] = None,
    migration_name: Optional[str] = None,
    database: str = "default",
    fake: bool = False,
    fake_initial: bool = False,
    run_syncdb: bool = False,
    verbosity: int = 1,
) -> bool:
    """
    Apply migrations to the database.

    Args:
        app_label: App label to migrate (None = all apps)
        migration_name: Specific migration to migrate to
        database: Database alias
        fake: Mark migrations as applied without running
        fake_initial: Fake initial migrations if tables exist
        run_syncdb: Create tables for apps without migrations
        verbosity: Output verbosity level

    Returns:
        True if successful
    """
    _ensure_django_configured()

    from django.core.management import call_command

    args = []
    if app_label:
        args.append(app_label)
        if migration_name:
            args.append(migration_name)

    kwargs = {
        "verbosity": verbosity,
        "database": database,
        "fake": fake,
        "fake_initial": fake_initial,
        "run_syncdb": run_syncdb,
        "interactive": False,
    }

    try:
        call_command("migrate", *args, **kwargs)
        return True
    except Exception as e:
        if verbosity > 0:
            print(f"Error applying migrations: {e}")
        return False


def showmigrations(
    app_labels: Optional[List[str]] = None,
    database: str = "default",
    verbosity: int = 1,
    plan: bool = False,
) -> bool:
    """
    Show all migrations and their status.

    Args:
        app_labels: App labels to show (None = all)
        database: Database alias
        verbosity: Output verbosity level
        plan: Show migration plan

    Returns:
        True if successful
    """
    _ensure_django_configured()

    from django.core.management import call_command

    args = app_labels or []
    kwargs = {
        "verbosity": verbosity,
        "database": database,
    }

    if plan:
        kwargs["plan"] = True

    try:
        call_command("showmigrations", *args, **kwargs)
        return True
    except Exception as e:
        if verbosity > 0:
            print(f"Error showing migrations: {e}")
        return False


def sqlmigrate(
    app_label: str,
    migration_name: str,
    database: str = "default",
    backwards: bool = False,
    verbosity: int = 1,
) -> Optional[str]:
    """
    Show the SQL for a migration.

    Args:
        app_label: App label
        migration_name: Migration name
        database: Database alias
        backwards: Show SQL for unapplying
        verbosity: Output verbosity level

    Returns:
        SQL string or None if failed
    """
    _ensure_django_configured()

    from io import StringIO

    from django.core.management import call_command

    output = StringIO()

    try:
        call_command(
            "sqlmigrate",
            app_label,
            migration_name,
            database=database,
            backwards=backwards,
            verbosity=verbosity,
            stdout=output,
        )
        return output.getvalue()
    except Exception as e:
        if verbosity > 0:
            print(f"Error getting SQL: {e}")
        return None


def inspectdb(
    database: str = "default",
    include_views: bool = False,
    table_names: Optional[List[str]] = None,
) -> Optional[str]:
    """
    Generate model code from existing database tables.

    Args:
        database: Database alias
        include_views: Include database views
        table_names: Specific tables to inspect (None = all)

    Returns:
        Generated model code or None if failed
    """
    _ensure_django_configured()

    from io import StringIO

    from django.core.management import call_command

    output = StringIO()

    args = table_names or []
    kwargs = {
        "database": database,
        "include_views": include_views,
        "stdout": output,
    }

    try:
        call_command("inspectdb", *args, **kwargs)
        result = output.getvalue()

        # Replace Django imports with sqlorm imports
        result = result.replace(
            "from django.db import models", "from sqlorm import Model, fields"
        )
        result = result.replace("models.Model", "Model")
        result = result.replace("models.", "fields.")

        return result
    except Exception as e:
        print(f"Error inspecting database: {e}")
        return None


def syncdb(database: str = "default", verbosity: int = 1) -> bool:
    """
    Quick sync - create tables for all models without migrations.

    This is a convenience function for development. For production,
    use makemigrations + migrate.

    Args:
        database: Database alias
        verbosity: Output verbosity level

    Returns:
        True if successful
    """
    _ensure_django_configured()

    from sqlorm.base import create_all_tables

    try:
        created = create_all_tables(verbosity=verbosity, using=database)
        if verbosity > 0 and created:
            print(f"Created tables: {', '.join(created)}")
        return True
    except Exception as e:
        if verbosity > 0:
            print(f"Error syncing database: {e}")
        return False


def shell():
    """Open an interactive Python shell with models loaded."""
    _ensure_django_configured()

    try:
        from django.core.management import call_command

        call_command("shell")
    except Exception as e:
        print(f"Error opening shell: {e}")
        # Fallback to basic Python shell
        import code

        from sqlorm.base import get_registered_models

        models = get_registered_models()
        banner = "SQLORM Shell\nAvailable models: " + ", ".join(models.keys())

        code.interact(banner=banner, local=dict(models))


def dbshell(database: str = "default"):
    """Open a database shell."""
    _ensure_django_configured()

    try:
        from django.core.management import call_command

        call_command("dbshell", database=database)
    except Exception as e:
        print(f"Error opening database shell: {e}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="sqlorm",
        description="SQLORM - Django ORM for standalone scripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sqlorm makemigrations          Create migrations for model changes
  sqlorm migrate                 Apply all migrations
  sqlorm showmigrations          Show migration status
  sqlorm syncdb                  Quick sync (create tables without migrations)
  sqlorm inspectdb               Generate models from existing database
  sqlorm shell                   Open Python shell with models
  sqlorm dbshell                 Open database shell
        """,
    )

    parser.add_argument("--version", action="version", version="%(prog)s 2.1.0")

    parser.add_argument(
        "-v",
        "--verbosity",
        type=int,
        choices=[0, 1, 2, 3],
        default=1,
        help="Verbosity level (0-3)",
    )

    parser.add_argument("--database", default="default", help="Database alias to use")

    parser.add_argument(
        "--settings", help="Python path to settings module (or JSON file)"
    )

    parser.add_argument(
        "--models", help="Python file containing model definitions to import"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # makemigrations
    mm_parser = subparsers.add_parser(
        "makemigrations", help="Create new migrations based on model changes"
    )
    mm_parser.add_argument(
        "app_label",
        nargs="?",
        default="sqlorm_models",
        help="App label (default: sqlorm_models)",
    )
    mm_parser.add_argument("-n", "--name", help="Custom migration name")
    mm_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't write migrations, just show what would be done",
    )
    mm_parser.add_argument(
        "--merge", action="store_true", help="Merge conflicting migrations"
    )
    mm_parser.add_argument(
        "--empty", action="store_true", help="Create an empty migration"
    )

    # migrate
    mig_parser = subparsers.add_parser(
        "migrate", help="Apply migrations to the database"
    )
    mig_parser.add_argument("app_label", nargs="?", help="App label to migrate")
    mig_parser.add_argument("migration_name", nargs="?", help="Migration to migrate to")
    mig_parser.add_argument(
        "--fake", action="store_true", help="Mark migrations as applied without running"
    )
    mig_parser.add_argument(
        "--fake-initial",
        action="store_true",
        help="Fake initial migrations if tables exist",
    )
    mig_parser.add_argument(
        "--run-syncdb",
        action="store_true",
        help="Create tables for apps without migrations",
    )

    # showmigrations
    sm_parser = subparsers.add_parser("showmigrations", help="Show migration status")
    sm_parser.add_argument("app_labels", nargs="*", help="App labels to show")
    sm_parser.add_argument("--plan", action="store_true", help="Show migration plan")

    # sqlmigrate
    sqlm_parser = subparsers.add_parser("sqlmigrate", help="Show SQL for a migration")
    sqlm_parser.add_argument("app_label", help="App label")
    sqlm_parser.add_argument("migration_name", help="Migration name")
    sqlm_parser.add_argument(
        "--backwards", action="store_true", help="Show SQL for unapplying"
    )

    # syncdb
    sync_parser = subparsers.add_parser(
        "syncdb", help="Quick sync - create tables without migrations"
    )

    # inspectdb
    insp_parser = subparsers.add_parser(
        "inspectdb", help="Generate models from existing database"
    )
    insp_parser.add_argument(
        "table_names", nargs="*", help="Specific tables to inspect"
    )
    insp_parser.add_argument(
        "--include-views", action="store_true", help="Include database views"
    )

    # shell
    subparsers.add_parser("shell", help="Open Python shell with models loaded")

    # dbshell
    subparsers.add_parser("dbshell", help="Open database shell")

    args = parser.parse_args()

    # Load settings if specified
    if args.settings:
        if args.settings.endswith(".json"):
            from sqlorm import configure_from_file

            configure_from_file(args.settings)
        else:
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", args.settings)

    # Import models if specified
    if args.models:
        _discover_models(args.models)
    else:
        _discover_models()

    # Execute command
    if args.command == "makemigrations":
        success = makemigrations(
            app_label=args.app_label,
            name=args.name,
            dry_run=args.dry_run,
            merge=args.merge,
            empty=args.empty,
            verbosity=args.verbosity,
        )
        sys.exit(0 if success else 1)

    elif args.command == "migrate":
        success = migrate(
            app_label=args.app_label,
            migration_name=args.migration_name,
            database=args.database,
            fake=args.fake,
            fake_initial=args.fake_initial,
            run_syncdb=args.run_syncdb,
            verbosity=args.verbosity,
        )
        sys.exit(0 if success else 1)

    elif args.command == "showmigrations":
        success = showmigrations(
            app_labels=args.app_labels if args.app_labels else None,
            database=args.database,
            verbosity=args.verbosity,
            plan=args.plan,
        )
        sys.exit(0 if success else 1)

    elif args.command == "sqlmigrate":
        sql = sqlmigrate(
            app_label=args.app_label,
            migration_name=args.migration_name,
            database=args.database,
            backwards=args.backwards,
            verbosity=args.verbosity,
        )
        if sql:
            print(sql)
            sys.exit(0)
        sys.exit(1)

    elif args.command == "syncdb":
        success = syncdb(
            database=args.database,
            verbosity=args.verbosity,
        )
        sys.exit(0 if success else 1)

    elif args.command == "inspectdb":
        code = inspectdb(
            database=args.database,
            include_views=args.include_views,
            table_names=args.table_names if args.table_names else None,
        )
        if code:
            print(code)
            sys.exit(0)
        sys.exit(1)

    elif args.command == "shell":
        shell()

    elif args.command == "dbshell":
        dbshell(database=args.database)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
