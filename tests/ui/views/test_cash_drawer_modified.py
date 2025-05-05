"""
Tests for cash drawer modifications and state changes.
"""

import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

pytestmark = pytest.mark.timeout(3)

def create_drawer_summary(is_open=False, current_balance=Decimal('100.00'), initial_amount=Decimal('100.00')):
    """Helper to create a drawer summary."""
    return {
        'is_open': is_open,
        'current_balance': current_balance,
        'initial_amount': initial_amount,
        'total_in': Decimal('0.00'),
        'total_out': Decimal('0.00'),
        'entries_today': []
    }

def test_drawer_modification_tracking(qtbot):
    """Test that drawer modifications are tracked correctly."""
    print("=== Starting test_drawer_modification_tracking with different approach ===")
    
    # Import first before patching
    from ui.views.cash_drawer_view import CashDrawerView
    from core.services.cash_drawer_service import CashDrawerService
    
    # Setup mock service
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=True)
    
    # Create view
    view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
    qtbot.addWidget(view)
    view.current_drawer_id = 1
    
    # Verify initial state
    assert view.status_label.text() == "Abierta"
    assert "$100.00" in view.balance_label.text()
    assert view.add_cash_button.isEnabled()
    assert view.remove_cash_button.isEnabled()
    
    # Simulate add cash operation and update
    print("=== Simulating add cash operation ===")
    mock_service.get_drawer_summary.return_value = create_drawer_summary(
        is_open=True,
        current_balance=Decimal('150.00'),
        initial_amount=Decimal('100.00')
    )
    
    # Force a refresh to update the view
    view._refresh_data()
    
    # Verify balance display updated
    assert "$150.00" in view.balance_label.text()
    
    # Simulate remove cash operation
    print("=== Simulating remove cash operation ===")
    mock_service.get_drawer_summary.return_value = create_drawer_summary(
        is_open=True,
        current_balance=Decimal('125.00'),
        initial_amount=Decimal('100.00')
    )
    
    # Force a refresh to update the view
    view._refresh_data()
    
    # Verify updated balance
    assert "$125.00" in view.balance_label.text()
    
    # Verify service was called appropriately
    assert mock_service.get_drawer_summary.call_count >= 3
    
    # Cleanup
    view.close()
    view.deleteLater()

def test_consecutive_modifications(qtbot):
    """Test multiple consecutive modifications to the cash drawer."""
    print("=== Starting test_consecutive_modifications with different approach ===")
    
    # Import first before patching to avoid import issues
    from ui.views.cash_drawer_view import CashDrawerView
    from core.services.cash_drawer_service import CashDrawerService
    
    # Setup mock service without relying on dialog patching
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=True)
    
    # Create the view 
    view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
    qtbot.addWidget(view)
    view.current_drawer_id = 1
    
    # Verify initial state
    assert view.status_label.text() == "Abierta"
    assert "$100.00" in view.balance_label.text()
    assert view.add_cash_button.isEnabled()
    assert view.remove_cash_button.isEnabled()
    
    # First operation: add cash (simulate success without dialog)
    print("=== First operation: simulate add cash ===")
    # Update the service mock to reflect successful add cash operation
    mock_service.get_drawer_summary.return_value = create_drawer_summary(
        is_open=True,
        current_balance=Decimal('150.00')
    )
    # Force a refresh to update the view
    view._refresh_data()
    
    # Verify balance updated after first operation
    assert "$150.00" in view.balance_label.text()
    
    # Second operation: add more cash
    print("=== Second operation: simulate add cash ===")
    # Update the service mock again
    mock_service.get_drawer_summary.return_value = create_drawer_summary(
        is_open=True,
        current_balance=Decimal('175.00')
    )
    view._refresh_data()
    
    # Verify balance updated after second operation
    assert "$175.00" in view.balance_label.text()
    
    # Third operation: remove cash
    print("=== Third operation: simulate remove cash ===")
    # Update the service mock for the final state
    mock_service.get_drawer_summary.return_value = create_drawer_summary(
        is_open=True,
        current_balance=Decimal('100.00')
    )
    view._refresh_data()
    
    # Verify final balance state
    assert "$100.00" in view.balance_label.text()
    
    # Verify service was called appropriately (once per refresh_data, plus initial)
    assert mock_service.get_drawer_summary.call_count >= 4
    
    # Cleanup
    view.close()
    view.deleteLater()
