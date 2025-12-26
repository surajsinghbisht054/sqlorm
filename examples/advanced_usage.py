#!/usr/bin/env python3
"""
SQLORM Advanced Example
=======================

This example demonstrates advanced features of SQLORM including:
- Complex queries with Q objects
- Aggregations
- Transactions
- Raw SQL
- Multiple database configurations
"""

from datetime import datetime, timedelta
from decimal import Decimal

# Import SQLORM
from sqlorm import (
    Avg,
    Count,
    F,
    Max,
    Min,
    Model,
    Q,
    Sum,
    configure,
    create_all_tables,
    execute_raw_sql,
    fields,
    get_connection,
    transaction,
)

# ============================================================================
# Configuration
# ============================================================================

configure(
    {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "example_advanced.sqlite3",
    },
    debug=True,
)

print("✅ Database configured!")


# ============================================================================
# Model Definitions
# ============================================================================


class Category(Model):
    """Product category."""

    name = fields.CharField(max_length=100, unique=True)
    description = fields.TextField(blank=True, default="")

    class Meta:
        verbose_name_plural = "categories"


class Product(Model):
    """Product model with various field types."""

    name = fields.CharField(max_length=200)
    sku = fields.CharField(max_length=50, unique=True)
    description = fields.TextField(blank=True, default="")
    price = fields.DecimalField(max_digits=10, decimal_places=2)
    cost = fields.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    quantity_in_stock = fields.PositiveIntegerField(default=0)
    is_available = fields.BooleanField(default=True)
    created_at = fields.DateTimeField(auto_now_add=True)
    updated_at = fields.DateTimeField(auto_now=True)

    # Choices example
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived"),
    ]
    status = fields.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    class Meta:
        ordering = ["-created_at"]


class Order(Model):
    """Order model for demonstrating aggregations."""

    order_number = fields.CharField(max_length=20, unique=True)
    customer_name = fields.CharField(max_length=200)
    customer_email = fields.EmailField()
    total_amount = fields.DecimalField(max_digits=12, decimal_places=2)
    is_paid = fields.BooleanField(default=False)
    created_at = fields.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


# Create tables
print("\n📋 Creating tables...")
create_all_tables()
print("✅ Tables created!")


# ============================================================================
# Seed Data
# ============================================================================

print("\n📝 Creating sample data...")

# Create categories
categories = ["Electronics", "Books", "Clothing", "Home & Garden", "Sports"]
for name in categories:
    Category.objects.get_or_create(name=name)
print(f"   Created {Category.objects.count()} categories")

# Create products
products_data = [
    ("Laptop", "ELEC-001", Decimal("999.99"), Decimal("750.00"), 50, "published"),
    ("Smartphone", "ELEC-002", Decimal("699.99"), Decimal("500.00"), 100, "published"),
    ("Headphones", "ELEC-003", Decimal("149.99"), Decimal("80.00"), 200, "published"),
    ("Python Book", "BOOK-001", Decimal("49.99"), Decimal("20.00"), 30, "published"),
    ("Django Guide", "BOOK-002", Decimal("39.99"), Decimal("15.00"), 25, "draft"),
    ("T-Shirt", "CLTH-001", Decimal("29.99"), Decimal("10.00"), 500, "published"),
    ("Jeans", "CLTH-002", Decimal("79.99"), Decimal("35.00"), 150, "published"),
    ("Garden Tools", "HOME-001", Decimal("59.99"), Decimal("30.00"), 0, "archived"),
    ("Yoga Mat", "SPRT-001", Decimal("34.99"), Decimal("15.00"), 75, "published"),
]

for name, sku, price, cost, qty, status in products_data:
    Product.objects.get_or_create(
        sku=sku,
        defaults={
            "name": name,
            "price": price,
            "cost": cost,
            "quantity_in_stock": qty,
            "status": status,
            "is_available": qty > 0,
        },
    )
print(f"   Created {Product.objects.count()} products")

# Create orders
import random

for i in range(20):
    Order.objects.get_or_create(
        order_number=f"ORD-{1000 + i}",
        defaults={
            "customer_name": f"Customer {i}",
            "customer_email": f"customer{i}@example.com",
            "total_amount": Decimal(str(random.uniform(50, 500))).quantize(
                Decimal("0.01")
            ),
            "is_paid": random.choice([True, False]),
        },
    )
print(f"   Created {Order.objects.count()} orders")


# ============================================================================
# Complex Queries with Q Objects
# ============================================================================

print("\n🔍 Complex queries with Q objects...")

# OR query: Products that are either cheap OR out of stock
cheap_or_out_of_stock = Product.objects.filter(Q(price__lt=50) | Q(quantity_in_stock=0))
print(f"   Cheap OR out of stock: {cheap_or_out_of_stock.count()} products")

# AND query: Published AND in stock
available_published = Product.objects.filter(
    Q(status="published") & Q(quantity_in_stock__gt=0)
)
print(f"   Published AND in stock: {available_published.count()} products")

# NOT query: NOT archived
not_archived = Product.objects.filter(~Q(status="archived"))
print(f"   Not archived: {not_archived.count()} products")

# Complex combination
complex_query = Product.objects.filter(
    (Q(price__gte=30) & Q(price__lte=100)) | Q(sku__startswith="ELEC")
).exclude(status="archived")
print(f"   Complex query result: {complex_query.count()} products")


# ============================================================================
# F Expressions (Database-level operations)
# ============================================================================

print("\n📊 F expressions (database operations)...")

# Calculate profit margin (price - cost)
products_with_margin = Product.objects.annotate(margin=F("price") - F("cost"))
for p in products_with_margin[:3]:
    print(f"   {p.name}: margin = ${p.margin}")

# Update based on current value (increase all prices by 10%)
# Product.objects.update(price=F('price') * Decimal('1.10'))
# print("   Increased all prices by 10%")


# ============================================================================
# Aggregations
# ============================================================================

print("\n📈 Aggregations...")

# Count
total_products = Product.objects.count()
print(f"   Total products: {total_products}")

# Sum
total_stock_value = Product.objects.aggregate(
    total=Sum(F("price") * F("quantity_in_stock"))
)
print(f"   Total stock value: ${total_stock_value['total'] or 0:.2f}")

# Average
avg_price = Product.objects.aggregate(avg_price=Avg("price"))
print(f"   Average price: ${avg_price['avg_price']:.2f}")

# Max and Min
price_range = Product.objects.aggregate(min_price=Min("price"), max_price=Max("price"))
print(
    f"   Price range: ${price_range['min_price']:.2f} - ${price_range['max_price']:.2f}"
)

# Multiple aggregations
order_stats = Order.objects.aggregate(
    total_orders=Count("id"),
    total_revenue=Sum("total_amount"),
    avg_order=Avg("total_amount"),
    paid_orders=Count("id", filter=Q(is_paid=True)),
)
print(f"   Order stats:")
print(f"      Total orders: {order_stats['total_orders']}")
print(f"      Total revenue: ${order_stats['total_revenue']:.2f}")
print(f"      Average order: ${order_stats['avg_order']:.2f}")
print(f"      Paid orders: {order_stats['paid_orders']}")


# ============================================================================
# Transactions
# ============================================================================

print("\n🔒 Transactions...")

try:
    with transaction():
        # Create an order
        order = Order.objects.create(
            order_number="ORD-TRANS-001",
            customer_name="Transaction Test",
            customer_email="trans@example.com",
            total_amount=Decimal("199.99"),
            is_paid=False,
        )
        print(f"   Created order: {order.order_number}")

        # Update it
        order.is_paid = True
        order.save()
        print(f"   Updated order payment status")

        # All changes are committed when exiting the context
    print("   ✅ Transaction committed successfully!")
except Exception as e:
    print(f"   ❌ Transaction rolled back: {e}")


# ============================================================================
# Raw SQL Queries
# ============================================================================

print("\n📝 Raw SQL queries...")

# Simple query (use %s for placeholders with Django)
products = execute_raw_sql(
    "SELECT name, price FROM sqlorm_models_product WHERE price > %s", [100]
)
print(f"   Products over $100:")
for name, price in products[:3]:
    print(f"      {name}: ${price}")

# Get connection for more control
from sqlorm.connection import execute_raw_sql_dict

# Return as dictionaries
products_dict = execute_raw_sql_dict(
    "SELECT name, price, quantity_in_stock FROM sqlorm_models_product LIMIT 3"
)
print(f"   Products as dictionaries:")
for p in products_dict:
    print(f"      {p['name']}: ${p['price']} (stock: {p['quantity_in_stock']})")


# ============================================================================
# Useful QuerySet Methods
# ============================================================================

print("\n🔧 Useful QuerySet methods...")

# values() - Get dictionaries
print("   values():")
for p in Product.objects.values("name", "price")[:2]:
    print(f"      {p}")

# values_list() - Get tuples or flat list
print("   values_list():")
names = list(Product.objects.values_list("name", flat=True)[:3])
print(f"      {names}")

# distinct() - Get unique values
print("   distinct():")
statuses = list(Product.objects.values_list("status", flat=True).distinct())
print(f"      Unique statuses: {statuses}")

# exists() - Check if any records match
print("   exists():")
has_expensive = Product.objects.filter(price__gt=500).exists()
print(f"      Products over $500: {has_expensive}")

# first() / last()
print("   first() / last():")
first = Product.objects.order_by("price").first()
last = Product.objects.order_by("price").last()
print(f"      Cheapest: {first.name} (${first.price})")
print(f"      Most expensive: {last.name} (${last.price})")


# ============================================================================
# Cleanup
# ============================================================================

print("\n🎉 Advanced example complete!")
print(f"   Database file: example_advanced.sqlite3")
