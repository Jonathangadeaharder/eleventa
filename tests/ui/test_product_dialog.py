import pytest
from PySide6 import QtWidgets
from ui.dialogs.product_dialog import ProductDialog
from core.models.product import Product

class MockProductService:
    def __init__(self):
        self.added_product = None
        self.updated_product = None
        self.departments = [
            {"id": 1, "name": "Beverages"},
            {"id": 2, "name": "Snacks"},
        ]

    def get_departments(self):
        return self.departments

    def add_product(self, product):
        self.added_product = product
        return True

    def update_product(self, product):
        self.updated_product = product
        return True

@pytest.fixture
def product_service():
    return MockProductService()

@pytest.fixture
def dialog_add_mode(qtbot, product_service):
    dlg = ProductDialog(product_service=product_service, mode="add")
    qtbot.addWidget(dlg)
    return dlg

@pytest.fixture
def dialog_edit_mode(qtbot, product_service):
    product = Product(
        code="P001",
        description="Test Product",
        price=10.0,
        department_id=1,
        control_stock=True,
        stock=50,
        min_stock=5,
        active=True,
    )
    dlg = ProductDialog(product_service=product_service, mode="edit", product=product)
    qtbot.addWidget(dlg)
    return dlg

def test_form_population_add_mode(dialog_add_mode):
    assert dialog_add_mode.windowTitle() == "Agregar Producto"
    assert dialog_add_mode.code_edit.text() == ""
    assert dialog_add_mode.description_edit.text() == ""
    assert dialog_add_mode.price_spin.value() == 0.0

def test_form_population_edit_mode(dialog_edit_mode):
    assert dialog_edit_mode.windowTitle() == "Modificar Producto"
    assert dialog_edit_mode.code_edit.text() == "P001"
    assert dialog_edit_mode.description_edit.text() == "Test Product"
    assert dialog_edit_mode.price_spin.value() == 10.0
    assert dialog_edit_mode.department_combo.currentText() == "Beverages"
    assert dialog_edit_mode.stock_spin.value() == 50
    assert dialog_edit_mode.min_stock_spin.value() == 5
    assert dialog_edit_mode.active_checkbox.isChecked()

def test_validation_empty_code(qtbot, dialog_add_mode):
    dialog_add_mode.code_edit.setText("")
    dialog_add_mode.description_edit.setText("Some Description")
    dialog_add_mode.price_spin.setValue(5.0)
    with qtbot.waitSignal(dialog_add_mode.validation_failed, timeout=1000):
        dialog_add_mode.accept()

def test_validation_negative_price(qtbot, dialog_add_mode):
    dialog_add_mode.code_edit.setText("P002")
    dialog_add_mode.description_edit.setText("Some Description")
    dialog_add_mode.price_spin.setValue(-1.0)
    with qtbot.waitSignal(dialog_add_mode.validation_failed, timeout=1000):
        dialog_add_mode.accept()

def test_state_change_control_stock(qtbot, dialog_add_mode):
    # Uncheck "Controlar Stock" and check that stock fields are hidden
    dialog_add_mode.control_stock_checkbox.setChecked(False)
    assert not dialog_add_mode.stock_spin.isVisible()
    assert not dialog_add_mode.min_stock_spin.isVisible()
    # Check "Controlar Stock" and check that stock fields are visible
    dialog_add_mode.control_stock_checkbox.setChecked(True)
    assert dialog_add_mode.stock_spin.isVisible()
    assert dialog_add_mode.min_stock_spin.isVisible()

def test_service_call_add_product(qtbot, dialog_add_mode, product_service):
    dialog_add_mode.code_edit.setText("P003")
    dialog_add_mode.description_edit.setText("New Product")
    dialog_add_mode.price_spin.setValue(12.5)
    dialog_add_mode.department_combo.setCurrentIndex(1)  # "Beverages"
    dialog_add_mode.control_stock_checkbox.setChecked(True)
    dialog_add_mode.stock_spin.setValue(20)
    dialog_add_mode.min_stock_spin.setValue(2)
    dialog_add_mode.active_checkbox.setChecked(True)
    # Simulate accept
    dialog_add_mode.accept()
    assert product_service.added_product is not None
    assert product_service.added_product.code == "P003"
    assert product_service.added_product.description == "New Product"
    assert product_service.added_product.price == 12.5
    assert product_service.added_product.department_id == 1
    assert product_service.added_product.control_stock is True
    assert product_service.added_product.stock == 20
    assert product_service.added_product.min_stock == 2
    assert product_service.added_product.active is True

def test_service_call_update_product(qtbot, dialog_edit_mode, product_service):
    dialog_edit_mode.description_edit.setText("Updated Product")
    dialog_edit_mode.price_spin.setValue(15.0)
    # Simulate accept
    dialog_edit_mode.accept()
    assert product_service.updated_product is not None
    assert product_service.updated_product.description == "Updated Product"
    assert product_service.updated_product.price == 15.0
