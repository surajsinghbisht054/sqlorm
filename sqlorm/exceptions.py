"""
SQLORM Exceptions Module
========================

This module defines custom exceptions for SQLORM, providing clear
error messages and proper exception hierarchy.

Exception Hierarchy:
    SQLORMError (base)
    ├── ConfigurationError
    ├── ModelError
    ├── MigrationError
    └── ConnectionError

Example:
    >>> from sqlorm.exceptions import ConfigurationError
    >>> 
    >>> try:
    ...     configure({})  # Missing required keys
    ... except ConfigurationError as e:
    ...     print(f"Configuration failed: {e}")
"""


class SQLORMError(Exception):
    """
    Base exception for all SQLORM errors.
    
    All SQLORM-specific exceptions inherit from this class,
    allowing you to catch all SQLORM errors with a single except clause.
    
    Example:
        >>> try:
        ...     # SQLORM operations
        ... except SQLORMError as e:
        ...     print(f"SQLORM error: {e}")
    """
    pass


class ConfigurationError(SQLORMError):
    """
    Exception raised when there's a configuration problem.
    
    This is raised when:
    - Required configuration keys are missing
    - Configuration values are invalid
    - Django cannot be initialized
    - Configuration file cannot be loaded
    
    Example:
        >>> try:
        ...     configure({'NAME': 'db.sqlite3'})  # Missing ENGINE
        ... except ConfigurationError as e:
        ...     print(f"Config error: {e}")
    """
    pass


class ModelError(SQLORMError):
    """
    Exception raised when there's a model-related problem.
    
    This is raised when:
    - Model definition is invalid
    - Model operations fail
    - Table operations fail
    - Field definitions are incorrect
    
    Example:
        >>> try:
        ...     User.drop_table()  # Without confirm=True
        ... except ModelError as e:
        ...     print(f"Model error: {e}")
    """
    pass


class MigrationError(SQLORMError):
    """
    Exception raised when there's a migration problem.
    
    This is raised when:
    - Table creation fails
    - Schema changes fail
    - Database constraints are violated during migration
    
    Example:
        >>> try:
        ...     User.migrate()
        ... except MigrationError as e:
        ...     print(f"Migration error: {e}")
    """
    pass


class ConnectionError(SQLORMError):
    """
    Exception raised when there's a database connection problem.
    
    This is raised when:
    - Cannot connect to database
    - Connection is lost
    - Raw SQL execution fails
    - Database is unavailable
    
    Example:
        >>> try:
        ...     conn = get_connection()
        ... except ConnectionError as e:
        ...     print(f"Connection error: {e}")
    """
    pass


class ValidationError(SQLORMError):
    """
    Exception raised when data validation fails.
    
    This wraps Django's ValidationError for convenience.
    
    Example:
        >>> try:
        ...     user = User(email="invalid-email")
        ...     user.full_clean()
        ... except ValidationError as e:
        ...     print(f"Validation error: {e}")
    """
    pass
