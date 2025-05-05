"""
Tests for the GenerateInvoiceDialog UI component.
Focus: Sale search, validation, and invoice generation.

This test suite verifies the functionality of the GenerateInvoiceDialog component, including:
- Dialog initialization and UI elements
- Sale search functionality
- Validation of sale conditions for invoice generation
- Invoice generation process
- Dialog acceptance and rejection
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QDialog, QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

from ui.dialogs.generate_invoice_dialog import GenerateInvoiceDialog
from core.models.sale import Sale, SaleItem
from core.models.customer import Customer
from core.models.invoice import Invoice

# Create QApplication instance once for all tests
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app
    app.quit()

# Test fixtures
@pytest.fixture
def mock_invoicing_service():
    """Create a mock invoicing service with necessary repositories and methods."""
    mock_service = MagicMock()
    
    # Mock sale repository
    mock_sale_repo = MagicMock()
    mock_service.sale_repo = mock_sale_repo
    
    # Mock customer repository
    mock_customer_repo = MagicMock()
    mock_service.customer_repo = mock_customer_repo
    
    # Mock invoice methods
    mock_service.get_invoice_by_sale_id = MagicMock(return_value=None)
    mock_service.create_invoice_from_sale = MagicMock()
    
    return mock_service

@pytest.fixture
def mock_sale():
    """Create a mock sale with items and customer ID."""
    # Use a fixed date for reproducible tests
    sale_date = datetime(2023, 5, 10)
    
    # Mock the sale object
    mock_sale = MagicMock(spec=Sale)
    mock_sale.id = 1
    mock_sale.date = sale_date  # We'll use date instead of timestamp for tests
    mock_sale.timestamp = sale_date  # Add both properties for flexibility
    mock_sale.customer_id = 1
    mock_sale.total = Decimal('100.00')
    
    # Create mock sale items
    item1 = MagicMock(spec=SaleItem)
    item1.id = 1
    item1.sale_id = 1
    item1.product_id = 1
    item1.product_code = "P001"
    item1.product_name = "Product 1"  # This is used by the UI
    item1.product_description = "Product 1"  # This is the actual model property
    item1.quantity = Decimal('2')
    item1.unit_price = Decimal('10.00')
    item1.subtotal = Decimal('20.00')
    
    item2 = MagicMock(spec=SaleItem)
    item2.id = 2
    item2.sale_id = 1
    item2.product_id = 2
    item2.product_code = "P002"
    item2.product_name = "Product 2"
    item2.product_description = "Product 2"
    item2.quantity = Decimal('1')
    item2.unit_price = Decimal('80.00')
    item2.subtotal = Decimal('80.00')
    
    # Set up the items list
    mock_sale.items = [item1, item2]
    
    return mock_sale

@pytest.fixture
def mock_customer():
    """Create a mock customer."""
    mock_customer = MagicMock(spec=Customer)
    mock_customer.id = 1
    mock_customer.name = "John Doe"
    mock_customer.email = "john@example.com"
    mock_customer.phone = "555-1234"
    mock_customer.address = "123 Test St"
    mock_customer.tax_id = "TAX12345"
    return mock_customer

@pytest.fixture
def invoice_dialog(qtbot, mock_invoicing_service, qapp):
    """Create a GenerateInvoiceDialog instance for testing."""
    dialog = GenerateInvoiceDialog(mock_invoicing_service)
    qtbot.addWidget(dialog)
    return dialog

# Tests
def test_dialog_initialization(invoice_dialog):
    """Test that the dialog initializes with the correct title and UI elements."""
    assert invoice_dialog.windowTitle() == "Generar Factura"
    assert invoice_dialog.minimumSize().width() >= 500
    assert invoice_dialog.minimumSize().height() >= 400
    
    # Check UI components
    assert invoice_dialog.sale_id_edit is not None
    assert invoice_dialog.search_button is not None
    assert invoice_dialog.sale_items_table is not None
    assert invoice_dialog.sale_items_model is not None
    assert invoice_dialog.generate_button is not None
    assert invoice_dialog.cancel_button is not None
    
    # Verify initial state
    assert invoice_dialog.generate_button.isEnabled() is False

@patch('ui.dialogs.generate_invoice_dialog.show_error_message')
def test_search_sale_empty_id(mock_error_message, invoice_dialog):
    """Test searching for a sale with an empty sale ID."""
    # Set empty sale ID
    invoice_dialog.sale_id_edit.setText("")
    
    # Trigger search button click using QTest
    QTest.mouseClick(invoice_dialog.search_button, Qt.LeftButton)
    
    # Verify error message
    mock_error_message.assert_called_once_with("Por favor ingrese un ID de venta.")
    assert invoice_dialog.generate_button.isEnabled() is False

@patch('ui.dialogs.generate_invoice_dialog.show_error_message')
def test_search_sale_invalid_id(mock_error_message, invoice_dialog):
    """Test searching for a sale with an invalid sale ID."""
    # Set invalid sale ID (non-numeric)
    invoice_dialog.sale_id_edit.setText("abc")
    
    # Trigger search button click using QTest
    QTest.mouseClick(invoice_dialog.search_button, Qt.LeftButton)
    
    # Verify error message
    mock_error_message.assert_called_once_with("Por favor ingrese un ID de venta válido (número entero).")
    assert invoice_dialog.generate_button.isEnabled() is False

def test_search_sale_not_found(invoice_dialog, mock_invoicing_service):
    """Test searching for a non-existent sale."""
    # Configure mock service to return None for the sale
    mock_invoicing_service.sale_repo.get_by_id.return_value = None
    
    # Set sale ID
    invoice_dialog.sale_id_edit.setText("999")
    
    # Use patch to capture error message
    with patch('ui.dialogs.generate_invoice_dialog.show_error_message') as mock_error:
        # Trigger search button click using QTest
        QTest.mouseClick(invoice_dialog.search_button, Qt.LeftButton)
        
        # Verify service was called and error message shown
        mock_invoicing_service.sale_repo.get_by_id.assert_called_once_with(999)
        mock_error.assert_called_once_with("No se encontró una venta con ID: 999")
        assert invoice_dialog.generate_button.isEnabled() is False

def test_search_sale_with_existing_invoice(invoice_dialog, mock_invoicing_service, mock_sale):
    """Test searching for a sale that already has an invoice."""
    # Configure mocks
    mock_invoicing_service.sale_repo.get_by_id.return_value = mock_sale
    
    # Create a mock existing invoice
    mock_invoice = MagicMock()
    mock_invoice.invoice_number = "INV-2023-001"
    mock_invoicing_service.get_invoice_by_sale_id.return_value = mock_invoice
    
    # Set sale ID
    invoice_dialog.sale_id_edit.setText("1")
    
    # Use patch to capture error message
    with patch('ui.dialogs.generate_invoice_dialog.show_error_message') as mock_error:
        # Trigger search button click using QTest
        QTest.mouseClick(invoice_dialog.search_button, Qt.LeftButton)
        
        # Verify service calls and error message
        mock_invoicing_service.sale_repo.get_by_id.assert_called_once_with(1)
        mock_invoicing_service.get_invoice_by_sale_id.assert_called_once_with(1)
        mock_error.assert_called_once()
        assert "ya tiene una factura asociada" in mock_error.call_args[0][0]
        assert invoice_dialog.generate_button.isEnabled() is False

def test_search_sale_without_customer(invoice_dialog, mock_invoicing_service, mock_sale):
    """Test searching for a sale without associated customer."""
    # Configure mocks
    mock_sale.customer_id = None  # Sale without customer
    mock_invoicing_service.sale_repo.get_by_id.return_value = mock_sale
    mock_invoicing_service.get_invoice_by_sale_id.return_value = None
    
    # Set sale ID
    invoice_dialog.sale_id_edit.setText("1")
    
    # Use patch to capture error message
    with patch('ui.dialogs.generate_invoice_dialog.show_error_message') as mock_error:
        # Trigger search button click using QTest
        QTest.mouseClick(invoice_dialog.search_button, Qt.LeftButton)
        
        # Verify service calls and error message
        mock_invoicing_service.sale_repo.get_by_id.assert_called_once_with(1)
        mock_invoicing_service.get_invoice_by_sale_id.assert_called_once_with(1)
        mock_error.assert_called_once()
        assert "no tiene un cliente asociado" in mock_error.call_args[0][0]
        assert invoice_dialog.generate_button.isEnabled() is False

def test_search_valid_sale(invoice_dialog, mock_invoicing_service, mock_sale, mock_customer):
    """Test searching for a valid sale with customer."""
    # Configure mocks
    mock_invoicing_service.sale_repo.get_by_id.return_value = mock_sale
    mock_invoicing_service.get_invoice_by_sale_id.return_value = None
    mock_invoicing_service.customer_repo.get_by_id.return_value = mock_customer
    
    # Set sale ID
    invoice_dialog.sale_id_edit.setText("1")
    
    # Trigger search button click using QTest
    QTest.mouseClick(invoice_dialog.search_button, Qt.LeftButton)
    
    # Verify service calls
    mock_invoicing_service.sale_repo.get_by_id.assert_called_once_with(1)
    mock_invoicing_service.get_invoice_by_sale_id.assert_called_once_with(1)
    mock_invoicing_service.customer_repo.get_by_id.assert_called_once_with(1)
    
    # Verify UI updates
    assert invoice_dialog.customer_label.text() == "Cliente: John Doe"
    assert invoice_dialog.sale_date_label.text() == "Fecha: 10/05/2023"
    assert invoice_dialog.sale_total_label.text() == "Total: $100.00"
    assert invoice_dialog.sale_items_model.rowCount() == 2
    assert invoice_dialog.generate_button.isEnabled() is True

def test_generate_invoice_success(invoice_dialog, mock_invoicing_service, mock_sale, mock_customer):
    """Test successful invoice generation."""
    # Configure mocks
    mock_invoicing_service.sale_repo.get_by_id.return_value = mock_sale
    mock_invoicing_service.get_invoice_by_sale_id.return_value = None
    mock_invoicing_service.customer_repo.get_by_id.return_value = mock_customer
    
    # Mock successful invoice creation
    mock_invoice = MagicMock(spec=Invoice)
    mock_invoice.invoice_number = "INV-2023-001"
    mock_invoicing_service.create_invoice_from_sale.return_value = mock_invoice
    
    # Set sale ID and load sale data
    invoice_dialog.sale_id_edit.setText("1")
    QTest.mouseClick(invoice_dialog.search_button, Qt.LeftButton)
    
    # Generate invoice
    with patch('ui.dialogs.generate_invoice_dialog.show_info_message') as mock_info:
        QTest.mouseClick(invoice_dialog.generate_button, Qt.LeftButton)
        
        # Verify invoice created and success message
        mock_invoicing_service.create_invoice_from_sale.assert_called_once_with(1)
        mock_info.assert_called_once()
        assert "generada correctamente" in mock_info.call_args[0][2]
        assert "INV-2023-001" in mock_info.call_args[0][2]

@patch('ui.dialogs.generate_invoice_dialog.show_error_message')
def test_generate_invoice_exception(mock_error, invoice_dialog, mock_invoicing_service, mock_sale, mock_customer):
    """Test handling of exceptions during invoice generation."""
    # Configure mocks
    mock_invoicing_service.sale_repo.get_by_id.return_value = mock_sale
    mock_invoicing_service.get_invoice_by_sale_id.return_value = None
    mock_invoicing_service.customer_repo.get_by_id.return_value = mock_customer
    
    # Mock exception during invoice creation
    error_message = "Error de conexión con el servicio SAT"
    mock_invoicing_service.create_invoice_from_sale.side_effect = Exception(error_message)
    
    # Set sale ID and load sale data
    invoice_dialog.sale_id_edit.setText("1")
    QTest.mouseClick(invoice_dialog.search_button, Qt.LeftButton)
    
    # Try to generate invoice
    QTest.mouseClick(invoice_dialog.generate_button, Qt.LeftButton)
    
    # Verify error message
    mock_invoicing_service.create_invoice_from_sale.assert_called_once_with(1)
    mock_error.assert_called_once()
    assert error_message in mock_error.call_args[0][2]

def test_cancel_dialog(invoice_dialog):
    """Test canceling the dialog."""
    # Set up to spy on the reject signal
    with patch.object(invoice_dialog, 'reject') as mock_reject:
        # Click cancel button
        QTest.mouseClick(invoice_dialog.cancel_button, Qt.LeftButton)
        
        # Verify dialog rejected
        mock_reject.assert_called_once()
