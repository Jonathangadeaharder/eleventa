import unittest
from unittest.mock import MagicMock, patch, ANY # Added ANY
from decimal import Decimal

# Service and Models
from core.services.sale_service import SaleService
from core.models.sale import Sale, SaleItem
from core.models.product import Product

# Interfaces and other services needed for mocks
from core.interfaces.repository_interfaces import ISaleRepository, IProductRepository, ICustomerRepository # Added ICustomerRepository
from core.services.inventory_service import InventoryService
from core.services.customer_service import CustomerService # Added CustomerService


class TestSaleService(unittest.TestCase):

    def setUp(self):
        """Set up mocks for repositories and services."""
        self.mock_sale_repo = MagicMock(spec=ISaleRepository)
        self.mock_product_repo = MagicMock(spec=IProductRepository)
        self.mock_inventory_service = MagicMock(spec=InventoryService)
        self.mock_customer_service = MagicMock(spec=CustomerService) # Mock CustomerService

        # Instantiate the service with mocks
        self.sale_service = SaleService(
            sale_repository=self.mock_sale_repo,
            product_repository=self.mock_product_repo,
            inventory_service=self.mock_inventory_service,
            customer_service=self.mock_customer_service # Pass mock CustomerService
        )

        # Prepare some mock product data
        self.product1 = Product(id=1, code="P001", description="Prod 1", sell_price=10.0, uses_inventory=True)
        self.product2 = Product(id=2, code="P002", description="Prod 2", sell_price=20.0, uses_inventory=True)
        self.product3_no_inv = Product(id=3, code="P003", description="Prod 3 NonInv", sell_price=5.0, uses_inventory=False)

    @patch('infrastructure.persistence.utils.session_scope') # Mock the transaction context
    def test_create_sale_success(self, mock_session_scope):
        """Verify successful sale creation and inventory decrease calls."""
        # Arrange: Mock repository/service return values
        self.mock_product_repo.get_by_id.side_effect = lambda pid: {
            1: self.product1,
            2: self.product2
        }.get(pid)

        # Mock add_sale to return a Sale object with IDs assigned
        def mock_add_sale_impl(sale_arg): # sale_arg is the Sale object passed to add_sale
            # Simulate ID assignment by DB
            sale_arg.id = 101
            for idx, item in enumerate(sale_arg.items):
                item.id = 200 + idx
                item.sale_id = 101
            return sale_arg # Return the modified Sale object
        self.mock_sale_repo.add_sale.side_effect = mock_add_sale_impl

        # Mock the inventory service method (doesn't need to return anything)
        self.mock_inventory_service.decrease_stock_for_sale.return_value = None

        # Input data for the sale
        items_data = [
            {'product_id': 1, 'quantity': '2'},
            {'product_id': 2, 'quantity': Decimal('1.5')}
        ]
        user_id = 1 # Example user ID
        payment_type = "Efectivo" # Example payment type

        # Act: Call the service method with new args
        created_sale = self.sale_service.create_sale(
            items_data=items_data,
            user_id=user_id,
            payment_type=payment_type
            # customer_id=None, is_credit_sale=False by default
        )

        # Assert:
        # 1. Product repo was called correctly
        self.mock_product_repo.get_by_id.assert_any_call(1)
        self.mock_product_repo.get_by_id.assert_any_call(2)
        self.assertEqual(self.mock_product_repo.get_by_id.call_count, 2)

        # 2. Sale repo was called once with the correct Sale structure (before IDs)
        self.mock_sale_repo.add_sale.assert_called_once()
        call_args, _ = self.mock_sale_repo.add_sale.call_args
        sale_arg = call_args[0]
        self.assertIsInstance(sale_arg, Sale)
        self.assertEqual(len(sale_arg.items), 2)
        self.assertEqual(sale_arg.items[0].product_id, 1)
        self.assertEqual(sale_arg.items[0].quantity, Decimal('2'))
        self.assertEqual(sale_arg.items[0].unit_price, Decimal('10.00'))
        self.assertEqual(sale_arg.items[1].product_id, 2)
        self.assertEqual(sale_arg.items[1].quantity, Decimal('1.5'))
        self.assertEqual(sale_arg.items[1].unit_price, Decimal('20.00'))
        # Assert new fields are passed correctly
        self.assertEqual(sale_arg.user_id, user_id)
        self.assertEqual(sale_arg.payment_type, payment_type)
        self.assertFalse(sale_arg.is_credit_sale) # Check default
        self.assertIsNone(sale_arg.customer_id) # Check default

        # 3. Inventory service was called for each item that uses inventory
        self.assertEqual(self.mock_inventory_service.decrease_stock_for_sale.call_count, 2)
        # Inventory service calls remain the same for this test
        self.mock_inventory_service.decrease_stock_for_sale.assert_any_call(
            session=ANY, product_id=1, quantity=2.0, sale_id=101
        )
        self.mock_inventory_service.decrease_stock_for_sale.assert_any_call(
            session=ANY, product_id=2, quantity=1.5, sale_id=101
        )
        # Assert customer service was NOT called for non-credit sale
        self.mock_customer_service.increase_customer_debt.assert_not_called()

        # 4. The returned sale object has IDs assigned
        self.assertEqual(created_sale.id, 101)
        self.assertEqual(created_sale.items[0].id, 200)
        self.assertEqual(created_sale.items[1].id, 201)
        self.assertEqual(created_sale.items[0].sale_id, 101)
        self.assertEqual(created_sale.items[1].sale_id, 101)

    @patch('infrastructure.persistence.utils.session_scope')
    def test_create_sale_success_item_without_inventory(self, mock_session_scope):
        """Verify sale creation succeeds, but stock is not decreased for non-inventory item."""
        # Arrange
        self.mock_product_repo.get_by_id.side_effect = lambda pid: {
            1: self.product1,
            3: self.product3_no_inv
        }.get(pid)

        def mock_add_sale_impl(sale_arg):
            sale_arg.id = 102
            for idx, item in enumerate(sale_arg.items):
                item.id = 300 + idx
                item.sale_id = 102
            return sale_arg
        self.mock_sale_repo.add_sale.side_effect = mock_add_sale_impl

        self.mock_inventory_service.decrease_stock_for_sale.return_value = None

        items_data = [
            {'product_id': 1, 'quantity': '1'},
            {'product_id': 3, 'quantity': '5'} # Product 3 does not use inventory
        ]
        user_id = 2
        payment_type = "Tarjeta"

        # Act
        created_sale = self.sale_service.create_sale(
            items_data=items_data,
            user_id=user_id,
            payment_type=payment_type
        )

        # Assert
        self.mock_sale_repo.add_sale.assert_called_once()
        # Inventory service ONLY called for product 1
        self.assertEqual(self.mock_inventory_service.decrease_stock_for_sale.call_count, 1)
        self.mock_inventory_service.decrease_stock_for_sale.assert_called_once_with(
            session=ANY, product_id=1, quantity=1.0, sale_id=102
        )
        self.assertEqual(created_sale.id, 102)
        self.assertEqual(len(created_sale.items), 2)


    @patch('infrastructure.persistence.utils.session_scope')
    def test_create_sale_validation_empty_list(self, mock_session_scope):
        """Test creating sale with an empty item list raises ValueError."""
        with self.assertRaisesRegex(ValueError, "Cannot create a sale with no items."):
            self.sale_service.create_sale(items_data=[], user_id=1, payment_type="Efectivo")
        self.mock_sale_repo.add_sale.assert_not_called()

    @patch('infrastructure.persistence.utils.session_scope')
    def test_create_sale_validation_missing_data(self, mock_session_scope):
        """Test creating sale with missing item data raises ValueError."""
        items_data = [
            {'product_id': 1} # Missing quantity
        ]
        with self.assertRaisesRegex(ValueError, "Missing 'product_id' or 'quantity'"):
            self.sale_service.create_sale(items_data=items_data, user_id=1, payment_type="Efectivo")
        self.mock_sale_repo.add_sale.assert_not_called()

    @patch('infrastructure.persistence.utils.session_scope')
    def test_create_sale_validation_invalid_quantity(self, mock_session_scope):
        """Test creating sale with invalid quantity raises ValueError."""
        items_data = [
            {'product_id': 1, 'quantity': 'abc'}
        ]
        with self.assertRaisesRegex(ValueError, "Invalid quantity format"):
            self.sale_service.create_sale(items_data=items_data, user_id=1, payment_type="Efectivo")

        items_data_zero = [
            {'product_id': 1, 'quantity': '0'}
        ]
        with self.assertRaisesRegex(ValueError, "Sale quantity must be positive"):
            self.sale_service.create_sale(items_data=items_data_zero, user_id=1, payment_type="Efectivo")

        items_data_negative = [
            {'product_id': 1, 'quantity': '-1.5'}
        ]
        with self.assertRaisesRegex(ValueError, "Sale quantity must be positive"):
            self.sale_service.create_sale(items_data=items_data_negative, user_id=1, payment_type="Efectivo")
    @patch('infrastructure.persistence.utils.session_scope')
    def test_create_sale_with_various_payment_types(self, mock_session_scope):
        """Test creating sales with each allowed payment type."""
        allowed_payment_types = ["Efectivo", "Tarjeta", "Crédito", "Otro"]
        items_data = [
            {'product_id': 1, 'quantity': '1'}
        ]
        user_id = 42

        # Mock product repo
        self.mock_product_repo.get_by_id.return_value = self.product1

        # Mock add_sale to assign IDs
        def mock_add_sale_impl(sale_arg):
            sale_arg.id = 999
            for idx, item in enumerate(sale_arg.items):
                item.id = 1000 + idx
                item.sale_id = 999
            return sale_arg
        self.mock_sale_repo.add_sale.side_effect = mock_add_sale_impl

        for payment_type in allowed_payment_types:
            created_sale = self.sale_service.create_sale(
                items_data=items_data,
                user_id=user_id,
                payment_type=payment_type
            )
            self.assertEqual(created_sale.payment_type, payment_type)
            self.assertEqual(created_sale.user_id, user_id)
            self.assertEqual(created_sale.items[0].product_id, 1)

    @patch('infrastructure.persistence.utils.session_scope')
    def test_create_sale_with_different_user_ids(self, mock_session_scope):
        """Test creating sales with different user IDs."""
        items_data = [
            {'product_id': 1, 'quantity': '1'}
        ]
        payment_type = "Efectivo"
        user_ids = [101, 202]

        self.mock_product_repo.get_by_id.return_value = self.product1

        def mock_add_sale_impl(sale_arg):
            sale_arg.id = 888
            for idx, item in enumerate(sale_arg.items):
                item.id = 1100 + idx
                item.sale_id = 888
            return sale_arg
        self.mock_sale_repo.add_sale.side_effect = mock_add_sale_impl

        for user_id in user_ids:
            created_sale = self.sale_service.create_sale(
                items_data=items_data,
                user_id=user_id,
                payment_type=payment_type
            )
            self.assertEqual(created_sale.user_id, user_id)
            self.assertEqual(created_sale.payment_type, payment_type)
            self.assertEqual(created_sale.items[0].product_id, 1)

        self.mock_sale_repo.add_sale.assert_not_called()

    @patch('infrastructure.persistence.utils.session_scope')
    def test_create_sale_validation_product_not_found(self, mock_session_scope):
        """Test creating sale with non-existent product ID raises ValueError."""
        # Arrange: Mock product repo to return None for product 99
        self.mock_product_repo.get_by_id.side_effect = lambda pid: {
            1: self.product1
        }.get(pid) # Returns None for pid 99

        items_data = [
            {'product_id': 1, 'quantity': '1'},
            {'product_id': 99, 'quantity': '1'}
        ]

        # Act & Assert
        with self.assertRaisesRegex(ValueError, "Product with ID 99 not found."):
            self.sale_service.create_sale(items_data=items_data, user_id=1, payment_type="Efectivo")
        self.mock_sale_repo.add_sale.assert_not_called()

    @patch('infrastructure.persistence.utils.session_scope')
    def test_create_sale_transactionality_inventory_fail(self, mock_session_scope):
        """Test that if inventory decrease fails, the sale add is effectively rolled back."""
        # Arrange
        self.mock_product_repo.get_by_id.side_effect = lambda pid: {
            1: self.product1,
            2: self.product2
        }.get(pid)

        def mock_add_sale_impl(sale_arg):
            sale_arg.id = 103
            for idx, item in enumerate(sale_arg.items):
                item.id = 400 + idx
                item.sale_id = 103
            return sale_arg
        self.mock_sale_repo.add_sale.side_effect = mock_add_sale_impl

        # Mock inventory service to raise an error on the second call
        inventory_call_count = 0
        def inventory_side_effect(*args, **kwargs):
            nonlocal inventory_call_count
            inventory_call_count += 1
            if inventory_call_count > 1:
                raise ValueError("Insufficient stock simulation")
            return None
        self.mock_inventory_service.decrease_stock_for_sale.side_effect = inventory_side_effect

        items_data = [
            {'product_id': 1, 'quantity': '1'},
            {'product_id': 2, 'quantity': '1'}
        ]

        # Act & Assert: The service should raise the exception from the inventory service
        with self.assertRaisesRegex(ValueError, "Insufficient stock simulation"):
            self.sale_service.create_sale(items_data=items_data, user_id=1, payment_type="Efectivo")

        # Assert that add_sale was called (as it happens before inventory decrease)
        self.mock_sale_repo.add_sale.assert_called_once()
        # Assert inventory decrease was attempted for both items
        self.assertEqual(self.mock_inventory_service.decrease_stock_for_sale.call_count, 2)

        # The session_scope context manager should handle the rollback implicitly.
        # We don't explicitly check rollback in the mock, but verify the exception propagates.

    @patch('infrastructure.persistence.utils.session_scope')
    def test_create_sale_validation_missing_user_id(self, mock_session_scope):
        """Test creating sale with missing user_id raises ValueError."""
        items_data = [{'product_id': 1, 'quantity': '1'}]
        with self.assertRaisesRegex(ValueError, "User ID must be provided"):
            self.sale_service.create_sale(items_data=items_data, user_id=None, payment_type="Efectivo")
        self.mock_sale_repo.add_sale.assert_not_called()

    @patch('infrastructure.persistence.utils.session_scope')
    def test_create_sale_validation_missing_payment_type_non_credit(self, mock_session_scope):
        """Test creating non-credit sale with missing payment_type raises ValueError."""
        items_data = [{'product_id': 1, 'quantity': '1'}]
        with self.assertRaisesRegex(ValueError, "Payment type must be provided"):
            self.sale_service.create_sale(items_data=items_data, user_id=1, payment_type=None, is_credit_sale=False)
        self.mock_sale_repo.add_sale.assert_not_called()

    @patch('infrastructure.persistence.utils.session_scope')
    def test_create_sale_credit_sale_success(self, mock_session_scope):
        """Test creating a credit sale successfully."""
        # Arrange
        self.mock_product_repo.get_by_id.return_value = self.product1
        # Mock customer service to return a customer
        mock_customer = MagicMock()
        mock_customer.id = 50
        self.mock_customer_service.get_customer_by_id.return_value = mock_customer

        def mock_add_sale_impl(sale_arg):
            sale_arg.id = 104
            sale_arg.items[0].id = 500
            sale_arg.items[0].sale_id = 104
            return sale_arg
        self.mock_sale_repo.add_sale.side_effect = mock_add_sale_impl

        items_data = [{'product_id': 1, 'quantity': '3'}]
        user_id = 3
        customer_id = 50

        # Act
        created_sale = self.sale_service.create_sale(
            items_data=items_data,
            user_id=user_id,
            payment_type=None, # Payment type ignored for credit sale
            customer_id=customer_id,
            is_credit_sale=True
        )

        # Assert
        self.mock_customer_service.get_customer_by_id.assert_called_once_with(customer_id)
        self.mock_sale_repo.add_sale.assert_called_once()
        call_args, _ = self.mock_sale_repo.add_sale.call_args
        sale_arg = call_args[0]
        self.assertEqual(sale_arg.user_id, user_id)
        self.assertEqual(sale_arg.customer_id, customer_id)
        self.assertTrue(sale_arg.is_credit_sale)
        self.assertEqual(sale_arg.payment_type, 'Crédito') # Should be set to Crédito

        # Assert inventory decrease called
        self.mock_inventory_service.decrease_stock_for_sale.assert_called_once_with(
            session=ANY, product_id=1, quantity=3.0, sale_id=104
        )
        # Assert customer debt increase called
        expected_debt_increase = Decimal('30.00') # 3 * 10.0
        self.mock_customer_service.increase_customer_debt.assert_called_once_with(
            session=ANY, customer_id=customer_id, amount=expected_debt_increase
        )
        self.assertEqual(created_sale.id, 104)

    @patch('infrastructure.persistence.utils.session_scope')
    def test_create_sale_credit_sale_missing_customer(self, mock_session_scope):
        """Test creating credit sale without customer_id raises ValueError."""
        items_data = [{'product_id': 1, 'quantity': '1'}]
        with self.assertRaisesRegex(ValueError, "A customer ID must be provided for credit sales."):
            self.sale_service.create_sale(
                items_data=items_data,
                user_id=1,
                payment_type=None,
                customer_id=None, # Missing customer
                is_credit_sale=True
            )
        self.mock_sale_repo.add_sale.assert_not_called()


if __name__ == '__main__':
    unittest.main()
