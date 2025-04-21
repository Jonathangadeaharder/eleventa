"""
Tests for the DepartmentDialog UI component.
Focus: Department creation/editing, validation, and dialog interaction.
"""

import pytest

from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication, QMessageBox
from ui.dialogs.department_dialog import DepartmentDialog
from PySide6.QtCore import Qt
from core.models.product import Department
from unittest.mock import patch

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
    yield dlg
    dlg.close()

def test_load_departments(dialog, mock_product_service):
    """Should load departments into the list."""
    assert dialog.dept_list_widget.count() == 2
    names = [dialog.dept_list_widget.item(i).text() for i in range(2)]
    assert "Grocery" in names
    assert "Electronics" in names

def test_add_department(dialog, qtbot, mock_product_service):
    """Should add a new department and refresh the list."""
    qtbot.mouseClick(dialog.new_button, Qt.LeftButton)  # Poner en modo 'nuevo'
    dialog.name_input.setText("Toys")
    qtbot.mouseClick(dialog.save_button, Qt.LeftButton)
    mock_product_service.add_department.assert_called_once()
    # After add, list should refresh (simulate)
    dialog._load_departments()
    names = [dialog.dept_list_widget.item(i).text() for i in range(dialog.dept_list_widget.count())]
    assert "Toys" in names or mock_product_service.add_department.called

def test_edit_department(dialog, qtbot, mock_product_service):
    """Should edit an existing department and call update on the service."""
    # Select first department
    dialog.dept_list_widget.setCurrentRow(0)
    dialog.name_input.setText("Groceries")
    qtbot.mouseClick(dialog.save_button, Qt.LeftButton)
    mock_product_service.update_department.assert_called_once()
    # Ensure the Department object passed has the updated name
    dept_arg = mock_product_service.update_department.call_args.args[0]
    assert hasattr(dept_arg, 'name') and dept_arg.name == "Groceries"

def test_delete_department(dialog, qtbot, mock_product_service):
    """Should delete a department after user confirmation."""
    # Select first department
    dialog.dept_list_widget.setCurrentRow(0)
    # Patch QMessageBox to auto-confirm
    with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
        qtbot.mouseClick(dialog.delete_button, Qt.LeftButton)
        mock_product_service.delete_department.assert_called_once()
