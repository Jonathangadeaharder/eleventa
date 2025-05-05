 # Robust tests for SelectCustomerDialog matching actual implementation
import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit, QTableView, QPushButton
from PySide6.QtCore import QItemSelectionModel

from ui.dialogs.select_customer_dialog import SelectCustomerDialog
from core.models.customer import Customer

@pytest.fixture
def sample_customers():
    return [
        Customer(id=1, name="John Doe", email="john@example.com"),
        Customer(id=2, name="Jane Smith", email="jane@example.com")
    ]

@pytest.fixture
def dialog(qtbot, sample_customers):
    dialog = SelectCustomerDialog(customers=sample_customers)
    qtbot.addWidget(dialog)
    return dialog

def test_dialog_initialization(dialog):
    """Test dialog initializes with correct UI elements"""
    assert dialog.windowTitle() == "Seleccionar Cliente"
    assert dialog.findChild(QLineEdit).placeholderText() == "Nombre, teléfono, email..."
    assert dialog.findChild(QTableView).model() is not None

def test_customer_loading(dialog, sample_customers):
    """Test customers are loaded into table"""
    table = dialog.findChild(QTableView)
    model = table.model().sourceModel()  # Get through proxy model
    assert model.rowCount() == 2
    
    # Verify first customer data
    assert model.item(0, 0).text() == "John Doe"
    assert model.item(0, 2).text() == "john@example.com"
    assert model.item(0, 0).data(Qt.UserRole) == sample_customers[0]

def test_customer_selection(dialog, sample_customers, qtbot):
    """Test selecting a customer"""
    table = dialog.findChild(QTableView)
    # Select first row
    table.selectRow(0)
    # Find the 'Seleccionar' button by text
    select_button = None
    for btn in dialog.findChildren(QPushButton):
        if btn.text().lower() == "seleccionar":
            select_button = btn
            break
    assert select_button is not None, "Seleccionar button not found"
    qtbot.mouseClick(select_button, Qt.LeftButton)
    # After clicking, dialog should be accepted and customer selected
    selected = dialog.get_selected_customer()
    assert selected == sample_customers[0]

def test_customer_filtering(dialog, qtbot):
    """Test customer search functionality"""
    search_input = dialog.findChild(QLineEdit)
    search_input.setText("John")
    qtbot.keyClick(search_input, Qt.Key_Enter)
    
    # Verify filtering
    proxy_model = dialog.findChild(QTableView).model()
    assert proxy_model.rowCount() == 1  # Should filter to just John Doe