import pytest
import sys
from unittest.mock import MagicMock, patch
from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialogButtonBox, QMessageBox
from PySide6.QtTest import QTest

from ui.dialogs.product_dialog import ProductDialog
from core.models.product import Product, Department
from core.services.product_service import ProductService


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    app.quit()


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
        unit="pcs",
        department_id=1
    )


@pytest.fixture
def sample_departments():
    """Create sample departments for testing."""
    return [
        Department(id=1, name="Electronics"),
        Department(id=2, name="Books")
    ]


@pytest.fixture
def mock_product_service(sample_departments):
    """Create a mock product service."""
    service = MagicMock(spec=ProductService)
    service.get_all_departments.return_value = sample_departments
    return service


@pytest.fixture
def dialog_add_mode(qapp, mock_product_service):
    """Create dialog in add mode."""
    return ProductDialog(mock_product_service, product_to_edit=None)


@pytest.fixture
def dialog_edit_mode(qapp, mock_product_service, sample_product):
    """Create dialog in edit mode."""
    return ProductDialog(mock_product_service, product_to_edit=sample_product)


def test_dialog_initialization_add_mode(qtbot, dialog_add_mode):
    """Test that the dialog initializes correctly in add mode."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Verify window title
    assert dialog.windowTitle() == "Agregar Producto"
    
    # Verify it's not in edit mode
    assert dialog.is_edit_mode is False
    assert dialog.product_to_edit is None
    
    # Verify default values
    assert dialog.code_edit.text() == ""
    assert dialog.description_edit.text() == ""
    assert dialog.cost_price_spinbox.value() == 0.0
    assert dialog.sell_price_spinbox.value() == 0.0
    assert dialog.min_stock_spinbox.value() == 0.0
    assert dialog.uses_inventory_checkbox.isChecked() is True


def test_dialog_initialization_edit_mode(qtbot, dialog_edit_mode, sample_product):
    """Test that the dialog initializes correctly in edit mode."""
    dialog = dialog_edit_mode
    qtbot.addWidget(dialog)
    
    # Verify window title
    assert dialog.windowTitle() == "Modificar Producto"
    
    # Verify it's in edit mode
    assert dialog.is_edit_mode is True
    assert dialog.product_to_edit == sample_product
    
    # Verify fields are populated with product data
    assert dialog.code_edit.text() == sample_product.code
    assert dialog.description_edit.text() == sample_product.description
    assert dialog.cost_price_spinbox.value() == float(sample_product.cost_price)
    assert dialog.sell_price_spinbox.value() == float(sample_product.sell_price)
    assert dialog.min_stock_spinbox.value() == float(sample_product.min_stock)
    assert dialog.uses_inventory_checkbox.isChecked() == sample_product.uses_inventory


def test_departments_loaded(qtbot, dialog_add_mode, mock_product_service):
    """Test that departments are loaded into the combo box."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Verify service was called
    mock_product_service.get_all_departments.assert_called_once()
    
    # Verify combo box is populated
    assert dialog.department_combo.count() == 2
    assert dialog.department_combo.itemText(0) == "Electronics"
    assert dialog.department_combo.itemData(0) == 1
    assert dialog.department_combo.itemText(1) == "Books"
    assert dialog.department_combo.itemData(1) == 2


def test_validation_empty_code(qtbot, dialog_add_mode):
    """Test validation when code is empty."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Leave code empty and try to accept
    dialog.description_edit.setText("Test Product")
    dialog.cost_price_spinbox.setValue(10.0)
    dialog.sell_price_spinbox.setValue(15.0)
    
    with patch.object(QMessageBox, 'warning') as mock_warning:
        dialog.accept()
        mock_warning.assert_called_once()
        assert "código" in mock_warning.call_args[0][2].lower()


def test_validation_empty_description(qtbot, dialog_add_mode):
    """Test validation when description is empty."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Leave description empty and try to accept
    dialog.code_edit.setText("TEST001")
    dialog.cost_price_spinbox.setValue(10.0)
    dialog.sell_price_spinbox.setValue(15.0)
    
    with patch.object(QMessageBox, 'warning') as mock_warning:
        dialog.accept()
        mock_warning.assert_called_once()
        assert "descripción" in mock_warning.call_args[0][2].lower()


def test_validation_zero_cost_price(qtbot, dialog_add_mode):
    """Test validation when cost price is zero."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Set cost price to zero and try to accept
    dialog.code_edit.setText("TEST001")
    dialog.description_edit.setText("Test Product")
    dialog.cost_price_spinbox.setValue(0.0)
    dialog.sell_price_spinbox.setValue(15.0)
    
    with patch.object(QMessageBox, 'warning') as mock_warning:
        dialog.accept()
        mock_warning.assert_called_once()
        assert "costo" in mock_warning.call_args[0][2].lower()


def test_validation_zero_sell_price(qtbot, dialog_add_mode):
    """Test validation when sell price is zero."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Set sell price to zero and try to accept
    dialog.code_edit.setText("TEST001")
    dialog.description_edit.setText("Test Product")
    dialog.cost_price_spinbox.setValue(10.0)
    dialog.sell_price_spinbox.setValue(0.0)
    
    with patch.object(QMessageBox, 'warning') as mock_warning:
        dialog.accept()
        mock_warning.assert_called_once()
        assert "venta" in mock_warning.call_args[0][2].lower()


def test_successful_add_product(qtbot, dialog_add_mode, mock_product_service, monkeypatch):
    """Test successful product addition."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Fill in valid data
    dialog.code_edit.setText("TEST001")
    dialog.description_edit.setText("Test Product")
    dialog.cost_price_spinbox.setValue(10.0)
    dialog.sell_price_spinbox.setValue(15.0)
    dialog.min_stock_spinbox.setValue(5.0)
    dialog.department_combo.setCurrentIndex(0)  # Electronics
    
    # Mock successful service call
    mock_product_service.add_product.return_value = True
    
    # Patch QDialog.accept to prevent actual dialog closing
    monkeypatch.setattr('PySide6.QtWidgets.QDialog.accept', lambda self: None)
    
    # Accept the dialog
    dialog.accept()
    
    # Verify service was called with correct data
    mock_product_service.add_product.assert_called_once()
    call_args = mock_product_service.add_product.call_args[0][0]
    assert call_args.code == "TEST001"
    assert call_args.description == "Test Product"
    assert call_args.cost_price == Decimal("10.0")
    assert call_args.sell_price == Decimal("15.0")
    assert call_args.min_stock == Decimal("5.0")
    assert call_args.department_id == 1


def test_successful_edit_product(qtbot, dialog_edit_mode, mock_product_service, sample_product, monkeypatch):
    """Test successful product editing."""
    dialog = dialog_edit_mode
    qtbot.addWidget(dialog)
    
    # Modify some data
    dialog.description_edit.setText("Modified Test Product")
    dialog.sell_price_spinbox.setValue(20.0)
    
    # Mock successful service call
    mock_product_service.update_product.return_value = True
    
    # Patch QDialog.accept to prevent actual dialog closing
    monkeypatch.setattr('PySide6.QtWidgets.QDialog.accept', lambda self: None)
    
    # Accept the dialog
    dialog.accept()
    
    # Verify service was called with correct data
    mock_product_service.update_product.assert_called_once()
    call_args = mock_product_service.update_product.call_args[0][0]
    assert call_args.id == sample_product.id
    assert call_args.description == "Modified Test Product"
    assert call_args.sell_price == Decimal("20.0")


def test_service_error_handling_add(qtbot, dialog_add_mode, mock_product_service):
    """Test handling of service errors during add."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Fill in valid data
    dialog.code_edit.setText("TEST001")
    dialog.description_edit.setText("Test Product")
    dialog.cost_price_spinbox.setValue(10.0)
    dialog.sell_price_spinbox.setValue(15.0)
    
    # Mock service error
    mock_product_service.add_product.side_effect = Exception("Database error")
    
    with patch.object(QMessageBox, 'critical') as mock_critical:
        dialog.accept()
        mock_critical.assert_called_once()
        assert "error" in mock_critical.call_args[0][2].lower()


def test_service_error_handling_edit(qtbot, dialog_edit_mode, mock_product_service):
    """Test handling of service errors during edit."""
    dialog = dialog_edit_mode
    qtbot.addWidget(dialog)
    
    # Mock service error
    mock_product_service.update_product.side_effect = Exception("Database error")
    
    with patch.object(QMessageBox, 'critical') as mock_critical:
        dialog.accept()
        mock_critical.assert_called_once()
        assert "error" in mock_critical.call_args[0][2].lower()


def test_cancel_dialog(qtbot, dialog_add_mode):
    """Test canceling the dialog."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Fill in some data
    dialog.code_edit.setText("TEST001")
    dialog.description_edit.setText("Test Product")
    
    # Cancel the dialog
    dialog.reject()
    
    # Verify dialog result
    assert dialog.result() == dialog.Rejected


def test_uses_inventory_checkbox_behavior(qtbot, dialog_add_mode):
    """Test that uses_inventory checkbox affects min_stock field."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Initially uses_inventory should be checked and min_stock enabled
    assert dialog.uses_inventory_checkbox.isChecked() is True
    assert dialog.min_stock_spinbox.isEnabled() is True
    
    # Uncheck uses_inventory
    dialog.uses_inventory_checkbox.setChecked(False)
    
    # min_stock should be disabled
    assert dialog.min_stock_spinbox.isEnabled() is False
    
    # Check uses_inventory again
    dialog.uses_inventory_checkbox.setChecked(True)
    
    # min_stock should be enabled again
    assert dialog.min_stock_spinbox.isEnabled() is True