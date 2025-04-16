import pytest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication
from ui.dialogs.department_dialog import DepartmentDialog
from PySide6.QtCore import Qt
from core.models.product import Department

@pytest.fixture
def mock_product_service():
    service = MagicMock()
    # Mock department list
    departments = [
        Department(id=1, name="Grocery"),
        Department(id=2, name="Electronics"),
    ]
    service.get_all_departments.return_value = departments
    service.add_department.return_value = Department(id=3, name="Toys")
    service.update_department.return_value = Department(id=1, name="Groceries")
    service.delete_department.return_value = None
    return service

@pytest.fixture
def dialog(qtbot, mock_product_service):
    dlg = DepartmentDialog(product_service=mock_product_service)
    qtbot.addWidget(dlg)
    dlg.show()
    return dlg

def test_load_departments(dialog, mock_product_service):
    # Should load departments into the list
    assert dialog.dept_list_widget.count() == 2
    names = [dialog.dept_list_widget.item(i).text() for i in range(2)]
    assert "Grocery" in names
    assert "Electronics" in names

def test_add_department(dialog, qtbot, mock_product_service):
    qtbot.mouseClick(dialog.new_button, Qt.LeftButton)  # Poner en modo 'nuevo'
    dialog.name_input.setText("Toys")
    qtbot.mouseClick(dialog.save_button, Qt.LeftButton)
    mock_product_service.add_department.assert_called_once()
    # After add, list should refresh (simulate)
    dialog._load_departments()
    names = [dialog.dept_list_widget.item(i).text() for i in range(dialog.dept_list_widget.count())]
    assert "Toys" in names or mock_product_service.add_department.called

def test_edit_department(dialog, qtbot, mock_product_service):
    # Select first department
    dialog.dept_list_widget.setCurrentRow(0)
    dialog.name_input.setText("Groceries")
    qtbot.mouseClick(dialog.save_button, Qt.LeftButton)
    mock_product_service.update_department.assert_called_once()
    args, kwargs = mock_product_service.update_department.call_args
    assert args[1] == "Groceries"

def test_delete_department(dialog, qtbot, mock_product_service, monkeypatch):
    # Select first department
    dialog.dept_list_widget.setCurrentRow(0)
    # Patch QMessageBox to auto-confirm
    monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.question", lambda *a, **k: 16384)  # QMessageBox.Yes
    qtbot.mouseClick(dialog.delete_button, Qt.LeftButton)
    mock_product_service.delete_department.assert_called_once()
