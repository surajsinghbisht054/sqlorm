# Technical Documentation

## Architecture Overview

SQLORM acts as a lightweight wrapper around Django's ORM, allowing it to be used in standalone scripts without the standard Django project structure (manage.py, settings.py, apps, etc.).

It achieves this through three main components:
1. **Dynamic Configuration**: Sets up Django's global state on the fly.
2. **Model Metaclass Magic**: Intercepts model definitions and registers them with a virtual Django app.
3. **CLI Wrapper**: Proxies Django's management commands for migrations.

## Core Components

### 1. Configuration (`sqlorm.config`)

The `configure()` function is the entry point. It:
1. Accepts a simple dictionary for database config.
2. Constructs a Django settings dictionary with defaults:
   - `INSTALLED_APPS`: Includes `django.contrib.contenttypes` and `sqlorm.app`.
   - `DATABASES`: Maps the user's config to Django's format.
3. Calls `settings.configure()` and `django.setup()`.

This initializes the Django registry so that models can be loaded.

### 2. Model Definition (`sqlorm.base`)

The `Model` class uses a custom metaclass `ModelMeta`. When a user defines a class inheriting from `Model`:

1. **Lazy Loading**: If Django isn't configured yet, the model creation is deferred.
2. **Field Extraction**: It iterates over the class attributes to find Django fields.
3. **App Registration**: It dynamically creates a new Django model class and registers it under the `sqlorm.app` label.
   - `Meta.app_label` is forced to `"sqlorm_app"`.
   - This tricks Django into thinking all models belong to the internal `sqlorm.app`.

### 3. Fields Proxy (`sqlorm.fields`)

To avoid importing Django (and triggering configuration errors) before `configure()` is called, `sqlorm.fields` uses a `FieldsProxy`.
- It lazily imports `django.db.models` only when a field is accessed.
- This allows users to import `fields` at the top level of their script without side effects.

### 4. CLI & Migrations (`sqlorm.cli`)

Since there is no `manage.py`, `sqlorm` provides its own CLI entry point.

- **`--models <file>`**: The CLI imports the user's script to ensure model classes are defined in memory.
- **`makemigrations`**: Calls Django's `makemigrations` command programmatically, targeting the `sqlorm_app`.
- **`migrate`**: Calls Django's `migrate` command to apply changes to the database.

## Usage Flow

1. **Import**: User imports `Model`, `fields`, `configure`.
2. **Configure**: User calls `configure(...)`. Django is initialized.
3. **Define**: User defines models. `ModelMeta` registers them with Django.
4. **Runtime**:
   - **No Migrations**: `create_tables()` (if available) or `Model.objects.create()` works directly if tables exist.
   - **With Migrations**: User runs `sqlorm makemigrations` -> `sqlorm migrate`.

## Directory Structure

- `sqlorm/`: Main package
  - `app/`: A dummy Django app to hold the models.
  - `base.py`: Model class and metaclass.
  - `config.py`: Settings configuration.
  - `cli.py`: Command-line interface.
  - `fields.py`: Lazy proxy for fields.
