"""
Tests for the ProductDialog UI component.
Focus: Adding/editing products, validation, and form population.
"""

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
    """Fixture for ProductDialog in add mode."""
    dlg = ProductDialog(product_service=product_service)
    qtbot.addWidget(dlg)
    yield dlg
    dlg.close()

@pytest.fixture
def dialog_edit_mode(qtbot, product_service):
    """Fixture for ProductDialog in edit mode."""
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
    yield dlg
    dlg.close()

@pytest.mark.skip(reason="Temporarily skipping due to persistent Qt crashes")
def test_form_population_add_mode(qtbot, dialog_add_mode):
    """Should verify form population in add mode."""
    assert dialog_add_mode.windowTitle() == "Agregar Producto"
    assert dialog_add_mode.code_input.text() == ""
    assert dialog_add_mode.description_input.text() == ""
    assert dialog_add_mode.sale_price_input.value() == 0.0

@pytest.mark.skip(reason="Temporarily skipping due to persistent Qt crashes")
def test_form_population_edit_mode(qtbot, dialog_edit_mode):
    """Should verify form population in edit mode."""
    assert dialog_edit_mode.windowTitle() == "Modificar Producto"
    assert dialog_edit_mode.code_input.text() == "P001"
    assert dialog_edit_mode.description_input.text() == "Test Product"
    assert dialog_edit_mode.sale_price_input.value() == 10.0
    assert dialog_edit_mode.department_combo.currentText() == "Beverages"
    assert dialog_edit_mode.stock_input.value() == 50
    assert dialog_edit_mode.min_stock_input.value() == 5
    assert dialog_edit_mode.inventory_checkbox.isChecked()

@pytest.mark.skip(reason="Temporarily skipping due to persistent Qt crashes")
def test_validation_empty_code(qtbot, dialog_add_mode):
    """Should trigger validation failed signal if code is empty."""
    validation_triggered = False
    def on_validation_failed():
        nonlocal validation_triggered
        validation_triggered = True
    dialog_add_mode.validation_failed.connect(on_validation_failed)
    try:
        dialog_add_mode.code_input.setText("")
        dialog_add_mode.description_input.setText("Some Description")
        dialog_add_mode.sale_price_input.setValue(5.0)
        dialog_add_mode.accept()
        qtbot.wait(100)
        assert validation_triggered, "Validation failed signal should have been triggered"
    finally:
        dialog_add_mode.validation_failed.disconnect(on_validation_failed)

@pytest.mark.skip(reason="Temporarily skipping due to persistent Qt crashes")
def test_validation_negative_price(qtbot, dialog_add_mode):
    """Should trigger validation failed signal if price is negative."""
    validation_triggered = False
    def on_validation_failed():
        nonlocal validation_triggered
        validation_triggered = True
    dialog_add_mode.validation_failed.connect(on_validation_failed)
    try:
        dialog_add_mode.code_input.setText("P002")
        dialog_add_mode.description_input.setText("Some Description")
        dialog_add_mode.sale_price_input.setRange(-999999.99, 999999.99)
        dialog_add_mode.sale_price_input.setValue(-1.0)
        dialog_add_mode.accept()
        qtbot.wait(100)
        assert validation_triggered, "Validation failed signal should have been triggered"
    finally:
        dialog_add_mode.validation_failed.disconnect(on_validation_failed)

@pytest.mark.skip(reason="Temporarily skipping due to persistent Qt crashes")
def test_state_change_control_stock(qtbot, dialog_add_mode):
    """Should update field visibility when inventory control changes."""
    dialog_add_mode.show()
    with qtbot.waitExposed(dialog_add_mode):
        pass
    dialog_add_mode.inventory_checkbox.setChecked(False)
    qtbot.wait(200)
    QApplication.processEvents()
    assert not dialog_add_mode.stock_input.isVisible()
    assert not dialog_add_mode.min_stock_input.isVisible()
    dialog_add_mode.inventory_checkbox.setChecked(True)
    qtbot.wait(200)
    QApplication.processEvents()
    qtbot.wait(100)
    QApplication.processEvents()
    assert dialog_add_mode.stock_input.isVisible()
    assert dialog_add_mode.min_stock_input.isVisible()

@pytest.mark.skip(reason="Temporarily skipping due to persistent Qt crashes")
def test_service_call_add_product(qtbot, dialog_add_mode, product_service):
    """Should call add_product with correct data when adding a product."""
    dialog_add_mode.code_input.setText("P003")
    dialog_add_mode.description_input.setText("New Product")
    dialog_add_mode.sale_price_input.setValue(12.5)
    dialog_add_mode.department_combo.setCurrentIndex(1)  # "Beverages"
    dialog_add_mode.inventory_checkbox.setChecked(True)
    dialog_add_mode.stock_input.setValue(20)
    dialog_add_mode.min_stock_input.setValue(2)
    dialog_add_mode.inventory_checkbox.setChecked(True)
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

@pytest.mark.skip(reason="Temporarily skipping due to persistent Qt crashes")
def test_service_call_update_product(qtbot, dialog_edit_mode, product_service):
    """Should call update_product with correct data when editing a product."""
    dialog_edit_mode.description_input.setText("Updated Product")
    dialog_edit_mode.sale_price_input.setValue(15.0)
    dialog_edit_mode.accept()
    assert product_service.updated_product is not None
    assert product_service.updated_product.description == "Updated Product"
    assert product_service.updated_product.sell_price == 15.0
