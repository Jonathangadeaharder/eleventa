import pytest
import random
import uuid
import datetime
from decimal import Decimal
import time
from sqlalchemy import delete, text
import sys
import os

# Ensure project root is in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.models.product import Product, Department
from infrastructure.persistence.sqlite.repositories import SqliteProductRepository, SqliteDepartmentRepository
from infrastructure.persistence.sqlite.database import Base, engine
from infrastructure.persistence.sqlite.models_mapping import ProductOrm, DepartmentOrm

# --- Helper Functions ---

def create_department(session, name="Testing Dept"):
    """Adds a department to the session but does NOT commit."""
    dept_repo = SqliteDepartmentRepository(session)
    dept = Department(name=name)
    added_dept = dept_repo.add(dept)
    # NO COMMIT HERE
    return added_dept

# --- Test Functions ---

@pytest.fixture
def setup_department(test_db_session):
    """Fixture to create and return a test department."""
    dept = create_department(test_db_session)
    assert dept.id is not None
    return dept

def test_add_product(test_db_session, setup_department, request):
    """Test adding a new product with transactional isolation."""
    
    # Test setup
    dept = setup_department
    repo = SqliteProductRepository(test_db_session)
    product = Product(code="TEST001", description="Test Product", cost_price=10.0, sell_price=10.99, department_id=dept.id, quantity_in_stock=100)
    
    # Execute operation
    added_product = repo.add(product)
    
    # Assertions
    assert added_product.id is not None
    assert added_product.code == "TEST001"
    db_product = test_db_session.query(ProductOrm).filter_by(id=added_product.id).first()
    assert db_product is not None
    assert db_product.code == "TEST001"
    

def test_add_product_duplicate_code(test_db_session, setup_department):
    """Test adding a product with a duplicate code raises error."""
    dept = setup_department
    repo = SqliteProductRepository(test_db_session)
    # Add first product, commit
    product1 = Product(code="DUP001", description="Duplicate 1", department_id=dept.id)
    repo.add(product1)

    # Try adding second with same code
    product2 = Product(code="DUP001", description="Duplicate 2", department_id=dept.id)
    with pytest.raises(ValueError):
        repo.add(product2)

def test_get_product_by_id(test_db_session, setup_department, request):
    """Test retrieving a product by ID with transactional isolation."""
    
    # Test setup
    dept = setup_department
    repo = SqliteProductRepository(test_db_session)
    # Add product
    prod1 = repo.add(Product(code="GETID01", description="Get By ID Test", department_id=dept.id))
    
    # Execute operation
    retrieved_prod = repo.get_by_id(prod1.id)

    # Assertions
    assert retrieved_prod is not None
    assert retrieved_prod.id == prod1.id
    assert retrieved_prod.department is not None
    assert retrieved_prod.department.id == dept.id
    

def test_get_product_by_id_not_found(test_db_session):
    """Test retrieving a non-existent product by ID returns None."""
    repo = SqliteProductRepository(test_db_session)
    retrieved_prod = repo.get_by_id(99999)
    assert retrieved_prod is None

def test_get_product_by_code(test_db_session, setup_department, request):
    """Test retrieving a product by code with transactional isolation."""
    
    # Test setup
    dept = setup_department
    repo = SqliteProductRepository(test_db_session)
    
    # Add product
    prod1 = repo.add(Product(code="GETCODE01", description="Get By Code Test", department_id=dept.id))
    
    # Execute operation
    retrieved_prod = repo.get_by_code("GETCODE01")

    # Assertions
    assert retrieved_prod is not None
    assert retrieved_prod.id == prod1.id
    assert retrieved_prod.department is not None
    assert retrieved_prod.department.id == dept.id
    

def test_get_product_by_code_not_found(test_db_session):
    """Test retrieving a non-existent product by code returns None."""
    repo = SqliteProductRepository(test_db_session)
    retrieved_prod = repo.get_by_code("NONEXISTENTCODE")
    assert retrieved_prod is None

def test_get_all_products(test_db_session, setup_department, request):
    """Test retrieving all products with transactional isolation."""
    
    # Test setup
    dept = setup_department
    repo = SqliteProductRepository(test_db_session)
    
    # Add products and commit
    prod1 = repo.add(Product(code="ALL01", description="All Prod 1", department_id=dept.id))
    prod2 = repo.add(Product(code="ALL02", description="All Prod 2", department_id=dept.id))

    all_prods = repo.get_all()
    assert len(all_prods) == 2
    retrieved_codes = sorted([p.code for p in all_prods])
    assert retrieved_codes == ["ALL01", "ALL02"]
    

def test_update_product(test_db_session, setup_department, request):
    """Test updating an existing product with transactional isolation."""
    
    # Test setup
    dept = setup_department
    repo = SqliteProductRepository(test_db_session)
    # Add product
    prod_to_update = repo.add(Product(
        code="UPD01", description="Original Desc", cost_price=5.0, sell_price=10.0,
        department_id=dept.id, uses_inventory=True, quantity_in_stock=10
    ))
    original_id = prod_to_update.id

    # Create a new department specifically for this test
    dept_repo = SqliteDepartmentRepository(test_db_session)
    update_dept_name = f"Update Target Dept {int(time.time()*1000)}"
    other_dept = dept_repo.add(Department(name=update_dept_name))
    test_db_session.commit()  # Ensure the department is committed
    assert other_dept.id is not None

    # Modify product object IN MEMORY
    prod_to_update = repo.get_by_id(original_id) # Re-fetch might be safer
    prod_to_update.description = "Updated Desc"
    prod_to_update.sell_price = Decimal("12.50")
    prod_to_update.uses_inventory = False
    prod_to_update.department_id = other_dept.id

    # Execute operation
    updated_prod = repo.update(prod_to_update)
    test_db_session.flush()  # Ensure changes are visible
    
    # Assertions
    assert updated_prod is not None
    assert updated_prod.id == original_id

    # Verify the update by fetching fresh from DB
    retrieved_prod = repo.get_by_id(original_id)
    assert retrieved_prod is not None
    assert retrieved_prod.description == "Updated Desc"
    assert retrieved_prod.sell_price == Decimal("12.50")
    assert retrieved_prod.uses_inventory is False
    assert retrieved_prod.department_id == other_dept.id
    
    # Get department associated with the product
    assert retrieved_prod.department is not None
    assert retrieved_prod.department.id == other_dept.id
    # Check department name
    assert retrieved_prod.department.name == update_dept_name

    # Test updating non-existent product
    non_existent_prod = Product(id=7777, code="GHOST", description="Ghost Prod", department_id=dept.id)
    with pytest.raises(ValueError, match="Product with ID 7777 not found"):
        repo.update(non_existent_prod)
    

def test_delete_product(test_db_session, setup_department, request):
    """Test deleting an existing product with transactional isolation."""
    
    # Add product
    dept = setup_department
    repo = SqliteProductRepository(test_db_session)
    prod_to_delete = repo.add(Product(code="DEL01", description="To Delete", department_id=dept.id))
    prod_id = prod_to_delete.id

    # Delete product
    repo.delete(prod_id)

    # Verify it's deleted
    retrieved_prod = repo.get_by_id(prod_id)
    assert retrieved_prod is None

    # Make sure we don't manually rollback, let the fixture handle it
    # Verify product is actually deleted by checking directly in ORM
    deleted_check = test_db_session.query(ProductOrm).filter_by(id=prod_id).first()
    assert deleted_check is None
    
    # Test deleting non-existent (should not raise error)
    try:
        repo.delete(88888)
    except Exception as e:
        pytest.fail(f"Deleting non-existent product raised an error: {e}")

def test_search_product(test_db_session, setup_department):
    """Test searching for products."""
    dept = setup_department
    repo = SqliteProductRepository(test_db_session)

    # Add products and commit
    prod1 = repo.add(Product(code="SRCH01", description="Apple iPhone", department_id=dept.id))
    prod2 = repo.add(Product(code="SRCH02", description="Samsung Galaxy", department_id=dept.id))
    prod3 = repo.add(Product(code="MISC01", description="Generic Apple Case", department_id=dept.id))

    results = repo.search("SRCH01")
    assert len(results) == 1
    assert results[0].id == prod1.id

    results = repo.search("SRCH")
    assert len(results) == 2
    assert sorted([p.id for p in results]) == sorted([prod1.id, prod2.id])

    results = repo.search("apple")
    assert len(results) == 2
    assert sorted([p.id for p in results]) == sorted([prod1.id, prod3.id])

    results = repo.search("Galaxy")
    assert len(results) == 1
    assert results[0].id == prod2.id

    results = repo.search("NoSuchProduct")
    assert len(results) == 0

def test_update_stock(test_db_session, setup_department, request):
    """Test updating product stock with transactional isolation."""
    
    # Test setup
    dept = setup_department
    repo = SqliteProductRepository(test_db_session)
    # Add product, commit
    prod = repo.add(Product(
        code="STOCK01", description="Stock Update Test",
        sell_price=50.0, department_id=dept.id, quantity_in_stock=25.0
    ))
    original_id = prod.id
    
    # Update stock and commit
    updated_stock_value = Decimal("35.5")
    repo.update_stock(original_id, updated_stock_value)

    # Verify update by fetching fresh
    retrieved_prod = repo.get_by_id(original_id)
    assert retrieved_prod is not None
    # Convert both to float for comparison
    assert abs(float(retrieved_prod.quantity_in_stock) - float(updated_stock_value)) < 0.0001

    # Test update stock for non-existent product
    try:
        repo.update_stock(8888, Decimal("10"))
        assert repo.get_by_id(8888) is None
    except Exception as e:
        test_db_session.rollback()
        pytest.fail(f"update_stock on non-existent product raised an error: {e}")
    

def test_get_low_stock(test_db_session, setup_department, request):
    """Test retrieving products with low stock with transactional isolation."""
    
    # Test setup
    dept = setup_department
    repo = SqliteProductRepository(test_db_session)

    # Add products, commit
    prod_low = repo.add(Product(
        code="LOW01", description="Low Stock Item", uses_inventory=True,
        quantity_in_stock=5, min_stock=10, department_id=dept.id
    ))
    prod_exact = repo.add(Product(
        code="LOW02", description="Exact Stock Item", uses_inventory=True,
        quantity_in_stock=10, min_stock=10, department_id=dept.id
    ))
    prod_ok = repo.add(Product(
        code="LOW03", description="OK Stock Item", uses_inventory=True,
        quantity_in_stock=15, min_stock=10, department_id=dept.id
    ))
    prod_no_inv = repo.add(Product(
        code="LOW04", description="No Inventory Item", uses_inventory=False,
        quantity_in_stock=0, min_stock=10, department_id=dept.id
    ))
    prod_min_none = repo.add(Product(
        code="LOW05", description="Min Stock None", uses_inventory=True,
        quantity_in_stock=1, min_stock=None, department_id=dept.id
    ))
    
    # Retrieve low stock
    low_stock_products = repo.get_low_stock()
    assert len(low_stock_products) == 2 # LOW01 and LOW02
    low_stock_codes = {p.code for p in low_stock_products}
    assert "LOW01" in low_stock_codes
    assert "LOW02" in low_stock_codes
    assert "LOW03" not in low_stock_codes
    assert "LOW04" not in low_stock_codes
    assert "LOW05" not in low_stock_codes
    

def test_get_all_products_filtered_and_paginated(test_db_session, setup_department, request):
    """Test retrieving products with filtering and pagination with transactional isolation."""
    
    # Test setup
    dept = setup_department
    repo = SqliteProductRepository(test_db_session)
    # Add products, commit
    prod_a1 = repo.add(Product(code="FPA01", description="A1 Active", department_id=dept.id, is_active=True))
    prod_a2 = repo.add(Product(code="FPA02", description="A2 Inactive", department_id=dept.id, is_active=False))

    # Test filtering
    results_dept = repo.get_all(filter_params={"department_id": dept.id})
    assert len(results_dept) == 2
    assert {p.code for p in results_dept} == {"FPA01", "FPA02"}

    results_active = repo.get_all(filter_params={"is_active": True})
    assert len(results_active) == 1
    assert results_active[0].code == "FPA01"

    # Test pagination
    all_prods = repo.get_all(sort_params={'sort_by': 'code', 'sort_order': 'asc'})
    page1 = repo.get_all(pagination_params={"page": 1, "page_size": 1}, sort_params={'sort_by': 'code', 'sort_order': 'asc'})
    page2 = repo.get_all(pagination_params={"page": 2, "page_size": 1}, sort_params={'sort_by': 'code', 'sort_order': 'asc'})
    assert len(page1) == 1
    assert len(page2) == 1
    assert page1[0].code == all_prods[0].code
    assert page2[0].code == all_prods[1].code
    

def test_get_all_products_sorting(test_db_session, setup_department, request):
    """Test retrieving products with sorting with transactional isolation."""
    
    # Test setup
    dept = setup_department
    repo = SqliteProductRepository(test_db_session)
    # Add products, commit
    prod_b = repo.add(Product(code="SORT01", description="Banana", sell_price=Decimal("1.50"), department_id=dept.id))
    prod_a = repo.add(Product(code="SORT02", description="Apple", sell_price=Decimal("2.00"), department_id=dept.id))
    prod_c = repo.add(Product(code="SORT03", description="Cherry", sell_price=Decimal("1.00"), department_id=dept.id))
    prod_d = repo.add(Product(code="SORT04", description="Apple Pie", sell_price=Decimal("3.00"), department_id=dept.id, is_active=False))

    # Test sorting
    sorted_desc = repo.get_all(sort_params={"sort_by": "description", "sort_order": "asc"})
    assert [p.code for p in sorted_desc] == ["SORT02", "SORT04", "SORT01", "SORT03"]

    # Sort by sell_price descending
    sorted_price = repo.get_all(sort_params={"sort_by": "sell_price", "sort_order": "desc"})
    assert [p.code for p in sorted_price] == ["SORT04", "SORT02", "SORT01", "SORT03"]

    # Sort by code descending
    sorted_code = repo.get_all(sort_params={"sort_by": "code", "sort_order": "desc"})
    assert [p.code for p in sorted_code] == ["SORT04", "SORT03", "SORT02", "SORT01"]
