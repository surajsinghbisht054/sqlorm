"""
SQLORM Base Model Module
========================

This module provides the base Model class that uses Django's ORM directly
with monkey-patching to inject models into the sqlorm.models_app module.

The new approach:
- Models inherit directly from Django's models.Model
- Models are automatically registered in sqlorm.models_app
- No wrapper classes - direct Django model usage
- Migrations handled via sqlorm CLI commands

Example:
    >>> from sqlorm import configure, Model, fields
    >>>
    >>> configure({'ENGINE': 'django.db.backends.sqlite3', 'NAME': 'db.sqlite3'})
    >>>
    >>> class Article(Model):
    ...     title = fields.CharField(max_length=200)
    ...     content = fields.TextField()
    ...     published = fields.BooleanField(default=False)
    >>>
    >>> # Run migrations: sqlorm makemigrations && sqlorm migrate
    >>>
    >>> article = Article.objects.create(
    ...     title="Hello World",
    ...     content="This is my first article"
    ... )
"""

import logging
import sys
from typing import Any, Dict, List, Optional, Type

from .exceptions import MigrationError, ModelError

# Logger for this module
logger = logging.getLogger("sqlorm.base")

# Registry to keep track of all defined models
_model_registry: Dict[str, Type["Model"]] = {}

# Track if we've initialized Django
_django_initialized = False


def _ensure_django_setup():
    """Ensure Django is configured before model creation."""
    global _django_initialized

    if _django_initialized:
        return True

    try:
        import django
        from django.conf import settings

        if settings.configured:
            if not django.apps.apps.ready:
                django.setup()
            _django_initialized = True
            return True
        return False
    except Exception:
        return False


def _get_django_models_module():
    """Get Django's models module."""
    from django.db import models as django_models

    return django_models


def _register_model_in_app(model_class, model_name):
    """
    Register a model in the sqlorm.models_app module.

    This makes the model appear as if it was defined in sqlorm.models_app.models,
    which is required for Django's migration system to work properly.
    """
    try:
        from sqlorm.models_app import models as models_module

        # Add to the models module
        models_module.register_model(model_name, model_class)

        # Also set it on the module directly for Django's app loading
        setattr(models_module, model_name, model_class)

        logger.debug(f"Registered model {model_name} in sqlorm.models_app")

    except Exception as e:
        logger.debug(f"Could not register model in app: {e}")


class ModelMeta(type):
    """
    Metaclass for Model that handles:
    - Model creation using Django's model system
    - Model registration in sqlorm.models_app
    - App label assignment
    """

    def __new__(mcs, name: str, bases: tuple, namespace: dict):
        # Don't process the base Model class itself
        if name == "Model" and not any(hasattr(b, "_is_sqlorm_model") for b in bases):
            cls = super().__new__(mcs, name, bases, namespace)
            cls._is_sqlorm_model = True
            return cls

        # Check if this is an abstract model
        meta = namespace.get("Meta")
        is_abstract = False
        if meta:
            is_abstract = getattr(meta, "abstract", False)

        if namespace.get("_abstract", False):
            is_abstract = True

        # If Django isn't set up yet, defer model creation
        if not _ensure_django_setup():
            # Store the class definition for later
            cls = super().__new__(mcs, name, bases, namespace)
            cls._deferred = True
            cls._namespace = namespace
            _model_registry[name] = cls
            logger.debug(f"Deferred model creation for {name}")
            return cls

        # Get Django's models module
        django_models = _get_django_models_module()

        # Gather field definitions from the namespace
        fields = {}
        other_attrs = {}

        for attr_name, attr_value in namespace.items():
            if attr_name.startswith("_"):
                other_attrs[attr_name] = attr_value
            elif isinstance(attr_value, django_models.Field):
                fields[attr_name] = attr_value
            elif attr_name == "Meta":
                other_attrs[attr_name] = attr_value
            elif callable(attr_value) or isinstance(
                attr_value, (classmethod, staticmethod, property)
            ):
                other_attrs[attr_name] = attr_value
            else:
                other_attrs[attr_name] = attr_value

        # Build Meta class with app_label
        meta_attrs = {
            "app_label": "sqlorm_models",
        }

        # Get db_table from class if specified
        if "_db_table" in namespace:
            meta_attrs["db_table"] = namespace["_db_table"]

        # Copy user's Meta attributes
        if "Meta" in namespace:
            user_meta = namespace["Meta"]
            for attr in dir(user_meta):
                if not attr.startswith("_"):
                    meta_attrs[attr] = getattr(user_meta, attr)

        # Override abstract if needed
        if is_abstract:
            meta_attrs["abstract"] = True

        NewMeta = type("Meta", (), meta_attrs)

        # Build the model attributes
        model_attrs = {
            "__module__": "sqlorm.models_app.models",  # Critical: set module for migrations
            "Meta": NewMeta,
            **fields,
        }

        # Add methods from the original class
        for attr_name, attr_value in other_attrs.items():
            if attr_name not in ("Meta", "_abstract", "_db_table", "_using"):
                if callable(attr_value) and not isinstance(attr_value, type):
                    model_attrs[attr_name] = attr_value

        # Create the Django model class
        django_model = type(name, (django_models.Model,), model_attrs)

        # Store the database alias preference
        if "_using" in namespace:
            django_model._default_using = namespace["_using"]

        # Register with Django's app registry
        if not is_abstract:
            try:
                from django.apps import apps

                if "sqlorm_models" not in apps.all_models:
                    apps.all_models["sqlorm_models"] = {}

                apps.all_models["sqlorm_models"][name.lower()] = django_model

                # Register in our models_app module
                _register_model_in_app(django_model, name)

            except Exception as e:
                logger.debug(f"Could not register model with app registry: {e}")

        # Add to our registry
        if not is_abstract:
            _model_registry[name] = django_model

        logger.debug(f"Created Django model: {name}")

        # Add convenience methods to the model
        mcs._add_convenience_methods(django_model)

        return django_model

    @staticmethod
    def _add_convenience_methods(model_class):
        """Add SQLORM convenience methods to the Django model."""

        def to_dict(
            self,
            fields: Optional[List[str]] = None,
            exclude: Optional[List[str]] = None,
            include_pk: bool = True,
        ) -> Dict[str, Any]:
            """Convert the model instance to a dictionary."""
            exclude = exclude or []
            result = {}

            model_fields = self._meta.get_fields()
            for field in model_fields:
                if not hasattr(field, "attname"):
                    continue

                name = field.name

                if fields is not None and name not in fields:
                    if not (include_pk and field.primary_key):
                        continue
                if name in exclude:
                    continue
                if not include_pk and field.primary_key:
                    continue

                value = getattr(self, name, None)

                # Handle special types for JSON serialization
                if hasattr(value, "isoformat"):
                    # datetime, date, time
                    value = value.isoformat()
                elif hasattr(value, "hex") and hasattr(value, "int"):
                    # UUID
                    value = str(value)
                elif value.__class__.__name__ == "Decimal":
                    # Decimal
                    value = float(value)
                # Leave int, bool, str, None, float as-is

                result[name] = value

            return result

        def to_json(
            self,
            fields: Optional[List[str]] = None,
            exclude: Optional[List[str]] = None,
            include_pk: bool = True,
            indent: Optional[int] = None,
        ) -> str:
            """Convert the model instance to a JSON string."""
            import json

            data = self.to_dict(fields=fields, exclude=exclude, include_pk=include_pk)
            return json.dumps(data, indent=indent, default=str)

        def update(self, **kwargs):
            """Update fields and save in one operation."""
            for key, value in kwargs.items():
                setattr(self, key, value)
            self.save(update_fields=list(kwargs.keys()))
            return self

        # Add methods to the model class
        model_class.to_dict = to_dict
        model_class.to_json = to_json
        model_class.update = update

        # Add class methods
        @classmethod
        def get_table_name(cls) -> str:
            """Get the database table name for this model."""
            return cls._meta.db_table

        @classmethod
        def get_fields(cls) -> List[str]:
            """Get a list of field names for this model."""
            return [f.name for f in cls._meta.get_fields()]

        @classmethod
        def get_database_alias(cls) -> str:
            """Get the database alias this model uses."""
            return getattr(cls, "_default_using", None) or "default"

        @classmethod
        def table_exists(cls, using: Optional[str] = None) -> bool:
            """Check if the database table for this model exists."""
            db_alias = using or getattr(cls, "_default_using", None) or "default"
            try:
                from django.db import connections

                connection = connections[db_alias]
                table_name = cls._meta.db_table
                return table_name in connection.introspection.table_names()
            except Exception:
                return False

        model_class.get_table_name = get_table_name
        model_class.get_fields = get_fields
        model_class.get_database_alias = get_database_alias
        model_class.table_exists = table_exists


class Model(metaclass=ModelMeta):
    """
    Base class for all SQLORM models.

    Inherit from this class to define your database models. The syntax
    is identical to Django's model definition.

    Models are automatically registered in sqlorm.models_app and can
    be migrated using the sqlorm CLI:

        $ sqlorm makemigrations
        $ sqlorm migrate

    Class Attributes:
        _abstract: Set to True to make this an abstract base class
        _db_table: Custom database table name
        _using: Database alias for multi-database support

    Example:
        >>> from sqlorm import Model, fields, configure
        >>>
        >>> configure({
        ...     'ENGINE': 'django.db.backends.sqlite3',
        ...     'NAME': 'mydb.sqlite3'
        ... })
        >>>
        >>> class User(Model):
        ...     name = fields.CharField(max_length=100)
        ...     email = fields.EmailField(unique=True)
        ...     is_active = fields.BooleanField(default=True)
        ...
        ...     class Meta:
        ...         ordering = ['-id']
        >>>
        >>> # Run: sqlorm makemigrations && sqlorm migrate
        >>>
        >>> # Create a user
        >>> user = User.objects.create(name="John", email="john@example.com")
        >>>
        >>> # Query users
        >>> active_users = User.objects.filter(is_active=True)
    """

    _is_sqlorm_model = True
    _abstract = False
    _db_table: Optional[str] = None
    _using: Optional[str] = None


def get_registered_models() -> Dict[str, Type]:
    """
    Get all registered models.

    Returns:
        Dictionary mapping model names to model classes
    """
    return _model_registry.copy()


def clear_registry():
    """
    Clear the model registry.

    Warning: This is primarily for testing purposes.
    """
    global _model_registry

    # Also clear from the models_app
    try:
        from sqlorm.models_app import models as models_module

        models_module.clear_registry()
    except Exception:
        pass

    _model_registry = {}
    logger.warning("Model registry cleared")


def create_all_tables(verbosity: int = 1, using: str = "default") -> List[str]:
    """
    Create database tables for all registered models (quick sync mode).

    This is a convenience function that directly creates tables without
    using Django's migration system. For proper migrations, use:
        $ sqlorm makemigrations
        $ sqlorm migrate

    Args:
        verbosity: Output verbosity level
        using: Database alias

    Returns:
        List of created table names
    """
    from django.db import connections

    created = []
    connection = connections[using]

    for name, model in _model_registry.items():
        try:
            # Check if model specifies a different database
            model_db = getattr(model, "_default_using", None) or using
            model_connection = connections[model_db]

            table_name = model._meta.db_table
            existing_tables = model_connection.introspection.table_names()

            if table_name not in existing_tables:
                with model_connection.schema_editor() as schema_editor:
                    schema_editor.create_model(model)
                created.append(table_name)
                if verbosity > 0:
                    logger.info(f"Created table: {table_name} in '{model_db}'")
        except Exception as e:
            logger.error(f"Failed to create table for {name}: {e}")

    return created


def create_table(model_class, using: Optional[str] = None, verbosity: int = 1) -> bool:
    """
    Create a table for a single model.

    Args:
        model_class: The model class to create a table for
        using: Database alias (overrides model's _default_using)
        verbosity: Output verbosity level

    Returns:
        True if table was created, False if it already exists
    """
    from django.db import connections

    db_alias = using or getattr(model_class, "_default_using", None) or "default"
    connection = connections[db_alias]

    table_name = model_class._meta.db_table
    existing_tables = connection.introspection.table_names()

    if table_name in existing_tables:
        if verbosity > 0:
            logger.info(f"Table {table_name} already exists in '{db_alias}'")
        return False

    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(model_class)

    if verbosity > 0:
        logger.info(f"Created table: {table_name} in '{db_alias}'")

    return True


def migrate_all(verbosity: int = 1, using: str = "default") -> None:
    """
    Quick migrate all registered models (creates tables directly).

    For proper migrations with history, use:
        $ sqlorm makemigrations
        $ sqlorm migrate

    Args:
        verbosity: Output verbosity level
        using: Database alias
    """
    create_all_tables(verbosity=verbosity, using=using)


# =============================================================================
# Schema Utilities
# =============================================================================


def get_table_columns(table_name: str, using: str = "default") -> List[str]:
    """Get the list of column names for a table."""
    try:
        from django.db import connections

        connection = connections[using]
        with connection.cursor() as cursor:
            return [
                col.name
                for col in connection.introspection.get_table_description(
                    cursor, table_name
                )
            ]
    except Exception as e:
        logger.error(f"Failed to get columns for {table_name}: {e}")
        return []


def column_exists(table_name: str, column_name: str, using: str = "default") -> bool:
    """Check if a column exists in a table."""
    columns = get_table_columns(table_name, using)
    return column_name.lower() in [c.lower() for c in columns]


def add_column(
    table_name: str,
    column_name: str,
    column_type: str,
    default: Optional[str] = None,
    nullable: bool = True,
    using: str = "default",
) -> bool:
    """Add a new column to an existing table."""
    try:
        from django.db import connections

        connection = connections[using]
        cursor = connection.cursor()

        null_clause = "" if nullable else " NOT NULL"
        default_clause = f" DEFAULT {default}" if default else ""

        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}{null_clause}{default_clause}"

        cursor.execute(sql)
        logger.info(f"Added column '{column_name}' to table '{table_name}'")
        return True

    except Exception as e:
        raise MigrationError(
            f"Failed to add column '{column_name}' to '{table_name}': {e}"
        ) from e


def safe_add_column(
    table_name: str,
    column_name: str,
    column_type: str,
    default: Optional[str] = None,
    nullable: bool = True,
    using: str = "default",
) -> bool:
    """Add a column only if it doesn't already exist."""
    if column_exists(table_name, column_name, using):
        logger.debug(
            f"Column '{column_name}' already exists in '{table_name}', skipping"
        )
        return False

    add_column(table_name, column_name, column_type, default, nullable, using)
    return True


def rename_column(
    table_name: str, old_column_name: str, new_column_name: str, using: str = "default"
) -> bool:
    """Rename a column in a table."""
    try:
        from django.db import connections

        connection = connections[using]
        cursor = connection.cursor()

        if connection.vendor == "sqlite":
            raise MigrationError(
                "SQLite does not support renaming columns directly. "
                "Use recreate_table() instead."
            )

        sql = f"ALTER TABLE {table_name} RENAME COLUMN {old_column_name} TO {new_column_name}"
        cursor.execute(sql)
        logger.info(f"Renamed column '{old_column_name}' to '{new_column_name}'")
        return True

    except Exception as e:
        raise MigrationError(f"Failed to rename column: {e}") from e


def get_schema_diff(model_class, using: str = "default") -> Dict[str, Any]:
    """
    Compare model definition with actual database schema.

    Returns a dict with added/removed/changed columns.
    """
    from django.db import connections

    connection = connections[using]
    table_name = model_class._meta.db_table

    # Get existing columns
    existing_columns = set(get_table_columns(table_name, using))

    # Get model columns
    model_columns = set()
    for field in model_class._meta.local_fields:
        model_columns.add(field.column)

    return {
        "added": model_columns - existing_columns,
        "removed": existing_columns - model_columns,
        "table_exists": table_name in connection.introspection.table_names(),
    }


def sync_schema(model_class, using: str = "default", verbosity: int = 1) -> bool:
    """
    Sync a model's schema with the database.

    This adds missing columns but does not remove extra columns.
    """
    from django.db import connections

    diff = get_schema_diff(model_class, using)
    connection = connections[using]

    if not diff["table_exists"]:
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(model_class)
        if verbosity > 0:
            logger.info(f"Created table for {model_class.__name__}")
        return True

    if diff["added"]:
        with connection.schema_editor() as schema_editor:
            for field in model_class._meta.local_fields:
                if field.column in diff["added"]:
                    schema_editor.add_field(model_class, field)
                    if verbosity > 0:
                        logger.info(f"Added column {field.column}")

    return True
