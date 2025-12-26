"""
SQLORM - Django ORM for Standalone Scripts
===========================================

A lightweight library that lets you use Django's powerful ORM in standalone
Python scripts without requiring a full Django project structure.

Key Features:
- Use Django's mature, battle-tested ORM in any Python script
- Support for multiple database backends (SQLite, PostgreSQL, MySQL, etc.)
- Easy configuration with minimal boilerplate
- Full access to Django's model fields, querysets, and migrations
- CLI commands for migrations: `sqlorm makemigrations`, `sqlorm migrate`
- No manage.py, settings.py, or Django project structure required

Quick Start:
    >>> from sqlorm import configure, Model, fields
    >>>
    >>> # Configure the database
    >>> configure({
    ...     'ENGINE': 'django.db.backends.sqlite3',
    ...     'NAME': 'mydb.sqlite3',
    ... })
    >>>
    >>> # Define a model
    >>> class User(Model):
    ...     name = fields.CharField(max_length=100)
    ...     email = fields.EmailField(unique=True)
    ...     age = fields.IntegerField(null=True, blank=True)
    >>>
    >>> # Run migrations (from command line):
    >>> # $ sqlorm makemigrations
    >>> # $ sqlorm migrate
    >>>
    >>> # Or quick sync (development only):
    >>> from sqlorm import create_all_tables
    >>> create_all_tables()
    >>>
    >>> # Use Django ORM as usual
    >>> user = User.objects.create(name="John", email="john@example.com")
    >>> users = User.objects.filter(age__gte=18)
    >>>
    >>> # Serialize to dict/JSON
    >>> user.to_dict()
    {'id': 1, 'name': 'John', 'email': 'john@example.com'}

Author: S.S.B (surajsinghbisht054@gmail.com)
License: MIT
Repository: https://github.com/surajsinghbisht054/sqlorm
"""

from typing import TYPE_CHECKING

__version__ = "3.0.0"
__author__ = "S.S.B"
__email__ = "surajsinghbisht054@gmail.com"
__license__ = "MIT"

# Base model and utilities
from .base import (  # Schema utilities
    Model,
    add_column,
    clear_registry,
    column_exists,
    create_all_tables,
    create_table,
    get_registered_models,
    get_schema_diff,
    get_table_columns,
    migrate_all,
    rename_column,
    safe_add_column,
    sync_schema,
)

# CLI functions (for programmatic use)
from .cli import (
    inspectdb,
    makemigrations,
    migrate,
    showmigrations,
    syncdb,
)

# Core imports - Configuration
from .config import (
    add_database,
    configure,
    configure_databases,
    configure_from_dict,
    configure_from_file,
    get_database_aliases,
    get_database_config,
    get_migrations_dir,
    get_settings,
    is_configured,
)

# Connection utilities
from .connection import (
    close_all_connections,
    close_connection,
    execute_raw_sql,
    execute_raw_sql_dict,
    get_connection,
    get_database_info,
    get_table_description,
    get_table_names,
    transaction,
)

# Exceptions
from .exceptions import (
    ConfigurationError,
    ConnectionError,
    MigrationError,
    ModelError,
    QueryError,
    SQLORMError,
    ValidationError,
)

# Fields proxy
from .fields import fields

# Expose aggregation functions from Django
try:
    from django.db.models import (
        Avg,
        Case,
        Count,
        Exists,
        F,
        Max,
        Min,
        OuterRef,
        Prefetch,
        Q,
        Subquery,
        Sum,
        Value,
        When,
    )
except ImportError:
    # Django not installed yet
    pass

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    # Configuration
    "configure",
    "configure_databases",
    "configure_from_dict",
    "configure_from_file",
    "add_database",
    "get_database_aliases",
    "get_database_config",
    "get_migrations_dir",
    "get_settings",
    "is_configured",
    # Model
    "Model",
    "fields",
    "get_registered_models",
    "clear_registry",
    # Quick migrations
    "create_all_tables",
    "create_table",
    "migrate_all",
    # Schema utilities
    "add_column",
    "column_exists",
    "get_schema_diff",
    "get_table_columns",
    "rename_column",
    "safe_add_column",
    "sync_schema",
    # Connections
    "close_all_connections",
    "close_connection",
    "execute_raw_sql",
    "execute_raw_sql_dict",
    "get_connection",
    "get_database_info",
    "get_table_description",
    "get_table_names",
    "transaction",
    # CLI functions
    "makemigrations",
    "migrate",
    "showmigrations",
    "syncdb",
    "inspectdb",
    # Exceptions
    "ConfigurationError",
    "ConnectionError",
    "MigrationError",
    "ModelError",
    "QueryError",
    "SQLORMError",
    "ValidationError",
    # Django aggregations
    "Avg",
    "Count",
    "F",
    "Max",
    "Min",
    "Q",
    "Sum",
    "Value",
    "Case",
    "When",
    "Subquery",
    "OuterRef",
    "Exists",
    "Prefetch",
]
