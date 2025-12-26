"""
SQLORM Configuration Module
===========================

This module handles Django settings configuration, allowing you to use
Django's ORM without a full Django project structure.

The configuration system supports:
- Direct dictionary configuration
- Configuration from JSON/YAML files
- Environment variable configuration
- Multiple database configurations with aliases

Example:
    >>> from sqlorm import configure, configure_databases
    >>>
    >>> # Simple SQLite configuration
    >>> configure({
    ...     'ENGINE': 'django.db.backends.sqlite3',
    ...     'NAME': 'mydb.sqlite3',
    ... })
    >>>
    >>> # Multiple database configuration (Django-like)
    >>> configure_databases({
    ...     'default': {
    ...         'ENGINE': 'django.db.backends.sqlite3',
    ...         'NAME': 'main.sqlite3',
    ...     },
    ...     'analytics': {
    ...         'ENGINE': 'django.db.backends.sqlite3',
    ...         'NAME': 'analytics.sqlite3',
    ...     },
    ... })
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .exceptions import ConfigurationError

# Logger for this module
logger = logging.getLogger("sqlorm.config")

# Global state to track if Django has been configured
_django_configured = False
_current_settings = {}
_configured_databases = {}

# Default Django settings for standalone usage
# Includes sqlorm.models_app for the migration system
DEFAULT_SETTINGS = {
    "DEBUG": True,
    "INSTALLED_APPS": [
        "django.contrib.contenttypes",
        "sqlorm.models_app",  # SQLORM models container app
    ],
    "DATABASES": {},
    "DEFAULT_AUTO_FIELD": "django.db.models.BigAutoField",
    "USE_TZ": True,
    "TIME_ZONE": "UTC",
}


def _validate_database_config(database: Dict[str, Any]) -> None:
    """
    Validate a database configuration dictionary.

    Args:
        database: Database configuration to validate

    Raises:
        ConfigurationError: If required fields are missing
    """
    if not isinstance(database, dict):
        raise ConfigurationError("Database configuration must be a dictionary")

    if "ENGINE" not in database:
        raise ConfigurationError(
            "Database configuration must include 'ENGINE'. "
            "Example: 'django.db.backends.sqlite3'"
        )

    if "NAME" not in database:
        raise ConfigurationError(
            "Database configuration must include 'NAME'. "
            "For SQLite, this is the file path."
        )


def _refresh_connections():
    """
    Refresh Django's database connections after configuration changes.
    """
    try:
        import django.db
        from django.conf import settings
        from django.db.utils import ConnectionHandler

        # Close all existing connections
        try:
            django.db.connections.close_all()
        except Exception:
            pass

        # Create new ConnectionHandler
        databases = settings.DATABASES
        new_handler = ConnectionHandler(databases)
        django.db.connections = new_handler

        # Update default connection
        try:
            django.db.connection = django.db.ConnectionProxy(new_handler, "default")
        except (AttributeError, TypeError):
            pass

        logger.debug(f"Refreshed connections for databases: {list(databases.keys())}")

    except Exception as e:
        logger.debug(f"Could not refresh connections: {e}")


def _setup_django():
    """
    Initialize Django with settings for standalone ORM usage.
    """
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
        logger.info("Django ORM configured successfully")

    except ImportError as e:
        raise ConfigurationError(
            "Django is not installed. Install with: pip install django"
        ) from e
    except Exception as e:
        raise ConfigurationError(f"Failed to configure Django: {e}") from e


def configure(
    database: Dict[str, Any],
    *,
    alias: str = "default",
    debug: bool = False,
    time_zone: str = "UTC",
    use_tz: bool = True,
    installed_apps: Optional[list] = None,
    auto_field: str = "django.db.models.BigAutoField",
    migrations_dir: Optional[str] = None,
    **extra_settings,
) -> None:
    """
    Configure the database connection and Django settings.

    This is the main configuration function for SQLORM. It sets up Django's
    settings module and initializes the ORM for standalone use.

    Args:
        database: Database configuration dictionary with keys:
            - ENGINE: Database backend (e.g., 'django.db.backends.sqlite3')
            - NAME: Database name or path (for SQLite)
            - USER: Database user (for server-based databases)
            - PASSWORD: Database password
            - HOST: Database host
            - PORT: Database port
        alias: Database alias for multiple database support (default: "default")
        debug: Enable Django debug mode (default: False)
        time_zone: Time zone string (default: "UTC")
        use_tz: Enable timezone-aware datetimes (default: True)
        installed_apps: Additional Django apps to install
        auto_field: Default auto field type for primary keys
        migrations_dir: Custom directory for migrations (default: ./migrations)
        **extra_settings: Additional Django settings

    Raises:
        ConfigurationError: If configuration fails or Django is not installed

    Example:
        >>> configure({
        ...     'ENGINE': 'django.db.backends.sqlite3',
        ...     'NAME': 'mydb.sqlite3',
        ... })
    """
    global _current_settings, _django_configured, _configured_databases

    # Validate database configuration
    _validate_database_config(database)

    # Build settings dictionary
    _current_settings = {
        **DEFAULT_SETTINGS,
        "DEBUG": debug,
        "TIME_ZONE": time_zone,
        "USE_TZ": use_tz,
        "DEFAULT_AUTO_FIELD": auto_field,
        **extra_settings,
    }

    # Set up database configuration
    _current_settings["DATABASES"] = {
        alias: database,
    }

    # Store configured databases
    _configured_databases = {alias: database}

    # Add any extra installed apps
    if installed_apps:
        _current_settings["INSTALLED_APPS"] = list(
            set(_current_settings["INSTALLED_APPS"] + installed_apps)
        )

    # Ensure sqlorm.models_app is always included
    if "sqlorm.models_app" not in _current_settings["INSTALLED_APPS"]:
        _current_settings["INSTALLED_APPS"].append("sqlorm.models_app")

    # Set up migrations directory
    if migrations_dir:
        _current_settings["MIGRATION_MODULES"] = {
            "sqlorm_models": migrations_dir,
        }

    # If already configured, reconfigure
    if _django_configured:
        logger.warning("Django was already configured. Reconfiguring...")
        from django.conf import settings

        for key, value in _current_settings.items():
            setattr(settings, key, value)
        _refresh_connections()
    else:
        _setup_django()


def configure_databases(
    databases: Dict[str, Dict[str, Any]],
    *,
    debug: bool = False,
    time_zone: str = "UTC",
    use_tz: bool = True,
    installed_apps: Optional[list] = None,
    auto_field: str = "django.db.models.BigAutoField",
    migrations_dir: Optional[str] = None,
    **extra_settings,
) -> None:
    """
    Configure multiple database connections with aliases.

    Args:
        databases: Dictionary mapping aliases to database configurations
        debug: Enable Django debug mode
        time_zone: Time zone string
        use_tz: Enable timezone-aware datetimes
        installed_apps: Additional Django apps to install
        auto_field: Default auto field type
        migrations_dir: Custom directory for migrations
        **extra_settings: Additional Django settings

    Example:
        >>> configure_databases({
        ...     'default': {
        ...         'ENGINE': 'django.db.backends.sqlite3',
        ...         'NAME': 'main.sqlite3',
        ...     },
        ...     'analytics': {
        ...         'ENGINE': 'django.db.backends.sqlite3',
        ...         'NAME': 'analytics.sqlite3',
        ...     },
        ... })
    """
    global _current_settings, _django_configured, _configured_databases

    if not databases:
        raise ConfigurationError("At least one database configuration is required")

    if "default" not in databases:
        raise ConfigurationError("A 'default' database configuration is required.")

    # Validate all database configurations
    for alias, db_config in databases.items():
        try:
            _validate_database_config(db_config)
        except ConfigurationError as e:
            raise ConfigurationError(
                f"Invalid configuration for database '{alias}': {e}"
            )

    _configured_databases = databases.copy()

    # Build settings dictionary
    _current_settings = {
        **DEFAULT_SETTINGS,
        "DEBUG": debug,
        "TIME_ZONE": time_zone,
        "USE_TZ": use_tz,
        "DEFAULT_AUTO_FIELD": auto_field,
        **extra_settings,
    }

    _current_settings["DATABASES"] = databases.copy()

    if installed_apps:
        _current_settings["INSTALLED_APPS"] = list(
            set(_current_settings["INSTALLED_APPS"] + installed_apps)
        )

    if "sqlorm.models_app" not in _current_settings["INSTALLED_APPS"]:
        _current_settings["INSTALLED_APPS"].append("sqlorm.models_app")

    if migrations_dir:
        _current_settings["MIGRATION_MODULES"] = {
            "sqlorm_models": migrations_dir,
        }

    if _django_configured:
        logger.warning("Django was already configured. Reconfiguring...")
        from django.conf import settings

        for key, value in _current_settings.items():
            setattr(settings, key, value)
        _refresh_connections()
    else:
        _setup_django()

    logger.info(
        f"Configured {len(databases)} database(s): {', '.join(databases.keys())}"
    )


def configure_from_dict(config: Dict[str, Any]) -> None:
    """
    Configure from a dictionary with full settings.

    Args:
        config: Dictionary with 'database' or 'databases' key

    Example:
        >>> configure_from_dict({
        ...     'database': {
        ...         'ENGINE': 'django.db.backends.sqlite3',
        ...         'NAME': 'mydb.sqlite3',
        ...     },
        ...     'debug': True,
        ... })
    """
    if "databases" in config:
        databases = config.pop("databases")
        configure_databases(databases, **config)
    elif "database" in config:
        database = config.pop("database")
        configure(database, **config)
    else:
        raise ConfigurationError(
            "Configuration must include 'database' or 'databases' key"
        )


def configure_from_file(file_path: Union[str, Path]) -> None:
    """
    Configure from a JSON or YAML file.

    Args:
        file_path: Path to configuration file

    Example:
        >>> configure_from_file('config.json')
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise ConfigurationError(f"Configuration file not found: {file_path}")

    suffix = file_path.suffix.lower()

    if suffix == ".json":
        with open(file_path, "r") as f:
            config = json.load(f)
    elif suffix in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError:
            raise ConfigurationError(
                "PyYAML is required for YAML configuration. "
                "Install with: pip install pyyaml"
            )
        with open(file_path, "r") as f:
            config = yaml.safe_load(f)
    else:
        raise ConfigurationError(
            f"Unsupported configuration file format: {suffix}. "
            "Use .json or .yaml/.yml"
        )

    configure_from_dict(config)


def add_database(alias: str, database: Dict[str, Any]) -> None:
    """
    Add a database configuration after initial setup.

    Args:
        alias: Unique alias for the database
        database: Database configuration dictionary

    Example:
        >>> add_database('backup', {
        ...     'ENGINE': 'django.db.backends.sqlite3',
        ...     'NAME': 'backup.sqlite3',
        ... })
    """
    global _configured_databases

    if not _django_configured:
        raise ConfigurationError(
            "SQLORM must be configured before adding databases. "
            "Call configure() first."
        )

    _validate_database_config(database)

    from django.conf import settings

    if alias in settings.DATABASES:
        raise ConfigurationError(f"Database alias '{alias}' already exists.")

    db_config = {
        "ENGINE": database.get("ENGINE", ""),
        "NAME": database.get("NAME", ""),
        "USER": database.get("USER", ""),
        "PASSWORD": database.get("PASSWORD", ""),
        "HOST": database.get("HOST", ""),
        "PORT": database.get("PORT", ""),
        "ATOMIC_REQUESTS": database.get("ATOMIC_REQUESTS", False),
        "AUTOCOMMIT": database.get("AUTOCOMMIT", True),
        "CONN_MAX_AGE": database.get("CONN_MAX_AGE", 0),
        "OPTIONS": database.get("OPTIONS", {}),
    }

    settings.DATABASES[alias] = db_config
    _configured_databases[alias] = db_config
    _refresh_connections()

    logger.info(f"Added database '{alias}'")


def get_database_aliases() -> list:
    """Get a list of all configured database aliases."""
    if not _django_configured:
        return []

    from django.conf import settings

    return list(settings.DATABASES.keys())


def get_database_config(alias: str = "default") -> Dict[str, Any]:
    """Get the configuration for a specific database alias."""
    if not _django_configured:
        raise ConfigurationError("SQLORM is not configured")

    from django.conf import settings

    if alias not in settings.DATABASES:
        raise ConfigurationError(f"Database '{alias}' is not configured")

    return dict(settings.DATABASES[alias])


def get_settings() -> Dict[str, Any]:
    """Get a copy of the current Django settings."""
    return _current_settings.copy()


def is_configured() -> bool:
    """Check if SQLORM has been configured."""
    return _django_configured


def get_migrations_dir() -> Path:
    """
    Get the migrations directory path.

    Returns the configured migrations directory or the default location
    in the current working directory.
    """
    if "MIGRATION_MODULES" in _current_settings:
        modules = _current_settings["MIGRATION_MODULES"]
        if "sqlorm_models" in modules:
            return Path(modules["sqlorm_models"])

    # Default: migrations folder in current directory
    return Path.cwd() / "migrations"
