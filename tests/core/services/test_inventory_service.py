import pytest
from unittest.mock import MagicMock, patch, call, ANY # Added ANY
from datetime import datetime
from decimal import Decimal # Added Decimal for numeric comparison
from dataclasses import replace # Added replace

# Adjust imports based on project structure
from core.services.inventory_service import InventoryService
from core.models.product import Product
from core.models.inventory import InventoryMovement
from core.interfaces.repository_interfaces import IProductRepository, IInventoryRepository
from infrastructure.persistence.utils import session_scope # For mocking

# --- Fixtures ---

@pytest.fixture
def mock_product_repo():
    """Fixture for a mock Product Repository."""
    repo = MagicMock(spec=IProductRepository)
    # Add default return values if needed, e.g., for get_by_id
    repo.get_by_id.return_value = None
    repo.update_stock.return_value = True # Assume success by default
    return repo

@pytest.fixture
def mock_inventory_repo():
    """Fixture for a mock Inventory Movement Repository."""
    repo = MagicMock(spec=IInventoryRepository)
    repo.add_movement.return_value = None # add_movement usually doesn't return anything significant
    return repo

@pytest.fixture
def inventory_service(mock_inventory_repo, mock_product_repo):
    """Fixture for the InventoryService with mocked repository factories."""
    # Create factory functions that return the mocked repositories
    def inventory_repo_factory(session):
        return mock_inventory_repo

    def product_repo_factory(session):
        return mock_product_repo

    service = InventoryService(inventory_repo_factory, product_repo_factory)
    return service

@pytest.fixture
def sample_product():
    """Fixture for a sample product that uses inventory."""
    return Product(
        id=1,
        code="P001",
        description="Test Product",
        cost_price=Decimal('10.00'), # Use Decimal
        sell_price=Decimal('20.00'), # Use Decimal
        uses_inventory=True,
        quantity_in_stock=Decimal('50.0'), # Use Decimal
        min_stock=Decimal('10.0') # Use Decimal
    )

@pytest.fixture
def sample_product_no_inventory():
    """Fixture for a sample product that does NOT use inventory."""
    return Product(
        id=2,
        code="P002",
        description="Service Product",
        cost_price=Decimal('0.00'),
        sell_price=Decimal('100.00'),
        uses_inventory=False,
        quantity_in_stock=Decimal('0.0')
    )

# --- Tests for add_inventory ---

@patch('core.services.inventory_service.session_scope')
def test_add_inventory_success(mock_session_scope, inventory_service, mock_product_repo, mock_inventory_repo, sample_product):
    """Test successfully adding inventory to a product."""
    product_id = sample_product.id
    quantity_to_add = Decimal('25.0')
    new_cost = Decimal('11.0')
    notes = "Received shipment"
    user_id = 1

    # Create a copy to simulate the state fetched from the DB
    # Note: In pytest, fixtures usually provide fresh instances, but explicit copy can be clearer
    product_from_db = Product(**sample_product.__dict__)

    # Configure mocks
    mock_product_repo.get_by_id.return_value = product_from_db
    mock_session = MagicMock()
    mock_session_scope.return_value.__enter__.return_value = mock_session

    # Action
    result_product = inventory_service.add_inventory(
        product_id=product_id,
        quantity=quantity_to_add,
        new_cost_price=new_cost,
        notes=notes,
        user_id=user_id
    )

    # Assertions
    mock_product_repo.get_by_id.assert_called_once_with(product_id)
    # Check stock update call
    expected_new_quantity = Decimal('75.0') # 50.0 + 25.0
    mock_product_repo.update_stock.assert_called_once_with(product_id, expected_new_quantity, new_cost)
    # Check movement log call
    mock_inventory_repo.add_movement.assert_called_once()
    added_movement = mock_inventory_repo.add_movement.call_args[0][0] # Get the movement object passed
    assert isinstance(added_movement, InventoryMovement)
    assert added_movement.product_id == product_id
    assert added_movement.quantity == quantity_to_add
    # Check movement type convention (assuming PURCHASE for adds)
    assert added_movement.movement_type == "PURCHASE"
    assert added_movement.description == notes
    assert added_movement.user_id == user_id
    # Check session usage (verify factories were called within scope)
    mock_session_scope.assert_called_once()
    # Check the returned product reflects updates
    assert result_product.quantity_in_stock == expected_new_quantity
    assert result_product.cost_price == new_cost

@patch('core.services.inventory_service.session_scope')
def test_add_inventory_zero_quantity(mock_session_scope, inventory_service):
    """Test adding zero quantity raises ValueError."""
    with pytest.raises(ValueError, match="Quantity must be positive"):
        inventory_service.add_inventory(product_id=1, quantity=0)
    mock_session_scope.assert_not_called()

@patch('core.services.inventory_service.session_scope')
def test_add_inventory_negative_quantity(mock_session_scope, inventory_service):
    """Test adding negative quantity raises ValueError."""
    with pytest.raises(ValueError, match="Quantity must be positive"):
        inventory_service.add_inventory(product_id=1, quantity=-10)
    mock_session_scope.assert_not_called()

@patch('core.services.inventory_service.session_scope')
def test_add_inventory_product_not_found(mock_session_scope, inventory_service, mock_product_repo):
    """Test adding inventory to a non-existent product raises ValueError."""
    product_id = 999
    mock_product_repo.get_by_id.return_value = None
    with pytest.raises(ValueError, match=f"Product with ID {product_id} not found"):
        inventory_service.add_inventory(product_id=product_id, quantity=10)
    mock_session_scope.assert_called_once() # Scope is entered before product check

@patch('core.services.inventory_service.session_scope')
def test_add_inventory_product_does_not_use_inventory(mock_session_scope, inventory_service, mock_product_repo, sample_product_no_inventory):
    """Test adding inventory to a product not using inventory raises ValueError."""
    product_id = sample_product_no_inventory.id
    mock_product_repo.get_by_id.return_value = sample_product_no_inventory
    with pytest.raises(ValueError, match=f"Product {sample_product_no_inventory.code} does not use inventory control"):
        inventory_service.add_inventory(product_id=product_id, quantity=5)
    mock_session_scope.assert_called_once() # Scope is entered before product check

# --- Tests for adjust_inventory ---

@patch('core.services.inventory_service.session_scope')
def test_adjust_inventory_success_positive(mock_session_scope, inventory_service, mock_product_repo, mock_inventory_repo, sample_product):
    """Test successfully adjusting inventory upwards."""
    product_id = sample_product.id
    quantity_to_adjust = Decimal('5.0')
    reason = "Stock count correction"
    user_id = 2

    product_from_db = Product(**sample_product.__dict__)
    mock_product_repo.get_by_id.return_value = product_from_db
    mock_session = MagicMock()
    mock_session_scope.return_value.__enter__.return_value = mock_session

    result_product = inventory_service.adjust_inventory(product_id, quantity_to_adjust, reason, user_id)

    expected_new_quantity = Decimal('55.0') # 50.0 + 5.0
    mock_product_repo.update_stock.assert_called_once_with(product_id, expected_new_quantity)
    mock_inventory_repo.add_movement.assert_called_once()
    added_movement = mock_inventory_repo.add_movement.call_args[0][0]
    assert added_movement.quantity == quantity_to_adjust
    assert added_movement.movement_type == "ADJUSTMENT"
    assert added_movement.description == reason
    assert added_movement.user_id == user_id
    assert result_product.quantity_in_stock == expected_new_quantity

@patch('core.services.inventory_service.session_scope')
def test_adjust_inventory_success_negative(mock_session_scope, inventory_service, mock_product_repo, mock_inventory_repo, sample_product):
    """Test successfully adjusting inventory downwards."""
    product_id = sample_product.id
    quantity_to_adjust = Decimal('-15.0') # Remove 15
    reason = "Damaged goods"
    user_id = 1

    product_from_db = Product(**sample_product.__dict__)
    mock_product_repo.get_by_id.return_value = product_from_db
    mock_session = MagicMock()
    mock_session_scope.return_value.__enter__.return_value = mock_session

    result_product = inventory_service.adjust_inventory(product_id, quantity_to_adjust, reason, user_id)

    expected_new_quantity = Decimal('35.0') # 50.0 - 15.0
    mock_product_repo.update_stock.assert_called_once_with(product_id, expected_new_quantity)
    mock_inventory_repo.add_movement.assert_called_once()
    added_movement = mock_inventory_repo.add_movement.call_args[0][0]
    assert added_movement.quantity == quantity_to_adjust
    assert added_movement.movement_type == "ADJUSTMENT"
    assert result_product.quantity_in_stock == expected_new_quantity

@patch('core.services.inventory_service.session_scope')
def test_adjust_inventory_zero_quantity(mock_session_scope, inventory_service):
    """Test adjusting by zero quantity raises ValueError."""
    with pytest.raises(ValueError, match="Adjustment quantity cannot be zero"):
        inventory_service.adjust_inventory(product_id=1, quantity=0, reason="Test reason")
    mock_session_scope.assert_not_called()

@patch('core.services.inventory_service.session_scope')
def test_adjust_inventory_product_not_found(mock_session_scope, inventory_service, mock_product_repo):
    """Test adjusting non-existent product raises ValueError."""
    product_id = 999
    mock_product_repo.get_by_id.return_value = None
    with pytest.raises(ValueError, match=f"Product with ID {product_id} not found"):
        inventory_service.adjust_inventory(product_id=product_id, quantity=10, reason="Test reason")
    mock_session_scope.assert_called_once()

@patch('core.services.inventory_service.session_scope')
def test_adjust_inventory_product_does_not_use_inventory(mock_session_scope, inventory_service, mock_product_repo, sample_product_no_inventory):
    """Test adjusting product not using inventory raises ValueError."""
    product_id = sample_product_no_inventory.id
    mock_product_repo.get_by_id.return_value = sample_product_no_inventory
    with pytest.raises(ValueError, match=f"Product {sample_product_no_inventory.code} does not use inventory control"):
        inventory_service.adjust_inventory(product_id=product_id, quantity=5, reason="Test reason")
    mock_session_scope.assert_called_once()

@patch('core.services.inventory_service.session_scope')
def test_adjust_inventory_results_in_negative_stock(mock_session_scope, inventory_service, mock_product_repo, mock_inventory_repo, sample_product):
    """Test adjustment resulting in negative stock raises ValueError (default behavior)."""
    product_id = sample_product.id
    mock_product_repo.get_by_id.return_value = sample_product # Return the original product
    # Try removing 60 when stock is 50
    with pytest.raises(ValueError, match="Adjustment results in negative stock.*not allowed"):
         inventory_service.adjust_inventory(product_id=product_id, quantity=Decimal('-60.0'), reason="Test reason") # Use Decimal
    # Ensure no update or movement was attempted
    mock_product_repo.update_stock.assert_not_called()
    mock_inventory_repo.add_movement.assert_not_called()
    mock_session_scope.assert_called_once() # Scope was entered, but actions failed within

# --- Tests for decrease_stock_for_sale ---
# Note: These tests need a mock session object passed directly

def test_decrease_stock_for_sale_success(inventory_service, mock_product_repo, mock_inventory_repo, sample_product):
    """Test successfully decreasing stock for a sale item."""
    mock_session = MagicMock() # Create mock session
    product_id = sample_product.id
    quantity_sold = Decimal('3.0')
    sale_id = 123
    user_id = 5

    product_from_db = Product(**sample_product.__dict__)
    mock_product_repo.get_by_id.return_value = product_from_db

    # Action - pass the mock session
    inventory_service.decrease_stock_for_sale(
        session=mock_session,
        product_id=product_id,
        quantity=quantity_sold,
        sale_id=sale_id,
        user_id=user_id
    )

    # Assertions
    mock_product_repo.get_by_id.assert_called_once_with(product_id)
    expected_new_quantity = Decimal('47.0') # 50.0 - 3.0
    mock_product_repo.update_stock.assert_called_once_with(product_id, expected_new_quantity)
    mock_inventory_repo.add_movement.assert_called_once()
    added_movement = mock_inventory_repo.add_movement.call_args[0][0]
    assert isinstance(added_movement, InventoryMovement)
    assert added_movement.product_id == product_id
    assert added_movement.quantity == -quantity_sold # Note the negative sign
    assert added_movement.movement_type == "SALE"
    assert added_movement.description == f"Venta #{sale_id}"
    assert added_movement.related_id == sale_id
    assert added_movement.user_id == user_id

def test_decrease_stock_for_sale_product_not_found(inventory_service, mock_product_repo):
    """Test decreasing stock fails if product not found."""
    mock_session = MagicMock()
    product_id = 999
    mock_product_repo.get_by_id.return_value = None
    with pytest.raises(ValueError, match=f"Product with ID {product_id} not found"):
        inventory_service.decrease_stock_for_sale(session=mock_session, product_id=product_id, quantity=1, sale_id=1)

def test_decrease_stock_for_sale_product_no_inventory(inventory_service, mock_product_repo, sample_product_no_inventory):
    """Test decreasing stock fails if product does not use inventory."""
    mock_session = MagicMock()
    product_id = sample_product_no_inventory.id
    sale_id = 124
    mock_product_repo.get_by_id.return_value = sample_product_no_inventory
    with pytest.raises(ValueError, match=f"Product {sample_product_no_inventory.code} does not use inventory control.*sale {sale_id}"):
        inventory_service.decrease_stock_for_sale(
            session=mock_session,
            product_id=product_id,
            quantity=1,
            sale_id=sale_id
        )

def test_decrease_stock_for_sale_insufficient_stock(inventory_service, mock_product_repo, mock_inventory_repo, sample_product):
    """Test decreasing stock fails if quantity sold exceeds stock (and negative stock not allowed)."""
    mock_session = MagicMock()
    product_id = sample_product.id
    quantity_sold = sample_product.quantity_in_stock + 1 # Sell more than available
    sale_id = 125

    product_from_db = Product(**sample_product.__dict__)
    mock_product_repo.get_by_id.return_value = product_from_db

    with pytest.raises(ValueError, match=f"Insufficient stock for product {sample_product.code}"):
        inventory_service.decrease_stock_for_sale(
            session=mock_session,
            product_id=product_id,
            quantity=quantity_sold,
            sale_id=sale_id
        )
    mock_product_repo.update_stock.assert_not_called()
    mock_inventory_repo.add_movement.assert_not_called()

def test_decrease_stock_for_sale_zero_quantity(inventory_service):
    """Test decreasing stock by zero quantity raises ValueError."""
    mock_session = MagicMock()
    with pytest.raises(ValueError, match="Quantity for sale must be positive"):
        inventory_service.decrease_stock_for_sale(session=mock_session, product_id=1, quantity=0, sale_id=1)

def test_decrease_stock_for_sale_negative_quantity(inventory_service):
    """Test decreasing stock by negative quantity raises ValueError."""
    mock_session = MagicMock()
    with pytest.raises(ValueError, match="Quantity for sale must be positive"):
        inventory_service.decrease_stock_for_sale(session=mock_session, product_id=1, quantity=-5, sale_id=1)

# --- Tests for Reporting Methods ---

@patch('core.services.inventory_service.session_scope')
def test_get_inventory_report(mock_session_scope, inventory_service, mock_product_repo, sample_product):
    """Test retrieving the general inventory report."""
    # Arrange
    expected_products = [sample_product] # Assume repo returns a list
    mock_product_repo.get_all.return_value = expected_products
    mock_session = MagicMock()
    mock_session_scope.return_value.__enter__.return_value = mock_session

    # Act
    report = inventory_service.get_inventory_report()

    # Assert
    mock_session_scope.assert_called_once()
    mock_product_repo.get_all.assert_called_once()
    assert report == expected_products

@patch('core.services.inventory_service.session_scope')
def test_get_low_stock_products(mock_session_scope, inventory_service, mock_product_repo, sample_product):
    """Test retrieving products with low stock."""
    # Arrange
    # Simulate sample_product being low stock
    low_stock_product = replace(sample_product, quantity_in_stock=Decimal('5.0')) # Below min_stock of 10.0
    expected_products = [low_stock_product]
    mock_product_repo.get_low_stock.return_value = expected_products
    mock_session = MagicMock()
    mock_session_scope.return_value.__enter__.return_value = mock_session

    # Act
    low_stock_list = inventory_service.get_low_stock_products()

    # Assert
    mock_session_scope.assert_called_once()
    mock_product_repo.get_low_stock.assert_called_once()
    assert low_stock_list == expected_products

@patch('core.services.inventory_service.session_scope')
def test_get_inventory_movements_all(mock_session_scope, inventory_service, mock_inventory_repo):
    """Test retrieving all inventory movements."""
    # Arrange
    movement1 = InventoryMovement(id=1, product_id=1, quantity=10, movement_type='PURCHASE')
    movement2 = InventoryMovement(id=2, product_id=2, quantity=-5, movement_type='SALE')
    expected_movements = [movement1, movement2]
    mock_inventory_repo.get_all_movements.return_value = expected_movements
    mock_session = MagicMock()
    mock_session_scope.return_value.__enter__.return_value = mock_session

    # Act
    movements = inventory_service.get_inventory_movements()

    # Assert
    mock_session_scope.assert_called_once()
    mock_inventory_repo.get_all_movements.assert_called_once()
    mock_inventory_repo.get_movements_for_product.assert_not_called()
    assert movements == expected_movements

@patch('core.services.inventory_service.session_scope')
def test_get_inventory_movements_for_product(mock_session_scope, inventory_service, mock_inventory_repo, sample_product):
    """Test retrieving inventory movements for a specific product."""
    # Arrange
    product_id_to_filter = sample_product.id
    movement1 = InventoryMovement(id=1, product_id=product_id_to_filter, quantity=10, movement_type='PURCHASE')
    movement2 = InventoryMovement(id=3, product_id=product_id_to_filter, quantity=-2, movement_type='ADJUSTMENT')
    expected_movements = [movement1, movement2]
    mock_inventory_repo.get_movements_for_product.return_value = expected_movements
    mock_session = MagicMock()
    mock_session_scope.return_value.__enter__.return_value = mock_session

    # Act
    movements = inventory_service.get_inventory_movements(product_id=product_id_to_filter)

    # Assert
    mock_session_scope.assert_called_once()
    mock_inventory_repo.get_movements_for_product.assert_called_once_with(product_id_to_filter)
    mock_inventory_repo.get_all_movements.assert_not_called()
    assert movements == expected_movements

# Remove the old unittest runner if it exists
# if __name__ == '__main__':
#     pytest.main() 