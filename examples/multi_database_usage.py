#!/usr/bin/env python3
"""
SQLORM Multi-Database Example
==============================

This example demonstrates how to use SQLORM with multiple databases
simultaneously using the Django-like approach. This is useful for:

- Separating read/write databases (read replicas)
- Using different databases for different types of data
- Isolating analytics/logs from the main application database
- Multi-tenant applications

SQLORM provides a clean, Django-like API for multi-database support:
1. Configure all databases with configure_databases()
2. Use _using class attribute on models to specify the database
3. All ORM operations are automatically routed to the correct database

NO raw sqlite3 or database driver code needed!
"""

import os
from datetime import datetime, timedelta

# Import SQLORM
from sqlorm import (
    Avg,
    Count,
    Model,
    Sum,
    add_database,
    configure_databases,
    fields,
    get_database_aliases,
    get_database_config,
)

print("=" * 70)
print("SQLORM Multi-Database Example")
print("=" * 70)


# ============================================================================
# Step 1: Configure Multiple Databases
# ============================================================================

print("\n" + "=" * 70)
print("Step 1: Configure Multiple Databases")
print("=" * 70)

# Configure all databases at once (Django-like approach)
configure_databases(
    {
        # Default database for main application data
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": "main_app.sqlite3",
        },
        # Analytics database for tracking events
        "analytics": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": "analytics.sqlite3",
        },
        # Logs database for application logs
        "logs": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": "logs.sqlite3",
        },
    }
)

print("\n✅ Configured databases:")
for alias in get_database_aliases():
    config = get_database_config(alias)
    print(f"   - {alias}: {config['NAME']}")


# ============================================================================
# Step 2: Define Models with Database Routing
# ============================================================================

print("\n" + "=" * 70)
print("Step 2: Define Models with Database Routing")
print("=" * 70)


# Model for 'default' database (no _using needed, it's the default)
class User(Model):
    """User model - uses the default database."""

    username = fields.CharField(max_length=100, unique=True)
    email = fields.EmailField()
    is_admin = fields.BooleanField(default=False)
    created_at = fields.DateTimeField(auto_now_add=True)


print(f"\n📦 User model → database: '{User.get_database_alias()}'")


# Model for 'analytics' database
class PageView(Model):
    """Page view tracking - uses the analytics database."""

    _using = "analytics"  # This routes ALL queries to 'analytics' database

    page_url = fields.CharField(max_length=500)
    user_id = fields.IntegerField(null=True, blank=True)
    session_id = fields.CharField(max_length=100)
    view_count = fields.IntegerField(default=1)
    timestamp = fields.DateTimeField(auto_now_add=True)


print(f"📦 PageView model → database: '{PageView.get_database_alias()}'")


# Model for 'logs' database
class AppLog(Model):
    """Application logs - uses the logs database."""

    _using = "logs"  # This routes ALL queries to 'logs' database

    LEVEL_CHOICES = [
        ("DEBUG", "Debug"),
        ("INFO", "Info"),
        ("WARNING", "Warning"),
        ("ERROR", "Error"),
        ("CRITICAL", "Critical"),
    ]

    level = fields.CharField(max_length=10, choices=LEVEL_CHOICES)
    message = fields.TextField()
    source = fields.CharField(max_length=100, null=True, blank=True)
    timestamp = fields.DateTimeField(auto_now_add=True)


print(f"📦 AppLog model → database: '{AppLog.get_database_alias()}'")


# ============================================================================
# Step 3: Create Tables (Migrations)
# ============================================================================

print("\n" + "=" * 70)
print("Step 3: Create Tables (Auto-routed Migrations)")
print("=" * 70)

# Each model's migrate() automatically uses the correct database!
User.migrate()
print("   ✓ User table created in 'default' database")

PageView.migrate()
print("   ✓ PageView table created in 'analytics' database")

AppLog.migrate()
print("   ✓ AppLog table created in 'logs' database")


# ============================================================================
# Step 4: CRUD Operations (Automatic Database Routing)
# ============================================================================

print("\n" + "=" * 70)
print("Step 4: CRUD Operations (Automatic Routing)")
print("=" * 70)

# --- Users (default database) ---
print("\n📊 Creating users (default database)...")

# Clean up from previous runs
User.objects.all().delete()

admin = User.objects.create(username="admin", email="admin@example.com", is_admin=True)
john = User.objects.create(
    username="john_doe", email="john@example.com", is_admin=False
)
jane = User.objects.create(
    username="jane_smith", email="jane@example.com", is_admin=False
)

print(f"   Created {User.objects.count()} users")
for user in User.objects.all():
    role = "👑 Admin" if user.is_admin else "👤 User"
    print(f"   - {role}: {user.username} ({user.email})")


# --- Page Views (analytics database) ---
print("\n📊 Recording page views (analytics database)...")

# Clean up from previous runs
PageView.objects.all().delete()

# Create page views
pages = [
    ("/home", admin.id, "sess_001", 150),
    ("/products", admin.id, "sess_001", 75),
    ("/products/widget", john.id, "sess_002", 50),
    ("/about", john.id, "sess_002", 30),
    ("/contact", jane.id, "sess_003", 25),
    ("/home", jane.id, "sess_003", 100),
]

for url, user_id, session_id, views in pages:
    PageView.objects.create(
        page_url=url, user_id=user_id, session_id=session_id, view_count=views
    )

print(f"   Recorded {PageView.objects.count()} page view entries")
print(f"   Total views: {PageView.objects.aggregate(total=Sum('view_count'))['total']}")


# --- App Logs (logs database) ---
print("\n📊 Writing logs (logs database)...")

# Clean up from previous runs
AppLog.objects.all().delete()

# Create logs
logs_data = [
    ("INFO", "Application started successfully", "main"),
    ("DEBUG", "Database connection established", "database"),
    ("INFO", f"User '{admin.username}' logged in", "auth"),
    ("WARNING", "Rate limit approaching for API endpoint", "api"),
    ("DEBUG", "Cache miss for user preferences", "cache"),
    ("INFO", "Scheduled task completed", "scheduler"),
]

for level, message, source in logs_data:
    AppLog.objects.create(level=level, message=message, source=source)

print(f"   Created {AppLog.objects.count()} log entries")

# Query logs by level
log_counts = {}
for level_choice in ["DEBUG", "INFO", "WARNING", "ERROR"]:
    count = AppLog.objects.filter(level=level_choice).count()
    if count > 0:
        log_counts[level_choice] = count

print("   Log levels:", dict(log_counts))


# ============================================================================
# Step 5: Advanced Queries (Cross-Model Analytics)
# ============================================================================

print("\n" + "=" * 70)
print("Step 5: Advanced Queries (Cross-Model Analytics)")
print("=" * 70)

# Analytics queries on the analytics database
print("\n📊 Top pages by view count:")
top_pages = (
    PageView.objects.values("page_url")
    .annotate(total_views=Sum("view_count"))
    .order_by("-total_views")[:5]
)

for page in top_pages:
    print(f"   📈 {page['page_url']}: {page['total_views']} views")


# User activity analysis (combining data from different databases)
print("\n📊 User Activity Report:")
print("   " + "-" * 50)

for user in User.objects.all():
    # Query analytics database for this user's page views
    user_views = PageView.objects.filter(user_id=user.id).aggregate(
        total=Sum("view_count"), pages=Count("id")
    )
    total = user_views["total"] or 0
    pages = user_views["pages"] or 0

    badge = "👑" if user.is_admin else "👤"
    print(f"   {badge} {user.username}: {pages} pages, {total} total views")


# Log analysis
print("\n📊 Log Analysis:")
log_stats = (
    AppLog.objects.values("source").annotate(count=Count("id")).order_by("-count")
)

for stat in log_stats:
    print(f"   📝 {stat['source']}: {stat['count']} entries")


# ============================================================================
# Step 6: Dynamic Database Addition
# ============================================================================

print("\n" + "=" * 70)
print("Step 6: Dynamic Database Addition")
print("=" * 70)

# Add a new database at runtime
add_database(
    "archive",
    {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "archive.sqlite3",
    },
)

print("\n✅ Added 'archive' database dynamically")
print(f"   Current databases: {get_database_aliases()}")


# Create a model for the archive database
class ArchivedUser(Model):
    """Archived user data - uses the archive database."""

    _using = "archive"

    original_id = fields.IntegerField()
    username = fields.CharField(max_length=100)
    email = fields.EmailField()
    archived_at = fields.DateTimeField(auto_now_add=True)


ArchivedUser.migrate()
print(f"   Created ArchivedUser table in 'archive' database")


# ============================================================================
# Step 7: Manual Database Override with .using()
# ============================================================================

print("\n" + "=" * 70)
print("Step 7: Manual Database Override with .using()")
print("=" * 70)

print(
    """
You can also override the default database for specific queries using .using():

    # Query User model on a different database (if same schema exists)
    User.objects.using('replica').all()

    # Save to a specific database
    user = User(username='test')
    user.save(using='backup')

    # Delete from a specific database
    User.objects.using('backup').filter(username='test').delete()

This gives you complete control over which database handles each operation.
"""
)


# ============================================================================
# Summary
# ============================================================================

print("=" * 70)
print("Summary: Database Files Created")
print("=" * 70)

db_files = ["main_app.sqlite3", "analytics.sqlite3", "logs.sqlite3", "archive.sqlite3"]
for db_file in db_files:
    if os.path.exists(db_file):
        size = os.path.getsize(db_file)
        print(f"   📁 {db_file} ({size:,} bytes)")

print("\n" + "=" * 70)
print("Key Concepts")
print("=" * 70)

print(
    """
1. 🎯 configure_databases(): Set up multiple databases with aliases

   configure_databases({
       'default': {...},
       'analytics': {...},
       'logs': {...},
   })

2. 📦 _using class attribute: Route all model operations to a database

   class PageView(Model):
       _using = 'analytics'  # All queries go to 'analytics' DB
       ...

3. 🔀 .using() method: Override database for specific queries

   Model.objects.using('replica').all()

4. 📊 Cross-database queries: Combine data from multiple databases

   for user in User.objects.all():  # From 'default'
       views = PageView.objects.filter(user_id=user.id)  # From 'analytics'

5. ➕ add_database(): Add databases dynamically at runtime

   add_database('backup', {'ENGINE': '...', 'NAME': '...'})
"""
)

print("\n🎉 Multi-database example complete!")
print("   All database operations use the ORM - no raw SQL needed!")
