"""
Minimal test file for cash drawer functionality.
Tests only the core cash drawer operations with minimal setup.
"""

import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

pytestmark = pytest.mark.timeout(3)

def create_drawer_summary(is_open=False, current_balance=Decimal('0.00')):
    """Helper to create a simple drawer summary."""
    return {
        'is_open': is_open,
        'current_balance': current_balance,
        'initial_amount': Decimal('0.00') if not is_open else current_balance,
        'total_in': Decimal('0.00'),
        'total_out': Decimal('0.00'),
        'entries_today': []
    }

def test_minimal_drawer_operations(qtbot):
    """Test basic drawer operations with minimal mocking."""
    print("=== Starting minimal drawer operations test ===")
    
    # Import first before patching to avoid conflicts
    from ui.views.cash_drawer_view import CashDrawerView
    from core.services.cash_drawer_service import CashDrawerService
    
    # Setup mock service
    mock_service = MagicMock(spec=CashDrawerService)
    
    # Drawer initially closed
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
    
    # Create view
    view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
    qtbot.addWidget(view)
    
    # Verify initial state (drawer closed)
    assert view.status_label.text() == "Cerrada"
    assert not view.add_cash_button.isEnabled()
    assert not view.remove_cash_button.isEnabled()
    assert view.open_button.text() == "Abrir Caja"
    
    # Simulate successful drawer opening
    print("=== Simulating drawer open ===")
    
    # Update service to reflect open drawer
    mock_service.get_drawer_summary.return_value = create_drawer_summary(
        is_open=True, 
        current_balance=Decimal('100.00')
    )
    
    # Force refresh to update the view
    view._refresh_data()
    
    # Verify view state after opening
    assert view.status_label.text() == "Abierta"
    assert "$100.00" in view.balance_label.text()
    assert view.add_cash_button.isEnabled()
    assert view.remove_cash_button.isEnabled()
    assert view.open_button.text() == "Cerrar Caja"
    
    # Verify service called appropriately
    assert mock_service.get_drawer_summary.call_count >= 2
    
    # Close view
    view.close()
    view.deleteLater()
