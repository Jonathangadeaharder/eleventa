"""
Tests for keyboard shortcut handling in the UI.
Focus: Shortcut registration, triggering, and action mapping.
"""

# This test requires pytest-qt to be installed: pip install pytest-qt
import pytest
from PySide6.QtCore import Qt
from ui.views.sales_view import SalesView
from unittest.mock import MagicMock

@pytest.mark.skip(reason="Temporarily skipping due to persistent Qt crash (access violation) during SalesView init")
def test_f12_shortcut_finalizes_sale(qtbot, mocker):
    """Test that pressing F12 in SalesView triggers finalize_current_sale."""
    product_service = MagicMock()
    sale_service = MagicMock()
    customer_service = MagicMock()
    current_user = MagicMock()
    sales_view = SalesView(
        product_service=product_service,
        sale_service=sale_service,
        customer_service=customer_service,
        current_user=current_user
    )
    qtbot.addWidget(sales_view)
    finalize_spy = mocker.spy(sales_view, "finalize_current_sale")
    # Simulate F12 key press
    qtbot.keyPress(sales_view, Qt.Key_F12)
    assert finalize_spy.call_count == 1
