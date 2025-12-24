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
    ...     'logs': {
    ...         'ENGINE': 'django.db.backends.postgresql',
    ...         'NAME': 'logs_db',
    ...         'USER': 'admin',
    ...         'PASSWORD': 'secret',
    ...         'HOST': 'localhost',
    ...         'PORT': '5432',
    ...     },
    ... })
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union

from .exceptions import ConfigurationError

# Logger for this module
logger = logging.getLogger("sqlorm.config")

# Global state to track if Django has been configured
_django_configured = False
_current_settings = {}
_configured_databases = {}

# Default Django settings that are required for standalone usage
DEFAULT_SETTINGS = {
    "DEBUG": True,
    "INSTALLED_APPS": [
        "django.contrib.contenttypes",
    ],
    "DATABASES": {},
    "DEFAULT_AUTO_FIELD": "django.db.models.BigAutoField",
    "USE_TZ": True,
    "TIME_ZONE": "UTC",
}


def _refresh_connections():
    """
    Refresh Django's database connections after configuration changes.
    
    This is needed when reconfiguring databases to ensure the connection
    handler picks up the new database configurations.
    
    Note: Django isn't designed for runtime reconfiguration. This function
    attempts to update all cached references to the connections object,
    but some edge cases may not work correctly.
    """
    try:
        import sys
        import django.db
        from django.conf import settings
        from django.db.utils import ConnectionHandler
        
        # Close all existing connections first
        try:
            django.db.connections.close_all()
        except Exception:
            pass
        
        # Get the new database settings
        databases = settings.DATABASES
        
        # Create a completely new ConnectionHandler with the updated settings
        new_handler = ConnectionHandler(databases)
        
        # Replace the connections in django.db module
        django.db.connections = new_handler
        
        # Update the default connection proxy
        try:
            # Django 4.x uses ConnectionProxy
            django.db.connection = django.db.ConnectionProxy(new_handler, 'default')
        except (AttributeError, TypeError):
            try:
                # Older Django versions
                django.db.connection = django.db.DefaultConnectionProxy()
            except AttributeError:
                pass
        
        # CRITICAL: Update all modules that have imported 'connections'
        # These modules cache the reference at import time
        modules_to_update = [
            'django.db.models.query',
            'django.db.models.base',
            'django.db.models.sql.compiler',
            'django.db.models.sql.subqueries',
            'django.db.transaction',
            'django.db.models.deletion',
            'django.db.models.sql.query',
            'django.db.backends.base.base',
            'django.db.models.manager',
        ]
        
        for module_name in modules_to_update:
            if module_name in sys.modules:
                module = sys.modules[module_name]
                if hasattr(module, 'connections'):
                    module.connections = new_handler
        
        logger.debug(f"Refreshed connections for databases: {list(databases.keys())}")
        
    except Exception as e:
        logger.debug(f"Could not refresh connections: {e}")


def _setup_django():
    """
    Initialize Django with minimal settings for standalone ORM usage.
    
    This function configures Django to work outside of a full Django project,
    enabling you to use the ORM in standalone scripts.
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
            "Django is not installed. Please install it with: pip install django"
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
    **extra_settings
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
        **extra_settings: Additional Django settings
    
    Raises:
        ConfigurationError: If configuration fails or Django is not installed
    
    Example:
        >>> configure({
        ...     'ENGINE': 'django.db.backends.sqlite3',
        ...     'NAME': 'mydb.sqlite3',
        ... })
        
        >>> # With additional options
        >>> configure(
        ...     database={
        ...         'ENGINE': 'django.db.backends.postgresql',
        ...         'NAME': 'mydb',
        ...         'USER': 'user',
        ...         'PASSWORD': 'pass',
        ...         'HOST': 'localhost',
        ...         'PORT': '5432',
        ...     },
        ...     debug=True,
        ...     time_zone='America/New_York',
        ... )
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
    
    # If already configured, we need to reconfigure
    if _django_configured:
        logger.warning("Django was already configured. Reconfiguring...")
        # Update Django settings
        from django.conf import settings
        for key, value in _current_settings.items():
            setattr(settings, key, value)
        # Refresh database connections
        _refresh_connections()
    else:
        # Initialize Django
        _setup_django()


def configure_databases(
    databases: Dict[str, Dict[str, Any]],
    *,
    debug: bool = False,
    time_zone: str = "UTC",
    use_tz: bool = True,
    installed_apps: Optional[list] = None,
    auto_field: str = "django.db.models.BigAutoField",
    **extra_settings
) -> None:
    """
    Configure multiple database connections with aliases (Django-like approach).
    
    This is the recommended way to set up multiple databases. Each database
    is identified by an alias, with 'default' being the primary database.
    
    Models can then specify which database to use via the `_using` class
    attribute or by passing `using='alias'` to queryset methods.
    
    Args:
        databases: Dictionary mapping aliases to database configurations.
            Each configuration should have:
            - ENGINE: Database backend (e.g., 'django.db.backends.sqlite3')
            - NAME: Database name or path
            - USER: Database user (for server-based databases)
            - PASSWORD: Database password
            - HOST: Database host
            - PORT: Database port
        debug: Enable Django debug mode (default: False)
        time_zone: Time zone string (default: "UTC")
        use_tz: Enable timezone-aware datetimes (default: True)
        installed_apps: Additional Django apps to install
        auto_field: Default auto field type for primary keys
        **extra_settings: Additional Django settings
    
    Raises:
        ConfigurationError: If configuration fails or 'default' is missing
    
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
        ...     'logs': {
        ...         'ENGINE': 'django.db.backends.postgresql',
        ...         'NAME': 'logs_db',
        ...         'USER': 'admin',
        ...         'PASSWORD': 'secret',
        ...         'HOST': 'localhost',
        ...         'PORT': '5432',
        ...     },
        ... })
        
        >>> # Define models that use specific databases
        >>> class User(Model):
        ...     name = fields.CharField(max_length=100)
        ...     # Uses 'default' database by default
        
        >>> class AnalyticsEvent(Model):
        ...     _using = 'analytics'  # Use analytics database
        ...     event_name = fields.CharField(max_length=100)
        
        >>> class LogEntry(Model):
        ...     _using = 'logs'  # Use logs database
        ...     message = fields.TextField()
    """
    global _current_settings, _django_configured, _configured_databases
    
    if not databases:
        raise ConfigurationError("At least one database configuration is required")
    
    if 'default' not in databases:
        raise ConfigurationError(
            "A 'default' database configuration is required. "
            "Other databases can be added with different aliases."
        )
    
    # Validate all database configurations
    for alias, db_config in databases.items():
        try:
            _validate_database_config(db_config)
        except ConfigurationError as e:
            raise ConfigurationError(f"Invalid configuration for database '{alias}': {e}")
    
    # Store configured databases
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
    
    # Set up all database configurations
    _current_settings["DATABASES"] = databases.copy()
    
    # Add any extra installed apps
    if installed_apps:
        _current_settings["INSTALLED_APPS"] = list(
            set(_current_settings["INSTALLED_APPS"] + installed_apps)
        )
    
    # If already configured, we need to reconfigure
    if _django_configured:
        logger.warning("Django was already configured. Reconfiguring...")
        # Update Django settings
        from django.conf import settings
        for key, value in _current_settings.items():
            setattr(settings, key, value)
        # Refresh database connections
        _refresh_connections()
    else:
        # Initialize Django
        _setup_django()
    
    logger.info(f"Configured {len(databases)} database(s): {', '.join(databases.keys())}")


def add_database(alias: str, database: Dict[str, Any]) -> None:
    """
    Add an additional database configuration to an already configured system.
    
    This allows you to dynamically add databases after initial configuration.
    
    Args:
        alias: Unique alias for the database
        database: Database configuration dictionary
    
    Raises:
        ConfigurationError: If SQLORM hasn't been configured or alias already exists
    
    Example:
        >>> configure({'ENGINE': '...', 'NAME': 'main.db'})
        >>> 
        >>> # Later, add another database
        >>> add_database('backup', {
        ...     'ENGINE': 'django.db.backends.sqlite3',
        ...     'NAME': 'backup.sqlite3',
        ... })
    """
    global _configured_databases
    
    if not _django_configured:
        raise ConfigurationError(
            "SQLORM must be configured before adding databases. "
            "Call configure() or configure_databases() first."
        )
    
    _validate_database_config(database)
    
    from django.conf import settings
    
    if alias in settings.DATABASES:
        raise ConfigurationError(
            f"Database alias '{alias}' already exists. "
            "Use a different alias or reconfigure with configure_databases()."
        )
    
    # Ensure all required keys are present (Django requirement)
    db_config = {
        'ENGINE': database.get('ENGINE', ''),
        'NAME': database.get('NAME', ''),
        'USER': database.get('USER', ''),
        'PASSWORD': database.get('PASSWORD', ''),
        'HOST': database.get('HOST', ''),
        'PORT': database.get('PORT', ''),
        'ATOMIC_REQUESTS': database.get('ATOMIC_REQUESTS', False),
        'AUTOCOMMIT': database.get('AUTOCOMMIT', True),
        'CONN_MAX_AGE': database.get('CONN_MAX_AGE', 0),
        'CONN_HEALTH_CHECKS': database.get('CONN_HEALTH_CHECKS', False),
        'OPTIONS': database.get('OPTIONS', {}),
        'TIME_ZONE': database.get('TIME_ZONE', None),
        'TEST': database.get('TEST', {}),
    }
    
    # Add to Django settings
    settings.DATABASES[alias] = db_config
    _configured_databases[alias] = db_config
    
    logger.info(f"Added database '{alias}'")


def get_database_aliases() -> list:
    """
    Get a list of all configured database aliases.
    
    Returns:
        List of database alias strings
    
    Example:
        >>> configure_databases({
        ...     'default': {...},
        ...     'analytics': {...},
        ... })
        >>> get_database_aliases()
        ['default', 'analytics']
    """
    if not _django_configured:
        return []
    
    from django.conf import settings
    return list(settings.DATABASES.keys())


def get_database_config(alias: str = 'default') -> Dict[str, Any]:
    """
    Get the configuration for a specific database alias.
    
    Args:
        alias: Database alias (default: 'default')
    
    Returns:
        Database configuration dictionary
    
    Raises:
        ConfigurationError: If alias doesn't exist
    
    Example:
        >>> config = get_database_config('analytics')
        >>> print(config['ENGINE'])
    """
    if not _django_configured:
        raise ConfigurationError("SQLORM is not configured")
    
    from django.conf import settings
    
    if alias not in settings.DATABASES:
        raise ConfigurationError(
            f"Database alias '{alias}' not found. "
            f"Available: {', '.join(settings.DATABASES.keys())}"
        )
    
    return dict(settings.DATABASES[alias])


def configure_from_dict(config: Dict[str, Any]) -> None:
    """
    Configure SQLORM from a dictionary containing all settings.
    
    This is useful when loading configuration from a config file or
    environment variables that have already been parsed.
    
    Args:
        config: Dictionary containing:
            - database: Database configuration (required)
            - debug: Debug mode (optional)
            - time_zone: Time zone (optional)
            - use_tz: Use timezone-aware datetimes (optional)
            - installed_apps: Additional apps (optional)
            - Any other Django settings
    
    Example:
        >>> config = {
        ...     'database': {
        ...         'ENGINE': 'django.db.backends.sqlite3',
        ...         'NAME': 'mydb.sqlite3',
        ...     },
        ...     'debug': True,
        ... }
        >>> configure_from_dict(config)
    """
    if "database" not in config:
        raise ConfigurationError("Configuration must include 'database' key")
    
    database = config.pop("database")
    configure(database, **config)


def configure_from_file(
    filepath: Union[str, Path],
    format: Optional[str] = None
) -> None:
    """
    Configure SQLORM from a JSON or YAML configuration file.
    
    Args:
        filepath: Path to the configuration file
        format: File format ('json' or 'yaml'). Auto-detected if None.
    
    Raises:
        ConfigurationError: If file doesn't exist or is invalid
        FileNotFoundError: If file doesn't exist
    
    Example:
        >>> # config.json
        >>> # {
        >>> #     "database": {
        >>> #         "ENGINE": "django.db.backends.sqlite3",
        >>> #         "NAME": "mydb.sqlite3"
        >>> #     }
        >>> # }
        >>> configure_from_file('config.json')
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(f"Configuration file not found: {filepath}")
    
    # Auto-detect format from extension
    if format is None:
        suffix = filepath.suffix.lower()
        if suffix in ('.json',):
            format = 'json'
        elif suffix in ('.yaml', '.yml'):
            format = 'yaml'
        else:
            raise ConfigurationError(
                f"Unknown config file format: {suffix}. "
                "Supported formats: .json, .yaml, .yml"
            )
    
    try:
        with open(filepath, 'r') as f:
            if format == 'json':
                config = json.load(f)
            elif format == 'yaml':
                try:
                    import yaml
                    config = yaml.safe_load(f)
                except ImportError:
                    raise ConfigurationError(
                        "PyYAML is required for YAML config files. "
                        "Install it with: pip install pyyaml"
                    )
            else:
                raise ConfigurationError(f"Unsupported format: {format}")
    except json.JSONDecodeError as e:
        raise ConfigurationError(f"Invalid JSON in config file: {e}")
    except Exception as e:
        raise ConfigurationError(f"Failed to load config file: {e}")
    
    configure_from_dict(config)


def configure_from_env(
    prefix: str = "SQLORM_",
    database_url_key: str = "DATABASE_URL"
) -> None:
    """
    Configure SQLORM from environment variables.
    
    This supports two methods:
    1. Using a DATABASE_URL style connection string
    2. Using individual environment variables with a prefix
    
    Environment variables (with default prefix SQLORM_):
        - SQLORM_DB_ENGINE: Database backend
        - SQLORM_DB_NAME: Database name
        - SQLORM_DB_USER: Database user
        - SQLORM_DB_PASSWORD: Database password
        - SQLORM_DB_HOST: Database host
        - SQLORM_DB_PORT: Database port
        - SQLORM_DEBUG: Debug mode (true/false)
        - SQLORM_TIME_ZONE: Time zone
    
    Or using DATABASE_URL:
        - DATABASE_URL: postgres://user:pass@host:port/dbname
    
    Args:
        prefix: Prefix for environment variables (default: "SQLORM_")
        database_url_key: Key for DATABASE_URL style config
    
    Example:
        >>> import os
        >>> os.environ['SQLORM_DB_ENGINE'] = 'django.db.backends.sqlite3'
        >>> os.environ['SQLORM_DB_NAME'] = 'mydb.sqlite3'
        >>> configure_from_env()
    """
    # Try DATABASE_URL first
    database_url = os.environ.get(database_url_key)
    if database_url:
        database = _parse_database_url(database_url)
    else:
        # Build from individual environment variables
        database = {}
        
        engine = os.environ.get(f"{prefix}DB_ENGINE")
        if engine:
            database["ENGINE"] = engine
        
        name = os.environ.get(f"{prefix}DB_NAME")
        if name:
            database["NAME"] = name
        
        user = os.environ.get(f"{prefix}DB_USER")
        if user:
            database["USER"] = user
        
        password = os.environ.get(f"{prefix}DB_PASSWORD")
        if password:
            database["PASSWORD"] = password
        
        host = os.environ.get(f"{prefix}DB_HOST")
        if host:
            database["HOST"] = host
        
        port = os.environ.get(f"{prefix}DB_PORT")
        if port:
            database["PORT"] = port
    
    if not database:
        raise ConfigurationError(
            "No database configuration found in environment variables. "
            f"Set {database_url_key} or {prefix}DB_* variables."
        )
    
    # Get other settings from environment
    debug = os.environ.get(f"{prefix}DEBUG", "false").lower() == "true"
    time_zone = os.environ.get(f"{prefix}TIME_ZONE", "UTC")
    
    configure(database, debug=debug, time_zone=time_zone)


def _parse_database_url(url: str) -> Dict[str, str]:
    """
    Parse a DATABASE_URL style connection string.
    
    Supports formats:
        - postgres://user:pass@host:port/dbname
        - postgresql://user:pass@host:port/dbname
        - mysql://user:pass@host:port/dbname
        - sqlite:///path/to/db.sqlite3
    
    Args:
        url: Database URL string
    
    Returns:
        Database configuration dictionary
    """
    from urllib.parse import urlparse, unquote
    
    parsed = urlparse(url)
    
    # Map URL schemes to Django backends
    scheme_to_engine = {
        "postgres": "django.db.backends.postgresql",
        "postgresql": "django.db.backends.postgresql",
        "mysql": "django.db.backends.mysql",
        "sqlite": "django.db.backends.sqlite3",
        "sqlite3": "django.db.backends.sqlite3",
        "oracle": "django.db.backends.oracle",
    }
    
    scheme = parsed.scheme.lower()
    if scheme not in scheme_to_engine:
        raise ConfigurationError(
            f"Unknown database scheme: {scheme}. "
            f"Supported: {', '.join(scheme_to_engine.keys())}"
        )
    
    database = {
        "ENGINE": scheme_to_engine[scheme],
    }
    
    # SQLite handling
    if scheme in ("sqlite", "sqlite3"):
        # sqlite:///path/to/db or sqlite:///:memory:
        database["NAME"] = parsed.path.lstrip("/") or ":memory:"
        return database
    
    # Server-based databases
    database["NAME"] = parsed.path.lstrip("/")
    
    if parsed.username:
        database["USER"] = unquote(parsed.username)
    
    if parsed.password:
        database["PASSWORD"] = unquote(parsed.password)
    
    if parsed.hostname:
        database["HOST"] = parsed.hostname
    
    if parsed.port:
        database["PORT"] = str(parsed.port)
    
    return database


def _validate_database_config(config: Dict[str, Any]) -> None:
    """
    Validate a database configuration dictionary.
    
    Args:
        config: Database configuration to validate
    
    Raises:
        ConfigurationError: If configuration is invalid
    """
    if not isinstance(config, dict):
        raise ConfigurationError("Database configuration must be a dictionary")
    
    if "ENGINE" not in config:
        raise ConfigurationError("Database configuration must include 'ENGINE'")
    
    if "NAME" not in config:
        raise ConfigurationError("Database configuration must include 'NAME'")
    
    valid_engines = [
        "django.db.backends.sqlite3",
        "django.db.backends.postgresql",
        "django.db.backends.mysql",
        "django.db.backends.oracle",
    ]
    
    engine = config.get("ENGINE", "")
    if not any(engine.startswith(ve.rsplit('.', 1)[0]) for ve in valid_engines):
        logger.warning(
            f"Non-standard database engine: {engine}. "
            "This may be a third-party backend, which is fine."
        )


def get_settings() -> Dict[str, Any]:
    """
    Get the current Django settings as a dictionary.
    
    Returns:
        Dictionary of current settings
    
    Example:
        >>> settings = get_settings()
        >>> print(settings['DEBUG'])
        False
    """
    return _current_settings.copy()


def is_configured() -> bool:
    """
    Check if Django has been configured.
    
    Returns:
        True if configured, False otherwise
    """
    return _django_configured


def reset():
    """
    Reset the configuration state.
    
    Warning: This is primarily for testing purposes.
    Resetting after models have been registered may cause issues.
    """
    global _django_configured, _current_settings
    _django_configured = False
    _current_settings = {}
    logger.warning("Configuration reset. This may cause issues with registered models.")
