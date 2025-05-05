import unittest
from dataclasses import is_dataclass, field
from datetime import datetime
from decimal import Decimal

from core.models.inventory import InventoryMovement
from core.models.product import Product

class TestInventoryMovement(unittest.TestCase):

    def test_inventory_movement_creation(self):
        """
        Test that an InventoryMovement object can be created.
        """
        movement = InventoryMovement(
            product_id=1,
            quantity=Decimal('10.5'),
            movement_type='PURCHASE',
            description='Initial stock',
            user_id=1,
            timestamp=datetime.now(),
            related_id=1,
            id=1
        )
        self.assertEqual(movement.id, 1)
        self.assertEqual(movement.product_id, 1)
        self.assertEqual(movement.user_id, 1)
        self.assertEqual(movement.movement_type, "PURCHASE")
        self.assertEqual(movement.quantity, Decimal('10.5'))
        self.assertEqual(movement.description, "Initial stock")
        self.assertEqual(movement.related_id, 1)

if __name__ == '__main__':
    unittest.main() 