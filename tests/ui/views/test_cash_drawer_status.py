"""
Test for CashDrawerView status display functionality.
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
    # Patch QTableView methods that might cause issues
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

def create_drawer_summary(is_open=True, balance=Decimal('100.00'), initial_amount=Decimal('100.00'),
                         total_in=Decimal('0.00'), total_out=Decimal('0.00')):
    """Create a mock drawer summary for testing."""
    return {
        'is_open': is_open,
        'current_balance': balance,
        'initial_amount': initial_amount,
        'total_in': total_in,
        'total_out': total_out,
        'entries_today': [],
        'opened_at': datetime.now() if is_open else None,
        'opened_by': 1 if is_open else None
    }

def test_drawer_status_display_open():
    """Test that drawer status is correctly displayed when open."""
    # Create mock service with open drawer
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary(
        is_open=True,
        balance=Decimal('150.00'),
        initial_amount=Decimal('100.00'),
        total_in=Decimal('75.00'),
        total_out=Decimal('25.00')
    )
    
    # Create view
    view = None
    try:
        view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
        
        # Verify initial state
        assert view.is_open
        assert "OPEN" in view.status_label.text()
        assert "150.00" in view.balance_label.text()
        assert "100.00" in view.initial_amount_label.text()
        assert "75.00" in view.total_cash_in_label.text()
        assert "25.00" in view.total_cash_out_label.text()
        
        # Buttons should be enabled when drawer is open
        assert view.add_cash_button.isEnabled()
        assert view.remove_cash_button.isEnabled()
        assert view.close_drawer_button.isEnabled()
        assert not view.open_drawer_button.isEnabled()
        
    finally:
        # Aggressive cleanup
        if view:
            view.close()
            view.deleteLater()
            for _ in range(5):
                QApplication.processEvents()

def test_drawer_status_display_closed():
    """Test that drawer status is correctly displayed when closed."""
    # Create mock service with closed drawer
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
    
    # Create view
    view = None
    try:
        view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
        
        # Verify initial state
        assert not view.is_open
        assert "CLOSED" in view.status_label.text()
        
        # When drawer is closed, cash operations should be disabled
        assert not view.add_cash_button.isEnabled()
        assert not view.remove_cash_button.isEnabled()
        assert not view.close_drawer_button.isEnabled()
        assert view.open_drawer_button.isEnabled()
        
    finally:
        # Aggressive cleanup
        if view:
            view.close()
            view.deleteLater()
            for _ in range(5):
                QApplication.processEvents()

def test_refresh_data():
    """Test that refresh updates the UI with new data."""
    # Create mock service
    mock_service = MagicMock(spec=CashDrawerService)
    
    # Initial state - drawer open with 100.00 balance
    mock_service.get_drawer_summary.return_value = create_drawer_summary(
        is_open=True,
        balance=Decimal('100.00')
    )
    
    # Create view
    view = None
    try:
        view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
        
        # Initial checks
        assert view.is_open
        assert "100.00" in view.balance_label.text()
        
        # Change drawer state in the service
        mock_service.get_drawer_summary.return_value = create_drawer_summary(
            is_open=True,
            balance=Decimal('200.00'),
            total_in=Decimal('100.00')
        )
        
        # Refresh the view
        view._refresh_data()
        QApplication.processEvents()
        
        # Verify updated state
        assert view.is_open
        assert "200.00" in view.balance_label.text()
        assert "100.00" in view.total_cash_in_label.text()
        
        # Change to closed state
        mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
        
        # Refresh again
        view._refresh_data()
        QApplication.processEvents()
        
        # Verify drawer is now closed in UI
        assert not view.is_open
        assert "CLOSED" in view.status_label.text()
        assert not view.add_cash_button.isEnabled()
        assert not view.remove_cash_button.isEnabled()
        assert not view.close_drawer_button.isEnabled()
        assert view.open_drawer_button.isEnabled()
        
    finally:
        # Aggressive cleanup
        if view:
            view.close()
            view.deleteLater()
            for _ in range(5):
                QApplication.processEvents()

def test_service_error_on_load():
    """Test handling of service errors during data loading."""
    # Create mock service that raises an exception
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.side_effect = Exception("Database connection error")
    
    # Create view
    view = None
    try:
        view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
        
        # Verify error message was shown
        mock_message_box.critical.assert_called_once()
        
        # The view should assume drawer is closed when an error occurs
        assert not view.is_open
        assert not view.add_cash_button.isEnabled()
        assert not view.remove_cash_button.isEnabled()
        assert not view.close_drawer_button.isEnabled()
        
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