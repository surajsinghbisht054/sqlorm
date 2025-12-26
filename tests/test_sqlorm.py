"""
SQLORM Tests
============

Basic tests for SQLORM functionality.
Run with: pytest tests/test_sqlorm.py -v
"""

import os
import tempfile

import pytest


@pytest.fixture(autouse=True)
def clean_env():
    """Reset Django for each test."""
    import sys

    # Remove cached modules
    mods_to_remove = [m for m in sys.modules if m.startswith(("sqlorm", "django"))]
    for mod in mods_to_remove:
        del sys.modules[mod]

    yield


class TestConfiguration:
    """Test configuration."""

    def test_configure_sqlite(self):
        from sqlorm import configure, is_configured

        with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as f:
            db_path = f.name

        try:
            configure(
                {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": db_path,
                }
            )
            assert is_configured()
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_configure_with_migrations_dir(self):
        from sqlorm import configure, get_migrations_dir

        with tempfile.TemporaryDirectory() as tmpdir:
            migrations_path = os.path.join(tmpdir, "migrations")

            configure(
                {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                },
                migrations_dir=migrations_path,
            )

            assert get_migrations_dir() is not None
            assert os.path.exists(migrations_path)


class TestModels:
    """Test model definition and operations."""

    def test_model_creation(self):
        from sqlorm import Model, configure, fields

        configure(
            {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        )

        class TestModel(Model):
            name = fields.CharField(max_length=100)

        assert TestModel._meta.app_label == "sqlorm_app"
        assert hasattr(TestModel, "objects")

    def test_create_tables(self):
        from sqlorm import Model, configure, create_tables, fields

        configure(
            {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        )

        class Item(Model):
            title = fields.CharField(max_length=100)

        created = create_tables(verbosity=0)
        assert "sqlorm_app_item" in created

    def test_crud_operations(self):
        from sqlorm import Model, configure, create_tables, fields

        configure(
            {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        )

        class Person(Model):
            name = fields.CharField(max_length=100)
            age = fields.IntegerField(default=0)

        create_tables(verbosity=0)

        # Create
        p = Person.objects.create(name="Alice", age=30)
        assert p.id is not None
        assert p.name == "Alice"

        # Read
        p2 = Person.objects.get(id=p.id)
        assert p2.name == "Alice"

        # Update
        p2.age = 31
        p2.save()
        p3 = Person.objects.get(id=p.id)
        assert p3.age == 31

        # Delete
        p3.delete()
        assert Person.objects.count() == 0

    def test_to_dict(self):
        from sqlorm import Model, configure, create_tables, fields

        configure(
            {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        )

        class Thing(Model):
            name = fields.CharField(max_length=100)

        create_tables(verbosity=0)

        t = Thing.objects.create(name="Widget")
        d = t.to_dict()

        assert "id" in d
        assert d["name"] == "Widget"

    def test_to_json(self):
        import json

        from sqlorm import Model, configure, create_tables, fields

        configure(
            {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        )

        class Widget(Model):
            name = fields.CharField(max_length=100)

        create_tables(verbosity=0)

        w = Widget.objects.create(name="Gadget")
        j = w.to_json()

        data = json.loads(j)
        assert data["name"] == "Gadget"
