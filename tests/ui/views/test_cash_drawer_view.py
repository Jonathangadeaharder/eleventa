"""
Basic initialization tests for the CashDrawerView.
"""

import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

pytestmark = pytest.mark.timeout(3)

def test_initialization(qtbot):
    """Test that the view initializes correctly with all required components."""
    # Removed patch for setModel as it likely caused crashes
    from ui.views.cash_drawer_view import CashDrawerView
    from core.services.cash_drawer_service import CashDrawerService
    
    # Create a mock service
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = {
        'is_open': False,
        'current_balance': Decimal('0.00'),
        'initial_amount': Decimal('0.00'),
        'total_in': Decimal('0.00'),
        'total_out': Decimal('0.00'),
        'entries_today': []
    }
    
    # Create the view
    view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
    qtbot.addWidget(view)
    
    # Check that all required UI elements exist
    assert hasattr(view, 'open_button')
    # assert hasattr(view, 'close_button') # No separate close button
    assert hasattr(view, 'add_cash_button')
    assert hasattr(view, 'remove_cash_button')
    assert hasattr(view, 'print_report_button')
    assert hasattr(view, 'entries_table') # Correct table name
    assert hasattr(view, 'status_label')
    assert hasattr(view, 'balance_label')
    
    # Check initial state (drawer closed)
    assert view.open_button.isEnabled()
    assert view.open_button.text() == "Abrir Caja"
    assert not view.add_cash_button.isEnabled()
    assert not view.remove_cash_button.isEnabled()
    assert not view.print_report_button.isEnabled() # Also check print button
    
    # Clean up
    view.close()
    view.deleteLater()
