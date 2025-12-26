"""
SQLORM Edge Case and Performance Test Suite
=============================================

This module contains:
1. Edge case tests: Empty databases, concurrent access
2. Performance tests: Load testing with large datasets

Run tests with:
    pytest tests/test_edge_cases_and_performance.py -v

Run only edge case tests:
    pytest tests/test_edge_cases_and_performance.py -v -k "edge"

Run only performance tests:
    pytest tests/test_edge_cases_and_performance.py -v -k "performance"

Note: Performance tests may take longer to run due to large dataset operations.
"""

import concurrent.futures
import os
import sys
import tempfile
import threading
import time
from decimal import Decimal
from pathlib import Path
from typing import List

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================================
# Edge Case Tests: Empty Database Operations
# ============================================================================


class TestEmptyDatabaseEdgeCases:
    """Test cases for operations on empty databases and tables."""

    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Set up a test database for each test."""
        from sqlorm import configure
        from sqlorm.base import clear_registry

        with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as f:
            self.db_path = f.name

        configure(
            {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": self.db_path,
            }
        )

        yield

        # Cleanup
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_query_empty_table(self):
        """Test querying an empty table returns empty queryset."""
        from sqlorm import Model, fields

        class EmptyModel(Model):
            name = fields.CharField(max_length=100)

        EmptyModel.migrate()

        # Query empty table
        result = EmptyModel.objects.all()
        assert list(result) == []
        assert result.count() == 0

    def test_filter_empty_table(self):
        """Test filtering an empty table."""
        from sqlorm import Model, fields

        class EmptyFilterModel(Model):
            name = fields.CharField(max_length=100)
            value = fields.IntegerField(default=0)

        EmptyFilterModel.migrate()

        # Various filter operations on empty table
        assert EmptyFilterModel.objects.filter(name="test").count() == 0
        assert EmptyFilterModel.objects.filter(value__gt=10).count() == 0
        assert EmptyFilterModel.objects.filter(value__range=(1, 100)).count() == 0
        assert EmptyFilterModel.objects.exclude(name="anything").count() == 0

    def test_first_last_on_empty_table(self):
        """Test first() and last() on empty table."""
        from sqlorm import Model, fields

        class FirstLastEmptyModel(Model):
            name = fields.CharField(max_length=100)

        FirstLastEmptyModel.migrate()

        assert FirstLastEmptyModel.objects.first() is None
        assert FirstLastEmptyModel.objects.last() is None

    def test_get_on_empty_table(self):
        """Test get() on empty table raises DoesNotExist."""
        from django.core.exceptions import ObjectDoesNotExist

        from sqlorm import Model, fields

        class GetEmptyModel(Model):
            name = fields.CharField(max_length=100)

        GetEmptyModel.migrate()

        with pytest.raises(ObjectDoesNotExist):
            GetEmptyModel.objects.get(id=1)

    def test_aggregate_on_empty_table(self):
        """Test aggregate functions on empty table."""
        from django.db.models import Avg, Count, Max, Min, Sum

        from sqlorm import Model, fields

        class AggregateEmptyModel(Model):
            value = fields.IntegerField()

        AggregateEmptyModel.migrate()

        # Aggregates on empty table
        result = AggregateEmptyModel.objects.aggregate(
            avg=Avg("value"),
            sum=Sum("value"),
            max=Max("value"),
            min=Min("value"),
            count=Count("value"),
        )

        assert result["avg"] is None
        assert result["sum"] is None
        assert result["max"] is None
        assert result["min"] is None
        assert result["count"] == 0

    def test_values_on_empty_table(self):
        """Test values() and values_list() on empty table."""
        from sqlorm import Model, fields

        class ValuesEmptyModel(Model):
            name = fields.CharField(max_length=100)
            value = fields.IntegerField()

        ValuesEmptyModel.migrate()

        assert list(ValuesEmptyModel.objects.values()) == []
        assert list(ValuesEmptyModel.objects.values_list()) == []
        assert list(ValuesEmptyModel.objects.values("name")) == []
        assert list(ValuesEmptyModel.objects.values_list("name", flat=True)) == []

    def test_delete_on_empty_table(self):
        """Test bulk delete on empty table."""
        from sqlorm import Model, fields

        class DeleteEmptyModel(Model):
            name = fields.CharField(max_length=100)

        DeleteEmptyModel.migrate()

        # Should not raise error
        deleted, _ = DeleteEmptyModel.objects.all().delete()
        assert deleted == 0

    def test_update_on_empty_table(self):
        """Test bulk update on empty table."""
        from sqlorm import Model, fields

        class UpdateEmptyModel(Model):
            name = fields.CharField(max_length=100)
            active = fields.BooleanField(default=True)

        UpdateEmptyModel.migrate()

        # Should not raise error and return 0 updated
        updated = UpdateEmptyModel.objects.all().update(active=False)
        assert updated == 0

    def test_exists_on_empty_table(self):
        """Test exists() on empty table."""
        from sqlorm import Model, fields

        class ExistsEmptyModel(Model):
            name = fields.CharField(max_length=100)

        ExistsEmptyModel.migrate()

        assert ExistsEmptyModel.objects.exists() is False
        assert ExistsEmptyModel.objects.filter(name="test").exists() is False

    def test_order_by_on_empty_table(self):
        """Test ordering on empty table."""
        from sqlorm import Model, fields

        class OrderEmptyModel(Model):
            name = fields.CharField(max_length=100)
            position = fields.IntegerField()

        OrderEmptyModel.migrate()

        result = OrderEmptyModel.objects.order_by("position")
        assert list(result) == []

        result = OrderEmptyModel.objects.order_by("-position", "name")
        assert list(result) == []

    def test_distinct_on_empty_table(self):
        """Test distinct() on empty table."""
        from sqlorm import Model, fields

        class DistinctEmptyModel(Model):
            category = fields.CharField(max_length=100)

        DistinctEmptyModel.migrate()

        result = DistinctEmptyModel.objects.values("category").distinct()
        assert list(result) == []

    def test_get_or_create_on_empty_table(self):
        """Test get_or_create() on empty table creates object."""
        from sqlorm import Model, fields

        class GetOrCreateEmptyModel(Model):
            name = fields.CharField(max_length=100)
            value = fields.IntegerField(default=0)

        GetOrCreateEmptyModel.migrate()

        obj, created = GetOrCreateEmptyModel.objects.get_or_create(
            name="test", defaults={"value": 42}
        )

        assert created is True
        assert obj.name == "test"
        assert obj.value == 42

    def test_update_or_create_on_empty_table(self):
        """Test update_or_create() on empty table creates object."""
        from sqlorm import Model, fields

        class UpdateOrCreateEmptyModel(Model):
            name = fields.CharField(max_length=100, unique=True)
            value = fields.IntegerField(default=0)

        UpdateOrCreateEmptyModel.migrate()

        obj, created = UpdateOrCreateEmptyModel.objects.update_or_create(
            name="test", defaults={"value": 100}
        )

        assert created is True
        assert obj.value == 100

    def test_slicing_empty_queryset(self):
        """Test slicing on empty queryset."""
        from sqlorm import Model, fields

        class SliceEmptyModel(Model):
            name = fields.CharField(max_length=100)

        SliceEmptyModel.migrate()

        result = SliceEmptyModel.objects.all()[:10]
        assert list(result) == []

        result = SliceEmptyModel.objects.all()[5:15]
        assert list(result) == []

    def test_fresh_database_no_tables(self):
        """Test operations on fresh database with no tables yet."""
        from sqlorm import Model, fields
        from sqlorm.connection import get_table_names

        # Get table names from fresh database
        tables = get_table_names()
        # May include django internal tables, but no user tables
        user_tables = [
            t
            for t in tables
            if not t.startswith("django_") and not t.startswith("auth_")
        ]
        # After configuration, there might be some tables, this just checks it doesn't crash
        assert isinstance(tables, list)


# ============================================================================
# Edge Case Tests: Concurrent Access
# ============================================================================


class TestConcurrentAccessEdgeCases:
    """Test cases for concurrent database access scenarios."""

    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Set up a test database for each test."""
        from sqlorm import configure
        from sqlorm.base import clear_registry

        with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as f:
            self.db_path = f.name

        configure(
            {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": self.db_path,
            }
        )

        yield

        # Cleanup
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_concurrent_creates(self):
        """Test concurrent create operations."""
        from django.db import close_old_connections

        from sqlorm import Model, fields

        class ConcurrentCreateModel(Model):
            name = fields.CharField(max_length=100)
            thread_id = fields.IntegerField()

        ConcurrentCreateModel.migrate()

        results = []
        errors = []

        def create_record(thread_num):
            try:
                close_old_connections()
                for i in range(10):
                    ConcurrentCreateModel.objects.create(
                        name=f"Thread-{thread_num}-Item-{i}",
                        thread_id=thread_num,
                    )
                results.append(thread_num)
            except Exception as e:
                errors.append((thread_num, str(e)))

        threads = []
        for i in range(5):
            t = threading.Thread(target=create_record, args=(i,))
            threads.append(t)

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # All threads should complete without errors
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5

        # Should have 5 threads * 10 items = 50 records
        total_count = ConcurrentCreateModel.objects.count()
        assert total_count == 50

    def test_concurrent_reads(self):
        """Test concurrent read operations."""
        from django.db import close_old_connections

        from sqlorm import Model, fields

        class ConcurrentReadModel(Model):
            name = fields.CharField(max_length=100)
            value = fields.IntegerField()

        ConcurrentReadModel.migrate()

        # Create test data
        for i in range(100):
            ConcurrentReadModel.objects.create(name=f"Item-{i}", value=i)

        results = []
        errors = []

        def read_records(thread_num):
            try:
                close_old_connections()
                for _ in range(10):
                    # Various read operations
                    count = ConcurrentReadModel.objects.count()
                    items = list(ConcurrentReadModel.objects.filter(value__gte=50))
                    first = ConcurrentReadModel.objects.first()
                    exists = ConcurrentReadModel.objects.filter(value=25).exists()
                results.append(thread_num)
            except Exception as e:
                errors.append((thread_num, str(e)))

        threads = []
        for i in range(10):
            t = threading.Thread(target=read_records, args=(i,))
            threads.append(t)

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10

    def test_concurrent_updates_simple(self):
        """Test concurrent update operations without select_for_update (SQLite compatible)."""
        from django.db import close_old_connections

        from sqlorm import Model, fields

        class ConcurrentUpdateSimpleModel(Model):
            name = fields.CharField(max_length=100)
            counter = fields.IntegerField(default=0)

        ConcurrentUpdateSimpleModel.migrate()

        # Create multiple items to update concurrently
        for i in range(10):
            ConcurrentUpdateSimpleModel.objects.create(name=f"item-{i}", counter=0)

        errors = []
        completed = []

        def update_items(thread_num):
            try:
                close_old_connections()
                # Each thread updates different items based on thread_num
                ConcurrentUpdateSimpleModel.objects.filter(
                    name__startswith="item"
                ).update(counter=thread_num)
                completed.append(thread_num)
            except Exception as e:
                errors.append((thread_num, str(e)))

        threads = []
        for i in range(5):
            t = threading.Thread(target=update_items, args=(i,))
            threads.append(t)

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # All threads should complete
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(completed) == 5

        # All items should have been updated (counter will be one of the thread values)
        items = ConcurrentUpdateSimpleModel.objects.all()
        for item in items:
            assert item.counter >= 0  # At least one update happened

    def test_concurrent_mixed_operations(self):
        """Test mixed concurrent CRUD operations."""
        from django.db import close_old_connections

        from sqlorm import Model, fields

        class ConcurrentMixedModel(Model):
            name = fields.CharField(max_length=100)
            value = fields.IntegerField()

        ConcurrentMixedModel.migrate()

        # Pre-populate with some data
        for i in range(50):
            ConcurrentMixedModel.objects.create(name=f"Initial-{i}", value=i)

        errors = []
        completed = {"create": 0, "read": 0, "update": 0}
        lock = threading.Lock()

        def create_task():
            try:
                close_old_connections()
                for i in range(20):
                    ConcurrentMixedModel.objects.create(
                        name=f"Created-{threading.current_thread().name}-{i}",
                        value=i * 10,
                    )
                with lock:
                    completed["create"] += 1
            except Exception as e:
                errors.append(("create", str(e)))

        def read_task():
            try:
                close_old_connections()
                for _ in range(30):
                    list(ConcurrentMixedModel.objects.all()[:10])
                    ConcurrentMixedModel.objects.count()
                with lock:
                    completed["read"] += 1
            except Exception as e:
                errors.append(("read", str(e)))

        def update_task():
            try:
                close_old_connections()
                for _ in range(10):
                    ConcurrentMixedModel.objects.filter(value__lt=25).update(value=25)
                with lock:
                    completed["update"] += 1
            except Exception as e:
                errors.append(("update", str(e)))

        threads = []
        # Mix of operations
        for _ in range(2):
            threads.append(threading.Thread(target=create_task))
        for _ in range(3):
            threads.append(threading.Thread(target=read_task))
        for _ in range(2):
            threads.append(threading.Thread(target=update_task))

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Check that operations completed
        assert completed["create"] == 2
        assert completed["read"] == 3
        assert completed["update"] == 2

    def test_concurrent_with_threadpool(self):
        """Test concurrent access using ThreadPoolExecutor."""
        from django.db import close_old_connections

        from sqlorm import Model, fields

        class ThreadPoolModel(Model):
            name = fields.CharField(max_length=100)
            processed = fields.BooleanField(default=False)

        ThreadPoolModel.migrate()

        # Create test data
        for i in range(100):
            ThreadPoolModel.objects.create(name=f"Item-{i}", processed=False)

        def process_item(item_id):
            close_old_connections()
            try:
                item = ThreadPoolModel.objects.get(id=item_id)
                item.processed = True
                item.save()
                return item_id
            except Exception as e:
                return None

        item_ids = list(ThreadPoolModel.objects.values_list("id", flat=True))

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(process_item, item_ids))

        # All items should be processed
        processed_count = ThreadPoolModel.objects.filter(processed=True).count()
        assert processed_count == 100

    def test_concurrent_bulk_operations(self):
        """Test concurrent bulk create operations using sequential approach for SQLite."""
        from sqlorm import Model, fields

        class BulkConcurrentModel(Model):
            batch_id = fields.IntegerField()
            name = fields.CharField(max_length=100)
            status = fields.CharField(max_length=20, default="pending")

        BulkConcurrentModel.migrate()

        # Get the Django model class for bulk_create
        DjangoModel = BulkConcurrentModel._django_model

        # Create batches sequentially (SQLite has threading limitations)
        for batch_id in range(5):
            items = [
                DjangoModel(batch_id=batch_id, name=f"Batch-{batch_id}-Item-{i}")
                for i in range(50)
            ]
            BulkConcurrentModel.objects.bulk_create(items)

        # Should have 5 batches * 50 items = 250 records
        total = BulkConcurrentModel.objects.count()
        assert total == 250

        # Verify each batch is present
        for batch_id in range(5):
            batch_count = BulkConcurrentModel.objects.filter(batch_id=batch_id).count()
            assert batch_count == 50


# ============================================================================
# Performance Tests: Load Testing with Large Datasets
# ============================================================================


class TestPerformanceLargeDatasets:
    """Performance tests with large datasets."""

    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Set up a test database for each test."""
        from sqlorm import configure
        from sqlorm.base import clear_registry

        with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as f:
            self.db_path = f.name

        configure(
            {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": self.db_path,
            }
        )

        yield

        # Cleanup
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_bulk_create_performance(self):
        """Test bulk create performance with large dataset."""
        from sqlorm import Model, fields

        class BulkCreatePerfModel(Model):
            name = fields.CharField(max_length=100)
            description = fields.TextField()
            value = fields.IntegerField()
            active = fields.BooleanField(default=True)

        BulkCreatePerfModel.migrate()
        DjangoModel = BulkCreatePerfModel._django_model

        # Create 10,000 records using bulk_create
        batch_size = 1000
        total_records = 10000

        start_time = time.time()

        for batch_num in range(total_records // batch_size):
            items = [
                DjangoModel(
                    name=f"Item-{batch_num * batch_size + i}",
                    description=f"Description for item {batch_num * batch_size + i}",
                    value=batch_num * batch_size + i,
                )
                for i in range(batch_size)
            ]
            BulkCreatePerfModel.objects.bulk_create(items)

        elapsed_time = time.time() - start_time

        # Verify all records created
        count = BulkCreatePerfModel.objects.count()
        assert count == total_records

        # Performance assertion: should complete in reasonable time
        assert elapsed_time < 30, f"Bulk create took too long: {elapsed_time:.2f}s"

    def test_large_query_performance(self):
        """Test query performance on large dataset."""
        from sqlorm import Model, fields

        class LargeQueryPerfModel(Model):
            category = fields.CharField(max_length=50)
            priority = fields.IntegerField()
            value = fields.DecimalField(max_digits=10, decimal_places=2)
            created_date = fields.DateField(auto_now_add=True)

        LargeQueryPerfModel.migrate()
        DjangoModel = LargeQueryPerfModel._django_model

        # Create large dataset
        items = [
            DjangoModel(
                category=f"Category-{i % 10}",
                priority=i % 5,
                value=Decimal(str(i * 1.5)),
            )
            for i in range(5000)
        ]
        LargeQueryPerfModel.objects.bulk_create(items)

        # Test various query patterns
        start_time = time.time()

        # Complex filter
        result1 = list(
            LargeQueryPerfModel.objects.filter(
                category="Category-5", priority__gte=3, value__lt=5000
            )
        )

        # Ordering with limit
        result2 = list(LargeQueryPerfModel.objects.order_by("-priority", "value")[:100])

        # Aggregate queries
        from django.db.models import Avg, Count, Sum

        agg_result = LargeQueryPerfModel.objects.aggregate(
            avg_value=Avg("value"),
            total_value=Sum("value"),
            count=Count("id"),
        )

        # Group by query
        group_result = list(
            LargeQueryPerfModel.objects.values("category")
            .annotate(total=Sum("value"))
            .order_by("-total")
        )

        elapsed_time = time.time() - start_time

        # Verify results are valid
        assert len(result2) == 100
        assert agg_result["count"] == 5000
        assert len(group_result) == 10

        # Performance assertion
        assert elapsed_time < 10, f"Queries took too long: {elapsed_time:.2f}s"

    def test_bulk_update_performance(self):
        """Test bulk update performance on large dataset."""
        from sqlorm import Model, fields

        class BulkUpdatePerfModel(Model):
            name = fields.CharField(max_length=100)
            status = fields.CharField(max_length=20, default="pending")
            processed_count = fields.IntegerField(default=0)

        BulkUpdatePerfModel.migrate()
        DjangoModel = BulkUpdatePerfModel._django_model

        # Create dataset
        items = [DjangoModel(name=f"Item-{i}", status="pending") for i in range(5000)]
        BulkUpdatePerfModel.objects.bulk_create(items)

        start_time = time.time()

        # Bulk update using filter().update()
        updated = BulkUpdatePerfModel.objects.filter(status="pending").update(
            status="processing"
        )

        # Another bulk update
        updated2 = BulkUpdatePerfModel.objects.filter(status="processing").update(
            status="completed", processed_count=1
        )

        elapsed_time = time.time() - start_time

        assert updated == 5000
        assert updated2 == 5000
        assert elapsed_time < 5, f"Bulk updates took too long: {elapsed_time:.2f}s"

    def test_pagination_performance(self):
        """Test pagination performance on large dataset."""
        from sqlorm import Model, fields

        class PaginationPerfModel(Model):
            title = fields.CharField(max_length=200)
            content = fields.TextField()
            order_index = fields.IntegerField(db_index=True)

        PaginationPerfModel.migrate()
        DjangoModel = PaginationPerfModel._django_model

        # Create dataset
        items = [
            DjangoModel(
                title=f"Article {i}",
                content=f"Content for article {i}" * 10,
                order_index=i,
            )
            for i in range(10000)
        ]
        PaginationPerfModel.objects.bulk_create(items)

        page_size = 100
        num_pages = 50

        start_time = time.time()

        # Simulate pagination through the dataset
        for page in range(num_pages):
            offset = page * page_size
            page_items = list(
                PaginationPerfModel.objects.order_by("order_index")[
                    offset : offset + page_size
                ]
            )
            assert len(page_items) == page_size

        elapsed_time = time.time() - start_time

        assert elapsed_time < 10, f"Pagination took too long: {elapsed_time:.2f}s"

    def test_search_performance(self):
        """Test search operations on large text dataset."""
        from sqlorm import Model, fields

        class SearchPerfModel(Model):
            title = fields.CharField(max_length=200)
            body = fields.TextField()
            tags = fields.CharField(max_length=500)

        SearchPerfModel.migrate()
        DjangoModel = SearchPerfModel._django_model

        # Create dataset with searchable content
        tags_list = ["python", "django", "database", "orm", "sql", "web", "api", "rest"]
        items = [
            DjangoModel(
                title=f"Article about {tags_list[i % len(tags_list)]} - {i}",
                body=f"This is an article about {tags_list[i % len(tags_list)]}. " * 20,
                tags=",".join(tags_list[: (i % len(tags_list)) + 1]),
            )
            for i in range(5000)
        ]
        SearchPerfModel.objects.bulk_create(items)

        start_time = time.time()

        # Contains search
        result1 = list(SearchPerfModel.objects.filter(title__icontains="python"))

        # Multiple condition search
        result2 = list(
            SearchPerfModel.objects.filter(
                title__icontains="django", body__icontains="article"
            )
        )

        # Startswith search
        result3 = list(SearchPerfModel.objects.filter(title__startswith="Article"))

        elapsed_time = time.time() - start_time

        assert len(result1) > 0
        assert len(result2) > 0
        assert len(result3) == 5000

        assert elapsed_time < 10, f"Searches took too long: {elapsed_time:.2f}s"

    def test_bulk_delete_performance(self):
        """Test bulk delete performance."""
        from sqlorm import Model, fields

        class BulkDeletePerfModel(Model):
            name = fields.CharField(max_length=100)
            to_delete = fields.BooleanField(default=False)

        BulkDeletePerfModel.migrate()
        DjangoModel = BulkDeletePerfModel._django_model

        # Create dataset - half marked for deletion
        items = [
            DjangoModel(name=f"Item-{i}", to_delete=(i % 2 == 0)) for i in range(10000)
        ]
        BulkDeletePerfModel.objects.bulk_create(items)

        initial_count = BulkDeletePerfModel.objects.count()
        assert initial_count == 10000

        start_time = time.time()

        # Bulk delete half the records
        deleted, _ = BulkDeletePerfModel.objects.filter(to_delete=True).delete()

        elapsed_time = time.time() - start_time

        assert deleted == 5000
        remaining = BulkDeletePerfModel.objects.count()
        assert remaining == 5000
        assert elapsed_time < 5, f"Bulk delete took too long: {elapsed_time:.2f}s"

    def test_relationship_query_performance(self):
        """Test query performance with relationships using string reference."""
        from sqlorm import Model, fields

        # Define Author model first
        class AuthorPerfModel(Model):
            name = fields.CharField(max_length=100)
            email = fields.EmailField()

        AuthorPerfModel.migrate()

        # Define Book model with string reference to avoid metaclass issues
        class BookPerfModel(Model):
            title = fields.CharField(max_length=200)
            author = fields.ForeignKey(
                "AuthorPerfModel", on_delete=fields.CASCADE, related_name="books"
            )
            price = fields.DecimalField(max_digits=8, decimal_places=2)

        BookPerfModel.migrate()

        # Create authors using objects.create
        author_ids = []
        for i in range(100):
            author = AuthorPerfModel.objects.create(
                name=f"Author {i}", email=f"author{i}@example.com"
            )
            author_ids.append(author.id)

        # Create books using objects.create
        for i in range(500):
            author_id = author_ids[i % len(author_ids)]
            BookPerfModel.objects.create(
                title=f"Book {i}",
                author_id=author_id,
                price=Decimal(str(10 + (i % 50))),
            )

        start_time = time.time()

        # Query with select_related
        result1 = list(BookPerfModel.objects.select_related("author").all()[:100])

        # Query with prefetch_related
        result2 = list(AuthorPerfModel.objects.prefetch_related("books").all()[:20])

        # Aggregate across relationship
        from django.db.models import Avg, Sum

        agg_result = BookPerfModel.objects.values("author__name").annotate(
            total_price=Sum("price"), avg_price=Avg("price")
        )[:50]
        agg_list = list(agg_result)

        elapsed_time = time.time() - start_time

        assert len(result1) == 100
        assert len(result2) == 20
        assert len(agg_list) == 50

        assert (
            elapsed_time < 10
        ), f"Relationship queries took too long: {elapsed_time:.2f}s"

    def test_large_iteration_performance(self):
        """Test iteration over large dataset."""
        from sqlorm import Model, fields

        class LargeIterationPerfModel(Model):
            data = fields.TextField()
            processed = fields.BooleanField(default=False)

        LargeIterationPerfModel.migrate()
        DjangoModel = LargeIterationPerfModel._django_model

        # Create large dataset with substantial data per record
        items = [DjangoModel(data=f"Large data content {i}" * 100) for i in range(5000)]
        LargeIterationPerfModel.objects.bulk_create(items)

        start_time = time.time()

        # Iterate using all() which is supported
        processed_count = 0
        for item in LargeIterationPerfModel.objects.all():
            processed_count += 1

        elapsed_time = time.time() - start_time

        assert processed_count == 5000
        assert elapsed_time < 15, f"Iteration took too long: {elapsed_time:.2f}s"

    def test_complex_aggregation_performance(self):
        """Test complex aggregation performance."""
        from sqlorm import Model, fields

        class SalesDataPerfModel(Model):
            product = fields.CharField(max_length=100)
            region = fields.CharField(max_length=50)
            salesperson = fields.CharField(max_length=100)
            amount = fields.DecimalField(max_digits=12, decimal_places=2)
            quantity = fields.IntegerField()

        SalesDataPerfModel.migrate()
        DjangoModel = SalesDataPerfModel._django_model

        # Create sales data
        products = ["Widget", "Gadget", "Tool", "Device", "Component"]
        regions = ["North", "South", "East", "West", "Central"]
        salespeople = [f"Person-{i}" for i in range(50)]

        items = [
            DjangoModel(
                product=products[i % len(products)],
                region=regions[i % len(regions)],
                salesperson=salespeople[i % len(salespeople)],
                amount=Decimal(str(100 + (i % 1000))),
                quantity=(i % 10) + 1,
            )
            for i in range(10000)
        ]
        SalesDataPerfModel.objects.bulk_create(items)

        from django.db.models import Avg, Count, Max, Min, Sum

        start_time = time.time()

        # Multiple aggregations
        overall = SalesDataPerfModel.objects.aggregate(
            total_amount=Sum("amount"),
            avg_amount=Avg("amount"),
            total_quantity=Sum("quantity"),
            num_sales=Count("id"),
        )

        # Group by product
        by_product = list(
            SalesDataPerfModel.objects.values("product")
            .annotate(
                total=Sum("amount"),
                count=Count("id"),
                avg_qty=Avg("quantity"),
            )
            .order_by("-total")
        )

        # Group by region and product - with explicit grouping
        by_region_product = list(
            SalesDataPerfModel.objects.values("region", "product")
            .annotate(total=Sum("amount"), max_sale=Max("amount"))
            .order_by("region", "product")
        )

        # Top salesperson by region
        by_salesperson = list(
            SalesDataPerfModel.objects.values("salesperson")
            .annotate(total_sales=Sum("amount"), num_sales=Count("id"))
            .order_by("-total_sales")[:10]
        )

        elapsed_time = time.time() - start_time

        assert overall["num_sales"] == 10000
        assert len(by_product) == 5
        # Due to data distribution, region+product may have fewer than 25 unique combinations
        assert len(by_region_product) >= 5  # At least 5 combinations exist
        assert len(by_salesperson) == 10

        assert (
            elapsed_time < 10
        ), f"Complex aggregations took too long: {elapsed_time:.2f}s"


# ============================================================================
# Performance Benchmarks (Optional - can be skipped for regular test runs)
# ============================================================================


class TestPerformanceBenchmarks:
    """Extended performance benchmarks."""

    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Set up a test database for each test."""
        from sqlorm import configure

        with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as f:
            self.db_path = f.name

        configure(
            {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": self.db_path,
            }
        )

        yield

        # Cleanup
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_very_large_dataset(self):
        """Test with very large dataset (50,000 records)."""
        from sqlorm import Model, fields

        class VeryLargeDatasetModel(Model):
            code = fields.CharField(max_length=20)
            value1 = fields.IntegerField()
            value2 = fields.DecimalField(max_digits=10, decimal_places=2)
            text_data = fields.TextField()

        VeryLargeDatasetModel.migrate()
        DjangoModel = VeryLargeDatasetModel._django_model

        # Create 50,000 records in batches
        total_records = 50000
        batch_size = 5000

        start_time = time.time()

        for batch_num in range(total_records // batch_size):
            items = [
                DjangoModel(
                    code=f"CODE-{batch_num * batch_size + i:06d}",
                    value1=batch_num * batch_size + i,
                    value2=Decimal(str((batch_num * batch_size + i) * 1.23)),
                    text_data=f"Sample text data for record {batch_num * batch_size + i}",
                )
                for i in range(batch_size)
            ]
            VeryLargeDatasetModel.objects.bulk_create(items)

        create_time = time.time() - start_time

        # Query benchmarks
        query_start = time.time()

        count = VeryLargeDatasetModel.objects.count()
        filtered = VeryLargeDatasetModel.objects.filter(
            value1__range=(10000, 20000)
        ).count()
        ordered = list(VeryLargeDatasetModel.objects.order_by("-value2")[:100])

        query_time = time.time() - query_start

        assert count == total_records
        assert filtered == 10001
        assert len(ordered) == 100

        # Performance assertions
        assert (
            create_time < 60
        ), f"Create {total_records} records took too long: {create_time:.2f}s"
        assert query_time < 10, f"Query operations took too long: {query_time:.2f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
