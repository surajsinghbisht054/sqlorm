#!/usr/bin/env python3
"""
SQLORM Example - Model Definitions
==================================

This file demonstrates how to define models for use with the sqlorm CLI.

Usage:
    1. Define your models in this file
    2. Run: sqlorm --models models_example.py makemigrations
    3. Run: sqlorm --models models_example.py migrate
    4. Import and use your models in your application

OR for quick development (no migrations):
    1. Define models and call create_all_tables() in your script
"""

from sqlorm import Model, configure, fields

# Configure the database
configure(
    {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "example.sqlite3",
    }
)


# Define your models
class User(Model):
    """User model with profile information."""

    username = fields.CharField(max_length=150, unique=True)
    email = fields.EmailField(unique=True)
    first_name = fields.CharField(max_length=150, blank=True)
    last_name = fields.CharField(max_length=150, blank=True)
    is_active = fields.BooleanField(default=True)
    date_joined = fields.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["username"]

    def __str__(self):
        return self.username

    def get_full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip() or self.username


class Post(Model):
    """Blog post model."""

    title = fields.CharField(max_length=200)
    slug = fields.SlugField(max_length=200, unique=True)
    content = fields.TextField()
    author_id = fields.IntegerField()  # Simple FK without actual foreign key
    is_published = fields.BooleanField(default=False)
    created_at = fields.DateTimeField(auto_now_add=True)
    updated_at = fields.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Comment(Model):
    """Comment on a blog post."""

    post_id = fields.IntegerField()
    author_name = fields.CharField(max_length=100)
    author_email = fields.EmailField()
    content = fields.TextField()
    is_approved = fields.BooleanField(default=False)
    created_at = fields.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author_name}"


# When run directly, show registered models
if __name__ == "__main__":
    from sqlorm import get_registered_models

    print("Registered models:")
    for name, model in get_registered_models().items():
        print(f"  - {name}: {model._meta.db_table}")
        print(f"    Fields: {', '.join(model.get_fields())}")

    print("\nTo create migrations:")
    print("  sqlorm --models models_example.py makemigrations")
    print("  sqlorm --models models_example.py migrate")
