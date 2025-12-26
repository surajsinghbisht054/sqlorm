#!/usr/bin/env python3
"""
SQLORM Todo App Example
=======================

A simple CLI Todo application demonstrating SQLORM usage.
"""

import os
import sys

# Add parent directory to path so we can import sqlorm
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from datetime import datetime

from django.utils import timezone

from sqlorm import Model, configure, fields

# ============================================================================
# 1. Configure Database
# ============================================================================
configure(
    {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "todo_app.sqlite3",
    }
)


# ============================================================================
# 2. Define Model
# ============================================================================
class Task(Model):
    """A simple task model."""

    title = fields.CharField(max_length=200)
    description = fields.TextField(blank=True, default="")
    is_completed = fields.BooleanField(default=False)
    created_at = fields.DateTimeField(auto_now_add=True)
    completed_at = fields.DateTimeField(null=True, blank=True)

    def __str__(self):
        status = "✅" if self.is_completed else "⬜"
        return f"{self.id}. {status} {self.title}"

    def complete(self):
        """Mark task as complete."""
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save()


# Ensure table exists
Task.migrate(verbosity=0)

# ============================================================================
# 3. CLI Functions
# ============================================================================


def add_task(title, description=""):
    task = Task.objects.create(title=title, description=description)
    print(f"Created task: {task.title}")


def list_tasks(show_all=False):
    tasks = Task.objects.all().order_by("-created_at")
    if not show_all:
        tasks = tasks.filter(is_completed=False)

    if not tasks.exists():
        print("No tasks found!")
        return

    print("\nYour Tasks:")
    print("-" * 40)
    for task in tasks:
        print(str(task))
    print("-" * 40)


def complete_task(task_id):
    try:
        task = Task.objects.get(id=task_id)
        task.complete()
        print(f"Completed: {task.title}")
    except Task.DoesNotExist:
        print(f"Task {task_id} not found!")


def delete_task(task_id):
    try:
        task = Task.objects.get(id=task_id)
        title = task.title
        task.delete()
        print(f"Deleted: {title}")
    except Task.DoesNotExist:
        print(f"Task {task_id} not found!")


def clear_completed():
    count, _ = Task.objects.filter(is_completed=True).delete()
    print(f"Cleared {count} completed tasks.")


# ============================================================================
# 4. Main Entry Point
# ============================================================================


def main():
    parser = argparse.ArgumentParser(description="Simple SQLORM Todo App")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("title", help="Task title")
    add_parser.add_argument("--desc", "-d", default="", help="Task description")

    # List command
    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument(
        "--all", "-a", action="store_true", help="Show all tasks (including completed)"
    )

    # Complete command
    done_parser = subparsers.add_parser("done", help="Mark task as complete")
    done_parser.add_argument("id", type=int, help="Task ID")

    # Delete command
    del_parser = subparsers.add_parser("delete", help="Delete a task")
    del_parser.add_argument("id", type=int, help="Task ID")

    # Clear command
    subparsers.add_parser("clear", help="Clear completed tasks")

    args = parser.parse_args()

    if args.command == "add":
        add_task(args.title, args.desc)
    elif args.command == "list":
        list_tasks(args.all)
    elif args.command == "done":
        complete_task(args.id)
    elif args.command == "delete":
        delete_task(args.id)
    elif args.command == "clear":
        clear_completed()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
