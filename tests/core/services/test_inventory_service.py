import unittest
from unittest.mock import MagicMock, patch, call
from datetime import datetime

# Adjust imports based on project structure
from core.services.inventory_service import InventoryService
from core.models.product import Product
from core.models.inventory import InventoryMovement
from core.interfaces.repository_interfaces import IProductRepository, IInventoryRepository
from infrastructure.persistence.utils import session_scope # Assuming we might need to mock this behavior

class TestInventoryService(unittest.TestCase):

    def setUp(self):
        """Set up mock repositories and the service before each test."""
        self.mock_product_repo = MagicMock(spec=IProductRepository)
        self.mock_inventory_repo = MagicMock(spec=IInventoryRepository)
        
        # Create factory functions that return the mocked repositories
        def inventory_repo_factory(session):
            return self.mock_inventory_repo
            
        def product_repo_factory(session):
            return self.mock_product_repo
            
        self.inventory_service = InventoryService(inventory_repo_factory, product_repo_factory)

        # Default product for testing
        self.test_product = Product(
            id=1,
            code="P001",
            description="Test Product",
            cost_price=10.0,
            sell_price=20.0,
            uses_inventory=True,
            quantity_in_stock=50.0,
            min_stock=10.0
        )
        self.product_no_inventory = Product(
            id=2,
            code="P002",
            description="Service Product",
            cost_price=0.0,
            sell_price=100.0,
            uses_inventory=False,
            quantity_in_stock=0.0
        )

    # --- Tests for add_inventory ---

    @patch('core.services.inventory_service.session_scope')
    def test_add_inventory_success(self, mock_session_scope):
        """Test successfully adding inventory to a product."""
        product_id = 1
        quantity_to_add = 25.0
        new_cost = 11.0 # Optional new cost
        notes = "Received shipment"
        user_id = 1

        # Create a copy of the test product to avoid modifying the original
        test_product_copy = Product(
            id=product_id,
            code="P001",
            description="Test Product",
            cost_price=10.0,
            sell_price=20.0,
            uses_inventory=True,
            quantity_in_stock=50.0,  # Ensure this is a numeric value
            min_stock=10.0
        )
        
        # Configure mocks
        self.mock_product_repo.get_by_id.return_value = test_product_copy
        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session

        # Action
        result_product = self.inventory_service.add_inventory(
            product_id=product_id,
            quantity=quantity_to_add,
            new_cost_price=new_cost,
            notes=notes,
            user_id=user_id
        )

        # Assertions
        self.mock_product_repo.get_by_id.assert_called_once_with(product_id)
        # Check stock update call
        expected_new_quantity = 75.0  # 50.0 + 25.0
        self.mock_product_repo.update_stock.assert_called_once_with(product_id, expected_new_quantity, new_cost)
        # Check movement log call
        self.mock_inventory_repo.add_movement.assert_called_once()
        added_movement = self.mock_inventory_repo.add_movement.call_args[0][0] # Get the movement object passed
        self.assertIsInstance(added_movement, InventoryMovement)
        self.assertEqual(added_movement.product_id, product_id)
        self.assertEqual(added_movement.quantity, quantity_to_add)
        self.assertEqual(added_movement.movement_type, "PURCHASE") # Or maybe "ADDITION"? Decide convention
        self.assertEqual(added_movement.description, notes)
        self.assertEqual(added_movement.user_id, user_id)
        # Check session usage (verify methods called on the session-scoped repos)
        self.assertTrue(self.mock_product_repo.update_stock.called)
        self.assertTrue(self.mock_inventory_repo.add_movement.called)
        self.assertEqual(result_product, test_product_copy) # Service returns the updated product

    @patch('core.services.inventory_service.session_scope')
    def test_add_inventory_zero_quantity(self, mock_session_scope):
        """Test adding zero quantity raises ValueError."""
        with self.assertRaisesRegex(ValueError, "Quantity must be positive"):
            self.inventory_service.add_inventory(product_id=1, quantity=0)
        mock_session_scope.assert_not_called()

    @patch('core.services.inventory_service.session_scope')
    def test_add_inventory_negative_quantity(self, mock_session_scope):
        """Test adding negative quantity raises ValueError."""
        with self.assertRaisesRegex(ValueError, "Quantity must be positive"):
            self.inventory_service.add_inventory(product_id=1, quantity=-10)
        mock_session_scope.assert_not_called()

    @patch('core.services.inventory_service.session_scope')
    def test_add_inventory_product_not_found(self, mock_session_scope):
        """Test adding inventory to a non-existent product raises ValueError."""
        self.mock_product_repo.get_by_id.return_value = None
        with self.assertRaisesRegex(ValueError, "Product with ID 999 not found"):
            self.inventory_service.add_inventory(product_id=999, quantity=10)
        # Session scope is entered but exited due to error, so don't assert not called

    @patch('core.services.inventory_service.session_scope')
    def test_add_inventory_product_does_not_use_inventory(self, mock_session_scope):
        """Test adding inventory to a product not using inventory raises ValueError."""
        self.mock_product_repo.get_by_id.return_value = self.product_no_inventory
        with self.assertRaisesRegex(ValueError, "Product P002 does not use inventory control"):
            self.inventory_service.add_inventory(product_id=self.product_no_inventory.id, quantity=5)
        # Session scope is entered but exited due to error, so don't assert not called

    # --- Tests for adjust_inventory ---

    @patch('core.services.inventory_service.session_scope')
    def test_adjust_inventory_success_positive(self, mock_session_scope):
        """Test successfully adjusting inventory upwards."""
        product_id = self.test_product.id
        quantity_to_adjust = 5.0
        reason = "Stock count correction"
        user_id = 2

        # Create a copy of the test product to avoid modifying the original
        test_product_copy = Product(
            id=self.test_product.id,
            code=self.test_product.code,
            description=self.test_product.description,
            cost_price=self.test_product.cost_price,
            sell_price=self.test_product.sell_price,
            uses_inventory=self.test_product.uses_inventory,
            quantity_in_stock=50.0,  # Ensure this is a numeric value
            min_stock=self.test_product.min_stock
        )
        
        self.mock_product_repo.get_by_id.return_value = test_product_copy
        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session

        result_product = self.inventory_service.adjust_inventory(product_id, quantity_to_adjust, reason, user_id)

        expected_new_quantity = 55.0  # 50.0 + 5.0
        self.mock_product_repo.update_stock.assert_called_once_with(product_id, expected_new_quantity)
        self.mock_inventory_repo.add_movement.assert_called_once()
        added_movement = self.mock_inventory_repo.add_movement.call_args[0][0]
        self.assertEqual(added_movement.quantity, quantity_to_adjust)
        self.assertEqual(added_movement.movement_type, "ADJUSTMENT")
        self.assertEqual(added_movement.description, reason)
        self.assertEqual(added_movement.user_id, user_id)
        self.assertEqual(result_product, test_product_copy)

    @patch('core.services.inventory_service.session_scope')
    def test_adjust_inventory_success_negative(self, mock_session_scope):
        """Test successfully adjusting inventory downwards."""
        product_id = self.test_product.id
        quantity_to_adjust = -15.0 # Remove 15
        reason = "Damaged goods"
        user_id = 1

        # Create a copy of the test product to avoid modifying the original
        test_product_copy = Product(
            id=self.test_product.id,
            code=self.test_product.code,
            description=self.test_product.description,
            cost_price=self.test_product.cost_price,
            sell_price=self.test_product.sell_price,
            uses_inventory=self.test_product.uses_inventory,
            quantity_in_stock=50.0,  # Ensure this is a numeric value
            min_stock=self.test_product.min_stock
        )
        
        self.mock_product_repo.get_by_id.return_value = test_product_copy
        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session

        result_product = self.inventory_service.adjust_inventory(product_id, quantity_to_adjust, reason, user_id)

        expected_new_quantity = 35.0  # 50.0 - 15.0
        self.mock_product_repo.update_stock.assert_called_once_with(product_id, expected_new_quantity)
        self.mock_inventory_repo.add_movement.assert_called_once()
        added_movement = self.mock_inventory_repo.add_movement.call_args[0][0]
        self.assertEqual(added_movement.quantity, quantity_to_adjust)
        self.assertEqual(added_movement.movement_type, "ADJUSTMENT")
        self.assertEqual(result_product, test_product_copy)

    @patch('core.services.inventory_service.session_scope')
    def test_adjust_inventory_zero_quantity(self, mock_session_scope):
        """Test adjusting by zero quantity raises ValueError."""
        with self.assertRaisesRegex(ValueError, "Adjustment quantity cannot be zero"):
            self.inventory_service.adjust_inventory(product_id=1, quantity=0, reason="Test reason")
        mock_session_scope.assert_not_called()

    @patch('core.services.inventory_service.session_scope')
    def test_adjust_inventory_product_not_found(self, mock_session_scope):
        """Test adjusting non-existent product raises ValueError."""
        self.mock_product_repo.get_by_id.return_value = None
        with self.assertRaisesRegex(ValueError, "Product with ID 999 not found"):
            self.inventory_service.adjust_inventory(product_id=999, quantity=10, reason="Test reason")
        # Session scope is entered but exited due to error, so don't assert not called

    @patch('core.services.inventory_service.session_scope')
    def test_adjust_inventory_product_does_not_use_inventory(self, mock_session_scope):
        """Test adjusting product not using inventory raises ValueError."""
        self.mock_product_repo.get_by_id.return_value = self.product_no_inventory
        with self.assertRaisesRegex(ValueError, "Product P002 does not use inventory control"):
            self.inventory_service.adjust_inventory(product_id=self.product_no_inventory.id, quantity=5, reason="Test reason")
        # Session scope is entered but exited due to error, so don't assert not called

    @patch('core.services.inventory_service.session_scope')
    def test_adjust_inventory_results_in_negative_stock(self, mock_session_scope):
        """Test adjustment resulting in negative stock raises ValueError (default behavior)."""
        self.mock_product_repo.get_by_id.return_value = self.test_product
        # Try removing 60 when stock is 50
        with self.assertRaisesRegex(ValueError, "Adjustment results in negative stock.*not allowed"):
             self.inventory_service.adjust_inventory(product_id=self.test_product.id, quantity=-60.0, reason="Test reason")
        # Ensure no update or movement was attempted
        self.mock_product_repo.update_stock.assert_not_called()
        self.mock_inventory_repo.add_movement.assert_not_called()
        mock_session_scope.assert_called_once() # Scope was entered, but actions failed


    # --- Tests for decrease_stock_for_sale ---

    def test_decrease_stock_for_sale_success(self):
        """Test successfully decreasing stock for a sale item."""
        mock_session = MagicMock() # The session is passed in
        product_id = self.test_product.id
        quantity_sold = 3.0
        sale_id = 123
        user_id = 1

        # Configure mock product repo (it will be re-instantiated with the session)
        mock_product = MagicMock()
        mock_product.id = product_id
        mock_product.code = "P001"
        mock_product.uses_inventory = True
        mock_product.quantity_in_stock = 50.0  # Ensure this is a numeric value, not a MagicMock
        self.mock_product_repo.get_by_id.return_value = mock_product

        # Action
        self.inventory_service.decrease_stock_for_sale(
            session=mock_session,
            product_id=product_id,
            quantity=quantity_sold,
            sale_id=sale_id,
            user_id=user_id
        )

        # Assertions
        expected_new_quantity = mock_product.quantity_in_stock - quantity_sold
        self.mock_product_repo.update_stock.assert_called_once_with(product_id, expected_new_quantity)

        self.mock_inventory_repo.add_movement.assert_called_once()
        added_movement = self.mock_inventory_repo.add_movement.call_args[0][0]
        self.assertEqual(added_movement.product_id, product_id)
        self.assertEqual(added_movement.quantity, -quantity_sold) # Negative for decrease
        self.assertEqual(added_movement.movement_type, "SALE")
        self.assertEqual(added_movement.related_id, sale_id)
        self.assertEqual(added_movement.user_id, user_id)
        self.assertEqual(added_movement.description, f"Venta #{sale_id}")

    def test_decrease_stock_for_sale_product_not_found(self):
        """Test decreasing stock for non-existent product raises ValueError."""
        mock_session = MagicMock()
        self.mock_product_repo.get_by_id.return_value = None
        with self.assertRaisesRegex(ValueError, "Product with ID 999 not found for sale item"):
            self.inventory_service.decrease_stock_for_sale(mock_session, 999, 1, 123)
        self.mock_product_repo.update_stock.assert_not_called()
        self.mock_inventory_repo.add_movement.assert_not_called()

    def test_decrease_stock_for_sale_product_no_inventory(self):
        """Test decreasing stock for product not using inventory raises ValueError."""
        mock_session = MagicMock()
        mock_product = MagicMock()
        mock_product.code = "P002"
        mock_product.uses_inventory = False
        mock_product.quantity_in_stock = 0.0
        self.mock_product_repo.get_by_id.return_value = mock_product
        
        with self.assertRaisesRegex(ValueError, "Product P002 does not use inventory control"):
            self.inventory_service.decrease_stock_for_sale(mock_session, 2, 1, 123)
        self.mock_product_repo.update_stock.assert_not_called()
        self.mock_inventory_repo.add_movement.assert_not_called()

    def test_decrease_stock_for_sale_insufficient_stock(self):
        """Test decreasing stock below zero raises ValueError (default behavior)."""
        mock_session = MagicMock()
        quantity_to_sell = 51.0 # Stock is 50
        
        mock_product = MagicMock()
        mock_product.code = "P001"
        mock_product.uses_inventory = True
        mock_product.quantity_in_stock = 50.0  # Ensure this is a numeric value
        self.mock_product_repo.get_by_id.return_value = mock_product

        with self.assertRaisesRegex(ValueError, "Insufficient stock for product P001"):
            self.inventory_service.decrease_stock_for_sale(mock_session, 1, quantity_to_sell, 123)

        self.mock_product_repo.update_stock.assert_not_called()
        self.mock_inventory_repo.add_movement.assert_not_called()

    def test_decrease_stock_for_sale_zero_quantity(self):
        """Test decreasing zero quantity raises ValueError."""
        mock_session = MagicMock()
        with self.assertRaisesRegex(ValueError, "Quantity for sale must be positive"):
             self.inventory_service.decrease_stock_for_sale(mock_session, self.test_product.id, 0, 123)

    def test_decrease_stock_for_sale_negative_quantity(self):
        """Test decreasing negative quantity raises ValueError."""
        mock_session = MagicMock()
        with self.assertRaisesRegex(ValueError, "Quantity for sale must be positive"):
             self.inventory_service.decrease_stock_for_sale(mock_session, self.test_product.id, -1, 123)


if __name__ == '__main__':
    unittest.main() 