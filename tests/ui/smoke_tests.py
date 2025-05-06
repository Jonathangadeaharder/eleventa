"""
UI Smoke Tests
--------------
This file contains critical path tests that verify the most important UI workflows.

These tests are designed to be stable and reliable, avoiding access violations
and crashes that can occur with more comprehensive UI testing.

The focus is on testing minimal but critical user workflows to ensure core
functionality works as expected.

Run these tests with: pytest tests/ui/smoke_tests.py -v
"""

import pytest
import sys
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QDialog, QPushButton, QMessageBox, QTableView, QLineEdit
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex

from ui.dialogs.select_customer_dialog import SelectCustomerDialog
from ui.dialogs.cash_drawer_dialogs import OpenCashDrawerDialog
from ui.utils import style_text_input
from tests.ui.qt_test_utils import (
    process_events, safe_click_button, 
    safely_apply_styles, with_timeout,
    safely_test_styling_function
)

# Mark all tests in this file as smoke tests
pytestmark = [pytest.mark.smoke, pytest.mark.timeout(10)]


@pytest.fixture
def mock_customer_service():
    """Create a mock customer service with test data."""
    service = MagicMock()
    service.get_all_customers.return_value = [
        MagicMock(id=1, name="Customer 1", cuit="20-12345678-9"),
        MagicMock(id=2, name="Customer 2", cuit="20-87654321-9")
    ]
    service.search_customers.return_value = service.get_all_customers.return_value
    return service


@pytest.fixture
def mock_cash_drawer_service():
    """Create a mock cash drawer service."""
    service = MagicMock()
    service.open_drawer.return_value = True
    return service


@pytest.mark.xfail(reason="This test might fail in CI environments without proper QPA setup", strict=False)
def test_select_customer_dialog_smoke(qtbot, mock_customer_service):
    """
    Smoke test for customer selection workflow.
    
    Verifies that:
    1. The dialog can be instantiated
    2. Customer data is loaded and displayed
    3. Basic navigation and selection works
    """
    # Create the dialog with mock service
    dialog = SelectCustomerDialog(mock_customer_service)
    qtbot.addWidget(dialog)
    
    try:
        # Show dialog but don't wait for exposure
        dialog.show()
        process_events()
        
        # Verify customer service was called to load data
        mock_customer_service.get_all_customers.assert_called_once()
        
        # Verify dialog structure
        assert dialog.windowTitle() == "Seleccionar Cliente"
        
        # Test that customer search works by directly calling the method
        dialog.search_for_customers("Customer")
        mock_customer_service.search_customers.assert_called_with("Customer")
        
        # Test selection by setting the selection directly rather than clicking
        dialog.customer_table.selectRow(0)
        process_events()
        
        # Verify that a customer is selected
        assert dialog.get_selected_customer() is not None
        
        # Test dialog acceptance
        dialog.accept()
        process_events()
        
        # Verify dialog result
        assert dialog.result() == QDialog.Accepted
        
    finally:
        # Clean up resources
        dialog.hide()
        process_events()
        dialog.deleteLater()
        process_events()


@pytest.mark.xfail(reason="This test might fail in CI environments without proper QPA setup", strict=False)
def test_cash_drawer_dialog_smoke(qtbot, mock_cash_drawer_service):
    """
    Smoke test for cash drawer dialog.
    
    Verifies that:
    1. The dialog can be instantiated
    2. Amount and description fields work
    3. The dialog can be accepted/rejected
    """
    # Create the dialog with mock service
    dialog = OpenCashDrawerDialog(mock_cash_drawer_service)
    qtbot.addWidget(dialog)
    
    try:
        # Show dialog but don't wait for exposure
        dialog.show()
        process_events()
        
        # Verify dialog structure and defaults
        assert dialog.windowTitle() == "Abrir Caja"
        ok_button = dialog.get_ok_button()
        assert ok_button is not None
        
        # Set values directly instead of simulating input
        dialog.amount_input.setValue(1000.0)
        dialog.description_input.setText("Test opening")
        process_events()
        
        # Test dialog acceptance using direct signal
        safe_click_button(ok_button)
        process_events()
        
        # Verify service was called with correct values
        mock_cash_drawer_service.open_drawer.assert_called_with(1000.0, "Test opening")
        
    finally:
        # Clean up resources
        dialog.hide()
        process_events()
        dialog.deleteLater()
        process_events()


def test_text_input_styling(qtbot):
    """
    Smoke test for text input styling.
    
    Verifies that:
    1. The styling function can be applied without errors
    2. The expected styling is applied to the widget
    """
    # Use our safe styling test utility
    input_widget, _ = safely_test_styling_function(qtbot, QLineEdit, style_text_input)
    
    # Check that styling was applied correctly
    assert input_widget.styleSheet() != ""
    assert "border: 1px solid #cccccc" in input_widget.styleSheet()
    assert "border-radius: 4px" in input_widget.styleSheet()
    assert input_widget.minimumHeight() == 28


class TestBasicUIComponents:
    """Tests for basic UI components that don't require actual UI rendering."""
    
    class SimpleTableModel(QAbstractTableModel):
        """A simple table model for testing."""
        
        def __init__(self, data=None):
            super().__init__()
            self._data = data or [["Item 1", 10], ["Item 2", 20]]
            self._headers = ["Name", "Value"]
            
        def rowCount(self, parent=QModelIndex()):
            return len(self._data)
            
        def columnCount(self, parent=QModelIndex()):
            return len(self._data[0]) if self._data else 0
            
        def data(self, index, role=Qt.DisplayRole):
            if role == Qt.DisplayRole:
                return str(self._data[index.row()][index.column()])
            return None
            
        def headerData(self, section, orientation, role=Qt.DisplayRole):
            if orientation == Qt.Horizontal and role == Qt.DisplayRole:
                return self._headers[section]
            return None
            
    def test_table_models(self):
        """Test that table models can be instantiated and function correctly."""
        # Create a simple table model
        model = self.SimpleTableModel()
        
        # Check basic properties
        assert model.rowCount() == 2
        assert model.columnCount() == 2
        
        # Check data retrieval
        assert model.data(model.index(0, 0), Qt.DisplayRole) == "Item 1"
        assert model.data(model.index(0, 1), Qt.DisplayRole) == "10"
        assert model.data(model.index(1, 0), Qt.DisplayRole) == "Item 2"
        assert model.data(model.index(1, 1), Qt.DisplayRole) == "20"
        
        # Check header data
        assert model.headerData(0, Qt.Horizontal, Qt.DisplayRole) == "Name"
        assert model.headerData(1, Qt.Horizontal, Qt.DisplayRole) == "Value" 