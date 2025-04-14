import unittest
from dataclasses import is_dataclass
from datetime import datetime

# Assuming the model will be created in core/models/inventory.py
# Need to adjust import if the location changes
try:
    from core.models.inventory import InventoryMovement
except ImportError:
    # Define a placeholder if the actual class doesn't exist yet
    class InventoryMovement: pass

class TestInventoryMovement(unittest.TestCase):

    def test_inventory_movement_creation(self):
        """Tests basic creation of an InventoryMovement object."""
        # First, check if it's a dataclass (will fail initially)
        self.assertTrue(is_dataclass(InventoryMovement), "InventoryMovement should be a dataclass")

        # Placeholder for actual attribute tests once defined
        now = datetime.now()
        try:
            movement = InventoryMovement(
                id=1,
                product_id=10,
                user_id=1, # Assuming user ID is tracked
                timestamp=now,
                movement_type="SALE", # Example type
                quantity=-2.0, # Example quantity change
                description="Sale #50",
                related_id=50 # Example related Sale ID
            )
            self.assertEqual(movement.id, 1)
            self.assertEqual(movement.product_id, 10)
            self.assertEqual(movement.user_id, 1)
            self.assertEqual(movement.timestamp, now)
            self.assertEqual(movement.movement_type, "SALE")
            self.assertEqual(movement.quantity, -2.0)
            self.assertEqual(movement.description, "Sale #50")
            self.assertEqual(movement.related_id, 50)
        except TypeError:
            self.fail("InventoryMovement dataclass likely not defined or missing fields.")

if __name__ == '__main__':
    unittest.main() 