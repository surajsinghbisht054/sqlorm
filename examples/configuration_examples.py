#!/usr/bin/env python3
"""
SQLORM Configuration Examples
==============================

This file demonstrates various ways to configure SQLORM for different
database backends and deployment scenarios.
"""

print("=" * 60)
print("SQLORM Configuration Examples")
print("=" * 60)

# ============================================================================
# Example 1: Simple SQLite Configuration
# ============================================================================

def example_sqlite():
    """The simplest configuration - SQLite database."""
    from sqlorm import configure
    
    configure({
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'my_database.sqlite3',
    })
    print("✅ SQLite configured: my_database.sqlite3")


# ============================================================================
# Example 2: In-Memory SQLite (Great for Testing)
# ============================================================================

def example_sqlite_memory():
    """In-memory SQLite database - perfect for tests."""
    from sqlorm import configure
    
    configure({
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # In-memory database
    })
    print("✅ In-memory SQLite configured")


# ============================================================================
# Example 3: PostgreSQL Configuration
# ============================================================================

def example_postgresql():
    """PostgreSQL database configuration."""
    from sqlorm import configure
    
    configure({
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'myapp_db',
        'USER': 'postgres',
        'PASSWORD': 'secretpassword',
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'connect_timeout': 10,
        },
    })
    print("✅ PostgreSQL configured")


# ============================================================================
# Example 4: MySQL Configuration
# ============================================================================

def example_mysql():
    """MySQL database configuration."""
    from sqlorm import configure
    
    configure({
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'myapp_db',
        'USER': 'root',
        'PASSWORD': 'secretpassword',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    })
    print("✅ MySQL configured")


# ============================================================================
# Example 5: Configuration from Environment Variables
# ============================================================================

def example_environment_variables():
    """Configure from environment variables."""
    import os
    from sqlorm.config import configure_from_env
    
    # Set environment variables (in production, these would be pre-set)
    os.environ['DATABASE_URL'] = 'postgres://user:pass@localhost:5432/myapp'
    
    # Or individual variables:
    # os.environ['SQLORM_DB_ENGINE'] = 'django.db.backends.postgresql'
    # os.environ['SQLORM_DB_NAME'] = 'myapp_db'
    # os.environ['SQLORM_DB_USER'] = 'postgres'
    # os.environ['SQLORM_DB_PASSWORD'] = 'password'
    # os.environ['SQLORM_DB_HOST'] = 'localhost'
    # os.environ['SQLORM_DB_PORT'] = '5432'
    
    configure_from_env()
    print("✅ Configured from environment variables")


# ============================================================================
# Example 6: Configuration from JSON File
# ============================================================================

def example_json_file():
    """Configure from a JSON configuration file."""
    import json
    import tempfile
    from sqlorm import configure_from_file
    
    # Create a sample config file
    config = {
        "database": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": "from_json.sqlite3"
        },
        "debug": True,
        "time_zone": "America/New_York"
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f)
        config_path = f.name
    
    configure_from_file(config_path)
    print(f"✅ Configured from JSON file: {config_path}")


# ============================================================================
# Example 7: Configuration from YAML File
# ============================================================================

def example_yaml_file():
    """Configure from a YAML configuration file."""
    import tempfile
    from sqlorm import configure_from_file
    
    yaml_content = """
database:
  ENGINE: django.db.backends.sqlite3
  NAME: from_yaml.sqlite3

debug: true
time_zone: UTC
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        config_path = f.name
    
    # Note: Requires pyyaml: pip install pyyaml
    configure_from_file(config_path)
    print(f"✅ Configured from YAML file: {config_path}")


# ============================================================================
# Example 8: Configuration from Dictionary
# ============================================================================

def example_from_dict():
    """Configure from a dictionary (useful for programmatic config)."""
    from sqlorm import configure_from_dict
    
    config = {
        "database": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": "from_dict.sqlite3"
        },
        "debug": True,
        "time_zone": "Europe/London",
        "use_tz": True,
    }
    
    configure_from_dict(config)
    print("✅ Configured from dictionary")


# ============================================================================
# Example 9: Full Configuration with All Options
# ============================================================================

def example_full_configuration():
    """Comprehensive configuration with all available options."""
    from sqlorm import configure
    
    configure(
        database={
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'production_db',
            'USER': 'app_user',
            'PASSWORD': 'secure_password_here',
            'HOST': 'db.example.com',
            'PORT': '5432',
            'CONN_MAX_AGE': 600,  # Connection pooling
            'OPTIONS': {
                'connect_timeout': 10,
                'sslmode': 'require',  # Require SSL
            },
        },
        alias='default',          # Database alias
        debug=False,              # Django debug mode
        time_zone='UTC',          # Time zone
        use_tz=True,              # Timezone-aware datetimes
        auto_field='django.db.models.BigAutoField',  # Primary key type
        
        # Additional Django settings can be passed as kwargs
        CONN_HEALTH_CHECKS=True,
        DATA_UPLOAD_MAX_MEMORY_SIZE=10 * 1024 * 1024,  # 10MB
    )
    print("✅ Full configuration applied")


# ============================================================================
# Example 10: Production-Ready Configuration Pattern
# ============================================================================

def example_production_pattern():
    """
    Production-ready configuration pattern with environment-based settings.
    """
    import os
    from sqlorm import configure
    
    # Determine environment
    ENV = os.environ.get('APP_ENV', 'development')
    
    # Base configuration
    config = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'dev.sqlite3',
    }
    
    # Environment-specific overrides
    if ENV == 'production':
        config = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'production_db'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
            'CONN_MAX_AGE': 600,
        }
    elif ENV == 'testing':
        config = {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    
    configure(
        database=config,
        debug=(ENV == 'development'),
        time_zone='UTC',
    )
    print(f"✅ Configured for {ENV} environment")


# ============================================================================
# Run Examples
# ============================================================================

if __name__ == "__main__":
    print("\nRunning Example 1: SQLite")
    example_sqlite()
    
    print("\n" + "-" * 60)
    print("Other examples are documented but not run to avoid conflicts.")
    print("Uncomment and run individually as needed.")
    print("-" * 60)
    
    # Uncomment to run other examples:
    # example_sqlite_memory()
    # example_postgresql()
    # example_mysql()
    # example_environment_variables()
    # example_json_file()
    # example_yaml_file()
    # example_from_dict()
    # example_full_configuration()
    # example_production_pattern()
    
    print("\n🎉 Configuration examples complete!")
