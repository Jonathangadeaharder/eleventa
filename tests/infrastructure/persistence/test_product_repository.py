import pytest
from sqlalchemy.exc import IntegrityError
import datetime

# Adjust path to import from the project root
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Imports for testing
from core.models.product import Product, Department
# Import repository classes directly
from infrastructure.persistence.sqlite.repositories import (
    SqliteProductRepository, 
    SqliteDepartmentRepository
)
from infrastructure.persistence.sqlite.database import engine, Base
from infrastructure.persistence.sqlite.models_mapping import DepartmentOrm, ProductOrm

# Fixture to set up the database schema once per module
@pytest.fixture(scope="module", autouse=True)
def setup_database_schema():
    Base.metadata.create_all(bind=engine)
    yield
    # Base.metadata.drop_all(bind=engine) # Cleanup handled by main fixture

# Fixture to provide a repository instance for each test
@pytest.fixture
def product_repo(test_db_session):
    return SqliteProductRepository(test_db_session)

# Fixture to provide a department repository and create a sample department
@pytest.fixture
def sample_dept(test_db_session):
    """Creates a sample department for product tests, ensuring cleanup."""
    dept_repo = SqliteDepartmentRepository(test_db_session)
    dept_names_to_clean = ["Testing Dept", "Other Dept", "Update Target Dept"]

    # Clean up potentially existing conflicting departments first
    for name in dept_names_to_clean:
        existing = test_db_session.query(DepartmentOrm).filter_by(name=name).first()
        if existing:
            # Delete associated products first
            test_db_session.query(ProductOrm).filter_by(department_id=existing.id).delete(synchronize_session=False)
            test_db_session.delete(existing)
    test_db_session.flush()

    # Now create the primary testing department
    dept = Department(name="Testing Dept")
    added_dept = dept_repo.add(dept)
    return added_dept # Return the created department with its ID

# --- Test Cases ---

def test_add_product(product_repo, sample_dept):
    """Test adding a new product and retrieving it."""
    new_prod = Product(
        code="TEST001",
        description="Test Product One",
        cost_price=10.0,
        sell_price=20.0,
        department_id=sample_dept.id
    )
    added_prod = product_repo.add(new_prod)

    assert added_prod.id is not None
    assert added_prod.code == "TEST001"
    assert added_prod.description == "Test Product One"
    assert added_prod.department_id == sample_dept.id

    # Verify it can be retrieved
    retrieved_prod = product_repo.get_by_id(added_prod.id)
    assert retrieved_prod is not None
    assert retrieved_prod.id == added_prod.id
    assert retrieved_prod.code == "TEST001"
    assert retrieved_prod.department_id == sample_dept.id
    # Check if department object is loaded (depends on repo implementation)
    assert retrieved_prod.department is not None
    assert retrieved_prod.department.id == sample_dept.id
    assert retrieved_prod.department.name == "Testing Dept"

def test_add_product_duplicate_code(product_repo, sample_dept):
    """Test that adding a product with a duplicate code raises an error."""
    product_repo.add(Product(code="DUP001", description="Duplicate 1", department_id=sample_dept.id))

    with pytest.raises(ValueError):
        product_repo.add(Product(code="DUP001", description="Duplicate 2", department_id=sample_dept.id))

def test_get_product_by_id(product_repo, sample_dept):
    """Test retrieving a product by its ID, including department."""
    prod1 = product_repo.add(Product(code="GETID01", description="Get By ID Test", department_id=sample_dept.id))
    retrieved_prod = product_repo.get_by_id(prod1.id)

    assert retrieved_prod is not None
    assert retrieved_prod.id == prod1.id
    assert retrieved_prod.code == "GETID01"
    assert retrieved_prod.department is not None
    assert retrieved_prod.department.id == sample_dept.id
    assert retrieved_prod.department.name == "Testing Dept"

def test_get_product_by_id_not_found(product_repo):
    """Test retrieving a non-existent product ID returns None."""
    retrieved_prod = product_repo.get_by_id(99999)
    assert retrieved_prod is None

def test_get_product_by_code(product_repo, sample_dept):
    """Test retrieving a product by its code."""
    prod1 = product_repo.add(Product(code="GETCODE01", description="Get By Code Test", department_id=sample_dept.id))
    retrieved_prod = product_repo.get_by_code("GETCODE01")

    assert retrieved_prod is not None
    assert retrieved_prod.id == prod1.id
    assert retrieved_prod.code == "GETCODE01"
    assert retrieved_prod.department is not None
    assert retrieved_prod.department.id == sample_dept.id

def test_get_product_by_code_not_found(product_repo):
    """Test retrieving a non-existent product code returns None."""
    retrieved_prod = product_repo.get_by_code("NONEXISTENTCODE")
    assert retrieved_prod is None

def test_get_all_products(product_repo, sample_dept, test_db_session):
    """Test retrieving all products."""
    # Clear existing products first
    test_db_session.query(ProductOrm).delete()

    prod1 = product_repo.add(Product(code="ALL01", description="All Prod 1", department_id=sample_dept.id))
    prod2 = product_repo.add(Product(code="ALL02", description="All Prod 2", department_id=sample_dept.id))

    all_prods = product_repo.get_all()
    assert len(all_prods) == 2
    retrieved_codes = sorted([p.code for p in all_prods])
    assert retrieved_codes == ["ALL01", "ALL02"]

def test_update_product(product_repo, sample_dept, test_db_session):
    """Test updating various fields of an existing product."""
    prod_to_update = product_repo.add(Product(
        code="UPD01", description="Original Desc", cost_price=5.0, sell_price=10.0,
        department_id=sample_dept.id, uses_inventory=True, quantity_in_stock=10
    ))

    prod_to_update.description = "Updated Desc"
    prod_to_update.sell_price = 12.50
    prod_to_update.uses_inventory = False
    # Create a new department with a unique name
    dept_repo = SqliteDepartmentRepository(test_db_session)
    other_dept = dept_repo.add(Department(name="Update Target Dept")) # Use unique name
    prod_to_update.department_id = other_dept.id
    prod_to_update.department = None # Clear loaded department for update

    product_repo.update(prod_to_update)

    # Verify the update
    retrieved_prod = product_repo.get_by_id(prod_to_update.id)
    assert retrieved_prod is not None
    assert retrieved_prod.description == "Updated Desc"
    assert retrieved_prod.sell_price == 12.50
    assert retrieved_prod.uses_inventory is False
    assert retrieved_prod.department_id == other_dept.id
    assert retrieved_prod.department is not None
    assert retrieved_prod.department.name == "Update Target Dept" # Verify correct dept name
    # Ensure other fields didn't change unintentionally
    assert retrieved_prod.code == "UPD01"
    assert retrieved_prod.cost_price == 5.0
    assert retrieved_prod.quantity_in_stock == 10

    # For non-existent product, we expect a ValueError to be raised
    non_existent_prod = Product(id=7777, code="GHOST", description="Ghost Prod")
    with pytest.raises(ValueError, match="not found for update"):
        product_repo.update(non_existent_prod)

def test_delete_product(product_repo, sample_dept):
    """Test deleting a product."""
    prod_to_delete = product_repo.add(Product(code="DEL01", description="To Delete", department_id=sample_dept.id))
    prod_id = prod_to_delete.id

    product_repo.delete(prod_id)

    # Verify it's deleted
    retrieved_prod = product_repo.get_by_id(prod_id)
    assert retrieved_prod is None

    # Test deleting non-existent (should not raise error)
    try:
        product_repo.delete(88888)
    except Exception as e:
        pytest.fail(f"Deleting non-existent product raised an error: {e}")

def test_search_product(product_repo, sample_dept, test_db_session):
    """Test searching for products by code or description."""
    # Clear existing products
    test_db_session.query(ProductOrm).delete()

    prod1 = product_repo.add(Product(code="SRCH01", description="Apple iPhone", department_id=sample_dept.id))
    prod2 = product_repo.add(Product(code="SRCH02", description="Samsung Galaxy", department_id=sample_dept.id))
    prod3 = product_repo.add(Product(code="MISC01", description="Generic Apple Case", department_id=sample_dept.id))

    # Search by exact code
    results = product_repo.search("SRCH01")
    assert len(results) == 1
    assert results[0].id == prod1.id

    # Search by partial code
    results = product_repo.search("SRCH")
    assert len(results) == 2
    assert sorted([p.id for p in results]) == sorted([prod1.id, prod2.id])

    # Search by description fragment (case-insensitive)
    results = product_repo.search("apple")
    assert len(results) == 2
    assert sorted([p.id for p in results]) == sorted([prod1.id, prod3.id])

    # Search by description fragment
    results = product_repo.search("Galaxy")
    assert len(results) == 1
    assert results[0].id == prod2.id

    # Search with no results
    results = product_repo.search("NoSuchProduct")
    assert len(results) == 0

def test_update_stock(product_repo, sample_dept):
    """Test updating only the stock quantity of a product."""
    prod = product_repo.add(Product(
        code="STOCK01", description="Stock Update Test",
        sell_price=50.0, department_id=sample_dept.id, quantity_in_stock=25.0
    ))

    product_repo.update_stock(prod.id, 35.5)

    # Verify update
    retrieved_prod = product_repo.get_by_id(prod.id)
    assert retrieved_prod is not None
    assert retrieved_prod.quantity_in_stock == 35.5
    # Verify other fields are unchanged
    assert retrieved_prod.description == "Stock Update Test"
    assert retrieved_prod.sell_price == 50.0

    # Test update non-existent (should not raise error)
    try:
        product_repo.update_stock(76543, 100.0)
    except Exception as e:
        pytest.fail(f"update_stock on non-existent product raised an error: {e}")

def test_get_low_stock(product_repo, sample_dept, test_db_session):
    """Test retrieving products with low stock levels."""
    # Clear existing products
    test_db_session.query(ProductOrm).delete()

    # Product that uses inventory and is low
    prod_low = product_repo.add(Product(
        code="LOW01", description="Low Stock Item", uses_inventory=True,
        quantity_in_stock=5, min_stock=10, department_id=sample_dept.id
    ))
    # Product that uses inventory and is exactly at min stock (should be included)
    prod_exact = product_repo.add(Product(
        code="LOW02", description="Exact Stock Item", uses_inventory=True,
        quantity_in_stock=10, min_stock=10, department_id=sample_dept.id
    ))
    # Product that uses inventory and is above min stock
    prod_ok = product_repo.add(Product(
        code="LOW03", description="OK Stock Item", uses_inventory=True,
        quantity_in_stock=15, min_stock=10, department_id=sample_dept.id
    ))
    # Product that doesn't use inventory (should not be included)
    prod_no_inv = product_repo.add(Product(
        code="LOW04", description="No Inventory Item", uses_inventory=False,
        quantity_in_stock=0, min_stock=10, department_id=sample_dept.id
    ))
    # Product using inventory with min_stock=None (should not be included)
    prod_min_none = product_repo.add(Product(
        code="LOW05", description="Min Stock None", uses_inventory=True,
        quantity_in_stock=1, min_stock=None, department_id=sample_dept.id
    ))

    low_stock_prods = product_repo.get_low_stock()

    assert len(low_stock_prods) == 2
    retrieved_ids = sorted([p.id for p in low_stock_prods])
    assert retrieved_ids == sorted([prod_low.id, prod_exact.id])

    # Test with explicit threshold (implementation might vary)
    # Assuming default implementation compares quantity_in_stock <= min_stock
    # If get_low_stock accepts a threshold, add tests for that. 