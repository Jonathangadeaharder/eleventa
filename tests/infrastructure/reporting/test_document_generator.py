# tests/infrastructure/reporting/test_document_generator.py
"""
Tests for PDF document generation functionality.
"""
import pytest
import os
import tempfile
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from infrastructure.reporting.document_generator import DocumentPdfGenerator


class TestDocumentPdfGenerator:
    """Tests for DocumentPdfGenerator class."""
    
    @pytest.fixture
    def store_info(self):
        """Sample store information for testing."""
        return {
            "name": "Test Store",
            "address": "123 Test St, Test City",
            "phone": "555-0123",
            "cuit": "30-12345678-9",
            "iva_condition": "Responsable Inscripto",
            "logo_path": None
        }
    
    @pytest.fixture
    def generator(self, store_info):
        """DocumentPdfGenerator instance for testing."""
        return DocumentPdfGenerator(store_info)
    
    @pytest.fixture
    def sample_invoice_data(self):
        """Sample invoice data for testing."""
        return {
            "invoice_number": "A-0001-00000123",
            "invoice_date": datetime(2024, 1, 15),
            "customer": {
                "name": "Test Customer",
                "address": "456 Customer St",
                "cuit": "20-87654321-0",
                "iva_condition": "Consumidor Final"
            },
            "items": [
                {
                    "description": "Product 1",
                    "quantity": Decimal('2'),
                    "unit_price": Decimal('100.00'),
                    "total": Decimal('200.00')
                },
                {
                    "description": "Product 2",
                    "quantity": Decimal('1'),
                    "unit_price": Decimal('50.00'),
                    "total": Decimal('50.00')
                }
            ],
            "subtotal": Decimal('250.00'),
            "tax_amount": Decimal('52.50'),
            "total": Decimal('302.50')
        }
    
    def test_init_with_store_info(self, store_info):
        """Test initialization with provided store info."""
        generator = DocumentPdfGenerator(store_info)
        assert generator.store_info == store_info
        assert hasattr(generator, 'styles')
    
    @patch('infrastructure.reporting.document_generator.Config')
    def test_init_without_store_info(self, mock_config):
        """Test initialization without store info uses Config defaults."""
        mock_config.STORE_NAME = "Default Store"
        mock_config.STORE_ADDRESS = "Default Address"
        mock_config.STORE_PHONE = "555-0000"
        mock_config.STORE_CUIT = "30-00000000-0"
        mock_config.STORE_IVA_CONDITION = "Responsable Inscripto"
        mock_config.STORE_LOGO_PATH = None
        
        generator = DocumentPdfGenerator()
        
        assert generator.store_info["name"] == "Default Store"
        assert generator.store_info["address"] == "Default Address"
        assert generator.store_info["phone"] == "555-0000"
        assert generator.store_info["cuit"] == "30-00000000-0"
        assert generator.store_info["iva_condition"] == "Responsable Inscripto"
        assert generator.store_info["logo_path"] is None
    
    @patch('infrastructure.reporting.document_generator.Config')
    def test_init_with_none_config_values(self, mock_config):
        """Test initialization when Config values are None."""
        mock_config.STORE_NAME = None
        mock_config.STORE_ADDRESS = None
        mock_config.STORE_PHONE = None
        mock_config.STORE_CUIT = None
        mock_config.STORE_IVA_CONDITION = None
        mock_config.STORE_LOGO_PATH = None
        
        generator = DocumentPdfGenerator()
        
        assert generator.store_info["name"] == "Eleventa Demo Store"
        assert generator.store_info["address"] == "123 Main St, Buenos Aires, Argentina"
        assert generator.store_info["phone"] == "555-1234"
        assert generator.store_info["cuit"] == "30-12345678-9"
        assert generator.store_info["iva_condition"] == "Responsable Inscripto"
        assert generator.store_info["logo_path"] is None
    
    def test_generate_invoice_creates_file(self, generator, sample_invoice_data):
        """Test that generate_invoice_pdf creates a PDF file."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            # Generate the invoice
            result = generator.generate_invoice_pdf(sample_invoice_data, sample_invoice_data["items"], output_path)
            
            # Verify file was created
            assert result is True
            assert os.path.exists(output_path)
            
            # Verify file has content
            assert os.path.getsize(output_path) > 0
            
        finally:
            # Clean up
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_generate_receipt_creates_file(self, generator):
        """Test that generate_receipt creates a PDF file."""
        receipt_data = {
            "receipt_number": "R-001",
            "date": datetime(2024, 1, 15),
            "customer_name": "Test Customer",
            "items": [
                {
                    "description": "Product 1",
                    "quantity": Decimal('1'),
                    "price": Decimal('100.00')
                }
            ],
            "total": Decimal('100.00'),
            "payment_method": "Efectivo"
        }
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            # Generate the receipt
            result = generator.generate_receipt(receipt_data, output_path)
            
            # Verify file was created
            assert result is True
            assert os.path.exists(output_path)
            
            # Verify file has content
            assert os.path.getsize(output_path) > 0
            
        finally:
            # Clean up
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_generate_presupuesto_creates_file(self, generator):
        """Test that generate_presupuesto creates a PDF file."""
        presupuesto_data = {
            "presupuesto_id": "P-001",
            "customer_name": "Test Customer",
            "user_name": "Test User",
            "items": [
                {
                    "description": "Product 1",
                    "quantity": Decimal('1'),
                    "unit_price": Decimal('100.00'),
                    "total": Decimal('100.00')
                }
            ],
            "total": Decimal('100.00')
        }
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            # Generate the presupuesto
            result = generator.generate_presupuesto(presupuesto_data["items"], 
                                                   presupuesto_data["total"],
                                                   output_path, 
                                                   presupuesto_data["customer_name"],
                                                   presupuesto_data["user_name"], 
                                                   presupuesto_data["presupuesto_id"])
            
            # Verify file was created
            assert result is True
            assert os.path.exists(output_path)
            
            # Verify file has content
            assert os.path.getsize(output_path) > 0
            
        finally:
            # Clean up
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_format_currency_receipt(self, generator):
        """Test currency formatting for receipts."""
        # Test with decimal
        result = generator._format_currency_receipt(Decimal('1234.56'))
        assert '$' in result
        assert '1,234.56' in result  # US format with comma separator
        
        # Test with zero
        result = generator._format_currency_receipt(Decimal('0.00'))
        assert '$' in result
        assert '0' in result
        
        # Test with large number
        result = generator._format_currency_receipt(Decimal('999999.99'))
        assert '$' in result
    
    def test_format_sale_date_receipt(self, generator):
        """Test date formatting for receipts."""
        test_date = datetime(2024, 1, 15, 14, 30, 0)
        result = generator._format_sale_date_receipt(test_date)
        
        # Should contain date components
        assert '2024' in result or '24' in result
        assert '01' in result or '1' in result
        assert '15' in result
    
    @patch('infrastructure.reporting.document_generator.SimpleDocTemplate')
    def test_generate_invoice_handles_errors(self, mock_doc, generator, sample_invoice_data):
        """Test that generate_invoice_pdf handles errors gracefully."""
        # Mock SimpleDocTemplate to raise an exception
        mock_doc.side_effect = Exception("PDF generation failed")
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            # Should return False on error
            result = generator.generate_invoice_pdf(sample_invoice_data, sample_invoice_data["items"], output_path)
            assert result is False
        finally:
            # Clean up
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_invalid_output_path(self, generator, sample_invoice_data):
        """Test handling of invalid output path."""
        # Use a path with invalid characters that will definitely fail on Windows
        invalid_path = "C:\\invalid\\path\\with<invalid>chars\\file.pdf"
        
        # Should return False on error
        result = generator.generate_invoice_pdf(sample_invoice_data, sample_invoice_data["items"], invalid_path)
        assert result is False
    
    def test_empty_invoice_data(self, generator):
        """Test handling of empty invoice data."""
        empty_data = {}
        empty_items = []
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            # Should return False on error
            result = generator.generate_invoice_pdf(empty_data, empty_items, output_path)
            assert result is False
        finally:
            # Clean up
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_missing_required_invoice_fields(self, generator):
        """Test handling of missing required fields in invoice data."""
        incomplete_data = {
            "invoice_number": "A-0001-00000123"
            # Missing other required fields
        }
        incomplete_items = []
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            # Should return False on error
            result = generator.generate_invoice_pdf(incomplete_data, incomplete_items, output_path)
            assert result is False
        finally:
            # Clean up
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    @patch('infrastructure.reporting.document_generator.locale')
    def test_locale_handling(self, mock_locale, store_info):
        """Test locale configuration handling."""
        # Test when locale setting fails
        mock_locale.setlocale.side_effect = [Exception("Locale not available"), None]
        
        # Should not raise exception, should fall back to default
        generator = DocumentPdfGenerator(store_info)
        assert generator is not None
    
    def test_logger_initialization(self, generator):
        """Test that logger is properly initialized."""
        assert hasattr(generator, 'logger')
        assert generator.logger.name == 'DocumentPdfGenerator'