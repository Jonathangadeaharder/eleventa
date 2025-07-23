import pytest
import sys
from unittest.mock import MagicMock, patch
from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialogButtonBox, QMessageBox

from ui.dialogs.product_dialog import ProductDialog
from core.models.product import Product, Department
from core.services.product_service import ProductService
from core.models.unit import Unit


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
        unit="Pieza",
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
def sample_units():
    """Create sample units for testing."""
    return [
        Unit(id=1, name="Pieza", abbreviation="pza", is_active=True),
        Unit(id=2, name="Kilogramo", abbreviation="kg", is_active=True),
        Unit(id=3, name="Metro", abbreviation="m", is_active=True)
    ]


@pytest.fixture
def mock_product_service(sample_departments):
    """Create a mock product service."""
    service = MagicMock(spec=ProductService)
    service.get_all_departments.return_value = sample_departments
    return service


@pytest.fixture
def mock_unit_service(sample_units):
    """Create a mock unit service."""
    from core.services.unit_service import UnitService
    service = MagicMock(spec=UnitService)
    service.get_all_units.return_value = sample_units
    return service


@pytest.fixture
def dialog_add_mode(qapp, mock_product_service, mock_unit_service):
    """Create dialog in add mode."""
    with patch('ui.dialogs.product_dialog.UnitService', return_value=mock_unit_service):
        return ProductDialog(mock_product_service, product_to_edit=None)


@pytest.fixture
def dialog_edit_mode(qapp, mock_product_service, mock_unit_service, sample_product):
    """Create dialog in edit mode."""
    with patch('ui.dialogs.product_dialog.UnitService', return_value=mock_unit_service):
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
    assert dialog.code_input.text() == ""
    assert dialog.description_input.text() == ""
    assert dialog.cost_price_input.value() == 0.0
    assert dialog.sale_price_input.value() == 0.0
    assert dialog.min_stock_input.value() == 0.0
    assert dialog.inventory_checkbox.isChecked() is True
    
    # Check that unit combo is populated
    assert dialog.unit_combo.count() > 0


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
    assert dialog.code_input.text() == sample_product.code
    assert dialog.description_input.text() == sample_product.description
    assert dialog.cost_price_input.value() == float(sample_product.cost_price)
    assert dialog.sale_price_input.value() == float(sample_product.sell_price)
    assert dialog.min_stock_input.value() == float(sample_product.min_stock)
    assert dialog.inventory_checkbox.isChecked() == sample_product.uses_inventory
    
    # Check that unit combo has the correct selection
    current_unit = dialog.unit_combo.currentData()
    assert current_unit is not None


def test_departments_loaded(qtbot, dialog_add_mode, mock_product_service):
    """Test that departments are loaded into the combo box."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Verify service was called
    mock_product_service.get_all_departments.assert_called_once()
    
    # Verify combo box is populated
    assert dialog.department_combo.count() == 3  # "- Sin Departamento -" + 2 departments
    assert dialog.department_combo.itemText(0) == "- Sin Departamento -"
    assert dialog.department_combo.itemData(0) is None
    assert dialog.department_combo.itemText(1) == "Electronics"
    assert dialog.department_combo.itemData(1) == 1
    assert dialog.department_combo.itemText(2) == "Books"
    assert dialog.department_combo.itemData(2) == 2


def test_service_validation_empty_code(qtbot, dialog_add_mode, mock_product_service):
    """Test handling of service validation error for empty code."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Fill in data with empty code
    dialog.id_input.setText("")  # Clear auto-suggested ID
    dialog.code_input.setText("")  # Empty code
    dialog.description_input.setText("Test Product")
    dialog.cost_price_input.setValue(10.0)
    dialog.sale_price_input.setValue(15.0)
    
    # Mock service to raise validation error
    mock_product_service.add_product.side_effect = ValueError("Code cannot be empty")
    
    with patch('ui.dialogs.product_dialog.show_error_message') as mock_error:
        dialog.accept()
        mock_error.assert_called_once_with(dialog, "Error de validación", "Code cannot be empty")


def test_service_validation_empty_description(qtbot, dialog_add_mode, mock_product_service):
    """Test handling of service validation error for empty description."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Fill in data with empty description
    dialog.id_input.setText("")  # Clear auto-suggested ID
    dialog.code_input.setText("TEST001")
    dialog.description_input.setText("")  # Empty description
    dialog.cost_price_input.setValue(10.0)
    dialog.sale_price_input.setValue(15.0)
    
    # Mock service to raise validation error
    mock_product_service.add_product.side_effect = ValueError("Description cannot be empty")
    
    with patch('ui.dialogs.product_dialog.show_error_message') as mock_error:
        dialog.accept()
        mock_error.assert_called_once_with(dialog, "Error de validación", "Description cannot be empty")


def test_service_validation_zero_cost_price(qtbot, dialog_add_mode, mock_product_service):
    """Test handling of service validation error for zero cost price."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Set cost price to zero
    dialog.id_input.setText("")  # Clear auto-suggested ID
    dialog.code_input.setText("TEST001")
    dialog.description_input.setText("Test Product")
    dialog.cost_price_input.setValue(0.0)
    dialog.sale_price_input.setValue(15.0)
    
    # Mock service to raise validation error
    mock_product_service.add_product.side_effect = ValueError("Cost price cannot be zero")
    
    with patch('ui.dialogs.product_dialog.show_error_message') as mock_error:
        dialog.accept()
        mock_error.assert_called_once_with(dialog, "Error de validación", "Cost price cannot be zero")


def test_service_validation_zero_sell_price(qtbot, dialog_add_mode, mock_product_service):
    """Test handling of service validation error for zero sell price."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Set sell price to zero
    dialog.id_input.setText("")  # Clear auto-suggested ID
    dialog.code_input.setText("TEST001")
    dialog.description_input.setText("Test Product")
    dialog.cost_price_input.setValue(10.0)
    dialog.sale_price_input.setValue(0.0)
    
    # Mock service to raise validation error
    mock_product_service.add_product.side_effect = ValueError("Sell price cannot be zero")
    
    with patch('ui.dialogs.product_dialog.show_error_message') as mock_error:
        dialog.accept()
        mock_error.assert_called_once_with(dialog, "Error de validación", "Sell price cannot be zero")


def test_successful_add_product(qtbot, dialog_add_mode, mock_product_service, monkeypatch):
    """Test successful product addition."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Fill in valid data
    dialog.id_input.setText("")  # Clear auto-suggested ID
    dialog.code_input.setText("TEST001")
    dialog.description_input.setText("Test Product")
    dialog.cost_price_input.setValue(10.0)
    dialog.sale_price_input.setValue(15.0)
    dialog.min_stock_input.setValue(5.0)
    dialog.department_combo.setCurrentIndex(1)  # Electronics
    
    # Mock successful service call - should return a Product object
    from core.models.product import Product
    from decimal import Decimal
    mock_product = Product(
        id=1,
        code="TEST001",
        description="Test Product",
        cost_price=Decimal("10.0"),
        sell_price=Decimal("15.0"),
        quantity_in_stock=Decimal("0.0"),
        uses_inventory=False,
        min_stock=Decimal("5.0"),
        unit="U",
        department_id=1
    )
    mock_product_service.add_product.return_value = mock_product
    
    # Patch QDialog.accept to prevent actual dialog closing
    monkeypatch.setattr('PySide6.QtWidgets.QDialog.accept', lambda self: None)
    
    with patch('ui.dialogs.product_dialog.show_info_message') as mock_info, \
         patch('ui.dialogs.product_dialog.show_error_message') as mock_error:
        # Accept the dialog
        dialog.accept()
        # Verify success message was shown
        mock_info.assert_called_once_with(dialog, "Éxito", "Producto agregado correctamente")
        # Verify no error was shown
        mock_error.assert_not_called()
    
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
    dialog.description_input.setText("Modified Test Product")
    dialog.sale_price_input.setValue(20.0)
    
    # Mock successful service call - update_product doesn't return anything
    mock_product_service.update_product.return_value = None
    
    # Patch QDialog.accept to prevent actual dialog closing
    monkeypatch.setattr('PySide6.QtWidgets.QDialog.accept', lambda self: None)
    
    with patch('ui.dialogs.product_dialog.show_info_message') as mock_info, \
         patch('ui.dialogs.product_dialog.show_error_message') as mock_error:
        # Accept the dialog
        dialog.accept()
        # Verify success message was shown
        mock_info.assert_called_once_with(dialog, "Éxito", "Producto modificado correctamente")
        # Verify no error was shown
        mock_error.assert_not_called()
    
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
    dialog.id_input.setText("")  # Clear auto-suggested ID
    dialog.code_input.setText("TEST001")
    dialog.description_input.setText("Test Product")
    dialog.cost_price_input.setValue(10.0)
    dialog.sale_price_input.setValue(15.0)
    
    # Mock service error
    mock_product_service.add_product.side_effect = Exception("Database error")
    
    with patch('ui.dialogs.product_dialog.show_error_message') as mock_error:
        dialog.accept()
        mock_error.assert_called_once()
        # Check that error message contains "error"
        call_args = mock_error.call_args[0]
        assert "error" in call_args[2].lower()


def test_field_focus_on_validation_error(qtbot, dialog_add_mode, mock_product_service):
    """Test that the correct field gets focus when validation errors occur."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Show the dialog to ensure it can receive focus
    dialog.show()
    qtbot.waitExposed(dialog)
    
    # Test code field focus
    dialog.id_input.setText("")  # Clear auto-suggested ID
    dialog.code_input.setText("")
    dialog.description_input.setText("Test Product")
    mock_product_service.add_product.side_effect = ValueError("Code cannot be empty")
    
    with patch('ui.dialogs.product_dialog.show_error_message'):
        dialog.accept()
        qtbot.wait(10)  # Allow time for focus to be set
        assert dialog.code_input.hasFocus()
    
    # Test description field focus
    dialog.code_input.setText("TEST001")
    dialog.description_input.setText("")
    mock_product_service.add_product.side_effect = ValueError("Description cannot be empty")
    
    with patch('ui.dialogs.product_dialog.show_error_message'):
        dialog.accept()
        qtbot.wait(10)  # Allow time for focus to be set
        assert dialog.description_input.hasFocus()
    
    # Test cost price field focus
    dialog.description_input.setText("Test Product")
    dialog.cost_price_input.setValue(0.0)
    mock_product_service.add_product.side_effect = ValueError("Cost price cannot be zero")
    
    with patch('ui.dialogs.product_dialog.show_error_message'):
        dialog.accept()
        qtbot.wait(10)  # Allow time for focus to be set
        assert dialog.cost_price_input.hasFocus()
    
    # Test sell price field focus
    dialog.cost_price_input.setValue(10.0)
    dialog.sale_price_input.setValue(0.0)
    mock_product_service.add_product.side_effect = ValueError("Sell price cannot be zero")
    
    with patch('ui.dialogs.product_dialog.show_error_message'):
        dialog.accept()
        qtbot.wait(10)  # Allow time for focus to be set
        assert dialog.sale_price_input.hasFocus()


def test_duplicate_code_error_handling(qtbot, dialog_add_mode, mock_product_service):
    """Test handling of duplicate product code error."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Show the dialog to ensure it can receive focus
    dialog.show()
    qtbot.waitExposed(dialog)
    
    # Fill in data
    dialog.id_input.setText("")  # Clear auto-suggested ID
    dialog.code_input.setText("DUP001")
    dialog.description_input.setText("Test Product")
    dialog.cost_price_input.setValue(10.0)
    dialog.sale_price_input.setValue(15.0)
    
    # Mock service to raise duplicate code error
    mock_product_service.add_product.side_effect = ValueError("Product code 'DUP001' already exists")
    
    with patch('ui.dialogs.product_dialog.show_error_message') as mock_error:
        dialog.accept()
        mock_error.assert_called_once_with(dialog, "Error de validación", "Product code 'DUP001' already exists")
        # Code field should get focus for duplicate code error
        qtbot.wait(10)  # Allow time for focus to be set
        assert dialog.code_input.hasFocus()


def test_service_error_handling_edit(qtbot, dialog_edit_mode, mock_product_service):
    """Test handling of service errors during edit."""
    dialog = dialog_edit_mode
    qtbot.addWidget(dialog)
    
    # Mock service error
    mock_product_service.update_product.side_effect = Exception("Database error")
    
    with patch('ui.dialogs.product_dialog.show_error_message') as mock_error:
        dialog.accept()
        mock_error.assert_called_once()
        # Check that error message contains "error"
        call_args = mock_error.call_args[0]
        assert "error" in call_args[2].lower()


def test_cancel_dialog(qtbot, dialog_add_mode):
    """Test canceling the dialog."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Fill in some data
    dialog.code_input.setText("TEST001")
    dialog.description_input.setText("Test Product")
    
    # Cancel the dialog
    dialog.reject()
    
    # Verify dialog result
    from PySide6.QtWidgets import QDialog
    assert dialog.result() == QDialog.Rejected


def test_uses_inventory_checkbox_behavior(qtbot, dialog_add_mode):
    """Test that uses_inventory checkbox affects min_stock field visibility."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Show the dialog and wait for it to be exposed
    with qtbot.waitExposed(dialog):
        dialog.show()
    
    # Process events to ensure UI is fully initialized
    qtbot.wait(50)
    
    # Initially uses_inventory should be checked
    assert dialog.inventory_checkbox.isChecked() is True
    
    # Trigger the checkbox to ensure signal is processed
    dialog.inventory_checkbox.setChecked(True)  # Re-set to trigger signal
    qtbot.wait(10)
    
    # The min_stock field should be visible since checkbox is checked
    assert dialog.min_stock_input.isVisible() is True
    
    # Test hiding the fields by unchecking
    dialog.inventory_checkbox.setChecked(False)
    qtbot.wait(10)  # Wait for signal processing
    assert dialog.min_stock_input.isVisible() is False
    
    # Test showing them again by checking
    dialog.inventory_checkbox.setChecked(True)
    qtbot.wait(10)  # Wait for signal processing
    assert dialog.min_stock_input.isVisible() is True
    
    # Test unchecking again
    dialog.inventory_checkbox.setChecked(False)
    qtbot.wait(10)  # Wait for signal processing
    
    # min_stock should be hidden
    assert dialog.min_stock_input.isVisible() is False
    
    # Check uses_inventory one more time
    dialog.inventory_checkbox.setChecked(True)
    qtbot.wait(10)  # Wait for signal processing
    
    # min_stock should be visible again
    assert dialog.min_stock_input.isVisible() is True


def test_unit_combo_functionality(qtbot, dialog_add_mode, sample_units):
    """Test that unit combo box works correctly with units."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Verify unit combo is populated (includes default "U" + sample_units)
    expected_count = len(sample_units) + 1  # +1 for default "U"
    assert dialog.unit_combo.count() == expected_count
    
    # Verify default unit "U" is first
    assert dialog.unit_combo.itemText(0) == "U"
    assert dialog.unit_combo.itemData(0) == "U"
    
    # Verify sample units are loaded correctly (starting from index 1)
    for i, unit in enumerate(sample_units):
        combo_index = i + 1  # +1 because "U" is at index 0
        expected_text = f"{unit.name} ({unit.abbreviation})"
        assert dialog.unit_combo.itemText(combo_index) == expected_text
        assert dialog.unit_combo.itemData(combo_index) == unit.name  # Data is unit.name, not abbreviation
    
    # Test selecting different units
    dialog.unit_combo.setCurrentIndex(1)  # Select first sample unit
    assert dialog.unit_combo.currentData() == sample_units[0].name
    
    dialog.unit_combo.setCurrentIndex(2)  # Select second sample unit
    assert dialog.unit_combo.currentData() == sample_units[1].name


def test_unit_combo_in_edit_mode(qtbot, dialog_edit_mode, sample_product, sample_units):
    """Test that unit combo shows correct selection in edit mode."""
    dialog = dialog_edit_mode
    qtbot.addWidget(dialog)
    
    # Verify the unit combo has the correct selection for the product being edited
    current_unit = dialog.unit_combo.currentData()
    assert current_unit == sample_product.unit  # Should be "Pieza"
    
    # Verify the correct index is selected (should be index 1 for "Pieza")
    expected_index = 1  # "Pieza" is the first unit in sample_units, so index 1 (after "U" at index 0)
    assert dialog.unit_combo.currentIndex() == expected_index
    
    # Test changing the unit selection
    original_index = dialog.unit_combo.currentIndex()
    new_index = (original_index + 1) % dialog.unit_combo.count()
    dialog.unit_combo.setCurrentIndex(new_index)
    
    # Verify the selection changed
    assert dialog.unit_combo.currentIndex() == new_index
    assert dialog.unit_combo.currentData() != sample_product.unit


def test_product_creation_with_unit_selection(qtbot, dialog_add_mode, mock_product_service):
    """Test that product creation includes the selected unit."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Clear auto-suggested ID
    dialog.id_input.setText("")
    
    # Fill in valid data
    dialog.code_input.setText("TEST001")
    dialog.description_input.setText("Test Product")
    dialog.cost_price_input.setValue(10.0)
    dialog.sale_price_input.setValue(15.0)
    dialog.min_stock_input.setValue(5.0)
    dialog.department_combo.setCurrentIndex(1)  # Electronics
    dialog.unit_combo.setCurrentIndex(1)  # Select second unit
    
    # Mock successful service call
    from core.models.product import Product
    from decimal import Decimal
    mock_product = Product(
         id=1,
         code="TEST001",
         description="Test Product",
         cost_price=Decimal("10.0"),
         sell_price=Decimal("15.0"),
         quantity_in_stock=Decimal("0.0"),
         uses_inventory=True,
         min_stock=Decimal("5.0"),
         unit="Pieza",  # First unit from sample_units (index 1 in combo)
         department_id=1
     )
    mock_product_service.add_product.return_value = mock_product
    
    with patch('ui.dialogs.product_dialog.show_info_message') as mock_info:
        # Patch super().accept() to prevent actual dialog closing but allow the method to complete
        with patch.object(dialog.__class__.__bases__[0], 'accept') as mock_super_accept:
            dialog.accept()
            mock_info.assert_called_once_with(dialog, "Éxito", "Producto agregado correctamente")
            mock_super_accept.assert_called_once()
    
    # Verify service was called with correct unit
    mock_product_service.add_product.assert_called_once()
    call_args = mock_product_service.add_product.call_args[0][0]
    assert call_args.unit == dialog.unit_combo.currentData()