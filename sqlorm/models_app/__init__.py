"""
SQLORM Models App
=================

This is a Django app that acts as a container for all user-defined models.
Models defined using sqlorm.Model are monkey-patched into this module,
making them appear as native Django models for migration purposes.

This eliminates the need for:
- manage.py
- settings.py
- Django project structure
- Django app structure

Usage:
    Models are automatically registered here when you define them:

    >>> from sqlorm import Model, fields
    >>>
    >>> class User(Model):
    ...     name = fields.CharField(max_length=100)

    The User model is now part of 'sqlorm.models_app' and can be migrated
    using: sqlorm makemigrations && sqlorm migrate
"""

# This will be populated by the Model metaclass
# All user models will be added here dynamically

default_app_config = "sqlorm.models_app.apps.SqlormModelsConfig"
