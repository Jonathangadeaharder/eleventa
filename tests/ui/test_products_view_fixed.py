"""
Fixed tests for ProductsView to avoid hanging issues.
"""
import pytest
from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import Qt, QModelIndex, QTimer
from PySide6.QtWidgets import QApplication
from unittest.mock import patch, MagicMock

pytestmark = pytest.mark.timeout(5)  # Short timeout

# Import our resource patching module to fix icon loading
import tests.ui.patch_resources

# Define this class here to avoid importing from core models
class MockProduct:
    def __init__(self, id=1, code="P001", description="Test Product"):
        self.id = id
        self.code = code
        self.description = description
        self.sale_price = 9.99
        self.cost_price = 0.00
        self.quantity_in_stock = 10
        self.min_stock = 5
        self.department_id = 1
        self.department_name = "Test Dept"
        self.uses_inventory = True
        self.unit = "U"

# Create a concrete TableModel implementation that doesn't depend on the real one
class MockProductTableModel(QtCore.QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self._products = []
        
    def rowCount(self, parent=QModelIndex()):
        return len(self._products)
        
    def columnCount(self, parent=QModelIndex()):
        return 7  # Same as ProductTableModel.HEADERS
        
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            return "Test Data"  # Simplified, return same data for all cells
        elif role == Qt.UserRole:
            return self._products[index.row()]
        return None
        
    def update_data(self, products):
        self.beginResetModel()
        self._products = products
        self.endResetModel()

class MockProductService:
    def __init__(self):
        self.products = []
        
    def find_product(self, search_term=None):
        # Simplified mock implementation
        return self.products
        
    def get_all_departments(self):
        return []
        
    def get_all_products(self, department_id=None):
        return self.products

@pytest.fixture
def mock_product_service():
    return MockProductService()

@pytest.fixture
def products_view(qtbot, mock_product_service, monkeypatch):
    # We need to import here to avoid circular imports
    from ui.views.products_view import ProductsView
    
    # Patch dialog so they don't actually show
    monkeypatch.setattr('ui.dialogs.product_dialog.ProductDialog.exec', lambda self: 1)
    monkeypatch.setattr('ui.dialogs.department_dialog.DepartmentDialog.exec', lambda self: 1)
    
    # Patch the model to use our mock
    monkeypatch.setattr('ui.views.products_view.ProductTableModel', MockProductTableModel)
    
    # Create the view with auto-refresh disabled
    view = ProductsView(product_service=mock_product_service, enable_auto_refresh=False)
    
    # Add to qtbot and show
    qtbot.addWidget(view)
    view.show()
    
    # Process events
    QApplication.processEvents()
    
    # Clean yield
    yield view
    
    # Clean up
    view.close()
    view.deleteLater()
    QApplication.processEvents()

def test_products_view_instantiates(products_view):
    """Test that the view can be instantiated successfully."""
    assert products_view is not None
    assert hasattr(products_view, 'table_view')
    assert hasattr(products_view, 'new_button')
    QApplication.processEvents()

def test_button_clicks(products_view, qtbot):
    """Test that button clicks don't cause the test to hang."""
    # Test each button
    qtbot.mouseClick(products_view.new_button, Qt.LeftButton)
    QApplication.processEvents()
    
    qtbot.mouseClick(products_view.departments_button, Qt.LeftButton)
    QApplication.processEvents()
    
    # Test passes if it doesn't hang

def test_model_update(products_view, mock_product_service):
    """Test that model updates work."""
    # Start with empty model
    assert products_view._model.rowCount() == 0
    
    # Add a product
    mock_product_service.products.append(MockProduct())
    
    # Refresh the view
    products_view.refresh_products()
    QApplication.processEvents()
    
    # Verify row was added
    assert products_view._model.rowCount() == 1 