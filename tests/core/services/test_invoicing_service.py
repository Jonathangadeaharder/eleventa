"""
Tests for the InvoicingService class.

This test suite covers the invoicing functionality including:
- Invoice creation from sales
- Invoice number generation and validation
- Invoice type determination based on customer IVA condition
- Error cases for invoice creation
- PDF generation for invoices

Coverage goals:
- 100% coverage of the InvoicingService public API
- Error handling scenarios for all public methods
- Edge cases for invoice numbering

Test dependencies:
- unittest mocking for isolation from database
- temp files for PDF generation tests
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal
import os
import tempfile

from core.services.invoicing_service import InvoicingService
from core.models.invoice import Invoice
from core.models.sale import Sale, SaleItem
from core.models.customer import Customer
from core.exceptions import ResourceNotFoundError
from core.interfaces.repository_interfaces import IInvoiceRepository

class TestInvoicingService(unittest.TestCase):
    """Tests for the InvoicingService."""

    def setup_method(self, method=None):
        """Set up common test dependencies."""
        # Create service with Unit of Work pattern
        self.service = InvoicingService()

    @patch('core.services.invoicing_service.unit_of_work')
    def test_create_invoice_from_sale_success(self, mock_uow):
        """Test successful invoice creation from a sale."""
        # Mock sale data with customer_id
        mock_sale = MagicMock(spec=Sale)
        mock_sale.id = 1
        mock_sale.customer_id = 2
        mock_sale.total = Decimal("121.00")  # Including IVA
        mock_sale.items = [
            MagicMock(spec=SaleItem, product_id=1, quantity=Decimal("2"), unit_price=Decimal("50.00"))
        ]
        
        # Mock customer data
        mock_customer = MagicMock(spec=Customer)
        mock_customer.id = 2
        mock_customer.name = "Test Customer"
        mock_customer.address = "123 Test St"
        mock_customer.cuit = "20-12345678-9"
        mock_customer.iva_condition = "Consumidor Final"
        mock_customer.email = "test@example.com"
        mock_customer.phone = "555-1234"
        
        # Set up Unit of Work mock
        mock_context = MagicMock()
        mock_uow.return_value.__enter__.return_value = mock_context
        mock_context.sales.get_by_id.return_value = mock_sale
        mock_context.customers.get_by_id.return_value = mock_customer
        mock_context.invoices.get_by_sale_id.return_value = None  # No existing invoice
        mock_context.invoices.get_all.return_value = []  # No existing invoices for numbering
        
        # Mock the added invoice
        mock_invoice = MagicMock(spec=Invoice)
        mock_invoice.id = 1
        mock_invoice.sale_id = 1
        mock_invoice.invoice_number = "0001-00000001"
        
        def mock_add(invoice):
            invoice.id = 1
            return invoice
        mock_context.invoices.add.side_effect = mock_add
        
        # Call the service method
        result = self.service.create_invoice_from_sale(sale_id=1)
        
        # Assertions
        mock_context.sales.get_by_id.assert_called_once_with(1)
        mock_context.customers.get_by_id.assert_called_once_with(2)
        mock_context.invoices.get_by_sale_id.assert_called_once_with(1)
        
        # Verify invoice creation with correct data
        mock_context.invoices.add.assert_called_once()
        invoice_arg = mock_context.invoices.add.call_args[0][0]
        self.assertEqual(invoice_arg.sale_id, 1)
        self.assertEqual(invoice_arg.customer_id, 2)
        self.assertEqual(invoice_arg.invoice_number, "0001-00000001")
        self.assertEqual(invoice_arg.invoice_type, "B")
        
        # Verify customer details are correctly captured
        self.assertEqual(invoice_arg.customer_details["name"], "Test Customer")
        self.assertEqual(invoice_arg.customer_details["cuit"], "20-12345678-9")
        
        # Verify result
        self.assertEqual(result.sale_id, 1)

    @patch('core.services.invoicing_service.unit_of_work')
    def test_create_invoice_sale_not_found(self, mock_uow):
        """Test invoice creation fails when sale is not found."""
        # Set up Unit of Work mock
        mock_context = MagicMock()
        mock_uow.return_value.__enter__.return_value = mock_context
        mock_context.sales.get_by_id.return_value = None
        
        # Expect ValueError
        with self.assertRaises(ValueError) as context:
            self.service.create_invoice_from_sale(sale_id=1)
        
        self.assertIn("not found", str(context.exception))
        # Verify repo calls
        mock_context.sales.get_by_id.assert_called_once_with(1)
        mock_context.invoices.add.assert_not_called()

    @patch('core.services.invoicing_service.unit_of_work')
    def test_create_invoice_already_exists(self, mock_uow):
        """Test invoice creation fails when sale already has an invoice."""
        # Mock sale data
        mock_sale = Mock(spec=Sale)
        mock_sale.id = 1
        
        # Mock existing invoice
        mock_invoice = Mock(spec=Invoice)
        mock_invoice.id = 5
        
        # Set up Unit of Work mock
        mock_context = MagicMock()
        mock_uow.return_value.__enter__.return_value = mock_context
        mock_context.sales.get_by_id.return_value = mock_sale
        mock_context.invoices.get_by_sale_id.return_value = mock_invoice
        
        # Expect ValueError
        with self.assertRaises(ValueError) as context:
            self.service.create_invoice_from_sale(sale_id=1)
        
        self.assertIn("already has an invoice", str(context.exception))
        # Verify repo calls
        mock_context.sales.get_by_id.assert_called_once_with(1)
        mock_context.invoices.get_by_sale_id.assert_called_once_with(1)
        mock_context.invoices.add.assert_not_called()

    @patch('core.services.invoicing_service.unit_of_work')
    def test_create_invoice_no_customer(self, mock_uow):
        """Test invoice creation fails when sale has no customer."""
        # Mock sale data without customer
        mock_sale = Mock(spec=Sale)
        mock_sale.id = 1
        mock_sale.customer_id = None
        
        # Set up Unit of Work mock
        mock_context = MagicMock()
        mock_uow.return_value.__enter__.return_value = mock_context
        mock_context.sales.get_by_id.return_value = mock_sale
        mock_context.invoices.get_by_sale_id.return_value = None
        
        # Expect ValueError
        with self.assertRaises(ValueError) as context:
            self.service.create_invoice_from_sale(sale_id=1)
        
        self.assertIn("customer", str(context.exception))
        # Verify repo calls
        mock_context.sales.get_by_id.assert_called_once_with(1)
        mock_context.invoices.get_by_sale_id.assert_called_once_with(1)
        mock_context.customers.get_by_id.assert_not_called()
        mock_context.invoices.add.assert_not_called()

    @patch('core.services.invoicing_service.unit_of_work')
    def test_create_invoice_customer_not_found(self, mock_uow):
        """Test invoice creation fails when customer is not found."""
        # Mock sale data with customer ID
        mock_sale = Mock(spec=Sale)
        mock_sale.id = 1
        mock_sale.customer_id = 10
        
        # Set up Unit of Work mock
        mock_context = MagicMock()
        mock_uow.return_value.__enter__.return_value = mock_context
        mock_context.sales.get_by_id.return_value = mock_sale
        mock_context.invoices.get_by_sale_id.return_value = None
        mock_context.customers.get_by_id.return_value = None
        
        # Expect ValueError
        with self.assertRaises(ValueError) as context:
            self.service.create_invoice_from_sale(sale_id=1)
        
        self.assertIn("Customer", str(context.exception))
        self.assertIn("not found", str(context.exception))
        # Verify repo calls
        mock_context.sales.get_by_id.assert_called_once_with(1)
        mock_context.invoices.get_by_sale_id.assert_called_once_with(1)
        mock_context.customers.get_by_id.assert_called_once_with(10)
        mock_context.invoices.add.assert_not_called()

    @patch('core.services.invoicing_service.unit_of_work')
    def test_get_next_invoice_number(self, mock_uow):
        """Test invoice number generation logic."""
        # Mock existing invoices with numbers
        mock_invoice1 = Mock(spec=Invoice)
        mock_invoice1.invoice_number = "0001-00000001"
        mock_invoice2 = Mock(spec=Invoice)
        mock_invoice2.invoice_number = "0001-00000005"  # Highest number
        mock_invoice3 = Mock(spec=Invoice)
        mock_invoice3.invoice_number = "0001-00000003"
        
        # Set up Unit of Work mock
        mock_context = MagicMock()
        mock_uow.return_value.__enter__.return_value = mock_context
        mock_context.invoices.get_all.return_value = [mock_invoice1, mock_invoice2, mock_invoice3]
        
        # Call the method directly
        result = self.service._generate_next_invoice_number(mock_context.invoices)
        
        # Verify correct number generation
        self.assertEqual(result, "0001-00000006")  # Next after highest (5)
        mock_context.invoices.get_all.assert_called_once()

    @patch('core.services.invoicing_service.unit_of_work')
    def test_get_next_invoice_number_first_invoice(self, mock_uow):
        """Test invoice number generation for first invoice."""
        # Set up Unit of Work mock
        mock_context = MagicMock()
        mock_uow.return_value.__enter__.return_value = mock_context
        mock_context.invoices.get_all.return_value = []
        
        # Call the method
        result = self.service._generate_next_invoice_number(mock_context.invoices)
        
        # Verify first invoice number
        self.assertEqual(result, "0001-00000001")
        mock_context.invoices.get_all.assert_called_once()

    def test_determine_invoice_type(self):
        """Test invoice type determination based on IVA condition."""
        # Test different IVA conditions
        self.assertEqual(self.service._determine_invoice_type("Responsable Inscripto"), "A")
        self.assertEqual(self.service._determine_invoice_type("Monotributista"), "B")
        self.assertEqual(self.service._determine_invoice_type("Consumidor Final"), "B")
        self.assertEqual(self.service._determine_invoice_type(None), "B")  # Default case
        self.assertEqual(self.service._determine_invoice_type("Unknown"), "B")  # Default case

    def test_get_iva_rate(self):
        """Test IVA rate calculation based on invoice type and customer condition."""
        # Test Type A invoice for registered taxpayer
        self.assertEqual(
            self.service._get_iva_rate("A", "Responsable Inscripto"),
            Decimal("0.21")
        )
        
        # Test Type B invoice (consumer)
        self.assertEqual(
            self.service._get_iva_rate("B", "Consumidor Final"),
            Decimal("0")
        )
        
        # Test exempt entity
        self.assertEqual(
            self.service._get_iva_rate("B", "Exento"),
            Decimal("0")
        )
        
        # Test default case
        self.assertEqual(
            self.service._get_iva_rate("C", None),
            Decimal("0.21")
        )

    @patch('core.services.invoicing_service.unit_of_work')
    def test_generate_invoice_pdf(self, mock_uow):
        """Test PDF generation for invoice."""
        # Mock invoice data
        mock_invoice = Mock(spec=Invoice)
        mock_invoice.id = 1
        mock_invoice.sale_id = 1
        mock_invoice.invoice_number = "A-0001-00000001"
        mock_invoice.invoice_type = "A"
        mock_invoice.invoice_date = datetime(2023, 1, 15)
        mock_invoice.issue_date = datetime(2023, 1, 15)
        mock_invoice.due_date = datetime(2023, 2, 15)
        mock_invoice.total_amount = Decimal('1000.00')
        mock_invoice.iva_amount = Decimal('210.00')
        mock_invoice.net_amount = Decimal('790.00')
        mock_invoice.subtotal = Decimal('790.00')
        mock_invoice.total = Decimal('1000.00')
        mock_invoice.cae = "12345678901234"
        mock_invoice.cae_due_date = datetime(2023, 1, 25)
        mock_invoice.customer_id = 1
        mock_invoice.customer_details = {
            "name": "Test Customer",
            "address": "123 Test St",
            "cuit": "20-12345678-9",
            "iva_condition": "Responsable Inscripto"
        }
        
        # Mock sale data
        mock_sale = Mock(spec=Sale)
        mock_sale.id = 1
        mock_sale.total = Decimal("1000.00")
        mock_sale_item = Mock(spec=SaleItem)
        mock_sale_item.product_code = "TP001"
        mock_sale_item.quantity = Decimal("2")
        mock_sale_item.unit_price = Decimal("500.00")
        mock_sale_item.product_description = "Test Product"
        mock_sale_item.total_price = Decimal("1000.00")
        mock_sale_item.subtotal = Decimal("1000.00")
        mock_sale.items = [mock_sale_item]
        
        # Set up Unit of Work mock
        mock_context = MagicMock()
        mock_uow.return_value.__enter__.return_value = mock_context
        mock_context.invoices.get_by_id.return_value = mock_invoice
        mock_context.sales.get_by_id.return_value = mock_sale
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Store info
            store_info = {
                "name": "Test Store",
                "address": "123 Store St",
                "phone": "555-1234",
                "cuit": "30-71234567-9",
                "logo_path": None,
                "iva_condition": "Responsable Inscripto"
            }
            
            # Mock the PDF generation by patching os.makedirs and Config
            with patch('os.makedirs') as mock_makedirs, \
                 patch('core.services.invoicing_service.Config') as mock_config:
                mock_config.PDF_OUTPUT_DIR = tempfile.gettempdir()
                
                result = self.service.generate_invoice_pdf(
                    invoice_id=1,
                    filename=os.path.basename(tmp_path),
                    store_info=store_info
                )
                
                # Assertions
                mock_context.invoices.get_by_id.assert_called_once_with(1)
                mock_context.sales.get_by_id.assert_called_once_with(1)
                self.assertTrue(result.endswith('.pdf'))

        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @patch('core.services.invoicing_service.unit_of_work')
    def test_generate_invoice_pdf_error_handling(self, mock_uow):
        """Test error handling when generating PDF."""
        # Set up Unit of Work mock
        mock_context = MagicMock()
        mock_uow.return_value.__enter__.return_value = mock_context
        mock_context.invoices.get_by_id.return_value = None  # Invoice not found
        
        # Expect ResourceNotFoundError for non-existent invoice
        with self.assertRaises(ResourceNotFoundError) as context:
            self.service.generate_invoice_pdf(invoice_id=999)
            
        self.assertIn("not found", str(context.exception))
        mock_context.invoices.get_by_id.assert_called_once_with(999)

if __name__ == "__main__":
    unittest.main()