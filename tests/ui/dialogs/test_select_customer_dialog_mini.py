"""
Minimal test cases for SelectCustomerDialog.

These tests cover only the most critical functionality.
"""
import pytest
from PySide6.QtWidgets import QTableView
from ui.dialogs.select_customer_dialog import SelectCustomerDialog

def test_empty_customer_list(qtbot):
    """Dialog should handle empty customer list gracefully."""
    dialog = SelectCustomerDialog(customers=[])
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitForWindowShown(dialog)

    table = dialog.findChild(QTableView)
    model = table.model().sourceModel()
    assert model.rowCount() == 0, "Table should be empty when no customers are provided"

    # Try to accept without selection
    dialog.accept()
    selected = dialog.get_selected_customer()
    assert selected is None, "No customer should be selected if list is empty"