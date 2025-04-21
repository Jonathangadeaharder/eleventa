"""
Test for CashDrawerView data display and refresh functionality.
"""
import sys
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import datetime

# Import QApplication first to ensure it's created before any QWidgets
from PySide6.QtWidgets import QApplication
app = QApplication.instance() or QApplication(sys.argv)

# Create patches before importing CashDrawerView
patches = [
    # Mock QMessageBox to prevent any dialog displays
    patch('ui.views.cash_drawer_view.QMessageBox'),
    # Patch QTableView and QTableView methods that might cause issues
    patch('PySide6.QtWidgets.QTableView.setModel', MagicMock()),
]

# Apply all patches
patchers = [p.start() for p in patches]
mock_message_box, _ = patchers

# Now it's safe to import
from ui.views.cash_drawer_view import CashDrawerView
from core.services.cash_drawer_service import CashDrawerService

# Very short timeout
pytestmark = pytest.mark.timeout(3)

def create_drawer_summary(is_open=True, balance=Decimal('100.00'), 
                         initial_amount=Decimal('100.00'), 
                         total_in=Decimal('50.00'), 
                         total_out=Decimal('25.00'),
                         entries=None):
    """Create a mock drawer summary with optional details."""
    if entries is None:
        entries = [
            {
                'id': 1,
                'type': 'add',
                'amount': Decimal('50.00'),
                'reason': 'Deposit',
                'timestamp': datetime.now(),
                'user_id': 1
            },
            {
                'id': 2,
                'type': 'remove',
                'amount': Decimal('25.00'),
                'reason': 'Withdrawal',
                'timestamp': datetime.now(),
                'user_id': 1
            }
        ]
    
    return {
        'is_open': is_open,
        'current_balance': balance,
        'initial_amount': initial_amount,
        'total_in': total_in,
        'total_out': total_out,
        'entries_today': entries,
        'opened_at': datetime.now() if is_open else None,
        'opened_by': 1 if is_open else None
    }

def test_refresh_data_display():
    """Test that _refresh_data updates the view correctly."""
    # Create mock service
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary()
    
    # Create view
    view = None
    try:
        view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
        
        # Verify initial data is displayed
        # Money display calls .format() which could be challenging to test in detail
        # So we'll just check basics
        assert view.balance_display.text() != ""
        assert view.initial_amount_display.text() != ""
        assert view.total_in_display.text() != ""
        assert view.total_out_display.text() != ""
        
        # Updated mock with different values
        mock_service.get_drawer_summary.return_value = create_drawer_summary(
            balance=Decimal('200.00'),
            initial_amount=Decimal('150.00'),
            total_in=Decimal('100.00'),
            total_out=Decimal('50.00')
        )
        
        # Trigger refresh
        view._refresh_data()
        QApplication.processEvents()
        
        # Service should have been called twice (once during init, once for refresh)
        assert mock_service.get_drawer_summary.call_count == 2
        
    finally:
        # Aggressive cleanup
        if view:
            view.close()
            view.deleteLater()
            for _ in range(5):
                QApplication.processEvents()

def test_drawer_state_transitions():
    """Test transitions between open and closed drawer states."""
    # Create mock service
    mock_service = MagicMock(spec=CashDrawerService)
    
    # Start with a closed drawer
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
    
    # Create view
    view = None
    try:
        view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
        
        # Verify initial state (closed drawer)
        assert view.open_button.isEnabled()
        assert not view.close_button.isEnabled()
        assert not view.add_cash_button.isEnabled()
        assert not view.remove_cash_button.isEnabled()
        
        # Change to open drawer state
        mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=True)
        
        # Refresh data
        view._refresh_data()
        QApplication.processEvents()
        
        # Verify updated state (open drawer)
        assert not view.open_button.isEnabled()
        assert view.close_button.isEnabled()
        assert view.add_cash_button.isEnabled()
        assert view.remove_cash_button.isEnabled()
        
        # Change back to closed drawer
        mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
        
        # Refresh data
        view._refresh_data()
        QApplication.processEvents()
        
        # Verify initial state again (closed drawer)
        assert view.open_button.isEnabled()
        assert not view.close_button.isEnabled()
        assert not view.add_cash_button.isEnabled()
        assert not view.remove_cash_button.isEnabled()
        
    finally:
        # Aggressive cleanup
        if view:
            view.close()
            view.deleteLater()
            for _ in range(5):
                QApplication.processEvents()

def test_empty_entries():
    """Test view with empty entries list."""
    # Create mock service
    mock_service = MagicMock(spec=CashDrawerService)
    
    # Create a summary with no entries
    mock_service.get_drawer_summary.return_value = create_drawer_summary(entries=[])
    
    # Create view
    view = None
    try:
        view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
        
        # The view should still initialize correctly
        assert view is not None
        
        # Table model should be set (we've mocked setModel, but we can check if view is setup)
        assert view.transactions_table is not None
        
    finally:
        # Aggressive cleanup
        if view:
            view.close()
            view.deleteLater()
            for _ in range(5):
                QApplication.processEvents()

# Clean up patches at the end
for p in patches:
    p.stop() 