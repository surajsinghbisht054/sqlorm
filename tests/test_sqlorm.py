"""
SQLORM Test Suite
=================

Comprehensive test cases for SQLORM - the Django ORM wrapper for standalone scripts.

Run tests with:
    pytest tests/test_sqlorm.py -v
    
Or with coverage:
    pytest tests/test_sqlorm.py --cov=sqlorm --cov-report=html
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConfiguration:
    """Test cases for configuration module."""
    
    def test_configure_sqlite(self):
        """Test SQLite configuration."""
        from sqlorm import configure
        
        with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as f:
            db_path = f.name
        
        try:
            configure({
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': db_path,
            })
            
            from sqlorm.config import is_configured
            assert is_configured() is True
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)
    
    def test_configure_missing_engine(self):
        """Test that missing ENGINE raises error."""
        from sqlorm import configure
        from sqlorm.exceptions import ConfigurationError
        
        with pytest.raises(ConfigurationError) as exc_info:
            configure({'NAME': 'test.db'})
        
        assert "ENGINE" in str(exc_info.value)
    
    def test_configure_missing_name(self):
        """Test that missing NAME raises error."""
        from sqlorm import configure
        from sqlorm.exceptions import ConfigurationError
        
        with pytest.raises(ConfigurationError) as exc_info:
            configure({'ENGINE': 'django.db.backends.sqlite3'})
        
        assert "NAME" in str(exc_info.value)
    
    def test_get_settings(self):
        """Test getting current settings."""
        from sqlorm import configure, get_settings
        
        with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as f:
            db_path = f.name
        
        try:
            configure({
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': db_path,
            }, debug=True)
            
            settings = get_settings()
            assert settings['DEBUG'] is True
            assert 'DATABASES' in settings
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)


class TestModel:
    """Test cases for Model class."""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Set up a test database for each test."""
        from sqlorm import configure
        from sqlorm.base import clear_registry
        
        with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as f:
            self.db_path = f.name
        
        configure({
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': self.db_path,
        })
        
        yield
        
        # Cleanup
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
    
    def test_model_definition(self):
        """Test defining a simple model."""
        from sqlorm import Model, fields
        
        class TestUser(Model):
            name = fields.CharField(max_length=100)
            email = fields.EmailField(unique=True)
        
        assert TestUser is not None
        assert hasattr(TestUser, 'objects')
    
    def test_model_migrate(self):
        """Test creating a table for a model."""
        from sqlorm import Model, fields
        
        class TestArticle(Model):
            title = fields.CharField(max_length=200)
            content = fields.TextField()
        
        TestArticle.migrate()
        assert TestArticle.table_exists()
    
    def test_model_crud_operations(self):
        """Test Create, Read, Update, Delete operations."""
        from sqlorm import Model, fields
        
        class TestProduct(Model):
            name = fields.CharField(max_length=100)
            price = fields.DecimalField(max_digits=10, decimal_places=2)
            in_stock = fields.BooleanField(default=True)
        
        TestProduct.migrate()
        
        # Create
        product = TestProduct.objects.create(
            name="Widget",
            price="19.99",
            in_stock=True
        )
        assert product.id is not None
        
        # Read
        fetched = TestProduct.objects.get(id=product.id)
        assert fetched.name == "Widget"
        
        # Update
        fetched.name = "Super Widget"
        fetched.save()
        updated = TestProduct.objects.get(id=product.id)
        assert updated.name == "Super Widget"
        
        # Delete
        updated.delete()
        assert TestProduct.objects.filter(id=product.id).count() == 0
    
    def test_model_queryset_filter(self):
        """Test QuerySet filtering."""
        from sqlorm import Model, fields
        
        class TestPerson(Model):
            name = fields.CharField(max_length=100)
            age = fields.IntegerField()
        
        TestPerson.migrate()
        
        TestPerson.objects.create(name="Alice", age=25)
        TestPerson.objects.create(name="Bob", age=30)
        TestPerson.objects.create(name="Charlie", age=35)
        
        # Filter by age
        adults = TestPerson.objects.filter(age__gte=30)
        assert adults.count() == 2
        
        # Filter by name
        alice = TestPerson.objects.filter(name="Alice")
        assert alice.count() == 1
        assert alice.first().age == 25
    
    def test_model_queryset_ordering(self):
        """Test QuerySet ordering."""
        from sqlorm import Model, fields
        
        class TestItem(Model):
            name = fields.CharField(max_length=100)
            position = fields.IntegerField()
        
        TestItem.migrate()
        
        TestItem.objects.create(name="Third", position=3)
        TestItem.objects.create(name="First", position=1)
        TestItem.objects.create(name="Second", position=2)
        
        ordered = TestItem.objects.order_by('position')
        names = [item.name for item in ordered]
        assert names == ["First", "Second", "Third"]
        
        # Reverse order
        reversed_order = TestItem.objects.order_by('-position')
        names = [item.name for item in reversed_order]
        assert names == ["Third", "Second", "First"]
    
    def test_model_get_fields(self):
        """Test getting model fields."""
        from sqlorm import Model, fields
        
        class TestEmployee(Model):
            first_name = fields.CharField(max_length=50)
            last_name = fields.CharField(max_length=50)
            salary = fields.DecimalField(max_digits=10, decimal_places=2)
        
        TestEmployee.migrate()
        
        field_names = TestEmployee.get_fields()
        assert 'first_name' in field_names
        assert 'last_name' in field_names
        assert 'salary' in field_names
        assert 'id' in field_names  # Auto-generated primary key


class TestFields:
    """Test cases for fields module."""
    
    def test_fields_proxy(self):
        """Test that fields proxy provides Django fields."""
        from sqlorm import fields
        
        # Check that field types are accessible
        assert hasattr(fields, 'CharField')
        assert hasattr(fields, 'IntegerField')
        assert hasattr(fields, 'TextField')
        assert hasattr(fields, 'BooleanField')
        assert hasattr(fields, 'DateTimeField')
    
    def test_field_instantiation(self):
        """Test creating field instances."""
        from sqlorm import fields
        
        char_field = fields.CharField(max_length=100)
        assert char_field.max_length == 100
        
        int_field = fields.IntegerField(null=True)
        assert int_field.null is True
        
        bool_field = fields.BooleanField(default=False)
        assert bool_field.default is False


class TestConnection:
    """Test cases for connection module."""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Set up a test database."""
        from sqlorm import configure
        
        with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as f:
            self.db_path = f.name
        
        configure({
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': self.db_path,
        })
        
        yield
        
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
    
    def test_get_connection(self):
        """Test getting database connection."""
        from sqlorm import get_connection
        
        conn = get_connection()
        assert conn is not None
        assert conn.vendor == 'sqlite'
    
    def test_execute_raw_sql(self):
        """Test executing raw SQL."""
        from sqlorm import execute_raw_sql
        
        # Create a table using raw SQL
        execute_raw_sql(
            "CREATE TABLE test_raw (id INTEGER PRIMARY KEY, name TEXT)",
            fetch=False
        )
        
        # Insert data
        execute_raw_sql(
            "INSERT INTO test_raw (name) VALUES (?)",
            ['Test Name'],
            fetch=False
        )
        
        # Query data
        results = execute_raw_sql("SELECT * FROM test_raw")
        assert len(results) == 1
        assert results[0][1] == 'Test Name'
    
    def test_get_table_names(self):
        """Test getting table names."""
        from sqlorm import Model, fields, execute_raw_sql
        from sqlorm.connection import get_table_names
        
        # Create a test table
        execute_raw_sql(
            "CREATE TABLE test_tables (id INTEGER PRIMARY KEY)",
            fetch=False
        )
        
        tables = get_table_names()
        assert 'test_tables' in tables


class TestExceptions:
    """Test cases for exception classes."""
    
    def test_exception_hierarchy(self):
        """Test that all exceptions inherit from SQLORMError."""
        from sqlorm.exceptions import (
            SQLORMError,
            ConfigurationError,
            ModelError,
            MigrationError,
            ConnectionError,
        )
        
        assert issubclass(ConfigurationError, SQLORMError)
        assert issubclass(ModelError, SQLORMError)
        assert issubclass(MigrationError, SQLORMError)
        assert issubclass(ConnectionError, SQLORMError)
    
    def test_exception_catching(self):
        """Test catching exceptions."""
        from sqlorm.exceptions import SQLORMError, ConfigurationError
        
        def raise_config_error():
            raise ConfigurationError("Test error")
        
        # Should be catchable as ConfigurationError
        with pytest.raises(ConfigurationError):
            raise_config_error()
        
        # Should also be catchable as SQLORMError
        with pytest.raises(SQLORMError):
            raise_config_error()


class TestIntegration:
    """Integration tests for complete workflows."""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Set up a test database."""
        from sqlorm import configure
        from sqlorm.base import clear_registry
        
        with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as f:
            self.db_path = f.name
        
        configure({
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': self.db_path,
        })
        
        yield
        
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
    
    def test_complete_workflow(self):
        """Test a complete workflow from configuration to queries."""
        from sqlorm import Model, fields
        
        # Define models
        class Author(Model):
            name = fields.CharField(max_length=100)
            email = fields.EmailField(unique=True)
        
        class Book(Model):
            title = fields.CharField(max_length=200)
            isbn = fields.CharField(max_length=13, unique=True)
            published = fields.BooleanField(default=False)
        
        # Migrate
        Author.migrate()
        Book.migrate()
        
        # Create data
        author = Author.objects.create(
            name="Jane Author",
            email="jane@example.com"
        )
        
        book1 = Book.objects.create(
            title="First Book",
            isbn="1234567890123",
            published=True
        )
        
        book2 = Book.objects.create(
            title="Second Book",
            isbn="1234567890124",
            published=False
        )
        
        # Query
        assert Author.objects.count() == 1
        assert Book.objects.count() == 2
        assert Book.objects.filter(published=True).count() == 1
        
        # Update
        book2.published = True
        book2.save()
        assert Book.objects.filter(published=True).count() == 2
        
        # Delete
        book1.delete()
        assert Book.objects.count() == 1
    
    def test_queryset_chaining(self):
        """Test chaining multiple QuerySet methods."""
        from sqlorm import Model, fields
        
        class Task(Model):
            title = fields.CharField(max_length=200)
            priority = fields.IntegerField(default=0)
            completed = fields.BooleanField(default=False)
        
        Task.migrate()
        
        # Create sample data
        for i in range(10):
            Task.objects.create(
                title=f"Task {i}",
                priority=i % 5,
                completed=i % 2 == 0
            )
        
        # Chain filters
        results = (
            Task.objects
            .filter(completed=False)
            .filter(priority__gte=2)
            .order_by('-priority')
        )
        
        assert results.count() <= 5
        
        # Check ordering
        priorities = [task.priority for task in results]
        assert priorities == sorted(priorities, reverse=True)


class TestAdvancedQueries:
    """Test cases for advanced query features."""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Set up a test database."""
        from sqlorm import configure
        
        with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as f:
            self.db_path = f.name
        
        configure({
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': self.db_path,
        })
        
        yield
        
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
    
    def test_q_objects_or(self):
        """Test Q objects with OR operator."""
        from sqlorm import Model, fields, Q
        
        class Product(Model):
            name = fields.CharField(max_length=100)
            price = fields.DecimalField(max_digits=10, decimal_places=2)
            in_stock = fields.BooleanField(default=True)
        
        Product.migrate()
        
        Product.objects.create(name="Cheap", price="10.00", in_stock=True)
        Product.objects.create(name="Expensive", price="100.00", in_stock=True)
        Product.objects.create(name="OutOfStock", price="50.00", in_stock=False)
        
        # OR query
        results = Product.objects.filter(Q(price__lt=20) | Q(in_stock=False))
        assert results.count() == 2
    
    def test_q_objects_and(self):
        """Test Q objects with AND operator."""
        from sqlorm import Model, fields, Q
        
        class Item(Model):
            name = fields.CharField(max_length=100)
            category = fields.CharField(max_length=50)
            active = fields.BooleanField(default=True)
        
        Item.migrate()
        
        Item.objects.create(name="A", category="electronics", active=True)
        Item.objects.create(name="B", category="electronics", active=False)
        Item.objects.create(name="C", category="clothing", active=True)
        
        # AND query
        results = Item.objects.filter(Q(category="electronics") & Q(active=True))
        assert results.count() == 1
        assert results.first().name == "A"
    
    def test_q_objects_not(self):
        """Test Q objects with NOT operator."""
        from sqlorm import Model, fields, Q
        
        class Status(Model):
            name = fields.CharField(max_length=100)
            state = fields.CharField(max_length=20)
        
        Status.migrate()
        
        Status.objects.create(name="Active1", state="active")
        Status.objects.create(name="Pending", state="pending")
        Status.objects.create(name="Active2", state="active")
        
        # NOT query
        results = Status.objects.filter(~Q(state="active"))
        assert results.count() == 1
        assert results.first().name == "Pending"
    
    def test_f_expressions(self):
        """Test F expressions for database-level operations."""
        from sqlorm import Model, fields, F
        
        class Account(Model):
            name = fields.CharField(max_length=100)
            balance = fields.DecimalField(max_digits=10, decimal_places=2)
            credit_limit = fields.DecimalField(max_digits=10, decimal_places=2)
        
        Account.migrate()
        
        Account.objects.create(name="User1", balance="100.00", credit_limit="500.00")
        Account.objects.create(name="User2", balance="600.00", credit_limit="500.00")
        
        # Filter where balance exceeds credit_limit
        over_limit = Account.objects.filter(balance__gt=F('credit_limit'))
        assert over_limit.count() == 1
        assert over_limit.first().name == "User2"
    
    def test_aggregations(self):
        """Test aggregation functions."""
        from sqlorm import Model, fields, Count, Sum, Avg, Max, Min
        
        class Sale(Model):
            product = fields.CharField(max_length=100)
            amount = fields.DecimalField(max_digits=10, decimal_places=2)
            quantity = fields.IntegerField()
        
        Sale.migrate()
        
        Sale.objects.create(product="A", amount="100.00", quantity=2)
        Sale.objects.create(product="B", amount="200.00", quantity=3)
        Sale.objects.create(product="C", amount="150.00", quantity=1)
        
        # Count
        result = Sale.objects.aggregate(total=Count('id'))
        assert result['total'] == 3
        
        # Sum
        result = Sale.objects.aggregate(total_amount=Sum('amount'))
        assert float(result['total_amount']) == 450.0
        
        # Avg
        result = Sale.objects.aggregate(avg_amount=Avg('amount'))
        assert float(result['avg_amount']) == 150.0
        
        # Max/Min
        result = Sale.objects.aggregate(max_qty=Max('quantity'), min_qty=Min('quantity'))
        assert result['max_qty'] == 3
        assert result['min_qty'] == 1
    
    def test_annotations(self):
        """Test QuerySet annotations."""
        from sqlorm import Model, fields, F
        
        class Invoice(Model):
            description = fields.CharField(max_length=200)
            unit_price = fields.DecimalField(max_digits=10, decimal_places=2)
            quantity = fields.IntegerField()
        
        Invoice.migrate()
        
        Invoice.objects.create(description="Item A", unit_price="10.00", quantity=5)
        Invoice.objects.create(description="Item B", unit_price="20.00", quantity=3)
        
        # Annotate with calculated field
        invoices = Invoice.objects.annotate(
            total=F('unit_price') * F('quantity')
        )
        
        for inv in invoices:
            assert hasattr(inv, 'total')
    
    def test_values_and_values_list(self):
        """Test values() and values_list() methods."""
        from sqlorm import Model, fields
        
        class Person(Model):
            first_name = fields.CharField(max_length=50)
            last_name = fields.CharField(max_length=50)
            age = fields.IntegerField()
        
        Person.migrate()
        
        Person.objects.create(first_name="John", last_name="Doe", age=30)
        Person.objects.create(first_name="Jane", last_name="Smith", age=25)
        
        # values() returns dictionaries
        values = list(Person.objects.values('first_name', 'age'))
        assert len(values) == 2
        assert 'first_name' in values[0]
        assert 'age' in values[0]
        assert 'last_name' not in values[0]
        
        # values_list() returns tuples
        names = list(Person.objects.values_list('first_name', flat=True))
        assert set(names) == {'John', 'Jane'}
    
    def test_exists_method(self):
        """Test exists() method."""
        from sqlorm import Model, fields
        
        class Record(Model):
            name = fields.CharField(max_length=100)
            category = fields.CharField(max_length=50)
        
        Record.migrate()
        
        Record.objects.create(name="Test", category="A")
        
        assert Record.objects.filter(category="A").exists() is True
        assert Record.objects.filter(category="B").exists() is False
    
    def test_bulk_operations(self):
        """Test bulk create and update operations."""
        from sqlorm import Model, fields
        
        class BulkItem(Model):
            name = fields.CharField(max_length=100)
            value = fields.IntegerField(default=0)
        
        BulkItem.migrate()
        
        # Bulk create
        items = [
            BulkItem.objects.create(name=f"Item{i}", value=i)
            for i in range(5)
        ]
        
        assert BulkItem.objects.count() == 5
        
        # Bulk update
        BulkItem.objects.filter(value__gte=3).update(value=100)
        
        assert BulkItem.objects.filter(value=100).count() == 2
    
    def test_ordering_and_slicing(self):
        """Test ordering and slicing querysets."""
        from sqlorm import Model, fields
        
        class OrderedItem(Model):
            name = fields.CharField(max_length=100)
            position = fields.IntegerField()
        
        OrderedItem.migrate()
        
        for i in range(10):
            OrderedItem.objects.create(name=f"Item{i}", position=i)
        
        # Order ascending
        asc = list(OrderedItem.objects.order_by('position').values_list('position', flat=True))
        assert asc == list(range(10))
        
        # Order descending
        desc = list(OrderedItem.objects.order_by('-position').values_list('position', flat=True))
        assert desc == list(range(9, -1, -1))
        
        # Slicing
        first_three = OrderedItem.objects.order_by('position')[:3]
        assert first_three.count() == 3
        
        # Offset slicing
        middle = list(OrderedItem.objects.order_by('position')[3:6].values_list('position', flat=True))
        assert middle == [3, 4, 5]


class TestFieldTypes:
    """Test cases for different field types."""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Set up a test database."""
        from sqlorm import configure
        
        with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as f:
            self.db_path = f.name
        
        configure({
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': self.db_path,
        })
        
        yield
        
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
    
    def test_text_fields(self):
        """Test CharField and TextField."""
        from sqlorm import Model, fields
        
        class TextModel(Model):
            short_text = fields.CharField(max_length=50)
            long_text = fields.TextField(blank=True, default="")
            slug = fields.SlugField(max_length=100)
        
        TextModel.migrate()
        
        obj = TextModel.objects.create(
            short_text="Hello",
            long_text="This is a long text " * 100,
            slug="hello-world"
        )
        
        fetched = TextModel.objects.get(id=obj.id)
        assert fetched.short_text == "Hello"
        assert "long text" in fetched.long_text
        assert fetched.slug == "hello-world"
    
    def test_numeric_fields(self):
        """Test numeric field types."""
        from sqlorm import Model, fields
        from decimal import Decimal
        
        class NumericModel(Model):
            integer_val = fields.IntegerField()
            big_int = fields.BigIntegerField()
            positive_int = fields.PositiveIntegerField()
            float_val = fields.FloatField()
            decimal_val = fields.DecimalField(max_digits=10, decimal_places=4)
        
        NumericModel.migrate()
        
        obj = NumericModel.objects.create(
            integer_val=-42,
            big_int=9999999999999,
            positive_int=100,
            float_val=3.14159,
            decimal_val=Decimal("123.4567")
        )
        
        fetched = NumericModel.objects.get(id=obj.id)
        assert fetched.integer_val == -42
        assert fetched.big_int == 9999999999999
        assert fetched.positive_int == 100
        assert abs(fetched.float_val - 3.14159) < 0.0001
        assert fetched.decimal_val == Decimal("123.4567")
    
    def test_boolean_field(self):
        """Test BooleanField."""
        from sqlorm import Model, fields
        
        class BoolModel(Model):
            flag = fields.BooleanField(default=False)
            nullable_flag = fields.BooleanField(null=True, blank=True)
        
        BoolModel.migrate()
        
        obj1 = BoolModel.objects.create(flag=True, nullable_flag=None)
        obj2 = BoolModel.objects.create(flag=False, nullable_flag=True)
        
        assert BoolModel.objects.filter(flag=True).count() == 1
        assert BoolModel.objects.filter(nullable_flag__isnull=True).count() == 1
    
    def test_datetime_fields(self):
        """Test date and datetime fields."""
        from sqlorm import Model, fields
        from datetime import date, datetime, timedelta
        
        class DateModel(Model):
            created_date = fields.DateField()
            created_time = fields.TimeField(null=True)
            created_at = fields.DateTimeField(auto_now_add=True)
            updated_at = fields.DateTimeField(auto_now=True)
        
        DateModel.migrate()
        
        today = date.today()
        obj = DateModel.objects.create(created_date=today)
        
        fetched = DateModel.objects.get(id=obj.id)
        assert fetched.created_date == today
        assert fetched.created_at is not None
        assert fetched.updated_at is not None
    
    def test_email_and_url_fields(self):
        """Test EmailField and URLField."""
        from sqlorm import Model, fields
        
        class ContactModel(Model):
            email = fields.EmailField()
            website = fields.URLField(blank=True, default="")
        
        ContactModel.migrate()
        
        obj = ContactModel.objects.create(
            email="test@example.com",
            website="https://example.com"
        )
        
        fetched = ContactModel.objects.get(id=obj.id)
        assert fetched.email == "test@example.com"
        assert fetched.website == "https://example.com"
    
    def test_choice_field(self):
        """Test CharField with choices."""
        from sqlorm import Model, fields
        
        STATUS_CHOICES = [
            ('draft', 'Draft'),
            ('published', 'Published'),
            ('archived', 'Archived'),
        ]
        
        class ChoiceModel(Model):
            status = fields.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
        
        ChoiceModel.migrate()
        
        obj = ChoiceModel.objects.create(status='published')
        
        assert obj.status == 'published'
        assert ChoiceModel.objects.filter(status='published').count() == 1


class TestTransactions:
    """Test cases for transaction handling."""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Set up a test database."""
        from sqlorm import configure
        
        with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as f:
            self.db_path = f.name
        
        configure({
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': self.db_path,
        })
        
        yield
        
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
    
    def test_transaction_commit(self):
        """Test that transactions commit correctly."""
        from sqlorm import Model, fields, transaction
        
        class TxModel(Model):
            name = fields.CharField(max_length=100)
        
        TxModel.migrate()
        
        with transaction():
            TxModel.objects.create(name="Transaction Test")
        
        assert TxModel.objects.filter(name="Transaction Test").exists()
    
    def test_transaction_rollback(self):
        """Test that transactions rollback on error."""
        from sqlorm import Model, fields, transaction
        
        class TxModel2(Model):
            name = fields.CharField(max_length=100)
        
        TxModel2.migrate()
        
        try:
            with transaction():
                TxModel2.objects.create(name="Will Rollback")
                raise ValueError("Force rollback")
        except ValueError:
            pass
        
        assert not TxModel2.objects.filter(name="Will Rollback").exists()


class TestRawSQL:
    """Test cases for raw SQL execution."""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Set up a test database."""
        from sqlorm import configure
        
        with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as f:
            self.db_path = f.name
        
        configure({
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': self.db_path,
        })
        
        yield
        
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
    
    def test_raw_sql_select(self):
        """Test raw SQL SELECT queries."""
        from sqlorm import execute_raw_sql
        
        # Create table
        execute_raw_sql(
            "CREATE TABLE test_raw_select (id INTEGER PRIMARY KEY, name TEXT, value INTEGER)",
            fetch=False
        )
        
        # Insert data
        execute_raw_sql("INSERT INTO test_raw_select (name, value) VALUES (%s, %s)", ["A", 10], fetch=False)
        execute_raw_sql("INSERT INTO test_raw_select (name, value) VALUES (%s, %s)", ["B", 20], fetch=False)
        
        # Query
        results = execute_raw_sql("SELECT name, value FROM test_raw_select ORDER BY value")
        assert len(results) == 2
        assert results[0][0] == "A"
        assert results[1][1] == 20
    
    def test_raw_sql_dict(self):
        """Test raw SQL with dictionary results."""
        from sqlorm import execute_raw_sql
        from sqlorm.connection import execute_raw_sql_dict
        
        execute_raw_sql(
            "CREATE TABLE test_raw_dict (id INTEGER PRIMARY KEY, name TEXT)",
            fetch=False
        )
        execute_raw_sql("INSERT INTO test_raw_dict (name) VALUES (%s)", ["Test"], fetch=False)
        
        results = execute_raw_sql_dict("SELECT * FROM test_raw_dict")
        assert len(results) == 1
        assert 'name' in results[0]
        assert results[0]['name'] == "Test"


class TestLookups:
    """Test cases for various lookup types."""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Set up a test database."""
        from sqlorm import configure
        
        with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as f:
            self.db_path = f.name
        
        configure({
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': self.db_path,
        })
        
        yield
        
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
    
    def test_string_lookups(self):
        """Test string-based lookups."""
        from sqlorm import Model, fields
        
        class StringLookup(Model):
            text = fields.CharField(max_length=200)
        
        StringLookup.migrate()
        
        # Clean up any existing data from previous runs
        StringLookup.objects.all().delete()
        
        StringLookup.objects.create(text="Hello World")
        StringLookup.objects.create(text="hello universe")
        StringLookup.objects.create(text="Goodbye World")
        
        # exact
        assert StringLookup.objects.filter(text="Hello World").count() == 1
        
        # iexact (case insensitive)
        assert StringLookup.objects.filter(text__iexact="hello world").count() == 1
        
        # contains
        assert StringLookup.objects.filter(text__contains="World").count() == 2
        
        # icontains
        assert StringLookup.objects.filter(text__icontains="world").count() == 2
        
        # startswith - Note: SQLite's LIKE is case-insensitive by default
        # so both "Hello World" and "hello universe" match
        assert StringLookup.objects.filter(text__startswith="Hello").count() == 2
        
        # istartswith (explicit case insensitive)
        assert StringLookup.objects.filter(text__istartswith="hello").count() == 2
        
        # endswith - Note: SQLite's LIKE is case-insensitive
        assert StringLookup.objects.filter(text__endswith="World").count() == 2
    
    def test_numeric_lookups(self):
        """Test numeric lookups."""
        from sqlorm import Model, fields
        
        class NumericLookup(Model):
            value = fields.IntegerField()
        
        NumericLookup.migrate()
        
        # Clean up any existing data from previous runs
        NumericLookup.objects.all().delete()
        
        for v in [10, 20, 30, 40, 50]:
            NumericLookup.objects.create(value=v)
        
        # gt, gte
        assert NumericLookup.objects.filter(value__gt=30).count() == 2
        assert NumericLookup.objects.filter(value__gte=30).count() == 3
        
        # lt, lte
        assert NumericLookup.objects.filter(value__lt=30).count() == 2
        assert NumericLookup.objects.filter(value__lte=30).count() == 3
        
        # range
        assert NumericLookup.objects.filter(value__range=(20, 40)).count() == 3
        
        # in
        assert NumericLookup.objects.filter(value__in=[10, 30, 50]).count() == 3
    
    def test_null_lookups(self):
        """Test null/isnull lookups."""
        from sqlorm import Model, fields
        
        class NullLookup(Model):
            name = fields.CharField(max_length=100, null=True, blank=True)
        
        NullLookup.migrate()
        
        # Clean up any existing data from previous runs
        NullLookup.objects.all().delete()
        
        NullLookup.objects.create(name="HasValue")
        NullLookup.objects.create(name=None)
        NullLookup.objects.create(name="")
        
        # isnull
        assert NullLookup.objects.filter(name__isnull=True).count() == 1
        assert NullLookup.objects.filter(name__isnull=False).count() == 2


class TestModelInstanceMethods:
    """Test cases for custom methods on SQLORM model instances."""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Set up a test database for each test."""
        from sqlorm import configure
        from sqlorm.base import clear_registry
        
        with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as f:
            self.db_path = f.name
        
        configure({
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': self.db_path,
        })
        
        yield
        
        # Cleanup
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
    
    def test_custom_method_accessible_from_get(self):
        """Test that custom methods are accessible on instances from get()."""
        from sqlorm import Model, fields
        
        class TaskWithMethod(Model):
            title = fields.CharField(max_length=100)
            is_done = fields.BooleanField(default=False)
            
            def mark_done(self):
                self.is_done = True
                self.save()
            
            def get_title_upper(self):
                return self.title.upper()
        
        TaskWithMethod.migrate()
        
        # Create a task
        task = TaskWithMethod.objects.create(title="Test Task")
        assert task.is_done is False
        
        # Fetch and use custom method
        fetched = TaskWithMethod.objects.get(id=task.id)
        assert hasattr(fetched, 'mark_done')
        fetched.mark_done()
        
        # Verify the change was saved
        verified = TaskWithMethod.objects.get(id=task.id)
        assert verified.is_done is True
    
    def test_custom_method_accessible_from_filter(self):
        """Test that custom methods are accessible on instances from filter()."""
        from sqlorm import Model, fields
        
        class ItemWithMethod(Model):
            name = fields.CharField(max_length=100)
            
            def get_display_name(self):
                return f"[{self.name}]"
        
        ItemWithMethod.migrate()
        
        ItemWithMethod.objects.create(name="Item1")
        ItemWithMethod.objects.create(name="Item2")
        
        items = ItemWithMethod.objects.filter(name__startswith="Item")
        for item in items:
            assert hasattr(item, 'get_display_name')
            assert item.get_display_name().startswith("[")
            assert item.get_display_name().endswith("]")
    
    def test_custom_method_accessible_from_first(self):
        """Test that custom methods are accessible on instances from first()."""
        from sqlorm import Model, fields
        
        class FirstTestModel(Model):
            value = fields.IntegerField()
            
            def double_value(self):
                return self.value * 2
        
        FirstTestModel.migrate()
        FirstTestModel.objects.create(value=5)
        
        item = FirstTestModel.objects.first()
        assert item.double_value() == 10
    
    def test_custom_method_accessible_from_create(self):
        """Test that custom methods are accessible on instances from create()."""
        from sqlorm import Model, fields
        
        class CreateTestModel(Model):
            name = fields.CharField(max_length=100)
            
            def greet(self):
                return f"Hello, {self.name}!"
        
        CreateTestModel.migrate()
        
        item = CreateTestModel.objects.create(name="World")
        assert item.greet() == "Hello, World!"
    
    def test_does_not_exist_exception(self):
        """Test that DoesNotExist exception is accessible on model class."""
        from sqlorm import Model, fields
        
        class ExceptionTestModel(Model):
            name = fields.CharField(max_length=100)
        
        ExceptionTestModel.migrate()
        
        # Verify DoesNotExist is accessible
        assert hasattr(ExceptionTestModel, 'DoesNotExist')
        
        # Test that it's raised correctly
        with pytest.raises(ExceptionTestModel.DoesNotExist):
            ExceptionTestModel.objects.get(id=99999)
    
    def test_multiple_objects_returned_exception(self):
        """Test that MultipleObjectsReturned exception is accessible on model class."""
        from sqlorm import Model, fields
        
        class MultipleTestModel(Model):
            name = fields.CharField(max_length=100)
        
        MultipleTestModel.migrate()
        
        # Verify MultipleObjectsReturned is accessible
        assert hasattr(MultipleTestModel, 'MultipleObjectsReturned')
        
        # Create duplicates
        MultipleTestModel.objects.create(name="Duplicate")
        MultipleTestModel.objects.create(name="Duplicate")
        
        # Test that it's raised correctly
        with pytest.raises(MultipleTestModel.MultipleObjectsReturned):
            MultipleTestModel.objects.get(name="Duplicate")
    
    def test_custom_str_method(self):
        """Test that custom __str__ method works on instances."""
        from sqlorm import Model, fields
        
        class StrTestModel(Model):
            title = fields.CharField(max_length=100)
            
            def __str__(self):
                return f"Model: {self.title}"
        
        StrTestModel.migrate()
        
        item = StrTestModel.objects.create(title="Test")
        fetched = StrTestModel.objects.get(id=item.id)
        assert str(fetched) == "Model: Test"
    
    def test_method_with_self_modification(self):
        """Test custom method that modifies instance and saves."""
        from sqlorm import Model, fields
        
        class CounterModel(Model):
            name = fields.CharField(max_length=100)
            count = fields.IntegerField(default=0)
            
            def increment(self):
                self.count += 1
                self.save()
                return self.count
        
        CounterModel.migrate()
        
        item = CounterModel.objects.create(name="Counter")
        fetched = CounterModel.objects.get(id=item.id)
        
        result = fetched.increment()
        assert result == 1
        
        # Verify persisted
        verified = CounterModel.objects.get(id=item.id)
        assert verified.count == 1
    
    def test_queryset_chaining_with_custom_methods(self):
        """Test that queryset chaining preserves access to custom methods."""
        from sqlorm import Model, fields
        
        class ChainTestModel(Model):
            name = fields.CharField(max_length=100)
            category = fields.CharField(max_length=50)
            active = fields.BooleanField(default=True)
            
            def full_info(self):
                return f"{self.name} ({self.category})"
        
        ChainTestModel.migrate()
        
        ChainTestModel.objects.create(name="Item1", category="A", active=True)
        ChainTestModel.objects.create(name="Item2", category="A", active=False)
        ChainTestModel.objects.create(name="Item3", category="B", active=True)
        
        # Chain filter, exclude, order_by
        items = (ChainTestModel.objects
                .filter(active=True)
                .exclude(category="B")
                .order_by('name'))
        
        for item in items:
            assert hasattr(item, 'full_info')
            info = item.full_info()
            assert "(" in info and ")" in info


class TestSerialization:
    """Test cases for serialization features (to_dict, to_json, etc.)."""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Set up a test database for each test."""
        from sqlorm import configure
        from sqlorm.base import clear_registry
        
        with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as f:
            self.db_path = f.name
        
        configure({
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': self.db_path,
        })
        
        yield
        
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
    
    def test_to_dict_basic(self):
        """Test basic to_dict functionality."""
        from sqlorm import Model, fields
        
        class DictTestModel(Model):
            name = fields.CharField(max_length=100)
            value = fields.IntegerField(default=0)
        
        DictTestModel.migrate()
        
        item = DictTestModel.objects.create(name="Test", value=42)
        fetched = DictTestModel.objects.get(id=item.id)
        
        data = fetched.to_dict()
        assert isinstance(data, dict)
        assert data['name'] == "Test"
        assert data['value'] == 42
        assert 'id' in data
    
    def test_to_dict_with_fields(self):
        """Test to_dict with field selection."""
        from sqlorm import Model, fields
        
        class FieldSelectModel(Model):
            name = fields.CharField(max_length=100)
            email = fields.EmailField()
            age = fields.IntegerField()
        
        FieldSelectModel.migrate()
        
        item = FieldSelectModel.objects.create(
            name="John", email="john@example.com", age=30
        )
        fetched = FieldSelectModel.objects.get(id=item.id)
        
        data = fetched.to_dict(fields=['name', 'email'])
        assert 'name' in data
        assert 'email' in data
        assert 'age' not in data
    
    def test_to_dict_with_exclude(self):
        """Test to_dict with field exclusion."""
        from sqlorm import Model, fields
        
        class ExcludeModel(Model):
            name = fields.CharField(max_length=100)
            secret = fields.CharField(max_length=100)
        
        ExcludeModel.migrate()
        
        item = ExcludeModel.objects.create(name="Public", secret="Private")
        fetched = ExcludeModel.objects.get(id=item.id)
        
        data = fetched.to_dict(exclude=['secret'])
        assert 'name' in data
        assert 'secret' not in data
    
    def test_to_dict_without_pk(self):
        """Test to_dict without primary key."""
        from sqlorm import Model, fields
        
        class NoPkModel(Model):
            name = fields.CharField(max_length=100)
        
        NoPkModel.migrate()
        
        item = NoPkModel.objects.create(name="Test")
        fetched = NoPkModel.objects.get(id=item.id)
        
        data = fetched.to_dict(include_pk=False)
        assert 'id' not in data
        assert 'name' in data
    
    def test_to_json_basic(self):
        """Test basic to_json functionality."""
        import json
        from sqlorm import Model, fields
        
        class JsonTestModel(Model):
            name = fields.CharField(max_length=100)
            count = fields.IntegerField()
        
        JsonTestModel.migrate()
        
        item = JsonTestModel.objects.create(name="Test", count=5)
        fetched = JsonTestModel.objects.get(id=item.id)
        
        json_str = fetched.to_json()
        assert isinstance(json_str, str)
        
        parsed = json.loads(json_str)
        assert parsed['name'] == "Test"
        assert parsed['count'] == 5
    
    def test_to_json_with_indent(self):
        """Test to_json with indentation."""
        from sqlorm import Model, fields
        
        class IndentModel(Model):
            name = fields.CharField(max_length=100)
        
        IndentModel.migrate()
        
        item = IndentModel.objects.create(name="Test")
        fetched = IndentModel.objects.get(id=item.id)
        
        json_str = fetched.to_json(indent=2)
        assert '\n' in json_str
        assert '  ' in json_str
    
    def test_refresh_method(self):
        """Test refresh method to reload from database."""
        from sqlorm import Model, fields
        
        class RefreshModel(Model):
            name = fields.CharField(max_length=100)
        
        RefreshModel.migrate()
        
        item = RefreshModel.objects.create(name="Original")
        fetched = RefreshModel.objects.get(id=item.id)
        
        # Modify without saving
        fetched.name = "Modified"
        assert fetched.name == "Modified"
        
        # Refresh from database
        fetched.refresh()
        assert fetched.name == "Original"
    
    def test_update_method(self):
        """Test update method for field updates."""
        from sqlorm import Model, fields
        
        class UpdateModel(Model):
            name = fields.CharField(max_length=100)
            count = fields.IntegerField(default=0)
        
        UpdateModel.migrate()
        
        item = UpdateModel.objects.create(name="Test", count=0)
        fetched = UpdateModel.objects.get(id=item.id)
        
        # Update multiple fields
        fetched.update(name="Updated", count=10)
        
        # Verify in database
        verified = UpdateModel.objects.get(id=item.id)
        assert verified.name == "Updated"
        assert verified.count == 10
    
    def test_clone_method(self):
        """Test clone method for copying instances."""
        from sqlorm import Model, fields
        
        class CloneModel(Model):
            name = fields.CharField(max_length=100)
            category = fields.CharField(max_length=50)
        
        CloneModel.migrate()
        
        original = CloneModel.objects.create(name="Original", category="A")
        fetched = CloneModel.objects.get(id=original.id)
        
        # Clone with override
        clone = fetched.clone(name="Clone of Original")
        
        # Clone is not saved yet
        assert clone.name == "Clone of Original"
        assert clone.category == "A"
        
        # Save and verify
        clone.save()
        assert clone.id != original.id
        assert CloneModel.objects.count() == 2


class TestModelClassMethods:
    """Test cases for Model class methods (count, exists, truncate)."""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Set up a test database for each test."""
        from sqlorm import configure
        from sqlorm.base import clear_registry
        
        with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as f:
            self.db_path = f.name
        
        configure({
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': self.db_path,
        })
        
        yield
        
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
    
    def test_count_method(self):
        """Test Model.count() class method."""
        from sqlorm import Model, fields
        
        class CountModel(Model):
            name = fields.CharField(max_length=100)
        
        CountModel.migrate()
        
        assert CountModel.count() == 0
        
        CountModel.objects.create(name="One")
        CountModel.objects.create(name="Two")
        CountModel.objects.create(name="Three")
        
        assert CountModel.count() == 3
    
    def test_exists_method_basic(self):
        """Test Model.exists() class method without filters."""
        from sqlorm import Model, fields
        
        class ExistsModel(Model):
            name = fields.CharField(max_length=100)
        
        ExistsModel.migrate()
        
        assert ExistsModel.exists() is False
        
        ExistsModel.objects.create(name="Test")
        
        assert ExistsModel.exists() is True
    
    def test_exists_method_with_filters(self):
        """Test Model.exists() class method with filters."""
        from sqlorm import Model, fields
        
        class FilterExistsModel(Model):
            name = fields.CharField(max_length=100)
            active = fields.BooleanField(default=True)
        
        FilterExistsModel.migrate()
        
        FilterExistsModel.objects.create(name="Active", active=True)
        FilterExistsModel.objects.create(name="Inactive", active=False)
        
        assert FilterExistsModel.exists(active=True) is True
        assert FilterExistsModel.exists(active=False) is True
        assert FilterExistsModel.exists(name="Nonexistent") is False
    
    def test_truncate_method(self):
        """Test Model.truncate() class method."""
        from sqlorm import Model, fields
        from sqlorm.exceptions import ModelError
        
        class TruncateModel(Model):
            name = fields.CharField(max_length=100)
        
        TruncateModel.migrate()
        
        TruncateModel.objects.create(name="One")
        TruncateModel.objects.create(name="Two")
        TruncateModel.objects.create(name="Three")
        
        assert TruncateModel.count() == 3
        
        # Test safety check
        with pytest.raises(ModelError):
            TruncateModel.truncate()
        
        # Truncate with confirmation
        TruncateModel.truncate(confirm=True)
        
        assert TruncateModel.count() == 0
    
    def test_get_field_info(self):
        """Test Model.get_field_info() class method."""
        from sqlorm import Model, fields
        
        class FieldInfoModel(Model):
            name = fields.CharField(max_length=100)
            email = fields.EmailField(unique=True)
            age = fields.IntegerField(null=True)
        
        FieldInfoModel.migrate()
        
        info = FieldInfoModel.get_field_info()
        
        assert 'name' in info
        assert info['name']['type'] == 'CharField'
        assert info['name']['max_length'] == 100
        
        assert 'email' in info
        assert info['email']['unique'] is True
        
        assert 'age' in info
        assert info['age']['null'] is True


class TestEnhancedExceptions:
    """Test cases for enhanced exception features."""
    
    def test_exception_details(self):
        """Test that exceptions support details dict."""
        from sqlorm.exceptions import SQLORMError, ConfigurationError
        
        error = SQLORMError("Test error", details={"key": "value"})
        assert error.details == {"key": "value"}
        
        config_error = ConfigurationError(
            "Missing config",
            missing_keys=["ENGINE", "NAME"]
        )
        assert config_error.details["missing_keys"] == ["ENGINE", "NAME"]
    
    def test_exception_hint(self):
        """Test that exceptions support hints."""
        from sqlorm.exceptions import SQLORMError
        
        error = SQLORMError(
            "Connection failed",
            hint="Check your database credentials"
        )
        assert error.hint == "Check your database credentials"
        assert "Hint:" in str(error)
    
    def test_exception_to_dict(self):
        """Test that exceptions can be serialized to dict."""
        from sqlorm.exceptions import MigrationError
        
        error = MigrationError(
            "Table creation failed",
            table_name="users",
            operation="CREATE TABLE"
        )
        
        error_dict = error.to_dict()
        assert error_dict["error_type"] == "MigrationError"
        assert error_dict["message"] == "Table creation failed"
        assert error_dict["details"]["table"] == "users"


class TestEquality:
    """Test cases for equality and hashing of model instances."""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Set up a test database for each test."""
        from sqlorm import configure
        
        with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as f:
            self.db_path = f.name
        
        configure({
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': self.db_path,
        })
        
        yield
        
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
    
    def test_instance_equality(self):
        """Test that instances with same pk are equal."""
        from sqlorm import Model, fields
        
        class EqualityModel(Model):
            name = fields.CharField(max_length=100)
        
        EqualityModel.migrate()
        
        item = EqualityModel.objects.create(name="Test")
        
        fetched1 = EqualityModel.objects.get(id=item.id)
        fetched2 = EqualityModel.objects.get(id=item.id)
        
        assert fetched1 == fetched2
    
    def test_instance_hashing(self):
        """Test that instances can be used in sets and as dict keys."""
        from sqlorm import Model, fields
        
        class HashModel(Model):
            name = fields.CharField(max_length=100)
        
        HashModel.migrate()
        
        item1 = HashModel.objects.create(name="One")
        item2 = HashModel.objects.create(name="Two")
        
        # Test in set
        items_set = {item1, item2}
        assert len(items_set) == 2
        
        # Fetch again and add to set
        fetched1 = HashModel.objects.get(id=item1.id)
        items_set.add(fetched1)
        assert len(items_set) == 2  # Should not add duplicate
        
        # Test as dict key
        items_dict = {item1: "first", item2: "second"}
        assert items_dict[fetched1] == "first"


# Multi-database tests are in a separate file: test_multi_database.py
# This is necessary because Django doesn't support full reconfiguration
# after django.setup() has been called. The separate file ensures a
# fresh Python process and Django configuration.


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
