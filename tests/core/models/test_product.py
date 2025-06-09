import pytest
import datetime
from decimal import Decimal

# Adjust path to import from the project root
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.models.product import Department, Product

def test_department_creation():
    """Test creating a Department object with default and specific values."""
    # Test default creation
    dept_default = Department()
    assert dept_default.id is None
    assert dept_default.name == ""

    # Test creation with specific values
    dept1 = Department(id=1, name="Electronics")
    assert dept1.id == 1
    assert dept1.name == "Electronics"

def test_product_creation():
    """Test creating a Product object with default and specific values."""
    # Test default creation
    prod_default = Product()
    assert prod_default.id is None
    assert prod_default.code == ""
    assert prod_default.description == ""
    assert prod_default.cost_price == Decimal('0.0')
    assert prod_default.sell_price == Decimal('0.0')
    assert prod_default.wholesale_price is None
    assert prod_default.special_price is None
    assert prod_default.department_id is None
    assert prod_default.department is None
    assert prod_default.unit == "Unidad"
    assert prod_default.uses_inventory is True
    assert prod_default.quantity_in_stock == Decimal('0.0')
    assert prod_default.min_stock == Decimal('0.0')
    assert prod_default.max_stock is None
    assert prod_default.last_updated is None
    assert prod_default.notes is None
    assert prod_default.is_active is True

    # Test creation with specific values
    now = datetime.datetime.now()
    dept = Department(id=5, name="Groceries")
    prod1 = Product(
        id=101,
        code="PROD001",
        description="Test Product 1",
        cost_price=10.50,
        sell_price=19.99,
        wholesale_price=18.00,
        department_id=5,
        department=dept,
        unit="Kg",
        uses_inventory=False,
        quantity_in_stock=50.5,
        min_stock=5.0,
        max_stock=100.0,
        last_updated=now,
        notes="Sample note",
        is_active=False
    )
    assert prod1.id == 101
    assert prod1.code == "PROD001"
    assert prod1.description == "Test Product 1"
    assert prod1.cost_price == Decimal('10.50')
    assert prod1.sell_price == Decimal('19.99')
    assert prod1.wholesale_price == Decimal('18.00')
    assert prod1.special_price is None # Check default for unspecified optional
    assert prod1.department_id == 5
    assert prod1.department == dept
    assert prod1.unit == "Kg"
    assert prod1.uses_inventory is False
    assert prod1.quantity_in_stock == Decimal('50.5')
    assert prod1.min_stock == Decimal('5.0')
    assert prod1.max_stock == Decimal('100.0')
    assert prod1.last_updated == now
    assert prod1.notes == "Sample note"
    assert prod1.is_active is False

def test_product_edge_cases():
    """Test Product with edge/invalid values (negative prices, empty strings, negative stock)."""
    # Negative prices
    prod_neg_price = Product(cost_price=-5.0, sell_price=-10.0)
    assert prod_neg_price.cost_price == Decimal('-5.0')
    assert prod_neg_price.sell_price == Decimal('-10.0')

    # Negative stock
    prod_neg_stock = Product(quantity_in_stock=-100.0, min_stock=-1.0)
    assert prod_neg_stock.quantity_in_stock == Decimal('-100.0')
    assert prod_neg_stock.min_stock == Decimal('-1.0')

    # Empty strings for code and description
    prod_empty = Product(code="", description="")
    assert prod_empty.code == ""
    assert prod_empty.description == ""

    # Extremely large values
    prod_large = Product(cost_price=1e12, sell_price=1e12, quantity_in_stock=1e9)
    assert prod_large.cost_price == Decimal('1e12')
    assert prod_large.sell_price == Decimal('1e12')
    assert prod_large.quantity_in_stock == Decimal('1e9')

def test_department_edge_cases():
    """Test Department with edge/invalid values (empty name, None id)."""
    dept_empty = Department(name="")
    assert dept_empty.name == ""
    dept_none_id = Department(id=None)
    assert dept_none_id.id is None