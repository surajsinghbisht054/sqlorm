"""
SQLORM Migration Test Suite
============================

Test cases for schema migrations and column structure changes.

Migrations in SQLORM:
- SQLORM uses Django's schema_editor for DDL operations
- Initial table creation is fully supported
- Column additions are supported via add_column()
- Column modifications require manual ALTER statements or recreating tables
- For complex migrations, use execute_raw_sql() for direct DDL

Run tests with:
    pytest tests/test_migrations.py -v
"""

import os
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestBasicMigrations:
    """Test cases for basic table creation migrations."""

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

    def test_initial_table_creation(self):
        """Test that migrate() creates a new table."""
        from sqlorm import Model, fields

        class MigrationTest1(Model):
            name = fields.CharField(max_length=100)
            value = fields.IntegerField()

        # Table should not exist initially
        assert not MigrationTest1.table_exists()

        # Migrate should create the table
        MigrationTest1.migrate()

        # Table should now exist
        assert MigrationTest1.table_exists()

    def test_migrate_idempotent(self):
        """Test that migrate() can be called multiple times safely."""
        from sqlorm import Model, fields

        class MigrationTest2(Model):
            name = fields.CharField(max_length=100)

        # First migration
        MigrationTest2.migrate()
        assert MigrationTest2.table_exists()

        # Second migration should not raise an error
        MigrationTest2.migrate()
        assert MigrationTest2.table_exists()

        # Should still be able to use the model
        obj = MigrationTest2.objects.create(name="Test")
        assert obj.id is not None

    def test_table_exists_check(self):
        """Test the table_exists() method."""
        from sqlorm import Model, fields

        class MigrationTest3(Model):
            title = fields.CharField(max_length=200)

        # Before migration
        assert MigrationTest3.table_exists() is False

        # After migration
        MigrationTest3.migrate()
        assert MigrationTest3.table_exists() is True

    def test_automatic_column_addition(self):
        """Test that migrate() automatically adds missing columns."""
        from sqlorm import Model, fields
        from sqlorm.base import get_table_columns

        # Define initial model
        class AutoMigrateTest(Model):
            name = fields.CharField(max_length=100)

        # Create table
        AutoMigrateTest.migrate()
        assert AutoMigrateTest.table_exists()

        # Verify columns
        columns = get_table_columns(AutoMigrateTest.get_table_name())
        assert "name" in columns
        assert "age" not in columns

        # Define updated model with same table name
        class AutoMigrateTestUpdated(Model):
            name = fields.CharField(max_length=100)
            age = fields.IntegerField(default=0)

            class Meta:
                db_table = AutoMigrateTest.get_table_name()

        # Run migrate again
        AutoMigrateTestUpdated.migrate()

        # Verify new column exists
        columns = get_table_columns(AutoMigrateTest.get_table_name())
        assert "name" in columns
        assert "age" in columns

    def test_drop_table(self):
        """Test dropping a table."""
        from sqlorm import Model, fields
        from sqlorm.exceptions import ModelError

        class MigrationTest4(Model):
            data = fields.TextField()

        MigrationTest4.migrate()
        assert MigrationTest4.table_exists()

        # Without confirm should raise error
        with pytest.raises(ModelError) as exc_info:
            MigrationTest4.drop_table()
        assert "confirm=True" in str(exc_info.value)

        # With confirm should drop table
        MigrationTest4.drop_table(confirm=True)
        assert not MigrationTest4.table_exists()

    def test_get_table_name(self):
        """Test getting the table name."""
        from sqlorm import Model, fields

        class MigrationTest5(Model):
            field1 = fields.CharField(max_length=50)

        MigrationTest5.migrate()

        table_name = MigrationTest5.get_table_name()
        assert "migrationtest5" in table_name.lower()

    def test_get_fields(self):
        """Test getting model fields."""
        from sqlorm import Model, fields

        class MigrationTest6(Model):
            name = fields.CharField(max_length=100)
            age = fields.IntegerField()
            active = fields.BooleanField(default=True)

        MigrationTest6.migrate()

        field_names = MigrationTest6.get_fields()
        assert "id" in field_names  # Auto-generated PK
        assert "name" in field_names
        assert "age" in field_names
        assert "active" in field_names


class TestColumnAdditions:
    """Test cases for adding new columns to existing tables."""

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

        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_add_column_with_default(self):
        """Test adding a new column with a default value."""
        from sqlorm import Model, execute_raw_sql, fields
        from sqlorm.base import add_column

        # First, create initial table with raw SQL
        execute_raw_sql(
            """
            CREATE TABLE add_column_test1 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL
            )
        """,
            fetch=False,
        )

        # Insert some data
        execute_raw_sql(
            "INSERT INTO add_column_test1 (name) VALUES (?)",
            ["Original Row"],
            fetch=False,
        )

        # Add a new column with default value
        add_column(
            table_name="add_column_test1",
            column_name="status",
            column_type="VARCHAR(50)",
            default="'pending'",
        )

        # Verify the column was added and default applied
        result = execute_raw_sql("SELECT name, status FROM add_column_test1")
        assert len(result) == 1
        assert result[0][0] == "Original Row"
        assert result[0][1] == "pending"

    def test_add_nullable_column(self):
        """Test adding a new nullable column."""
        from sqlorm import execute_raw_sql
        from sqlorm.base import add_column

        # Create initial table
        execute_raw_sql(
            """
            CREATE TABLE add_column_test2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL
            )
        """,
            fetch=False,
        )

        # Insert data
        execute_raw_sql(
            "INSERT INTO add_column_test2 (name) VALUES (?)", ["Row 1"], fetch=False
        )

        # Add nullable column
        add_column(
            table_name="add_column_test2",
            column_name="description",
            column_type="TEXT",
            nullable=True,
        )

        # Verify existing data has NULL for new column
        result = execute_raw_sql("SELECT name, description FROM add_column_test2")
        assert result[0][1] is None

        # Insert new data with value
        execute_raw_sql(
            "INSERT INTO add_column_test2 (name, description) VALUES (?, ?)",
            ["Row 2", "Has description"],
            fetch=False,
        )

        result = execute_raw_sql("SELECT * FROM add_column_test2 ORDER BY id")
        assert len(result) == 2
        assert result[1][2] == "Has description"

    def test_add_integer_column(self):
        """Test adding an integer column."""
        from sqlorm import execute_raw_sql
        from sqlorm.base import add_column

        execute_raw_sql(
            """
            CREATE TABLE add_column_test3 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100)
            )
        """,
            fetch=False,
        )

        execute_raw_sql(
            "INSERT INTO add_column_test3 (name) VALUES (?)", ["Test"], fetch=False
        )

        add_column(
            table_name="add_column_test3",
            column_name="count",
            column_type="INTEGER",
            default="0",
        )

        result = execute_raw_sql("SELECT name, count FROM add_column_test3")
        assert result[0][1] == 0


class TestSchemaChanges:
    """Test cases for handling schema changes and modifications."""

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

        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_rename_column_sqlite(self):
        """Test renaming a column in SQLite."""
        from sqlorm import execute_raw_sql
        from sqlorm.base import rename_column

        # Create table with original column
        execute_raw_sql(
            """
            CREATE TABLE rename_test (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                old_name VARCHAR(100)
            )
        """,
            fetch=False,
        )

        execute_raw_sql(
            "INSERT INTO rename_test (old_name) VALUES (?)", ["Test Value"], fetch=False
        )

        # Rename the column
        rename_column(
            table_name="rename_test",
            old_column_name="old_name",
            new_column_name="new_name",
        )

        # Verify data is preserved under new column name
        result = execute_raw_sql("SELECT new_name FROM rename_test")
        assert result[0][0] == "Test Value"

    def test_detect_schema_differences(self):
        """Test detecting differences between model and table schema."""
        from sqlorm import Model, execute_raw_sql, fields
        from sqlorm.base import get_schema_diff

        # Create a table manually with fewer columns
        execute_raw_sql(
            """
            CREATE TABLE schema_diff_test (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100)
            )
        """,
            fetch=False,
        )

        # Define a model with more columns
        class SchemaDiffTest(Model):
            _db_table = "schema_diff_test"
            name = fields.CharField(max_length=100)
            email = fields.EmailField()  # New column
            age = fields.IntegerField(default=0)  # New column

        SchemaDiffTest._create_django_model()

        # Get schema differences
        diff = get_schema_diff(SchemaDiffTest)

        # Should detect missing columns
        assert "missing_in_db" in diff
        assert "email" in diff["missing_in_db"] or len(diff["missing_in_db"]) > 0

    def test_sync_schema_adds_columns(self):
        """Test that sync_schema adds missing columns."""
        from sqlorm import Model, execute_raw_sql, fields
        from sqlorm.base import sync_schema

        # Create initial table
        execute_raw_sql(
            """
            CREATE TABLE sync_test (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL
            )
        """,
            fetch=False,
        )

        # Insert data
        execute_raw_sql(
            "INSERT INTO sync_test (name) VALUES (?)", ["Original"], fetch=False
        )

        # Define model with additional columns
        class SyncTest(Model):
            _db_table = "sync_test"
            name = fields.CharField(max_length=100)
            status = fields.CharField(max_length=50, default="active")

        SyncTest._create_django_model()

        # Sync the schema
        sync_schema(SyncTest)

        # Verify new column was added
        result = execute_raw_sql("SELECT name, status FROM sync_test")
        assert len(result) == 1
        # Existing row should have default value or NULL


class TestMigrationEdgeCases:
    """Test edge cases and error handling in migrations."""

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

        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_recreate_table_with_data_preservation(self):
        """Test recreating a table while preserving data."""
        from sqlorm import execute_raw_sql
        from sqlorm.base import recreate_table

        # Create original table
        execute_raw_sql(
            """
            CREATE TABLE recreate_test (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100),
                old_field VARCHAR(50)
            )
        """,
            fetch=False,
        )

        # Insert data
        execute_raw_sql(
            "INSERT INTO recreate_test (name, old_field) VALUES (?, ?)",
            ["Test 1", "old_value"],
            fetch=False,
        )
        execute_raw_sql(
            "INSERT INTO recreate_test (name, old_field) VALUES (?, ?)",
            ["Test 2", "old_value_2"],
            fetch=False,
        )

        # Recreate table with new schema (removing old_field, adding new_field)
        new_schema = """
            CREATE TABLE recreate_test (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100),
                new_field VARCHAR(50) DEFAULT 'default_value'
            )
        """

        recreate_table(
            table_name="recreate_test",
            new_schema=new_schema,
            columns_to_copy=["id", "name"],
        )

        # Verify data preserved
        result = execute_raw_sql(
            "SELECT id, name, new_field FROM recreate_test ORDER BY id"
        )
        assert len(result) == 2
        assert result[0][1] == "Test 1"
        assert result[0][2] == "default_value"
        assert result[1][1] == "Test 2"

    def test_migration_with_foreign_key(self):
        """Test migration with foreign key relationships."""
        from sqlorm import Model, fields

        class FKParent(Model):
            name = fields.CharField(max_length=100)

        # Migrate parent first
        FKParent.migrate()
        assert FKParent.table_exists()

        class FKChild(Model):
            name = fields.CharField(max_length=100)
            parent = fields.ForeignKey(
                "FKParent", on_delete=fields.CASCADE, null=True  # Use string reference
            )

        # Then migrate child
        FKChild.migrate()

        # Both tables should exist
        assert FKChild.table_exists()

        # Create and link records
        parent = FKParent.objects.create(name="Parent")
        child = FKChild.objects.create(name="Child", parent=parent)

        # Verify relationship
        assert child.parent.id == parent.id

    def test_handle_data_type_changes(self):
        """Test handling data type changes via table recreation."""
        from sqlorm import execute_raw_sql
        from sqlorm.base import change_column_type

        # Create table with VARCHAR column
        execute_raw_sql(
            """
            CREATE TABLE type_change_test (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount VARCHAR(50)
            )
        """,
            fetch=False,
        )

        # Insert string data that looks like numbers
        execute_raw_sql(
            "INSERT INTO type_change_test (amount) VALUES (?)", ["100"], fetch=False
        )
        execute_raw_sql(
            "INSERT INTO type_change_test (amount) VALUES (?)", ["200"], fetch=False
        )

        # Change column type from VARCHAR to INTEGER
        change_column_type(
            table_name="type_change_test", column_name="amount", new_type="INTEGER"
        )

        # Verify data conversion
        result = execute_raw_sql("SELECT id, amount FROM type_change_test ORDER BY id")
        assert result[0][1] == 100  # Should now be integer
        assert result[1][1] == 200

    def test_migration_verbosity(self):
        """Test migration with different verbosity levels."""
        import logging

        from sqlorm import Model, fields

        class VerbosityTest(Model):
            name = fields.CharField(max_length=100)

        # Test silent migration
        VerbosityTest.migrate(verbosity=0)
        assert VerbosityTest.table_exists()

    def test_migrate_all_models(self):
        """Test migrating all registered models at once."""
        from sqlorm import Model, fields
        from sqlorm.base import create_all_tables, migrate_all

        class MigrateAll1(Model):
            field1 = fields.CharField(max_length=50)

        class MigrateAll2(Model):
            field2 = fields.IntegerField()

        # Migrate all
        migrate_all(verbosity=0)

        # Both should exist
        assert MigrateAll1.table_exists()
        assert MigrateAll2.table_exists()


class TestDataPreservation:
    """Test cases ensuring data is preserved during migrations."""

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

        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_data_preserved_on_remigrate(self):
        """Test that data is preserved when migrate() is called again."""
        from sqlorm import Model, fields

        class DataPreserve(Model):
            name = fields.CharField(max_length=100)
            value = fields.IntegerField(default=0)

        # First migration
        DataPreserve.migrate()

        # Insert data
        DataPreserve.objects.create(name="Item 1", value=10)
        DataPreserve.objects.create(name="Item 2", value=20)

        # Call migrate again
        DataPreserve.migrate()

        # Data should still be there
        assert DataPreserve.objects.count() == 2
        assert DataPreserve.objects.get(name="Item 1").value == 10

    def test_backup_and_restore_table(self):
        """Test backing up and restoring a table."""
        from sqlorm import execute_raw_sql
        from sqlorm.base import backup_table, restore_table

        # Create and populate table
        execute_raw_sql(
            """
            CREATE TABLE backup_test (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data VARCHAR(100)
            )
        """,
            fetch=False,
        )

        execute_raw_sql(
            "INSERT INTO backup_test (data) VALUES (?)", ["Important Data"], fetch=False
        )

        # Backup table
        backup_table("backup_test")

        # Verify backup exists
        backup_result = execute_raw_sql("SELECT * FROM backup_test_backup")
        assert len(backup_result) == 1
        assert backup_result[0][1] == "Important Data"

        # Drop original
        execute_raw_sql("DROP TABLE backup_test", fetch=False)

        # Restore from backup
        restore_table("backup_test")

        # Verify restoration
        result = execute_raw_sql("SELECT * FROM backup_test")
        assert len(result) == 1
        assert result[0][1] == "Important Data"


class TestMigrationUtilities:
    """Test cases for migration utility functions."""

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

        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_get_table_columns(self):
        """Test getting columns from a table."""
        from sqlorm import execute_raw_sql
        from sqlorm.base import get_table_columns

        execute_raw_sql(
            """
            CREATE TABLE columns_test (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100),
                age INTEGER,
                email VARCHAR(200)
            )
        """,
            fetch=False,
        )

        columns = get_table_columns("columns_test")

        # Should return column names
        assert "id" in columns
        assert "name" in columns
        assert "age" in columns
        assert "email" in columns

    def test_column_exists(self):
        """Test checking if a column exists."""
        from sqlorm import execute_raw_sql
        from sqlorm.base import column_exists

        execute_raw_sql(
            """
            CREATE TABLE column_exists_test (
                id INTEGER PRIMARY KEY,
                existing_column VARCHAR(100)
            )
        """,
            fetch=False,
        )

        assert column_exists("column_exists_test", "existing_column") is True
        assert column_exists("column_exists_test", "nonexistent_column") is False

    def test_safe_add_column(self):
        """Test adding a column only if it doesn't exist."""
        from sqlorm import execute_raw_sql
        from sqlorm.base import safe_add_column

        execute_raw_sql(
            """
            CREATE TABLE safe_add_test (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100)
            )
        """,
            fetch=False,
        )

        # Add column first time - should succeed
        result1 = safe_add_column(
            table_name="safe_add_test", column_name="new_col", column_type="VARCHAR(50)"
        )
        assert result1 is True

        # Add same column again - should be skipped (no error)
        result2 = safe_add_column(
            table_name="safe_add_test", column_name="new_col", column_type="VARCHAR(50)"
        )
        assert result2 is False  # Already exists, not added


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
