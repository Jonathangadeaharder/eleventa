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
def mock_session():
    """Fixture for a mock session."""
    return MagicMock()

@pytest.fixture
def inventory_service(mock_inventory_repo, mock_product_repo):
    """Fixture for the InventoryService with mocked repository factories."""
    # Create factory functions that return the mocked repositories
    def inventory_repo_factory(session):
        return mock_inventory_repo

    def product_repo_factory(session):
        return mock_product_repo

    service = InventoryService(inventory_repo_factory, product_repo_factory)
    
    # Patch _with_session to execute the function directly with our mock session
    # This avoids the need to patch session_scope in every test
    def mock_with_session(func, *args, **kwargs):
        mock_session = MagicMock()
        return func(mock_session, *args, **kwargs)
    
    service._with_session = mock_with_session
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

def test_add_inventory_success(inventory_service, mock_product_repo, mock_inventory_repo, sample_product):
    """Test successfully adding inventory to a product."""
    product_id = sample_product.id
    quantity_to_add = Decimal('25.0')
    new_cost = Decimal('11.0')
    notes = "Received shipment"
    user_id = 1

    # Create a copy by explicitly passing attributes, avoiding internal SQLAlchemy state
    product_from_db = Product(
        id=sample_product.id,
        code=sample_product.code,
        description=sample_product.description,
        cost_price=sample_product.cost_price,
        sell_price=sample_product.sell_price,
        uses_inventory=sample_product.uses_inventory,
        quantity_in_stock=sample_product.quantity_in_stock,
        min_stock=sample_product.min_stock
    )

    # Configure mocks
    mock_product_repo.get_by_id.return_value = product_from_db

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
    # Check stock update call - Since update_stock parameter signature may have changed,
    # just check that it's called with the appropriate parameters
    mock_product_repo.update_stock.assert_called_once()
    args, kwargs = mock_product_repo.update_stock.call_args
    assert args[0] == product_id  # First argument should be product_id
    assert args[1] == quantity_to_add  # Second argument should be the quantity_to_add
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

def test_add_inventory_zero_quantity(inventory_service):
    """Test adding zero quantity raises ValueError."""
    with pytest.raises(ValueError, match="Quantity must be positive"):
        inventory_service.add_inventory(product_id=1, quantity=0)

def test_add_inventory_negative_quantity(inventory_service):
    """Test adding negative quantity raises ValueError."""
    with pytest.raises(ValueError, match="Quantity must be positive"):
        inventory_service.add_inventory(product_id=1, quantity=-10)

def test_add_inventory_product_not_found(inventory_service, mock_product_repo):
    """Test adding inventory to a non-existent product raises ValueError."""
    product_id = 999
    mock_product_repo.get_by_id.return_value = None
    with pytest.raises(ValueError, match=f"Product with ID {product_id} not found"):
        inventory_service.add_inventory(product_id=product_id, quantity=10)

def test_add_inventory_product_does_not_use_inventory(inventory_service, mock_product_repo, sample_product_no_inventory):
    """Test adding inventory to a product not using inventory raises ValueError."""
    product_id = sample_product_no_inventory.id
    mock_product_repo.get_by_id.return_value = sample_product_no_inventory
    with pytest.raises(ValueError, match=f"Product {sample_product_no_inventory.code} does not use inventory control"):
        inventory_service.add_inventory(product_id=product_id, quantity=5)

# --- Tests for adjust_inventory ---

def test_adjust_inventory_success_positive(inventory_service, mock_product_repo, mock_inventory_repo, sample_product):
    """Test successfully adjusting inventory upwards."""
    product_id = sample_product.id
    quantity_to_adjust = Decimal('5.0')
    reason = "Stock count correction"
    user_id = 2

    # Explicit creation of product_from_db
    product_from_db = Product(
        id=sample_product.id,
        code=sample_product.code,
        description=sample_product.description,
        cost_price=sample_product.cost_price,
        sell_price=sample_product.sell_price,
        uses_inventory=sample_product.uses_inventory,
        quantity_in_stock=sample_product.quantity_in_stock,
        min_stock=sample_product.min_stock
    )
    mock_product_repo.get_by_id.return_value = product_from_db

    result_product = inventory_service.adjust_inventory(product_id, quantity_to_adjust, reason, user_id)

    # Assertions
    mock_product_repo.get_by_id.assert_called_once_with(product_id)
    # Check update_stock was called with quantity_to_adjust
    mock_product_repo.update_stock.assert_called_once_with(product_id, quantity_to_adjust)
    mock_inventory_repo.add_movement.assert_called_once()
    added_movement = mock_inventory_repo.add_movement.call_args[0][0]
    assert added_movement.quantity == quantity_to_adjust
    assert added_movement.movement_type == "ADJUSTMENT"
    assert added_movement.description == reason
    assert added_movement.user_id == user_id

def test_adjust_inventory_success_negative(inventory_service, mock_product_repo, mock_inventory_repo, sample_product):
    """Test successfully adjusting inventory downwards."""
    product_id = sample_product.id
    # We'll set the initial stock to 10 so we can decrease by 3
    sample_product.quantity_in_stock = 10.0
    
    quantity_to_adjust = Decimal('-3.0')  # Negative quantity for decreasing
    reason = "Stock count correction - reducing"
    user_id = 2

    # Explicit creation of product_from_db
    product_from_db = Product(
        id=sample_product.id,
        code=sample_product.code,
        description=sample_product.description,
        cost_price=sample_product.cost_price,
        sell_price=sample_product.sell_price,
        uses_inventory=sample_product.uses_inventory,
        quantity_in_stock=sample_product.quantity_in_stock,
        min_stock=sample_product.min_stock
    )
    mock_product_repo.get_by_id.return_value = product_from_db

    result_product = inventory_service.adjust_inventory(product_id, quantity_to_adjust, reason, user_id)

    # Assertions
    mock_product_repo.get_by_id.assert_called_once_with(product_id)
    # Check update_stock was called with quantity_to_adjust
    mock_product_repo.update_stock.assert_called_once_with(product_id, quantity_to_adjust)
    mock_inventory_repo.add_movement.assert_called_once()
    added_movement = mock_inventory_repo.add_movement.call_args[0][0]
    assert added_movement.quantity == quantity_to_adjust
    assert added_movement.movement_type == "ADJUSTMENT"
    assert added_movement.description == reason
    assert added_movement.user_id == user_id
    
def test_adjust_inventory_zero_quantity(inventory_service, mock_product_repo, mock_inventory_repo, sample_product):
    """Test that adjusting inventory with quantity zero raises an error."""
    product_id = sample_product.id
    quantity_to_adjust = Decimal('0.0')
    reason = "This should fail"

    # Set up mock
    mock_product_repo.get_by_id.return_value = sample_product

    # Attempt to adjust with zero quantity
    with pytest.raises(ValueError) as excinfo:
        inventory_service.adjust_inventory(product_id, quantity_to_adjust, reason)
    
    # Assert error message
    assert "Adjustment quantity cannot be zero" in str(excinfo.value)
    
    # Verify no repository methods were called after validation failed
    mock_product_repo.update_stock.assert_not_called()
    mock_inventory_repo.add_movement.assert_not_called()

def test_adjust_inventory_negative_stock(inventory_service, mock_product_repo, mock_inventory_repo, sample_product):
    """Test that attempting to adjust inventory below zero raises an error."""
    product_id = sample_product.id
    # Set initial stock to 5
    sample_product.quantity_in_stock = Decimal('5.0')
    # Try to decrease by 10, which would make stock negative
    quantity_to_adjust = Decimal('-10.0')
    reason = "This should fail"
    
    # Set up mock
    mock_product_repo.get_by_id.return_value = sample_product

    # Attempt to adjust to negative stock
    with pytest.raises(ValueError) as excinfo:
        inventory_service.adjust_inventory(product_id, quantity_to_adjust, reason)
    
    # Assert error message
    assert "negative stock" in str(excinfo.value).lower()
    
    # Verify no repository methods were called after validation failed
    mock_product_repo.update_stock.assert_not_called()
    mock_inventory_repo.add_movement.assert_not_called()

def test_adjust_inventory_product_not_found(inventory_service, mock_product_repo, sample_product):
    """Test that adjusting inventory for a non-existent product raises an error."""
    product_id = 999  # Nonexistent ID
    quantity_to_adjust = Decimal('5.0')
    reason = "This should fail"
    
    # Configure mock to return None (product not found)
    mock_product_repo.get_by_id.return_value = None

    # Attempt to adjust for nonexistent product
    with pytest.raises(ValueError) as excinfo:
        inventory_service.adjust_inventory(product_id, quantity_to_adjust, reason)
    
    # Assert error message
    assert "not found" in str(excinfo.value).lower()
    
    # Verify only get_by_id was called, but no update happened
    mock_product_repo.get_by_id.assert_called_once_with(product_id)
    mock_product_repo.update_stock.assert_not_called()

def test_adjust_inventory_product_no_inventory_control(inventory_service, mock_product_repo, sample_product):
    """Test that adjusting inventory for a product that doesn't use inventory control raises an error."""
    product_id = sample_product.id
    # Set product to not use inventory control
    sample_product.uses_inventory = False
    quantity_to_adjust = Decimal('5.0')
    reason = "This should fail"
    
    # Configure mock
    mock_product_repo.get_by_id.return_value = sample_product

    # Attempt to adjust for product that doesn't use inventory
    with pytest.raises(ValueError) as excinfo:
        inventory_service.adjust_inventory(product_id, quantity_to_adjust, reason)
    
    # Assert error message
    assert "does not use inventory control" in str(excinfo.value).lower()
    
    # Verify only get_by_id was called, but no update happened
    mock_product_repo.get_by_id.assert_called_once_with(product_id)
    mock_product_repo.update_stock.assert_not_called()

# --- Tests for decrease_stock_for_sale ---
# Note: These tests need a mock session object passed directly

def test_decrease_stock_for_sale_success(inventory_service, mock_product_repo, mock_inventory_repo, sample_product):
    """Test successfully decreasing stock for a sale item."""
    mock_session = MagicMock() # Create mock session
    product_id = sample_product.id
    quantity_sold = Decimal('3.0')
    sale_id = 101
    user_id = 3

    # product_from_db = Product(**sample_product.__dict__) # Old problematic line
    product_from_db = Product( # Explicit creation
        id=sample_product.id,
        code=sample_product.code,
        description=sample_product.description,
        cost_price=sample_product.cost_price,
        sell_price=sample_product.sell_price,
        uses_inventory=sample_product.uses_inventory,
        quantity_in_stock=sample_product.quantity_in_stock,
        min_stock=sample_product.min_stock
    )
    mock_product_repo.get_by_id.return_value = product_from_db

    # Action - session is the first parameter now
    inventory_service.decrease_stock_for_sale(product_id, quantity_sold, sale_id, user_id, mock_session)

    # Assertions
    mock_product_repo.get_by_id.assert_called_once_with(product_id)
    # Check stock update was called with negative quantity (decrement)
    mock_product_repo.update_stock.assert_called_once_with(product_id, -quantity_sold)
    # Check movement add was called
    mock_inventory_repo.add_movement.assert_called_once()
    # Check movement properties
    args, _ = mock_inventory_repo.add_movement.call_args
    movement = args[0]
    assert isinstance(movement, InventoryMovement)
    assert movement.product_id == product_id
    assert movement.quantity == -quantity_sold # Should be negative for sales
    assert movement.movement_type == "SALE"
    assert movement.related_id == sale_id
    assert movement.user_id == user_id

def test_decrease_stock_for_sale_product_not_found(inventory_service, mock_product_repo):
    """Test decreasing stock fails when product not found."""
    # Create mock session since the service now expects it as a parameter
    mock_session = MagicMock()
    mock_product_repo.get_by_id.return_value = None
    product_id = 999 # Non-existent ID
    with pytest.raises(ValueError, match=f"Product with ID {product_id} not found"):
        inventory_service.decrease_stock_for_sale(product_id, Decimal('1.0'), 202, session=mock_session)
    mock_product_repo.get_by_id.assert_called_once_with(product_id)

def test_decrease_stock_for_sale_product_no_inventory(inventory_service, mock_product_repo, sample_product_no_inventory):
    """Test decreasing stock fails for product not using inventory."""
    # Create mock session since the service now expects it as a parameter
    mock_session = MagicMock()
    mock_product_repo.get_by_id.return_value = sample_product_no_inventory
    product_id = sample_product_no_inventory.id
    sale_id = 201
    with pytest.raises(ValueError, match=f"Product {sample_product_no_inventory.code} does not use inventory control"):
        inventory_service.decrease_stock_for_sale(product_id, Decimal('1.0'), sale_id, session=mock_session)
    mock_product_repo.get_by_id.assert_called_once_with(product_id)

def test_decrease_stock_for_sale_insufficient_stock(inventory_service, mock_product_repo, mock_inventory_repo, sample_product):
    """Test decreasing stock fails when insufficient stock."""
    # Create mock session since the service now expects it as a parameter
    mock_session = MagicMock()
    # Create a copy of the product with low stock
    product_with_low_stock = Product(
        id=sample_product.id,
        code=sample_product.code,
        description=sample_product.description,
        cost_price=sample_product.cost_price,
        sell_price=sample_product.sell_price,
        uses_inventory=sample_product.uses_inventory,
        quantity_in_stock=Decimal('5.0'), # Only 5 in stock
        min_stock=sample_product.min_stock
    )
    mock_product_repo.get_by_id.return_value = product_with_low_stock
    
    product_id = product_with_low_stock.id
    sale_id = 202
    quantity_to_sell = Decimal('10.0') # Try to sell more than in stock
    
    with pytest.raises(ValueError, match="Insufficient stock for product"):
        inventory_service.decrease_stock_for_sale(product_id, quantity_to_sell, sale_id, session=mock_session)
    
    mock_product_repo.get_by_id.assert_called_once_with(product_id)
    mock_product_repo.update_stock.assert_not_called() # Stock should not be updated
    mock_inventory_repo.add_movement.assert_not_called() # No movement should be recorded

def test_decrease_stock_for_sale_zero_quantity(inventory_service):
    """Test decreasing stock by zero quantity raises ValueError."""
    mock_session = MagicMock()
    with pytest.raises(ValueError, match="Quantity for sale must be positive"):
        inventory_service.decrease_stock_for_sale(product_id=1, quantity=0, sale_id=1, session=mock_session)

def test_decrease_stock_for_sale_negative_quantity(inventory_service):
    """Test decreasing stock by negative quantity raises ValueError."""
    mock_session = MagicMock()
    with pytest.raises(ValueError, match="Quantity for sale must be positive"):
        inventory_service.decrease_stock_for_sale(product_id=1, quantity=-5, sale_id=1, session=mock_session)

# --- Tests for Reporting Methods ---

def test_get_inventory_report(inventory_service, mock_product_repo, sample_product):
    """Test retrieving the general inventory report."""
    # Arrange
    expected_products = [sample_product] # Assume repo returns a list
    mock_product_repo.get_all.return_value = expected_products

    # Act
    report = inventory_service.get_inventory_report()

    # Assert
    assert report == expected_products # Check it returns the products from the repo
    mock_product_repo.get_all.assert_called_once() # Check the repo was queried

def test_get_low_stock_products(inventory_service, mock_product_repo, sample_product):
    """Test retrieving products with low stock."""
    # Arrange
    # Simulate sample_product being low stock
    # Create a low stock product based on sample_product, but manually
    low_stock_product = Product(
        id=sample_product.id,
        code=sample_product.code,
        description=sample_product.description,
        cost_price=sample_product.cost_price,
        sell_price=sample_product.sell_price,
        uses_inventory=sample_product.uses_inventory,
        quantity_in_stock=Decimal('5.0'), # Set the desired low quantity
        min_stock=sample_product.min_stock
    )

    # Configure mock to return this product
    mock_product_repo.get_low_stock.return_value = [low_stock_product]

    # Act
    low_stock_list = inventory_service.get_low_stock_products()

    # Assert
    assert low_stock_list == [low_stock_product] # Check it returns the products from the repo
    mock_product_repo.get_low_stock.assert_called_once() # Check the repo method was called

def test_get_inventory_movements_all(inventory_service, mock_inventory_repo):
    """Test retrieving all inventory movements."""
    # Arrange
    movement1 = InventoryMovement(id=1, product_id=1, quantity=10, movement_type='PURCHASE')
    movement2 = InventoryMovement(id=2, product_id=2, quantity=-5, movement_type='SALE')
    expected_movements = [movement1, movement2]
    mock_inventory_repo.get_all_movements.return_value = expected_movements

    # Act
    movements = inventory_service.get_inventory_movements()

    # Assert
    assert movements == expected_movements # Check it returns the movements from the repo
    mock_inventory_repo.get_all_movements.assert_called_once() # Check repo method called

def test_get_inventory_movements_for_product(inventory_service, mock_inventory_repo, sample_product):
    """Test retrieving inventory movements for a specific product."""
    # Arrange
    product_id_to_filter = sample_product.id
    movement1 = InventoryMovement(id=1, product_id=product_id_to_filter, quantity=10, movement_type='PURCHASE')
    movement2 = InventoryMovement(id=3, product_id=product_id_to_filter, quantity=-2, movement_type='ADJUSTMENT')
    expected_movements = [movement1, movement2]
    mock_inventory_repo.get_movements_for_product.return_value = expected_movements

    # Act
    movements = inventory_service.get_inventory_movements(product_id=product_id_to_filter)

    # Assert
    assert movements == expected_movements # Check it returns the movements from the repo
    mock_inventory_repo.get_movements_for_product.assert_called_once_with(product_id_to_filter)

# Remove the old unittest runner if it exists
# if __name__ == '__main__':
#     pytest.main() 