import unittest
import os
import tempfile
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

from infrastructure.reporting.invoice_builder import InvoiceBuilder

class TestInvoiceBuilder(unittest.TestCase):
    """Tests for the InvoiceBuilder class."""
    
    def setUp(self):
        """Set up common test data."""
        # Test store info
        self.store_info = {
            'name': 'Test Company',
            'address': 'Av. Test 123, Buenos Aires, Argentina',
            'cuit': '30-12345678-9',
            'iva_condition': 'Responsable Inscripto'
        }
        
        # Test invoice data
        self.invoice_data = {
            'id': 1,
            'invoice_number': '0001-00000001',
            'invoice_date': datetime(2025, 4, 13, 10, 30, 0),
            'invoice_type': 'B',
            'customer_details': {
                'name': 'Test Customer',
                'address': 'Customer Address 123',
                'cuit': '20-98765432-1',
                'iva_condition': 'Consumidor Final',
                'email': 'customer@example.com',
                'phone': '123456789'
            },
            'subtotal': Decimal('100.00'),
            'iva_amount': Decimal('21.00'),
            'total': Decimal('121.00'),
            'iva_condition': 'Consumidor Final',
            'cae': '12345678901234',
            'cae_due_date': datetime(2025, 5, 13),
            'is_active': True
        }
        
        # Test sale items
        self.sale_items = [
            {
                'code': 'P001',
                'description': 'Test Product 1',
                'quantity': Decimal('2'),
                'unit_price': Decimal('30.00'),
                'subtotal': Decimal('60.00')
            },
            {
                'code': 'P002',
                'description': 'Test Product 2',
                'quantity': Decimal('1'),
                'unit_price': Decimal('40.00'),
                'subtotal': Decimal('40.00')
            },
            {
                'code': 'P003',
                'description': 'Test Product 3',
                'quantity': Decimal('1'),
                'unit_price': Decimal('21.00'),
                'subtotal': Decimal('21.00')
            }
        ]
        
        # Create the invoice builder
        self.builder = InvoiceBuilder(self.store_info)
    
    def test_generate_invoice_pdf_success(self):
        """Test successful generation of a PDF invoice."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_filename = temp_file.name
        
        try:
            # Generate the PDF
            result = self.builder.generate_invoice_pdf(
                invoice_data=self.invoice_data,
                sale_items=self.sale_items,
                filename=temp_filename
            )
            
            # Assert
            self.assertTrue(result)
            self.assertTrue(os.path.exists(temp_filename))
            self.assertTrue(os.path.getsize(temp_filename) > 0)  # File should not be empty
        finally:
            # Clean up
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
    
    def test_generate_invoice_pdf_type_a(self):
        """Test generation of a Type A invoice (with separate IVA)."""
        # Update invoice data to Type A
        invoice_data = self.invoice_data.copy()
        invoice_data['invoice_type'] = 'A'
        invoice_data['customer_details'] = {**self.invoice_data['customer_details'], 'iva_condition': 'Responsable Inscripto'}
        invoice_data['iva_condition'] = 'Responsable Inscripto'
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_filename = temp_file.name
        
        try:
            # Generate the PDF
            result = self.builder.generate_invoice_pdf(
                invoice_data=invoice_data,
                sale_items=self.sale_items,
                filename=temp_filename
            )
            
            # Assert
            self.assertTrue(result)
            self.assertTrue(os.path.exists(temp_filename))
            self.assertTrue(os.path.getsize(temp_filename) > 0)
        finally:
            # Clean up
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
    
    def test_generate_invoice_pdf_without_cae(self):
        """Test generation of an invoice without CAE data."""
        # Remove CAE data
        invoice_data = self.invoice_data.copy()
        invoice_data['cae'] = None
        invoice_data['cae_due_date'] = None
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_filename = temp_file.name
        
        try:
            # Generate the PDF
            result = self.builder.generate_invoice_pdf(
                invoice_data=invoice_data,
                sale_items=self.sale_items,
                filename=temp_filename
            )
            
            # Assert
            self.assertTrue(result)
            self.assertTrue(os.path.exists(temp_filename))
        finally:
            # Clean up
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
    
    @patch('reportlab.platypus.SimpleDocTemplate.build')
    def test_invoice_pdf_content(self, mock_build):
        """Test that PDF content contains the expected elements."""
        # This test verifies that the correct elements are being added to the PDF
        # Without actually generating a PDF file (mocking the build process)
        
        # Generate a PDF (build will be mocked)
        self.builder.generate_invoice_pdf(
            invoice_data=self.invoice_data,
            sale_items=self.sale_items,
            filename='test.pdf'
        )
        
        # Verify the build was called
        self.assertTrue(mock_build.called)
        
        # Get the elements passed to build
        elements = mock_build.call_args[0][0]
        
        # Basic structure checks (should have elements for all sections)
        self.assertTrue(len(elements) > 0)
        
        # Convert elements to string representation to check for key content
        elements_str = str(elements)
        
        # Check for key invoice information
        self.assertIn('Test Company', elements_str)  # Store name
        self.assertIn('FACTURA B', elements_str)     # Invoice type
        self.assertIn('0001-00000001', elements_str) # Invoice number
        self.assertIn('Test Customer', elements_str) # Customer name
        self.assertIn('20-98765432-1', elements_str) # Customer CUIT
        
        # Check for sale items
        self.assertIn('Test Product 1', elements_str)
        self.assertIn('P001', elements_str)  # Product code

    def test_generate_invoice_pdf_multi_page(self):
        """Test PDF generation with a very large item list (multi-page)."""
        # Create a large list of sale items to force multiple pages
        large_sale_items = []
        for i in range(100):
            large_sale_items.append({
                'code': f'P{i:03}',
                'description': f'Product {i}',
                'quantity': Decimal('1'),
                'unit_price': Decimal('10.00'),
                'subtotal': Decimal('10.00')
            })
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_filename = temp_file.name
        try:
            result = self.builder.generate_invoice_pdf(
                invoice_data=self.invoice_data,
                sale_items=large_sale_items,
                filename=temp_filename
            )
            self.assertTrue(result)
            self.assertTrue(os.path.exists(temp_filename))
            self.assertTrue(os.path.getsize(temp_filename) > 0)
        finally:
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    def test_generate_invoice_pdf_custom_store_and_unusual_customer(self):
        """Test PDF generation with custom store info and missing customer fields."""
        # Custom store info
        custom_store_info = {
            'name': '¡Tienda Ñandú & Co.!',
            'address': 'Calle Falsa 123, Córdoba',
            'cuit': '30-00000000-0',
            'iva_condition': 'Monotributo'
        }
        # Customer with missing fields
        unusual_customer = {
            'name': 'Cliente Raro',
            # 'address' omitted
            # 'cuit' omitted
            'iva_condition': 'Exento'
            # 'email' and 'phone' omitted
        }
        invoice_data = self.invoice_data.copy()
        invoice_data['customer_details'] = unusual_customer
        builder = InvoiceBuilder(custom_store_info)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_filename = temp_file.name
        try:
            result = builder.generate_invoice_pdf(
                invoice_data=invoice_data,
                sale_items=self.sale_items,
                filename=temp_filename
            )
            self.assertTrue(result)
            self.assertTrue(os.path.exists(temp_filename))
            self.assertTrue(os.path.getsize(temp_filename) > 0)
        finally:
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    def test_error_handling(self):
        """Test error handling during PDF generation."""
        # Create a situation that would cause an error
        with patch('reportlab.platypus.SimpleDocTemplate.build', side_effect=Exception("Test error")):
            result = self.builder.generate_invoice_pdf(
                invoice_data=self.invoice_data,
                sale_items=self.sale_items,
                filename='test.pdf'
            )
            
            # Should return False on error
            self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()