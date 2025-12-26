"""
SQLORM - Django ORM for Standalone Scripts
===========================================

A lightweight wrapper around Django's powerful ORM that allows you to use
Django's database functionality in standalone Python scripts without
requiring a full Django project structure.

Key Features:
- Use Django's mature, battle-tested ORM in any Python script
- Support for multiple database backends (SQLite, PostgreSQL, MySQL, etc.)
- Easy configuration with minimal boilerplate
- Full access to Django's model fields, querysets, and migrations
- Compatible with existing Django knowledge

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
    >>> # Create tables
    >>> User.migrate()
    >>> 
    >>> # Use Django ORM as usual
    >>> user = User.objects.create(name="John", email="john@example.com")
    >>> users = User.objects.filter(age__gte=18)

Author: S.S.B (surajsinghbisht054@gmail.com)
License: MIT
Repository: https://github.com/surajsinghbisht054/sqlorm
"""

__version__ = "2.0.0"
__author__ = "S.S.B"
__email__ = "surajsinghbisht054@gmail.com"
__license__ = "MIT"

# Core imports
from .config import (
    configure,
    configure_databases,
    configure_from_dict,
    configure_from_file,
    add_database,
    get_database_aliases,
    get_database_config,
    get_settings,
)
from .base import (
    Model,
    get_registered_models,
    create_all_tables,
    migrate_all,
    # Migration utilities
    get_table_columns,
    column_exists,
    add_column,
    safe_add_column,
    rename_column,
    change_column_type,
    recreate_table,
    backup_table,
    restore_table,
    get_schema_diff,
    sync_schema,
)
from .fields import fields
from .connection import get_connection, close_connection, execute_raw_sql, transaction
from .exceptions import (
    SQLORMError,
    ConfigurationError,
    ModelError,
    MigrationError,
    ConnectionError,
)

# Convenience re-exports from Django
try:
    from django.db.models import Q, F, Count, Sum, Avg, Max, Min, Prefetch
    from django.db.models import Value, Case, When, OuterRef, Subquery
except ImportError:
    pass  # Django not installed yet

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
    "get_settings",
    # Models
    "Model",
    "get_registered_models",
    "create_all_tables",
    "migrate_all",
    # Fields
    "fields",
    # Connection
    "get_connection",
    "close_connection",
    "execute_raw_sql",
    # Migration utilities
    "get_table_columns",
    "column_exists",
    "add_column",
    "safe_add_column",
    "rename_column",
    "change_column_type",
    "recreate_table",
    "backup_table",
    "restore_table",
    "get_schema_diff",
    "sync_schema",
    # Exceptions
    "SQLORMError",
    "ConfigurationError",
    "ModelError",
    "MigrationError",
    "ConnectionError",
    # Django re-exports
    "Q",
    "F",
    "Count",
    "Sum",
    "Avg",
    "Max",
    "Min",
    "Prefetch",
    "Value",
    "Case",
    "When",
    "OuterRef",
    "Subquery",
    "transaction",
]
