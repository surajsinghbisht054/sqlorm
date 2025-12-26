"""
SQLORM Base Model
=================

Provides the Model class that creates Django models automatically.

Example:
    >>> from sqlorm import configure, Model, fields
    >>> configure({'ENGINE': 'django.db.backends.sqlite3', 'NAME': 'db.sqlite3'})
    >>>
    >>> class User(Model):
    ...     name = fields.CharField(max_length=100)
    ...     email = fields.EmailField(unique=True)
"""

import logging
from typing import Any, Dict, List, Optional, Type

from .exceptions import ConfigurationError

logger = logging.getLogger("sqlorm")

_model_registry: Dict[str, Type] = {}


def _ensure_django():
    """Ensure Django is configured."""
    try:
        import django
        from django.conf import settings

        if settings.configured and django.apps.apps.ready:
            return True
    except Exception:
        pass
    return False


def _register_model(model_class, name):
    """Register model in the sqlorm.app module."""
    try:
        from sqlorm.app import models as app_models

        app_models.register_model(name, model_class)
    except Exception as e:
        logger.debug(f"Could not register model: {e}")


class ModelMeta(type):
    """Metaclass that creates Django models from SQLORM model definitions."""

    def __new__(mcs, name: str, bases: tuple, namespace: dict):
        # Skip the base Model class
        if name == "Model" and not any(hasattr(b, "_is_sqlorm") for b in bases):
            cls = super().__new__(mcs, name, bases, namespace)
            cls._is_sqlorm = True
            return cls

        # Check for abstract
        meta = namespace.get("Meta")
        is_abstract = getattr(meta, "abstract", False) if meta else False

        if not _ensure_django():
            # Defer if Django not ready
            cls = super().__new__(mcs, name, bases, namespace)
            cls._deferred = True
            _model_registry[name] = cls
            return cls

        from django.apps import apps
        from django.db import models as django_models

        # Collect fields and methods
        fields = {}
        methods = {}
        for attr_name, attr_value in namespace.items():
            if isinstance(attr_value, django_models.Field):
                fields[attr_name] = attr_value
            elif callable(attr_value) or attr_name == "__str__":
                methods[attr_name] = attr_value

        # Build Meta
        meta_attrs = {"app_label": "sqlorm_app"}
        if namespace.get("_db_table"):
            meta_attrs["db_table"] = namespace["_db_table"]
        if meta:
            for attr in dir(meta):
                if not attr.startswith("_"):
                    meta_attrs[attr] = getattr(meta, attr)
        if is_abstract:
            meta_attrs["abstract"] = True

        NewMeta = type("Meta", (), meta_attrs)

        # Create Django model
        model_attrs = {
            "__module__": "sqlorm.app.models",
            "Meta": NewMeta,
            **fields,
            **methods,
        }

        django_model = type(name, (django_models.Model,), model_attrs)

        # Add custom methods
        for method_name, method in methods.items():
            setattr(django_model, method_name, method)

        # Add convenience methods
        mcs._add_methods(django_model)

        # Store database routing
        if "_using" in namespace:
            django_model._default_using = namespace["_using"]

        # Register
        if not is_abstract:
            try:
                if "sqlorm_app" not in apps.all_models:
                    apps.all_models["sqlorm_app"] = {}
                apps.all_models["sqlorm_app"][name.lower()] = django_model
                _register_model(django_model, name)
            except Exception as e:
                logger.debug(f"Registry error: {e}")

            _model_registry[name] = django_model

        return django_model

    @staticmethod
    def _add_methods(model):
        """Add convenience methods to the model."""

        def to_dict(self, fields=None, exclude=None) -> Dict[str, Any]:
            """Convert instance to dictionary."""
            exclude = exclude or []
            result = {}
            for field in self._meta.get_fields():
                if not hasattr(field, "attname"):
                    continue
                if fields and field.name not in fields:
                    continue
                if field.name in exclude:
                    continue
                value = getattr(self, field.name, None)
                if hasattr(value, "isoformat"):
                    value = value.isoformat()
                result[field.name] = value
            return result

        def to_json(self, indent=None) -> str:
            """Convert instance to JSON string."""
            import json

            return json.dumps(self.to_dict(), indent=indent, default=str)

        model.to_dict = to_dict
        model.to_json = to_json


class Model(metaclass=ModelMeta):
    """
    Base class for SQLORM models.

    Example:
        >>> class User(Model):
        ...     name = fields.CharField(max_length=100)
        ...     email = fields.EmailField(unique=True)
        ...
        ...     class Meta:
        ...         ordering = ['-id']
    """

    _is_sqlorm = True


def get_models() -> Dict[str, Type]:
    """Get all registered models."""
    return _model_registry.copy()


def create_tables(verbosity: int = 1) -> List[str]:
    """
    Create database tables for all registered models.

    Returns list of created table names.
    """
    from django.db import connections

    created = []
    for name, model in _model_registry.items():
        try:
            db = getattr(model, "_default_using", "default")
            conn = connections[db]
            table = model._meta.db_table

            if table not in conn.introspection.table_names():
                with conn.schema_editor() as editor:
                    editor.create_model(model)
                created.append(table)
                if verbosity:
                    print(f"Created table: {table}")
        except Exception as e:
            logger.error(f"Failed to create {name}: {e}")

    return created
