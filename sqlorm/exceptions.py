"""SQLORM Exceptions."""


class SQLORMError(Exception):
    """Base exception for SQLORM errors."""

    pass


class ConfigurationError(SQLORMError):
    """Configuration error."""

    pass


class ModelError(SQLORMError):
    """Model definition error."""

    pass


class MigrationError(SQLORMError):
    """Migration error."""

    pass
