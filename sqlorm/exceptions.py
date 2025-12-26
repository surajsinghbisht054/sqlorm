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
    ├── ConnectionError
    └── ValidationError

Example:
    >>> from sqlorm.exceptions import ConfigurationError
    >>>
    >>> try:
    ...     configure({})  # Missing required keys
    ... except ConfigurationError as e:
    ...     print(f"Configuration failed: {e}")
"""

from typing import Any, Dict, List, Optional


class SQLORMError(Exception):
    """
    Base exception for all SQLORM errors.

    All SQLORM-specific exceptions inherit from this class,
    allowing you to catch all SQLORM errors with a single except clause.

    Attributes:
        message: Human-readable error message
        details: Additional context dictionary
        hint: Suggested fix or action

    Example:
        >>> try:
        ...     # SQLORM operations
        ... except SQLORMError as e:
        ...     print(f"SQLORM error: {e}")
        ...     if e.hint:
        ...         print(f"Hint: {e.hint}")
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        hint: Optional[str] = None,
    ):
        self.message = message
        self.details = details or {}
        self.hint = hint
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format the full error message."""
        msg = self.message
        if self.hint:
            msg += f"\n  Hint: {self.hint}"
        return msg

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
            "hint": self.hint,
        }


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

    def __init__(
        self,
        message: str,
        missing_keys: Optional[List[str]] = None,
        invalid_keys: Optional[Dict[str, str]] = None,
        hint: Optional[str] = None,
    ):
        details = {}
        if missing_keys:
            details["missing_keys"] = missing_keys
        if invalid_keys:
            details["invalid_keys"] = invalid_keys
        super().__init__(message, details=details, hint=hint)


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

    def __init__(
        self,
        message: str,
        model_name: Optional[str] = None,
        field_name: Optional[str] = None,
        hint: Optional[str] = None,
    ):
        details = {}
        if model_name:
            details["model"] = model_name
        if field_name:
            details["field"] = field_name
        super().__init__(message, details=details, hint=hint)


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

    def __init__(
        self,
        message: str,
        table_name: Optional[str] = None,
        operation: Optional[str] = None,
        hint: Optional[str] = None,
    ):
        details = {}
        if table_name:
            details["table"] = table_name
        if operation:
            details["operation"] = operation
        super().__init__(message, details=details, hint=hint)


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

    def __init__(
        self,
        message: str,
        database_alias: Optional[str] = None,
        sql: Optional[str] = None,
        hint: Optional[str] = None,
    ):
        details = {}
        if database_alias:
            details["database"] = database_alias
        if sql:
            # Truncate long SQL for readability
            details["sql"] = sql[:200] + "..." if len(sql) > 200 else sql
        super().__init__(message, details=details, hint=hint)


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

    def __init__(
        self,
        message: str,
        field_errors: Optional[Dict[str, List[str]]] = None,
        hint: Optional[str] = None,
    ):
        details = {}
        if field_errors:
            details["field_errors"] = field_errors
        super().__init__(message, details=details, hint=hint)


class QueryError(SQLORMError):
    """
    Exception raised when a database query fails.

    This is raised when:
    - Query syntax is invalid
    - Query references non-existent fields
    - Query constraints are violated

    Example:
        >>> try:
        ...     User.objects.filter(invalid_field=True)
        ... except QueryError as e:
        ...     print(f"Query error: {e}")
    """

    def __init__(
        self,
        message: str,
        query: Optional[str] = None,
        model_name: Optional[str] = None,
        hint: Optional[str] = None,
    ):
        details = {}
        if query:
            details["query"] = query[:500] + "..." if len(query) > 500 else query
        if model_name:
            details["model"] = model_name
        super().__init__(message, details=details, hint=hint)
