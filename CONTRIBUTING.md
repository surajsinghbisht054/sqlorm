# Contributing to SQLORM

Thank you for your interest in contributing to SQLORM! This document provides guidelines and instructions for contributing.

## 🚀 Quick Start

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/sqlorm.git
   cd sqlorm
   ```

2. **Set up development environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

3. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/test_sqlorm.py -v

# Run with coverage
pytest tests/test_sqlorm.py --cov=sqlorm --cov-report=html

# Run specific test class
pytest tests/test_sqlorm.py::TestSerialization -v

# Run multi-database tests (requires fresh process)
pytest tests/test_multi_database.py -v
```

## 📝 Code Style

We use the following tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

Run these manually:
```bash
black sqlorm
isort sqlorm
flake8 sqlorm
mypy sqlorm --ignore-missing-imports
```

Or let pre-commit handle it automatically on commit.

## 📦 Making Changes

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation changes
- `refactor/description` - Code refactoring

### Commit Messages

Follow conventional commits format:
```
type(scope): description

[optional body]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
```
feat(model): add to_dict serialization method
fix(connection): handle connection timeout properly
docs(readme): add serialization examples
```

## 🔧 Development Guidelines

### Adding New Features

1. **Write tests first** - Add tests in `tests/test_sqlorm.py`
2. **Update documentation** - Add docstrings and update README if needed
3. **Update CHANGELOG** - Add entry under "Unreleased" section

### Code Requirements

- All public functions/methods must have docstrings
- Type hints are encouraged for function parameters and returns
- Keep backward compatibility in mind
- Follow Django ORM conventions where applicable

### Exception Handling

When raising exceptions, use the appropriate exception class:
```python
from sqlorm.exceptions import ConfigurationError, ModelError, MigrationError

raise ConfigurationError(
    "Missing required key",
    missing_keys=["ENGINE"],
    hint="Add 'ENGINE' key to your configuration"
)
```

## 🔍 Pull Request Process

1. **Ensure all tests pass**
2. **Update documentation** if needed
3. **Add entry to CHANGELOG.md**
4. **Request review** from maintainers

### PR Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] CHANGELOG entry added
- [ ] Code follows style guidelines
- [ ] No breaking changes (or clearly documented)

## 📚 Project Structure

```
sqlorm/
├── __init__.py      # Package exports
├── base.py          # Model class and QuerySet wrappers
├── config.py        # Configuration utilities
├── connection.py    # Database connection utilities
├── exceptions.py    # Custom exceptions
├── fields.py        # Field proxy for Django fields
└── py.typed         # PEP 561 type marker

tests/
├── test_sqlorm.py        # Main test suite
└── test_multi_database.py # Multi-database tests
```

## 💬 Getting Help

- Open an issue for bugs or feature requests
- Start a discussion for questions
- Tag `@surajsinghbisht054` for urgent matters

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.
