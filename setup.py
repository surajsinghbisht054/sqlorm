"""
SQLORM - Django ORM for Standalone Python Scripts
==================================================

A lightweight wrapper that brings Django's powerful, battle-tested ORM
to standalone Python scripts without requiring a full Django project.

Installation:
    pip install sqlorm

Quick Start:
    from sqlorm import configure, Model, fields
    
    configure({
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'mydb.sqlite3',
    })
    
    class User(Model):
        name = fields.CharField(max_length=100)
        email = fields.EmailField(unique=True)
    
    User.migrate()
    user = User.objects.create(name="John", email="john@example.com")

For more information, visit: https://github.com/surajsinghbisht054/sqlorm
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="sqlorm",
    version="2.0.0",
    author="S.S.B",
    author_email="surajsinghbisht054@gmail.com",
    description="Django ORM for standalone Python scripts - Use Django's powerful ORM without a full Django project",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/surajsinghbisht054/sqlorm",
    project_urls={
        "Bug Tracker": "https://github.com/surajsinghbisht054/sqlorm/issues",
        "Documentation": "https://github.com/surajsinghbisht054/sqlorm#readme",
        "Source Code": "https://github.com/surajsinghbisht054/sqlorm",
    },
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Database",
        "Topic :: Database :: Front-Ends",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Framework :: Django",
    ],
    python_requires=">=3.8",
    install_requires=[
        "Django>=3.2",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=23.0",
            "isort>=5.0",
            "flake8>=6.0",
            "mypy>=1.0",
        ],
        "postgresql": [
            "psycopg2-binary>=2.9",
        ],
        "mysql": [
            "mysqlclient>=2.1",
        ],
        "yaml": [
            "pyyaml>=6.0",
        ],
    },
    keywords=[
        "django",
        "orm",
        "database",
        "sql",
        "sqlite",
        "postgresql",
        "mysql",
        "standalone",
        "script",
        "models",
    ],
    include_package_data=True,
    zip_safe=False,
)
