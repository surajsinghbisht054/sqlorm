#!/usr/bin/env python3
"""
SQLORM Example: Todo List Application
=====================================

This script demonstrates the core features of SQLORM, a lightweight wrapper
around Django's ORM for standalone Python scripts.

Features covered:
1. Configuration (Database setup)
2. Model Definition (Fields, Meta options)
3. Programmatic Migrations (makemigrations/migrate)
4. CRUD Operations (Create, Read, Update, Delete)
5. Advanced Querying (Filtering, Ordering, Q objects)
"""

import os
from datetime import timedelta

from django.utils import timezone

from sqlorm import F, Model, Q, configure, fields

# ==========================================
# 1. Configuration
# ==========================================
# Configure the database connection.
# We use SQLite for this example, but PostgreSQL, MySQL, etc., are supported.
# 'migrations_dir' tells SQLORM where to store migration files.
DB_FILE = "todo_app.sqlite3"
MIGRATIONS_DIR = "./todo_migrations"

print(f"--> Configuring database: {DB_FILE}")
configure(
    {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DB_FILE,
    },
    migrations_dir=MIGRATIONS_DIR,
)


# ==========================================
# 2. Model Definition
# ==========================================
# Define your data models using standard Django fields.
# SQLORM automatically registers these with the internal Django app.


class Task(Model):
    # CharField for short text
    title = fields.CharField(max_length=200, help_text="The task description")

    # TextField for longer content (optional)
    description = fields.TextField(blank=True, default="")

    # BooleanField for status
    is_completed = fields.BooleanField(default=False)

    # IntegerField for priority (1=High, 2=Medium, 3=Low)
    priority = fields.IntegerField(
        default=2,
        choices=[
            (1, "High"),
            (2, "Medium"),
            (3, "Low"),
        ],
    )

    # DateTimeFields for tracking time
    due_date = fields.DateTimeField(null=True, blank=True)
    created_at = fields.DateTimeField(auto_now_add=True)  # Set on creation
    updated_at = fields.DateTimeField(auto_now=True)  # Update on save

    class Meta:
        # Default ordering when querying
        ordering = ["-created_at"]

    def __str__(self):
        status = "✓" if self.is_completed else " "
        return f"[{status}] {self.title} (Priority: {self.get_priority_display()})"


# ==========================================
# 3. Main Execution Flow
# ==========================================


def run_demo():
    # --------------------------------------
    # A. Migrations (Schema Management)
    # --------------------------------------
    # In a real app, you might run these via CLI, but here we do it programmatically
    # to make this script self-contained.
    from sqlorm.cli import makemigrations, migrate

    print("\n--> Checking schema...")
    # Create migration files based on Model changes
    makemigrations(name="auto_update")
    # Apply migrations to the database
    migrate()

    # --------------------------------------
    # B. Create (Data Seeding)
    # --------------------------------------
    print("\n--> Creating tasks...")

    # Clear existing data for a clean run
    Task.objects.all().delete()

    # Method 1: create() shortcut
    t1 = Task.objects.create(
        title="Buy groceries", priority=1, due_date=timezone.now() + timedelta(days=1)
    )
    print(f"Created: {t1}")

    # Method 2: Instantiate and save()
    t2 = Task(title="Walk the dog", priority=2)
    t2.save()
    print(f"Created: {t2}")

    # Bulk creation
    tasks = [
        Task(title="Read a book", priority=3, is_completed=True),
        Task(
            title="Pay bills", priority=1, due_date=timezone.now() + timedelta(days=2)
        ),
        Task(title="Learn SQLORM", priority=1),
    ]
    Task.objects.bulk_create(tasks)
    print(f"Bulk created {len(tasks)} additional tasks.")

    # --------------------------------------
    # C. Read (Querying)
    # --------------------------------------
    print("\n--> Querying tasks...")

    # Get all objects
    all_tasks = Task.objects.all()
    print(f"Total tasks: {all_tasks.count()}")

    # Filtering
    high_priority = Task.objects.filter(priority=1)
    print(f"High priority tasks: {high_priority.count()}")

    # Chaining filters
    pending_high_priority = Task.objects.filter(priority=1, is_completed=False)
    print(f"Pending high priority: {pending_high_priority.count()}")

    # Complex lookups (contains, gt, etc.)
    search_results = Task.objects.filter(title__icontains="book")
    print(f"Tasks containing 'book': {[t.title for t in search_results]}")

    # --------------------------------------
    # D. Update
    # --------------------------------------
    print("\n--> Updating tasks...")

    # Update single object
    t1.is_completed = True
    t1.save()
    print(f"Marked '{t1.title}' as complete.")

    # Bulk update (efficient)
    # Mark all 'High' priority tasks as 'Medium'
    updated_count = Task.objects.filter(priority=1).update(priority=2)
    print(f"Downgraded priority for {updated_count} tasks.")

    # Using F expressions (referencing fields in the query)
    # Extend due date by 1 day for all pending tasks
    # Task.objects.filter(is_completed=False).update(due_date=F('due_date') + timedelta(days=1))

    # --------------------------------------
    # E. Advanced Features
    # --------------------------------------
    print("\n--> Advanced Queries...")

    # Q Objects for OR queries
    # Get tasks that are either completed OR have high priority (which is now 2 after update)
    complex_query = Task.objects.filter(Q(is_completed=True) | Q(priority=2))
    print(f"Completed OR Priority 2: {complex_query.count()}")

    # Ordering
    print("\nList of all tasks (ordered by creation date desc):")
    for task in Task.objects.all():
        print(f"  {task}")


if __name__ == "__main__":
    run_demo()
