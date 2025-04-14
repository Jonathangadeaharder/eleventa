import pytest
from unittest.mock import MagicMock, call

# Adjust path to import from the project root
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.services.product_service import ProductService # To be created
from core.models.product import Product, Department
from core.interfaces.repository_interfaces import IProductRepository, IDepartmentRepository

# Fixtures for mocked repositories
@pytest.fixture
def mock_product_repo(mocker): # pytest-mock provides mocker fixture
    return mocker.MagicMock(spec=IProductRepository)

@pytest.fixture
def mock_dept_repo(mocker):
    return mocker.MagicMock(spec=IDepartmentRepository)

# Fixture for the service instance with mocked dependencies
@pytest.fixture
def product_service(mock_product_repo, mock_dept_repo):
    # Create factory functions that return the mocks, ignoring the session parameter
    def product_repo_factory(session):
        return mock_product_repo
        
    def department_repo_factory(session):
        return mock_dept_repo
        
    return ProductService(product_repo_factory, department_repo_factory)

# --- Test Cases for Product Operations ---

def test_add_product_success(product_service, mock_product_repo, mock_dept_repo):
    """Test successful addition of a valid product."""
    dept = Department(id=1, name="Valid Dept")
    # Define product data *without* id initially
    product_data = Product(
        code="P001", description="Valid Product", sell_price=10.0, cost_price=5.0,
        department_id=1
    )
    # Create the expected return value explicitly
    expected_added_product = Product(
        id=101, code="P001", description="Valid Product", sell_price=10.0, cost_price=5.0,
        department_id=1
    )
    # Mock repo calls
    mock_dept_repo.get_by_id.return_value = dept # Department exists
    mock_product_repo.get_by_code.return_value = None # Code is unique
    # mock_product_repo.add.return_value = Product(id=101, **product_data.__dict__)
    mock_product_repo.add.return_value = expected_added_product # Use explicitly created object

    added_product = product_service.add_product(product_data)

    mock_dept_repo.get_by_id.assert_called_once_with(1)
    mock_product_repo.get_by_code.assert_called_once_with("P001")
    mock_product_repo.add.assert_called_once_with(product_data)
    assert added_product is not None
    assert added_product.id == 101
    assert added_product.code == "P001"

@pytest.mark.parametrize("invalid_product, expected_error_msg", [
    (Product(code="", description="Test"), "Código es requerido"),
    (Product(code="P002", description=""), "Descripción es requerida"),
    (Product(code="P003", description="Test", sell_price=-1.0), "Precio de venta debe ser positivo"),
    (Product(code="P004", description="Test", cost_price=-5.0), "Precio de costo debe ser positivo"),
])
def test_add_product_basic_validation_fails(product_service, mock_product_repo, mock_dept_repo, invalid_product, expected_error_msg):
    """Test validation failures for basic required fields and positive prices."""
    # Mock department check to pass, focusing on product fields
    mock_dept_repo.get_by_id.return_value = Department(id=1, name="Exists")

    with pytest.raises(ValueError, match=expected_error_msg):
        product_service.add_product(invalid_product)
    mock_product_repo.add.assert_not_called()

def test_add_product_duplicate_code_fails(product_service, mock_product_repo, mock_dept_repo):
    """Test validation failure when adding a product with a duplicate code."""
    product_data = Product(code="DUP01", description="Valid Desc", department_id=1)
    mock_dept_repo.get_by_id.return_value = Department(id=1, name="Exists")
    mock_product_repo.get_by_code.return_value = Product(id=99, code="DUP01", description="Existing") # Simulate duplicate

    with pytest.raises(ValueError, match="Código \'DUP01\' ya existe"): # Check error message
        product_service.add_product(product_data)
    mock_product_repo.add.assert_not_called()

def test_add_product_nonexistent_dept_fails(product_service, mock_product_repo, mock_dept_repo):
    """Test validation failure when adding a product with a non-existent department ID."""
    product_data = Product(code="P005", description="Valid Desc", department_id=99)
    mock_dept_repo.get_by_id.return_value = None # Simulate department not found

    with pytest.raises(ValueError, match="Departamento con ID 99 no existe"):
        product_service.add_product(product_data)
    mock_dept_repo.get_by_id.assert_called_once_with(99)
    mock_product_repo.add.assert_not_called()

def test_update_product_success(product_service, mock_product_repo, mock_dept_repo):
    """Test successful update of a valid product."""
    existing_product = Product(id=101, code="P001", description="Old Desc", department_id=1)
    product_update_data = Product(
        id=101, code="P001-MOD", description="New Desc", sell_price=12.0,
        department_id=2 # Change department
    )
    mock_dept_repo.get_by_id.side_effect = [Department(id=2, name="New Dept")] # For new dept check
    mock_product_repo.get_by_id.return_value = existing_product # Product exists
    mock_product_repo.get_by_code.return_value = None # New code is unique

    product_service.update_product(product_update_data)

    mock_product_repo.get_by_id.assert_called_once_with(101)
    mock_dept_repo.get_by_id.assert_called_once_with(2) # Check new department exists
    mock_product_repo.get_by_code.assert_called_once_with("P001-MOD")
    # Check that repo.update was called with the correct data
    mock_product_repo.update.assert_called_once()
    call_args, _ = mock_product_repo.update.call_args
    assert call_args[0].id == 101
    assert call_args[0].code == "P001-MOD"
    assert call_args[0].description == "New Desc"
    assert call_args[0].sell_price == 12.0
    assert call_args[0].department_id == 2

def test_update_product_validation_fails(product_service, mock_product_repo, mock_dept_repo):
    """Test validation failures during product update (similar to add)."""
    existing_product = Product(id=101, code="P001", description="Old Desc", department_id=1)
    mock_product_repo.get_by_id.return_value = existing_product
    # Ensure department check passes when needed
    mock_dept_repo.get_by_id.return_value = Department(id=1, name="Exists")

    # Test empty description
    invalid_update = Product(id=101, code="P001", description="", department_id=1)
    with pytest.raises(ValueError, match="Descripción es requerida"):
        product_service.update_product(invalid_update)

    # Test negative price
    invalid_update = Product(id=101, code="P001", description="Desc", sell_price=-5.0, department_id=1)
    with pytest.raises(ValueError, match="Precio de venta debe ser positivo"):
        product_service.update_product(invalid_update)

    mock_product_repo.update.assert_not_called()

def test_update_product_code_conflict_fails(product_service, mock_product_repo, mock_dept_repo):
    """Test validation failure when updating code to one that already exists."""
    existing_product1 = Product(id=101, code="P001", description="Prod 1", department_id=1)
    existing_product2 = Product(id=102, code="P002", description="Prod 2", department_id=1)
    product_update_data = Product(id=101, code="P002", description="Updated P001", department_id=1)

    mock_product_repo.get_by_id.return_value = existing_product1
    mock_dept_repo.get_by_id.return_value = Department(id=1, name="Exists")
    mock_product_repo.get_by_code.return_value = existing_product2 # Simulate code conflict

    with pytest.raises(ValueError, match="Código \'P002\' ya existe para otro producto"):
        product_service.update_product(product_update_data)

    mock_product_repo.get_by_code.assert_called_once_with("P002")
    mock_product_repo.update.assert_not_called()

def test_update_product_nonexistent_fails(product_service, mock_product_repo):
    """Test failure when trying to update a product that does not exist."""
    product_update_data = Product(id=999, code="P999", description="Nonexistent")
    mock_product_repo.get_by_id.return_value = None # Simulate product not found

    with pytest.raises(ValueError, match="Producto con ID 999 no encontrado"):
        product_service.update_product(product_update_data)
    mock_product_repo.update.assert_not_called()

def test_delete_product_success(product_service, mock_product_repo):
    """Test successful deletion of a product with no stock or not using inventory."""
    # Case 1: Product with no stock
    product_no_stock = Product(id=201, code="DEL01", description="No Stock", uses_inventory=True, quantity_in_stock=0)
    mock_product_repo.get_by_id.return_value = product_no_stock
    product_service.delete_product(201)
    mock_product_repo.delete.assert_called_with(201)

    # Case 2: Product not using inventory (even if stock > 0)
    mock_product_repo.reset_mock()
    product_no_inv = Product(id=202, code="DEL02", description="No Inv", uses_inventory=False, quantity_in_stock=10)
    mock_product_repo.get_by_id.return_value = product_no_inv
    product_service.delete_product(202)
    mock_product_repo.delete.assert_called_with(202)

def test_delete_product_with_stock_fails(product_service, mock_product_repo):
    """Test that deleting a product that uses inventory and has stock fails."""
    product_with_stock = Product(id=203, code="DEL03", description="With Stock", uses_inventory=True, quantity_in_stock=5)
    mock_product_repo.get_by_id.return_value = product_with_stock

    # Updated regex to accept integer or float (5 or 5.0)
    with pytest.raises(ValueError, match=r"no puede ser eliminado porque tiene stock \(5(?:\.0)?\)"):
        product_service.delete_product(203)

    mock_product_repo.get_by_id.assert_called_once_with(203)
    mock_product_repo.delete.assert_not_called()

def test_delete_product_nonexistent(product_service, mock_product_repo):
    """Test deleting a non-existent product (should not fail, do nothing)."""
    mock_product_repo.get_by_id.return_value = None # Simulate not found
    try:
        product_service.delete_product(999)
    except Exception as e:
        pytest.fail(f"Deleting non-existent product raised error: {e}")

    mock_product_repo.get_by_id.assert_called_once_with(999)
    mock_product_repo.delete.assert_not_called()

def test_find_product_calls_search(product_service, mock_product_repo):
    """Test that find_product calls repo.search when a term is provided."""
    search_term = "search term"
    product_service.find_product(search_term)
    mock_product_repo.search.assert_called_once_with(search_term)
    mock_product_repo.get_all.assert_not_called()

def test_find_product_calls_get_all(product_service, mock_product_repo):
    """Test that find_product calls repo.get_all when no term is provided."""
    product_service.find_product(None)
    mock_product_repo.search.assert_not_called()
    mock_product_repo.get_all.assert_called_once()

# --- Test Cases for Department Operations ---

def test_add_department_success(product_service, mock_dept_repo):
    """Test successful addition of a valid department."""
    dept_data = Department(name="New Dept")
    mock_dept_repo.get_by_name.return_value = None # Name is unique
    mock_dept_repo.add.return_value = Department(id=5, name="New Dept")

    added_dept = product_service.add_department(dept_data)

    mock_dept_repo.get_by_name.assert_called_once_with("New Dept")
    mock_dept_repo.add.assert_called_once_with(dept_data)
    assert added_dept.id == 5

@pytest.mark.parametrize("invalid_dept, expected_error_msg", [
    (Department(name=""), "Nombre de departamento es requerido"),
])
def test_add_department_validation_fails(product_service, mock_dept_repo, invalid_dept, expected_error_msg):
    """Test validation failures for department name."""
    with pytest.raises(ValueError, match=expected_error_msg):
        product_service.add_department(invalid_dept)
    mock_dept_repo.add.assert_not_called()

def test_add_department_duplicate_name_fails(product_service, mock_dept_repo):
    """Test validation failure for duplicate department name."""
    dept_data = Department(name="Existing Dept")
    mock_dept_repo.get_by_name.return_value = Department(id=9, name="Existing Dept") # Simulate duplicate

    with pytest.raises(ValueError, match="Departamento \'Existing Dept\' ya existe"):
        product_service.add_department(dept_data)
    mock_dept_repo.add.assert_not_called()

def test_delete_department_success(product_service, mock_dept_repo, mock_product_repo):
    """Test successful deletion of an unused department."""
    dept_id_to_delete = 10
    mock_dept_repo.get_by_id.return_value = Department(id=dept_id_to_delete, name="ToDelete")
    # Mock product search to return empty list, indicating department is not in use
    mock_product_repo.search.return_value = [] # TODO: Refine this check later

    product_service.delete_department(dept_id_to_delete)

    # TODO: Add assertion for checking products using the department
    # mock_product_repo.search.assert_called_once_with(???) # How to check usage?
    mock_dept_repo.delete.assert_called_once_with(dept_id_to_delete)

def test_delete_department_in_use_fails(product_service, mock_dept_repo, mock_product_repo):
    """Test that deleting a department currently used by products fails."""
    dept_id_to_delete = 11
    dept_name = "InUseDept"
    mock_dept_repo.get_by_id.return_value = Department(id=dept_id_to_delete, name=dept_name)
    # Simulate that products use this department
    mock_product_repo.search.return_value = [Product(id=301, code="P301", description="Using Dept", department_id=dept_id_to_delete)]

    with pytest.raises(ValueError, match=f"Departamento '{dept_name}' no puede ser eliminado, está en uso"):
        product_service.delete_department(dept_id_to_delete)

    mock_dept_repo.delete.assert_not_called()

def test_get_all_departments(product_service, mock_dept_repo):
    """Test that get_all_departments calls the repository."""
    product_service.get_all_departments()
    mock_dept_repo.get_all.assert_called_once()

# TODO: Add tests for update_department if implemented in service

import tempfile
import os
import shutil
import pytest

def test_product_service_integration(tmp_path):
    """Integration test: ProductService with real repositories and SQLite DB."""
    # Setup: Use a temporary SQLite file DB
    db_path = tmp_path / "test_integration.db"
    db_url = f"sqlite:///{db_path}"
    # Patch DATABASE_URL before importing DB setup
    import sys
    import importlib

    # Patch config.DATABASE_URL
    config_module = importlib.import_module("config")
    old_db_url = config_module.DATABASE_URL
    config_module.DATABASE_URL = db_url

    # Re-import and re-initialize DB
    db_module = importlib.import_module("infrastructure.persistence.sqlite.database")
    db_module.engine.dispose()
    db_module.engine = db_module.create_engine(db_url, connect_args={"check_same_thread": False})
    db_module.SessionLocal.configure(bind=db_module.engine)
    db_module.init_db()

    # Import repository implementations
    from infrastructure.persistence.sqlite.repositories import SqliteDepartmentRepository, SqliteProductRepository
    from core.services.product_service import ProductService
    from core.models.product import Department, Product

    # Factories for real repositories
    def product_repo_factory(session):
        return SqliteProductRepository(session)
    def department_repo_factory(_session):
        return SqliteDepartmentRepository()

    # Service instance
    service = ProductService(product_repo_factory, department_repo_factory)

    # Add a department
    dept = Department(name="IntegrationDept")
    added_dept = service.add_department(dept)
    assert added_dept.id is not None

    # Add a product in that department
    product = Product(code="INTEG01", description="Integration Product", department_id=added_dept.id, sell_price=10.0, cost_price=5.0)
    added_product = service.add_product(product)
    assert added_product.id is not None

    # Attempt to delete department in use (should fail)
    with pytest.raises(ValueError):
        service.delete_department(added_dept.id)

    # Delete the product
    service.delete_product(added_product.id)

    # Now delete the department (should succeed)
    service.delete_department(added_dept.id)

    # Cleanup: Restore DATABASE_URL
    config_module.DATABASE_URL = old_db_url