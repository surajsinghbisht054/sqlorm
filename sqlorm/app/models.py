"""
SQLORM Models Registry
======================

User-defined models are dynamically registered here by the Model metaclass.
"""

_registry = {}


def register_model(name, model_class):
    """Register a model."""
    _registry[name] = model_class
    globals()[name] = model_class


def get_all_models():
    """Get all registered models."""
    return _registry.copy()


def clear():
    """Clear registry."""
    global _registry
    for name in list(_registry.keys()):
        if name in globals():
            del globals()[name]
    _registry = {}
