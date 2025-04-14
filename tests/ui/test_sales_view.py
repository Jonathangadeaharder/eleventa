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
def sales_view(qtbot, mock_sale_service):
    # Create a SalesView instance with mocked dependencies
    # The actual constructor may require more arguments; adjust as needed
    view = SalesView()
    view.sale_service = mock_sale_service
    # Mock other dependencies as needed
    view.show_info_message = MagicMock()
    view.show_error_message = MagicMock()
    view._get_items_data = MagicMock(return_value=[{"id": 1, "qty": 2}])
    view._get_selected_customer = MagicMock(return_value=None)
    view._get_payment_type = MagicMock(return_value="cash")
    view._clear_sale = MagicMock()
    view.ask_confirmation = MagicMock(return_value=True)
    view._has_items = MagicMock(return_value=True)
    return view

def test_finalize_sale_success(sales_view, mock_sale_service):
    # Simulate successful sale finalization
    mock_sale_service.create_sale.return_value = 123  # sale_id
    sales_view.finalize_current_sale()
    # Should call create_sale with expected arguments
    assert mock_sale_service.create_sale.called
    # Should show info message
    assert sales_view.show_info_message.called
    # Should clear sale
    assert sales_view._clear_sale.called

def test_finalize_sale_error_handling(sales_view, mock_sale_service):
    # Simulate service raising an exception
    mock_sale_service.create_sale.side_effect = Exception("Service error")
    sales_view.finalize_current_sale()
    # Should show error message
    assert sales_view.show_error_message.called
    # Should not call _clear_sale
    assert not sales_view._clear_sale.called

@patch("ui.views.sales_view.PaymentDialog")
def test_payment_dialog_credit_option_enabled(qtbot, sales_view, mock_sale_service, mocker):
    """
    Test that the PaymentDialog enables/disables the credit option based on customer selection.
    """
    # Patch _get_selected_customer_id to simulate customer selection
    mocker.patch.object(sales_view, "_get_selected_customer_id", return_value=42)
    # Patch sale_item_model.get_all_items to simulate items in the sale
    mocker.patch.object(sales_view.sale_item_model, "get_all_items", return_value=[MagicMock(subtotal=100, product_id=1, quantity=1)])
    # Patch ask_confirmation to always confirm
    mocker.patch("ui.views.sales_view.ask_confirmation", return_value=True)
    # Mock PaymentDialog instance
    dialog_instance = MagicMock()
    dialog_instance.exec.return_value = True
    dialog_instance.selected_payment_method = "Crédito"
    mock_payment_dialog = mocker.patch("ui.views.sales_view.PaymentDialog", return_value=dialog_instance)
    # Patch current_user
    sales_view.current_user = MagicMock(id=1)
    # Patch customer_combo.currentText
    sales_view.customer_combo = MagicMock()
    sales_view.customer_combo.currentText.return_value = "Test Customer"
    # Call finalize_current_sale
    sales_view.finalize_current_sale()
    # PaymentDialog should be called with allow_credit=True
    args, kwargs = mock_payment_dialog.call_args
    assert kwargs.get("allow_credit", args[1] if len(args) > 1 else None) is True
    # Sale should be finalized with is_credit_sale True
    assert mock_sale_service.create_sale.called
    call_kwargs = mock_sale_service.create_sale.call_args.kwargs
    assert call_kwargs.get("is_credit_sale") is True
    assert call_kwargs.get("payment_type") == "Crédito"

@patch("ui.views.sales_view.PaymentDialog")
def test_payment_dialog_credit_option_disabled(qtbot, sales_view, mock_sale_service, mocker):
    """
    Test that the PaymentDialog disables the credit option when no customer is selected.
    """
    mocker.patch.object(sales_view, "_get_selected_customer_id", return_value=None)
    mocker.patch.object(sales_view.sale_item_model, "get_all_items", return_value=[MagicMock(subtotal=100, product_id=1, quantity=1)])
    mocker.patch("ui.views.sales_view.ask_confirmation", return_value=True)
    dialog_instance = MagicMock()
    dialog_instance.exec.return_value = True
    dialog_instance.selected_payment_method = "Efectivo"
    mock_payment_dialog = mocker.patch("ui.views.sales_view.PaymentDialog", return_value=dialog_instance)
    sales_view.current_user = MagicMock(id=1)
    sales_view.customer_combo = MagicMock()
    sales_view.customer_combo.currentText.return_value = ""
    sales_view.finalize_current_sale()
    args, kwargs = mock_payment_dialog.call_args
    assert kwargs.get("allow_credit", args[1] if len(args) > 1 else None) is False
    assert mock_sale_service.create_sale.called
    call_kwargs = mock_sale_service.create_sale.call_args.kwargs
    assert call_kwargs.get("is_credit_sale") is False
    assert call_kwargs.get("payment_type") == "Efectivo"

@patch("ui.views.sales_view.PaymentDialog")
def test_payment_dialog_cancel(qtbot, sales_view, mock_sale_service, mocker):
    """
    Test that canceling the PaymentDialog prevents sale finalization.
    """
    mocker.patch.object(sales_view, "_get_selected_customer_id", return_value=42)
    mocker.patch.object(sales_view.sale_item_model, "get_all_items", return_value=[MagicMock(subtotal=100, product_id=1, quantity=1)])
    dialog_instance = MagicMock()
    dialog_instance.exec.return_value = False  # Simulate user cancel
    dialog_instance.selected_payment_method = None
    mocker.patch("ui.views.sales_view.PaymentDialog", return_value=dialog_instance)
    sales_view.current_user = MagicMock(id=1)
    sales_view.customer_combo = MagicMock()
    sales_view.customer_combo.currentText.return_value = "Test Customer"
    sales_view.finalize_current_sale()
    # Sale should not be finalized
    assert not mock_sale_service.create_sale.called

def test_print_receipt_pdf_open_failure(sales_view, mock_sale_service):
    """
    Test that an error is shown if opening the PDF file fails in print_receipt.
    """
    # Mock generate_receipt_pdf to return a dummy path
    mock_sale_service.generate_receipt_pdf.return_value = "dummy_receipt.pdf"
    # Patch open_pdf_file to raise an exception
    sales_view.open_pdf_file = MagicMock(side_effect=Exception("Failed to open PDF"))
    # Call print_receipt
    sales_view.print_receipt(123)
    # Should show error message
    assert sales_view.show_error_message.called