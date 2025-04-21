"""
Example test demonstrating the use of standardized fixtures.

This test serves as an example of how to use the standardized fixtures
for test data management to create cleaner, more maintainable tests.
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta

# Import service to test
from core.services.sale_service import SaleService

# Import models
from core.models.sale import Sale, SaleItem
from core.models.product import Product

# Import test data creation functions
from tests.fixtures.test_data import (
    create_product, create_sale, create_sale_item, 
    create_customer, ProductBuilder, SaleBuilder
)

# Test with individual fixtures
def test_create_sale_with_fixtures(
    mock_product_repo, 
    mock_sale_repo, 
    test_customer
):
    """Test creating a sale using individual fixtures."""
    # Create a sale service with mock repositories
    sale_service = SaleService(
        sale_repo=mock_sale_repo,
        product_repo=mock_product_repo,
        customer_repo=None,  # Not needed for this test
        inventory_service=None  # Not needed for this test
    )
    
    # Add test products to the mock repository
    product1 = create_product(code="P001", description="Test Product 1", sell_price=Decimal("10.00"))
    product2 = create_product(code="P002", description="Test Product 2", sell_price=Decimal("20.00"))
    mock_product_repo.add(product1)
    mock_product_repo.add(product2)
    
    # Create sale items
    items = [
        {"product_id": product1.id, "quantity": 2},
        {"product_id": product2.id, "quantity": 1}
    ]
    
    # Call the service method
    sale = sale_service.create_sale(items, customer_id=test_customer.id)
    
    # Assertions
    assert sale is not None
    assert len(sale.items) == 2
    assert sale.customer_id == test_customer.id
    assert sale.total == Decimal("40.00")  # (2 * 10.00) + (1 * 20.00)

# Test with repository mocks and factory functions
def test_create_sale_with_factory_functions(mock_sale_repo):
    """Test creating a sale using factory functions and mocks."""
    # Create products directly
    product1 = create_product(id=1, code="P001", sell_price=Decimal("10.00"))
    product2 = create_product(id=2, code="P002", sell_price=Decimal("20.00"))
    
    # Create a customer
    customer = create_customer(id="a5f5d8f5-9af4-4fba-9061-cd771a3ba788")
    
    # Create a sale with the builder pattern
    sale = SaleBuilder() \
        .with_customer(customer.id) \
        .with_product(product1.id, Decimal("2"), product1.sell_price, product1.code, product1.description) \
        .with_product(product2.id, Decimal("1"), product2.sell_price, product2.code, product2.description) \
        .build()
    
    # Add the sale to the mock repository
    mock_sale_repo.add(sale)
    
    # Retrieve the sale
    retrieved_sale = mock_sale_repo.get_by_id(sale.id)
    
    # Assertions
    assert retrieved_sale is not None
    assert len(retrieved_sale.items) == 2
    assert retrieved_sale.total == Decimal("40.00")

# Test with setup helper functions
def test_sale_with_setup_helpers(clean_db, setup_test_data):
    """Test creating sales using setup helper functions with real DB session."""
    session = clean_db
    
    # Use setup helpers to create test data
    department, products = setup_test_data["setup_basic_product_data"](session)
    customers = setup_test_data["setup_customer_data"](session, num_customers=1)
    sales = setup_test_data["setup_sale_data"](session, products, customers[0], num_sales=1)
    
    # Verify the data was created correctly
    assert len(products) == 3
    assert len(customers) == 1
    assert len(sales) == 1
    assert sales[0].customer_id == customers[0].id
    
    # Create a sale service with real repositories
    from infrastructure.persistence.sqlite.repositories import (
        SqliteSaleRepository, SqliteProductRepository, SqliteCustomerRepository
    )
    
    sale_repo = SqliteSaleRepository(session)
    
    # Verify we can retrieve the sale
    retrieved_sale = sale_repo.get_by_id(sales[0].id)
    assert retrieved_sale is not None
    assert retrieved_sale.id == sales[0].id
    
    # Verify the total is calculated correctly based on the items
    expected_total = sum(item.quantity * item.unit_price for item in retrieved_sale.items)
    assert retrieved_sale.total == expected_total

# Test with complete test environment
def test_with_complete_environment(clean_db, setup_test_data):
    """Test using the complete test environment setup."""
    session = clean_db
    
    # Set up a complete test environment
    env = setup_test_data["setup_complete_test_environment"](session)
    
    # Verify all expected data was created
    assert env["department"] is not None
    assert len(env["products"]) == 3
    assert len(env["customers"]) == 2
    assert len(env["sales"]) == 2
    assert len(env["invoices"]) == 2
    assert env["purchase_order"] is not None
    
    # Verify relationships between entities
    assert env["sales"][0].customer_id == env["customers"][0].id
    assert env["invoices"][0].sale_id == env["sales"][0].id
    assert env["purchase_order"].supplier_id == env["supplier"].id
    
    # Verify product data is consistent
    for product in env["products"]:
        assert product.department_id == env["department"].id 