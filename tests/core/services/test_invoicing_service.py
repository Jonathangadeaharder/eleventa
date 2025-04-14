import unittest
from unittest.mock import Mock, patch
from datetime import datetime
from decimal import Decimal
import os
import tempfile

from core.services.invoicing_service import InvoicingService
from core.models.invoice import Invoice
from core.models.sale import Sale, SaleItem
from core.models.customer import Customer

class TestInvoicingService(unittest.TestCase):
    """Tests for the InvoicingService."""

    def setUp(self):
        """Set up common test dependencies."""
        self.invoice_repo = Mock()
        self.sale_repo = Mock()
        self.customer_repo = Mock()
        self.service = InvoicingService(
            invoice_repo=self.invoice_repo,
            sale_repo=self.sale_repo,
            customer_repo=self.customer_repo
        )

    def test_create_invoice_from_sale_success(self):
        """Test successful invoice creation from a sale."""
        # Mock sale data with customer_id
        mock_sale = Mock(spec=Sale)
        mock_sale.id = 1
        mock_sale.customer_id = 2
        mock_sale.total = Decimal("121.00")  # Including IVA
        mock_sale.items = [
            Mock(spec=SaleItem, product_id=1, quantity=Decimal("2"), unit_price=Decimal("50.00"))
        ]
        
        # Mock customer data
        mock_customer = Mock(spec=Customer)
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
        mock_invoice = Mock(spec=Invoice)
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
        result = self.service._generate_next_invoice_number()
        
        # Verify correct number generation
        self.assertEqual(result, "0001-00000006")  # Next after highest (5)
        self.invoice_repo.get_all.assert_called_once()

    def test_get_next_invoice_number_first_invoice(self):
        """Test invoice number generation for first invoice."""
        # Mock no existing invoices
        self.invoice_repo.get_all.return_value = []
        
        # Call the method
        result = self.service._generate_next_invoice_number()
        
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
        """Test PDF generation for an invoice."""
        # Mock repositories
        self.invoice_repo = Mock()
        self.sale_repo = Mock()
        self.customer_repo = Mock()
        self.service = InvoicingService(
            invoice_repo=self.invoice_repo,
            sale_repo=self.sale_repo,
            customer_repo=self.customer_repo
        )
        
        # Mock invoice
        mock_invoice = Mock(spec=Invoice)
        mock_invoice.id = 1
        mock_invoice.sale_id = 2
        mock_invoice.invoice_number = "0001-00000001"
        mock_invoice.invoice_date = datetime.now()
        mock_invoice.invoice_type = "B"
        mock_invoice.customer_details = {
            "name": "Test Customer",
            "address": "Test Address",
            "cuit": "20-12345678-9",
            "iva_condition": "Consumidor Final"
        }
        mock_invoice.subtotal = Decimal("100.00")
        mock_invoice.iva_amount = Decimal("21.00")
        mock_invoice.total = Decimal("121.00")
        mock_invoice.iva_condition = "Consumidor Final"
        mock_invoice.cae = "12345678901234"
        mock_invoice.cae_due_date = datetime(2025, 5, 1)
        mock_invoice.is_active = True
        
        # Mock sale with items
        mock_sale_item1 = Mock(spec=SaleItem)
        mock_sale_item1.product_code = "P001"
        mock_sale_item1.product_description = "Test Product 1"
        mock_sale_item1.quantity = Decimal("2")
        mock_sale_item1.unit_price = Decimal("30.00")
        mock_sale_item1.subtotal = Decimal("60.00")
        
        mock_sale_item2 = Mock(spec=SaleItem)
        mock_sale_item2.product_code = "P002"
        mock_sale_item2.product_description = "Test Product 2"
        mock_sale_item2.quantity = Decimal("1")
        mock_sale_item2.unit_price = Decimal("40.00")
        mock_sale_item2.subtotal = Decimal("40.00")
        
        mock_sale = Mock(spec=Sale)
        mock_sale.id = 2
        mock_sale.items = [mock_sale_item1, mock_sale_item2]
        
        # Set up repository mocks
        self.invoice_repo.get_by_id.return_value = mock_invoice
        self.sale_repo.get_by_id.return_value = mock_sale
        
        # Mock InvoiceBuilder
        with patch('infrastructure.reporting.invoice_builder.InvoiceBuilder') as mock_builder_class, \
             patch('core.services.invoicing_service.Config') as mock_config:
            
            # Set Config mock values
            mock_config.STORE_NAME = "Store Name from Config"
            mock_config.STORE_ADDRESS = "Address from Config"
            mock_config.STORE_CUIT = "CUIT from Config"
            mock_config.STORE_IVA_CONDITION = "IVA Condition from Config"
            mock_config.STORE_PHONE = "Phone from Config"
            
            # Configure the mock builder instance
            mock_builder_instance = mock_builder_class.return_value
            mock_builder_instance.generate_invoice_pdf.return_value = True
            
            # Call the service method with no explicit store_info
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_filename = temp_file.name
                
            try:
                result = self.service.generate_invoice_pdf(
                    invoice_id=1,
                    filename=temp_filename
                )
                
                # Verify calls
                self.invoice_repo.get_by_id.assert_called_once_with(1)
                self.sale_repo.get_by_id.assert_called_once_with(2)
                
                # Verify InvoiceBuilder was initialized with config store info
                mock_builder_class.assert_called_once()
                expected_store_info = {
                    'name': "Store Name from Config",
                    'address': "Address from Config",
                    'cuit': "CUIT from Config",
                    'iva_condition': "IVA Condition from Config",
                    'phone': "Phone from Config"
                }
                self.assertEqual(mock_builder_class.call_args[0][0], expected_store_info)
                
                # Verify generate_invoice_pdf was called with correct data
                mock_builder_instance.generate_invoice_pdf.assert_called_once()
                call_args = mock_builder_instance.generate_invoice_pdf.call_args[1]
                
                # Check invoice data
                invoice_data = call_args['invoice_data']
                self.assertEqual(invoice_data['invoice_number'], "0001-00000001")
                self.assertEqual(invoice_data['invoice_type'], "B")
                
                # Check sale items
                sale_items = call_args['sale_items']
                self.assertEqual(len(sale_items), 2)
                self.assertEqual(sale_items[0]['code'], "P001")
                self.assertEqual(sale_items[1]['code'], "P002")
                
                # Check filename
                self.assertEqual(call_args['filename'], temp_filename)
                
                # Check result
                self.assertEqual(result, temp_filename)
                
                # Test with custom store_info provided (should override Config)
                mock_builder_class.reset_mock()
                custom_store_info = {"name": "Custom Store"}
                
                result = self.service.generate_invoice_pdf(
                    invoice_id=1,
                    filename=temp_filename,
                    store_info=custom_store_info
                )
                
                # Verify custom store_info was used instead of Config
                mock_builder_class.assert_called_once()
                self.assertEqual(mock_builder_class.call_args[0][0], custom_store_info)
                
            finally:
                # Clean up
                if os.path.exists(temp_filename):
                    os.unlink(temp_filename)
    
    def test_generate_invoice_pdf_error_handling(self):
        """Test error handling when generating PDF."""
        # Set up mocks
        self.invoice_repo.get_by_id.return_value = None  # Invoice not found
        
        # Expect ValueError for non-existent invoice
        with self.assertRaises(ValueError) as context:
            self.service.generate_invoice_pdf(invoice_id=999)
            
        self.assertIn("not found", str(context.exception))

if __name__ == "__main__":
    unittest.main()