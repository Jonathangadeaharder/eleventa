import unittest
import os
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Assume these paths might need adjustment depending on execution context
from infrastructure.persistence.sqlite.database import Base
from infrastructure.persistence.sqlite.models_mapping import ProductOrm, InventoryMovementOrm, DepartmentOrm # Added InventoryMovementOrm
# Import repository classes directly
from infrastructure.persistence.sqlite.repositories import SqliteProductRepository, SqliteInventoryRepository
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
    session = None

    @classmethod
    def setUpClass(cls):
        """Set up the in-memory database and create tables."""
        cls.engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        
        # Create a session for this test class
        cls.session = cls.SessionLocal()

        # Add a product to associate movements with
        product_repo = SqliteProductRepository(cls.session)  # Pass session
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
        cls.session.commit()  # Commit the changes
        
        if not cls.test_product_id or not cls.test_product_id_2:
            raise Exception("Failed to set up test products.")


    @classmethod
    def tearDownClass(cls):
        """Clean up the database."""
        if cls.session:
            cls.session.close()
        Base.metadata.drop_all(bind=cls.engine)

    def setUp(self):
        """Ensure each test starts with a clean state if needed."""
        # Clean movements before each test
        self.__class__.session.query(InventoryMovementOrm).delete()
        self.__class__.session.commit()

    def test_add_movement(self):
        """Verify an inventory movement is added correctly."""
        repo = SqliteInventoryRepository(self.__class__.session)  # Pass session
        movement_data = InventoryMovement(
            product_id=self.test_product_id,
            quantity=10.0,
            movement_type="PURCHASE",
            description="Initial stock",
            user_id=1,
            related_id=101
        )
        added_movement = repo.add_movement(movement_data)
        self.__class__.session.commit()  # Commit changes

        self.assertIsNotNone(added_movement.id)
        self.assertEqual(added_movement.product_id, self.test_product_id)
        self.assertEqual(added_movement.quantity, 10.0)
        self.assertEqual(added_movement.movement_type, "PURCHASE")
        self.assertEqual(added_movement.description, "Initial stock")
        self.assertEqual(added_movement.user_id, 1)
        self.assertEqual(added_movement.related_id, 101)
        self.assertIsInstance(added_movement.timestamp, datetime)

        # Verify in DB
        db_movement = self.__class__.session.query(InventoryMovementOrm).filter_by(id=added_movement.id).first()
        self.assertIsNotNone(db_movement)
        self.assertEqual(db_movement.quantity, 10.0)
        self.assertEqual(db_movement.movement_type, "PURCHASE")

    def test_get_movements_for_product(self):
        """Verify retrieving movements only for a specific product."""
        repo = SqliteInventoryRepository(self.__class__.session)  # Pass session
        now = datetime.now()
        
        # Clear existing movements first to ensure clean test environment
        self.__class__.session.query(InventoryMovementOrm).delete()
        self.__class__.session.commit()
        
        # Create movements for testing
        m1 = InventoryMovement(product_id=self.test_product_id, quantity=5.0, movement_type="ADJUST", timestamp=now - timedelta(hours=2))
        m2 = InventoryMovement(product_id=self.test_product_id, quantity=-2.0, movement_type="SALE", timestamp=now - timedelta(hours=1), related_id=50)
        m3 = InventoryMovement(product_id=self.test_product_id_2, quantity=20.0, movement_type="PURCHASE", timestamp=now) # Different product

        # Add movements
        repo.add_movement(m1)
        repo.add_movement(m2)
        repo.add_movement(m3)
        self.__class__.session.commit()  # Commit changes

        # Retrieve movements for the first product only
        retrieved_movements = repo.get_movements_for_product(self.test_product_id)

        # Verify we get exactly 2 movements for the first product
        self.assertEqual(len(retrieved_movements), 2)
        
        # Sort them by timestamp for predictable testing
        retrieved_movements.sort(key=lambda x: x.timestamp)
        
        self.assertEqual(retrieved_movements[0].movement_type, "ADJUST")
        self.assertEqual(retrieved_movements[0].quantity, 5.0)
        self.assertEqual(retrieved_movements[1].movement_type, "SALE")
        self.assertEqual(retrieved_movements[1].quantity, -2.0)
        self.assertEqual(retrieved_movements[1].related_id, 50)
        # Check if sorted by timestamp
        self.assertTrue(retrieved_movements[0].timestamp < retrieved_movements[1].timestamp)


    def test_get_all_movements(self):
        """Verify retrieving all movements."""
        repo = SqliteInventoryRepository(self.__class__.session)  # Pass session
        now = datetime.now()
        # Clear existing movements first for a clean test
        self.__class__.session.query(InventoryMovementOrm).delete()
        self.__class__.session.commit()

        m1 = InventoryMovement(product_id=self.test_product_id, quantity=1.0, movement_type="INIT", timestamp=now - timedelta(days=1))
        m2 = InventoryMovement(product_id=self.test_product_id_2, quantity=5.0, movement_type="PURCHASE", timestamp=now)

        repo.add_movement(m1)
        repo.add_movement(m2)
        self.__class__.session.commit()  # Commit changes

        all_movements = repo.get_all_movements()

        self.assertEqual(len(all_movements), 2)
        # Check if product IDs are correct in the results
        product_ids = {m.product_id for m in all_movements}
        self.assertIn(self.test_product_id, product_ids)
        self.assertIn(self.test_product_id_2, product_ids)

if __name__ == '__main__':
    unittest.main() 