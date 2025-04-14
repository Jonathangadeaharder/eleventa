import unittest
from unittest.mock import MagicMock, patch
import os
from decimal import Decimal
from datetime import datetime

from core.services.sale_service import SaleService
from core.models.sale import Sale, SaleItem
from core.models.customer import Customer


class TestReceiptGeneration(unittest.TestCase):
    def setUp(self):
        """Set up the test environment with mocks."""
        # Create mocks for dependencies
        self.mock_sale_repo = MagicMock()
        self.mock_product_repo = MagicMock()
        self.mock_inventory_service = MagicMock()
        self.mock_customer_service = MagicMock()
        
        # Create the service with mocked dependencies
        self.sale_service = SaleService(
            sale_repository=self.mock_sale_repo,
            product_repository=self.mock_product_repo,
            inventory_service=self.mock_inventory_service,
            customer_service=self.mock_customer_service
        )
        
        # Sample sale data
        self.sale = Sale(
            id=101,
            timestamp=datetime(2025, 4, 13, 14, 30, 0),
            items=[
                SaleItem(
                    id=1,
                    sale_id=101,
                    product_id=201,
                    product_code="P001",
                    product_description="Test Product 1",
                    quantity=Decimal("2"),
                    unit_price=Decimal("10.50")
                ),
                SaleItem(
                    id=2,
                    sale_id=101,
                    product_id=202,
                    product_code="P002",
                    product_description="Test Product 2",
                    quantity=Decimal("1.5"),
                    unit_price=Decimal("20.00")
                )
            ],
            user_id=5,
            payment_type="Efectivo"
        )
        
        # Sample customer
        self.customer = Customer(
            id=50,
            name="Cliente de Prueba",
            email="cliente@ejemplo.com",
            phone="123-456-7890"
        )

    @patch('core.services.sale_service.create_receipt_pdf')
    @patch('core.services.sale_service.os.makedirs')
    def test_generate_receipt_pdf_success(self, mock_makedirs, mock_create_receipt):
        """Test successfully generating a receipt PDF."""
        # Configure mocks
        self.mock_sale_repo.get_by_id.return_value = self.sale
        self.mock_customer_service.get_customer_by_id.return_value = self.customer
        mock_create_receipt.return_value = "/path/to/generated/receipt.pdf"
        
        # Call the method with a specific filename
        result = self.sale_service.generate_receipt_pdf(101, "test_receipt.pdf")
        
        # Assert expected behavior
        self.mock_sale_repo.get_by_id.assert_called_once_with(101)
        self.mock_customer_service.get_customer_by_id.assert_not_called()  # Customer ID not set in our sale
        mock_makedirs.assert_called_once()  # Directory should be created
        mock_create_receipt.assert_called_once()  # Receipt builder should be called
        
        # Verify format of result
        self.assertEqual(result, "/path/to/generated/receipt.pdf")
        
        # Check that sale was enhanced with user name
        # The first argument to create_receipt_pdf is the sale object
        called_sale = mock_create_receipt.call_args[0][0]
        self.assertEqual(called_sale.user_name, "Usuario 5")

    @patch('core.services.sale_service.create_receipt_pdf')
    def test_generate_receipt_pdf_with_customer(self, mock_create_receipt):
        """Test generating a receipt PDF for a sale with a customer."""
        # Set customer ID on the sale
        self.sale.customer_id = 50
        
        # Configure mocks
        self.mock_sale_repo.get_by_id.return_value = self.sale
        self.mock_customer_service.get_customer_by_id.return_value = self.customer
        mock_create_receipt.return_value = "/path/to/generated/receipt.pdf"
        
        # Call the method
        result = self.sale_service.generate_receipt_pdf(101)
        
        # Assert customer service was called
        self.mock_customer_service.get_customer_by_id.assert_called_once_with(50)
        
        # Check that sale was enhanced with customer name
        called_sale = mock_create_receipt.call_args[0][0]
        self.assertEqual(called_sale.customer_name, "Cliente de Prueba")

    def test_generate_receipt_pdf_sale_not_found(self):
        """Test handling when the sale ID is not found."""
        # Configure mock to return None for the sale
        self.mock_sale_repo.get_by_id.return_value = None
        
        # Assert the method raises ValueError with appropriate message
        with self.assertRaisesRegex(ValueError, "Sale with ID 101 not found"):
            self.sale_service.generate_receipt_pdf(101)
            
    @patch('core.services.sale_service.create_receipt_pdf')
    def test_generate_receipt_pdf_config_values(self, mock_create_receipt):
        """Test that the correct store info from Config is passed to the receipt generator."""
        # Configure mocks
        self.mock_sale_repo.get_by_id.return_value = self.sale
        mock_create_receipt.return_value = "/path/to/generated/receipt.pdf"
        
        # Call the method
        with patch('core.services.sale_service.Config') as mock_config:
            # Set up config mock values
            mock_config.STORE_NAME = "Store Name from Config"
            mock_config.STORE_ADDRESS = "Address from Config"
            mock_config.STORE_CUIT = "CUIT from Config"
            mock_config.STORE_IVA_CONDITION = "IVA Condition from Config"
            mock_config.STORE_PHONE = "Phone from Config"
            
            self.sale_service.generate_receipt_pdf(101)
            
            # Extract the store_info dict that was passed to create_receipt_pdf
            store_info = mock_create_receipt.call_args[0][1]
            
            # Verify the config values were used
            self.assertEqual(store_info['name'], "Store Name from Config")
            self.assertEqual(store_info['address'], "Address from Config")
            self.assertEqual(store_info['tax_id'], "CUIT from Config")
            self.assertEqual(store_info['iva_condition'], "IVA Condition from Config")
            self.assertEqual(store_info['phone'], "Phone from Config")


if __name__ == '__main__':
    unittest.main()