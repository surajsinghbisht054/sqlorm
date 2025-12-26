# CHANGELOG

All notable changes to SQLORM will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2024-12-26

### 🚀 New Features

#### Serialization Support
- **`to_dict()`**: Convert model instances to dictionaries with flexible field selection
- **`to_json()`**: Serialize model instances to JSON strings
- **`clone()`**: Create copies of model instances with optional overrides
- **`refresh()`**: Reload instance from database
- **`update()`**: Update multiple fields and save in one operation

#### Model Improvements
- **`get_field_info()`**: Get detailed information about all model fields
- **`count()`**: Class method to get record count
- **`exists()`**: Class method to check if records exist with optional filters
- **`truncate()`**: Fast deletion of all records in a table

#### Enhanced Exceptions
- All exceptions now support `details` dict and `hint` property
- New `to_dict()` method on exceptions for logging/serialization
- New `QueryError` exception type for query-related errors
- New `ValidationError` exception type for data validation

#### Developer Experience
- Added `py.typed` marker for PEP 561 compliance
- Python 3.13 support
- Pre-commit configuration for code quality
- Improved type hints throughout codebase
- Additional Django function re-exports (Coalesce, Concat, Now, etc.)

### Changed
- Version bumped to 2.1.0
- Enhanced `__init__.py` with more exports
- Improved docstrings throughout

## [2.0.0] - 2024-12-24

### 🚀 Complete Rewrite

This version is a complete rewrite of SQLORM to use Django's ORM under the hood instead of raw SQLite.

### Added

- **Django ORM Integration**: Now uses Django's mature, battle-tested ORM
- **Multiple Database Support**: SQLite, PostgreSQL, MySQL, and Oracle
- **Configuration Module**: Easy configuration with multiple options
  - Dictionary configuration
  - JSON/YAML file configuration
  - Environment variable configuration
  - DATABASE_URL support
- **Full Django Model Fields**: Access to all Django field types
- **QuerySet API**: Full Django QuerySet functionality
  - `filter()`, `exclude()`, `get()`, `create()`
  - `update()`, `delete()`, `count()`, `exists()`
  - `order_by()`, `distinct()`, `values()`, `values_list()`
  - `first()`, `last()`, `aggregate()`, `annotate()`
- **Q Objects**: Complex query building with `Q()` objects
- **F Expressions**: Database-level operations with `F()` expressions
- **Aggregations**: `Count`, `Sum`, `Avg`, `Max`, `Min`
- **Transactions**: Transaction context manager for atomic operations
- **Raw SQL**: Execute raw SQL queries when needed
- **Custom Exceptions**: Clear error hierarchy for better debugging
- **Comprehensive Tests**: pytest-based test suite
- **Examples**: Multiple example scripts for various use cases
- **Modern Packaging**: pyproject.toml and setup.py for PyPI distribution

### Changed

- **API Redesign**: New API aligned with Django ORM
- **Model Definition**: Now uses Django-style field definitions
- **Configuration**: New `configure()` function replaces class-based setup
- **Table Creation**: `Model.migrate()` replaces automatic table creation

### Deprecated

- Previous SQLite-only implementation (preserved as `sqlorm_legacy.py`)

### Removed

- Direct SQLite dependency (now uses Django's database abstraction)
- Custom Field class (replaced by Django fields)
- RowInterface and TableInterface (replaced by Django models)

## [1.0.0] - Previous Version

### Features (Legacy)

- SQLite-only database support
- Custom ORM implementation
- Model-based table definitions
- Basic CRUD operations
- Row and Table interfaces

---

## Migration Guide (1.x → 2.x)

### Before (1.x)

```python
from sqlorm import Model, Field

class MyDatabase(Model):
    class users:
        name = Field.String
        email = Field.String

db = MyDatabase()
db.connect()

table = db.Table("users")
table.insert(name="John", email="john@example.com")
```

### After (2.x)

```python
from sqlorm import configure, Model, fields

configure({
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': 'database.sqlite3',
})

class User(Model):
    name = fields.CharField(max_length=100)
    email = fields.EmailField(unique=True)

User.migrate()
User.objects.create(name="John", email="john@example.com")
```

The new API is cleaner, more powerful, and fully compatible with Django's ORM documentation.
