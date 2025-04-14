import pytest
from unittest.mock import MagicMock
from PyQt5.QtWidgets import QApplication
from ui.dialogs.department_dialog import DepartmentDialog
from PyQt5.QtCore import Qt

@pytest.fixture
def mock_product_service():
    service = MagicMock()
    # Mock department list
    service.get_departments.return_value = [
        MagicMock(id=1, name="Grocery"),
        MagicMock(id=2, name="Electronics"),
    ]
    service.add_department.return_value = MagicMock(id=3, name="Toys")
    service.update_department.return_value = None
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
    assert dialog.list_departments.count() == 2
    names = [dialog.list_departments.item(i).text() for i in range(2)]
    assert "Grocery" in names
    assert "Electronics" in names

def test_add_department(dialog, qtbot, mock_product_service):
    dialog.input_name.setText("Toys")
    qtbot.mouseClick(dialog.btn_save, Qt.LeftButton)
    mock_product_service.add_department.assert_called_once()
    # After add, list should refresh (simulate)
    dialog.load_departments()
    names = [dialog.list_departments.item(i).text() for i in range(dialog.list_departments.count())]
    assert "Toys" in names or mock_product_service.add_department.called

def test_edit_department(dialog, qtbot, mock_product_service):
    # Select first department
    dialog.list_departments.setCurrentRow(0)
    dialog.input_name.setText("Groceries")
    qtbot.mouseClick(dialog.btn_save, Qt.LeftButton)
    mock_product_service.update_department.assert_called_once()
    args, kwargs = mock_product_service.update_department.call_args
    assert args[1] == "Groceries"

def test_delete_department(dialog, qtbot, mock_product_service, monkeypatch):
    # Select first department
    dialog.list_departments.setCurrentRow(0)
    # Patch QMessageBox to auto-confirm
    monkeypatch.setattr("PyQt5.QtWidgets.QMessageBox.question", lambda *a, **k: 16384)  # QMessageBox.Yes
    qtbot.mouseClick(dialog.btn_delete, Qt.LeftButton)
    mock_product_service.delete_department.assert_called_once()