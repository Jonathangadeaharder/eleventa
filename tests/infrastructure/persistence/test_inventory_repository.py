import pytest
from datetime import datetime, timedelta

# Assume these paths might need adjustment depending on execution context
from infrastructure.persistence.sqlite.database import Base
from infrastructure.persistence.sqlite.models_mapping import ProductOrm, InventoryMovementOrm, DepartmentOrm
# Import repository classes directly
from infrastructure.persistence.sqlite.repositories import SqliteProductRepository, SqliteInventoryRepository
from core.interfaces.repository_interfaces import IInventoryRepository
from core.models.product import Product
from core.models.inventory import InventoryMovement
from core.models.enums import InventoryMovementType

@pytest.fixture
def test_product_ids(test_db_session):
    """Create test products and return their IDs."""
    product_repo = SqliteProductRepository(test_db_session)
    
    # Add a product to associate movements with
    test_product = Product(
        code="TESTPROD",
        description="Test Product",
        cost_price=10.0,
        sell_price=20.0,
        uses_inventory=True
    )
    test_product_2 = Product(
        code="TESTPROD2",
        description="Test Product 2",
        cost_price=5.0,
        sell_price=15.0,
        uses_inventory=True
    )
    added_product = product_repo.add(test_product)
    added_product_2 = product_repo.add(test_product_2)
    test_db_session.commit()
    
    return {'product1': added_product.id, 'product2': added_product_2.id}

@pytest.fixture
def clean_movements(test_db_session):
    """Clear all inventory movements before test."""
    test_db_session.query(InventoryMovementOrm).delete()
    test_db_session.commit()

def test_add_movement(test_db_session, test_product_ids, clean_movements):
    """Verify an inventory movement is added correctly."""
    repo = SqliteInventoryRepository(test_db_session)
    movement_data = InventoryMovement(
        product_id=test_product_ids['product1'],
        quantity=10.0,
        movement_type=InventoryMovementType.PURCHASE,
        description="Initial stock",
        user_id=1,
        related_id=101
    )
    added_movement = repo.add_movement(movement_data)
    test_db_session.commit()

    assert added_movement.id is not None
    assert added_movement.product_id == test_product_ids['product1']
    assert added_movement.quantity == 10.0
    assert added_movement.movement_type == InventoryMovementType.PURCHASE
    assert added_movement.description == "Initial stock"
    assert added_movement.user_id == 1
    assert added_movement.related_id == 101
    assert isinstance(added_movement.timestamp, datetime)

    # Verify in DB
    db_movement = test_db_session.query(InventoryMovementOrm).filter_by(id=added_movement.id).first()
    assert db_movement is not None
    assert db_movement.quantity == 10.0
    assert db_movement.movement_type == InventoryMovementType.PURCHASE.value

def test_get_movements_for_product(test_db_session, test_product_ids, clean_movements):
    """Verify retrieving movements only for a specific product."""
    repo = SqliteInventoryRepository(test_db_session)
    now = datetime.now()
    
    # Create movements for testing
    m1 = InventoryMovement(product_id=test_product_ids['product1'], quantity=5.0, movement_type=InventoryMovementType.ADJUSTMENT, timestamp=now - timedelta(hours=2))
    m2 = InventoryMovement(product_id=test_product_ids['product1'], quantity=-2.0, movement_type=InventoryMovementType.SALE, timestamp=now - timedelta(hours=1), related_id=50)
    m3 = InventoryMovement(product_id=test_product_ids['product2'], quantity=20.0, movement_type=InventoryMovementType.PURCHASE, timestamp=now) # Different product

    # Add movements
    repo.add_movement(m1)
    repo.add_movement(m2)
    repo.add_movement(m3)
    test_db_session.commit()

    # Retrieve movements for the first product only
    retrieved_movements = repo.get_movements_for_product(test_product_ids['product1'])

    # Verify we get exactly 2 movements for the first product
    assert len(retrieved_movements) == 2
    
    # Sort them by timestamp for predictable testing
    retrieved_movements.sort(key=lambda x: x.timestamp)
    
    assert retrieved_movements[0].movement_type == InventoryMovementType.ADJUSTMENT
    assert retrieved_movements[0].quantity == 5.0
    assert retrieved_movements[1].movement_type == InventoryMovementType.SALE
    assert retrieved_movements[1].quantity == -2.0
    assert retrieved_movements[1].related_id == 50
    # Check if sorted by timestamp
    assert retrieved_movements[0].timestamp < retrieved_movements[1].timestamp

def test_get_all_movements(test_db_session, test_product_ids, clean_movements):
    """Verify retrieving all movements."""
    repo = SqliteInventoryRepository(test_db_session)
    now = datetime.now()

    m1 = InventoryMovement(product_id=test_product_ids['product1'], quantity=1.0, movement_type=InventoryMovementType.INITIAL, timestamp=now - timedelta(days=1))
    m2 = InventoryMovement(product_id=test_product_ids['product2'], quantity=5.0, movement_type=InventoryMovementType.PURCHASE, timestamp=now)

    repo.add_movement(m1)
    repo.add_movement(m2)
    test_db_session.commit()

    all_movements = repo.get_all_movements()

    assert len(all_movements) == 2
    # Check if product IDs are correct in the results
    product_ids = {m.product_id for m in all_movements}
    assert test_product_ids['product1'] in product_ids
    assert test_product_ids['product2'] in product_ids