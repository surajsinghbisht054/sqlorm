"""
SQLORM Configuration
====================

Configure Django ORM for standalone usage without a Django project.

Example:
    >>> from sqlorm import configure
    >>> configure({
    ...     'ENGINE': 'django.db.backends.sqlite3',
    ...     'NAME': 'mydb.sqlite3',
    ... }, migrations_dir='./migrations')
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .exceptions import ConfigurationError

logger = logging.getLogger("sqlorm")

# Global state
_django_configured = False
_current_settings = {}
_migrations_dir = None

DEFAULT_SETTINGS = {
    "DEBUG": False,
    "INSTALLED_APPS": [
        "django.contrib.contenttypes",
        "sqlorm.app",
    ],
    "DATABASES": {},
    "DEFAULT_AUTO_FIELD": "django.db.models.BigAutoField",
    "USE_TZ": True,
    "TIME_ZONE": "UTC",
}


def _validate_database_config(database: Dict[str, Any]) -> None:
    """Validate database configuration."""
    if not isinstance(database, dict):
        raise ConfigurationError("Database configuration must be a dictionary")
    if "ENGINE" not in database:
        raise ConfigurationError("Database config must include 'ENGINE'")
    if "NAME" not in database:
        raise ConfigurationError("Database config must include 'NAME'")


def _setup_django():
    """Initialize Django with current settings."""
    global _django_configured

    if _django_configured:
        return

    try:
        import django
        from django.conf import settings

        if not settings.configured:
            settings.configure(**_current_settings)

        django.setup()
        _django_configured = True
        logger.debug("Django ORM configured")

    except ImportError as e:
        raise ConfigurationError("Django not installed. Run: pip install django") from e
    except Exception as e:
        raise ConfigurationError(f"Failed to configure Django: {e}") from e


def configure(
    database: Dict[str, Any],
    *,
    migrations_dir: Optional[str] = None,
    debug: bool = False,
    time_zone: str = "UTC",
    use_tz: bool = True,
    **extra_settings,
) -> None:
    """
    Configure SQLORM with a database connection.

    Args:
        database: Database configuration dict with ENGINE and NAME keys
        migrations_dir: Path to store migrations (required for makemigrations)
        debug: Enable debug mode
        time_zone: Timezone string (default: UTC)
        use_tz: Use timezone-aware datetimes
        **extra_settings: Additional Django settings

    Example:
        >>> configure({
        ...     'ENGINE': 'django.db.backends.sqlite3',
        ...     'NAME': 'mydb.sqlite3',
        ... }, migrations_dir='./migrations')
    """
    global _current_settings, _django_configured, _migrations_dir

    _validate_database_config(database)

    _current_settings = {
        **DEFAULT_SETTINGS,
        "DEBUG": debug,
        "TIME_ZONE": time_zone,
        "USE_TZ": use_tz,
        "DATABASES": {"default": database},
        **extra_settings,
    }

    # Set migrations directory
    if migrations_dir:
        _migrations_dir = Path(migrations_dir).resolve()
        _migrations_dir.mkdir(parents=True, exist_ok=True)

        # Create __init__.py if not exists
        init_file = _migrations_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text("")

        _current_settings["MIGRATION_MODULES"] = {
            "sqlorm_app": str(_migrations_dir),
        }

    if _django_configured:
        from django.conf import settings

        for key, value in _current_settings.items():
            setattr(settings, key, value)
    else:
        _setup_django()


def configure_from_file(file_path: Union[str, Path]) -> None:
    """
    Configure from a JSON file.

    Args:
        file_path: Path to JSON config file

    Example config.json:
        {
            "database": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": "mydb.sqlite3"
            },
            "migrations_dir": "./migrations"
        }
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise ConfigurationError(f"Config file not found: {file_path}")

    with open(file_path) as f:
        config = json.load(f)

    database = config.pop("database", None)
    if not database:
        raise ConfigurationError("Config must include 'database' key")

    configure(database, **config)


def get_migrations_dir() -> Optional[Path]:
    """Get the configured migrations directory."""
    return _migrations_dir


def is_configured() -> bool:
    """Check if SQLORM has been configured."""
    return _django_configured
