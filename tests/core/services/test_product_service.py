import pytest
from unittest.mock import MagicMock, call
from decimal import Decimal

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
    # Create factory functions that return the mocks, IGNORING the session parameter
    # because the mocks themselves don't need a real session.
    def product_repo_factory(session=None): # Add default None for session
        return mock_product_repo

    def department_repo_factory(session=None): # Add default None for session
        return mock_dept_repo
        
    return ProductService(product_repo_factory, department_repo_factory)

# --- Test Cases for Product Operations ---

def test_add_product_success(product_service, mock_product_repo, mock_dept_repo):
    """Test successful addition of a valid product."""
    dept = Department(id=1, name="Valid Dept")
    # Define product data *without* id initially
    product_data = Product(
        code="P001", description="Valid Product", sell_price=Decimal('10.00'), cost_price=Decimal('5.00'),
        department_id=1
    )
    # Create the expected return value explicitly
    expected_added_product = Product(
        id=101, code="P001", description="Valid Product", sell_price=Decimal('10.00'), cost_price=Decimal('5.00'),
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
    (Product(code="", description="Test", cost_price=Decimal('10.00'), sell_price=Decimal('20.00')), "Código es requerido"),
    (Product(code="P002", description="", cost_price=Decimal('10.00'), sell_price=Decimal('20.00')), "Descripción es requerida"),
    (Product(code="P003", description="Test", cost_price=Decimal('10.00'), sell_price=Decimal('-1.00')), "Precio de venta debe ser positivo"),
    (Product(code="P004", description="Test", cost_price=Decimal('-5.00'), sell_price=Decimal('20.00')), "Precio de costo debe ser positivo"),
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
    product_data = Product(code="DUP01", description="Valid Desc", department_id=1, cost_price=Decimal('10.00'), sell_price=Decimal('20.00'))
    mock_dept_repo.get_by_id.return_value = Department(id=1, name="Exists")
    mock_product_repo.get_by_code.return_value = Product(id=99, code="DUP01", description="Existing", cost_price=Decimal('10.00'), sell_price=Decimal('20.00')) # Simulate duplicate

    with pytest.raises(ValueError, match="Código \'DUP01\' ya existe"): # Check error message
        product_service.add_product(product_data)
    mock_product_repo.add.assert_not_called()

def test_add_product_nonexistent_dept_fails(product_service, mock_product_repo, mock_dept_repo):
    """Test validation failure when adding a product with a non-existent department ID."""
    product_data = Product(code="P005", description="Valid Desc", department_id=99, cost_price=Decimal('10.00'), sell_price=Decimal('20.00'))
    mock_dept_repo.get_by_id.return_value = None # Simulate department not found

    with pytest.raises(ValueError, match="Departamento con ID 99 no existe"):
        product_service.add_product(product_data)
    mock_dept_repo.get_by_id.assert_called_once_with(99)
    mock_product_repo.add.assert_not_called()

def test_update_product_success(product_service, mock_product_repo, mock_dept_repo):
    """Test successful update of a valid product."""
    existing_product = Product(id=101, code="P001", description="Old Desc", department_id=1, cost_price=Decimal('10.00'), sell_price=Decimal('20.00'))
    product_update_data = Product(
        id=101, code="P001-MOD", description="New Desc", sell_price=Decimal('12.00'),
        department_id=2, cost_price=Decimal('8.00') # Change department
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
    assert call_args[0].sell_price == Decimal('12.00')
    assert call_args[0].department_id == 2

def test_update_product_validation_fails(product_service, mock_product_repo, mock_dept_repo):
    """Test validation failures during product update (similar to add)."""
    existing_product = Product(id=101, code="P001", description="Old Desc", department_id=1, cost_price=Decimal('10.00'), sell_price=Decimal('20.00'))
    mock_product_repo.get_by_id.return_value = existing_product
    # Ensure department check passes when needed
    mock_dept_repo.get_by_id.return_value = Department(id=1, name="Exists")

    # Test empty description
    invalid_update = Product(id=101, code="P001", description="", department_id=1, cost_price=Decimal('10.00'), sell_price=Decimal('20.00'))
    with pytest.raises(ValueError, match="Descripción es requerida"):
        product_service.update_product(invalid_update)

    # Test negative price
    invalid_update = Product(id=101, code="P001", description="Desc", sell_price=Decimal('-5.00'), department_id=1, cost_price=Decimal('10.00'))
    with pytest.raises(ValueError, match="Precio de venta debe ser positivo"):
        product_service.update_product(invalid_update)

    mock_product_repo.update.assert_not_called()

def test_update_product_code_conflict_fails(product_service, mock_product_repo, mock_dept_repo):
    """Test validation failure when updating code to one that already exists."""
    existing_product1 = Product(id=101, code="P001", description="Prod 1", department_id=1, cost_price=Decimal('10.00'), sell_price=Decimal('20.00'))
    existing_product2 = Product(id=102, code="P002", description="Prod 2", department_id=1, cost_price=Decimal('10.00'), sell_price=Decimal('20.00'))
    product_update_data = Product(id=101, code="P002", description="Updated P001", department_id=1, cost_price=Decimal('10.00'), sell_price=Decimal('20.00'))

    mock_product_repo.get_by_id.return_value = existing_product1
    mock_dept_repo.get_by_id.return_value = Department(id=1, name="Exists")
    mock_product_repo.get_by_code.return_value = existing_product2 # Simulate code conflict

    with pytest.raises(ValueError, match="Código \'P002\' ya existe para otro producto"):
        product_service.update_product(product_update_data)

    mock_product_repo.get_by_code.assert_called_once_with("P002")
    mock_product_repo.update.assert_not_called()

def test_update_product_nonexistent_fails(product_service, mock_product_repo):
    """Test failure when trying to update a product that does not exist."""
    product_update_data = Product(
        id=999, 
        code="P999", 
        description="Nonexistent",
        cost_price=Decimal('10.00'),
        sell_price=Decimal('20.00')
    )
    mock_product_repo.get_by_id.return_value = None # Simulate product not found

    with pytest.raises(ValueError, match="Producto con ID 999 no encontrado"):
        product_service.update_product(product_update_data)
    mock_product_repo.update.assert_not_called()

def test_delete_product_success(product_service, mock_product_repo):
    """Test successful deletion of a product with no stock or not using inventory."""
    # Case 1: Product with no stock
    product_no_stock = Product(id=201, code="DEL01", description="No Stock", uses_inventory=True, quantity_in_stock=Decimal('0.00'), cost_price=Decimal('10.00'), sell_price=Decimal('20.00'))
    mock_product_repo.get_by_id.return_value = product_no_stock
    product_service.delete_product(201)
    mock_product_repo.delete.assert_called_with(201)

    # Case 2: Product not using inventory (even if stock > 0)
    mock_product_repo.reset_mock()
    product_no_inv = Product(id=202, code="DEL02", description="No Inv", uses_inventory=False, quantity_in_stock=Decimal('10.00'), cost_price=Decimal('10.00'), sell_price=Decimal('20.00'))
    mock_product_repo.get_by_id.return_value = product_no_inv
    product_service.delete_product(202)
    mock_product_repo.delete.assert_called_with(202)

def test_delete_product_with_stock_fails(product_service, mock_product_repo):
    """Test that deleting a product that uses inventory and has stock fails."""
    product_with_stock = Product(id=203, code="DEL03", description="With Stock", uses_inventory=True, quantity_in_stock=Decimal('5.00'), cost_price=Decimal('10.00'), sell_price=Decimal('20.00'))
    mock_product_repo.get_by_id.return_value = product_with_stock

    # The service should raise ValueError when trying to delete a product with stock
    with pytest.raises(ValueError, match="Producto 'DEL03' no puede ser eliminado porque tiene stock"):
        product_service.delete_product(203)
    
    # Verify delete was NOT called
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
    # Mock the new method to return an empty list, indicating department is not in use
    mock_product_repo.get_by_department_id.return_value = []

    product_service.delete_department(dept_id_to_delete)

    # Assert the check for products using the department was made correctly via the new method
    mock_product_repo.get_by_department_id.assert_called_once_with(dept_id_to_delete)
    mock_dept_repo.delete.assert_called_once_with(dept_id_to_delete)

def test_delete_department_in_use_fails(product_service, mock_dept_repo, mock_product_repo):
    """Test that deleting a department currently used by products fails."""
    dept_id_to_delete = 11
    dept_name = "InUseDept"
    mock_dept_repo.get_by_id.return_value = Department(id=dept_id_to_delete, name=dept_name)
    # Simulate that products use this department via the new method
    mock_product_repo.get_by_department_id.return_value = [
        Product(
            id=301, 
            code="P301", 
            description="Using Dept", 
            department_id=dept_id_to_delete,
            cost_price=Decimal('10.00'),
            sell_price=Decimal('20.00')
        )
    ]

    with pytest.raises(ValueError, match=f"Departamento '{dept_name}' no puede ser eliminado, está en uso por 1 producto"):
        product_service.delete_department(dept_id_to_delete)

    mock_dept_repo.get_by_id.assert_called_once_with(dept_id_to_delete)
    mock_product_repo.get_by_department_id.assert_called_once_with(dept_id_to_delete)
    mock_dept_repo.delete.assert_not_called()

def test_get_all_departments(product_service, mock_dept_repo):
    """Test that get_all_departments calls the repository."""
    product_service.get_all_departments()
    mock_dept_repo.get_all.assert_called_once()

def test_update_department_success(product_service, mock_dept_repo):
    """Test successful update of a department."""
    dept_update_data = Department(id=5, name="Updated Dept Name")
    existing_dept = Department(id=5, name="Old Name")

    mock_dept_repo.get_by_id.return_value = existing_dept
    mock_dept_repo.get_by_name.return_value = None # New name is unique
    mock_dept_repo.update.return_value = dept_update_data # Simulate update returning the object

    updated_dept = product_service.update_department(dept_update_data)

    mock_dept_repo.get_by_id.assert_called_once_with(5)
    mock_dept_repo.get_by_name.assert_called_once_with("Updated Dept Name")
    mock_dept_repo.update.assert_called_once_with(dept_update_data)
    assert updated_dept is not None
    assert updated_dept.name == "Updated Dept Name"

def test_update_department_validation_fails(product_service, mock_dept_repo):
    """Test validation failure for empty department name during update."""
    dept_update_data = Department(id=5, name="")
    existing_dept = Department(id=5, name="Old Name")
    mock_dept_repo.get_by_id.return_value = existing_dept # Department exists

    with pytest.raises(ValueError, match="Nombre de departamento es requerido"):
        product_service.update_department(dept_update_data)

    mock_dept_repo.update.assert_not_called()

def test_update_department_duplicate_name_fails(product_service, mock_dept_repo):
    """Test validation failure when updating name to one that already exists."""
    dept_update_data = Department(id=5, name="Existing Name")
    existing_dept_to_update = Department(id=5, name="Old Name")
    conflicting_dept = Department(id=6, name="Existing Name") # Another dept has the target name

    mock_dept_repo.get_by_id.return_value = existing_dept_to_update
    mock_dept_repo.get_by_name.return_value = conflicting_dept # Simulate name conflict

    with pytest.raises(ValueError, match="Departamento 'Existing Name' ya existe"):
        product_service.update_department(dept_update_data)

    mock_dept_repo.get_by_name.assert_called_once_with("Existing Name")
    mock_dept_repo.update.assert_not_called()

def test_update_department_nonexistent_fails(product_service, mock_dept_repo):
    """Test failure when trying to update a department that does not exist."""
    dept_update_data = Department(id=999, name="Nonexistent Dept")
    mock_dept_repo.get_by_id.return_value = None # Simulate department not found

    with pytest.raises(ValueError, match="Departamento con ID 999 no encontrado"):
        product_service.update_department(dept_update_data)

    mock_dept_repo.update.assert_not_called()


# --- Integration Test ---

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import necessary components for integration test
from infrastructure.persistence.sqlite.database import Base, init_db # Assuming init_db creates tables
from infrastructure.persistence.sqlite.repositories import SqliteDepartmentRepository, SqliteProductRepository
from infrastructure.persistence.utils import session_scope_provider # Import the provider instance
from core.models.product import Department, Product # Import models

@pytest.fixture(scope="function") # Use function scope for isolation
def test_db_session_factory():
    """Fixture to set up an in-memory SQLite DB and configure session_scope."""
    # Use in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    # Create tables
    Base.metadata.create_all(bind=engine) # Use Base.metadata if init_db isn't suitable

    # Create a session factory bound to this engine
    TestSessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Store the original factory (if any)
    original_factory = session_scope_provider.get_session_factory()
    # Set the provider to use our test session factory
    session_scope_provider.set_session_factory(TestSessionFactory)

    yield TestSessionFactory # Provide the factory if needed, though session_scope uses it internally

    # Teardown: Restore the original session factory and clean up
    session_scope_provider.set_session_factory(original_factory)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_product_service_integration(test_db_session_factory): # Depend on the fixture
    """Integration test: ProductService with real repositories and in-memory SQLite DB."""

    # Factories for real repositories - THESE NOW WORK WITH THE TEST SESSION SCOPE
    def product_repo_factory(session):
        return SqliteProductRepository(session)
    def department_repo_factory(session):
        return SqliteDepartmentRepository(session)

    # Service instance - uses the factories which get sessions from the overridden provider
    service = ProductService(product_repo_factory, department_repo_factory)

    # --- Test Logic (same as before, but now uses the test DB via session_scope) ---

    # Add a department
    dept_data = Department(name="IntegrationDept")
    added_dept = service.add_department(dept_data)
    assert added_dept.id is not None
    assert added_dept.name == "IntegrationDept"

    # Add a product in that department
    product_data = Product(
        code="INTEG01",
        description="Integration Product",
        department_id=added_dept.id,
        sell_price=10.0,
        cost_price=5.0
    )
    added_product = service.add_product(product_data)
    assert added_product.id is not None
    assert added_product.code == "INTEG01"
    assert added_product.department_id == added_dept.id

    # Verify product and department exist using the service (which uses session_scope)
    retrieved_dept = service.get_all_departments()[0]
    assert retrieved_dept.id == added_dept.id
    retrieved_product = service.get_product_by_id(added_product.id)
    assert retrieved_product.id == added_product.id

    # Attempt to delete department in use (should fail) - Use the updated error message format and fix escape sequence warning
    expected_error_msg = f"Departamento '{added_dept.name}' no puede ser eliminado, está en uso por 1 producto\\(s\\)."
    with pytest.raises(ValueError, match=expected_error_msg):
        service.delete_department(added_dept.id)

    # Delete the product
    service.delete_product(added_product.id)

    # Verify product is deleted
    assert service.get_product_by_id(added_product.id) is None

    # Now delete the department (should succeed)
    service.delete_department(added_dept.id)

    # Verify department is deleted
    assert not service.get_all_departments() # List should be empty

# --- Test Cases for Update Prices by Percentage ---

def test_update_prices_all_products(product_service, mock_product_repo):
    """Test updating prices for all products by a positive percentage."""
    products = [
        Product(id=1, code="P001", description="Prod 1", sell_price=Decimal("100.00"), cost_price=Decimal("50.00")), 
        Product(id=2, code="P002", description="Prod 2", sell_price=Decimal("200.00"), cost_price=Decimal("100.00"))
    ]
    mock_product_repo.get_all.return_value = products
    
    updated_count = product_service.update_prices_by_percentage(Decimal("10")) # 10% increase

    assert updated_count == 2
    mock_product_repo.get_all.assert_called_once()
    mock_product_repo.get_by_department_id.assert_not_called()
    
    # Check that update was called for each product with correct new prices
    assert mock_product_repo.update.call_count == 2
    
    # First product: 100 * 1.10 = 110, 50 * 1.10 = 55
    call_args_1, _ = mock_product_repo.update.call_args_list[0]
    updated_product_1 = call_args_1[0]
    assert updated_product_1.id == 1
    assert updated_product_1.sell_price == Decimal("110.00")
    assert updated_product_1.cost_price == Decimal("55.00")

    # Second product: 200 * 1.10 = 220, 100 * 1.10 = 110
    call_args_2, _ = mock_product_repo.update.call_args_list[1]
    updated_product_2 = call_args_2[0]
    assert updated_product_2.id == 2
    assert updated_product_2.sell_price == Decimal("220.00")
    assert updated_product_2.cost_price == Decimal("110.00")

def test_update_prices_by_department(product_service, mock_product_repo):
    """Test updating prices for products in a specific department by a negative percentage."""
    dept_id = 1
    products_in_dept = [
        Product(id=3, code="P003", description="Prod 3 Dept 1", sell_price=Decimal("100.00"), department_id=dept_id, cost_price=Decimal("80.00") ),
    ]
    mock_product_repo.get_by_department_id.return_value = products_in_dept
    
    updated_count = product_service.update_prices_by_percentage(Decimal("-20"), department_id=dept_id) # 20% decrease

    assert updated_count == 1
    mock_product_repo.get_by_department_id.assert_called_once_with(dept_id)
    mock_product_repo.get_all.assert_not_called()
    
    mock_product_repo.update.assert_called_once()
    call_args, _ = mock_product_repo.update.call_args
    updated_product = call_args[0]
    assert updated_product.id == 3
    # 100 * 0.80 = 80
    # 80 * 0.80 = 64
    assert updated_product.sell_price == Decimal("80.00") 
    assert updated_product.cost_price == Decimal("64.00")

def test_update_prices_no_products_found_all(product_service, mock_product_repo):
    """Test updating prices when no products exist."""
    mock_product_repo.get_all.return_value = []
    updated_count = product_service.update_prices_by_percentage(Decimal("10"))
    assert updated_count == 0
    mock_product_repo.update.assert_not_called()

def test_update_prices_no_products_found_department(product_service, mock_product_repo):
    """Test updating prices when no products exist in the specified department."""
    dept_id = 5
    mock_product_repo.get_by_department_id.return_value = []
    updated_count = product_service.update_prices_by_percentage(Decimal("10"), department_id=dept_id)
    assert updated_count == 0
    mock_product_repo.update.assert_not_called()

@pytest.mark.parametrize("invalid_percentage", [
    Decimal("-100"), 
    Decimal("-100.01"),
    Decimal("-200")
])
def test_update_prices_invalid_percentage(product_service, mock_product_repo, invalid_percentage):
    """Test updating prices with an invalid percentage (<= -100%)."""
    with pytest.raises(ValueError, match="Porcentaje debe ser un número mayor que -100."):
        product_service.update_prices_by_percentage(invalid_percentage)
    mock_product_repo.update.assert_not_called()

def test_update_prices_product_with_no_sell_price(product_service, mock_product_repo):
    """Test that products with no sell_price are skipped."""
    products = [
        Product(id=1, code="P001", description="Prod 1", sell_price=None, cost_price=Decimal("50.00")),
        Product(id=2, code="P002", description="Prod 2", sell_price=Decimal("200.00"), cost_price=Decimal("100.00"))
    ]
    mock_product_repo.get_all.return_value = products
    
    updated_count = product_service.update_prices_by_percentage(Decimal("10"))
    assert updated_count == 1 # Only one product should be updated
    mock_product_repo.update.assert_called_once() # Called only for the second product
    call_args, _ = mock_product_repo.update.call_args
    updated_product = call_args[0]
    assert updated_product.id == 2 # Ensure the correct product was updated
    assert updated_product.sell_price == Decimal("220.00")
    assert updated_product.cost_price == Decimal("110.00")

def test_update_prices_rounding_and_zero_floor(product_service, mock_product_repo):
    """Test price rounding to two decimal places and that prices don't go below zero."""
    products = [
        Product(id=1, code="P001", description="Prod Round", sell_price=Decimal("10.33"), cost_price=Decimal("5.11")),
        Product(id=2, code="P002", description="Prod To Zero", sell_price=Decimal("1.00"), cost_price=Decimal("0.50"))
    ]
    mock_product_repo.get_all.return_value = products

    # Test positive percentage with rounding
    product_service.update_prices_by_percentage(Decimal("10.555")) # 10.555% increase
    call_args_1, _ = mock_product_repo.update.call_args_list[0]
    updated_product_1 = call_args_1[0]
    # 10.33 * 1.10555 = 11.4236315 -> 11.42
    # 5.11 * 1.10555 = 5.6513605 -> 5.65
    assert updated_product_1.sell_price == Decimal("11.42")
    assert updated_product_1.cost_price == Decimal("5.65")

    # Test negative percentage that would make price negative (should be floored at 0.00)
    mock_product_repo.update.reset_mock() # Reset mock for the second part of the test
    mock_product_repo.get_all.return_value = [ # Provide a fresh list to avoid state issues from previous mock calls
         Product(id=2, code="P002", description="Prod To Zero", sell_price=Decimal("1.00"), cost_price=Decimal("0.50"))
    ]
    product_service.update_prices_by_percentage(Decimal("-99.5")) # 99.5% decrease
    
    call_args_2_new, _ = mock_product_repo.update.call_args_list[0]
    updated_product_2_new = call_args_2_new[0]
    # Sell: 1.00 * (1 - 0.995) = 1.00 * 0.005 = 0.005 -> 0.01 (due to rounding)
    # Cost: 0.50 * (1 - 0.995) = 0.50 * 0.005 = 0.0025 -> 0.00 (due to rounding to 0.01 then max with 0.00)
    assert updated_product_2_new.sell_price == Decimal("0.00") # 1.00 * 0.005 = 0.005, rounds to 0.01 but floored to 0.00
    assert updated_product_2_new.cost_price == Decimal("0.00") # 0.50 * 0.005 = 0.0025, rounds to 0.00
