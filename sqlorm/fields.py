"""
SQLORM Fields
=============

Proxy to Django model fields for lazy loading.

Example:
    >>> from sqlorm import fields
    >>> name = fields.CharField(max_length=100)
    >>> email = fields.EmailField(unique=True)
"""


class FieldsProxy:
    """Lazy proxy to Django model fields."""

    _module = None

    def __getattr__(self, name):
        if self._module is None:
            from django.db import models

            self._module = models

        if hasattr(self._module, name):
            return getattr(self._module, name)

        raise AttributeError(f"Unknown field: {name}")


fields = FieldsProxy()
