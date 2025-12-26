#!/usr/bin/env python3
"""
SQLORM PostgreSQL Example
=========================

This example demonstrates how to use SQLORM with PostgreSQL.

Prerequisites:
    1. Install PostgreSQL database driver:
       pip install psycopg2-binary

    2. Create a database:
       createdb myapp_db

    3. Update the configuration below with your credentials
"""

from datetime import datetime
from decimal import Decimal

# Import SQLORM
from sqlorm import Model, configure, fields

# ============================================================================
# PostgreSQL Configuration
# ============================================================================

# Option 1: Using individual settings
configure(
    {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "myapp_db",  # Database name
        "USER": "postgres",  # Database user
        "PASSWORD": "your_password",  # Database password
        "HOST": "localhost",  # Database host
        "PORT": "5432",  # Database port
    }
)

# Option 2: You can also use environment variables
# import os
# from sqlorm.config import configure_from_env
# os.environ['DATABASE_URL'] = 'postgres://user:pass@localhost:5432/myapp_db'
# configure_from_env()

print("✅ PostgreSQL database configured!")


# ============================================================================
# Model Definitions (Same as SQLite - no changes needed!)
# ============================================================================


class Author(Model):
    """Author model with various PostgreSQL-compatible fields."""

    name = fields.CharField(max_length=200)
    email = fields.EmailField(unique=True)
    bio = fields.TextField(blank=True, default="")
    website = fields.URLField(blank=True, default="")
    is_verified = fields.BooleanField(default=False)
    joined_at = fields.DateTimeField(auto_now_add=True)


class Article(Model):
    """Article model demonstrating text search capabilities."""

    title = fields.CharField(max_length=300)
    slug = fields.SlugField(max_length=300, unique=True)
    content = fields.TextField()
    summary = fields.TextField(max_length=500, blank=True, default="")

    # PostgreSQL-specific: JSONField for flexible data
    metadata = fields.JSONField(default=dict, blank=True)

    view_count = fields.PositiveIntegerField(default=0)
    is_published = fields.BooleanField(default=False)
    published_at = fields.DateTimeField(null=True, blank=True)
    created_at = fields.DateTimeField(auto_now_add=True)
    updated_at = fields.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]


# Create tables
print("\n📋 Creating tables...")
Author.migrate()
Article.migrate()
print("✅ Tables created!")


# ============================================================================
# CRUD Operations (Same API as SQLite!)
# ============================================================================

print("\n📝 Creating records...")

# Create author
author, created = Author.objects.get_or_create(
    email="jane@example.com",
    defaults={
        "name": "Jane Writer",
        "bio": "Tech writer and blogger",
        "website": "https://janewriter.com",
        "is_verified": True,
    },
)
print(f"   Author: {author.name}")

# Create article with JSON metadata
article, created = Article.objects.get_or_create(
    slug="getting-started-with-sqlorm",
    defaults={
        "title": "Getting Started with SQLORM",
        "content": """
        SQLORM is a powerful library that brings Django's ORM to standalone scripts.

        In this article, we'll explore how to set up and use SQLORM with PostgreSQL.
        """.strip(),
        "summary": "Learn how to use Django ORM in standalone scripts",
        "metadata": {
            "tags": ["python", "django", "orm", "postgresql"],
            "reading_time_minutes": 5,
            "difficulty": "beginner",
        },
        "is_published": True,
        "published_at": datetime.now(),
    },
)
print(f"   Article: {article.title}")


# ============================================================================
# PostgreSQL-Specific Features
# ============================================================================

print("\n🐘 PostgreSQL-specific features...")

# JSON field queries (PostgreSQL's JSONField)
articles_tagged_python = Article.objects.filter(metadata__tags__contains=["python"])
print(f"   Articles tagged 'python': {articles_tagged_python.count()}")

# JSON key lookup
beginner_articles = Article.objects.filter(metadata__difficulty="beginner")
print(f"   Beginner articles: {beginner_articles.count()}")


# ============================================================================
# Querying
# ============================================================================

print("\n🔍 Querying...")

# All articles
articles = Article.objects.all()
print(f"   Total articles: {articles.count()}")

# Published articles
published = Article.objects.filter(is_published=True)
print(f"   Published: {published.count()}")

# Full-text search (basic - for full PostgreSQL text search, use SearchVector)
search_term = "SQLORM"
matching = Article.objects.filter(title__icontains=search_term)
print(f"   Articles matching '{search_term}': {matching.count()}")

# Get article details
for article in Article.objects.all()[:5]:
    tags = article.metadata.get("tags", [])
    print(f"   📄 {article.title}")
    print(f"      Tags: {', '.join(tags)}")
    print(f"      Views: {article.view_count}")


# ============================================================================
# Cleanup
# ============================================================================

print("\n🎉 PostgreSQL example complete!")
print("   Note: Make sure to update the database credentials in this script.")
