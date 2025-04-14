import unittest
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Assume these paths might need adjustment depending on execution context
from infrastructure.persistence.sqlite.database import Base
from infrastructure.persistence.sqlite.models_mapping import ProductOrm, InventoryMovementOrm, DepartmentOrm # Added InventoryMovementOrm
from infrastructure.persistence.utils import session_scope, session_scope_provider
# Import compatibility wrappers instead of direct repositories
from infrastructure.persistence.compat import (
    SqliteProductRepositoryCompat as SqliteProductRepository,
    SqliteInventoryRepositoryCompat as SqliteInventoryRepository
)
from core.interfaces.repository_interfaces import IInventoryRepository
from core.models.product import Product
from core.models.inventory import InventoryMovement

# Use an in-memory SQLite database for testing repositories
DATABASE_URL = "sqlite:///:memory:"

class TestSqliteInventoryRepository(unittest.TestCase):

    engine = None
    SessionLocal = None
    test_product_id = None
    test_product_id_2 = None

    @classmethod
    def setUpClass(cls):
        """Set up the in-memory database and create tables."""
        cls.engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        
        # Set up the session provider to use our test session
        session_scope_provider.set_session_factory(cls.SessionLocal)

        # Add a product to associate movements with
        product_repo = SqliteProductRepository()  # No session needed with compat adapter
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
        cls.test_product_id = added_product.id
        cls.test_product_id_2 = added_product_2.id
        if not cls.test_product_id or not cls.test_product_id_2:
            raise Exception("Failed to set up test products.")


    @classmethod
    def tearDownClass(cls):
        """Clean up the database."""
        Base.metadata.drop_all(bind=cls.engine)
        # Reset session factory provider
        session_scope_provider.set_session_factory(None)

    def setUp(self):
        """Ensure each test starts with a clean state if needed (or use setUpClass)."""
        # Optionally, clean movements before each test if needed
        # with session_scope() as session:
        #     session.query(InventoryMovementOrm).delete()
        pass

    def test_add_movement(self):
        """Verify an inventory movement is added correctly."""
        repo: IInventoryRepository = SqliteInventoryRepository()  # No session needed with compat adapter
        movement_data = InventoryMovement(
            product_id=self.test_product_id,
            quantity=10.0,
            movement_type="PURCHASE",
            description="Initial stock",
            user_id=1,
            related_id=101
        )
        added_movement = repo.add_movement(movement_data)

        self.assertIsNotNone(added_movement.id)
        self.assertEqual(added_movement.product_id, self.test_product_id)
        self.assertEqual(added_movement.quantity, 10.0)
        self.assertEqual(added_movement.movement_type, "PURCHASE")
        self.assertEqual(added_movement.description, "Initial stock")
        self.assertEqual(added_movement.user_id, 1)
        self.assertEqual(added_movement.related_id, 101)
        self.assertIsInstance(added_movement.timestamp, datetime)

        # Verify in DB
        with session_scope() as session:
            db_movement = session.query(InventoryMovementOrm).filter_by(id=added_movement.id).first()
            self.assertIsNotNone(db_movement)
            self.assertEqual(db_movement.quantity, 10.0)
            self.assertEqual(db_movement.movement_type, "PURCHASE")

    def test_get_movements_for_product(self):
        """Verify retrieving movements only for a specific product."""
        repo = SqliteInventoryRepository()  # No session needed with compat adapter
        now = datetime.now()
        
        # Clear existing movements first to ensure clean test environment
        with session_scope() as session:
            session.query(InventoryMovementOrm).delete()
            session.commit()
        
        # Create movements for testing
        m1 = InventoryMovement(product_id=self.test_product_id, quantity=5.0, movement_type="ADJUST", timestamp=now - timedelta(hours=2))
        m2 = InventoryMovement(product_id=self.test_product_id, quantity=-2.0, movement_type="SALE", timestamp=now - timedelta(hours=1), related_id=50)
        m3 = InventoryMovement(product_id=self.test_product_id_2, quantity=20.0, movement_type="PURCHASE", timestamp=now) # Different product

        # Add movements
        repo.add_movement(m1)
        repo.add_movement(m2)
        repo.add_movement(m3)

        # Retrieve movements for the first product only
        retrieved_movements = repo.get_movements_for_product(self.test_product_id)

        # Verify we get exactly 2 movements for the first product
        self.assertEqual(len(retrieved_movements), 2)
        self.assertEqual(retrieved_movements[0].movement_type, "ADJUST")
        self.assertEqual(retrieved_movements[0].quantity, 5.0)
        self.assertEqual(retrieved_movements[1].movement_type, "SALE")
        self.assertEqual(retrieved_movements[1].quantity, -2.0)
        self.assertEqual(retrieved_movements[1].related_id, 50)
        # Check if sorted by timestamp (oldest first)
        self.assertTrue(retrieved_movements[0].timestamp < retrieved_movements[1].timestamp)


    def test_get_all_movements(self):
        """Verify retrieving all movements."""
        repo = SqliteInventoryRepository()  # No session needed with compat adapter
        now = datetime.now()
        # Clear existing movements first for a clean test
        with session_scope() as session:
             session.query(InventoryMovementOrm).delete()

        m1 = InventoryMovement(product_id=self.test_product_id, quantity=1.0, movement_type="INIT", timestamp=now - timedelta(days=1))
        m2 = InventoryMovement(product_id=self.test_product_id_2, quantity=5.0, movement_type="PURCHASE", timestamp=now)

        repo.add_movement(m1)
        repo.add_movement(m2)

        all_movements = repo.get_all_movements()

        self.assertEqual(len(all_movements), 2)
        # Check if product IDs are correct in the results
        product_ids = {m.product_id for m in all_movements}
        self.assertIn(self.test_product_id, product_ids)
        self.assertIn(self.test_product_id_2, product_ids)

if __name__ == '__main__':
    unittest.main() 