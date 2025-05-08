import pytest
import time
from sqlalchemy.exc import IntegrityError
from sqlalchemy import delete, text

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
from infrastructure.persistence.sqlite.database import Base, engine # For setup
from infrastructure.persistence.sqlite.models_mapping import DepartmentOrm, ProductOrm

# Remove potentially conflicting debug prints
# print("id(ProductOrm) in test_department_repository.py:", id(ProductOrm))
# print("id(Base):", id(Base))
# print("id(ProductOrm.__bases__[0]):", id(ProductOrm.__bases__[0]))

# Remove unused fixtures
# @pytest.fixture
# def department_repo(test_db_session):
#     return SqliteDepartmentRepository(test_db_session)

# Helper function adjusted to NOT commit
def create_department(session, name="Testing Dept"):
    """Adds a department to the session but does NOT commit."""
    dept_repo = SqliteDepartmentRepository(session)
    dept = Department(name=name)
    added_dept = dept_repo.add(dept)
    # NO COMMIT HERE - Let the test function handle commit
    return added_dept

@pytest.fixture
def setup_department(test_db_session):
    """Fixture to create and return a test department."""
    dept = create_department(test_db_session)
    test_db_session.commit()
    assert dept.id is not None
    return dept
# Test functions (no class needed if using function-scoped fixtures directly)

def test_add_department(test_db_session, request):
    """Test adding a new department with transactional isolation."""
    # Use savepoint instead of nested transaction
    # test_db_session.begin_nested()
    
    # Test setup
    repo = SqliteDepartmentRepository(test_db_session)
    # Use helper to add (no manual commit needed)
    dept = create_department(test_db_session, name="Test Department Add")
    
    # Assertions
    assert dept.id is not None # ID is assigned after add/flush inside repo
    assert dept.name == "Test Department Add"
    
    # Verify in DB without explicit commit
    db_dept = test_db_session.query(DepartmentOrm).filter_by(id=dept.id).first()
    assert db_dept is not None
    assert db_dept.name == "Test Department Add"
    
    # Remove finalizer that calls rollback as the test_db_session fixture
    # will handle transaction cleanup
    # def finalizer():
    #     test_db_session.rollback()
    # request.addfinalizer(finalizer)

def test_add_department_duplicate_name(test_db_session):
    """Test adding a department with a duplicate name raises error."""
    repo = SqliteDepartmentRepository(test_db_session)
    
    # Create a unique department name for this test
    unique_name = f"UniqueTest_{int(time.time()*1000)}"
    
    # Add first department and commit
    dept1 = Department(name=unique_name)
    repo.add(dept1)
    test_db_session.commit()  # Commit explicitly to ensure it's in the database
    
    # Try adding second with same name
    dept2 = Department(name=unique_name)
    with pytest.raises(ValueError):
        repo.add(dept2)

def test_get_department_by_id(test_db_session, request):
    """Test retrieving a department by ID with transactional isolation."""
    # Remove nested transaction
    # test_db_session.begin_nested()
    
    # Test setup
    repo = SqliteDepartmentRepository(test_db_session)
    # Add dept using helper, then commit
    dept1 = create_department(test_db_session, name="FindMeByID")
    test_db_session.commit()
    
    # Execute operation
    retrieved_dept = repo.get_by_id(dept1.id)
    
    # Assertions
    assert retrieved_dept is not None
    assert retrieved_dept.id == dept1.id
    assert retrieved_dept.name == "FindMeByID"
    
    # Remove finalizer
    # def finalizer():
    #     test_db_session.rollback()
    # request.addfinalizer(finalizer)

def test_get_department_by_id_not_found(test_db_session):
    """Test retrieving a non-existent department by ID returns None."""
    repo = SqliteDepartmentRepository(test_db_session)
    retrieved_dept = repo.get_by_id(9999)
    assert retrieved_dept is None

def test_get_department_by_name(test_db_session, request):
    """Test retrieving a department by name with transactional isolation."""
    # Remove nested transaction
    # test_db_session.begin_nested()
    
    # Test setup
    repo = SqliteDepartmentRepository(test_db_session)
    # Add dept using helper, then commit
    dept_to_find = create_department(test_db_session, name="FindMeByName")
    test_db_session.commit()
    
    # Execute operation
    retrieved_dept = repo.get_by_name("FindMeByName")
    
    # Assertions
    assert retrieved_dept is not None
    assert retrieved_dept.id == dept_to_find.id
    assert retrieved_dept.name == "FindMeByName"
    
    # Remove finalizer
    # def finalizer():
    #     test_db_session.rollback()
    # request.addfinalizer(finalizer)

def test_get_department_by_name_not_found(test_db_session):
    """Test retrieving a non-existent department by name returns None."""
    repo = SqliteDepartmentRepository(test_db_session)
    retrieved_dept = repo.get_by_name("NonExistentDeptName")
    assert retrieved_dept is None

def test_get_all_departments(test_db_session, request):
    """Test retrieving all departments with transactional isolation."""
    # Remove nested transaction
    # test_db_session.begin_nested()
    
    # Clean up any existing departments that might interfere with this test
    # Use direct delete instead of the repository to avoid our own guard checks
    test_db_session.execute(delete(DepartmentOrm).where(
        DepartmentOrm.name.in_(["Frozen GetALL", "Canned Goods GetALL", "Beverages GetALL"])
    ))
    test_db_session.commit()
    
    # Generate unique department names using timestamp to avoid conflicts
    timestamp = int(time.time()*1000)
    name1 = f"Frozen GetALL {timestamp}"
    name2 = f"Canned Goods GetALL {timestamp}"
    name3 = f"Beverages GetALL {timestamp}"
    
    # Test setup
    repo = SqliteDepartmentRepository(test_db_session)
    
    # Add depts and commit
    repo.add(Department(name=name1))
    repo.add(Department(name=name2))
    repo.add(Department(name=name3))
    test_db_session.commit()

    # Execute operation
    all_depts = repo.get_all()
    
    # Filter to just the departments created in this test
    test_depts = [d for d in all_depts if d.name in [name1, name2, name3]]
    
    # Assertions
    assert len(test_depts) == 3
    retrieved_names = sorted([d.name for d in test_depts])
    assert sorted([name1, name2, name3]) == retrieved_names
    
    # Keep finalizer to clean up created data but don't use rollback
    def finalizer():
        test_db_session.execute(delete(DepartmentOrm).where(
            DepartmentOrm.name.in_([name1, name2, name3])
        ))
        test_db_session.commit()
    request.addfinalizer(finalizer)

def test_update_department(test_db_session, request):
    """Test updating an existing department with transactional isolation."""
    # Remove nested transaction
    # test_db_session.begin_nested()
    
    # Test setup
    repo = SqliteDepartmentRepository(test_db_session)
    
    # Add dept and commit
    dept_to_update = repo.add(Department(name="Old Name Update"))
    test_db_session.commit()
    
    # Update object and call repo update, then commit
    dept_to_update.name = "New Name Updated"
    repo.update(dept_to_update)
    test_db_session.commit()
  
    # Execute operation
    retrieved_dept = repo.get_by_id(dept_to_update.id)
    
    # Assertions
    assert retrieved_dept is not None
    assert retrieved_dept.name == "New Name Updated"

    # Test updating non-existent department
    non_existent_dept = Department(id=8888, name="Ghost Update")
    with pytest.raises(ValueError):
        repo.update(non_existent_dept)
    
    # Remove finalizer
    # def finalizer():
    #     test_db_session.rollback()
    # request.addfinalizer(finalizer)

def test_delete_department(test_db_session, request):
    """Test deleting an existing department with transactional isolation."""
    # Remove nested transaction
    # test_db_session.begin_nested()
    
    # Test setup
    repo = SqliteDepartmentRepository(test_db_session)
    unique_name = f"ToDelete_{int(time.time()*1000)}"
    # Add using helper, then commit
    dept_to_delete = create_department(test_db_session, name=unique_name)
    test_db_session.commit()
    dept_id = dept_to_delete.id
    
    # Verify exists
    check_exists = repo.get_by_id(dept_id)
    assert check_exists is not None, f"Department {dept_id} should exist before delete"
    
    # Delete (no manual commit needed)
    repo.delete(dept_id)
  
    # Verify it's gone
    check_gone = repo.get_by_id(dept_id)
    assert check_gone is None, f"Department {dept_id} should be None after delete"

    # Test deleting non-existent (no manual commit/rollback needed)
    with pytest.raises(ValueError):
        repo.delete(999999)
    
    # Remove finalizer
    # def finalizer():
    #     test_db_session.rollback()
    # request.addfinalizer(finalizer)

def test_delete_department_with_linked_products_raises_error(test_db_session, request):
    """Test deleting a department linked to products raises an error with transactional isolation."""
    import warnings
    from sqlalchemy import exc as sa_exc
    
    # Temporarily suppress the SQLAlchemy warnings for this specific test
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=sa_exc.SAWarning)
        
        # Test setup using the fixture session
        dept_repo = SqliteDepartmentRepository(test_db_session)
        product_repo = SqliteProductRepository(test_db_session)
      
        # Add department using helper (no commit yet)
        dept_name = f"DeptWithProd_{int(time.time()*1000)}"
        dept = create_department(test_db_session, name=dept_name)
        # Commit now so product can link via FK
        test_db_session.commit() 
        assert dept.id is not None
    
        # Add product using repo (no commit yet)
        product_code = f"P_LINKED_{int(time.time()*1000)}"
        product = Product(code=product_code, description="Linked Product", sell_price=1.0, department_id=dept.id)
        added_product = product_repo.add(product)
        # Commit product
        test_db_session.commit()
        assert added_product.id is not None
        assert added_product.department_id == dept.id
    
        # Attempt to delete the department
        with pytest.raises(ValueError, match="Departamento .* no puede ser eliminado, est.* en uso"):
            dept_repo.delete(dept.id)
