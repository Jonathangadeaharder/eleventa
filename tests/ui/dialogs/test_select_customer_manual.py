import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLineEdit, QTableView, QPushButton
from ui.dialogs.select_customer_dialog import SelectCustomerDialog
from core.models.customer import Customer

@pytest.fixture
def sample_customers():
    return [
        Customer(id=1, name="John Doe", email="john@example.com"),
        Customer(id=2, name="Jane Smith", email="jane@example.com"),
    ]

def test_select_customer_automated(qtbot, sample_customers):
    dialog = SelectCustomerDialog(customers=sample_customers)
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitForWindowShown(dialog)

    # Select the second customer in the table
    table = dialog.findChild(QTableView)
    table.selectRow(1)

    # Find the 'Seleccionar' button by text
    select_button = None
    for btn in dialog.findChildren(QPushButton):
        if btn.text().lower() == "seleccionar":
            select_button = btn
            break
    assert select_button is not None, "Seleccionar button not found"

    # Simulate clicking the select button
    qtbot.mouseClick(select_button, Qt.LeftButton)

    # Verify the correct customer is selected
    selected = dialog.get_selected_customer()
    assert selected == sample_customers[1]