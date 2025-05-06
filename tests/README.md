# Eleventa Test Suite

This directory contains tests for the eleventa application.

## Test Structure

- `core/`: Unit tests for core business logic and services
- `infrastructure/`: Tests for database, repositories, and external systems
- `ui/`: Tests for the user interface components
- `integration/`: Integration tests for multiple components working together

## UI Testing Strategy

We've implemented a targeted approach to UI testing to balance coverage with stability:

### 1. Smoke Tests for Critical UI Workflows

Located in `ui/smoke_tests.py`, these tests:
- Cover the most critical user workflows
- Are designed to be stable and reliable
- Should be run before releases

Run smoke tests with:
```bash
python tests/run_smoke_tests.py
```

### 2. Lower-Level Tests for Comprehensive Coverage

Most functionality is covered by:
- Unit tests for view models and business logic
- Service-level integration tests
- Repository and data access tests

Read more about our UI testing approach in [tests/ui/README.md](ui/README.md).

## Test Documentation Standards

All test modules should include:

1. A detailed module docstring that explains:
   - The purpose of the test suite
   - Components being tested and their relationships
   - Coverage goals for the module
   - Special setup requirements or dependencies

2. Test function docstrings that explain:
   - What specific functionality is being tested
   - Expected outcomes and assertions
   - Edge cases or special scenarios being covered
   - Any complex setup or preconditions

3. Comments for complex test logic that isn't immediately obvious

Example module docstring:

```python
"""
Tests for the InvoicingService class.

This test suite covers the invoicing functionality including:
- Invoice creation from sales
- Invoice number generation and validation
- Invoice type determination based on customer IVA condition

Coverage goals:
- 100% coverage of the InvoicingService public API
- Error handling scenarios for all public methods

Test dependencies:
- unittest mocking for isolation from database
"""
```

## Coverage Goals

The project aims for the following test coverage:

- **Core Business Logic**: 95%+ coverage
- **Infrastructure**: 85%+ coverage
- **UI Components**: 70%+ coverage (focusing on view models and key workflows)
- **Integration Tests**: Key user flows and boundary conditions

## Setting Up for Testing

Install the required test dependencies:

```bash
pip install -r requirements-test.txt
```

### Test Database Setup

Tests use SQLite in-memory databases by default. The `clean_db` fixture in 
`conftest.py` provides a fresh database session for each test.

For tests requiring a persistent database:

```python
@pytest.mark.usefixtures("persistent_test_db")
def test_something_with_persistent_db():
    # This test will use a file-based SQLite database
    # that persists between test runs
    ...
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

# Run UI smoke tests (stable UI tests)
python -m pytest -m smoke

# Run all non-UI tests
python -m pytest -k "not ui"

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
# Run a specific UI test file (safer than running all UI tests)
python -m pytest ui/dialogs/test_specific_dialog.py -v

# NOT RECOMMENDED (may cause crashes)
python -m pytest ui/
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
- `ui/conftest.py`: UI test-specific fixtures

### Key Fixtures

- `test_user`: A pre-defined user for testing
- `authenticated_user`: A real user in the test database
- `mock_services`: Mock services for testing
- `clean_db`: A session with a clean database for testing 

## Mocking Guidelines

1. Use pytest's monkeypatch for simple attribute/function replacement
2. Use unittest.mock.patch for more complex mocking scenarios
3. Prefer dependency injection over monkey patching where possible
4. Always reset mocks between tests to avoid test interdependence

## Test Data Management

1. Use factories and fixtures to create consistent test data
2. Isolate test data between tests to prevent interference
3. Use appropriate scopes for fixtures (function, class, module, session)
4. Clean up after tests that create resources (files, database entries, etc.) 

## Standardized Test Data Management

The test suite now includes a standardized approach to test data management located in the `tests/fixtures` package:

### Factory Functions

Factory functions for creating test entities are available in `tests/fixtures/test_data.py`:

```python
# Creating test data with factory functions
from tests.fixtures.test_data import create_product, create_customer

# Create a product with default values
product = create_product()

# Create a product with custom values
custom_product = create_product(
    code="P123",
    description="Custom Product", 
    sell_price=Decimal("15.99")
)

# Create a customer with custom values
customer = create_customer(name="Test Customer", email="test@example.com")
```

### Builder Pattern

For complex objects, builder classes are available:

```python
# Using the builder pattern for complex objects
from tests.fixtures.test_data import ProductBuilder, SaleBuilder

# Build a product with chained methods
product = ProductBuilder() \
    .with_code("P999") \
    .with_description("Special Product") \
    .with_prices(Decimal("99.99"), Decimal("50.00")) \
    .with_department(1) \
    .build()

# Build a sale with multiple items
sale = SaleBuilder() \
    .with_customer(customer_id) \
    .with_product(1, Decimal("2"), Decimal("10.00")) \
    .with_product(2, Decimal("1"), Decimal("20.00")) \
    .with_payment_type("Tarjeta") \
    .build()
```

### Repository Mocking

Standardized repository mocks are available in `tests/fixtures/repository_mocks.py`:

```python
# Using mock repositories in tests
def test_with_mock_repos(mock_product_repo, mock_sale_repo):
    # These fixtures provide pre-configured repository mocks with
    # standard behavior for add, get_by_id, get_all, update, delete
    
    # Add a product to the mock repository
    product = create_product()
    mock_product_repo.add(product)
    
    # The ID will be automatically assigned and the product will be retrievable
    retrieved = mock_product_repo.get_by_id(product.id)
    assert retrieved == product
    
    # Custom method behavior can be added
    mock_sale_repo.get_sales_for_customer.return_value = [create_sale()]
```

### Setup Helper Functions

Helper functions for setting up complex test scenarios are available in `tests/fixtures/setup_helpers.py`:

```python
# Using setup helpers for complex data scenarios
def test_with_complex_setup(clean_db, setup_test_data):
    session = clean_db
    
    # Create a department and associated products
    department, products = setup_test_data["setup_basic_product_data"](session)
    
    # Create customers
    customers = setup_test_data["setup_customer_data"](session, num_customers=2)
    
    # Create sales for a customer
    sales = setup_test_data["setup_sale_data"](
        session, products, customers[0], num_sales=2
    )
    
    # Create invoices for those sales
    invoices = setup_test_data["setup_invoice_data"](
        session, sales, customers[0]
    )
    
    # Or set up a complete environment with all related entities
    env = setup_test_data["setup_complete_test_environment"](session)
    # env contains: department, products, customers, supplier, sales, invoices, purchase_order
```

### Best Practices for Test Data

1. Use factory functions for simple entity creation
2. Use builders for complex objects with many optional attributes
3. Use setup helpers for creating related entities and managing relationships
4. Use the mock repository fixtures for standard repository behavior
5. Keep test data isolated between tests using fixture function scope 