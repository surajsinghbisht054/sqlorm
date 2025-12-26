"""
SQLORM Base Model Module
========================

This module provides the base Model class that wraps Django's model
functionality for standalone usage.

The Model class provides:
- Automatic table creation and migrations
- All Django ORM querysets and methods
- Simplified model definition syntax
- Automatic app registration

Example:
    >>> from sqlorm import configure, Model, fields
    >>>
    >>> configure({'ENGINE': 'django.db.backends.sqlite3', 'NAME': 'db.sqlite3'})
    >>>
    >>> class Article(Model):
    ...     title = fields.CharField(max_length=200)
    ...     content = fields.TextField()
    ...     published = fields.BooleanField(default=False)
    ...     created_at = fields.DateTimeField(auto_now_add=True)
    >>>
    >>> Article.migrate()
    >>>
    >>> article = Article.objects.create(
    ...     title="Hello World",
    ...     content="This is my first article"
    ... )
"""

import logging
from typing import Any, Dict, List, Optional, Type

from .exceptions import MigrationError, ModelError

# Logger for this module
logger = logging.getLogger("sqlorm.base")

# Registry to keep track of all defined models
_model_registry: Dict[str, Type["Model"]] = {}


class ModelInstanceWrapper:
    """
    Wrapper that combines a Django model instance with SQLORM model methods.

    This allows custom methods defined on SQLORM models to be accessible
    on instances returned from querysets, and provides serialization utilities.
    """

    def __init__(self, django_instance, sqlorm_class):
        # Store references without triggering __setattr__ override
        object.__setattr__(self, "_django_instance", django_instance)
        object.__setattr__(self, "_sqlorm_class", sqlorm_class)

    def __getattr__(self, name):
        # First check if it's a custom method on the SQLORM class
        sqlorm_class = object.__getattribute__(self, "_sqlorm_class")
        django_instance = object.__getattribute__(self, "_django_instance")

        if name in sqlorm_class.__dict__ and callable(
            getattr(sqlorm_class, name, None)
        ):
            method = getattr(sqlorm_class, name)
            # Bind the method to this wrapper instance
            return lambda *args, **kwargs: method(self, *args, **kwargs)

        # Otherwise, get from Django instance
        return getattr(django_instance, name)

    def __setattr__(self, name, value):
        django_instance = object.__getattribute__(self, "_django_instance")
        setattr(django_instance, name, value)

    def __repr__(self):
        django_instance = object.__getattribute__(self, "_django_instance")
        return repr(django_instance)

    def __str__(self):
        sqlorm_class = object.__getattribute__(self, "_sqlorm_class")
        if "__str__" in sqlorm_class.__dict__:
            return sqlorm_class.__str__(self)
        django_instance = object.__getattribute__(self, "_django_instance")
        return str(django_instance)

    def __eq__(self, other):
        """Check equality with another instance."""
        django_instance = object.__getattribute__(self, "_django_instance")
        if isinstance(other, ModelInstanceWrapper):
            other_instance = object.__getattribute__(other, "_django_instance")
            return django_instance.pk == other_instance.pk
        if hasattr(other, "pk"):
            return django_instance.pk == other.pk
        return False

    def __hash__(self):
        """Make instance hashable for use in sets and as dict keys."""
        django_instance = object.__getattribute__(self, "_django_instance")
        return hash((type(django_instance).__name__, django_instance.pk))

    def to_dict(
        self,
        fields: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
        include_pk: bool = True,
    ) -> Dict[str, Any]:
        """
        Convert the model instance to a dictionary.

        Args:
            fields: List of field names to include (None = all fields)
            exclude: List of field names to exclude
            include_pk: Whether to include the primary key

        Returns:
            Dictionary representation of the model instance

        Example:
            >>> user = User.objects.get(id=1)
            >>> user.to_dict()
            {'id': 1, 'name': 'John', 'email': 'john@example.com'}
            >>> user.to_dict(fields=['name', 'email'])
            {'name': 'John', 'email': 'john@example.com'}
            >>> user.to_dict(exclude=['email'])
            {'id': 1, 'name': 'John'}
        """
        django_instance = object.__getattribute__(self, "_django_instance")
        exclude = exclude or []
        result = {}

        model_fields = django_instance._meta.get_fields()
        for field in model_fields:
            # Skip reverse relations and many-to-many for simple serialization
            if not hasattr(field, "attname"):
                continue

            name = field.name

            # Apply field filters
            if fields is not None and name not in fields:
                if not (include_pk and field.primary_key):
                    continue
            if name in exclude:
                continue
            if not include_pk and field.primary_key:
                continue

            value = getattr(django_instance, name, None)

            # Handle datetime objects for JSON serialization
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            # Handle Decimal
            elif hasattr(value, "__float__"):
                try:
                    value = float(value)
                except (TypeError, ValueError):
                    value = str(value)
            # Handle UUID
            elif hasattr(value, "hex"):
                value = str(value)

            result[name] = value

        return result

    def to_json(
        self,
        fields: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
        include_pk: bool = True,
        indent: Optional[int] = None,
    ) -> str:
        """
        Convert the model instance to a JSON string.

        Args:
            fields: List of field names to include (None = all fields)
            exclude: List of field names to exclude
            include_pk: Whether to include the primary key
            indent: JSON indentation level (None for compact)

        Returns:
            JSON string representation of the model instance

        Example:
            >>> user = User.objects.get(id=1)
            >>> user.to_json()
            '{"id": 1, "name": "John", "email": "john@example.com"}'
            >>> user.to_json(indent=2)
            '{\\n  "id": 1,\\n  "name": "John"\\n}'
        """
        import json

        data = self.to_dict(fields=fields, exclude=exclude, include_pk=include_pk)
        return json.dumps(data, indent=indent, default=str)

    def refresh(self) -> "ModelInstanceWrapper":
        """
        Reload the instance from the database.

        Returns:
            Self for chaining

        Example:
            >>> user.name = "Changed"
            >>> user.refresh()  # Reverts to database value
        """
        django_instance = object.__getattribute__(self, "_django_instance")
        django_instance.refresh_from_db()
        return self

    def update(self, **kwargs) -> "ModelInstanceWrapper":
        """
        Update fields and save in one operation.

        Args:
            **kwargs: Field names and values to update

        Returns:
            Self for chaining

        Example:
            >>> user.update(name="New Name", is_active=False)
        """
        django_instance = object.__getattribute__(self, "_django_instance")
        for key, value in kwargs.items():
            setattr(django_instance, key, value)
        django_instance.save(update_fields=list(kwargs.keys()))
        return self

    def clone(self, **overrides) -> "ModelInstanceWrapper":
        """
        Create a copy of this instance with optional field overrides.

        The clone is not saved to the database automatically.

        Args:
            **overrides: Field values to override in the clone

        Returns:
            New unsaved model instance

        Example:
            >>> original = User.objects.get(id=1)
            >>> clone = original.clone(name="Clone of " + original.name)
            >>> clone.save()
        """
        django_instance = object.__getattribute__(self, "_django_instance")
        sqlorm_class = object.__getattribute__(self, "_sqlorm_class")

        # Get all field values
        data = {}
        for field in django_instance._meta.get_fields():
            if hasattr(field, "attname") and not field.primary_key:
                data[field.name] = getattr(django_instance, field.name, None)

        # Apply overrides
        data.update(overrides)

        # Create new instance
        new_instance = sqlorm_class._django_model(**data)
        return ModelInstanceWrapper(new_instance, sqlorm_class)


class WrappedQuerySet:
    """
    A QuerySet wrapper that returns ModelInstanceWrapper objects instead
    of raw Django model instances.
    """

    def __init__(self, queryset, sqlorm_class):
        self._queryset = queryset
        self._sqlorm_class = sqlorm_class

    def _wrap(self, obj):
        """Wrap a Django model instance."""
        if obj is None:
            return None
        return ModelInstanceWrapper(obj, self._sqlorm_class)

    def _wrap_queryset(self, qs):
        """Return a new WrappedQuerySet for a queryset result."""
        return WrappedQuerySet(qs, self._sqlorm_class)

    def __iter__(self):
        for obj in self._queryset:
            yield self._wrap(obj)

    def __len__(self):
        return len(self._queryset)

    def __bool__(self):
        return bool(self._queryset)

    def __getitem__(self, key):
        result = self._queryset[key]
        if hasattr(result, "__iter__") and not hasattr(result, "_meta"):
            # It's a slice, return wrapped queryset
            return self._wrap_queryset(result)
        return self._wrap(result)

    # Methods that return single instances
    def get(self, *args, **kwargs):
        return self._wrap(self._queryset.get(*args, **kwargs))

    def first(self):
        return self._wrap(self._queryset.first())

    def last(self):
        return self._wrap(self._queryset.last())

    def earliest(self, *args, **kwargs):
        return self._wrap(self._queryset.earliest(*args, **kwargs))

    def latest(self, *args, **kwargs):
        return self._wrap(self._queryset.latest(*args, **kwargs))

    def create(self, **kwargs):
        return self._wrap(self._queryset.create(**kwargs))

    def get_or_create(self, **kwargs):
        obj, created = self._queryset.get_or_create(**kwargs)
        return self._wrap(obj), created

    def update_or_create(self, **kwargs):
        obj, created = self._queryset.update_or_create(**kwargs)
        return self._wrap(obj), created

    # Methods that return querysets
    def filter(self, *args, **kwargs):
        return self._wrap_queryset(self._queryset.filter(*args, **kwargs))

    def exclude(self, *args, **kwargs):
        return self._wrap_queryset(self._queryset.exclude(*args, **kwargs))

    def order_by(self, *args):
        return self._wrap_queryset(self._queryset.order_by(*args))

    def reverse(self):
        return self._wrap_queryset(self._queryset.reverse())

    def distinct(self, *args):
        return self._wrap_queryset(self._queryset.distinct(*args))

    def all(self):
        return self._wrap_queryset(self._queryset.all())

    def none(self):
        return self._wrap_queryset(self._queryset.none())

    def select_related(self, *args):
        return self._wrap_queryset(self._queryset.select_related(*args))

    def prefetch_related(self, *args):
        return self._wrap_queryset(self._queryset.prefetch_related(*args))

    def only(self, *args):
        return self._wrap_queryset(self._queryset.only(*args))

    def defer(self, *args):
        return self._wrap_queryset(self._queryset.defer(*args))

    def using(self, alias):
        return self._wrap_queryset(self._queryset.using(alias))

    def annotate(self, *args, **kwargs):
        return self._wrap_queryset(self._queryset.annotate(*args, **kwargs))

    def values(self, *args, **kwargs):
        return self._queryset.values(*args, **kwargs)

    def values_list(self, *args, **kwargs):
        return self._queryset.values_list(*args, **kwargs)

    # Aggregation methods (return values, not instances)
    def count(self):
        return self._queryset.count()

    def exists(self):
        return self._queryset.exists()

    def aggregate(self, *args, **kwargs):
        return self._queryset.aggregate(*args, **kwargs)

    def delete(self):
        return self._queryset.delete()

    def update(self, **kwargs):
        return self._queryset.update(**kwargs)

    def bulk_create(self, objs, **kwargs):
        results = self._queryset.bulk_create(objs, **kwargs)
        return [self._wrap(obj) for obj in results]

    def bulk_update(self, objs, fields, **kwargs):
        return self._queryset.bulk_update(objs, fields, **kwargs)

    def in_bulk(self, id_list=None, **kwargs):
        results = self._queryset.in_bulk(id_list, **kwargs)
        return {k: self._wrap(v) for k, v in results.items()}


class WrappedManager:
    """
    A manager wrapper that returns WrappedQuerySet objects.
    """

    def __init__(self, manager, sqlorm_class):
        self._manager = manager
        self._sqlorm_class = sqlorm_class

    def _wrap_queryset(self, qs):
        return WrappedQuerySet(qs, self._sqlorm_class)

    def _wrap(self, obj):
        if obj is None:
            return None
        return ModelInstanceWrapper(obj, self._sqlorm_class)

    def all(self):
        return self._wrap_queryset(self._manager.all())

    def filter(self, *args, **kwargs):
        return self._wrap_queryset(self._manager.filter(*args, **kwargs))

    def exclude(self, *args, **kwargs):
        return self._wrap_queryset(self._manager.exclude(*args, **kwargs))

    def get(self, *args, **kwargs):
        return self._wrap(self._manager.get(*args, **kwargs))

    def create(self, **kwargs):
        return self._wrap(self._manager.create(**kwargs))

    def get_or_create(self, **kwargs):
        obj, created = self._manager.get_or_create(**kwargs)
        return self._wrap(obj), created

    def update_or_create(self, **kwargs):
        obj, created = self._manager.update_or_create(**kwargs)
        return self._wrap(obj), created

    def first(self):
        return self._wrap(self._manager.first())

    def last(self):
        return self._wrap(self._manager.last())

    def count(self):
        return self._manager.count()

    def exists(self):
        return self._manager.exists()

    def none(self):
        return self._wrap_queryset(self._manager.none())

    def using(self, alias):
        return WrappedManager(self._manager.using(alias), self._sqlorm_class)

    def bulk_create(self, objs, **kwargs):
        results = self._manager.bulk_create(objs, **kwargs)
        return [self._wrap(obj) for obj in results]

    def in_bulk(self, id_list=None, **kwargs):
        results = self._manager.in_bulk(id_list, **kwargs)
        return {k: self._wrap(v) for k, v in results.items()}

    def order_by(self, *args):
        return self._wrap_queryset(self._manager.order_by(*args))

    def values(self, *args, **kwargs):
        return self._manager.values(*args, **kwargs)

    def values_list(self, *args, **kwargs):
        return self._manager.values_list(*args, **kwargs)

    def aggregate(self, *args, **kwargs):
        return self._manager.aggregate(*args, **kwargs)

    def annotate(self, *args, **kwargs):
        return self._wrap_queryset(self._manager.annotate(*args, **kwargs))

    def distinct(self, *args):
        return self._wrap_queryset(self._manager.distinct(*args))

    def select_related(self, *args):
        return self._wrap_queryset(self._manager.select_related(*args))

    def prefetch_related(self, *args):
        return self._wrap_queryset(self._manager.prefetch_related(*args))

    def only(self, *args):
        return self._wrap_queryset(self._manager.only(*args))

    def defer(self, *args):
        return self._wrap_queryset(self._manager.defer(*args))

    def reverse(self):
        return self._wrap_queryset(self._manager.reverse())

    def earliest(self, *args, **kwargs):
        return self._wrap(self._manager.earliest(*args, **kwargs))

    def latest(self, *args, **kwargs):
        return self._wrap(self._manager.latest(*args, **kwargs))


class ObjectsDescriptor:
    """
    Descriptor that provides access to the Django model's objects manager.

    This allows `Model.objects` to work as expected, returning the
    Django model's default manager.

    For multi-database support, this descriptor respects the model's
    `_using` attribute to route queries to the appropriate database.
    """

    def __get__(self, obj, objtype=None):
        if objtype is None:
            return self

        # Ensure the Django model is created
        if not getattr(objtype, "_initialized", False) or objtype._django_model is None:
            objtype._create_django_model()

        manager = objtype._django_model.objects

        # If model specifies a database alias, use it
        using_db = getattr(objtype, "_using", None)
        if using_db:
            manager = manager.using(using_db)

        # Return wrapped manager that provides SQLORM model instances
        return WrappedManager(manager, objtype)


class ModelMeta(type):
    """
    Metaclass for Model that handles:
    - Model registration
    - Django model class generation
    - App label assignment
    """

    def __new__(mcs, name: str, bases: tuple, namespace: dict):
        # Don't process the base Model class itself
        if name == "Model" and not any(hasattr(b, "_django_model") for b in bases):
            return super().__new__(mcs, name, bases, namespace)

        # Check if this is a proper model (not an abstract or mixin)
        if namespace.get("_abstract", False):
            return super().__new__(mcs, name, bases, namespace)

        # Add the objects descriptor if not already present
        if "objects" not in namespace:
            namespace["objects"] = ObjectsDescriptor()

        # Create the class first
        cls = super().__new__(mcs, name, bases, namespace)

        # Register the model
        if name != "Model":
            _model_registry[name] = cls
            logger.debug(f"Registered model: {name}")

        return cls


class Model(metaclass=ModelMeta):
    """
    Base class for all SQLORM models.

    Inherit from this class to define your database models. The syntax
    is identical to Django's model definition.

    Class Attributes:
        _abstract: Set to True to make this an abstract base class
        _app_label: Django app label (auto-generated if not set)
        _db_table: Custom database table name
        _using: Database alias for multi-database support (default: uses 'default')

    Example:
        >>> class User(Model):
        ...     name = fields.CharField(max_length=100)
        ...     email = fields.EmailField(unique=True)
        ...     is_active = fields.BooleanField(default=True)
        ...
        ...     class Meta:
        ...         ordering = ['-id']
        ...         verbose_name = 'User'
        >>>
        >>> # Create the table
        >>> User.migrate()
        >>>
        >>> # Create a user
        >>> user = User.objects.create(name="John", email="john@example.com")
        >>>
        >>> # Query users
        >>> active_users = User.objects.filter(is_active=True)
        >>> user = User.objects.get(email="john@example.com")

        >>> # Multi-database example
        >>> class AnalyticsEvent(Model):
        ...     _using = 'analytics'  # Routes all queries to 'analytics' database
        ...     event_name = fields.CharField(max_length=100)
        ...     timestamp = fields.DateTimeField(auto_now_add=True)
    """

    # Class-level attributes
    _abstract = False
    _app_label = "sqlorm_models"
    _db_table: Optional[str] = None
    _using: Optional[str] = None  # Database alias for multi-database support
    _django_model: Optional[Type] = None
    _initialized = False

    # Objects manager descriptor
    objects = ObjectsDescriptor()

    def __init_subclass__(cls, **kwargs):
        """
        Called when a class inherits from Model.
        This sets up the Django model and prepares it for use.
        """
        super().__init_subclass__(**kwargs)

        # Ensure objects descriptor is on each subclass
        if not isinstance(getattr(cls, "objects", None), ObjectsDescriptor):
            cls.objects = ObjectsDescriptor()

        # Skip abstract models
        if getattr(cls, "_abstract", False):
            return

        # Create Django model when the class is defined
        try:
            cls._create_django_model()
        except Exception as e:
            # Django might not be configured yet, defer creation
            logger.debug(f"Deferred Django model creation for {cls.__name__}: {e}")

        # Monkey patch __str__ if it's defined in the subclass
        if "__str__" in cls.__dict__:
            # We need to wrap it to handle 'self' correctly when called from Django model
            original_str = cls.__str__

            def wrapped_str(self):
                # Create a temporary instance of our Model class to pass to __str__
                # This is a bit hacky but necessary because Django models are different classes
                return original_str(self)

            cls._django_model.__str__ = wrapped_str

    @classmethod
    def _create_django_model(cls):
        """
        Create the underlying Django model class.

        This method generates a Django model class from the field definitions
        on the SQLORM model class.
        """
        if cls._django_model is not None:
            return cls._django_model

        try:
            from django.apps import apps
            from django.db import models as django_models
        except ImportError:
            raise ModelError(
                "Django is not installed. Install it with: pip install django"
            )

        # Gather field definitions
        fields = {}
        for attr_name in dir(cls):
            if attr_name.startswith("_"):
                continue
            if attr_name == "objects":
                continue  # Skip the objects descriptor

            attr = getattr(cls, attr_name, None)
            if isinstance(attr, django_models.Field):
                fields[attr_name] = attr

        # Build Meta class options
        meta_attrs = {
            "app_label": cls._app_label,
        }

        if cls._db_table:
            meta_attrs["db_table"] = cls._db_table

        # Check for user-defined Meta class
        if hasattr(cls, "Meta") and not isinstance(cls.Meta, type(None)):
            user_meta = cls.Meta
            for attr in dir(user_meta):
                if not attr.startswith("_"):
                    meta_attrs[attr] = getattr(user_meta, attr)

        Meta = type("Meta", (), meta_attrs)

        # Build the Django model class
        model_attrs = {
            "__module__": cls.__module__,
            "Meta": Meta,
            **fields,
        }

        # Create the Django model
        django_model = type(cls.__name__, (django_models.Model,), model_attrs)

        # Store reference
        cls._django_model = django_model
        cls._initialized = True

        # Expose Django model exceptions on SQLORM class for convenient access
        cls.DoesNotExist = django_model.DoesNotExist
        cls.MultipleObjectsReturned = django_model.MultipleObjectsReturned

        # Register with Django's app registry
        try:
            if not apps.all_models.get(cls._app_label):
                apps.all_models[cls._app_label] = {}
            apps.all_models[cls._app_label][cls.__name__.lower()] = django_model
        except Exception as e:
            logger.debug(f"Could not register model with app registry: {e}")

        logger.debug(f"Created Django model for {cls.__name__}")
        return django_model

    @classmethod
    def _ensure_initialized(cls):
        """Ensure the Django model is initialized."""
        if not cls._initialized or cls._django_model is None:
            cls._create_django_model()

    @classmethod
    def migrate(
        cls, verbosity: int = 1, interactive: bool = False, using: Optional[str] = None
    ) -> bool:
        """
        Create or update the database table for this model.

        This method handles table creation and schema migrations. It's
        equivalent to Django's makemigrations + migrate commands.

        For multi-database setups, the migration is applied to the database
        specified by the model's `_using` attribute, or the 'using' parameter.

        Args:
            verbosity: Output verbosity level (0=silent, 1=normal, 2=verbose)
            interactive: Whether to prompt for user input
            using: Database alias to migrate to (overrides model's _using)

        Returns:
            True if successful

        Raises:
            MigrationError: If migration fails

        Example:
            >>> class User(Model):
            ...     name = fields.CharField(max_length=100)
            >>>
            >>> User.migrate()
            True

            >>> # Migrate to a specific database
            >>> class LogEntry(Model):
            ...     _using = 'logs'
            ...     message = fields.TextField()
            >>>
            >>> LogEntry.migrate()  # Uses 'logs' database
            True
        """
        cls._ensure_initialized()

        # Determine which database to use
        db_alias = using or cls._using or "default"

        try:
            from django.core.management.color import no_style
            from django.db import connections
            from django.db.backends.base.schema import BaseDatabaseSchemaEditor

            # Get the connection for the specified database
            connection = connections[db_alias]

            # Check if table exists
            with connection.cursor() as cursor:
                table_list = connection.introspection.table_names(cursor)

            table_name = cls._django_model._meta.db_table

            with connection.schema_editor() as schema_editor:
                if table_name not in table_list:
                    schema_editor.create_model(cls._django_model)
                    if verbosity > 0:
                        logger.info(
                            f"Created table for {cls.__name__} in '{db_alias}' database"
                        )
                else:
                    # Table exists, check for missing columns
                    if verbosity > 0:
                        logger.info(
                            f"Table for {cls.__name__} already exists in '{db_alias}' database. Checking for schema updates..."
                        )

                    existing_columns = get_table_columns(table_name, using=db_alias)
                    existing_columns_lower = [c.lower() for c in existing_columns]

                    for field in cls._django_model._meta.local_fields:
                        if field.column.lower() not in existing_columns_lower:
                            try:
                                schema_editor.add_field(cls._django_model, field)
                                if verbosity > 0:
                                    logger.info(
                                        f"Added column '{field.column}' to table '{table_name}'"
                                    )
                            except Exception as e:
                                logger.error(
                                    f"Failed to add column '{field.column}': {e}"
                                )
                                raise

            return True

        except Exception as e:
            raise MigrationError(
                f"Failed to migrate {cls.__name__} to '{db_alias}': {e}"
            ) from e

    @classmethod
    def drop_table(cls, confirm: bool = False) -> bool:
        """
        Drop the database table for this model.

        Warning: This will permanently delete all data in the table!

        Args:
            confirm: Must be True to actually drop the table (safety check)
            using: Database alias to drop table from (overrides model's _using)

        Returns:
            True if successful

        Example:
            >>> User.drop_table(confirm=True)
            True
        """
        if not confirm:
            raise ModelError(
                "You must pass confirm=True to drop a table. "
                "This will permanently delete all data!"
            )

        cls._ensure_initialized()

        # Determine which database to use
        db_alias = cls._using or "default"

        try:
            from django.db import connections

            connection = connections[db_alias]
            with connection.schema_editor() as schema_editor:
                schema_editor.delete_model(cls._django_model)

            logger.info(f"Dropped table for {cls.__name__} from '{db_alias}' database")
            return True

        except Exception as e:
            raise ModelError(f"Failed to drop table for {cls.__name__}: {e}") from e

    @classmethod
    def table_exists(cls, using: Optional[str] = None) -> bool:
        """
        Check if the database table for this model exists.

        Args:
            using: Database alias to check (overrides model's _using)

        Returns:
            True if the table exists, False otherwise

        Example:
            >>> if not User.table_exists():
            ...     User.migrate()
        """
        cls._ensure_initialized()

        # Determine which database to use
        db_alias = using or cls._using or "default"

        try:
            from django.db import connections

            connection = connections[db_alias]
            table_name = cls._django_model._meta.db_table
            return table_name in connection.introspection.table_names()

        except Exception:
            return False

    @classmethod
    def get_database_alias(cls) -> str:
        """
        Get the database alias this model uses.

        Returns:
            Database alias string (default: 'default')

        Example:
            >>> class LogEntry(Model):
            ...     _using = 'logs'
            >>> LogEntry.get_database_alias()
            'logs'
        """
        return cls._using or "default"

    @classmethod
    def get_table_name(cls) -> str:
        """
        Get the database table name for this model.

        Returns:
            Table name string
        """
        cls._ensure_initialized()
        return cls._django_model._meta.db_table

    @classmethod
    def get_fields(cls) -> List[str]:
        """
        Get a list of field names for this model.

        Returns:
            List of field name strings

        Example:
            >>> User.get_fields()
            ['id', 'name', 'email', 'is_active']
        """
        cls._ensure_initialized()
        return [f.name for f in cls._django_model._meta.get_fields()]

    @classmethod
    def get_field_info(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get detailed information about all fields in this model.

        Returns:
            Dictionary mapping field names to their properties including
            type, null, blank, default, primary_key, unique, etc.

        Example:
            >>> info = User.get_field_info()
            >>> print(info['email'])
            {'type': 'EmailField', 'null': False, 'unique': True, ...}
        """
        cls._ensure_initialized()
        field_info = {}
        for field in cls._django_model._meta.get_fields():
            if hasattr(field, "get_internal_type"):
                field_info[field.name] = {
                    "type": field.get_internal_type(),
                    "null": getattr(field, "null", None),
                    "blank": getattr(field, "blank", None),
                    "default": getattr(field, "default", None),
                    "primary_key": getattr(field, "primary_key", False),
                    "unique": getattr(field, "unique", False),
                    "max_length": getattr(field, "max_length", None),
                    "db_column": getattr(field, "db_column", None) or field.name,
                }
        return field_info

    @classmethod
    def count(cls, using: Optional[str] = None) -> int:
        """
        Get the count of all records for this model.

        Args:
            using: Database alias (overrides model's _using)

        Returns:
            Number of records

        Example:
            >>> User.count()
            42
        """
        cls._ensure_initialized()
        db_alias = using or cls._using or "default"
        return cls._django_model.objects.using(db_alias).count()

    @classmethod
    def exists(cls, using: Optional[str] = None, **filters) -> bool:
        """
        Check if any records exist matching the given filters.

        Args:
            using: Database alias (overrides model's _using)
            **filters: Filter conditions (same as filter() method)

        Returns:
            True if matching records exist

        Example:
            >>> User.exists(is_active=True)
            True
        """
        cls._ensure_initialized()
        db_alias = using or cls._using or "default"
        queryset = cls._django_model.objects.using(db_alias)
        if filters:
            queryset = queryset.filter(**filters)
        return queryset.exists()

    @classmethod
    def truncate(cls, confirm: bool = False, using: Optional[str] = None) -> bool:
        """
        Delete all records from the table (faster than delete()).

        Warning: This permanently deletes all data!

        Args:
            confirm: Must be True to actually truncate (safety check)
            using: Database alias

        Returns:
            True if successful

        Example:
            >>> User.truncate(confirm=True)
            True
        """
        if not confirm:
            raise ModelError(
                "You must pass confirm=True to truncate a table. "
                "This will permanently delete all data!"
            )

        cls._ensure_initialized()
        db_alias = using or cls._using or "default"

        try:
            from django.db import connections

            connection = connections[db_alias]
            table_name = cls._django_model._meta.db_table

            with connection.cursor() as cursor:
                if connection.vendor == "sqlite":
                    cursor.execute(f"DELETE FROM {table_name}")
                else:
                    cursor.execute(f"TRUNCATE TABLE {table_name}")

            logger.info(f"Truncated table for {cls.__name__}")
            return True
        except Exception as e:
            raise ModelError(f"Failed to truncate table: {e}") from e

    def __repr__(self):
        cls_name = self.__class__.__name__
        pk = getattr(self, "pk", None) or getattr(self, "id", None)
        return f"<{cls_name}: {pk}>"

    def __str__(self):
        return self.__repr__()


def get_registered_models() -> Dict[str, Type[Model]]:
    """
    Get all registered models.

    Returns:
        Dictionary mapping model names to model classes

    Example:
        >>> models = get_registered_models()
        >>> for name, model in models.items():
        ...     print(f"{name}: {model.get_table_name()}")
    """
    return _model_registry.copy()


def create_all_tables(verbosity: int = 1) -> List[str]:
    """
    Create database tables for all registered models.

    This is a convenience function to migrate all models at once.

    Args:
        verbosity: Output verbosity level

    Returns:
        List of created table names

    Example:
        >>> create_all_tables()
        ['user', 'article', 'comment']
    """
    created = []

    for name, model in _model_registry.items():
        try:
            if not model.table_exists():
                model.migrate(verbosity=verbosity)
                created.append(model.get_table_name())
        except Exception as e:
            logger.error(f"Failed to create table for {name}: {e}")

    return created


def migrate_all(verbosity: int = 1) -> None:
    """
    Run migrations for all registered models.

    Args:
        verbosity: Output verbosity level

    Example:
        >>> migrate_all()
    """
    for name, model in _model_registry.items():
        try:
            model.migrate(verbosity=verbosity)
        except Exception as e:
            logger.error(f"Failed to migrate {name}: {e}")


def clear_registry():
    """
    Clear the model registry.

    Warning: This is primarily for testing purposes.
    """
    global _model_registry
    _model_registry = {}
    logger.warning("Model registry cleared")


# =============================================================================
# Schema Migration Utilities
# =============================================================================


def get_table_columns(table_name: str, using: str = "default") -> List[str]:
    """
    Get the list of column names for a table.

    Args:
        table_name: Name of the database table
        using: Database alias

    Returns:
        List of column name strings

    Example:
        >>> columns = get_table_columns('user')
        >>> print(columns)
        ['id', 'name', 'email', 'created_at']
    """
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
    """
    Check if a column exists in a table.

    Args:
        table_name: Name of the database table
        column_name: Name of the column to check
        using: Database alias

    Returns:
        True if column exists, False otherwise

    Example:
        >>> if not column_exists('user', 'phone'):
        ...     add_column('user', 'phone', 'VARCHAR(20)')
    """
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
    """
    Add a new column to an existing table.

    Args:
        table_name: Name of the database table
        column_name: Name of the new column
        column_type: SQL type of the column (e.g., 'VARCHAR(100)', 'INTEGER')
        default: Default value SQL expression (e.g., "'pending'", "0")
        nullable: Whether the column can be NULL
        using: Database alias

    Returns:
        True if successful

    Raises:
        MigrationError: If the column cannot be added

    Example:
        >>> add_column('user', 'phone', 'VARCHAR(20)', nullable=True)
        >>> add_column('product', 'discount', 'DECIMAL(5,2)', default='0.00')
    """
    try:
        from django.db import connections

        connection = connections[using]
        cursor = connection.cursor()

        # Build ALTER TABLE statement
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
    """
    Add a column only if it doesn't already exist.

    This is a safe wrapper around add_column() that checks for column
    existence first, preventing errors when running migrations multiple times.

    Args:
        table_name: Name of the database table
        column_name: Name of the new column
        column_type: SQL type of the column
        default: Default value SQL expression
        nullable: Whether the column can be NULL
        using: Database alias

    Returns:
        True if column was added, False if it already existed

    Example:
        >>> # Safe to call multiple times
        >>> safe_add_column('user', 'verified', 'BOOLEAN', default='0')
        True
        >>> safe_add_column('user', 'verified', 'BOOLEAN', default='0')
        False  # Already exists, not added again
    """
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
    """
    Rename a column in a table.

    Note: SQLite versions before 3.25.0 do not support ALTER TABLE RENAME COLUMN.
    For older SQLite versions, this function uses table recreation.

    Args:
        table_name: Name of the database table
        old_column_name: Current name of the column
        new_column_name: New name for the column
        using: Database alias

    Returns:
        True if successful

    Example:
        >>> rename_column('user', 'username', 'user_name')
    """
    try:
        import sqlite3

        from django.db import connections

        connection = connections[using]
        cursor = connection.cursor()

        if connection.vendor == "sqlite":
            # Check SQLite version
            sqlite_version = tuple(int(x) for x in sqlite3.sqlite_version.split("."))

            if sqlite_version >= (3, 25, 0):
                # Modern SQLite supports RENAME COLUMN
                sql = f"ALTER TABLE {table_name} RENAME COLUMN {old_column_name} TO {new_column_name}"
                cursor.execute(sql)
            else:
                # Older SQLite requires table recreation
                logger.warning(
                    f"SQLite {sqlite3.sqlite_version} doesn't support RENAME COLUMN, using table recreation"
                )
                _rename_column_via_recreation(
                    table_name, old_column_name, new_column_name, using
                )
        else:
            # PostgreSQL, MySQL support standard syntax
            if connection.vendor == "postgresql":
                sql = f"ALTER TABLE {table_name} RENAME COLUMN {old_column_name} TO {new_column_name}"
            elif connection.vendor == "mysql":
                # MySQL requires knowing the column type
                cursor.execute(f"DESCRIBE {table_name}")
                column_info = {row[0]: row[1] for row in cursor.fetchall()}
                col_type = column_info.get(old_column_name, "VARCHAR(255)")
                sql = f"ALTER TABLE {table_name} CHANGE {old_column_name} {new_column_name} {col_type}"
            else:
                sql = f"ALTER TABLE {table_name} RENAME COLUMN {old_column_name} TO {new_column_name}"

            cursor.execute(sql)

        logger.info(
            f"Renamed column '{old_column_name}' to '{new_column_name}' in '{table_name}'"
        )
        return True

    except Exception as e:
        raise MigrationError(f"Failed to rename column: {e}") from e


def _rename_column_via_recreation(
    table_name: str, old_column_name: str, new_column_name: str, using: str = "default"
):
    """Helper to rename column by recreating table (for old SQLite)."""
    from django.db import connections

    connection = connections[using]
    cursor = connection.cursor()

    # Get current schema
    cursor.execute(
        f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'"
    )
    create_sql = cursor.fetchone()[0]

    # Modify the CREATE statement
    new_create_sql = create_sql.replace(old_column_name, new_column_name)

    # Get all column names
    columns = get_table_columns(table_name, using)
    old_columns = ", ".join(columns)
    new_columns = ", ".join(
        new_column_name if c == old_column_name else c for c in columns
    )

    # Rename old table, create new, copy data, drop old
    cursor.execute(f"ALTER TABLE {table_name} RENAME TO {table_name}_old")
    cursor.execute(new_create_sql)
    cursor.execute(
        f"INSERT INTO {table_name} ({new_columns}) SELECT {old_columns} FROM {table_name}_old"
    )
    cursor.execute(f"DROP TABLE {table_name}_old")


def change_column_type(
    table_name: str, column_name: str, new_type: str, using: str = "default"
) -> bool:
    """
    Change the data type of a column.

    Warning: This may cause data loss if the conversion is not compatible.
    SQLite requires table recreation for type changes.

    Args:
        table_name: Name of the database table
        column_name: Name of the column to modify
        new_type: New SQL type for the column
        using: Database alias

    Returns:
        True if successful

    Example:
        >>> change_column_type('product', 'price', 'DECIMAL(12,4)')
    """
    try:
        from django.db import connections

        connection = connections[using]
        cursor = connection.cursor()

        if connection.vendor == "sqlite":
            # SQLite requires table recreation for type changes
            _change_column_type_sqlite(table_name, column_name, new_type, cursor)
        elif connection.vendor == "postgresql":
            sql = f"ALTER TABLE {table_name} ALTER COLUMN {column_name} TYPE {new_type}"
            cursor.execute(sql)
        elif connection.vendor == "mysql":
            sql = f"ALTER TABLE {table_name} MODIFY {column_name} {new_type}"
            cursor.execute(sql)
        else:
            raise MigrationError(f"Unsupported database vendor: {connection.vendor}")

        logger.info(
            f"Changed column '{column_name}' type to '{new_type}' in '{table_name}'"
        )
        return True

    except Exception as e:
        raise MigrationError(f"Failed to change column type: {e}") from e


def _change_column_type_sqlite(
    table_name: str, column_name: str, new_type: str, cursor
):
    """Helper to change column type in SQLite via table recreation."""
    # Get current table schema
    cursor.execute(
        f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'"
    )
    result = cursor.fetchone()
    if not result:
        raise MigrationError(f"Table '{table_name}' not found")

    create_sql = result[0]

    # Parse and modify the schema (simple regex replacement)
    import re

    # Match column definition like: column_name TYPE
    pattern = rf"\b{column_name}\s+\w+(?:\([^)]+\))?"
    new_def = f"{column_name} {new_type}"
    modified_sql = re.sub(pattern, new_def, create_sql, count=1, flags=re.IGNORECASE)

    # Get columns
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    columns_str = ", ".join(columns)

    # Recreate table
    cursor.execute(f"ALTER TABLE {table_name} RENAME TO {table_name}_old")
    cursor.execute(modified_sql)
    cursor.execute(
        f"INSERT INTO {table_name} ({columns_str}) SELECT {columns_str} FROM {table_name}_old"
    )
    cursor.execute(f"DROP TABLE {table_name}_old")


def recreate_table(
    table_name: str, new_schema: str, columns_to_copy: List[str], using: str = "default"
) -> bool:
    """
    Recreate a table with a new schema while preserving specified data.

    This is useful for complex schema changes that cannot be done with
    ALTER TABLE (especially in SQLite).

    Args:
        table_name: Name of the table to recreate
        new_schema: Full CREATE TABLE SQL statement for the new schema
        columns_to_copy: List of column names to copy from old to new table
        using: Database alias

    Returns:
        True if successful

    Example:
        >>> new_schema = '''
        ...     CREATE TABLE users (
        ...         id INTEGER PRIMARY KEY,
        ...         full_name VARCHAR(200),
        ...         email VARCHAR(254)
        ...     )
        ... '''
        >>> recreate_table('users', new_schema, ['id', 'email'])
    """
    try:
        from django.db import connections

        connection = connections[using]
        cursor = connection.cursor()

        columns_str = ", ".join(columns_to_copy)

        # Rename old table
        cursor.execute(f"ALTER TABLE {table_name} RENAME TO {table_name}_old")

        # Create new table
        cursor.execute(new_schema)

        # Copy data
        cursor.execute(
            f"INSERT INTO {table_name} ({columns_str}) SELECT {columns_str} FROM {table_name}_old"
        )

        # Drop old table
        cursor.execute(f"DROP TABLE {table_name}_old")

        logger.info(f"Recreated table '{table_name}' with new schema")
        return True

    except Exception as e:
        raise MigrationError(f"Failed to recreate table: {e}") from e


def backup_table(
    table_name: str, suffix: str = "_backup", using: str = "default"
) -> str:
    """
    Create a backup copy of a table.

    Args:
        table_name: Name of the table to backup
        suffix: Suffix for the backup table name
        using: Database alias

    Returns:
        Name of the backup table

    Example:
        >>> backup_name = backup_table('users')
        >>> print(backup_name)
        'users_backup'
    """
    try:
        from django.db import connections

        connection = connections[using]
        cursor = connection.cursor()

        backup_name = f"{table_name}{suffix}"

        # Create backup table with same structure and data
        if connection.vendor == "sqlite":
            cursor.execute(f"CREATE TABLE {backup_name} AS SELECT * FROM {table_name}")
        elif connection.vendor == "postgresql":
            cursor.execute(f"CREATE TABLE {backup_name} AS SELECT * FROM {table_name}")
        elif connection.vendor == "mysql":
            cursor.execute(f"CREATE TABLE {backup_name} AS SELECT * FROM {table_name}")
        else:
            cursor.execute(f"CREATE TABLE {backup_name} AS SELECT * FROM {table_name}")

        logger.info(f"Created backup table '{backup_name}'")
        return backup_name

    except Exception as e:
        raise MigrationError(f"Failed to backup table: {e}") from e


def restore_table(
    table_name: str, suffix: str = "_backup", using: str = "default"
) -> bool:
    """
    Restore a table from its backup.

    Args:
        table_name: Name of the table to restore
        suffix: Suffix of the backup table name
        using: Database alias

    Returns:
        True if successful

    Example:
        >>> restore_table('users')  # Restores from users_backup
    """
    try:
        from django.db import connections

        connection = connections[using]
        cursor = connection.cursor()

        backup_name = f"{table_name}{suffix}"

        # Recreate table from backup
        if connection.vendor == "sqlite":
            cursor.execute(f"CREATE TABLE {table_name} AS SELECT * FROM {backup_name}")
        else:
            cursor.execute(f"CREATE TABLE {table_name} AS SELECT * FROM {backup_name}")

        logger.info(f"Restored table '{table_name}' from backup")
        return True

    except Exception as e:
        raise MigrationError(f"Failed to restore table: {e}") from e


def get_schema_diff(model_class: Type[Model], using: str = "default") -> Dict[str, Any]:
    """
    Compare model definition with actual database schema.

    Returns information about differences between the model's field
    definitions and the actual database table structure.

    Args:
        model_class: The model class to compare
        using: Database alias

    Returns:
        Dictionary with 'missing_in_db', 'extra_in_db' lists

    Example:
        >>> diff = get_schema_diff(User)
        >>> if diff['missing_in_db']:
        ...     print(f"Need to add columns: {diff['missing_in_db']}")
    """
    model_class._ensure_initialized()

    table_name = model_class._django_model._meta.db_table

    # Get columns from database
    db_columns = set(c.lower() for c in get_table_columns(table_name, using))

    # Get columns from model
    model_columns = set()
    for field in model_class._django_model._meta.get_fields():
        if hasattr(field, "column") and field.column:
            model_columns.add(field.column.lower())
        elif hasattr(field, "name"):
            model_columns.add(field.name.lower())

    # Compute differences
    missing_in_db = model_columns - db_columns
    extra_in_db = db_columns - model_columns

    return {
        "missing_in_db": list(missing_in_db),
        "extra_in_db": list(extra_in_db),
        "model_columns": list(model_columns),
        "db_columns": list(db_columns),
    }


def sync_schema(
    model_class: Type[Model], using: str = "default"
) -> Dict[str, List[str]]:
    """
    Sync database schema with model definition by adding missing columns.

    This function adds columns that exist in the model but not in the
    database. It does NOT remove extra columns or change types.

    Args:
        model_class: The model class to sync
        using: Database alias

    Returns:
        Dictionary with 'added' and 'skipped' column lists

    Example:
        >>> result = sync_schema(User)
        >>> print(f"Added columns: {result['added']}")
    """
    model_class._ensure_initialized()

    diff = get_schema_diff(model_class, using)
    table_name = model_class._django_model._meta.db_table

    added = []
    skipped = []

    for column_name in diff["missing_in_db"]:
        # Find the field definition
        field = None
        for f in model_class._django_model._meta.get_fields():
            col_name = getattr(f, "column", getattr(f, "name", None))
            if col_name and col_name.lower() == column_name.lower():
                field = f
                break

        if field:
            try:
                # Determine SQL type (simplified mapping)
                field_type = type(field).__name__
                sql_type = _django_field_to_sql_type(field)

                # Get default value
                default = None
                if field.has_default():
                    default_val = field.get_default()
                    if isinstance(default_val, str):
                        default = f"'{default_val}'"
                    elif isinstance(default_val, bool):
                        default = "1" if default_val else "0"
                    elif default_val is not None:
                        default = str(default_val)

                safe_add_column(
                    table_name=table_name,
                    column_name=column_name,
                    column_type=sql_type,
                    default=default,
                    nullable=field.null if hasattr(field, "null") else True,
                    using=using,
                )
                added.append(column_name)
            except Exception as e:
                logger.warning(f"Could not add column {column_name}: {e}")
                skipped.append(column_name)
        else:
            skipped.append(column_name)

    return {"added": added, "skipped": skipped}


def _django_field_to_sql_type(field) -> str:
    """Convert a Django field to SQL type string."""
    field_type = type(field).__name__

    type_map = {
        "CharField": f"VARCHAR({getattr(field, 'max_length', 255)})",
        "TextField": "TEXT",
        "IntegerField": "INTEGER",
        "BigIntegerField": "BIGINT",
        "SmallIntegerField": "SMALLINT",
        "FloatField": "REAL",
        "DecimalField": f"DECIMAL({getattr(field, 'max_digits', 10)},{getattr(field, 'decimal_places', 2)})",
        "BooleanField": "BOOLEAN",
        "DateField": "DATE",
        "DateTimeField": "DATETIME",
        "TimeField": "TIME",
        "EmailField": f"VARCHAR({getattr(field, 'max_length', 254)})",
        "URLField": f"VARCHAR({getattr(field, 'max_length', 200)})",
        "UUIDField": "VARCHAR(36)",
        "AutoField": "INTEGER",
        "BigAutoField": "BIGINT",
    }

    return type_map.get(field_type, "TEXT")
