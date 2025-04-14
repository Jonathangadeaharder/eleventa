# This test requires pytest-qt to be installed: pip install pytest-qt
import pytest
from PySide6.QtCore import Qt
from ui.views.sales_view import SalesView

def test_f12_shortcut_finalizes_sale(qtbot, mocker):
    """Test that pressing F12 in SalesView triggers finalize_current_sale."""
    sales_view = SalesView()
    qtbot.addWidget(sales_view)
    finalize_spy = mocker.spy(sales_view, "finalize_current_sale")
    # Simulate F12 key press
    qtbot.keyPress(sales_view, Qt.Key_F12)
    assert finalize_spy.call_count == 1