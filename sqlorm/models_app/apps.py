"""
Django App Configuration for SQLORM Models
"""

from django.apps import AppConfig


class SqlormModelsConfig(AppConfig):
    """
    Django app configuration for the sqlorm models container.

    This app holds all user-defined models that inherit from sqlorm.Model.
    """

    name = "sqlorm.models_app"
    label = "sqlorm_models"
    verbose_name = "SQLORM Models"

    def ready(self):
        """Called when the app is ready."""
        # Models are registered dynamically via the Model metaclass
        pass
