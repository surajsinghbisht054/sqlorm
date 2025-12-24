<p align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/python-3.8%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/Django-3.2%2B-green" alt="Django">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="License">
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen" alt="PRs Welcome">
</p>

<h1 align="center">🚀 SQLORM</h1>

<p align="center">
  <strong>Django's Powerful ORM — Now for Standalone Python Scripts!</strong>
</p>

<p align="center">
  Use Django's mature, battle-tested ORM in any Python script without the overhead of a full Django project.
</p>

```
   ________  ________  ___       ________  ________  _____ ______      
  |\   ____\|\   __  \|\  \     |\   __  \|\   __  \|\   _ \  _   \    
  \ \  \___|\ \  \|\  \ \  \    \ \  \|\  \ \  \|\  \ \  \\\__\ \  \   
   \ \_____  \ \  \\\  \ \  \    \ \  \\\  \ \   _  _\ \  \\|__| \  \  
    \|____|\  \ \  \\\  \ \  \____\ \  \\\  \ \  \\  \\ \  \    \ \  \ 
      ____\_\  \ \_____  \ \_______\ \_______\ \__\\ _\\ \__\    \ \__\
     |\_________\|___| \__\|_______|\|_______|\|__|\|__|\|__|     \|__|
     \|_________|     \|__|                                            
```

---

## 🤔 Why SQLORM?

**Django's ORM is amazing**, but it comes with a catch — you typically need a full Django project structure to use it. That means:

- ❌ Creating `manage.py`, `settings.py`, and app folders
- ❌ Running `django-admin startproject`
- ❌ Dealing with `INSTALLED_APPS` and migrations infrastructure

**SQLORM solves this problem!** It wraps Django's ORM with a minimal configuration layer, giving you:

- ✅ **Zero Django project structure required** — just import and go
- ✅ **All Django ORM features** — querysets, fields, Q objects, F expressions, aggregations
- ✅ **All database backends** — SQLite, PostgreSQL, MySQL, Oracle
- ✅ **Production-ready** — Django is battle-tested at scale (Instagram, Spotify, Mozilla)
- ✅ **Familiar API** — if you know Django, you already know SQLORM

---

## 📦 Installation

Install directly from GitHub:

```bash
# Basic installation
pip install git+https://github.com/surajsinghbisht054/sqlorm.git

# Or clone and install locally
git clone https://github.com/surajsinghbisht054/sqlorm.git
cd sqlorm
pip install -e .
```

### With Database Drivers

```bash
# Install with PostgreSQL support
pip install git+https://github.com/surajsinghbisht054/sqlorm.git
pip install psycopg2-binary

# Install with MySQL support
pip install git+https://github.com/surajsinghbisht054/sqlorm.git
pip install mysqlclient

# For development (with test dependencies)
git clone https://github.com/surajsinghbisht054/sqlorm.git
cd sqlorm
pip install -e ".[dev]"
```

### Requirements

- Python 3.8+
- Django 3.2+

---

## 🚀 Quick Start

Here's a complete working example in just a few lines:

```python
from sqlorm import configure, Model, fields

# 1. Configure the database (that's it - no settings.py needed!)
configure({
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': 'my_app.sqlite3',
})

# 2. Define your models (exactly like Django!)
class User(Model):
    name = fields.CharField(max_length=100)
    email = fields.EmailField(unique=True)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DateTimeField(auto_now_add=True)

# 3. Create the table
User.migrate()

# 4. Use Django ORM as usual! 🎉
user = User.objects.create(name="John", email="john@example.com")
users = User.objects.filter(is_active=True)
john = User.objects.get(email="john@example.com")
```

**That's it!** No `manage.py`, no `startproject`, no `INSTALLED_APPS`. Just Python.

---

## 📖 Documentation

### Table of Contents

1. [Configuration](#configuration)
2. [Defining Models](#defining-models)
3. [Field Types](#field-types)
4. [CRUD Operations](#crud-operations)
5. [Querying](#querying)
6. [Advanced Features](#advanced-features)
7. [Raw SQL](#raw-sql)
8. [Transactions](#transactions)
9. [Multiple Databases](#multiple-databases)

---

### Configuration

#### SQLite (Simplest)

```python
from sqlorm import configure

configure({
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': 'database.sqlite3',  # Or ':memory:' for in-memory DB
})
```

#### PostgreSQL

```python
configure({
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': 'mydatabase',
    'USER': 'myuser',
    'PASSWORD': 'mypassword',
    'HOST': 'localhost',
    'PORT': '5432',
})
```

#### MySQL

```python
configure({
    'ENGINE': 'django.db.backends.mysql',
    'NAME': 'mydatabase',
    'USER': 'myuser',
    'PASSWORD': 'mypassword',
    'HOST': 'localhost',
    'PORT': '3306',
})
```

#### From Environment Variables

```python
import os
from sqlorm.config import configure_from_env

# Using DATABASE_URL (Heroku-style)
os.environ['DATABASE_URL'] = 'postgres://user:pass@localhost:5432/mydb'
configure_from_env()

# Or using individual variables
os.environ['SQLORM_DB_ENGINE'] = 'django.db.backends.postgresql'
os.environ['SQLORM_DB_NAME'] = 'mydb'
os.environ['SQLORM_DB_USER'] = 'user'
os.environ['SQLORM_DB_PASSWORD'] = 'pass'
os.environ['SQLORM_DB_HOST'] = 'localhost'
configure_from_env()
```

#### From Configuration File

```python
from sqlorm import configure_from_file

# JSON file
configure_from_file('config.json')

# YAML file (requires pyyaml)
configure_from_file('config.yaml')
```

**config.json:**
```json
{
    "database": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "mydb.sqlite3"
    },
    "debug": true
}
```

---

### Defining Models

Models are defined exactly like Django models:

```python
from sqlorm import Model, fields

class Article(Model):
    # Text fields
    title = fields.CharField(max_length=200)
    slug = fields.SlugField(unique=True)
    content = fields.TextField()
    
    # Numeric fields
    view_count = fields.PositiveIntegerField(default=0)
    rating = fields.DecimalField(max_digits=3, decimal_places=2, null=True)
    
    # Boolean fields
    is_published = fields.BooleanField(default=False)
    
    # Date/time fields
    published_at = fields.DateTimeField(null=True, blank=True)
    created_at = fields.DateTimeField(auto_now_add=True)
    updated_at = fields.DateTimeField(auto_now=True)
    
    # Choices
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('published', 'Published'),
    ]
    status = fields.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Article'
        verbose_name_plural = 'Articles'

# Create the table
Article.migrate()
```

---

### Field Types

All Django field types are available:

| Field Type | Description | Example |
|------------|-------------|---------|
| `CharField` | Fixed-length string | `fields.CharField(max_length=100)` |
| `TextField` | Unlimited text | `fields.TextField()` |
| `IntegerField` | Integer | `fields.IntegerField(default=0)` |
| `FloatField` | Floating point | `fields.FloatField()` |
| `DecimalField` | Fixed precision | `fields.DecimalField(max_digits=10, decimal_places=2)` |
| `BooleanField` | True/False | `fields.BooleanField(default=False)` |
| `DateField` | Date | `fields.DateField()` |
| `DateTimeField` | Date and time | `fields.DateTimeField(auto_now_add=True)` |
| `EmailField` | Email with validation | `fields.EmailField(unique=True)` |
| `URLField` | URL with validation | `fields.URLField()` |
| `SlugField` | URL-friendly string | `fields.SlugField(unique=True)` |
| `UUIDField` | UUID | `fields.UUIDField(default=uuid.uuid4)` |
| `JSONField` | JSON data | `fields.JSONField(default=dict)` |

**Common field options:**
- `null=True` — Allow NULL in database
- `blank=True` — Allow empty in forms
- `default=value` — Default value
- `unique=True` — Must be unique
- `db_index=True` — Create database index
- `choices=[...]` — Limit to specific values

---

### CRUD Operations

#### Create

```python
# Method 1: create()
user = User.objects.create(
    name="John Doe",
    email="john@example.com"
)

# Method 2: Instantiate and save
user = User(name="Jane Doe", email="jane@example.com")
user.save()

# Method 3: get_or_create
user, created = User.objects.get_or_create(
    email="bob@example.com",
    defaults={'name': 'Bob Smith'}
)
```

#### Read

```python
# Get all records
users = User.objects.all()

# Get single record
user = User.objects.get(id=1)
user = User.objects.get(email="john@example.com")

# Get first/last
first = User.objects.first()
last = User.objects.last()

# Count
count = User.objects.count()
```

#### Update

```python
# Single object
user = User.objects.get(id=1)
user.name = "John Smith"
user.save()

# Bulk update
User.objects.filter(is_active=False).update(is_active=True)
```

#### Delete

```python
# Single object
user = User.objects.get(id=1)
user.delete()

# Bulk delete
User.objects.filter(is_active=False).delete()
```

---

### Querying

SQLORM supports the full Django QuerySet API:

```python
# Filtering
User.objects.filter(is_active=True)
User.objects.filter(age__gte=18)
User.objects.filter(name__startswith='J')
User.objects.filter(email__contains='@gmail')

# Excluding
User.objects.exclude(is_active=False)

# Chaining
User.objects.filter(is_active=True).exclude(age__lt=18).order_by('name')

# Ordering
User.objects.order_by('name')        # Ascending
User.objects.order_by('-created_at') # Descending

# Limiting
User.objects.all()[:10]              # First 10
User.objects.all()[10:20]            # 10-20

# Values
User.objects.values('name', 'email')
User.objects.values_list('name', flat=True)

# Distinct
User.objects.values('city').distinct()
```

#### Lookup Types

```python
# Exact match
User.objects.filter(name='John')
User.objects.filter(name__exact='John')

# Case-insensitive
User.objects.filter(name__iexact='john')

# Contains
User.objects.filter(name__contains='oh')
User.objects.filter(name__icontains='OH')

# Starts/ends with
User.objects.filter(name__startswith='J')
User.objects.filter(name__endswith='n')

# Range
User.objects.filter(age__range=(18, 65))

# In list
User.objects.filter(status__in=['active', 'pending'])

# Is null
User.objects.filter(deleted_at__isnull=True)

# Greater/less than
User.objects.filter(age__gt=18)
User.objects.filter(age__gte=18)
User.objects.filter(age__lt=65)
User.objects.filter(age__lte=65)
```

---

### Advanced Features

#### Q Objects (Complex Queries)

```python
from sqlorm import Q

# OR queries
User.objects.filter(Q(age__lt=18) | Q(age__gt=65))

# AND queries (explicit)
User.objects.filter(Q(is_active=True) & Q(is_verified=True))

# NOT queries
User.objects.filter(~Q(status='banned'))

# Complex combinations
User.objects.filter(
    (Q(age__gte=18) & Q(age__lte=65)) | Q(is_verified=True)
).exclude(Q(status='banned'))
```

#### F Expressions (Database Operations)

```python
from sqlorm import F

# Reference other fields
Product.objects.filter(stock__lt=F('reorder_level'))

# Arithmetic
Product.objects.update(price=F('price') * 1.1)  # 10% increase

# Annotations
Product.objects.annotate(profit=F('price') - F('cost'))
```

#### Aggregations

```python
from sqlorm import Count, Sum, Avg, Max, Min

# Single aggregation
Order.objects.aggregate(total=Sum('amount'))
# {'total': Decimal('15420.00')}

# Multiple aggregations
Order.objects.aggregate(
    total=Sum('amount'),
    average=Avg('amount'),
    count=Count('id'),
    max_order=Max('amount'),
    min_order=Min('amount'),
)

# Conditional aggregation
Order.objects.aggregate(
    paid_total=Sum('amount', filter=Q(is_paid=True)),
    unpaid_total=Sum('amount', filter=Q(is_paid=False)),
)
```

#### Annotations

```python
from sqlorm import Count, Sum

# Add computed fields
users = User.objects.annotate(
    order_count=Count('orders'),
    total_spent=Sum('orders__amount'),
)

for user in users:
    print(f"{user.name}: {user.order_count} orders, ${user.total_spent}")
```

---

### Raw SQL

For complex queries that are hard to express with the ORM:

```python
from sqlorm import execute_raw_sql
from sqlorm.connection import execute_raw_sql_dict

# Execute and get tuples
results = execute_raw_sql(
    "SELECT name, email FROM users WHERE age > %s",
    [18]
)

# Execute and get dictionaries
results = execute_raw_sql_dict(
    "SELECT name, email FROM users WHERE age > %s",
    [18]
)
for row in results:
    print(f"{row['name']}: {row['email']}")

# Insert/Update (no fetch)
execute_raw_sql(
    "UPDATE users SET is_active = %s WHERE last_login < %s",
    [False, '2024-01-01'],
    fetch=False
)
```

⚠️ **Always use parameterized queries to prevent SQL injection!**

---

### Transactions

```python
from sqlorm import transaction

# Basic transaction
with transaction():
    user = User.objects.create(name="John", email="john@example.com")
    Profile.objects.create(user_id=user.id, bio="Hello!")
    # Both are committed together, or both are rolled back

# Handling errors
try:
    with transaction():
        User.objects.create(name="Jane", email="jane@example.com")
        raise ValueError("Something went wrong!")
except ValueError:
    pass  # Transaction was automatically rolled back
```

---

### Multiple Databases

```python
from sqlorm import configure

# Configure with alias
configure({
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': 'primary.sqlite3',
}, alias='default')

configure({
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': 'analytics',
    'HOST': 'analytics-db.example.com',
    'USER': 'readonly',
    'PASSWORD': 'secret',
}, alias='analytics')

# Use specific database
from sqlorm import get_connection
analytics_conn = get_connection('analytics')
```

---

## 🔄 Migration from Django

Already using Django? SQLORM is designed to be 100% compatible:

| Django | SQLORM |
|--------|--------|
| `from django.db import models` | `from sqlorm import fields` |
| `class User(models.Model):` | `class User(Model):` |
| `models.CharField(...)` | `fields.CharField(...)` |
| `python manage.py migrate` | `User.migrate()` |
| `User.objects.all()` | `User.objects.all()` ✅ Same! |

**Your Django knowledge transfers directly!**

---

## 🆚 Comparison with Other ORMs

| Feature | SQLORM | SQLAlchemy | Peewee | Raw Django |
|---------|--------|------------|--------|------------|
| Django-compatible API | ✅ | ❌ | ❌ | ✅ |
| No project structure | ✅ | ✅ | ✅ | ❌ |
| Battle-tested at scale | ✅ | ✅ | ⚠️ | ✅ |
| Learning curve | Low* | High | Medium | Low |
| Multiple DB backends | ✅ | ✅ | ✅ | ✅ |
| Async support | ⚠️ | ✅ | ⚠️ | ⚠️ |

\* If you know Django, you already know SQLORM!

---

## 📁 Project Structure

```
sqlorm/
├── sqlorm/
│   ├── __init__.py      # Main exports
│   ├── config.py        # Configuration management
│   ├── base.py          # Model base class
│   ├── fields.py        # Field type proxy
│   ├── connection.py    # Connection utilities
│   └── exceptions.py    # Custom exceptions
├── tests/
│   └── test_sqlorm.py   # Test suite
├── examples/
│   ├── basic_usage.py
│   ├── advanced_usage.py
│   ├── postgresql_usage.py
│   └── configuration_examples.py
├── setup.py
├── pyproject.toml
└── README.md
```

---

## 🧪 Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=sqlorm --cov-report=html
```

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please make sure to update tests as appropriate.

---

## 📚 Resources

- **Django ORM Documentation**: https://docs.djangoproject.com/en/stable/topics/db/
- **Django QuerySet API**: https://docs.djangoproject.com/en/stable/ref/models/querysets/
- **Django Field Types**: https://docs.djangoproject.com/en/stable/ref/models/fields/

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**S.S.B**

- Email: surajsinghbisht054@gmail.com
- GitHub: [@surajsinghbisht054](https://github.com/surajsinghbisht054)
- Blog: https://bitforestinfo.blogspot.com

---

<p align="center">
  <strong>⭐ If you find SQLORM useful, please give it a star! ⭐</strong>
</p>

<p align="center">
  Made with ❤️ for the Python community
</p>

