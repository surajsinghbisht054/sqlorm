"""
SQLORM Fields Module
====================

This module provides a convenient wrapper around Django's model fields,
making them easily accessible for use in standalone scripts.

All Django field types are available through the `fields` namespace:
    - fields.CharField
    - fields.IntegerField
    - fields.TextField
    - fields.BooleanField
    - And many more...

Example:
    >>> from sqlorm import fields
    >>>
    >>> class User(Model):
    ...     name = fields.CharField(max_length=100)
    ...     email = fields.EmailField(unique=True)
    ...     age = fields.IntegerField(null=True, blank=True)
    ...     bio = fields.TextField(default="")
    ...     is_active = fields.BooleanField(default=True)
    ...     created_at = fields.DateTimeField(auto_now_add=True)
    ...     updated_at = fields.DateTimeField(auto_now=True)
"""

import logging
from typing import Any

logger = logging.getLogger("sqlorm.fields")


class FieldsProxy:
    """
    Proxy class that provides access to Django model fields.

    This class lazily imports Django fields when accessed, allowing
    you to define models before Django is configured.

    Usage:
        >>> from sqlorm import fields
        >>>
        >>> # Access any Django field type
        >>> name_field = fields.CharField(max_length=100)
        >>> age_field = fields.IntegerField(null=True)
        >>> email_field = fields.EmailField(unique=True)
    """

    _fields_module = None

    @classmethod
    def _get_fields_module(cls):
        """Get the Django models module, importing it if necessary."""
        if cls._fields_module is None:
            try:
                from django.db import models

                cls._fields_module = models
            except ImportError:
                raise ImportError(
                    "Django is not installed. " "Install it with: pip install django"
                )
        return cls._fields_module

    def __getattr__(self, name: str) -> Any:
        """
        Get a Django field class by name.

        Args:
            name: Name of the Django field class (e.g., 'CharField')

        Returns:
            Django field class

        Raises:
            AttributeError: If the field type doesn't exist
        """
        models = self._get_fields_module()

        if hasattr(models, name):
            return getattr(models, name)

        raise AttributeError(
            f"Unknown field type: {name}. "
            f"See Django documentation for available field types."
        )

    def __dir__(self):
        """List available field types."""
        try:
            models = self._get_fields_module()
            return [
                name
                for name in dir(models)
                if name.endswith("Field")
                or name in ("ForeignKey", "OneToOneField", "ManyToManyField")
            ]
        except ImportError:
            return []


# Create the fields proxy instance
fields = FieldsProxy()


# =============================================================================
# Field Type Reference (for documentation purposes)
# =============================================================================

FIELD_TYPES_REFERENCE = """
SQLORM Field Types Reference
============================

All Django field types are available. Here are the most commonly used ones:

Text Fields
-----------
- CharField(max_length=N)         : Fixed-length string (required max_length)
- TextField()                      : Unlimited length text
- SlugField(max_length=50)         : URL-friendly short label
- URLField(max_length=200)         : URL with validation
- EmailField(max_length=254)       : Email with validation
- UUIDField()                      : UUID field

Numeric Fields
--------------
- IntegerField()                   : Integer (-2147483648 to 2147483647)
- BigIntegerField()                : Large integer
- SmallIntegerField()              : Small integer (-32768 to 32767)
- PositiveIntegerField()           : Positive integer (0 to 2147483647)
- FloatField()                     : Floating point number
- DecimalField(max_digits, decimal_places) : Fixed precision decimal

Boolean Fields
--------------
- BooleanField(default=False)      : True/False value
- NullBooleanField()               : True/False/None (deprecated, use BooleanField(null=True))

Date/Time Fields
----------------
- DateField()                      : Date (year, month, day)
- TimeField()                      : Time (hour, minute, second)
- DateTimeField()                  : Date and time combined
- DurationField()                  : Time duration

Special options:
  - auto_now=True       : Update to current time on every save
  - auto_now_add=True   : Set to current time when created

File Fields
-----------
- FileField(upload_to='path/')     : File upload
- ImageField(upload_to='path/')    : Image upload (requires Pillow)
- FilePathField(path='/path/')     : System file path

Relationship Fields
-------------------
- ForeignKey(Model, on_delete=...)     : Many-to-one relationship
- OneToOneField(Model, on_delete=...)  : One-to-one relationship
- ManyToManyField(Model)               : Many-to-many relationship

on_delete options:
  - models.CASCADE    : Delete related objects
  - models.PROTECT    : Prevent deletion
  - models.SET_NULL   : Set to NULL
  - models.SET_DEFAULT: Set to default value
  - models.DO_NOTHING : Do nothing

Other Fields
------------
- AutoField()                      : Auto-incrementing integer (usually for pk)
- BigAutoField()                   : Auto-incrementing big integer
- BinaryField()                    : Raw binary data
- JSONField()                      : JSON data (PostgreSQL, MySQL 5.7.8+)
- GenericIPAddressField()          : IPv4 or IPv6 address

Common Field Options
--------------------
All fields support these options:

- null=True/False        : Allow NULL in database (default: False)
- blank=True/False       : Allow blank in forms (default: False)
- default=value          : Default value for the field
- unique=True/False      : Must be unique in the table
- db_index=True/False    : Create database index
- primary_key=True/False : Use as primary key
- verbose_name='Name'    : Human-readable name
- help_text='Help text'  : Extra help text
- editable=True/False    : Can be edited in admin
- choices=[(val, label)] : Limit choices to a list

Examples
--------
>>> from sqlorm import Model, fields
>>>
>>> class Product(Model):
...     # Text fields
...     name = fields.CharField(max_length=200)
...     description = fields.TextField(blank=True)
...     sku = fields.CharField(max_length=50, unique=True)
...
...     # Numeric fields
...     price = fields.DecimalField(max_digits=10, decimal_places=2)
...     quantity = fields.PositiveIntegerField(default=0)
...
...     # Boolean fields
...     is_available = fields.BooleanField(default=True)
...
...     # Date/time fields
...     created_at = fields.DateTimeField(auto_now_add=True)
...     updated_at = fields.DateTimeField(auto_now=True)
...
...     # Choices
...     STATUS_CHOICES = [
...         ('draft', 'Draft'),
...         ('published', 'Published'),
...         ('archived', 'Archived'),
...     ]
...     status = fields.CharField(
...         max_length=20,
...         choices=STATUS_CHOICES,
...         default='draft'
...     )

>>> class Order(Model):
...     # Foreign key relationship
...     product = fields.ForeignKey(
...         Product,
...         on_delete=fields.CASCADE,
...         related_name='orders'
...     )
...     quantity = fields.PositiveIntegerField()
...     total = fields.DecimalField(max_digits=12, decimal_places=2)
"""

# Make reference available
fields.__doc__ = FIELD_TYPES_REFERENCE
