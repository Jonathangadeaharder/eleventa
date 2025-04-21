# Testing Guide for Eleventa

## Overview

This project uses pytest for testing. The test suite includes:

- Unit tests for core business logic
- Integration tests for database and service interactions
- GUI tests for Qt-based user interfaces

## Quick Start

Use the unified test runner to run tests:

```bash
# Run all tests
python run_unified_tests.py

# Run only non-GUI tests
python run_unified_tests.py --no-gui

# Run only integration tests
python run_unified_tests.py --integration

# Run with verbose output
python run_unified_tests.py --verbose
```

## Test Runner Options

The `run_unified_tests.py` script provides a flexible way to run different types of tests:

| Option | Description |
|--------|-------------|
| `--no-gui` | Run only non-GUI tests (core and infrastructure) |
| `--qt` | Run only Qt/GUI tests |
| `--specific PATH` | Run tests in a specific file or directory |
| `--integration` | Run only integration tests |
| `--unit` | Run only unit tests |
| `--coverage` | Generate coverage report |
| `--html-report` | Generate HTML coverage report |
| `--verbose` or `-v` | Verbose output |
| `--failfast` or `-x` | Stop on first failure |

## Test Organization

- `tests/core/` - Core business logic tests
- `tests/infrastructure/` - Database and persistence tests
- `integration/` - Cross-component integration tests
- UI tests - Tests for Qt components and dialogs

## Best Practices

1. **Qt-related testing**: 
   - Qt tests can be flaky due to GUI interactions
   - Use `--no-gui` when working on business logic
   - The unified test runner handles Qt environment setup automatically

2. **Test Isolation**:
   - Tests should be independent of each other
   - Clean up any test data or state changes

3. **Mocking**:
   - Use mocks for external dependencies
   - For Qt components, prefer to mock GUI interactions

## Known Issues and Solutions

### "This plugin does not support propagateSizeHints()" warning

This is a known issue with Qt on Windows. The unified test runner automatically sets the proper environment variables to fix this issue.

### Access violations in GUI tests

Some GUI tests may cause access violations. The unified test runner handles this by:

1. Running tests in a specific order to minimize issues
2. Setting up the proper Qt environment
3. Separating GUI tests from other tests

If you encounter access violations, try:
- Running with `--no-gui` flag to skip GUI tests
- Using the `--specific` flag to run a single test file

## Generating Coverage Reports

```bash
# Generate standard coverage report
python run_unified_tests.py --coverage

# Generate HTML coverage report
python run_unified_tests.py --html-report
```

The HTML report will be available in the `htmlcov/` directory.

## Adding New Tests

1. Create test files in the appropriate directory
2. Follow the existing naming conventions
3. Use pytest fixtures for setup/teardown
4. For Qt tests, use qtbot for GUI interaction
5. For business logic services requiring additional scenarios (e.g., concurrency and error handling), create `test_<service>_extra.py` files in `tests/core/services/` and use dummy repositories to simulate edge cases.

## CI/CD Integration

The unified test runner can be easily integrated into CI/CD pipelines:

```bash
# Run only non-GUI tests in CI environment
python run_unified_tests.py --no-gui --coverage
```

This will run all non-GUI tests and generate a coverage report suitable for CI systems. 