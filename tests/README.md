# Eleventa Test Suite

This directory contains tests for the eleventa application.

## Test Structure

- `core/`: Unit tests for core business logic
- `infrastructure/`: Tests for database and external systems
- `ui/`: Tests for the user interface components
- `integration/`: Integration tests for multiple components working together

## Setting Up for Testing

Install the required test dependencies:

```bash
pip install -r requirements-test.txt
```

## Running Tests

### Running All Tests

```bash
python -m pytest
```

### Running Specific Test Categories

```bash
# Run all integration tests
python -m pytest integration/

# Run all UI tests
python -m pytest ui/

# Run all infrastructure tests
python -m pytest infrastructure/

# Run all core tests
python -m pytest core/
```

### Running with Verbosity

```bash
python -m pytest -v
```

### Running with Coverage Report

```bash
python -m pytest --cov=. --cov-report=html
```

## Automated UI Testing

This project uses pytest-qt to test UI components without manual intervention. This allows:

1. Testing login without manual input
2. Testing UI components programmatically
3. Running integration tests in a CI/CD environment

### Example: Running UI Tests

```bash
python -m pytest ui/test_login.py -v
```

## Integration Testing Without Login Prompt

The application has been modified to support a testing mode that bypasses the login dialog:

```python
# Example of how to use test_mode in your tests
from main import main

def test_something():
    app, main_window = main(test_mode=True, test_user=mock_user)
    # Test main_window...
```

This approach is used in the integration tests to verify application behavior without requiring manual login.

## Test Fixtures

Common test fixtures are defined in:

- `conftest.py`: Global test fixtures
- `integration/conftest.py`: Integration test-specific fixtures

### Key Fixtures

- `test_user`: A pre-defined user for testing
- `authenticated_user`: A real user in the test database
- `mock_services`: Mock services for testing
- `clean_db`: A session with a clean database for testing 