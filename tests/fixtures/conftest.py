"""
Pytest configuration for fixtures package.

This module reexports fixtures from the fixtures package to make them
available to pytest when importing from this package.
"""
import pytest

# Re-export fixtures from test_data.py
from tests.fixtures.test_data import (
    test_department,
    test_product,
    test_customer,
    test_sale,
    test_invoice,
    test_user,
)

# Re-export fixtures from repository_mocks.py
from tests.fixtures.repository_mocks import (
    mock_product_repo,
    mock_department_repo,
    mock_customer_repo,
    mock_sale_repo,
    mock_inventory_repo,
    mock_invoice_repo,
    mock_user_repo,
)

# Register fixtures for setup_helpers
@pytest.fixture
def setup_test_data():
    """
    Fixture that provides access to data setup helpers.
    
    Returns:
        A dictionary containing references to setup helper functions
    """
    # Import here to avoid circular imports
    from tests.fixtures.setup_helpers import (
        setup_basic_product_data,
        setup_customer_data,
        setup_sale_data,
        setup_invoice_data,
        setup_complete_test_environment
    )
    
    return {
        "setup_basic_product_data": setup_basic_product_data,
        "setup_customer_data": setup_customer_data,
        "setup_sale_data": setup_sale_data,
        "setup_invoice_data": setup_invoice_data,
        "setup_complete_test_environment": setup_complete_test_environment
    } 