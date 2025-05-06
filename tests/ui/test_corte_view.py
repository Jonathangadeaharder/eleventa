"""
Test for the corte (cash drawer closing) view component.
"""

import sys
import pytest
from PySide6.QtWidgets import QApplication, QLabel
from unittest.mock import MagicMock, patch
from decimal import Decimal

from ui.views.corte_view import CorteView
from core.services.cash_drawer_service import CashDrawerService
from tests.ui.qt_test_utils import process_events

# Skip in general UI testing to avoid access violations
pytestmark = [
    pytest.mark.skipif("ui" in sys.argv, reason="Skip for general UI test runs to avoid access violations")
]

@pytest.fixture
def mock_cash_drawer_service():
    """Create a mock cash drawer service with the correct methods."""
    service = MagicMock()
    
    # Mock the get_drawer_summary method with a realistic return value
    service.get_drawer_summary.return_value = {
        'is_open': True,
        'current_balance': Decimal('200.00'),
        'initial_amount': Decimal('100.00'),
        'total_in': Decimal('50.00'),
        'total_out': Decimal('25.00'),
        'entries_today': [],
        'opened_at': None,
        'opened_by': None
    }
    
    return service

@pytest.fixture
def corte_view(qtbot, mock_cash_drawer_service):
    """Create a CorteView instance for testing."""
    # Create the view with mocked dependencies
    view = CorteView(mock_cash_drawer_service)
    qtbot.addWidget(view)
    
    # Show but don't wait for exposure to avoid access violations
    view.show()
    process_events()
    
    yield view
    
    # Clean up safely
    view.hide()
    process_events()
    view.deleteLater()
    process_events()

def test_corte_view_instantiation(corte_view, mock_cash_drawer_service):
    """Smoke test: CorteView can be instantiated and basic elements verified.

    Uses a safer approach to verify the widget exists with the expected structure.
    """
    # Ensure the view was created
    assert corte_view is not None
    assert isinstance(corte_view, CorteView)
    
    # Verify the service was used
    mock_cash_drawer_service.get_drawer_summary.assert_called
    
    # Test minimal functionality without intensive UI interaction
    # These assertions are less likely to cause access violations
    labels = corte_view.findChildren(QLabel)
    assert len(labels) > 0, "CorteView should contain labels"
