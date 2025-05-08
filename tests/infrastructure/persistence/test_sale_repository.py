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
        timestamp = int(time.time() * 1000)  # milliseconds for more uniqueness
        customer_name = name or f"Test Customer {timestamp}"
        
        # Ensure CUIT is unique by using timestamp for it as well
        unique_cuit = f"{timestamp}"
        
        repo = SqliteCustomerRepository(test_db_session)
        customer = Customer(
            name=customer_name,
            cuit=unique_cuit,  # Use unique timestamp-based CUIT
            email=f"customer.{timestamp}@test.com"  # Ensure unique email
        )
        return repo.add(customer)
    return _create_customer

def test_add_sale(test_db_session, create_product, create_customer):
    """Test adding a new sale."""
    # Create test data
    product1 = create_product("PROD1", "Product 1", 15.0, 8.0)
    product2 = create_product("PROD2", "Product 2", 25.0, 12.0)
    customer = create_customer()
    test_db_session.commit()
    
    # Create sale with items
    sale = Sale(
        timestamp=datetime.now(),
        payment_type="CASH",
        customer_id=customer.id,
        user_id=1
    )
    
    # Add sale items
    item1 = SaleItem(
        product_id=product1.id,
        quantity=Decimal('2'),
        unit_price=Decimal(str(product1.sell_price)),
        product_code=product1.code,
        product_description=product1.description
    )
    item2 = SaleItem(
        product_id=product2.id,
        quantity=Decimal('1'),
        unit_price=Decimal(str(product2.sell_price)),
        product_code=product2.code,
        product_description=product2.description
    )
    
    sale.items = [item1, item2]
    
    # Use repository to add the sale
    repository = SqliteSaleRepository(test_db_session)
    saved_sale = repository.add_sale(sale)
    test_db_session.commit()
    
    # Verify the sale and its items were saved correctly
    assert saved_sale.id is not None
    assert len(saved_sale.items) == 2
    assert saved_sale.total == Decimal('55.00')  # 2*15 + 1*25 = 55
    
    # Verify directly in database
    sale_orm = test_db_session.query(SaleOrm).filter_by(id=saved_sale.id).first()
    assert sale_orm is not None
    assert float(sale_orm.total_amount) == float(saved_sale.total)
    
    # Verify items
    items_orm = test_db_session.query(SaleItemOrm).filter_by(sale_id=saved_sale.id).all()
    assert len(items_orm) == 2
    
    # Verify the sale can be retrieved
    retrieved_sale = repository.get_by_id(saved_sale.id)
    assert retrieved_sale is not None
    assert retrieved_sale.id == saved_sale.id
    assert len(retrieved_sale.items) == 2

def test_get_sales_summary_by_period(test_db_session, create_product, create_customer):
    """Test getting sales summary grouped by period."""
    # Create test data
    product1 = create_product("TEST01", "Test Product 1", 10.0, 5.0)
    product2 = create_product("TEST02", "Test Product 2", 20.0, 10.0)
    customer = create_customer()
    test_db_session.commit()
    
    repository = SqliteSaleRepository(test_db_session)
    
    # Create sales for different dates
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    two_days_ago = now - timedelta(days=2)
    
    # Day 1 sales
    sale1 = Sale(timestamp=two_days_ago, payment_type="CASH", customer_id=customer.id, user_id=1)
    sale1.items = [
        SaleItem(product_id=product1.id, quantity=Decimal('3'), unit_price=Decimal('10.0'),
                 product_code=product1.code, product_description=product1.description)
    ]
    repository.add_sale(sale1)
    
    # Day 2 sales (2 sales)
    sale2 = Sale(timestamp=yesterday, payment_type="CARD", customer_id=customer.id, user_id=1)
    sale2.items = [
        SaleItem(product_id=product1.id, quantity=Decimal('1'), unit_price=Decimal('10.0'),
                 product_code=product1.code, product_description=product1.description),
        SaleItem(product_id=product2.id, quantity=Decimal('2'), unit_price=Decimal('20.0'),
                 product_code=product2.code, product_description=product2.description)
    ]
    repository.add_sale(sale2)
    
    sale3 = Sale(timestamp=yesterday + timedelta(hours=3), payment_type="CASH", customer_id=customer.id, user_id=1)
    sale3.items = [
        SaleItem(product_id=product2.id, quantity=Decimal('1'), unit_price=Decimal('20.0'),
                 product_code=product2.code, product_description=product2.description)
    ]
    repository.add_sale(sale3)
    
    test_db_session.commit()
    
    # Test get_sales_summary_by_period with daily grouping
    start_date = two_days_ago.date()
    end_date = yesterday.date()  # Change to yesterday to exclude today
    
    summary = repository.get_sales_summary_by_period(start_date=start_date, end_date=end_date, group_by="day")
    
    # Should have 2 days with sales
    assert len(summary) == 2
    
    # Extract the day strings from the summary dates and sort them chronologically
    summary_days = sorted(summary, key=lambda x: x['date'])
    day1 = summary_days[0]  # First day (two_days_ago)
    day2 = summary_days[1]  # Second day (yesterday)
    
    # Print for debugging
    print(f"Day 1: {day1}")
    print(f"Day 2: {day2}")
    print(f"Raw summary data: {summary}")
    
    # Day 1 (two_days_ago) - 1 sale of 3 items at $10 each = $30
    assert day1['num_sales'] == 1
    assert day1['total_sales'] == 30.0
    
    # Day 2 (yesterday) - With our current SQLite implementation, we only get 1 sale
    # but with the combined total of 70.0 from both sale2 and sale3
    assert day2['num_sales'] == 2  # Our SQLite implementation now counts 2 sales for this day 
    assert day2['total_sales'] == 70.0  # Total of both sales (sale2: 10 + 2*20 = 50, sale3: 20)

def test_get_sales_by_payment_type(test_db_session, create_product, create_customer):
    """Test getting sales summarized by payment type."""
    # Create test data
    product = create_product("PAYTEST", "Payment Test Product", 10.0, 5.0)
    customer = create_customer()
    test_db_session.commit()
    
    repository = SqliteSaleRepository(test_db_session)
    
    # Create sales with different payment types
    now = datetime.now()
    
    # Cash sales (2)
    for _ in range(2):
        sale = Sale(timestamp=now, payment_type="CASH", customer_id=customer.id, user_id=1)
        sale.items = [
            SaleItem(product_id=product.id, quantity=Decimal('1'), unit_price=Decimal('10.0'),
                     product_code=product.code, product_description=product.description)
        ]
        repository.add_sale(sale)
    
    # Card sales (3)
    for _ in range(3):
        sale = Sale(timestamp=now, payment_type="CARD", customer_id=customer.id, user_id=1)
        sale.items = [
            SaleItem(product_id=product.id, quantity=Decimal('1'), unit_price=Decimal('10.0'),
                     product_code=product.code, product_description=product.description)
        ]
        repository.add_sale(sale)
    
    test_db_session.commit()
    
    # Test get_sales_by_payment_type
    payment_summary = repository.get_sales_by_payment_type()
    
    # Should have 2 payment types
    assert len(payment_summary) == 2
    
    # Find each payment type in results
    cash_summary = [s for s in payment_summary if s['payment_type'] == "CASH"][0]
    card_summary = [s for s in payment_summary if s['payment_type'] == "CARD"][0]
    
    assert cash_summary['num_sales'] == 2
    assert cash_summary['total_sales'] == 20.0  # 2 sales * $10
    
    assert card_summary['num_sales'] == 3
    assert card_summary['total_sales'] == 30.0  # 3 sales * $10

def test_get_sales_by_department(test_db_session, create_department, create_product, create_customer):
    """Test getting sales summarized by department."""
    # Create departments and products
    dept1 = create_department("Department 1")
    dept2 = create_department("Department 2")
    
    # Create products in different departments
    repo = SqliteProductRepository(test_db_session)
    
    product1 = Product(
        code="DEPT1PROD",
        description="Department 1 Product",
        department_id=dept1.id,
        cost_price=5.0,
        sell_price=10.0
    )
    added_product1 = repo.add(product1)
    
    product2 = Product(
        code="DEPT2PROD",
        description="Department 2 Product",
        department_id=dept2.id,
        cost_price=15.0,
        sell_price=30.0
    )
    added_product2 = repo.add(product2)
    
    customer = create_customer()
    test_db_session.commit()
    
    # Create sales for different departments
    repository = SqliteSaleRepository(test_db_session)
    
    # Department 1 sales (2 sales * $10 = $20)
    for _ in range(2):
        sale = Sale(timestamp=datetime.now(), payment_type="CASH", customer_id=customer.id, user_id=1)
        sale.items = [
            SaleItem(product_id=added_product1.id, quantity=Decimal('1'), unit_price=Decimal('10.0'),
                     product_code=added_product1.code, product_description=added_product1.description)
        ]
        repository.add_sale(sale)
    
    # Department 2 sales (1 sale * $30 = $30)
    sale = Sale(timestamp=datetime.now(), payment_type="CARD", customer_id=customer.id, user_id=1)
    sale.items = [
        SaleItem(product_id=added_product2.id, quantity=Decimal('1'), unit_price=Decimal('30.0'),
                 product_code=added_product2.code, product_description=added_product2.description)
    ]
    repository.add_sale(sale)
    
    test_db_session.commit()
    
    # Test get_sales_by_department
    dept_summary = repository.get_sales_by_department()
    
    # Should have 2 departments
    assert len(dept_summary) == 2
    
    # Find each department in results
    dept1_summary = [s for s in dept_summary if s['department_name'] == "Department 1"][0]
    dept2_summary = [s for s in dept_summary if s['department_name'] == "Department 2"][0]
    
    assert dept1_summary['total_sales'] == 20.0  # 2 sales * $10
    assert dept2_summary['total_sales'] == 30.0  # 1 sale * $30

def test_get_sales_by_customer(test_db_session, create_product, create_customer):
    """Test getting sales summarized by customer."""
    # Create test data
    product = create_product("CUSTTEST", "Customer Test Product", 10.0, 5.0)
    
    # Make sure to use uniqueness for each customer
    timestamp1 = int(time.time() * 1000)
    timestamp2 = timestamp1 + 100  # Use a larger offset to ensure unique timestamps
    
    customer1 = create_customer(f"Customer One {timestamp1}")
    
    # Force a small delay to ensure different timestamps for CUIT
    time.sleep(0.01)
    timestamp2 = int(time.time() * 1000)  # Get a fresh timestamp
    
    customer2 = create_customer(f"Customer Two {timestamp2}")
    test_db_session.commit()
    
    repository = SqliteSaleRepository(test_db_session)
    
    # Create sales for each customer
    now = datetime.now()
    
    # Sales for customer 1 (more sales/volume)
    sale1 = Sale(timestamp=now - timedelta(days=5), payment_type="CASH", customer_id=customer1.id, user_id=1)
    sale1.items = [
        SaleItem(product_id=product.id, quantity=Decimal('3'), unit_price=Decimal('10.0'),
                  product_code=product.code, product_description=product.description)
    ]
    repository.add_sale(sale1)
    
    sale2 = Sale(timestamp=now - timedelta(days=3), payment_type="CASH", customer_id=customer1.id, user_id=1)
    sale2.items = [
        SaleItem(product_id=product.id, quantity=Decimal('2'), unit_price=Decimal('10.0'),
                  product_code=product.code, product_description=product.description)
    ]
    repository.add_sale(sale2)
    
    # Sale for customer 2 (less volume)
    sale3 = Sale(timestamp=now - timedelta(days=2), payment_type="CARD", customer_id=customer2.id, user_id=1)
    sale3.items = [
        SaleItem(product_id=product.id, quantity=Decimal('1'), unit_price=Decimal('10.0'),
                  product_code=product.code, product_description=product.description)
    ]
    repository.add_sale(sale3)
    
    test_db_session.commit()
    
    # Get sales by customer
    summary = repository.get_sales_by_customer(now - timedelta(days=10), now, limit=5)
    
    # Should have 2 customers
    assert len(summary) == 2
    
    # Customer 1 should be first (more sales)
    assert summary[0]['customer_id'] == customer1.id
    assert summary[0]['num_sales'] == 2
    assert summary[0]['total_sales'] == 50.0  # 3*10 + 2*10 = 50
    
    # Customer 2 should be second (less sales)
    assert summary[1]['customer_id'] == customer2.id
    assert summary[1]['num_sales'] == 1
    assert summary[1]['total_sales'] == 10.0  # 1*10 = 10

def test_get_top_selling_products(test_db_session, create_product, create_customer):
    """Test getting top selling products."""
    # Create test data
    product1 = create_product("TOP1", "Top Product 1", 10.0, 5.0)
    product2 = create_product("TOP2", "Top Product 2", 20.0, 10.0)
    product3 = create_product("TOP3", "Top Product 3", 30.0, 15.0)
    customer = create_customer()
    test_db_session.commit()
    
    repository = SqliteSaleRepository(test_db_session)
    
    # Create sales with different products
    # Product 1: 5 units
    sale1 = Sale(timestamp=datetime.now(), payment_type="CASH", customer_id=customer.id, user_id=1)
    sale1.items = [
        SaleItem(product_id=product1.id, quantity=Decimal('5'), unit_price=Decimal('10.0'),
                 product_code=product1.code, product_description=product1.description)
    ]
    repository.add_sale(sale1)
    
    # Product 2: 3 units
    sale2 = Sale(timestamp=datetime.now(), payment_type="CASH", customer_id=customer.id, user_id=1)
    sale2.items = [
        SaleItem(product_id=product2.id, quantity=Decimal('3'), unit_price=Decimal('20.0'),
                 product_code=product2.code, product_description=product2.description)
    ]
    repository.add_sale(sale2)
    
    # Product 3: 1 unit
    sale3 = Sale(timestamp=datetime.now(), payment_type="CASH", customer_id=customer.id, user_id=1)
    sale3.items = [
        SaleItem(product_id=product3.id, quantity=Decimal('1'), unit_price=Decimal('30.0'),
                 product_code=product3.code, product_description=product3.description)
    ]
    repository.add_sale(sale3)
    
    test_db_session.commit()
    
    # Test get_top_selling_products (quantity)
    top_products = repository.get_top_selling_products()
    
    # Should have 3 products, ordered by quantity sold
    assert len(top_products) == 3
    
    # Products should be ordered by quantity sold (descending)
    # Since we're using timestamped product codes, we need to check by product ID instead
    assert top_products[0]['product_id'] == product1.id  # 5 units
    assert top_products[1]['product_id'] == product2.id  # 3 units
    assert top_products[2]['product_id'] == product3.id  # 1 unit
    
    # Verify the quantities are as expected
    assert top_products[0]['quantity_sold'] == 5.0
    assert top_products[1]['quantity_sold'] == 3.0
    assert top_products[2]['quantity_sold'] == 1.0

def test_calculate_profit_for_period(test_db_session, create_product, create_customer):
    """Test calculating profit for a period."""
    # Create test data
    product1 = create_product("PROFIT1", "Profit Product 1", price=10.0, cost=5.0)  # 50% margin
    product2 = create_product("PROFIT2", "Profit Product 2", price=20.0, cost=16.0)  # 20% margin
    customer = create_customer()
    test_db_session.commit()
    
    repository = SqliteSaleRepository(test_db_session)
    
    # Create sales for the current date (today)
    now = datetime.now()
    
    # First sale - should be included in period
    sale1 = Sale(timestamp=now, payment_type="CASH", customer_id=customer.id, user_id=1)
    sale1.items = [
        SaleItem(product_id=product1.id, quantity=Decimal('5'), unit_price=Decimal('10.0'),
                 product_code=product1.code, product_description=product1.description)
    ]
    repository.add_sale(sale1)
    
    # Second sale - should be included in period
    sale2 = Sale(timestamp=now, payment_type="CARD", customer_id=customer.id, user_id=1)
    sale2.items = [
        SaleItem(product_id=product2.id, quantity=Decimal('2'), unit_price=Decimal('20.0'),
                 product_code=product2.code, product_description=product2.description)
    ]
    repository.add_sale(sale2)
    
    test_db_session.commit()
    
    # Test calculate_profit_for_period for today only
    start_date = now.date()
    end_date = now.date()
    
    profit_data = repository.calculate_profit_for_period(start_date, end_date)
    
    # Total sales: (5 * $10) + (2 * $20) = $50 + $40 = $90
    # Total cost: (5 * $5) + (2 * $16) = $25 + $32 = $57
    # Profit: $90 - $57 = $33
    
    assert profit_data['revenue'] == 90.0
    assert profit_data['cost'] == 57.0
    assert profit_data['profit'] == 33.0
    assert profit_data['margin'] == pytest.approx(0.367, 0.01)  # 33/90 = 0.367

def test_get_sale_by_id(test_db_session, create_product, create_customer):
    """Test retrieving a sale by ID."""
    # Create test data
    product = create_product("GETSALE", "Get Sale Product", 10.0, 5.0)
    customer = create_customer()
    test_db_session.commit()
    
    repository = SqliteSaleRepository(test_db_session)
    
    # Create a sale
    sale = Sale(timestamp=datetime.now(), payment_type="CASH", customer_id=customer.id, user_id=1)
    sale.items = [
        SaleItem(product_id=product.id, quantity=Decimal('3'), unit_price=Decimal('10.0'),
                 product_code=product.code, product_description=product.description)
    ]
    saved_sale = repository.add_sale(sale)
    test_db_session.commit()
    
    # Test get_by_id
    retrieved_sale = repository.get_by_id(saved_sale.id)
    
    # Verify the sale was retrieved correctly
    assert retrieved_sale is not None
    assert retrieved_sale.id == saved_sale.id
    assert retrieved_sale.payment_type == "CASH"
    assert retrieved_sale.customer_id == customer.id
    
    # Verify items
    assert len(retrieved_sale.items) == 1
    assert retrieved_sale.items[0].product_id == product.id
    assert retrieved_sale.items[0].quantity == Decimal('3')
    assert retrieved_sale.items[0].unit_price == Decimal('10.0')
    
    # Test getting a non-existent sale
    non_existent_id = 9999
    assert repository.get_by_id(non_existent_id) is None

def test_get_sales_by_period_filtering(test_db_session, create_product, create_customer):
    """Test filtering sales by period."""
    # Create test data
    product = create_product("PERIOD", "Period Test Product", 10.0, 5.0)
    customer = create_customer()
    test_db_session.commit()
    
    repository = SqliteSaleRepository(test_db_session)
    
    # Create sales for different dates
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    two_days_ago = now - timedelta(days=2)
    
    # Day 1 sale
    sale1 = Sale(timestamp=two_days_ago, payment_type="CASH", customer_id=customer.id, user_id=1)
    sale1.items = [
        SaleItem(product_id=product.id, quantity=Decimal('1'), unit_price=Decimal('10.0'),
                 product_code=product.code, product_description=product.description)
    ]
    repository.add_sale(sale1)
    
    # Day 2 sale
    sale2 = Sale(timestamp=yesterday, payment_type="CARD", customer_id=customer.id, user_id=1)
    sale2.items = [
        SaleItem(product_id=product.id, quantity=Decimal('1'), unit_price=Decimal('10.0'),
                 product_code=product.code, product_description=product.description)
    ]
    repository.add_sale(sale2)
    
    # Day 3 (today) sale
    sale3 = Sale(timestamp=now, payment_type="CASH", customer_id=customer.id, user_id=1)
    sale3.items = [
        SaleItem(product_id=product.id, quantity=Decimal('1'), unit_price=Decimal('10.0'),
                 product_code=product.code, product_description=product.description)
    ]
    repository.add_sale(sale3)
    
    test_db_session.commit()
    
    # Test get_sales_by_period with different date ranges
    
    # Full range (all sales)
    start_full = two_days_ago - timedelta(hours=1)
    end_full = now + timedelta(hours=1)
    sales_full = repository.get_sales_by_period(start_full, end_full)
    assert len(sales_full) == 3
    
    # Yesterday only
    start_yesterday = yesterday - timedelta(hours=1)
    end_yesterday = yesterday + timedelta(hours=1)
    sales_yesterday = repository.get_sales_by_period(start_yesterday, end_yesterday)
    assert len(sales_yesterday) == 1
    assert sales_yesterday[0].payment_type == "CARD"  # The payment type we used for yesterday's sale
    
    # Two days (yesterday and today)
    start_recent = yesterday - timedelta(hours=1)
    end_recent = now + timedelta(hours=1)
    sales_recent = repository.get_sales_by_period(start_recent, end_recent)
    assert len(sales_recent) == 2
