"""
SQLORM Models Container
=======================

This module serves as the container for all user-defined models.
Models are dynamically added to this module by the Model metaclass.

DO NOT define models directly in this file.
Instead, define them in your own Python scripts using sqlorm.Model.
"""

# Models will be added here dynamically by the Model metaclass
# Example: After defining class User(Model), you can access it as:
# from sqlorm.models_app.models import User

# The _registry dictionary keeps track of all registered models
_registry = {}


def get_all_models():
    """
    Get all registered models.

    Returns:
        dict: Dictionary mapping model names to model classes
    """
    return _registry.copy()


def register_model(name, model_class):
    """
    Register a model in this module.

    Args:
        name: The model class name
        model_class: The Django model class
    """
    _registry[name] = model_class
    # Make the model accessible as an attribute of this module
    globals()[name] = model_class


def unregister_model(name):
    """
    Unregister a model from this module.

    Args:
        name: The model class name
    """
    if name in _registry:
        del _registry[name]
    if name in globals():
        del globals()[name]


def clear_registry():
    """Clear all registered models."""
    global _registry
    for name in list(_registry.keys()):
        if name in globals():
            del globals()[name]
    _registry = {}
