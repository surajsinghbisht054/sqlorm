"""
SQLORM Connection Module
========================

This module provides database connection utilities and raw SQL execution
capabilities, building on Django's database connection handling.

Features:
- Get and manage database connections
- Execute raw SQL queries
- Transaction management
- Multiple database support

Example:
    >>> from sqlorm import get_connection, execute_raw_sql
    >>>
    >>> # Execute raw SQL
    >>> results = execute_raw_sql("SELECT * FROM users WHERE age > %s", [18])
    >>>
    >>> # Get the raw database connection
    >>> conn = get_connection()
    >>> cursor = conn.cursor()
"""

import logging
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple, Union

from .exceptions import ConnectionError

logger = logging.getLogger("sqlorm.connection")


def get_connection(alias: str = "default"):
    """
    Get the Django database connection for the specified alias.

    This gives you access to the underlying database connection,
    which is useful for executing raw SQL or advanced operations.

    Args:
        alias: Database alias (default: "default")

    Returns:
        Django database connection wrapper

    Example:
        >>> conn = get_connection()
        >>> cursor = conn.cursor()
        >>> cursor.execute("SELECT COUNT(*) FROM users")
        >>> count = cursor.fetchone()[0]
    """
    try:
        from django.db import connections

        return connections[alias]
    except ImportError:
        raise ConnectionError(
            "Django is not installed. Install it with: pip install django"
        )
    except Exception as e:
        raise ConnectionError(f"Failed to get connection: {e}") from e


def close_connection(alias: str = "default") -> None:
    """
    Close the database connection for the specified alias.

    This is useful for cleaning up connections in long-running scripts
    or when you want to force a reconnection.

    Args:
        alias: Database alias (default: "default")

    Example:
        >>> close_connection()
    """
    try:
        from django.db import connections

        connections[alias].close()
        logger.debug(f"Closed connection: {alias}")
    except Exception as e:
        raise ConnectionError(f"Failed to close connection: {e}") from e


def close_all_connections() -> None:
    """
    Close all database connections.

    Example:
        >>> close_all_connections()
    """
    try:
        from django.db import connections

        connections.close_all()
        logger.debug("Closed all connections")
    except Exception as e:
        raise ConnectionError(f"Failed to close connections: {e}") from e


def execute_raw_sql(
    sql: str,
    params: Optional[Union[List, Tuple, Dict]] = None,
    alias: str = "default",
    fetch: bool = True,
) -> Optional[List[Tuple]]:
    """
    Execute a raw SQL query and return the results.

    This is useful for complex queries that are difficult to express
    using the ORM, or for performance-critical operations.

    Args:
        sql: SQL query string with placeholders
        params: Parameters for the query (list, tuple, or dict)
        alias: Database alias (default: "default")
        fetch: Whether to fetch and return results (default: True)

    Returns:
        List of tuples containing the query results, or None if fetch=False

    Example:
        >>> # Simple query
        >>> users = execute_raw_sql("SELECT * FROM users")
        >>>
        >>> # Parameterized query (positional)
        >>> adults = execute_raw_sql(
        ...     "SELECT * FROM users WHERE age >= %s",
        ...     [18]
        ... )
        >>>
        >>> # Parameterized query (named)
        >>> user = execute_raw_sql(
        ...     "SELECT * FROM users WHERE email = %(email)s",
        ...     {'email': 'john@example.com'}
        ... )
        >>>
        >>> # Insert/Update (no fetch)
        >>> execute_raw_sql(
        ...     "UPDATE users SET is_active = %s WHERE id = %s",
        ...     [True, 1],
        ...     fetch=False
        ... )

    Warning:
        Always use parameterized queries to prevent SQL injection!
        Never concatenate user input directly into SQL strings.
    """
    try:
        from django.db import connections

        connection = connections[alias]

        with connection.cursor() as cursor:
            cursor.execute(sql, params or [])

            if fetch:
                return cursor.fetchall()
            return None

    except Exception as e:
        raise ConnectionError(f"Failed to execute SQL: {e}") from e


def execute_raw_sql_dict(
    sql: str, params: Optional[Union[List, Tuple, Dict]] = None, alias: str = "default"
) -> List[Dict[str, Any]]:
    """
    Execute a raw SQL query and return results as dictionaries.

    Each row is returned as a dictionary with column names as keys.

    Args:
        sql: SQL query string with placeholders
        params: Parameters for the query
        alias: Database alias (default: "default")

    Returns:
        List of dictionaries containing the query results

    Example:
        >>> users = execute_raw_sql_dict("SELECT id, name FROM users")
        >>> for user in users:
        ...     print(f"{user['id']}: {user['name']}")
    """
    try:
        from django.db import connections

        connection = connections[alias]

        with connection.cursor() as cursor:
            cursor.execute(sql, params or [])
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    except Exception as e:
        raise ConnectionError(f"Failed to execute SQL: {e}") from e


@contextmanager
def transaction(alias: str = "default", savepoint: bool = True):
    """
    Context manager for database transactions.

    All database operations within the context are wrapped in a
    transaction. If an exception occurs, the transaction is rolled
    back. Otherwise, it's committed.

    Args:
        alias: Database alias (default: "default")
        savepoint: Whether to use savepoints for nested transactions

    Example:
        >>> from sqlorm import transaction
        >>>
        >>> with transaction():
        ...     user = User.objects.create(name="John")
        ...     profile = Profile.objects.create(user=user)
        ...     # Both are committed together, or both are rolled back
        >>>
        >>> # Nested transactions with savepoints
        >>> with transaction():
        ...     User.objects.create(name="Alice")
        ...     try:
        ...         with transaction():
        ...             User.objects.create(name="Bob")
        ...             raise ValueError("Oops!")
        ...     except ValueError:
        ...         pass  # Bob is rolled back, Alice is still committed
    """
    try:
        from django.db import transaction as django_transaction

        with django_transaction.atomic(using=alias, savepoint=savepoint):
            yield

    except ImportError:
        raise ConnectionError(
            "Django is not installed. Install it with: pip install django"
        )


def get_database_info(alias: str = "default") -> Dict[str, Any]:
    """
    Get information about the database connection.

    Returns:
        Dictionary with database information including:
        - vendor: Database vendor (sqlite, postgresql, mysql, etc.)
        - version: Database version
        - name: Database name
        - alias: Connection alias

    Example:
        >>> info = get_database_info()
        >>> print(f"Using {info['vendor']} version {info['version']}")
    """
    try:
        from django.db import connections

        connection = connections[alias]

        return {
            "vendor": connection.vendor,
            "version": getattr(connection, "pg_version", None)
            or getattr(connection, "mysql_version", None)
            or getattr(connection, "sqlite_version", None),
            "name": connection.settings_dict.get("NAME"),
            "alias": alias,
            "engine": connection.settings_dict.get("ENGINE"),
        }

    except Exception as e:
        raise ConnectionError(f"Failed to get database info: {e}") from e


def get_table_names(alias: str = "default") -> List[str]:
    """
    Get a list of all table names in the database.

    Args:
        alias: Database alias (default: "default")

    Returns:
        List of table name strings

    Example:
        >>> tables = get_table_names()
        >>> print(f"Found {len(tables)} tables")
    """
    try:
        from django.db import connections

        connection = connections[alias]
        return connection.introspection.table_names()

    except Exception as e:
        raise ConnectionError(f"Failed to get table names: {e}") from e


def get_table_description(table_name: str, alias: str = "default") -> List[Dict]:
    """
    Get column information for a table.

    Args:
        table_name: Name of the table
        alias: Database alias (default: "default")

    Returns:
        List of dictionaries with column information

    Example:
        >>> columns = get_table_description("users")
        >>> for col in columns:
        ...     print(f"{col['name']}: {col['type']}")
    """
    try:
        from django.db import connections

        connection = connections[alias]

        with connection.cursor() as cursor:
            description = connection.introspection.get_table_description(
                cursor, table_name
            )

            return [
                {
                    "name": col.name,
                    "type": col.type_code,
                    "nullable": col.null_ok,
                    "default": col.default,
                    "primary_key": col.pk if hasattr(col, "pk") else None,
                }
                for col in description
            ]

    except Exception as e:
        raise ConnectionError(
            f"Failed to get table description for {table_name}: {e}"
        ) from e
