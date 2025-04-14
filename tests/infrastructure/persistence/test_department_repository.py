import pytest
from sqlalchemy.exc import IntegrityError

# Adjust path to import from the project root
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Imports for testing
from core.models.product import Department, Product
# Import repository classes directly
from infrastructure.persistence.sqlite.repositories import SqliteDepartmentRepository, SqliteProductRepository
from infrastructure.persistence.sqlite.database import engine, Base # For setup
from infrastructure.persistence.sqlite.models_mapping import DepartmentOrm, ProductOrm
print("id(ProductOrm) in test_department_repository.py:", id(ProductOrm))

print("id(Base):", id(Base))
print("id(ProductOrm.__bases__[0]):", id(ProductOrm.__bases__[0]))
from sqlalchemy import delete

# Fixture to set up the database schema once per module
@pytest.fixture(scope="module", autouse=True)
def setup_database_schema():
    """Set up the database schema for this module."""
    print("Creating tables for test database...")
    # Explicitly import all ORM models to ensure registration with Base
    # (Direct class imports are used at the top of the file.)
    # Create all tables
    Base.metadata.create_all(engine)
    Base.metadata.create_all(engine)
    print("Base.metadata.tables.keys():", list(Base.metadata.tables.keys()))
    print("id(Base):", id(Base))
    print("id(ProductOrm.__bases__[0]):", id(ProductOrm.__bases__[0]))
    # Access __table__ attributes to ensure registration
    _ = ProductOrm.__table__
    _ = DepartmentOrm.__table__
    
    yield
    
    print("Dropping tables from test database...")
    # Clean up by dropping all tables
    Base.metadata.drop_all(engine)

# Fixture to provide a repository instance for each test
@pytest.fixture
def department_repo(test_db_session):
    # Repository instantiation with test_db_session
    return SqliteDepartmentRepository(test_db_session)

# --- Test Cases ---

def test_add_department(department_repo):
    """Test adding a new department and retrieving it."""
    new_dept = Department(name="Fresh Bakery")
    added_dept = department_repo.add(new_dept)
    assert added_dept.id is not None
    assert added_dept.name == "Fresh Bakery"

    # Verify retrieval works
    retrieved_dept = department_repo.get_by_id(added_dept.id)
    assert retrieved_dept is not None
    assert retrieved_dept.id == added_dept.id
    assert retrieved_dept.name == "Fresh Bakery"

def test_add_department_duplicate_name(department_repo):
    """Test that adding a department with a duplicate name raises an error."""
    department_repo.add(Department(name="Produce")) # Add first time

    with pytest.raises(ValueError): # Changed from IntegrityError to ValueError
        department_repo.add(Department(name="Produce"))

def test_get_department_by_id(department_repo):
    """Test retrieving a department by its ID."""
    dept1 = department_repo.add(Department(name="Dairy"))
    retrieved_dept = department_repo.get_by_id(dept1.id)
    assert retrieved_dept is not None
    assert retrieved_dept.id == dept1.id
    assert retrieved_dept.name == "Dairy"

def test_get_department_by_id_not_found(department_repo):
    """Test retrieving a non-existent department ID returns None."""
    retrieved_dept = department_repo.get_by_id(9999)
    assert retrieved_dept is None

def test_get_department_by_name(department_repo):
    """Test retrieving a department by its name."""
    department_repo.add(Department(name="Meat"))
    retrieved_dept = department_repo.get_by_name("Meat")
    assert retrieved_dept is not None
    assert retrieved_dept.name == "Meat"

def test_get_department_by_name_not_found(department_repo):
    """Test retrieving a non-existent department name returns None."""
    retrieved_dept = department_repo.get_by_name("NonExistentDept")
    assert retrieved_dept is None

def test_get_all_departments(department_repo, test_db_session):
    """Test retrieving all departments."""
    # Clear any existing departments first for a clean slate
    test_db_session.query(DepartmentOrm).delete()
    test_db_session.flush()

    depts_data = [Department(name="Frozen"), Department(name="Canned Goods"), Department(name="Beverages")]
    for dept in depts_data:
        department_repo.add(dept)

    all_depts = department_repo.get_all()
    assert len(all_depts) == 3
    # Verify names are present and potentially check order (should be alphabetical)
    retrieved_names = sorted([d.name for d in all_depts])
    assert retrieved_names == ["Beverages", "Canned Goods", "Frozen"]

def test_update_department(department_repo):
    """Test updating an existing department's name."""
    dept_to_update = department_repo.add(Department(name="Old Name"))
    dept_to_update.name = "New Name"
    department_repo.update(dept_to_update)

    # Verify the update
    retrieved_dept = department_repo.get_by_id(dept_to_update.id)
    assert retrieved_dept is not None
    assert retrieved_dept.name == "New Name"

    # Test updating non-existent department (should raise ValueError)
    non_existent_dept = Department(id=8888, name="Ghost")
    with pytest.raises(ValueError):
        department_repo.update(non_existent_dept)

def test_delete_department(department_repo):
    """Test deleting a department."""
    import time
    unique_name = f"ToDelete_{int(time.time())}"
    dept_to_delete = department_repo.add(Department(name=unique_name))
    dept_id = dept_to_delete.id

    department_repo.delete(dept_id)

    # Verify it's gone
    assert department_repo.get_by_id(dept_id) is None

    # Test deleting non-existent (should not raise error)
    try:
        department_repo.delete(9999)
    except Exception as e:
        pytest.fail(f"Deleting non-existent department raised an error: {e}")

def test_delete_department_with_linked_products_raises_error(department_repo, test_db_session):
    """Test that we can't delete a department with linked products."""
    import time

    # Generate unique identifiers for this test run
    unique_suffix = str(int(time.time()))
    unique_dept_name = f"LinkedDept_{unique_suffix}"
    unique_product_code = f"P{unique_suffix}"

    # Add a department with a unique name
    dept = department_repo.add(Department(name=unique_dept_name))

    # Add a product linked to this department
    product_repo = SqliteProductRepository(test_db_session)
    product = Product(
        code=unique_product_code,
        description="Test Product",
        cost_price=10.0,
        sell_price=15.0,
        department_id=dept.id
    )
    product_repo.add(product)
    test_db_session.flush()

    # Attempt to delete the department - this should raise a ValueError because
    # the repository should check for linked products before deletion
    with pytest.raises(ValueError):
        department_repo.delete(dept.id)