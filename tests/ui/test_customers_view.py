"""
Tests for the CustomersView UI component.
Focus: View loading, customer dialog field population, and data extraction.
"""

import pytest
from PySide6.QtWidgets import QApplication
from ui.views.customers_view import CustomersView
from ui.dialogs.customer_dialog import CustomerDialog
from core.services.customer_service import CustomerService

@pytest.fixture
def app(qtbot):
    # Ensure QApplication exists for widget tests
    return QApplication.instance() or QApplication([])

class DummyCustomerService(CustomerService):
    def __init__(self):
        pass
    def get_all_customers(self):
        return []
    def add_customer(self, *args, **kwargs):
        pass
    def update_customer(self, *args, **kwargs):
        pass
    def delete_customer(self, *args, **kwargs):
        pass

def test_customers_view_loads_and_has_buttons(app, qtbot):
    """Should load CustomersView and verify presence of buttons."""
    service = DummyCustomerService()
    view = CustomersView(service)
    qtbot.addWidget(view)
    view.show()
    assert view.table_view is not None
    assert hasattr(view, "add_button")
    assert hasattr(view, "edit_button")
    assert hasattr(view, "delete_button")
    assert hasattr(view, "register_payment_button")
    # Check that buttons are enabled/disabled as expected
    assert view.add_button.isEnabled()
    # Check that refresh_customers can be called without error
    view.refresh_customers()

def test_customer_dialog_fields_populate_and_extract(app, qtbot):
    """Should populate customer dialog fields and extract data correctly."""
    service = DummyCustomerService()
    dialog = CustomerDialog(service)
    qtbot.addWidget(dialog)
    dialog.show()
    # Simulate populating form with a customer
    customer = type("Customer", (), {
        "name": "Test User",
        "phone": "555-1234",
        "email": "test@example.com",
        "address": "123 Main St",
        "credit_limit": 100.0,
        "credit_balance": 10.0
    })()
    dialog._populate_form(customer)
    assert dialog.name_edit.text() == "Test User"
    assert dialog.phone_edit.text() == "555-1234"
    assert dialog.email_edit.text() == "test@example.com"
    assert dialog.address_edit.text() == "123 Main St"
    # Simulate extracting data from form
    data = dialog._get_customer_data_from_form()
    assert data["name"] == "Test User"
    assert data["phone"] == "555-1234"
    assert data["email"] == "test@example.com"
    assert data["address"] == "123 Main St"