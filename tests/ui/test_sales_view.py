import pytest
from unittest.mock import MagicMock, patch

import sys

import types

import builtins

# Assume PyQt5 or PySide2 is used; adjust imports as needed
try:
    from PyQt5.QtWidgets import QMessageBox
except ImportError:
    QMessageBox = None

# Import the SalesView class
import importlib.util
import os

# Dynamically import SalesView from ui/views/sales_view.py
spec = importlib.util.spec_from_file_location(
    "sales_view", os.path.join(os.path.dirname(__file__), "../../ui/views/sales_view.py")
)
sales_view_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sales_view_module)
SalesView = getattr(sales_view_module, "SalesView", None)

@pytest.fixture
def mock_sale_service():
    service = MagicMock()
    return service

@pytest.fixture
def mock_product_service():
    service = MagicMock()
    return service

@pytest.fixture
def mock_customer_service():
    service = MagicMock()
    return service

@pytest.fixture
def mock_current_user():
    user = MagicMock()
    user.id = 1
    return user

@pytest.fixture
def sales_view(qtbot, mock_sale_service, mock_product_service, mock_customer_service, mock_current_user, monkeypatch):
    # Create a SalesView instance with mocked dependencies
    view = SalesView(
        product_service=mock_product_service,
        sale_service=mock_sale_service,
        customer_service=mock_customer_service,
        current_user=mock_current_user
    )
    # Mock other dependencies as needed
    view.show_info_message = MagicMock()
    view.show_error_message = MagicMock()
    view._get_items_data = MagicMock(return_value=[{"id": 1, "qty": 2}])
    view._get_selected_customer = MagicMock(return_value=None)
    view._get_payment_type = MagicMock(return_value="cash")
    view._clear_sale = MagicMock()
    view.ask_confirmation = MagicMock(return_value=True)
    view._has_items = MagicMock(return_value=True)
    
    # Mock sale_item_model
    view.sale_item_model = MagicMock()
    view.sale_item_model.get_all_items = MagicMock(return_value=[
        MagicMock(product_id=1, quantity=2, unit_price=10.0)
    ])
    
    # Mock _get_selected_customer_id
    view._get_selected_customer_id = MagicMock(return_value=None)
    
    # Mock _current_total
    view._current_total = 20.0
    
    # Mock customer_combo
    view.customer_combo = MagicMock()
    view.customer_combo.currentText.return_value = "Test Customer"
    
    # Mock invoice_button
    view.invoice_button = MagicMock()
    
    return view

def test_finalize_sale_success(qtbot, mock_sale_service, mock_product_service, mock_customer_service, mock_current_user, mocker):
    """Test that finalize_current_sale successfully creates a sale when all conditions are met."""
    
    # 1. Create mocks for dependent components
    PaymentDialogMock = mocker.patch('ui.views.sales_view.PaymentDialog')
    dialog_instance = mocker.MagicMock()
    dialog_instance.exec.return_value = True
    dialog_instance.selected_payment_method = "Efectivo"
    PaymentDialogMock.return_value = dialog_instance
    
    mocker.patch('ui.views.sales_view.ask_confirmation', return_value=True)
    mocker.patch('ui.views.sales_view.show_info_message')
    
    # 2. Create a successful sale return object
    sale_mock = mocker.MagicMock()
    sale_mock.id = 123
    mock_sale_service.create_sale.return_value = sale_mock
    
    # 3. Create SalesView instance with our mocks
    from ui.views.sales_view import SalesView
    view = SalesView(
        product_service=mock_product_service,
        sale_service=mock_sale_service,
        customer_service=mock_customer_service,
        current_user=mock_current_user
    )
    
    # 4. Mock the components we need for testing
    view._current_total = 100.0
    view.invoice_button = mocker.MagicMock()
    view._clear_sale = mocker.MagicMock()
    
    # Mock sale items
    item_mock = mocker.MagicMock()
    item_mock.product_id = 1
    item_mock.quantity = 2
    view.sale_item_model = mocker.MagicMock()
    view.sale_item_model.get_all_items.return_value = [item_mock]
    
    # Mock customer combo
    view.customer_combo = mocker.MagicMock()
    
    # 5. Call the method to test
    view.finalize_current_sale()
    
    # 6. Assertions
    # Check if create_sale was called with the right parameters
    mock_sale_service.create_sale.assert_called_once()
    
    # Check if the sale was cleared
    assert view._clear_sale.called

def test_finalize_sale_error_handling(qtbot, mock_sale_service, mock_product_service, mock_customer_service, mock_current_user, mocker):
    """Test exception handling for finalize_current_sale."""
    
    # Create mocks for dependent components
    PaymentDialogMock = mocker.patch('ui.views.sales_view.PaymentDialog')
    dialog_instance = mocker.MagicMock()
    dialog_instance.exec.return_value = True
    dialog_instance.selected_payment_method = "Efectivo"
    PaymentDialogMock.return_value = dialog_instance
    
    error_message_mock = mocker.MagicMock()
    mocker.patch('ui.views.sales_view.show_error_message', error_message_mock)
    mocker.patch('ui.views.sales_view.ask_confirmation', return_value=True)
    
    # Create a SalesView with our mocks
    from ui.views.sales_view import SalesView
    view = SalesView(
        product_service=mock_product_service,
        sale_service=mock_sale_service,
        customer_service=mock_customer_service,
        current_user=mock_current_user
    )
    
    # Setup test mocks
    view._current_total = 100.0
    view._clear_sale = mocker.MagicMock()
    
    # Mock customer components
    view.customer_combo = mocker.MagicMock()
    view.customer_combo.currentData = mocker.MagicMock(return_value=None)
    view.customer_combo.currentText = mocker.MagicMock(return_value="")
    
    # Mock item model
    item_mock = mocker.MagicMock()
    item_mock.product_id = 1
    item_mock.quantity = 2
    view.sale_item_model = mocker.MagicMock()
    view.sale_item_model.get_all_items.return_value = [item_mock]
    
    # Simulate service raising an exception
    mock_sale_service.create_sale.side_effect = Exception("Service error")
    
    # Execute the method
    view.finalize_current_sale()
    
    # Should show error message
    assert error_message_mock.called
    
    # Should not clear sale since there was an error
    assert not view._clear_sale.called

def test_payment_dialog_credit_option_enabled(qtbot, mock_sale_service, mock_product_service, mock_customer_service, mock_current_user, mocker):
    """Test that the PaymentDialog enables credit option when a customer is selected."""
    
    # Set up SalesView class with mocks
    from ui.views.sales_view import SalesView
    view = SalesView(
        product_service=mock_product_service,
        sale_service=mock_sale_service,
        customer_service=mock_customer_service,
        current_user=mock_current_user
    )
    
    # Create sale mock object
    sale_mock = mocker.MagicMock()
    sale_mock.id = 123
    mock_sale_service.create_sale.return_value = sale_mock
    
    # Set up view
    view._current_total = 100.0
    view.invoice_button = mocker.MagicMock()
    view._clear_sale = mocker.MagicMock()
    view.customer_combo = mocker.MagicMock()
    view.customer_combo.currentText.return_value = "Test Customer"
    view.customer_combo.currentData = mocker.MagicMock(return_value=42)
    
    # Mock items
    item_mock = mocker.MagicMock()
    item_mock.product_id = 1
    item_mock.quantity = 2
    view.sale_item_model = mocker.MagicMock()
    view.sale_item_model.get_all_items.return_value = [item_mock]
    
    # Mock PaymentDialog
    dialog_instance = mocker.MagicMock()
    dialog_instance.exec.return_value = True
    dialog_instance.selected_payment_method = "Crédito"
    payment_dialog_mock = mocker.patch('ui.views.sales_view.PaymentDialog', return_value=dialog_instance)
    
    # Mock other functions
    mocker.patch('ui.views.sales_view.ask_confirmation', return_value=True)
    mocker.patch('ui.views.sales_view.show_info_message')
    
    # Call the method
    view.finalize_current_sale()
    
    # Assert PaymentDialog was called with allow_credit=True
    assert payment_dialog_mock.called
    # Check positional arguments instead of keyword arguments
    args, kwargs = payment_dialog_mock.call_args
    if kwargs and 'allow_credit' in kwargs:
        assert kwargs['allow_credit'] is True
    else:
        # The second argument to PaymentDialog is allow_credit
        assert len(args) >= 2
        assert args[1] is True

def test_payment_dialog_credit_option_disabled(qtbot, mock_sale_service, mock_product_service, mock_customer_service, mock_current_user, mocker):
    """Test that the PaymentDialog disables credit option when no customer is selected."""
    
    # Set up SalesView class with mocks
    from ui.views.sales_view import SalesView
    view = SalesView(
        product_service=mock_product_service,
        sale_service=mock_sale_service,
        customer_service=mock_customer_service,
        current_user=mock_current_user
    )
    
    # Create sale mock object
    sale_mock = mocker.MagicMock()
    sale_mock.id = 123
    mock_sale_service.create_sale.return_value = sale_mock
    
    # Set up view
    view._current_total = 100.0
    view.invoice_button = mocker.MagicMock()
    view._clear_sale = mocker.MagicMock()
    view.customer_combo = mocker.MagicMock()
    view.customer_combo.currentText.return_value = ""  # No customer selected
    view.customer_combo.currentData = mocker.MagicMock(return_value=None)
    
    # Mock items
    item_mock = mocker.MagicMock()
    item_mock.product_id = 1
    item_mock.quantity = 2
    view.sale_item_model = mocker.MagicMock()
    view.sale_item_model.get_all_items.return_value = [item_mock]
    
    # Mock PaymentDialog
    dialog_instance = mocker.MagicMock()
    dialog_instance.exec.return_value = True
    dialog_instance.selected_payment_method = "Efectivo"  # Cash payment since credit unavailable
    payment_dialog_mock = mocker.patch('ui.views.sales_view.PaymentDialog', return_value=dialog_instance)
    
    # Mock other functions
    mocker.patch('ui.views.sales_view.ask_confirmation', return_value=True)
    mocker.patch('ui.views.sales_view.show_info_message')
    
    # Call the method
    view.finalize_current_sale()
    
    # Assert PaymentDialog was called with allow_credit=False
    assert payment_dialog_mock.called
    # Check positional arguments instead of keyword arguments
    args, kwargs = payment_dialog_mock.call_args
    if kwargs and 'allow_credit' in kwargs:
        assert kwargs['allow_credit'] is False
    else:
        # The second argument to PaymentDialog is allow_credit
        assert len(args) >= 2
        assert args[1] is False

def test_payment_dialog_cancel(qtbot, mock_sale_service, mock_product_service, mock_customer_service, mock_current_user, mocker):
    """Test that canceling the PaymentDialog prevents sale finalization."""
    
    # Set up SalesView class with mocks
    from ui.views.sales_view import SalesView
    view = SalesView(
        product_service=mock_product_service,
        sale_service=mock_sale_service,
        customer_service=mock_customer_service,
        current_user=mock_current_user
    )
    
    # Set up view
    view._current_total = 100.0
    view._clear_sale = mocker.MagicMock()
    
    # Mock customer combo
    view.customer_combo = mocker.MagicMock()
    view.customer_combo.currentText.return_value = "Test Customer"
    view.customer_combo.currentData = mocker.MagicMock(return_value=42)
    
    # Mock items
    item_mock = mocker.MagicMock()
    item_mock.product_id = 1
    item_mock.quantity = 2
    view.sale_item_model = mocker.MagicMock()
    view.sale_item_model.get_all_items.return_value = [item_mock]
    
    # Mock PaymentDialog with cancelled dialog
    dialog_instance = mocker.MagicMock()
    dialog_instance.exec.return_value = False  # User cancelled
    dialog_instance.selected_payment_method = None
    mocker.patch('ui.views.sales_view.PaymentDialog', return_value=dialog_instance)
    
    # Call finalize_current_sale
    view.finalize_current_sale()
    
    # Sale should not be finalized when dialog is cancelled
    assert not mock_sale_service.create_sale.called

def test_print_receipt_pdf_open_failure(qtbot, mock_sale_service, mock_product_service, mock_customer_service, mock_current_user, mocker):
    """Test error handling when opening a PDF receipt fails."""
    
    # Set up mocks for error message
    error_message_mock = mocker.MagicMock()
    mocker.patch('ui.views.sales_view.show_error_message', error_message_mock)
    
    # Create SalesView with mocks
    from ui.views.sales_view import SalesView
    view = SalesView(
        product_service=mock_product_service,
        sale_service=mock_sale_service,
        customer_service=mock_customer_service,
        current_user=mock_current_user
    )
    
    # Mock generate_receipt_pdf to return a dummy path
    mock_sale_service.generate_receipt_pdf.return_value = "dummy_receipt.pdf"
    
    # Mock open_pdf_file to raise an exception
    def mock_open_pdf_file(file_path):
        raise Exception("Failed to open PDF")
    
    view.open_pdf_file = mock_open_pdf_file
    
    # Call print_receipt
    view.print_receipt(123)
    
    # Should show error message
    assert error_message_mock.called