# Integration Tests

This directory contains integration tests for the eleventa application. Integration tests verify that different components of the system work together correctly.

## Background

The integration tests in this directory were added after discovering an error in production where the InvoicingService couldn't load invoices because it was initialized with repository factory functions instead of repository instances.

The error message was:
```
Error al cargar facturas: 'function' object has no attribute 'get_all'
```

This happened because in `main.py`, the service was initialized with factory functions:

```python
# INCORRECT: Passing factory functions directly
invoicing_service = InvoicingService(
    invoice_repo=get_invoice_repo,  # This is a function, not a repository instance
    sale_repo=get_sale_repo, 
    customer_repo=get_customer_repo
)
```

But the InvoicingService expected actual repository instances, not factory functions.

## The Fix

The problem was fixed by creating repository instances before passing them to the service:

```python
# CORRECT: Create actual repositories with session and pass the instances
with session_scope() as session:
    invoice_repo = get_invoice_repo(session)
    sale_repo = get_sale_repo(session)
    customer_repo = get_customer_repo(session)
    
    invoicing_service = InvoicingService(
        invoice_repo=invoice_repo,     # Pass repository instance
        sale_repo=sale_repo,           # Pass repository instance
        customer_repo=customer_repo    # Pass repository instance
    )
```

## Integration Tests Added

1. `test_main_initialization.py` - Demonstrates and verifies the fix for the repository factory issue:
   - `test_proposed_fix_directly` - Shows the exact error with a simplified test case
   - `test_fix_with_actual_repository` - Tests with the real repository class

2. `test_invoicing_integration.py` - Tests the full invoicing workflow:
   - `test_create_invoice_from_sale` - Tests creating an invoice from a sale
   - `test_get_all_invoices` - Tests the functionality that failed in production
   - `test_generate_invoice_pdf` - Tests PDF generation

## Running the Tests

```bash
# Run all integration tests
python -m pytest integration/

# Run specific test file
python -m pytest integration/test_main_initialization.py

# Run with verbose output
python -m pytest integration/ -v
```

## Best Practices for Integration Tests

1. Test actual component interaction, not just mock behavior
2. Use real database connections when possible (test database or in-memory)
3. Test complete workflows end-to-end
4. Ensure test environment is properly set up and torn down
5. Include specific tests for issues found in production
6. Test boundary cases and error conditions 