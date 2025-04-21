"""
Integration tests for product operations.

These tests verify product creation, retrieval, and management.
"""
import pytest
from core.models.product import Product


@pytest.mark.integration
def test_product_model():
    """Test that the Product model can be instantiated."""
    product = Product(
        code="TEST001",
        description="Test Product",
        cost_price=80.00,
        sell_price=100.00,
        quantity_in_stock=10
    )
    
    assert product.code == "TEST001"
    assert product.description == "Test Product"
    assert product.cost_price == 80.00
    assert product.sell_price == 100.00
    assert product.quantity_in_stock == 10 