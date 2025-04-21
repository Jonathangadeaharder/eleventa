"""
Tests for the ProductsView UI component.
Focus: Product listing, selection, and UI interaction.
"""
"""
Tests for the ProductsView component.

This test suite verifies the functionality of the ProductsView component, including:
- UI initialization and widget availability
- Button interactions and dialog openings
- Product model updates and view refreshing
"""
import pytest
# import patch_qt_tests # Remove top-level import
from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import QTimer, QCoreApplication, Qt, QModelIndex
from PySide6.QtWidgets import QApplication
from ui.views.products_view import ProductsView
from ui.dialogs.product_dialog import ProductDialog
from ui.dialogs.department_dialog import DepartmentDialog
from unittest.mock import patch, MagicMock
import sys

# Import our resource patching module
import tests.ui.patch_resources

# Shorter timeout
pytestmark = pytest.mark.timeout(5)

# Debug print function
def debug_print(message):
    print(f"DEBUG: {message}", file=sys.stderr)
    sys.stderr.flush()

# Mock product class
class DummyProduct:
    """Mock product class for testing."""
    def __init__(self, id=1, code="P001", description="Test Product", sale_price=9.99, 
                 quantity_in_stock=10, department_id=None, department_name=None):
        self.id = id
        self.code = code
        self.description = description
        self.sale_price = sale_price
        self.quantity_in_stock = quantity_in_stock
        self.department_id = department_id
        self.department_name = department_name or ""
        # Required for model to work properly
        self.cost_price = 0.0
        self.min_stock = 1.0
        self.uses_inventory = True
        self.unit = "U"

# Create a concrete TableModel implementation that doesn't depend on the real one
class MockProductTableModel(QtCore.QAbstractTableModel):
    """Mock implementation of ProductTableModel that works reliably in tests."""
    def __init__(self, *args):
        super().__init__()
        self._products = []
        
    def rowCount(self, parent=QModelIndex()):
        return len(self._products)
        
    def columnCount(self, parent=QModelIndex()):
        return 7  # Same as ProductTableModel.HEADERS
        
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._products):
            return None
            
        product = self._products[index.row()]
        column = index.column()
        
        if role == Qt.DisplayRole:
            # Return simplified data based on column
            if column == 0:
                return product.code
            elif column == 1:
                return product.description
            else:
                return "Test"
        elif role == Qt.UserRole:
            return product
            
        return None
        
    def update_data(self, products):
        """Update the model with new data."""
        self.beginResetModel()
        self._products = products
        self.endResetModel()

class MockProductService:
    """Mock implementation of ProductService for testing."""
    def __init__(self):
        self.products = []
        debug_print("MockProductService initialized")
        
    def find_product(self, search_term=None):
        debug_print(f"find_product called with '{search_term}'")
        return self.products
        
    def add_product(self, product):
        debug_print(f"add_product called with {product.code}")
        self.products.append(product)
        
    def update_product(self, product):
        debug_print(f"update_product called")
        pass
        
    def delete_product(self, product_id):
        debug_print(f"delete_product called with ID {product_id}")
        self.products = [p for p in self.products if p.id != product_id]
        
    def get_all_products(self, department_id=None):
        debug_print(f"get_all_products called")
        return self.products
        
    def get_all_departments(self):
        debug_print("get_all_departments called")
        return []

@pytest.fixture
def product_service():
    """Create a mock product service."""
    debug_print("Creating product_service fixture")
    return MockProductService()

@pytest.fixture
def products_view(qtbot, product_service, monkeypatch):
    """Create a ProductsView with patched components to avoid hanging."""
    debug_print("Creating products_view fixture")
    
    # Patch dialog classes to prevent hanging
    monkeypatch.setattr('ui.dialogs.product_dialog.ProductDialog.exec', lambda self: 1)
    monkeypatch.setattr('ui.dialogs.department_dialog.DepartmentDialog.exec', lambda self: 1)
    
    # Patch the table model
    monkeypatch.setattr('ui.views.products_view.ProductTableModel', MockProductTableModel)
    
    # Create the view with auto-refresh disabled
    view = ProductsView(product_service=product_service, enable_auto_refresh=False)
    debug_print("ProductsView created")
    
    qtbot.addWidget(view)
    debug_print("Widget added to qtbot")
    
    view.show()
    debug_print("Widget shown")
    
    # Process events to ensure UI is ready
    QApplication.processEvents()
    debug_print("Events processed")
    
    yield view
    
    # Clean up
    debug_print("Cleaning up products_view fixture")
    view.close()
    view.deleteLater()
    QApplication.processEvents()

@pytest.mark.skip(reason="Temporarily skipping due to persistent Qt crashes")
def test_products_view_instantiates(products_view):
    """Test that the view initializes correctly."""
    debug_print("Starting test_products_view_instantiates")
    
    assert products_view is not None
    assert products_view.table_view is not None
    
    debug_print("test_products_view_instantiates completed")

@pytest.mark.skip(reason="Temporarily skipping due to persistent Qt crashes")
def test_add_product_dialog_opens(products_view, qtbot):
    """Test that clicking the New button opens the product dialog."""
    debug_print("Starting test_add_product_dialog_opens")
    
    # Click the new button - dialog exec is patched to return 1 (accepted)
    qtbot.mouseClick(products_view.new_button, Qt.LeftButton)
    QApplication.processEvents()
    
    debug_print("test_add_product_dialog_opens completed")

@pytest.mark.skip(reason="Temporarily skipping due to persistent Qt crashes")
def test_manage_departments_dialog_opens(products_view, qtbot):
    """Test that clicking the Departments button opens the departments dialog."""
    debug_print("Starting test_manage_departments_dialog_opens")
    
    # Click the departments button - dialog exec is patched to return 1 (accepted)
    qtbot.mouseClick(products_view.departments_button, Qt.LeftButton)
    QApplication.processEvents()
    
    debug_print("test_manage_departments_dialog_opens completed")

@pytest.mark.skip(reason="Temporarily skipping due to persistent Qt crashes")
def test_model_update_reflected(products_view, product_service, qtbot):
    """Test that model updates are reflected in the view."""
    debug_print("Starting test_model_update_reflected")
    
    # Verify model starts empty
    products_view.refresh_products()
    QApplication.processEvents()
    assert products_view._model.rowCount() == 0
    debug_print("Verified model is empty")
    
    # Add a product
    new_product = DummyProduct(1, "P001", "Test Product", 9.99, 10, 1, "Test Department")
    product_service.add_product(new_product)
    debug_print("Added test product")
    
    # Refresh and verify
    products_view.refresh_products()
    QApplication.processEvents()
    assert products_view._model.rowCount() == 1
    debug_print("Verified model now has 1 row")
    
    debug_print("test_model_update_reflected completed")

@pytest.mark.skip(reason="Temporarily skipping due to persistent Qt crashes")
def test_button_clicks_dont_hang(products_view, qtbot):
    """
    Test that button clicks don't cause the test to hang.
    
    This test is a simplified version incorporated from test_products_view_fixed.py.
    """
    # Test each button in sequence
    qtbot.mouseClick(products_view.new_button, Qt.LeftButton)
    QApplication.processEvents()
    
    qtbot.mouseClick(products_view.departments_button, Qt.LeftButton)
    QApplication.processEvents()
    
    # Test passes if it doesn't hang
