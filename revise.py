"""
SQLORM v3.0 - Revised Architecture Test
========================================

This script tests the new simplified architecture:
- Models inherit directly from Django's models.Model
- Models are monkey-patched into sqlorm.models_app
- Migrations via: sqlorm makemigrations && sqlorm migrate
- No wrapper classes - direct Django model usage
"""

# Step 1: Configure Django with SQLORM
from sqlorm import Model, configure, create_all_tables, fields, get_registered_models

configure(
    {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "test_revise.sqlite3",
    }
)

print("✅ Database configured!")


# Step 3: Define models
class Task(Model):
    """A simple Task model."""

    title = fields.CharField(max_length=200)
    description = fields.TextField(blank=True, default="")
    is_completed = fields.BooleanField(default=False)
    created_at = fields.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({'Done' if self.is_completed else 'Pending'})"

    def mark_complete(self):
        """Custom method to mark task as complete."""
        self.is_completed = True
        self.save()


class Category(Model):
    """Category for organizing tasks."""

    name = fields.CharField(max_length=100)
    color = fields.CharField(max_length=7, default="#000000")  # Hex color

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


print("\n📋 Registered models:")
for name, model in get_registered_models().items():
    print(f"   - {name}: {model._meta.db_table}")

# Step 4: Create tables (quick sync for development)
print("\n🔨 Creating tables...")
created = create_all_tables(verbosity=1)
if created:
    print(f"   Created: {', '.join(created)}")
else:
    print("   Tables already exist")

# Step 5: Test CRUD operations
print("\n📝 Testing CRUD operations...")

# Create
task = Task.objects.create(
    title="Test SQLORM v3", description="Testing the new architecture"
)
print(f"   Created: {task}")

category = Category.objects.create(name="Work", color="#FF0000")
print(f"   Created: {category}")

# Read
all_tasks = Task.objects.all()
print(f"   Total tasks: {all_tasks.count()}")

# Update
task.title = "Updated Task"
task.save()
print(f"   Updated: {task}")

# Test custom method
task.mark_complete()
print(f"   Marked complete: {task}")

# Test to_dict
task_dict = task.to_dict()
print(f"   to_dict: {task_dict}")

# Test to_json
task_json = task.to_json(indent=2)
print(f"   to_json: {task_json[:50]}...")

# Query with filter
pending = Task.objects.filter(is_completed=False)
completed = Task.objects.filter(is_completed=True)
print(f"   Pending: {pending.count()}, Completed: {completed.count()}")

# Delete
task.delete()
category.delete()
print("   Cleaned up test data")

print("\n✅ All tests passed!")
print("\nTo use migrations instead of quick sync:")
print("  $ sqlorm makemigrations")
print("  $ sqlorm migrate")
