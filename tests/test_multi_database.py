"""
SQLORM Multi-Database Test Suite
=================================

Tests for multi-database functionality. These tests MUST be run
separately from the main test suite because they configure Django
with a specific multi-database setup at module import time.

IMPORTANT: These tests are excluded from the default pytest run
(configured in pyproject.toml with --ignore).

Run these tests separately with:
    pytest tests/test_multi_database.py -v

Run ALL tests (main + multi-database) with:
    pytest tests/test_sqlorm.py -v && pytest tests/test_multi_database.py -v

Do NOT run both test files together in the same pytest session:
    pytest tests/  # This will cause failures!
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# ============================================================================
# Module-level setup - configure databases ONCE for all tests
# ============================================================================

# Create temp files for databases
_temp_db_files = {}

def _create_temp_dbs():
    """Create temporary database files for testing."""
    global _temp_db_files
    for name in ['default', 'analytics', 'logs', 'secondary']:
        with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as f:
            _temp_db_files[name] = f.name

def _cleanup_temp_dbs():
    """Clean up temporary database files."""
    global _temp_db_files
    for path in _temp_db_files.values():
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

# Create temp DBs immediately
_create_temp_dbs()

# Configure databases at module import time (before any tests run)
from sqlorm import configure_databases

configure_databases({
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': _temp_db_files['default'],
    },
    'analytics': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': _temp_db_files['analytics'],
    },
    'logs': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': _temp_db_files['logs'],
    },
    'secondary': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': _temp_db_files['secondary'],
    },
})

# Register cleanup
import atexit
atexit.register(_cleanup_temp_dbs)


# ============================================================================
# Test Classes
# ============================================================================

class TestMultiDatabaseConfiguration:
    """Test cases for multi-database configuration."""
    
    def test_configure_databases(self):
        """Test configuring multiple databases."""
        from sqlorm import get_database_aliases, get_database_config
        
        aliases = get_database_aliases()
        assert 'default' in aliases
        assert 'analytics' in aliases
        assert 'logs' in aliases
        assert 'secondary' in aliases
        
        # Check config retrieval
        default_config = get_database_config('default')
        assert default_config['ENGINE'] == 'django.db.backends.sqlite3'
    
    def test_missing_default_raises_error(self):
        """Test that missing 'default' database raises error."""
        from sqlorm import configure_databases
        from sqlorm.exceptions import ConfigurationError
        
        # This will try to reconfigure which is tricky with Django
        # But the validation should happen first
        with pytest.raises(ConfigurationError, match="'default' database configuration is required"):
            configure_databases({
                'other': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': 'test.sqlite3',
                },
            })
    
    def test_model_uses_default_database(self):
        """Test that models without _using use default database."""
        from sqlorm import Model, fields
        
        class MDDefaultModel(Model):
            name = fields.CharField(max_length=100)
        
        assert MDDefaultModel.get_database_alias() == 'default'
    
    def test_model_uses_specified_database(self):
        """Test that models with _using use specified database."""
        from sqlorm import Model, fields
        
        class MDAnalyticsModel(Model):
            _using = 'analytics'
            event = fields.CharField(max_length=100)
        
        assert MDAnalyticsModel.get_database_alias() == 'analytics'
    
    def test_model_migrate_to_correct_database(self):
        """Test that models migrate to their specified database."""
        from sqlorm import Model, fields
        from django.db import connections
        
        class MDUserInDefault(Model):
            username = fields.CharField(max_length=100)
        
        class MDEventInAnalytics(Model):
            _using = 'analytics'
            event_name = fields.CharField(max_length=100)
        
        MDUserInDefault.migrate()
        MDEventInAnalytics.migrate()
        
        # Check tables exist in correct databases
        default_tables = connections['default'].introspection.table_names()
        analytics_tables = connections['analytics'].introspection.table_names()
        
        assert 'sqlorm_models_mduserindefault' in default_tables
        assert 'sqlorm_models_mdeventinanalytics' in analytics_tables
    
    def test_crud_on_specific_database(self):
        """Test CRUD operations are routed to correct database."""
        from sqlorm import Model, fields
        
        class MDProduct(Model):
            name = fields.CharField(max_length=100)
            price = fields.IntegerField()
        
        class MDMetric(Model):
            _using = 'analytics'
            name = fields.CharField(max_length=100)
            value = fields.IntegerField()
        
        MDProduct.migrate()
        MDMetric.migrate()
        
        # Clean up any existing data
        MDProduct.objects.all().delete()
        MDMetric.objects.all().delete()
        
        # Create in default database
        MDProduct.objects.create(name="Widget", price=100)
        MDProduct.objects.create(name="Gadget", price=200)
        
        # Create in analytics database
        MDMetric.objects.create(name="page_views", value=1000)
        MDMetric.objects.create(name="users", value=50)
        
        # Verify counts
        assert MDProduct.objects.count() == 2
        assert MDMetric.objects.count() == 2
        
        # Verify data
        assert MDProduct.objects.filter(name="Widget").exists()
        assert MDMetric.objects.filter(name="page_views").exists()
    
    def test_add_database_dynamically(self):
        """Test adding a database at runtime."""
        from sqlorm import add_database, get_database_aliases
        from sqlorm.exceptions import ConfigurationError
        
        # Try to add a duplicate - should fail
        with pytest.raises(ConfigurationError, match="already exists"):
            add_database('default', {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'test.sqlite3',
            })
        
        # Verify existing aliases
        aliases = get_database_aliases()
        assert 'default' in aliases
    
    def test_get_nonexistent_database_raises_error(self):
        """Test getting non-existent database config raises error."""
        from sqlorm import get_database_config
        from sqlorm.exceptions import ConfigurationError
        
        with pytest.raises(ConfigurationError, match="not found"):
            get_database_config('nonexistent_db')
    
    def test_queryset_using_method(self):
        """Test QuerySet.using() method for ad-hoc database switching."""
        from sqlorm import Model, fields
        
        class MDSharedModel(Model):
            name = fields.CharField(max_length=100)
        
        # Migrate to both databases
        MDSharedModel.migrate()  # default
        MDSharedModel.migrate(using='analytics')  # analytics
        
        # Clean up
        MDSharedModel.objects.all().delete()
        MDSharedModel.objects.using('analytics').all().delete()
        
        # Create in default
        MDSharedModel.objects.create(name="DefaultRecord")
        
        # Use .using() to query analytics (should be empty)
        default_count = MDSharedModel.objects.count()
        analytics_count = MDSharedModel.objects.using('analytics').count()
        
        assert default_count == 1
        assert analytics_count == 0
    
    def test_table_exists_on_correct_database(self):
        """Test table_exists() checks the correct database."""
        from sqlorm import Model, fields
        
        class MDLogEntry(Model):
            _using = 'logs'
            message = fields.TextField()
        
        # Migrate
        MDLogEntry.migrate()
        
        # Now it exists on logs
        assert MDLogEntry.table_exists() is True
        
        # But not on analytics database
        assert MDLogEntry.table_exists(using='analytics') is False
    
    def test_cross_database_queries(self):
        """Test combining data from multiple databases."""
        from sqlorm import Model, fields, Count, Sum
        
        class MDOrder(Model):
            customer_id = fields.IntegerField()
            total = fields.IntegerField()
        
        class MDCustomerStats(Model):
            _using = 'analytics'
            customer_id = fields.IntegerField()
            order_count = fields.IntegerField(default=0)
            total_spent = fields.IntegerField(default=0)
        
        MDOrder.migrate()
        MDCustomerStats.migrate()
        
        # Clean up
        MDOrder.objects.all().delete()
        MDCustomerStats.objects.all().delete()
        
        # Create orders
        MDOrder.objects.create(customer_id=1, total=100)
        MDOrder.objects.create(customer_id=1, total=150)
        MDOrder.objects.create(customer_id=2, total=200)
        
        # Calculate stats from orders and store in analytics
        for cid in [1, 2]:
            orders = MDOrder.objects.filter(customer_id=cid)
            stats = orders.aggregate(
                count=Count('id'),
                total=Sum('total')
            )
            MDCustomerStats.objects.create(
                customer_id=cid,
                order_count=stats['count'],
                total_spent=stats['total']
            )
        
        # Verify analytics data
        stats1 = MDCustomerStats.objects.get(customer_id=1)
        assert stats1.order_count == 2
        assert stats1.total_spent == 250
        
        stats2 = MDCustomerStats.objects.get(customer_id=2)
        assert stats2.order_count == 1
        assert stats2.total_spent == 200


class TestMultiDatabaseAdvanced:
    """Advanced test cases for multi-database functionality."""
    
    def test_model_with_foreign_key_same_database(self):
        """Test ForeignKey relationships within same database."""
        from sqlorm import Model, fields
        
        class MDACategory(Model):
            name = fields.CharField(max_length=100)
        
        # Ensure Category's Django model is created first
        MDACategory._ensure_initialized()
        
        class MDAItem(Model):
            name = fields.CharField(max_length=100)
            # Reference the Django model directly for ForeignKey
            category = fields.ForeignKey(
                MDACategory._django_model,
                on_delete=fields.CASCADE,
                null=True
            )
        
        MDACategory.migrate()
        MDAItem.migrate()
        
        # Clean up
        MDAItem.objects.all().delete()
        MDACategory.objects.all().delete()
        
        # Create with relationship
        cat = MDACategory.objects.create(name="Electronics")
        MDAItem.objects.create(name="Phone", category=cat)
        MDAItem.objects.create(name="Laptop", category=cat)
        
        # Query through relationship
        items = MDAItem.objects.filter(category__name="Electronics")
        assert items.count() == 2
    
    def test_bulk_create_on_specific_database(self):
        """Test bulk_create on specified database."""
        from sqlorm import Model, fields
        
        class MDABulkModel(Model):
            _using = 'secondary'
            value = fields.IntegerField()
        
        MDABulkModel.migrate()
        MDABulkModel.objects.all().delete()
        
        # Bulk create using Django model
        DjangoBulkModel = MDABulkModel._django_model
        objects = [DjangoBulkModel(value=i) for i in range(100)]
        MDABulkModel.objects.bulk_create(objects)
        
        assert MDABulkModel.objects.count() == 100
        assert MDABulkModel.objects.filter(value__lt=50).count() == 50
    
    def test_update_on_specific_database(self):
        """Test bulk update on specified database."""
        from sqlorm import Model, fields
        
        class MDAUpdateModel(Model):
            _using = 'secondary'
            status = fields.CharField(max_length=20, default='pending')
            value = fields.IntegerField()
        
        MDAUpdateModel.migrate()
        MDAUpdateModel.objects.all().delete()
        
        # Create records
        for i in range(10):
            MDAUpdateModel.objects.create(value=i)
        
        # Bulk update
        MDAUpdateModel.objects.filter(value__gte=5).update(status='processed')
        
        assert MDAUpdateModel.objects.filter(status='processed').count() == 5
        assert MDAUpdateModel.objects.filter(status='pending').count() == 5
    
    def test_delete_on_specific_database(self):
        """Test delete operations on specified database."""
        from sqlorm import Model, fields
        
        class MDADeleteModel(Model):
            _using = 'secondary'
            name = fields.CharField(max_length=100)
            active = fields.BooleanField(default=True)
        
        MDADeleteModel.migrate()
        MDADeleteModel.objects.all().delete()
        
        # Create records
        MDADeleteModel.objects.create(name="Keep1", active=True)
        MDADeleteModel.objects.create(name="Keep2", active=True)
        MDADeleteModel.objects.create(name="Delete1", active=False)
        MDADeleteModel.objects.create(name="Delete2", active=False)
        
        # Delete inactive
        MDADeleteModel.objects.filter(active=False).delete()
        
        assert MDADeleteModel.objects.count() == 2
        assert MDADeleteModel.objects.filter(active=True).count() == 2
    
    def test_aggregation_on_specific_database(self):
        """Test aggregation queries on specified database."""
        from sqlorm import Model, fields, Sum, Avg, Max, Min, Count
        
        class MDASale(Model):
            _using = 'secondary'
            product = fields.CharField(max_length=100)
            amount = fields.IntegerField()
            quantity = fields.IntegerField()
        
        MDASale.migrate()
        MDASale.objects.all().delete()
        
        # Create sales data
        sales_data = [
            ("Widget", 100, 5),
            ("Widget", 150, 3),
            ("Gadget", 200, 2),
            ("Gadget", 250, 1),
        ]
        for product, amount, qty in sales_data:
            MDASale.objects.create(product=product, amount=amount, quantity=qty)
        
        # Aggregations
        result = MDASale.objects.aggregate(
            total=Sum('amount'),
            avg_amount=Avg('amount'),
            max_qty=Max('quantity'),
            min_qty=Min('quantity'),
            count=Count('id')
        )
        
        assert result['total'] == 700
        assert result['count'] == 4
        assert result['max_qty'] == 5
        assert result['min_qty'] == 1
    
    def test_values_on_specific_database(self):
        """Test values() and values_list() on specified database."""
        from sqlorm import Model, fields
        
        class MDAPerson(Model):
            _using = 'secondary'
            name = fields.CharField(max_length=100)
            age = fields.IntegerField()
        
        MDAPerson.migrate()
        MDAPerson.objects.all().delete()
        
        MDAPerson.objects.create(name="Alice", age=30)
        MDAPerson.objects.create(name="Bob", age=25)
        
        # values()
        names = list(MDAPerson.objects.values('name'))
        assert len(names) == 2
        assert {'name': 'Alice'} in names
        
        # values_list()
        ages = list(MDAPerson.objects.values_list('age', flat=True))
        assert sorted(ages) == [25, 30]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
