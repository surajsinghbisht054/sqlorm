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
from typing import Dict, List, Type, Any, Optional

from .exceptions import ModelError, MigrationError

# Logger for this module
logger = logging.getLogger("sqlorm.base")

# Registry to keep track of all defined models
_model_registry: Dict[str, Type["Model"]] = {}


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
        if not getattr(objtype, '_initialized', False) or objtype._django_model is None:
            objtype._create_django_model()
        
        manager = objtype._django_model.objects
        
        # If model specifies a database alias, use it
        using_db = getattr(objtype, '_using', None)
        if using_db:
            return manager.using(using_db)
        
        return manager


class ModelMeta(type):
    """
    Metaclass for Model that handles:
    - Model registration
    - Django model class generation
    - App label assignment
    """
    
    def __new__(mcs, name: str, bases: tuple, namespace: dict):
        # Don't process the base Model class itself
        if name == "Model" and not any(
            hasattr(b, "_django_model") for b in bases
        ):
            return super().__new__(mcs, name, bases, namespace)
        
        # Check if this is a proper model (not an abstract or mixin)
        if namespace.get("_abstract", False):
            return super().__new__(mcs, name, bases, namespace)
        
        # Add the objects descriptor if not already present
        if 'objects' not in namespace:
            namespace['objects'] = ObjectsDescriptor()
        
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
        if not isinstance(getattr(cls, 'objects', None), ObjectsDescriptor):
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
            from django.db import models as django_models
            from django.apps import apps
        except ImportError:
            raise ModelError(
                "Django is not installed. Install it with: pip install django"
            )
        
        # Gather field definitions
        fields = {}
        for attr_name in dir(cls):
            if attr_name.startswith("_"):
                continue
            if attr_name == 'objects':
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
    def migrate(cls, verbosity: int = 1, interactive: bool = False, using: Optional[str] = None) -> bool:
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
        db_alias = using or cls._using or 'default'
        
        try:
            from django.db import connections
            from django.core.management.color import no_style
            from django.db.backends.base.schema import BaseDatabaseSchemaEditor
            
            # Get the connection for the specified database
            connection = connections[db_alias]
            
            with connection.schema_editor() as schema_editor:
                try:
                    schema_editor.create_model(cls._django_model)
                    if verbosity > 0:
                        logger.info(f"Created table for {cls.__name__} in '{db_alias}' database")
                except Exception as e:
                    # Table might already exist
                    if "already exists" in str(e).lower():
                        if verbosity > 0:
                            logger.info(f"Table for {cls.__name__} already exists in '{db_alias}' database")
                    else:
                        raise
            
            return True
            
        except Exception as e:
            raise MigrationError(f"Failed to migrate {cls.__name__} to '{db_alias}': {e}") from e
    
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
        db_alias = cls._using or 'default'
        
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
        db_alias = using or cls._using or 'default'
        
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
        return cls._using or 'default'
    
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
