#!/usr/bin/env python3
"""
SQLORM Basic Example
====================

This example demonstrates the basic usage of SQLORM to create a simple
database with users and perform CRUD operations.

This is a standalone script - no Django project structure needed!
"""

# Import SQLORM
from sqlorm import configure, Model, fields

# ============================================================================
# Step 1: Configure the Database
# ============================================================================

# For a simple SQLite database (great for development and small applications)
configure({
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': 'example_basic.sqlite3',
})

print("✅ Database configured!")


# ============================================================================
# Step 2: Define Your Models
# ============================================================================

class User(Model):
    """
    A simple User model with basic fields.
    
    This works exactly like a Django model!
    """
    username = fields.CharField(max_length=100, unique=True)
    email = fields.EmailField(unique=True)
    full_name = fields.CharField(max_length=200, blank=True, default="")
    is_active = fields.BooleanField(default=True)
    created_at = fields.DateTimeField(auto_now_add=True)
    updated_at = fields.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']


class Profile(Model):
    """
    User profile with additional information.
    """
    bio = fields.TextField(blank=True, default="")
    website = fields.URLField(blank=True, default="")
    age = fields.PositiveIntegerField(null=True, blank=True)


# ============================================================================
# Step 3: Create the Tables
# ============================================================================

print("\n📋 Creating tables...")
User.migrate()
Profile.migrate()
print("✅ Tables created!")


# ============================================================================
# Step 4: Create Records (CREATE)
# ============================================================================

print("\n📝 Creating users...")

# Method 1: Using objects.create() - Recommended!
user1 = User.objects.create(
    username="johndoe",
    email="john@example.com",
    full_name="John Doe"
)
print(f"   Created: {user1.username} (ID: {user1.id})")

# Method 2: Create another user using create()
user2 = User.objects.create(
    username="janedoe",
    email="jane@example.com",
    full_name="Jane Doe"
)
print(f"   Created: {user2.username} (ID: {user2.id})")

# Method 3: Using get_or_create
user3, created = User.objects.get_or_create(
    username="bobsmith",
    defaults={
        "email": "bob@example.com",
        "full_name": "Bob Smith"
    }
)
print(f"   {'Created' if created else 'Found'}: {user3.username} (ID: {user3.id})")


# ============================================================================
# Step 5: Query Records (READ)
# ============================================================================

print("\n🔍 Querying users...")

# Get all users
all_users = User.objects.all()
print(f"   Total users: {all_users.count()}")

# Get a specific user
john = User.objects.get(username="johndoe")
print(f"   Found John: {john.email}")

# Filter users
active_users = User.objects.filter(is_active=True)
print(f"   Active users: {active_users.count()}")

# Complex filters
users_with_j = User.objects.filter(username__startswith="j")
print(f"   Users starting with 'j': {users_with_j.count()}")

# First and last
first_user = User.objects.first()
print(f"   First user: {first_user.username}")


# ============================================================================
# Step 6: Update Records (UPDATE)
# ============================================================================

print("\n✏️  Updating users...")

# Method 1: Update single object
john = User.objects.get(username="johndoe")
john.full_name = "John William Doe"
john.save()
print(f"   Updated John's full name: {john.full_name}")

# Method 2: Bulk update
User.objects.filter(full_name="").update(full_name="Unknown")
print("   Updated all users without full names")


# ============================================================================
# Step 7: Delete Records (DELETE)
# ============================================================================

print("\n🗑️  Deleting users...")

# Create a temporary user to delete
temp_user = User.objects.create(
    username="tempuser",
    email="temp@example.com"
)
print(f"   Created temporary user: {temp_user.username}")

# Delete single object
temp_user.delete()
print("   Deleted temporary user")

# Bulk delete (commented out to preserve data)
# User.objects.filter(is_active=False).delete()


# ============================================================================
# Step 8: Advanced Queries
# ============================================================================

print("\n🚀 Advanced queries...")

# Count
count = User.objects.count()
print(f"   Total users: {count}")

# Exists
has_john = User.objects.filter(username="johndoe").exists()
print(f"   John exists: {has_john}")

# Values (get dictionaries instead of model instances)
usernames = User.objects.values_list('username', flat=True)
print(f"   Usernames: {list(usernames)}")

# Order by
ordered_users = User.objects.order_by('username')
print(f"   Users ordered by username: {[u.username for u in ordered_users]}")

# Exclude
not_john = User.objects.exclude(username="johndoe")
print(f"   Users except John: {[u.username for u in not_john]}")


# ============================================================================
# Cleanup
# ============================================================================

print("\n🎉 Example complete!")
print(f"   Database file: example_basic.sqlite3")
print("   You can now inspect the database using any SQLite browser.")
