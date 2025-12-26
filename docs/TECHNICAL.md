# SQLORM Technical Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [How It Works](#how-it-works)
4. [Core Components](#core-components)
5. [Configuration Deep Dive](#configuration-deep-dive)
6. [Model System](#model-system)
7. [Query Execution](#query-execution)
8. [Transaction Handling](#transaction-handling)
9. [Migration System](#migration-system)
10. [Extending SQLORM](#extending-sqlorm)

---

## Overview

SQLORM is a lightweight wrapper that brings Django's powerful ORM capabilities to standalone Python scripts without requiring a full Django project setup. It solves the common problem of wanting to use Django's mature, battle-tested ORM without the overhead of Django's project structure.

### The Problem

Django's ORM is one of the most powerful and feature-rich ORMs available for Python:

- Automatic table creation and migrations
- Complex query building with Q and F expressions
- Aggregations, annotations, and subqueries
- Built-in support for multiple database backends
- Connection pooling and optimization

However, using it traditionally requires:

```
myproject/
├── manage.py
├── myproject/
│   ├── __init__.py
│   ├── settings.py      # Required Django settings
│   ├── urls.py          # Not needed for ORM-only usage
│   └── wsgi.py          # Not needed for ORM-only usage
└── myapp/
    ├── __init__.py
    ├── models.py        # Your actual models
    ├── views.py         # Not needed for ORM-only usage
    └── migrations/      # Required for migrations
```

### The Solution

SQLORM reduces this to:

```python
from sqlorm import configure, Model, fields

configure({'ENGINE': 'django.db.backends.sqlite3', 'NAME': 'db.sqlite3'})

class MyModel(Model):
    name = fields.CharField(max_length=100)

MyModel.migrate()
```

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Your Application                         │
├─────────────────────────────────────────────────────────────────┤
│                           SQLORM API                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │ configure│  │  Model   │  │  fields  │  │ Q, F, Aggregates │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘ │
├───────┼─────────────┼─────────────┼──────────────────┼──────────┤
│       ▼             ▼             ▼                  ▼          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Django ORM Layer                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │   │
│  │  │   Models    │  │  QuerySet   │  │   Migrations    │   │   │
│  │  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘   │   │
│  └─────────┼────────────────┼──────────────────┼────────────┘   │
├────────────┼────────────────┼──────────────────┼────────────────┤
│            ▼                ▼                  ▼                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                 Database Backend Layer                    │   │
│  │   SQLite  │  PostgreSQL  │   MySQL   │   Oracle          │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Module Structure

```
sqlorm/
├── __init__.py      # Public API exports
├── base.py          # Model base class and metaclass
├── config.py        # Configuration management
├── connection.py    # Database connection utilities
├── exceptions.py    # Custom exceptions
└── fields.py        # Field proxy to Django fields
```

---

## How It Works

### Step 1: Django Initialization Without Django Project

When you call `configure()`, SQLORM performs a carefully orchestrated initialization:

```python
def configure(databases: dict = None, alias: str = 'default', ...):
    # 1. Set required Django environment variable
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sqlorm_settings')
    
    # 2. Configure Django settings programmatically
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DATABASES={...},
            INSTALLED_APPS=['django.contrib.contenttypes'],
            DEFAULT_AUTO_FIELD='django.db.models.BigAutoField',
            USE_TZ=True,
        )
    
    # 3. Initialize Django
    import django
    django.setup()
```

**Key Insight**: Django's settings can be configured programmatically using `settings.configure()` instead of requiring a `settings.py` file. SQLORM leverages this to inject database configuration at runtime.

### Step 2: Model Registration

SQLORM uses a custom metaclass to intercept model creation:

```python
class ModelMeta(type):
    """Metaclass that registers models dynamically."""
    _models = {}
    
    def __new__(mcs, name, bases, namespace, **kwargs):
        # Skip the base Model class itself
        if name == 'Model':
            return super().__new__(mcs, name, bases, namespace)
        
        # Dynamically create an app_label for this model
        # This is required by Django's model system
        if 'Meta' not in namespace:
            namespace['Meta'] = type('Meta', (), {'app_label': 'sqlorm'})
        
        # Create the class inheriting from Django's Model
        from django.db import models
        new_bases = tuple(
            models.Model if b.__name__ == 'Model' else b 
            for b in bases
        )
        
        cls = super().__new__(mcs, name, new_bases, namespace)
        mcs._models[name] = cls
        return cls
```

**Key Insight**: Django models require an `app_label` to function. SQLORM automatically assigns `app_label = 'sqlorm'` to all models, making them part of a virtual "sqlorm" application.

### Step 3: Objects Manager Access

Accessing `Model.objects` returns Django's QuerySet manager. SQLORM uses a descriptor to make this work seamlessly:

```python
class ObjectsDescriptor:
    """Descriptor that provides access to Django's objects manager."""
    
    def __get__(self, obj, objtype=None):
        if objtype is None:
            return None
        
        # Return Django's default manager
        from django.db import models
        for base in objtype.__mro__:
            if hasattr(base, '_default_manager'):
                return base._default_manager
        return None
```

**Why a Descriptor?** 

Python's `@property` decorator doesn't work with `@classmethod`. Using a descriptor allows us to intercept attribute access at the class level and return the correct manager.

---

## Core Components

### 1. Configuration Module (`config.py`)

The configuration module handles:

- Database configuration parsing
- Environment variable loading
- Configuration file support (JSON, YAML)
- DATABASE_URL parsing (Heroku, Docker compatibility)

```python
# Multiple configuration sources
configure({'ENGINE': '...', 'NAME': '...'})           # Direct dict
configure_from_file('database.json')                   # JSON file
configure_from_env('DATABASE_URL')                     # Environment variable
```

**DATABASE_URL Parsing:**

```python
def _parse_database_url(url: str) -> dict:
    """
    Parses URLs like:
    - sqlite:///path/to/db.sqlite3
    - postgres://user:pass@host:5432/dbname
    - mysql://user:pass@host:3306/dbname
    """
    parsed = urlparse(url)
    
    ENGINE_MAP = {
        'postgres': 'django.db.backends.postgresql',
        'postgresql': 'django.db.backends.postgresql',
        'mysql': 'django.db.backends.mysql',
        'sqlite': 'django.db.backends.sqlite3',
        'oracle': 'django.db.backends.oracle',
    }
    
    return {
        'ENGINE': ENGINE_MAP.get(parsed.scheme),
        'NAME': parsed.path.lstrip('/'),
        'USER': parsed.username,
        'PASSWORD': parsed.password,
        'HOST': parsed.hostname,
        'PORT': str(parsed.port) if parsed.port else '',
    }
```

### 2. Base Model (`base.py`)

The base model provides:

- Integration with Django's model system
- Automatic migration support
- Table introspection utilities

```python
class Model(metaclass=ModelMeta):
    """
    Base class for all SQLORM models.
    
    Inherits from Django's Model through metaclass transformation.
    """
    objects = ObjectsDescriptor()
    
    class Meta:
        abstract = True
        app_label = 'sqlorm'
    
    @classmethod
    def migrate(cls):
        """
        Create or update the database table for this model.
        Uses Django's schema editor for DDL operations.
        """
        from django.db import connection
        from django.db.backends.base.schema import BaseDatabaseSchemaEditor
        
        with connection.schema_editor() as schema_editor:
            try:
                schema_editor.create_model(cls)
            except Exception:
                # Table may already exist, try to sync
                pass
```

### 3. Fields Module (`fields.py`)

Fields are proxied from Django to avoid initialization order issues:

```python
class FieldsProxy:
    """
    Lazy proxy to Django model fields.
    
    We can't import Django fields at module load time because
    Django might not be configured yet. This proxy defers the
    import until first access.
    """
    
    def __getattr__(self, name: str):
        # Ensure Django is configured
        self._ensure_configured()
        
        # Import and return the requested field class
        from django.db import models
        return getattr(models, name)
    
    def _ensure_configured(self):
        from django.conf import settings
        if not settings.configured:
            raise ConfigurationError(
                "Call configure() before accessing fields"
            )

# Singleton instance
fields = FieldsProxy()
```

**Supported Field Types:**

| Field Type | Django Equivalent | Notes |
|------------|-------------------|-------|
| `CharField` | `models.CharField` | Requires `max_length` |
| `TextField` | `models.TextField` | Unlimited text |
| `IntegerField` | `models.IntegerField` | Standard integer |
| `BigIntegerField` | `models.BigIntegerField` | 64-bit integer |
| `FloatField` | `models.FloatField` | Floating point |
| `DecimalField` | `models.DecimalField` | Precise decimals |
| `BooleanField` | `models.BooleanField` | True/False |
| `DateField` | `models.DateField` | Date only |
| `DateTimeField` | `models.DateTimeField` | Date and time |
| `EmailField` | `models.EmailField` | Email validation |
| `URLField` | `models.URLField` | URL validation |
| `ForeignKey` | `models.ForeignKey` | Relationships |

### 4. Connection Module (`connection.py`)

Provides low-level database access:

```python
def get_connection(alias: str = 'default'):
    """Get the database connection for an alias."""
    from django.db import connections
    return connections[alias]

def execute_raw_sql(sql: str, params=None, using='default') -> list:
    """
    Execute raw SQL and return results.
    
    Args:
        sql: SQL query with %s placeholders
        params: Parameters to substitute
        using: Database alias
    
    Returns:
        List of tuples (rows)
    """
    from django.db import connections
    with connections[using].cursor() as cursor:
        cursor.execute(sql, params)
        if cursor.description:  # SELECT query
            return cursor.fetchall()
        return []
```

**Transaction Context Manager:**

```python
@contextmanager
def transaction(using: str = 'default'):
    """
    Context manager for database transactions.
    
    Usage:
        with transaction():
            Model.objects.create(...)
            Model.objects.update(...)
        # Commits on success, rolls back on exception
    """
    from django.db import connections
    connection = connections[using]
    
    # Start transaction
    connection.ensure_connection()
    connection.set_autocommit(False)
    
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.set_autocommit(True)
```

---

## Configuration Deep Dive

### Minimal Configuration

```python
from sqlorm import configure

configure({
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': 'database.sqlite3',
})
```

### Full Configuration Options

```python
configure(
    databases={
        # Core settings
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'my_database',
        'USER': 'db_user',
        'PASSWORD': 'db_password',
        'HOST': 'localhost',
        'PORT': '5432',
        
        # Connection options
        'CONN_MAX_AGE': 600,              # Connection pooling (seconds)
        'CONN_HEALTH_CHECKS': True,       # Health checks for pooled connections
        
        # SSL options (PostgreSQL)
        'OPTIONS': {
            'sslmode': 'require',
            'connect_timeout': 10,
        },
    },
    alias='default',        # Database alias
    debug=False,            # SQL logging
    time_zone='UTC',        # Timezone for datetime fields
)
```

### Engine Strings

| Database | Engine String |
|----------|---------------|
| SQLite | `django.db.backends.sqlite3` |
| PostgreSQL | `django.db.backends.postgresql` |
| MySQL | `django.db.backends.mysql` |
| Oracle | `django.db.backends.oracle` |

---

## Model System

### Field Definition

```python
class Product(Model):
    # Primary key (auto-created if not specified)
    id = fields.BigAutoField(primary_key=True)
    
    # Required field
    name = fields.CharField(max_length=200)
    
    # Optional field
    description = fields.TextField(null=True, blank=True)
    
    # Field with default
    price = fields.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Auto timestamps
    created_at = fields.DateTimeField(auto_now_add=True)
    updated_at = fields.DateTimeField(auto_now=True)
    
    # Choices
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]
    status = fields.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
```

### Relationships

```python
class Category(Model):
    name = fields.CharField(max_length=100)

class Product(Model):
    name = fields.CharField(max_length=200)
    
    # Foreign key relationship
    category = fields.ForeignKey(
        Category,
        on_delete=fields.CASCADE,    # Delete products when category deleted
        related_name='products',      # category.products.all()
        null=True,
    )
```

### Model Methods

```python
class Product(Model):
    name = fields.CharField(max_length=200)
    price = fields.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = fields.DecimalField(max_digits=4, decimal_places=2, default=0.1)
    
    @property
    def price_with_tax(self):
        """Computed property."""
        return self.price * (1 + self.tax_rate)
    
    def apply_discount(self, percentage):
        """Instance method."""
        self.price = self.price * (1 - percentage / 100)
        self.save()
    
    @classmethod
    def get_expensive_products(cls, min_price):
        """Class method for common queries."""
        return cls.objects.filter(price__gte=min_price)
    
    def __str__(self):
        return f"{self.name} (${self.price})"
```

---

## Query Execution

### QuerySet Methods

SQLORM provides full access to Django's QuerySet API:

```python
# Basic retrieval
Product.objects.all()                    # All products
Product.objects.get(id=1)                # Single product (raises if not found)
Product.objects.filter(price__gt=100)    # Filtered products
Product.objects.exclude(status='draft')  # Exclusion

# Chaining
Product.objects.filter(
    category__name='Electronics'
).exclude(
    price__lt=50
).order_by('-created_at')

# Aggregation
from sqlorm import Sum, Avg, Count

Product.objects.aggregate(
    total=Sum('price'),
    average=Avg('price'),
    count=Count('id'),
)

# Annotation
Product.objects.annotate(
    order_count=Count('orders'),
).filter(
    order_count__gt=10
)

# Values (dictionary output)
Product.objects.values('name', 'price')
Product.objects.values_list('name', flat=True)
```

### Complex Queries with Q and F

```python
from sqlorm import Q, F

# OR conditions
Product.objects.filter(
    Q(price__lt=100) | Q(status='sale')
)

# NOT conditions
Product.objects.filter(
    ~Q(status='draft')
)

# Combined conditions
Product.objects.filter(
    (Q(price__lt=100) | Q(status='sale')) & Q(in_stock=True)
)

# Field references (compare fields to each other)
Product.objects.filter(
    sale_price__lt=F('regular_price')
)

# Field arithmetic
Product.objects.update(
    price=F('price') * 1.1  # 10% price increase
)
```

### Lookups Reference

| Lookup | Example | SQL Equivalent |
|--------|---------|----------------|
| `exact` | `name__exact='Test'` | `name = 'Test'` |
| `iexact` | `name__iexact='test'` | `LOWER(name) = 'test'` |
| `contains` | `name__contains='est'` | `name LIKE '%est%'` |
| `icontains` | `name__icontains='est'` | `name ILIKE '%est%'` |
| `in` | `id__in=[1,2,3]` | `id IN (1, 2, 3)` |
| `gt` | `price__gt=100` | `price > 100` |
| `gte` | `price__gte=100` | `price >= 100` |
| `lt` | `price__lt=100` | `price < 100` |
| `lte` | `price__lte=100` | `price <= 100` |
| `range` | `price__range=(10,100)` | `price BETWEEN 10 AND 100` |
| `isnull` | `category__isnull=True` | `category IS NULL` |
| `startswith` | `name__startswith='Pro'` | `name LIKE 'Pro%'` |
| `endswith` | `name__endswith='duct'` | `name LIKE '%duct'` |
| `year` | `created__year=2024` | `EXTRACT(year FROM created) = 2024` |
| `month` | `created__month=12` | `EXTRACT(month FROM created) = 12` |

---

## Transaction Handling

### Automatic Transactions

By default, Django wraps each `save()` and `delete()` in its own transaction:

```python
product = Product.objects.create(name="Widget")  # Committed immediately
product.price = 99.99
product.save()  # Committed immediately
```

### Manual Transactions

For atomic operations across multiple statements:

```python
from sqlorm import transaction

# Context manager approach
with transaction():
    product = Product.objects.create(name="Widget")
    inventory = Inventory.objects.create(product=product, quantity=100)
    # Both committed together, or neither

# With exception handling
try:
    with transaction():
        Product.objects.create(name="Widget")
        raise ValueError("Something went wrong")  # Triggers rollback
except ValueError:
    pass  # Transaction was rolled back
```

### Savepoints

For nested transaction control:

```python
from django.db import transaction as django_transaction

with django_transaction.atomic():
    Product.objects.create(name="Product 1")
    
    sid = django_transaction.savepoint()
    try:
        Product.objects.create(name="Product 2")
        raise Exception("Rollback to savepoint")
    except Exception:
        django_transaction.savepoint_rollback(sid)
    
    # Product 1 is still created, Product 2 is rolled back
```

---

## Migration System

### Overview

SQLORM provides a comprehensive migration system that handles:
- ✅ Initial table creation
- ✅ Adding new columns to existing tables
- ✅ Renaming columns
- ✅ Changing column types
- ✅ Schema introspection and diff detection
- ✅ Table backup and restoration
- ✅ Data-preserving table recreation

Unlike Django's full migration system (which tracks migration history in files), SQLORM uses a simpler approach designed for standalone scripts and rapid development.

### How Migrations Work

#### Initial Table Creation

```python
class Product(Model):
    name = fields.CharField(max_length=200)
    price = fields.DecimalField(max_digits=10, decimal_places=2)

# Create or update table
Product.migrate()
```

**Under the Hood:**

1. SQLORM uses Django's `schema_editor` to generate DDL
2. For SQLite: Creates table with all columns
3. For PostgreSQL/MySQL: Creates table with proper column types
4. If table already exists, the operation is safely skipped

#### Checking Table Status

```python
# Check if table exists
if not Product.table_exists():
    Product.migrate()

# Get table name
table_name = Product.get_table_name()

# Get all field names
fields = Product.get_fields()
```

### Schema Changes: Adding Columns

When you add new fields to an existing model, use the migration utilities:

```python
from sqlorm import safe_add_column, add_column

# Safe add (won't fail if column exists)
safe_add_column(
    table_name='product',
    column_name='discount',
    column_type='DECIMAL(5,2)',
    default='0.00'
)

# Add nullable column
add_column(
    table_name='user',
    column_name='phone',
    column_type='VARCHAR(20)',
    nullable=True
)

# Add column with NOT NULL and default
add_column(
    table_name='order',
    column_name='status',
    column_type='VARCHAR(20)',
    default="'pending'",
    nullable=False
)
```

### Schema Changes: Renaming Columns

```python
from sqlorm import rename_column

# Rename a column
rename_column(
    table_name='user',
    old_column_name='username',
    new_column_name='user_name'
)
```

**Note:** For SQLite versions before 3.25.0, SQLORM automatically handles renaming via table recreation to preserve data.

### Schema Changes: Changing Column Types

```python
from sqlorm import change_column_type

# Change column type
change_column_type(
    table_name='product',
    column_name='price',
    new_type='DECIMAL(12,4)'  # More precision
)

# Convert varchar to integer
change_column_type(
    table_name='settings',
    column_name='value',
    new_type='INTEGER'
)
```

**Warning:** Type changes may cause data loss if the conversion is incompatible. Always backup important data first.

### Schema Introspection

SQLORM provides utilities to inspect and compare schemas:

```python
from sqlorm import get_table_columns, column_exists, get_schema_diff

# Get all columns in a table
columns = get_table_columns('product')
# ['id', 'name', 'price', 'created_at']

# Check if column exists
if not column_exists('product', 'discount'):
    add_column('product', 'discount', 'DECIMAL(5,2)')

# Compare model with database
class Product(Model):
    name = fields.CharField(max_length=200)
    price = fields.DecimalField(max_digits=10, decimal_places=2)
    discount = fields.DecimalField(max_digits=5, decimal_places=2)  # New!

diff = get_schema_diff(Product)
# {
#     'missing_in_db': ['discount'],
#     'extra_in_db': [],
#     'model_columns': ['id', 'name', 'price', 'discount'],
#     'db_columns': ['id', 'name', 'price']
# }
```

### Automatic Schema Sync

```python
from sqlorm import sync_schema

# Automatically add missing columns
result = sync_schema(Product)
print(f"Added columns: {result['added']}")
print(f"Skipped columns: {result['skipped']}")
```

### Table Recreation (Complex Changes)

For changes that can't be done with ALTER TABLE (especially in SQLite):

```python
from sqlorm import recreate_table

new_schema = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name VARCHAR(200),
    email VARCHAR(254) UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
"""

# Recreate table preserving specific columns
recreate_table(
    table_name='users',
    new_schema=new_schema,
    columns_to_copy=['id', 'email']  # Copy only these columns
)
```

### Backup and Restore

Always backup before risky operations:

```python
from sqlorm import backup_table, restore_table

# Create backup
backup_table('users')  # Creates 'users_backup'

# ... make changes ...

# If something goes wrong, restore
restore_table('users')  # Restores from 'users_backup'
```

### Migration Workflow: Best Practices

#### 1. Development Workflow

```python
from sqlorm import configure, Model, fields, sync_schema

configure({...})

class User(Model):
    name = fields.CharField(max_length=100)
    email = fields.EmailField(unique=True)

# Initial migration
User.migrate()

# Later, add new field to model
class User(Model):
    name = fields.CharField(max_length=100)
    email = fields.EmailField(unique=True)
    verified = fields.BooleanField(default=False)  # NEW!

# Sync to add the new column
sync_schema(User)
```

#### 2. Production Workflow

```python
from sqlorm import (
    backup_table,
    safe_add_column,
    column_exists,
    execute_raw_sql
)

# Step 1: Backup
backup_table('users')

# Step 2: Add columns safely
safe_add_column('users', 'verified', 'BOOLEAN', default='0')
safe_add_column('users', 'verification_token', 'VARCHAR(64)', nullable=True)

# Step 3: Migrate existing data
execute_raw_sql(
    "UPDATE users SET verified = 1 WHERE email_confirmed = 1",
    fetch=False
)

# Step 4: Verify migration
result = execute_raw_sql("SELECT COUNT(*) FROM users WHERE verified = 1")
print(f"Migrated {result[0][0]} verified users")
```

#### 3. Handling Complex Changes

For changes like removing columns or changing NOT NULL constraints:

```python
from sqlorm import recreate_table, backup_table

# Step 1: Backup
backup_table('products')

# Step 2: Define new schema
new_schema = """
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    price DECIMAL(10,2) NOT NULL DEFAULT 0,
    category_id INTEGER,
    -- removed: old_field
    -- added: category_id
    FOREIGN KEY (category_id) REFERENCES categories(id)
)
"""

# Step 3: Recreate with data
recreate_table(
    table_name='products',
    new_schema=new_schema,
    columns_to_copy=['id', 'name', 'price']
)
```

### Migration Utilities Reference

| Function | Purpose |
|----------|---------|
| `migrate()` | Create table for a model |
| `table_exists()` | Check if table exists |
| `get_table_columns()` | List all columns in a table |
| `column_exists()` | Check if specific column exists |
| `add_column()` | Add new column to table |
| `safe_add_column()` | Add column only if it doesn't exist |
| `rename_column()` | Rename a column |
| `change_column_type()` | Change column's data type |
| `recreate_table()` | Recreate table with new schema |
| `backup_table()` | Create backup copy of table |
| `restore_table()` | Restore table from backup |
| `get_schema_diff()` | Compare model with database |
| `sync_schema()` | Add missing columns to database |

### Limitations

The simplified migration system:

- ⚠️ Does not track migration history (no migration files)
- ⚠️ Cannot automatically detect and apply column removals
- ⚠️ Renaming tables requires manual recreation
- ⚠️ Complex constraint changes may require raw SQL

**For Very Complex Migrations**, consider using raw SQL:

```python
from sqlorm import execute_raw_sql

# Manual schema changes
execute_raw_sql("ALTER TABLE product ADD COLUMN discount DECIMAL(5,2)", fetch=False)
execute_raw_sql("CREATE INDEX idx_product_name ON product(name)", fetch=False)
execute_raw_sql("ALTER TABLE product DROP COLUMN old_field", fetch=False)  # PostgreSQL
```

### Database-Specific Considerations

#### SQLite

- Limited ALTER TABLE support (no DROP COLUMN before 3.35, no MODIFY)
- Use `recreate_table()` for complex changes
- Column renames available in SQLite 3.25+

```python
# For old SQLite, SQLORM handles this automatically
rename_column('users', 'old_name', 'new_name')  # Works on all SQLite versions
```

#### PostgreSQL

- Full ALTER TABLE support
- Transactional DDL (schema changes can be rolled back)

```python
from sqlorm import transaction

with transaction():
    add_column('users', 'role', 'VARCHAR(50)')
    execute_raw_sql("UPDATE users SET role = 'member'", fetch=False)
    # Commits on success, rolls back on error
```

#### MySQL

- Most ALTER TABLE operations work
- Some changes may lock the table temporarily

```python
# MySQL-specific syntax for modifications
execute_raw_sql(
    "ALTER TABLE users MODIFY phone VARCHAR(30)",
    fetch=False
)
```

---

## Extending SQLORM

### Custom Model Base

```python
from sqlorm import Model, fields
from datetime import datetime

class TimestampedModel(Model):
    """Base model with automatic timestamps."""
    
    created_at = fields.DateTimeField(auto_now_add=True)
    updated_at = fields.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class AuditModel(TimestampedModel):
    """Base model with audit fields."""
    
    created_by = fields.CharField(max_length=100, null=True)
    updated_by = fields.CharField(max_length=100, null=True)
    
    class Meta:
        abstract = True
    
    def save(self, *args, user=None, **kwargs):
        if user:
            if not self.pk:
                self.created_by = user
            self.updated_by = user
        super().save(*args, **kwargs)

# Usage
class Product(AuditModel):
    name = fields.CharField(max_length=200)
```

### Custom Manager

```python
class PublishedManager:
    """Custom manager for published items."""
    
    def __init__(self, model_class):
        self.model = model_class
    
    def all(self):
        return self.model.objects.filter(status='published')
    
    def recent(self, days=7):
        from datetime import timedelta
        from django.utils import timezone
        cutoff = timezone.now() - timedelta(days=days)
        return self.all().filter(created_at__gte=cutoff)

class Article(Model):
    title = fields.CharField(max_length=200)
    status = fields.CharField(max_length=20, default='draft')
    created_at = fields.DateTimeField(auto_now_add=True)
    
    # Custom manager (use as class attribute after definition)
    @classmethod
    def published(cls):
        return cls.objects.filter(status='published')
```

### Custom Field Validators

```python
from django.core.exceptions import ValidationError

def validate_positive(value):
    if value < 0:
        raise ValidationError(f'{value} is not a positive number')

class Product(Model):
    name = fields.CharField(max_length=200)
    price = fields.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[validate_positive]
    )
    
    def clean(self):
        """Model-level validation."""
        super().clean()
        if self.price and self.price > 10000:
            raise ValidationError({'price': 'Price cannot exceed $10,000'})
```

---

## Performance Considerations

### Connection Pooling

```python
configure({
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': 'mydb',
    'CONN_MAX_AGE': 600,  # Keep connections alive for 10 minutes
})
```

### Query Optimization

```python
# Use select_related for foreign keys (reduces queries)
Product.objects.select_related('category').all()

# Use prefetch_related for reverse relations
Category.objects.prefetch_related('products').all()

# Only fetch needed fields
Product.objects.only('name', 'price').all()
Product.objects.defer('description').all()  # Exclude large fields

# Use bulk operations
Product.objects.bulk_create([
    Product(name="Product 1"),
    Product(name="Product 2"),
])

Product.objects.filter(status='draft').update(status='published')

# Use iterator for large datasets
for product in Product.objects.iterator(chunk_size=1000):
    process(product)
```

### Indexing

```python
class Product(Model):
    name = fields.CharField(max_length=200, db_index=True)
    sku = fields.CharField(max_length=50, unique=True)  # Unique implies index
    
    class Meta:
        indexes = [
            models.Index(fields=['name', 'created_at']),
        ]
```

---

## Troubleshooting

### Common Issues

**1. "Django settings not configured"**
```python
# Solution: Call configure() before using models or fields
from sqlorm import configure
configure({'ENGINE': '...', 'NAME': '...'})
```

**2. "No such table"**
```python
# Solution: Call migrate() on the model
MyModel.migrate()
```

**3. "Database is locked" (SQLite)**
```python
# Solution: Use transactions properly and close connections
from sqlorm import transaction
with transaction():
    # Your operations
    pass
```

**4. Import errors with circular dependencies**
```python
# Solution: Import models after configure()
configure({...})

# Now import models
from myapp.models import User, Product
```

---

## Comparison with Alternatives

| Feature | SQLORM | SQLAlchemy | Peewee | Raw Django |
|---------|--------|------------|--------|------------|
| Setup Complexity | Low | Medium | Low | High |
| Learning Curve | Low (Django-like) | High | Medium | Low |
| Feature Richness | High | Very High | Medium | Very High |
| Django Compatibility | 100% | None | None | 100% |
| Standalone Usage | ✅ | ✅ | ✅ | ❌ |
| Async Support | Via Django 4.1+ | ✅ | Limited | Via Django 4.1+ |

---

## Contributing

SQLORM is open source and welcomes contributions. Key areas for contribution:

1. **Database Backend Support**: Testing and fixes for MySQL, Oracle
2. **Migration Improvements**: Schema diffing and migration history
3. **Documentation**: Examples, tutorials, and API documentation
4. **Performance**: Connection pooling optimizations
5. **Testing**: Additional test cases and CI improvements

See the project repository for contribution guidelines.

---

## License

SQLORM is released under the MIT License. This means you can use it freely in both open-source and commercial projects.

---

*This documentation covers SQLORM version 0.2.0. For the latest updates, check the project repository.*
