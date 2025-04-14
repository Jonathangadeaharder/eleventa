import pytest
from PySide6 import QtWidgets, QtCore
from ui.views.products_view import ProductsView
from ui.dialogs.product_dialog import ProductDialog
from ui.dialogs.department_dialog import DepartmentDialog

class MockProductService:
    def __init__(self):
        self.products = []
    def find_product(self, search_term=None):
        return self.products
    def add_product(self, product):
        self.products.append(product)
    def update_product(self, product):
        pass
    def delete_product(self, product_id):
        self.products = [p for p in self.products if p.id != product_id]

@pytest.fixture
def product_service():
    return MockProductService()

@pytest.fixture
def products_view(qtbot, product_service):
    widget = ProductsView(product_service=product_service)
    qtbot.addWidget(widget)
    widget.show()
    return widget

def test_products_view_instantiates(products_view):
    assert products_view.isVisible()
    assert products_view.table_view is not None

def test_add_product_dialog_opens(products_view, qtbot, monkeypatch):
    dialog_opened = {}

    def mock_exec(self):
        dialog_opened['opened'] = True
        return 0

    monkeypatch.setattr(ProductDialog, "exec", mock_exec)
    qtbot.mouseClick(products_view.new_button, QtCore.Qt.LeftButton)
    assert dialog_opened.get('opened', False)

def test_manage_departments_dialog_opens(products_view, qtbot, monkeypatch):
    dialog_opened = {}

    def mock_exec(self):
        dialog_opened['opened'] = True
        return 0

    monkeypatch.setattr(DepartmentDialog, "exec", mock_exec)
    qtbot.mouseClick(products_view.departments_button, QtCore.Qt.LeftButton)
    assert dialog_opened.get('opened', False)

def test_model_update_reflected(products_view, product_service, qtbot):
    # Simulate adding a product and refreshing the view
    class DummyProduct:
        def __init__(self, id, code, description, sale_price, quantity_in_stock, department_id=None, department_name=None):
            self.id = id
            self.code = code
            self.description = description
            self.sale_price = sale_price
            self.quantity_in_stock = quantity_in_stock
            self.department_id = department_id
            self.department_name = department_name or ""
    
    new_product = DummyProduct(1, "P001", "Test Product", 9.99, 10, 1, "Test Department")
    product_service.add_product(new_product)
    products_view.refresh_products()
    # Check that the table model now has at least one row
    assert products_view._model.rowCount() > 0
