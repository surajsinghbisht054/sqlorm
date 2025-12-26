#!/usr/bin/env python3
"""
Example 1: Quick Start
======================

Simple example using create_tables() for quick development.
No migrations needed - tables created directly.
"""

from sqlorm import Model, configure, create_tables, fields

# Configure database
configure(
    {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "quickstart.sqlite3",
    }
)


# Define models
class User(Model):
    name = fields.CharField(max_length=100)
    email = fields.EmailField(unique=True)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Post(Model):
    title = fields.CharField(max_length=200)
    content = fields.TextField()
    author_id = fields.IntegerField()
    published = fields.BooleanField(default=False)
    created_at = fields.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


# Create tables
print("Creating tables...")
create_tables()

# CRUD Operations
print("\n--- CREATE ---")
user = User.objects.create(name="Alice", email="alice@example.com")
print(f"Created: {user.name} (id={user.id})")

post = Post.objects.create(
    title="Hello World", content="My first post!", author_id=user.id, published=True
)
print(f"Created: {post.title}")

print("\n--- READ ---")
all_users = User.objects.all()
print(f"Total users: {all_users.count()}")

active_users = User.objects.filter(is_active=True)
print(f"Active users: {active_users.count()}")

print("\n--- UPDATE ---")
user.name = "Alice Smith"
user.save()
print(f"Updated: {user.name}")

print("\n--- DELETE ---")
post.delete()
print("Deleted post")

print("\n--- Serialization ---")
print(f"to_dict: {user.to_dict()}")
print(f"to_json: {user.to_json()}")

# Cleanup
user.delete()
print("\n✅ Done!")
