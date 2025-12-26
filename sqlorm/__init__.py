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
- Serialization support (to_dict, to_json)
- Type hints for better IDE support

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
    >>>
    >>> # Serialize to dict/JSON
    >>> user.to_dict()
    {'id': 1, 'name': 'John', 'email': 'john@example.com'}
    >>> user.to_json()
    '{"id": 1, "name": "John", "email": "john@example.com"}'

Author: S.S.B (surajsinghbisht054@gmail.com)
License: MIT
Repository: https://github.com/surajsinghbisht054/sqlorm
"""

from typing import TYPE_CHECKING

__version__ = "2.1.0"
__author__ = "S.S.B"
__email__ = "surajsinghbisht054@gmail.com"
__license__ = "MIT"

from .base import (  # Migration utilities
    Model,
    add_column,
    backup_table,
    change_column_type,
    clear_registry,
    column_exists,
    create_all_tables,
    get_registered_models,
    get_schema_diff,
    get_table_columns,
    migrate_all,
    recreate_table,
    rename_column,
    restore_table,
    safe_add_column,
    sync_schema,
)

# Core imports
from .config import (
    add_database,
    configure,
    configure_databases,
    configure_from_dict,
    configure_from_file,
    get_database_aliases,
    get_database_config,
    get_settings,
    is_configured,
)
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
from .exceptions import (
    ConfigurationError,
    ConnectionError,
    MigrationError,
    ModelError,
    QueryError,
    SQLORMError,
    ValidationError,
)
from .fields import fields

# Convenience re-exports from Django
try:
    from django.db.models import (
        Avg,
        Case,
        Count,
        Exists,
        ExpressionWrapper,
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
    from django.db.models.functions import (
        Cast,
        Coalesce,
        Concat,
        Greatest,
        Least,
        Length,
        Lower,
        Now,
        Trim,
        TruncDate,
        TruncMonth,
        TruncYear,
        Upper,
    )
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
    "is_configured",
    # Models
    "Model",
    "get_registered_models",
    "create_all_tables",
    "migrate_all",
    "clear_registry",
    # Fields
    "fields",
    # Connection
    "get_connection",
    "close_connection",
    "close_all_connections",
    "execute_raw_sql",
    "execute_raw_sql_dict",
    "transaction",
    "get_database_info",
    "get_table_names",
    "get_table_description",
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
    "ValidationError",
    "QueryError",
    # Django re-exports - Query building
    "Q",
    "F",
    "Value",
    "Case",
    "When",
    "OuterRef",
    "Subquery",
    "Exists",
    "ExpressionWrapper",
    # Django re-exports - Aggregations
    "Count",
    "Sum",
    "Avg",
    "Max",
    "Min",
    "Prefetch",
    # Django re-exports - Functions
    "Coalesce",
    "Concat",
    "Length",
    "Lower",
    "Upper",
    "Trim",
    "Now",
    "TruncDate",
    "TruncMonth",
    "TruncYear",
    "Cast",
    "Greatest",
    "Least",
]
