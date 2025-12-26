#!/usr/bin/env python3
"""
SQLORM Basic Example (Todo App)
===============================

This example demonstrates the basic usage of SQLORM to create a simple
Todo application.

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
    'NAME': 'example_todo.sqlite3',
})

print("✅ Database configured!")


# ============================================================================
# Step 2: Define Your Models
# ============================================================================

class Task(Model):
    """
    A simple Task model.
    """
    title = fields.CharField(max_length=200)
    is_completed = fields.BooleanField(default=False)
    created_at = fields.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({'Done' if self.is_completed else 'Pending'})"


# ============================================================================
# Step 3: Create the Tables
# ============================================================================

print("\n📋 Creating tables...")
Task.migrate()
print("✅ Tables created!")


# ============================================================================
# Step 4: Create Records (CREATE)
# ============================================================================

print("\n📝 Creating tasks...")

# Create tasks
task1 = Task.objects.create(title="Buy groceries")
print(f"   Created: {task1}")

task2 = Task.objects.create(title="Walk the dog")
print(f"   Created: {task2}")

task3 = Task.objects.create(title="Learn SQLORM")
print(f"   Created: {task3}")


# ============================================================================
# Step 5: Query Records (READ)
# ============================================================================

print("\n🔍 Querying tasks...")

# Get all tasks
all_tasks = Task.objects.all()
print(f"   Total tasks: {all_tasks.count()}")

# Filter pending tasks
pending = Task.objects.filter(is_completed=False)
print(f"   Pending tasks: {pending.count()}")


# ============================================================================
# Step 6: Update Records (UPDATE)
# ============================================================================

print("\n✏️  Completing a task...")

# Mark 'Learn SQLORM' as completed
learn_task = Task.objects.get(title="Learn SQLORM")
learn_task.is_completed = True
learn_task.save()
print(f"   Updated: {learn_task}")


# ============================================================================
# Step 7: Delete Records (DELETE)
# ============================================================================

print("\n🗑️  Deleting completed tasks...")

# Delete completed tasks
deleted_count, _ = Task.objects.filter(is_completed=True).delete()
print(f"   Deleted {deleted_count} completed tasks")


# ============================================================================
# Cleanup
# ============================================================================

print("\n🎉 Example complete!")
print(f"   Database file: example_todo.sqlite3")
