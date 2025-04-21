"""
Tests for the SelectCustomerDialog UI component.
Focus: Customer selection, search functionality, and dialog interaction.

This test suite verifies the functionality of the SelectCustomerDialog component, including:
- Dialog initialization and UI elements
- Customer listing and display
- Search and filtering functionality
- Customer selection and retrieval
- Dialog acceptance and rejection
"""

# Standard library imports
import sys
from decimal import Decimal

# Testing frameworks
import pytest
from unittest.mock import MagicMock, patch

# Qt components
from PySide6.QtWidgets import QDialog, QTableView, QApplication
from PySide6.QtCore import Qt, QModelIndex, QItemSelectionModel
from PySide6.QtGui import QStandardItem

# Application components
from ui.dialogs.select_customer_dialog import SelectCustomerDialog
from core.models.customer import Customer

# Test utilities
import patch_resources

# Set timeout to prevent hanging tests
pytestmark = pytest.mark.timeout(5)

# Test data generator
def create_test_customers():
    """Create a list of test customers for testing the dialog."""
    return [
        Customer(id=1, name="John Doe", phone="555-1234", email="john@example.com", 
                address="123 Main St", credit_balance=Decimal("100.00")),
        Customer(id=2, name="Jane Smith", phone="555-5678", email="jane@example.com", 
                address="456 Oak Ave", credit_balance=Decimal("250.75")),
        Customer(id=3, name="Robert Johnson", phone="555-9012", email="robert@example.com", 
                address="789 Pine Rd", credit_balance=Decimal("0.00")),
        Customer(id=4, name="Sarah Williams", phone="555-3456", email="sarah@example.com", 
                address="321 Elm Blvd", credit_balance=Decimal("75.50")),
    ]

@pytest.fixture
def test_customers():
    """Fixture to provide test customer data."""
    return create_test_customers()

@pytest.fixture
def select_customer_dialog(qtbot, test_customers):
    """
    Create a SelectCustomerDialog instance for testing.
    
    Parameters:
        qtbot: The Qt Robot test helper
        test_customers: List of test Customer objects
        
    Returns:
        A SelectCustomerDialog instance populated with test customers
    """
    dialog = SelectCustomerDialog(test_customers)
    qtbot.addWidget(dialog)
    dialog.show()
    # Use waitExposed instead of waitForWindowShown
    qtbot.waitExposed(dialog)
    
    yield dialog
    
    # Clean up
    dialog.close()
    dialog.deleteLater()
    QApplication.processEvents()

def test_dialog_initialization(select_customer_dialog):
    """
    Test that the dialog initializes correctly with all UI elements.
    
    Verifies that the dialog title, size, and main components are properly set up.
    """
    dialog = select_customer_dialog
    
    # Check dialog properties
    assert dialog.windowTitle() == "Seleccionar Cliente"
    assert dialog.minimumSize().width() >= 600
    assert dialog.minimumSize().height() >= 400
    
    # Check UI components
    assert dialog.search_edit is not None
    assert dialog.customer_table is not None
    assert dialog.cancel_button is not None
    assert dialog.select_button is not None
    
    # Check table model
    assert dialog.model is not None
    assert dialog.model.columnCount() == 5
    assert [dialog.model.headerData(i, Qt.Horizontal) for i in range(5)] == [
        "Nombre", "Teléfono", "Email", "Dirección", "Saldo"
    ]

def test_customers_populated(select_customer_dialog, test_customers):
    """
    Test that customers are properly populated in the table.
    
    Verifies that all test customers appear in the table with correct data.
    """
    dialog = select_customer_dialog
    
    # Check row count matches customer count
    assert dialog.model.rowCount() == len(test_customers)
    
    # Check first customer data
    customer = test_customers[0]
    row = 0
    assert dialog.model.item(row, 0).text() == customer.name
    assert dialog.model.item(row, 1).text() == customer.phone
    assert dialog.model.item(row, 2).text() == customer.email
    assert dialog.model.item(row, 3).text() == customer.address
    assert dialog.model.item(row, 4).text() == f"${customer.credit_balance:.2f}"
    
    # Check that customer object is stored in the model
    stored_customer = dialog.model.item(row, 0).data(Qt.UserRole)
    assert stored_customer is customer

def test_customer_search_filtering(select_customer_dialog, test_customers, qtbot, monkeypatch):
    """
    Test that the search functionality filters customers correctly.
    
    Verifies that entering search text properly filters the customer list.
    """
    dialog = select_customer_dialog
    
    # Override the filter_customers method to apply filtering directly
    original_filter = dialog.filter_customers
    
    def patched_filter():
        # Call original method
        original_filter()
        # Force the proxy model to update its filter
        dialog.proxy_model.invalidateFilter()
        QApplication.processEvents()
        
    monkeypatch.setattr(dialog, 'filter_customers', patched_filter)
    
    # Initial state - all customers visible
    assert dialog.proxy_model.rowCount() == len(test_customers)
    
    # Search by name (should match one customer)
    dialog.search_edit.setText("Jane")
    dialog.filter_customers()  # Call our patched method
    assert dialog.proxy_model.rowCount() == 1
    
    # Clear and search by email domain (should match all customers)
    dialog.search_edit.setText("")
    dialog.filter_customers()  # Call our patched method
    assert dialog.proxy_model.rowCount() == len(test_customers)
    
    # Search for a name that doesn't exist
    dialog.search_edit.setText("NONEXISTENT")
    dialog.filter_customers()  # Call our patched method
    assert dialog.proxy_model.rowCount() == 0

def test_customer_selection_and_accept(select_customer_dialog, test_customers, monkeypatch, qtbot):
    """
    Test selecting a customer and accepting the dialog.
    
    Verifies that selecting a row and accepting the dialog properly
    sets the selected customer.
    """
    dialog = select_customer_dialog
    
    # Mock QDialog.accept to prevent dialog from closing
    monkeypatch.setattr(QDialog, "accept", MagicMock())
    
    # Select the first customer manually
    index = dialog.proxy_model.index(0, 0)
    selection_model = dialog.customer_table.selectionModel()
    selection_model.select(index, QItemSelectionModel.SelectCurrent | QItemSelectionModel.Rows)
    qtbot.wait(10) # Short wait for selection to register

    # Simulate clicking the select button instead of calling accept directly
    qtbot.mouseClick(dialog.select_button, Qt.LeftButton)
    qtbot.wait(10) # Short wait for accept signal processing

    # Check that the selected customer is correct
    assert dialog.selected_customer is test_customers[0]
    assert dialog.get_selected_customer() is test_customers[0]

def test_customer_selection_by_double_click(select_customer_dialog, test_customers, monkeypatch):
    """
    Test selecting a customer by double-clicking.
    
    Verifies that double-clicking a row properly sets the selected customer
    and accepts the dialog.
    """
    dialog = select_customer_dialog
    
    # Mock QDialog.accept to prevent dialog from closing
    monkeypatch.setattr(QDialog, "accept", MagicMock())
    
    # Select the second customer manually
    index = dialog.proxy_model.index(1, 0)
    selection_model = dialog.customer_table.selectionModel()
    selection_model.select(index, QItemSelectionModel.SelectCurrent | QItemSelectionModel.Rows)
    qtbot.wait(10) # Short wait for selection

    # Simulate double-click on the table view cell
    qtbot.mouseDClick(dialog.customer_table.viewport(), Qt.LeftButton, pos=dialog.customer_table.visualRect(index).center())
    qtbot.wait(10) # Short wait for accept signal processing

    # Check that the selected customer is correct
    assert dialog.selected_customer is test_customers[1]
    assert dialog.get_selected_customer() is test_customers[1]

def test_cancel_returns_none(select_customer_dialog, monkeypatch):
    """
    Test that canceling the dialog returns no selected customer.
    
    Verifies that rejecting the dialog results in no customer being selected.
    """
    dialog = select_customer_dialog
    
    # Mock QDialog.reject to prevent dialog from closing
    monkeypatch.setattr(QDialog, "reject", MagicMock())
    
    # Call reject directly
    dialog.reject()
    QApplication.processEvents()
    
    # Check that no customer is selected
    assert dialog.selected_customer is None
    assert dialog.get_selected_customer() is None

def test_no_selection_returns_none(select_customer_dialog, monkeypatch):
    """
    Test that accepting without selection returns no customer.
    
    Verifies that accepting the dialog without selecting a row
    results in no customer being selected.
    """
    dialog = select_customer_dialog
    
    # Mock QDialog.accept to prevent dialog from closing
    monkeypatch.setattr(QDialog, "accept", MagicMock())
    
    # Ensure no selection
    dialog.customer_table.clearSelection()
    qtbot.wait(10) # Ensure selection is cleared

    # Simulate clicking the select button with no selection
    qtbot.mouseClick(dialog.select_button, Qt.LeftButton)
    qtbot.wait(10) # Short wait for accept signal processing

    # Check that no customer is selected
    assert dialog.selected_customer is None
    assert dialog.get_selected_customer() is None

def test_search_and_select(select_customer_dialog, test_customers, monkeypatch):
    """
    Test searching and then selecting a filtered customer.
    
    Verifies that searching for a customer, then selecting from the filtered
    results works correctly.
    """
    dialog = select_customer_dialog
    
    # Mock QDialog.accept to prevent dialog from closing
    monkeypatch.setattr(QDialog, "accept", MagicMock())
    
    # Override the filter_customers method to apply filtering directly
    original_filter = dialog.filter_customers
    
    def patched_filter():
        # Call original method
        original_filter()
        # Force the proxy model to update its filter
        dialog.proxy_model.invalidateFilter()
        QApplication.processEvents()
        
    monkeypatch.setattr(dialog, 'filter_customers', patched_filter)
    
    # Search for "Robert"
    dialog.search_edit.setText("Robert")
    dialog.filter_customers()  # Call our patched method
    assert dialog.proxy_model.rowCount() == 1
    
    # Select the filtered customer
    index = dialog.proxy_model.index(0, 0)
    selection_model = dialog.customer_table.selectionModel()
    selection_model.select(index, QItemSelectionModel.SelectCurrent | QItemSelectionModel.Rows)
    qtbot.wait(10) # Short wait for selection

    # Simulate clicking the select button after filtering and selecting
    qtbot.mouseClick(dialog.select_button, Qt.LeftButton)
    qtbot.wait(10) # Short wait for accept signal processing

    # Check that the selected customer is correct
    assert dialog.selected_customer.name == "Robert Johnson"
    assert dialog.selected_customer is test_customers[2]
