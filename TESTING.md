# Testing Guide for Eleventa

## Overview

This project uses pytest for testing. The test suite includes:

- Unit tests for core business logic (`tests/core/`)
- Integration tests for database, service interactions (`tests/infrastructure/`, `tests/integration/`)
- UI tests for Qt-based user interfaces (`tests/ui/`)

Tests in the `tests/ui/` directory are automatically marked with the `ui` marker by `conftest.py`.
Critical Qt environment variables (like running `offscreen`) are also set in `conftest.py`.

## Running Tests with Pytest

All tests are run using `pytest` directly from the command line in the project root directory.

### Basic Commands

- **Run all tests (including UI tests):**
  ```bash
  pytest
  ```

- **Run tests with verbose output:**
  ```bash
  pytest -v
  ```

- **Stop on the first failure:**
  ```bash
  pytest -x
  ```

### Selecting Tests

You can run specific subsets of tests using paths, keywords, or markers.

- **Run tests in a specific directory:**
  ```bash
  pytest tests/core/
  pytest tests/ui/
  ```

- **Run tests in a specific file:**
  ```bash
  pytest tests/core/models/test_product.py
  ```

- **Run tests matching a keyword expression:**
  (This will run tests whose names contain "customer" or "Product" - case-insensitive with `-k`)
  ```bash
  pytest -k "customer or Product"
  ```

- **Run tests with specific markers:**
  (Markers like `unit`, `integration`, `ui`, `smoke`, `alembic` are defined in `pytest.ini` and `conftest.py`)
  
  - Run only UI tests:
    ```bash
    pytest -m ui
    ```
  - Run all tests *except* UI tests:
    ```bash
    pytest -m "not ui"
    ```
  - Run only integration tests:
    ```bash
    pytest -m integration
    ```
  - Run smoke tests:
    ```bash
    pytest -m smoke
    ```

### Coverage Reports

Coverage is configured in `pytest.ini` and `.coveragerc`.

- **Run all tests and generate a terminal coverage report:**
  ```bash
  pytest --cov
  ```
  (Note: `--cov=core --cov-report=term` is often configured in `pytest.ini` `addopts`, so `pytest` might show it by default. To specify sources, use `--cov=core --cov=ui` etc.)

- **Generate an HTML coverage report (runs all tests):**
  ```bash
  pytest --cov --cov-report=html
  ```
  The HTML report will be available in the `htmlcov/` directory (as configured in `.coveragerc`).

## Test Organization

- `tests/core/` - Core business logic tests (often marked `unit`)
- `tests/infrastructure/` - Database and persistence tests (often marked `integration`)
- `tests/integration/` - Cross-component integration tests (marked `integration`)
- `tests/ui/` - Tests for Qt components and dialogs (automatically marked `ui`)

## Best Practices

1.  **Test Isolation**: Tests should be independent. Use fixtures for setup/teardown.
2.  **Mocking**: Use `pytest-mock` (or `unittest.mock`) for external dependencies.
3.  **Qt Testing**: 
    - UI tests are run by default with `pytest`.
    - Use `pytest -m "not ui"` if you are working only on non-GUI logic and want faster test cycles.
    - The `conftest.py` and `pytest-qt` plugin handle Qt environment setup (e.g., offscreen platform).

## Known Issues and Solutions

- **Qt Platform Warnings/Errors**: `conftest.py` attempts to set up a headless Qt environment (`offscreen`). If issues persist, ensure your PySide6 installation and system dependencies are correct.
- **Access violations in GUI tests**: While `conftest.py` sets up an offscreen platform, GUI tests can sometimes be sensitive. If you encounter issues:
    - Try running a problematic UI test file individually: `pytest tests/ui/problematic_test_file.py -v -s` (the `-s` shows print output).

## Adding New Tests

1.  Create test files in the appropriate directory (e.g., `tests/core/services/`).
2.  Follow naming conventions (e.g., `test_*.py` for files, `Test...` for classes, `test_...` for functions).
3.  Use pytest fixtures for setup/teardown.
4.  For Qt tests, use the `qtbot` fixture provided by `pytest-qt`.
5.  For business logic services requiring additional scenarios (e.g., concurrency and error handling), consider creating `test_<service>_extra.py` files in `tests/core/services/` and use dummy/mock repositories to simulate edge cases.

## CI/CD Integration

For CI/CD pipelines, you can use `pytest` commands directly:

- **Run all tests and generate Cobertura XML coverage report (common for CI):**
  ```bash
  pytest --cov --cov-report=xml
  ```

- **If UI tests are problematic or too slow for a particular CI stage, run non-UI tests:**
  ```bash
  pytest -m "not ui" --cov --cov-report=xml
  ``` 