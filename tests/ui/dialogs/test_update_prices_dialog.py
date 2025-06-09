# tests/ui/dialogs/test_update_prices_dialog.py
import pytest
from unittest.mock import MagicMock, call, ANY
from decimal import Decimal

from PySide6.QtWidgets import QApplication, QMessageBox, QDialog
from PySide6.QtCore import Qt

# Adjust path to import from the project root
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ui.dialogs.update_prices_dialog import UpdatePricesDialog
from core.services.product_service import ProductService
from core.models.product import Department, Product
from core.interfaces.repository_interfaces import IProductRepository, IDepartmentRepository

# QApplication instance for Qt widgets
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

@pytest.fixture
def mock_product_service(mocker):
    service = mocker.MagicMock(spec=ProductService)
    # Mock department fetching for the dialog
    service.get_all_departments.return_value = [
        Department(id=1, name="Electronics", description="E"),
        Department(id=2, name="Books", description="B")
    ]
    # Mock the main price update function
    service.update_prices_by_percentage.return_value = 5 # Simulate 5 products updated
    return service

@pytest.fixture
def dialog(qapp, mock_product_service):
    # Pass a parent if your dialog expects one, or None
    # Ensure qapp fixture is used to initialize QApplication if needed
    _dialog = UpdatePricesDialog(mock_product_service, parent=None) 
    return _dialog

def test_dialog_creation_loads_departments(dialog: UpdatePricesDialog, mock_product_service: MagicMock):
    """Test that departments are loaded into the combo box upon dialog creation."""
    mock_product_service.get_all_departments.assert_called_once()
    assert dialog.department_combo.count() == 3 # "All Departments" + 2 mocked depts
    assert dialog.department_combo.itemText(0) == "Todos los Departamentos"
    assert dialog.department_combo.itemData(0) is None
    assert dialog.department_combo.itemText(1) == "Electronics"
    assert dialog.department_combo.itemData(1) == 1
    assert dialog.department_combo.itemText(2) == "Books"
    assert dialog.department_combo.itemData(2) == 2

def test_get_percentage_valid(dialog: UpdatePricesDialog):
    """Test valid percentage inputs."""
    dialog.percentage_input.setText("10.5")
    assert dialog.get_percentage() == Decimal("10.5")
    dialog.percentage_input.setText("-5")
    assert dialog.get_percentage() == Decimal("-5")
    dialog.percentage_input.setText("0")
    assert dialog.get_percentage() == Decimal("0")
    dialog.percentage_input.setText("1,5") # Comma as decimal separator
    assert dialog.get_percentage() == Decimal("1.5")

def test_get_percentage_invalid(dialog: UpdatePricesDialog, mocker):
    """Test invalid percentage inputs."""
    mocker.patch.object(QMessageBox, 'warning')

    dialog.percentage_input.setText("")
    assert dialog.get_percentage() is None
    QMessageBox.warning.assert_called_with(dialog, "Entrada Inválida", "Por favor ingrese un porcentaje.")

    dialog.percentage_input.setText("abc")
    assert dialog.get_percentage() is None
    QMessageBox.warning.assert_called_with(dialog, "Entrada Inválida", "Porcentaje inválido. Use números (ej: 10.5 o -5).")

    dialog.percentage_input.setText("-100") # Boundary value, should be invalid as per dialog logic
    assert dialog.get_percentage() is None
    QMessageBox.warning.assert_called_with(dialog, "Entrada Inválida", "El porcentaje debe ser mayor que -100%.")

    dialog.percentage_input.setText("-101")
    assert dialog.get_percentage() is None
    QMessageBox.warning.assert_called_with(dialog, "Entrada Inválida", "El porcentaje debe ser mayor que -100%.")

def test_accept_successful_update_all_departments(dialog: UpdatePricesDialog, mock_product_service: MagicMock, mocker):
    """Test successful update for all departments."""
    mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes)
    mocker.patch.object(QMessageBox, 'information')
    mocker.patch.object(dialog, 'accept', wraps=dialog.accept) # Use wraps for super().accept()
    mocker.patch.object(QDialog, 'accept') # Mock the base QDialog.accept

    dialog.percentage_input.setText("15.5")
    dialog.department_combo.setCurrentIndex(0) # "Todos los Departamentos"

    dialog.accept() # Call the accept slot directly

    QMessageBox.question.assert_called_once()
    # Check parts of the message to be somewhat flexible with exact wording
    call_args = QMessageBox.question.call_args[0]
    message = call_args[2]  # The message is the third argument (index 2)
    assert "un 15.5%" in message
    assert "TODOS los productos?" in message
    
    mock_product_service.update_prices_by_percentage.assert_called_once_with(Decimal("15.5"), None)
    QMessageBox.information.assert_called_once_with(dialog, "Éxito", "Se actualizaron los precios de 5 producto(s).")
    QDialog.accept.assert_called_once() # Check that super().accept() was called from within dialog.accept()

def test_accept_successful_update_specific_department(dialog: UpdatePricesDialog, mock_product_service: MagicMock, mocker):
    """Test successful update for a specific department."""
    mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes)
    mocker.patch.object(QMessageBox, 'information')
    mocker.patch.object(dialog, 'accept', wraps=dialog.accept)
    mocker.patch.object(QDialog, 'accept')

    dialog.percentage_input.setText("-8")
    dialog.department_combo.setCurrentIndex(1) # "Electronics", ID 1

    dialog.accept()

    QMessageBox.question.assert_called_once()
    # Check parts of the message to be somewhat flexible with exact wording
    call_args = QMessageBox.question.call_args[0]
    message = call_args[2]  # The message is the third argument (index 2)
    assert "un -8%" in message
    assert "departamento 'Electronics'?" in message
    
    mock_product_service.update_prices_by_percentage.assert_called_once_with(Decimal("-8"), 1)
    QMessageBox.information.assert_called_once_with(dialog, "Éxito", "Se actualizaron los precios de 5 producto(s).")
    QDialog.accept.assert_called_once()

def test_accept_user_cancels_confirmation(dialog: UpdatePricesDialog, mock_product_service: MagicMock, mocker):
    """Test when the user cancels at the confirmation step."""
    mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.No) # User clicks No
    mocker.patch.object(QMessageBox, 'information')
    mocker.patch.object(QDialog, 'accept')

    dialog.percentage_input.setText("5")
    dialog.accept()

    QMessageBox.question.assert_called_once()
    mock_product_service.update_prices_by_percentage.assert_not_called()
    QMessageBox.information.assert_not_called()
    QDialog.accept.assert_not_called() # Dialog should not be accepted

def test_accept_invalid_percentage_prevents_update(dialog: UpdatePricesDialog, mock_product_service: MagicMock, mocker):
    """Test that an invalid percentage prevents the update process."""
    mocker.patch.object(QMessageBox, 'warning')
    mocker.patch.object(QMessageBox, 'question')
    mocker.patch.object(QDialog, 'accept')

    dialog.percentage_input.setText("invalid") # Invalid input
    dialog.accept()

    QMessageBox.warning.assert_called_once()
    QMessageBox.question.assert_not_called()
    mock_product_service.update_prices_by_percentage.assert_not_called()
    QDialog.accept.assert_not_called()

def test_accept_service_raises_value_error(dialog: UpdatePricesDialog, mock_product_service: MagicMock, mocker):
    """Test handling of ValueError from the product service."""
    mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes)
    mocker.patch.object(QMessageBox, 'critical')
    mocker.patch.object(QDialog, 'accept')
    
    mock_product_service.update_prices_by_percentage.side_effect = ValueError("Service validation failed")

    dialog.percentage_input.setText("20")
    dialog.accept()

    mock_product_service.update_prices_by_percentage.assert_called_once()
    QMessageBox.critical.assert_called_once_with(dialog, "Error de Validación", "Service validation failed")
    QDialog.accept.assert_not_called() # Dialog should not be accepted on error

def test_accept_service_raises_generic_exception(dialog: UpdatePricesDialog, mock_product_service: MagicMock, mocker):
    """Test handling of a generic Exception from the product service."""
    mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes)
    mocker.patch.object(QMessageBox, 'critical')
    mocker.patch.object(QDialog, 'accept')

    mock_product_service.update_prices_by_percentage.side_effect = Exception("Something went wrong")

    dialog.percentage_input.setText("25")
    dialog.accept()

    mock_product_service.update_prices_by_percentage.assert_called_once()
    QMessageBox.critical.assert_called_once_with(dialog, "Error", "Ocurrió un error al actualizar los precios: Something went wrong")
    QDialog.accept.assert_not_called()

# Test the static run method (optional, but good for coverage)
def test_run_update_prices_dialog_accepted(mocker, mock_product_service):
    mocker.patch.object(UpdatePricesDialog, 'exec', return_value=QDialog.Accepted)
    mocker.patch("ui.dialogs.update_prices_dialog.UpdatePricesDialog.__init__", return_value=None) # Mock __init__ to prevent actual creation for this static test
    
    result = UpdatePricesDialog.run_update_prices_dialog(mock_product_service, parent=None)
    assert result is True
    # UpdatePricesDialog.__init__.assert_called_once_with(mock_product_service, None) # Check dialog was instantiated
    # Cannot assert __init__ this way easily if exec is also on UpdatePricesDialog itself.
    # We are essentially testing if exec() == QDialog.Accepted part.

def test_run_update_prices_dialog_rejected(mocker, mock_product_service):
    mocker.patch.object(UpdatePricesDialog, 'exec', return_value=QDialog.Rejected)
    mocker.patch("ui.dialogs.update_prices_dialog.UpdatePricesDialog.__init__", return_value=None)

    result = UpdatePricesDialog.run_update_prices_dialog(mock_product_service, parent=None)
    assert result is False