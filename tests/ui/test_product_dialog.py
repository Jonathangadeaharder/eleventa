import pytest
import patch_qt_tests  # Import patch to prevent Qt dialogs from blocking
from PySide6 import QtWidgets
from PySide6.QtWidgets import QGroupBox, QMessageBox
from ui.dialogs.product_dialog import ProductDialog
from core.models.product import Product
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QApplication

class MockProductService:
    def __init__(self):
        self.added_product = None
        self.updated_product = None
        self.departments = [
            {"id": 1, "name": "Beverages"},
            {"id": 2, "name": "Snacks"},
        ]

    def get_departments(self):
        """Legacy method, keep for backward compatibility"""
        return self.departments

    def add_product(self, product):
        self.added_product = product
        return product

    def update_product(self, product):
        self.updated_product = product
        return product

    def find_product(self, search_term=None):
        return []

    def get_all_products(self, department_id=None):
        return []

    def get_all_departments(self):
        """Method called by ProductDialog to load departments"""
        return [
            type("Department", (), {"id": 1, "name": "Beverages"})(),
            type("Department", (), {"id": 2, "name": "Snacks"})(),
        ]

@pytest.fixture
def product_service():
    return MockProductService()

@pytest.fixture
def dialog_add_mode(qtbot, product_service):
    dlg = ProductDialog(product_service=product_service)
    qtbot.addWidget(dlg)
    return dlg

@pytest.fixture
def dialog_edit_mode(qtbot, product_service):
    product = Product(
        code="P001",
        description="Test Product",
        sell_price=10.0,
        department_id=1,
        uses_inventory=True,
        quantity_in_stock=50,
        min_stock=5,
        is_active=True,
    )
    dlg = ProductDialog(product_service=product_service, product_to_edit=product)
    qtbot.addWidget(dlg)
    return dlg

def test_form_population_add_mode(dialog_add_mode):
    assert dialog_add_mode.windowTitle() == "Agregar Producto"
    assert dialog_add_mode.code_input.text() == ""
    assert dialog_add_mode.description_input.text() == ""
    assert dialog_add_mode.sale_price_input.value() == 0.0

def test_form_population_edit_mode(dialog_edit_mode):
    assert dialog_edit_mode.windowTitle() == "Modificar Producto"
    assert dialog_edit_mode.code_input.text() == "P001"
    assert dialog_edit_mode.description_input.text() == "Test Product"
    assert dialog_edit_mode.sale_price_input.value() == 10.0
    assert dialog_edit_mode.department_combo.currentText() == "Beverages"
    assert dialog_edit_mode.stock_input.value() == 50
    assert dialog_edit_mode.min_stock_input.value() == 5
    assert dialog_edit_mode.inventory_checkbox.isChecked()

def test_validation_empty_code(qtbot, dialog_add_mode):
    dialog_add_mode.code_input.setText("")
    dialog_add_mode.description_input.setText("Some Description")
    dialog_add_mode.sale_price_input.setValue(5.0)
    with qtbot.waitSignal(dialog_add_mode.validation_failed, timeout=1000):
        dialog_add_mode.accept()

def test_validation_negative_price(qtbot, dialog_add_mode):
    dialog_add_mode.code_input.setText("P002")
    dialog_add_mode.description_input.setText("Some Description")
    dialog_add_mode.sale_price_input.setRange(-999999.99, 999999.99)
    dialog_add_mode.sale_price_input.setValue(-1.0)
    with qtbot.waitSignal(dialog_add_mode.validation_failed, timeout=1000):
        dialog_add_mode.accept()

def test_state_change_control_stock(qtbot, dialog_add_mode):
    # Ensure the dialog is visible to start with
    dialog_add_mode.show()
    qtbot.waitForWindowShown(dialog_add_mode)
    
    # First test: uncheck inventory control
    dialog_add_mode.inventory_checkbox.setChecked(False)
    
    # Make sure the change is fully processed
    qtbot.wait(200)  # Increased wait time
    QApplication.processEvents()
    
    # Verify fields are hidden
    assert not dialog_add_mode.stock_input.isVisible()
    assert not dialog_add_mode.min_stock_input.isVisible()
    
    # Second test: check inventory control
    dialog_add_mode.inventory_checkbox.setChecked(True)
    
    # Make sure the change is fully processed - multiple processing steps to ensure UI updates
    qtbot.wait(200)  # Increased wait time 
    QApplication.processEvents()
    qtbot.wait(100)  # Additional wait
    QApplication.processEvents()
    
    # Debug output if needed
    print(f"Stock input visibility: {dialog_add_mode.stock_input.isVisible()}")
    print(f"Min stock input visibility: {dialog_add_mode.min_stock_input.isVisible()}")
    
    # Verify fields are now visible
    assert dialog_add_mode.stock_input.isVisible()
    assert dialog_add_mode.min_stock_input.isVisible()

def test_service_call_add_product(qtbot, dialog_add_mode, product_service):
    dialog_add_mode.code_input.setText("P003")
    dialog_add_mode.description_input.setText("New Product")
    dialog_add_mode.sale_price_input.setValue(12.5)
    dialog_add_mode.department_combo.setCurrentIndex(1)  # "Beverages"
    dialog_add_mode.inventory_checkbox.setChecked(True)
    dialog_add_mode.stock_input.setValue(20)
    dialog_add_mode.min_stock_input.setValue(2)
    dialog_add_mode.inventory_checkbox.setChecked(True)
    # Simulate accept
    dialog_add_mode.accept()
    assert product_service.added_product is not None
    assert product_service.added_product.code == "P003"
    assert product_service.added_product.description == "New Product"
    assert product_service.added_product.sell_price == 12.5
    assert product_service.added_product.department_id == 1
    assert product_service.added_product.uses_inventory is True
    assert product_service.added_product.quantity_in_stock == 20
    assert product_service.added_product.min_stock == 2
    assert product_service.added_product.is_active is True

def test_service_call_update_product(qtbot, dialog_edit_mode, product_service):
    dialog_edit_mode.description_input.setText("Updated Product")
    dialog_edit_mode.sale_price_input.setValue(15.0)
    # Simulate accept
    dialog_edit_mode.accept()
    assert product_service.updated_product is not None
    assert product_service.updated_product.description == "Updated Product"
    assert product_service.updated_product.sell_price == 15.0
