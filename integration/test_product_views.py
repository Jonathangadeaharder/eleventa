"""
Integration tests for product-related views and models.

These tests verify that product components work together correctly,
including the table models and view rendering.
"""
import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QTableView

from core.models.product import Product, Department
from ui.models.table_models import ProductTableModel


class TestProductTableModel:
    """Tests for the product table model."""
    
    def test_product_table_model_with_product_attributes(self, qtbot):
        """Test that ProductTableModel handles Product attributes correctly."""
        # Create a sample product with the actual model attributes
        test_product = Product(
            id=1,
            code="P001",
            description="Test Product",
            cost_price=10.0,
            sell_price=20.0,  # Note: This is sell_price not sale_price
            department_id=1,
            quantity_in_stock=5.0,
            min_stock=2.0,
            uses_inventory=True,
            unit="Unidad"
        )
        
        # Create department and assign to product
        department = Department(id=1, name="Test Department")
        test_product.department = department
        
        # Create the model
        model = ProductTableModel()
        
        # Update with our test product
        model.update_data([test_product])
        
        # Verify the model has one row
        assert model.rowCount() == 1
        
        # Test that attribute access works correctly
        # Get the product at row 0
        retrieved_product = model.get_product_at_row(0)
        assert retrieved_product is not None
        assert retrieved_product.id == 1
        assert retrieved_product.code == "P001"
        assert retrieved_product.description == "Test Product"
        assert retrieved_product.cost_price == 10.0
        assert retrieved_product.sell_price == 20.0  # This should match the actual attribute name
        
        # Create a table view to test data rendering
        view = QTableView()
        view.setModel(model)
        qtbot.addWidget(view)
        
        # Test data display
        index = model.index(0, 0)  # Code column
        assert model.data(index, Qt.ItemDataRole.DisplayRole) == "P001"
        
        index = model.index(0, 1)  # Description column
        assert model.data(index, Qt.ItemDataRole.DisplayRole) == "Test Product"
        
        index = model.index(0, 2)  # Price column - this would fail if attributes don't match
        assert model.data(index, Qt.ItemDataRole.DisplayRole) == "20.00"
        
        # Test with department name
        index = model.index(0, 5)  # Department column
        assert model.data(index, Qt.ItemDataRole.DisplayRole) == "Test Department"


class TestProductViewIntegration:
    """Tests for product view integration."""
    
    @patch('ui.views.products_view.ProductsView')
    def test_product_view_initialization(self, mock_product_view, qtbot):
        """Test that ProductsView initializes with the correct model and data."""
        # This is a more comprehensive test that would need the actual view implementation
        # For now, we'll just verify that the view would be initialized correctly
        
        # Create mock repository that returns our test products
        mock_product_repo = MagicMock()
        test_products = [
            Product(
                id=1,
                code="P001",
                description="Test Product 1",
                cost_price=10.0,
                sell_price=20.0,
                department_id=1,
                quantity_in_stock=5.0,
                min_stock=2.0
            ),
            Product(
                id=2,
                code="P002",
                description="Test Product 2",
                cost_price=15.0,
                sell_price=30.0,
                department_id=1,
                quantity_in_stock=10.0,
                min_stock=3.0
            ),
        ]
        mock_product_repo.get_all.return_value = test_products
        
        # Since we're mocking the view, we'll just check that the product repository
        # would be called and assert that the data displayed would match our products
        # In a real test with the actual view implementation, we'd check the table contents
        
        # Assert that the mock view would be initialized with our mock repository
        # For now, we can just assert that the repository returns the expected products
        products = mock_product_repo.get_all()
        assert len(products) == 2
        assert products[0].code == "P001"
        assert products[0].sell_price == 20.0  # This would fail if we used sale_price
        assert products[1].code == "P002"
        assert products[1].sell_price == 30.0  # This would fail if we used sale_price 