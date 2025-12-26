"""
SQLORM - Django ORM for Standalone Scripts
===========================================

Use Django's ORM without a Django project structure.

Quick Start:
    >>> from sqlorm import configure, Model, fields
    >>>
    >>> configure({
    ...     'ENGINE': 'django.db.backends.sqlite3',
    ...     'NAME': 'mydb.sqlite3',
    ... }, migrations_dir='./migrations')
    >>>
    >>> class User(Model):
    ...     name = fields.CharField(max_length=100)
    ...     email = fields.EmailField(unique=True)
    >>>
    >>> # Create tables (quick sync)
    >>> from sqlorm import create_tables
    >>> create_tables()
    >>>
    >>> # Or use migrations
    >>> # $ sqlorm makemigrations --models myfile.py
    >>> # $ sqlorm migrate --models myfile.py
    >>>
    >>> # Use Django ORM
    >>> user = User.objects.create(name="John", email="john@example.com")
    >>> user.to_dict()
    {'id': 1, 'name': 'John', 'email': 'john@example.com'}
"""

__version__ = "3.0.0"
__author__ = "S.S.B"

from .base import Model, create_tables, get_models
from .config import configure, configure_from_file, get_migrations_dir, is_configured
from .exceptions import ConfigurationError, MigrationError, ModelError
from .fields import fields

# Re-export Django utilities
try:
    from django.db.models import Avg, Count, F, Max, Min, Q, Sum
except ImportError:
    pass

__all__ = [
    # Config
    "configure",
    "configure_from_file",
    "is_configured",
    "get_migrations_dir",
    # Models
    "Model",
    "fields",
    "create_tables",
    "get_models",
    # Exceptions
    "ConfigurationError",
    "ModelError",
    "MigrationError",
    # Django
    "Q",
    "F",
    "Count",
    "Sum",
    "Avg",
    "Max",
    "Min",
]
