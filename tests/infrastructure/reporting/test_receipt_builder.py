import unittest
import os
import tempfile
from decimal import Decimal
from datetime import datetime

from core.models.sale import Sale, SaleItem
from infrastructure.reporting.receipt_builder import (
    format_currency, format_sale_date, format_item_row, generate_receipt_pdf
)

class TestReceiptBuilder(unittest.TestCase):
    def setUp(self):
        """Set up test data."""
        # Create a sample sale with items
        self.item1 = SaleItem(
            id=1,
            sale_id=101,
            product_id=201,
            product_code="P001",
            product_description="Test Product 1",
            quantity=Decimal("2"),
            unit_price=Decimal("10.50")
        )
        
        self.item2 = SaleItem(
            id=2,
            sale_id=101,
            product_id=202,
            product_code="P002",
            product_description="Test Product 2 with a very long description that should be truncated",
            quantity=Decimal("1.5"),
            unit_price=Decimal("20.00")
        )
        
        self.sale = Sale(
            id=101,
            timestamp=datetime(2025, 4, 13, 14, 30, 0),
            items=[self.item1, self.item2],
            user_id=5,
            payment_type="Efectivo"
        )
        
        # Add user name and customer name attributes that would be added by the service
        self.sale.user_name = "Usuario 5"
        self.sale.customer_name = "Cliente de Prueba"
        
        # Store info for the receipt
        self.store_info = {
            'name': "Tienda de Prueba",
            'address': "Calle Ejemplo 123",
            'phone': "123-456-7890",
            'tax_id': "30-12345678-9"
        }

    def test_format_currency(self):
        """Test the format_currency helper function."""
        self.assertEqual(format_currency(10.5), "$10.50")
        self.assertEqual(format_currency(Decimal("10.5")), "$10.50")
        self.assertEqual(format_currency(0), "$0.00")
        self.assertEqual(format_currency(1000), "$1000.00")

    def test_format_sale_date(self):
        """Test the format_sale_date helper function."""
        date_obj = datetime(2025, 4, 13, 14, 30, 0)
        self.assertEqual(format_sale_date(date_obj), "13/04/2025 14:30:00")
        
        # Test with string input
        self.assertEqual(format_sale_date("2025-04-13"), "2025-04-13")

    def test_format_item_row(self):
        """Test the format_item_row helper function."""
        # Test with item1 (whole quantities)
        row = format_item_row(self.item1)
        self.assertEqual(row, ["P001", "Test Product 1", "2", "$10.50", "$21.00"])
        
        # Test with item2 (decimal quantities)
        row = format_item_row(self.item2)
        self.assertEqual(row, ["P002", "Test Product 2 with a very long d", "1.50", "$20.00", "$30.00"])
        
        # Test truncation of long descriptions
        long_desc_item = SaleItem(
            product_id=203,
            quantity=Decimal("1"),
            unit_price=Decimal("15.00"),
            product_code="P003",
            product_description="This is an extremely long product description that will definitely be truncated in the receipt"
        )
        row = format_item_row(long_desc_item)
        self.assertEqual(len(row[1]), 30)  # Description should be truncated to 30 chars

    def test_generate_receipt_pdf(self):
        """Test the PDF generation function."""
        # Create a temporary directory for test PDFs
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate a PDF file
            pdf_path = os.path.join(temp_dir, "test_receipt.pdf")
            result_path = generate_receipt_pdf(self.sale, self.store_info, pdf_path)
            
            # Check that the function returns the correct path
            self.assertEqual(result_path, pdf_path)
            
            # Check that the PDF file was created
            self.assertTrue(os.path.exists(pdf_path))
            
            # Check that the file size is greater than zero (valid PDF)
            self.assertGreater(os.path.getsize(pdf_path), 0)
            
            # Note: We can't easily check the PDF content programmatically
            # A manual check of the generated PDF is recommended


if __name__ == '__main__':
    unittest.main()