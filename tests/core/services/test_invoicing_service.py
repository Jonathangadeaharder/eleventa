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

class TestInvoicingService(unittest.TestCase):
    """Tests for the InvoicingService."""

    def setup_method(self, method=None):
        """Set up common test dependencies."""
        # Create mock repositories
        self.invoice_repo = MagicMock()
        self.sale_repo = MagicMock()
        self.customer_repo = MagicMock()
        
        # Create repository factory functions that return the mocks
        self.invoice_repo_factory = lambda session=None: self.invoice_repo
        self.sale_repo_factory = lambda session=None: self.sale_repo
        self.customer_repo_factory = lambda session=None: self.customer_repo
        
        # Create service with factory functions
        self.service = InvoicingService(
            invoice_repo_factory=self.invoice_repo_factory,
            sale_repo_factory=self.sale_repo_factory,
            customer_repo_factory=self.customer_repo_factory
        )

    def test_create_invoice_from_sale_success(self):
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
        
        # Set up repository mocks
        self.sale_repo.get_by_id.return_value = mock_sale
        self.customer_repo.get_by_id.return_value = mock_customer
        self.invoice_repo.get_by_sale_id.return_value = None  # No existing invoice
        self.invoice_repo.get_all.return_value = []  # No existing invoices for numbering
        
        # Mock the added invoice
        mock_invoice = MagicMock(spec=Invoice)
        mock_invoice.id = 1
        mock_invoice.sale_id = 1
        mock_invoice.invoice_number = "0001-00000001"
        self.invoice_repo.add.return_value = mock_invoice
        
        # Call the service method
        result = self.service.create_invoice_from_sale(sale_id=1)
        
        # Assertions
        self.sale_repo.get_by_id.assert_called_once_with(1)
        self.customer_repo.get_by_id.assert_called_once_with(2)
        self.invoice_repo.get_by_sale_id.assert_called_once_with(1)
        
        # Verify invoice creation with correct data
        self.invoice_repo.add.assert_called_once()
        invoice_arg = self.invoice_repo.add.call_args[0][0]
        self.assertEqual(invoice_arg.sale_id, 1)
        self.assertEqual(invoice_arg.customer_id, 2)
        self.assertEqual(invoice_arg.invoice_number, "0001-00000001")
        self.assertEqual(invoice_arg.invoice_type, "B")
        
        # Verify customer details are correctly captured
        self.assertEqual(invoice_arg.customer_details["name"], "Test Customer")
        self.assertEqual(invoice_arg.customer_details["cuit"], "20-12345678-9")
        
        # Verify result
        self.assertEqual(result, mock_invoice)

    def test_create_invoice_sale_not_found(self):
        """Test invoice creation fails when sale is not found."""
        # Mock sale not found
        self.sale_repo.get_by_id.return_value = None
        
        # Expect ValueError
        with self.assertRaises(ValueError) as context:
            self.service.create_invoice_from_sale(sale_id=1)
        
        self.assertIn("not found", str(context.exception))
        # Verify repo calls
        self.sale_repo.get_by_id.assert_called_once_with(1)
        self.invoice_repo.add.assert_not_called()

    def test_create_invoice_already_exists(self):
        """Test invoice creation fails when sale already has an invoice."""
        # Mock sale data
        mock_sale = Mock(spec=Sale)
        mock_sale.id = 1
        self.sale_repo.get_by_id.return_value = mock_sale
        
        # Mock existing invoice
        mock_invoice = Mock(spec=Invoice)
        mock_invoice.id = 5
        self.invoice_repo.get_by_sale_id.return_value = mock_invoice
        
        # Expect ValueError
        with self.assertRaises(ValueError) as context:
            self.service.create_invoice_from_sale(sale_id=1)
        
        self.assertIn("already has an invoice", str(context.exception))
        # Verify repo calls
        self.sale_repo.get_by_id.assert_called_once_with(1)
        self.invoice_repo.get_by_sale_id.assert_called_once_with(1)
        self.invoice_repo.add.assert_not_called()

    def test_create_invoice_no_customer(self):
        """Test invoice creation fails when sale has no customer."""
        # Mock sale with no customer
        mock_sale = Mock(spec=Sale)
        mock_sale.id = 1
        mock_sale.customer_id = None
        self.sale_repo.get_by_id.return_value = mock_sale
        self.invoice_repo.get_by_sale_id.return_value = None
        
        # Expect ValueError
        with self.assertRaises(ValueError) as context:
            self.service.create_invoice_from_sale(sale_id=1)
        
        self.assertIn("no associated customer", str(context.exception))
        # Verify repo calls
        self.sale_repo.get_by_id.assert_called_once_with(1)
        self.invoice_repo.get_by_sale_id.assert_called_once_with(1)
        self.customer_repo.get_by_id.assert_not_called()
        self.invoice_repo.add.assert_not_called()

    def test_create_invoice_customer_not_found(self):
        """Test invoice creation fails when customer is not found."""
        # Mock sale with customer_id
        mock_sale = Mock(spec=Sale)
        mock_sale.id = 1
        mock_sale.customer_id = 99  # Non-existent customer
        self.sale_repo.get_by_id.return_value = mock_sale
        self.invoice_repo.get_by_sale_id.return_value = None
        
        # Mock customer not found
        self.customer_repo.get_by_id.return_value = None
        
        # Expect ValueError
        with self.assertRaises(ValueError) as context:
            self.service.create_invoice_from_sale(sale_id=1)
        
        self.assertIn("Customer with ID 99 not found", str(context.exception))
        # Verify repo calls
        self.sale_repo.get_by_id.assert_called_once_with(1)
        self.invoice_repo.get_by_sale_id.assert_called_once_with(1)
        self.customer_repo.get_by_id.assert_called_once_with(99)
        self.invoice_repo.add.assert_not_called()

    def test_get_next_invoice_number(self):
        """Test invoice number generation logic."""
        # Mock existing invoices with numbers
        mock_invoice1 = Mock(spec=Invoice)
        mock_invoice1.invoice_number = "0001-00000001"
        mock_invoice2 = Mock(spec=Invoice)
        mock_invoice2.invoice_number = "0001-00000005"  # Highest number
        mock_invoice3 = Mock(spec=Invoice)
        mock_invoice3.invoice_number = "0001-00000003"
        
        self.invoice_repo.get_all.return_value = [mock_invoice1, mock_invoice2, mock_invoice3]
        
        # Call the method directly
        result = self.service._generate_next_invoice_number(self.invoice_repo)
        
        # Verify correct number generation
        self.assertEqual(result, "0001-00000006")  # Next after highest (5)
        self.invoice_repo.get_all.assert_called_once()

    def test_get_next_invoice_number_first_invoice(self):
        """Test invoice number generation for first invoice."""
        # Mock no existing invoices
        self.invoice_repo.get_all.return_value = []
        
        # Call the method
        result = self.service._generate_next_invoice_number(self.invoice_repo)
        
        # Verify first invoice number
        self.assertEqual(result, "0001-00000001")
        self.invoice_repo.get_all.assert_called_once()

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

    def test_generate_invoice_pdf(self):
        """
        Test invoice PDF generation functionality.
        
        This test verifies that:
        1. The PDF generation method properly formats invoice data
        2. The correct file is created with expected content
        3. Customer and sale details are properly included
        
        The test uses a temporary file to avoid filesystem pollution.
        """
        # Mock objects for the test
        mock_sale = Mock(spec=Sale)
        mock_sale.id = 1
        mock_sale.customer_id = 2
        mock_sale.timestamp = datetime.now()
        mock_sale.total = Decimal("121.00")
        mock_sale.items = [
            Mock(
                spec=SaleItem,
                product_id=1,
                quantity=Decimal("2"),
                unit_price=Decimal("50.00"),
                description="Test Product",
                product_code="TP001",
                line_total=Decimal("100.00")
            )
        ]
        
        mock_customer = Mock(spec=Customer)
        mock_customer.id = 2
        mock_customer.name = "Test Customer"
        mock_customer.address = "123 Test St"
        mock_customer.cuit = "20-12345678-9"
        mock_customer.iva_condition = "Responsable Inscripto"
        
        # Mock invoice with all required attributes
        mock_invoice = Mock(spec=Invoice)
        mock_invoice.id = 1
        mock_invoice.invoice_number = "0001-00000001"
        mock_invoice.invoice_type = "A"
        mock_invoice.timestamp = datetime.now()
        mock_invoice.invoice_date = datetime.now()
        mock_invoice.sale_id = 1
        mock_invoice.customer_id = 2
        mock_invoice.total = Decimal("121.00")
        mock_invoice.subtotal = Decimal("100.00")
        mock_invoice.iva_amount = Decimal("21.00")
        mock_invoice.iva_condition = "Responsable Inscripto"
        mock_invoice.cae = "12345678901234"
        mock_invoice.cae_due_date = datetime.now() + timedelta(days=10)
        mock_invoice.is_active = True
        mock_invoice.customer_details = {
            "name": "Test Customer",
            "address": "123 Test St",
            "cuit": "20-12345678-9",
            "iva_condition": "Responsable Inscripto"
        }
        
        # Set up repository returns
        self.invoice_repo.get_by_id.return_value = mock_invoice
        self.sale_repo.get_by_id.return_value = mock_sale
        self.customer_repo.get_by_id.return_value = mock_customer
        
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
                "logo_path": None,  # No logo for test
                "iva_condition": "Responsable Inscripto"
            }
            
            # Call PDF generation
            # Add patch for Config.PDF_OUTPUT_DIR
            with patch("os.makedirs") as mock_makedirs, \
                 patch("core.services.invoicing_service.Config") as mock_config:
                # Create a PDF_OUTPUT_DIR attribute on the mock Config
                mock_config.PDF_OUTPUT_DIR = tempfile.gettempdir()
                
                result_path = self.service.generate_invoice_pdf(
                    invoice_id=1,
                    filename=os.path.basename(tmp_path),  # Just use the filename
                    output_path=os.path.dirname(tmp_path), # Specify output path explicitly
                    store_info=store_info
                )
            
            # Assertions
            self.invoice_repo.get_by_id.assert_called_once_with(1)
            self.assertEqual(result_path, tmp_path)
            
            # Check that the file exists
            self.assertTrue(os.path.exists(tmp_path))
            
            # Read the file contents and verify it contains expected information
            with open(tmp_path, "r") as f:
                content = f.read()
                self.assertIn("INVOICE 0001-00000001", content)
                self.assertIn("Type: A", content)
                self.assertIn("Test Customer", content)
                self.assertIn("Test Product", content)
                
        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_generate_invoice_pdf_error_handling(self):
        """Test error handling when generating PDF."""
        # Set up mocks
        self.invoice_repo.get_by_id.return_value = None  # Invoice not found
        
        # Expect ValueError for non-existent invoice
        with self.assertRaises(ValueError) as context:
            with patch("core.services.invoicing_service.Config") as mock_config:
                # Create a PDF_OUTPUT_DIR attribute on the mock Config
                mock_config.PDF_OUTPUT_DIR = tempfile.gettempdir()
                self.service.generate_invoice_pdf(invoice_id=999)
            
        self.assertIn("not found", str(context.exception))

if __name__ == "__main__":
    unittest.main()