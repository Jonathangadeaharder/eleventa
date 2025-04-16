import pytest
import patch_qt_tests  # Import patch to prevent Qt dialogs from blocking
from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import QMessageBox
from ui.dialogs.add_inventory_dialog import AddInventoryDialog
from core.models.product import Product

class MockInventoryService:
    def __init__(self):
        self.called = False
        self.call_args = None

    def add_inventory(self, product_id, quantity, new_cost_price, notes, user_id):
        self.called = True
        self.call_args = {
            "product_id": product_id,
            "quantity": quantity,
            "new_cost_price": new_cost_price,
            "notes": notes,
            "user_id": user_id,
        }
        # Simulate returning updated product
        return {"id": product_id, "quantity": quantity}

@pytest.fixture
def product():
    # Minimal product stub
    return Product(
        id=1,
        code="P100",
        description="Test Product",
        quantity_in_stock=10.0,
        unit="pcs",
        cost_price=5.0
    )

@pytest.fixture
def inventory_service():
    return MockInventoryService()

@pytest.fixture
def dialog(qtbot, inventory_service, product):
    dlg = AddInventoryDialog(inventory_service=inventory_service, product=product)
    qtbot.addWidget(dlg)
    return dlg

def test_fields_present_and_defaults(dialog, product):
    assert dialog.windowTitle() == f"Agregar Cantidad - {product.description}"
    assert dialog.code_label.text() == product.code
    assert dialog.desc_label.text() == product.description
    assert dialog.current_stock_label.text().startswith(str(product.quantity_in_stock))
    assert dialog.quantity_spinbox.value() == 1.0
    assert dialog.cost_spinbox.value() == product.cost_price
    assert dialog.notes_edit.toPlainText() == ""

def test_accept_valid_add_inventory(qtbot, dialog, inventory_service, product):
    dialog.quantity_spinbox.setValue(2.5)
    dialog.cost_spinbox.setValue(6.0)
    dialog.notes_edit.setPlainText("Reposición")
    # Simulate OK button click
    qtbot.mouseClick(dialog.button_box.button(dialog.button_box.StandardButton.Ok), QtCore.Qt.LeftButton)
    assert inventory_service.called
    args = inventory_service.call_args
    assert args["product_id"] == product.id
    assert args["quantity"] == 2.5
    assert args["new_cost_price"] == 6.0
    assert args["notes"] == "Reposición"
    assert args["user_id"] is None

def test_validation_quantity_must_be_positive(qtbot, dialog):
    dialog.quantity_spinbox.setRange(0.0, 999999.99)
    dialog.quantity_spinbox.setValue(0.0)
    called = {}
    def fake_show_error_message(parent, title, msg):
        called["called"] = True
        called["title"] = title
        called["msg"] = msg
    import ui.dialogs.add_inventory_dialog as add_inventory_dialog_mod
    from PySide6.QtWidgets import QMessageBox
    orig = add_inventory_dialog_mod.show_error_message
    orig_warning = QMessageBox.warning
    def fake_warning(*args, **kwargs):
        return QMessageBox.Ok
    QMessageBox.warning = fake_warning
    add_inventory_dialog_mod.show_error_message = fake_show_error_message
    try:
        AddInventoryDialog.accept(dialog)
        assert called.get("called", False)
        assert "mayor que cero" in called.get("msg", "")
    finally:
        add_inventory_dialog_mod.show_error_message = orig
        QMessageBox.warning = orig_warning