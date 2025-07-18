import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from typing import Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialogButtonBox

from ui.dialogs.adjust_inventory_dialog import AdjustInventoryDialog
from core.models.product import Product
from core.services.inventory_service import InventoryService

@pytest.fixture
def sample_product():
    """Create a sample product for testing."""
    return Product(
        id=1,
        code="TEST001",
        description="Test Product",
        cost_price=Decimal("10.00"),
        sell_price=Decimal("15.00"),
        quantity_in_stock=Decimal("20.00"),
        uses_inventory=True,
        min_stock=Decimal("5.00"),
        unit="pcs"
    )

@pytest.fixture
def mock_inventory_service():
    """Create a mock inventory service."""
    return MagicMock(spec=InventoryService)

def test_dialog_initialization(qtbot, sample_product, mock_inventory_service):
    """Test that the dialog initializes correctly with product information."""
    dialog = AdjustInventoryDialog(mock_inventory_service, sample_product)
    qtbot.addWidget(dialog)
    
    # Verify product info is displayed correctly
    assert dialog.code_label.text() == sample_product.code
    assert dialog.desc_label.text() == sample_product.description
    assert f"{sample_product.quantity_in_stock:.2f}" in dialog.current_stock_label.text()
    
    # Verify default values
    assert dialog.increase_radio.isChecked() is True
    assert dialog.decrease_radio.isChecked() is False
    assert dialog.quantity_spinbox.value() == 1.0
    assert dialog.reason_edit.toPlainText() == ""
    
    # Verify the result preview shows the correct calculation
    expected_result = f"{sample_product.quantity_in_stock:.2f} + 1.00 = {sample_product.quantity_in_stock + 1:.2f}"
    assert expected_result in dialog.result_label.text()

def test_update_result_label_increase(qtbot, sample_product, mock_inventory_service):
    """Test that the result label updates correctly when increasing stock."""
    dialog = AdjustInventoryDialog(mock_inventory_service, sample_product)
    qtbot.addWidget(dialog)
    
    # Change quantity
    dialog.quantity_spinbox.setValue(5.0)
    
    # Verify result label
    expected_result = f"{sample_product.quantity_in_stock:.2f} + 5.00 = {sample_product.quantity_in_stock + 5:.2f}"
    assert expected_result in dialog.result_label.text()
    assert "red" not in dialog.result_label.styleSheet()  # Should not show error

def test_update_result_label_decrease(qtbot, sample_product, mock_inventory_service):
    """Test that the result label updates correctly when decreasing stock."""
    dialog = AdjustInventoryDialog(mock_inventory_service, sample_product)
    qtbot.addWidget(dialog)
    
    # Switch to decrease mode and change quantity
    dialog.decrease_radio.setChecked(True)
    dialog.quantity_spinbox.setValue(5.0)
    
    # Verify result label
    expected_result = f"{sample_product.quantity_in_stock:.2f} - 5.00 = {sample_product.quantity_in_stock - 5:.2f}"
    assert expected_result in dialog.result_label.text()
    assert "red" not in dialog.result_label.styleSheet()  # Should not show error

def test_update_result_label_negative_stock(qtbot, sample_product, mock_inventory_service):
    """Test that the result label shows error when adjustment would result in negative stock."""
    dialog = AdjustInventoryDialog(mock_inventory_service, sample_product)
    qtbot.addWidget(dialog)
    
    # Switch to decrease mode and set quantity higher than current stock
    dialog.decrease_radio.setChecked(True)
    dialog.quantity_spinbox.setValue(sample_product.quantity_in_stock + 5)
    
    # Verify result label shows error
    assert "ERROR" in dialog.result_label.text()
    assert "red" in dialog.result_label.styleSheet()

def test_accept_validation_quantity_zero(qtbot, sample_product, mock_inventory_service, monkeypatch):
    """Test validation when quantity is zero."""
    dialog = AdjustInventoryDialog(mock_inventory_service, sample_product)
    qtbot.addWidget(dialog)
    
    # Mock show_error_message to verify it's called
    mock_show_error = MagicMock()
    monkeypatch.setattr("ui.dialogs.adjust_inventory_dialog.show_error_message", mock_show_error)
    
    # Set quantity to zero
    dialog.quantity_spinbox.setValue(0.0)
    
    # Try to accept the dialog
    dialog.accept()
    
    # Verify error was shown
    mock_show_error.assert_called_once()
    assert "Cantidad Inválida" in mock_show_error.call_args[0][1]
    
    # Verify service was not called
    mock_inventory_service.adjust_inventory.assert_not_called()

def test_accept_validation_no_reason(qtbot, sample_product, mock_inventory_service, monkeypatch):
    """Test validation when reason is empty."""
    dialog = AdjustInventoryDialog(mock_inventory_service, sample_product)
    qtbot.addWidget(dialog)
    
    # Mock show_error_message to verify it's called
    mock_show_error = MagicMock()
    monkeypatch.setattr("ui.dialogs.adjust_inventory_dialog.show_error_message", mock_show_error)
    
    # Set valid quantity but empty reason
    dialog.quantity_spinbox.setValue(5.0)
    dialog.reason_edit.setPlainText("")
    
    # Try to accept the dialog
    dialog.accept()
    
    # Verify error was shown
    mock_show_error.assert_called_once()
    assert "Motivo Requerido" in mock_show_error.call_args[0][1]
    
    # Verify service was not called
    mock_inventory_service.adjust_inventory.assert_not_called()

def test_accept_validation_negative_stock(qtbot, sample_product, mock_inventory_service, monkeypatch):
    """Test validation when adjustment would result in negative stock."""
    dialog = AdjustInventoryDialog(mock_inventory_service, sample_product)
    qtbot.addWidget(dialog)
    
    # Mock show_error_message to verify it's called
    mock_show_error = MagicMock()
    monkeypatch.setattr("ui.dialogs.adjust_inventory_dialog.show_error_message", mock_show_error)
    
    # Set decrease mode with quantity higher than stock
    dialog.decrease_radio.setChecked(True)
    dialog.quantity_spinbox.setValue(sample_product.quantity_in_stock + 5)
    dialog.reason_edit.setPlainText("Test reason")
    
    # Try to accept the dialog
    dialog.accept()
    
    # Verify error was shown
    mock_show_error.assert_called_once()
    assert "Stock Insuficiente" in mock_show_error.call_args[0][1]
    
    # Verify service was not called
    mock_inventory_service.adjust_inventory.assert_not_called()

def test_successful_increase_stock(qtbot, sample_product, mock_inventory_service, monkeypatch):
    """Test successful stock increase."""
    dialog = AdjustInventoryDialog(mock_inventory_service, sample_product)
    qtbot.addWidget(dialog)
    
    # Set up valid inputs for increase
    dialog.increase_radio.setChecked(True)
    dialog.quantity_spinbox.setValue(5.0)
    dialog.reason_edit.setPlainText("Testing stock increase")
    
    # Configure mock to avoid UI interaction during the test
    mock_inventory_service.adjust_inventory.return_value = sample_product
    
    # Patch QDialog.accept to prevent actual dialog closing
    monkeypatch.setattr('PySide6.QtWidgets.QDialog.accept', lambda self: None)
    
    # Accept the dialog
    dialog.accept()
    
    # Verify service was called with correct parameters
    mock_inventory_service.adjust_inventory.assert_called_once_with(
        product_id=sample_product.id,
        quantity=Decimal('5.0'),  # Positive for increase
        reason="Testing stock increase",
        user_id=None
    )

def test_successful_decrease_stock(qtbot, sample_product, mock_inventory_service, monkeypatch):
    """Test successful stock decrease."""
    dialog = AdjustInventoryDialog(mock_inventory_service, sample_product)
    qtbot.addWidget(dialog)
    
    # Set up valid inputs for decrease
    dialog.decrease_radio.setChecked(True)
    dialog.quantity_spinbox.setValue(5.0)
    dialog.reason_edit.setPlainText("Testing stock decrease")
    
    # Configure mock to avoid UI interaction during the test
    mock_inventory_service.adjust_inventory.return_value = sample_product
    
    # Patch QDialog.accept to prevent actual dialog closing
    monkeypatch.setattr('PySide6.QtWidgets.QDialog.accept', lambda self: None)
    
    # Accept the dialog
    dialog.accept()
    
    # Verify service was called with correct parameters
    mock_inventory_service.adjust_inventory.assert_called_once_with(
        product_id=sample_product.id,
        quantity=Decimal('-5.0'),  # Negative for decrease
        reason="Testing stock decrease",
        user_id=None
    )

def test_service_error_handling(qtbot, sample_product, mock_inventory_service, monkeypatch):
    """Test handling of service errors."""
    dialog = AdjustInventoryDialog(mock_inventory_service, sample_product)
    qtbot.addWidget(dialog)
    
    # Set up valid inputs
    dialog.quantity_spinbox.setValue(5.0)
    dialog.reason_edit.setPlainText("Test error handling")
    
    # Configure mock to raise an exception
    error_message = "Test service error"
    mock_inventory_service.adjust_inventory.side_effect = ValueError(error_message)
    
    # Mock QMessageBox to avoid UI interaction
    mock_warning = MagicMock()
    monkeypatch.setattr("ui.dialogs.adjust_inventory_dialog.QMessageBox.warning", mock_warning)
    
    # Accept the dialog
    dialog.accept()
    
    # Verify warning was shown with correct error message
    mock_warning.assert_called_once()
    assert error_message in mock_warning.call_args[0][2]