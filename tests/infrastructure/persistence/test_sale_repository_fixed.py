import pytest
from decimal import Decimal
from datetime import datetime, timedelta
import uuid
from typing import Optional
import time
from sqlalchemy import text
import sys
import os

# Ensure project root is in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import domain models
from core.models.sale import Sale, SaleItem
from core.models.product import Product, Department
from core.models.customer import Customer
from core.interfaces.repository_interfaces import ISaleRepository

# Import application ORM models
from infrastructure.persistence.sqlite.models_mapping import (
    DepartmentOrm, ProductOrm, SaleOrm, SaleItemOrm, UserOrm, CustomerOrm
)
from infrastructure.persistence.sqlite.repositories import (
    SqliteSaleRepository, 
    SqliteProductRepository,
    SqliteDepartmentRepository,
    SqliteCustomerRepository
)

# Helper functions to set up test data
@pytest.fixture
def create_department(test_db_session):
    """Create a test department with timestamp to ensure uniqueness."""
    def _create_department(name=None):
        timestamp = int(time.time() * 1000)  # milliseconds for more uniqueness
        # Add UUID to ensure absolute uniqueness, even with timestamp collisions
        unique_id = str(uuid.uuid4())[:8]
        department_name = name or f"Test Dept {timestamp}_{unique_id}"
        repo = SqliteDepartmentRepository(test_db_session)
        department = Department(name=department_name)
        return repo.add(department)
    return _create_department

@pytest.fixture
def create_product(test_db_session, create_department):
    """Create a test product and return its model."""
    def _create_product(code, description, price=10.0, cost=5.0):
        # Create a unique department for each product
        department = create_department()
        repo = SqliteProductRepository(test_db_session)
        timestamp = int(time.time() * 1000)
        unique_code = f"{code}_{timestamp}"  # Ensure unique code
        product = Product(
            code=unique_code,
            description=description,
            department_id=department.id,
            cost_price=cost,
            sell_price=price,
            uses_inventory=True
        )
        return repo.add(product)
    return _create_product

@pytest.fixture
def create_customer(test_db_session):
    """Create a test customer with timestamp to ensure uniqueness."""
    def _create_customer(name=None):
        timestamp = int(time.time() * 1000)
        customer_name = name or f"Test Customer {timestamp}"
        repo = SqliteCustomerRepository(test_db_session)
        customer = Customer(
            name=customer_name,
            cuit=f"{timestamp}",  # Ensure unique CUIT
            email=f"customer.{timestamp}@test.com"  # Ensure unique email
        )
        return repo.add(customer)
    return _create_customer

def test_calculate_profit_for_period(test_db_session, create_product, create_customer):
    """Test calculating profit for a period."""
    # Create test data
    product1 = create_product("PROFIT1", "Profit Product 1", price=10.0, cost=5.0)  # 50% margin
    product2 = create_product("PROFIT2", "Profit Product 2", price=20.0, cost=16.0)  # 20% margin
    customer = create_customer()
    
    repository = SqliteSaleRepository(test_db_session)
    
    # Create sales for different dates - same day
    now = datetime.now()
    
    # First sale
    sale1 = Sale(timestamp=now, payment_type="CASH", customer_id=customer.id, user_id=1)
    sale1.items = [
        SaleItem(product_id=product1.id, quantity=Decimal('5'), unit_price=Decimal('10.0'),
                 product_code=product1.code, product_description=product1.description)
    ]
    repository.add_sale(sale1)
    
    # Second sale
    sale2 = Sale(timestamp=now, payment_type="CARD", customer_id=customer.id, user_id=1)
    sale2.items = [
        SaleItem(product_id=product2.id, quantity=Decimal('2'), unit_price=Decimal('20.0'),
                 product_code=product2.code, product_description=product2.description)
    ]
    repository.add_sale(sale2)
    
    # Commit the changes to make sure they're visible
    test_db_session.commit()
    
    # Inspect the sales data to confirm
    sales_query = test_db_session.query(SaleOrm).all()
    print(f"Found {len(sales_query)} sales in the database")
    
    for sale in sales_query:
        print(f"Sale ID: {sale.id}, Time: {sale.date_time}, Items: {len(sale.items)}")
        for item in sale.items:
            print(f"  - Item ID: {item.id}, Product ID: {item.product_id}, Quantity: {item.quantity}, Price: {item.unit_price}")
    
    # Calculate expected values
    expected_revenue = 5 * 10.0 + 2 * 20.0  # 50 + 40 = 90
    expected_cost = 5 * 5.0 + 2 * 16.0      # 25 + 32 = 57
    expected_profit = expected_revenue - expected_cost
    
    # Test calculate_profit_for_period for today
    start_date = now.date()  # Today's date
    end_date = now.date()    # Today's date
    
    print(f"Calculating profit for period: {start_date} to {end_date}")
    profit_data = repository.calculate_profit_for_period(start_date, end_date)
    print(f"Result: {profit_data}")
    
    # In this test we expect specific values - both sales should be included
    assert profit_data['revenue'] == expected_revenue
    assert profit_data['cost'] == expected_cost
    assert profit_data['profit'] == expected_profit
    assert profit_data['margin'] == pytest.approx(expected_profit / expected_revenue, 0.01) 