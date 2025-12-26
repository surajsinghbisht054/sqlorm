#!/usr/bin/env python3
"""
Example 2: With Migrations
==========================

Example using Django's migration system for schema management.

Usage:
    1. Run this script to define models
    2. Create migrations: sqlorm makemigrations --models 02_with_migrations.py
    3. Apply migrations: sqlorm migrate --models 02_with_migrations.py
"""

from sqlorm import Model, configure, fields

# Configure with migrations directory
configure(
    {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "app.sqlite3",
    },
    migrations_dir="./migrations",
)


# Models
class Category(Model):
    name = fields.CharField(max_length=100, unique=True)
    description = fields.TextField(blank=True, default="")

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Product(Model):
    name = fields.CharField(max_length=200)
    price = fields.DecimalField(max_digits=10, decimal_places=2)
    stock = fields.PositiveIntegerField(default=0)
    category_id = fields.IntegerField(null=True, blank=True)
    is_available = fields.BooleanField(default=True)
    created_at = fields.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} (${self.price})"


class Order(Model):
    customer_name = fields.CharField(max_length=200)
    customer_email = fields.EmailField()
    total = fields.DecimalField(max_digits=12, decimal_places=2)
    is_paid = fields.BooleanField(default=False)
    created_at = fields.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


# Show registered models
if __name__ == "__main__":
    from sqlorm import get_models

    print("Registered models:")
    for name, model in get_models().items():
        print(f"  - {name}: {model._meta.db_table}")

    print("\nTo create migrations:")
    print("  sqlorm makemigrations --models 02_with_migrations.py")
    print("\nTo apply migrations:")
    print("  sqlorm migrate --models 02_with_migrations.py")
