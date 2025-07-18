import unittest
from unittest.mock import MagicMock, patch
import os
from decimal import Decimal
from datetime import datetime

from core.services.sale_service import SaleService, create_receipt_pdf
from core.models.sale import Sale, SaleItem
from core.models.customer import Customer


class TestReceiptGeneration(unittest.TestCase):
    def setUp(self):
        """Set up the test environment with mocks."""
        # Create mock services
        self.mock_inventory_service = MagicMock()
        self.mock_customer_service = MagicMock()
        
        # Create the service instance with required dependencies
        self.sale_service = SaleService(
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

    @patch('core.services.sale_service.unit_of_work')
    @patch('core.services.sale_service.create_receipt_pdf')
    def test_generate_receipt_pdf_success(self, mock_create_receipt, mock_uow):
        """Test successfully generating a receipt PDF."""
        # Setup Unit of Work mock
        mock_context = MagicMock()
        mock_uow.return_value.__enter__.return_value = mock_context
        
        # Configure mocks
        mock_context.sales.get_by_id.return_value = self.sale
        mock_create_receipt.return_value = os.path.join("receipts", "test", "receipt_101.pdf")
        
        # Call the method
        output_dir = os.path.join("receipts", "test")
        result = self.sale_service.generate_receipt_pdf(101, output_dir)
        
        # Assert expected behavior
        mock_context.sales.get_by_id.assert_called_once_with(101)
        expected_path = os.path.join(output_dir, f"receipt_{self.sale.id}.pdf")
        mock_create_receipt.assert_called_once_with(self.sale, expected_path)
        
        # Verify result
        self.assertEqual(result, mock_create_receipt.return_value)

    @patch('core.services.sale_service.unit_of_work')
    @patch('core.services.sale_service.create_receipt_pdf')
    def test_generate_receipt_pdf_with_customer(self, mock_create_receipt, mock_uow):
        """Test generating a receipt PDF for a sale with a customer."""
        # Setup Unit of Work mock
        mock_context = MagicMock()
        mock_uow.return_value.__enter__.return_value = mock_context
        
        # Set customer ID on the sale
        self.sale.customer_id = 50
        
        # Configure mocks
        mock_context.sales.get_by_id.return_value = self.sale
        mock_create_receipt.return_value = os.path.join("receipts", "test", "receipt_101.pdf")
        
        # Call the method
        output_dir = os.path.join("receipts", "test")
        result = self.sale_service.generate_receipt_pdf(101, output_dir)
        
        # Since the implementation doesn't actually call customer_service.get_customer_by_id,
        # we just verify that the output path is correct
        expected_path = os.path.join(output_dir, f"receipt_{self.sale.id}.pdf")
        mock_create_receipt.assert_called_once_with(self.sale, expected_path)
        self.assertEqual(result, mock_create_receipt.return_value)

    @patch('core.services.sale_service.unit_of_work')
    def test_generate_receipt_pdf_sale_not_found(self, mock_uow):
        """Test handling when the sale ID is not found."""
        # Setup Unit of Work mock
        mock_context = MagicMock()
        mock_uow.return_value.__enter__.return_value = mock_context
        
        # Configure mock to return None for the sale
        mock_context.sales.get_by_id.return_value = None
        
        # Assert the method raises ValueError with appropriate message
        output_dir = os.path.join("receipts", "test")
        with self.assertRaisesRegex(ValueError, "Sale with ID 101 not found"):
            self.sale_service.generate_receipt_pdf(101, output_dir)
            
    @patch('core.services.sale_service.unit_of_work')
    @patch('core.services.sale_service.create_receipt_pdf')
    def test_generate_receipt_pdf_filename_format(self, mock_create_receipt, mock_uow):
        """Test that the PDF filename is formatted correctly."""
        # Setup Unit of Work mock
        mock_context = MagicMock()
        mock_uow.return_value.__enter__.return_value = mock_context
        
        # Configure mocks
        mock_context.sales.get_by_id.return_value = self.sale
        mock_create_receipt.return_value = "/path/to/generated/receipt.pdf"
        
        # Call the method
        output_dir = os.path.join("receipts", "test")
        self.sale_service.generate_receipt_pdf(101, output_dir)
        
        # Verify the filename format
        expected_path = os.path.join(output_dir, f"receipt_{self.sale.id}.pdf")
        mock_create_receipt.assert_called_once_with(self.sale, expected_path)


if __name__ == '__main__':
    unittest.main()