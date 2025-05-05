"""
Tests for the CashDrawerView UI component with proper QApplication handling.

This file contains a simplified test that:
1. Properly initializes QApplication
2. Mocks dialog classes to avoid possible hanging
3. Uses shorter timeouts
"""

# Standard library imports
import sys
from decimal import Decimal
from datetime import datetime
from unittest.mock import MagicMock, patch

# Testing frameworks
import pytest

# Import Qt support module first - this sets up the environment
from tests.ui.qt_support import (
    Qt, QApplication, QMessageBox, QT_IMPORTS_AVAILABLE
)

# Skip all tests if Qt imports aren't available
pytestmark = [
    pytest.mark.skipif(not QT_IMPORTS_AVAILABLE, reason="PySide6 imports not available"),
    pytest.mark.timeout(5)  # Set timeout to prevent hanging tests
]

# Application components
from ui.views.cash_drawer_view import CashDrawerView
from core.services.cash_drawer_service import CashDrawerService
from core.models.cash_drawer import CashDrawerEntry, CashDrawerEntryType

# --- Helper Functions ---

def create_drawer_summary(is_open=False):
    """Create a simple drawer summary for testing."""
    return {
        'is_open': is_open,
        'current_balance': Decimal('0.00'),
        'opened_at': None,
        'opened_by': None,
        'entries_today': [],
        'initial_amount': Decimal('0.00'),
        'total_in': Decimal('0.00'),
        'total_out': Decimal('0.00')
    }

# --- Fixtures ---

@pytest.fixture
def mock_cash_drawer_service():
    """Provides a mock CashDrawerService."""
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary()
    return mock_service

# --- Tests ---

# Simple test to check if the module loads properly
def test_module_loads():
    """Simple test to ensure module loads properly."""
    assert True

@pytest.mark.skipif(not QT_IMPORTS_AVAILABLE, reason="PySide6 imports not available")
@patch('ui.views.cash_drawer_view.OpenDrawerDialog', MagicMock())
@patch('ui.views.cash_drawer_view.CashMovementDialog', MagicMock())
def test_cash_drawer_view_basic(qtbot, mock_cash_drawer_service):
    """
    Basic test to verify CashDrawerView can be instantiated and works.
    
    This test:
    1. Creates a CashDrawerView instance
    2. Verifies its initial state
    3. Properly cleans up resources
    """
    # Create the view
    view = CashDrawerView(cash_drawer_service=mock_cash_drawer_service, user_id=1)
    
    try:
        # Register with qtbot and show
        qtbot.addWidget(view)
        view.show()
        qtbot.wait(100)  # Allow time for processing events
        
        # Basic assertions
        assert view is not None
        assert view.status_label.text() == "Cerrada"
        assert not view.add_cash_button.isEnabled()
        assert not view.remove_cash_button.isEnabled()
        assert not view.print_report_button.isEnabled()
        
        # Verify service was called
        mock_cash_drawer_service.get_drawer_summary.assert_called_once()
    finally:
        # Clean up
        view.close()
        view.deleteLater()
        qtbot.wait(50)  # Process cleanup events 