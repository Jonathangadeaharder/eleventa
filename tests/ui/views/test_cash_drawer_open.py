"""
Test for CashDrawerView open functionality.
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
    # Patch dialogs to prevent them from showing
    patch('ui.views.cash_drawer_view.OpenDrawerDialog'),
    # Patch QTableView methods that might cause issues
    patch('PySide6.QtWidgets.QTableView.setModel', MagicMock()),
]

# Apply all patches
patchers = [p.start() for p in patches]
mock_message_box, mock_open_dialog, _ = patchers

# Mock dialog instance
mock_dialog_instance = MagicMock()
mock_open_dialog.return_value = mock_dialog_instance

# Now it's safe to import
from ui.views.cash_drawer_view import CashDrawerView
from core.services.cash_drawer_service import CashDrawerService

# Very short timeout
pytestmark = pytest.mark.timeout(3)

def create_drawer_summary(is_open=False, balance=Decimal('0.00'), 
                         initial_amount=Decimal('0.00')):
    """Create a mock drawer summary for a closed drawer."""
    return {
        'is_open': is_open,
        'current_balance': balance,
        'initial_amount': initial_amount,
        'total_in': Decimal('0.00'),
        'total_out': Decimal('0.00'),
        'entries_today': [],
        'opened_at': datetime.now() if is_open else None,
        'opened_by': 1 if is_open else None
    }

def test_open_drawer_button():
    """Test that open drawer button shows the dialog and calls service."""
    # Create mock service
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
    
    # Configure dialog mock
    mock_dialog_instance.exec.return_value = True  # Dialog accepted
    mock_dialog_instance.get_initial_amount.return_value = Decimal('100.00')
    
    # Create view
    view = None
    try:
        view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
        
        # Verify initial state
        assert view.open_button.isEnabled()
        
        # Click the open button
        view.open_button.click()
        QApplication.processEvents()
        
        # Verify dialog was shown
        mock_open_dialog.assert_called_once()
        mock_dialog_instance.exec.assert_called_once()
        
        # Verify service was called
        mock_service.open_drawer.assert_called_once_with(
            initial_amount=Decimal('100.00'),
            user_id=1
        )
        
        # Update view state as if service call succeeded
        mock_service.get_drawer_summary.return_value = create_drawer_summary(
            is_open=True,
            initial_amount=Decimal('100.00'),
            balance=Decimal('100.00')
        )
        view._refresh_data()
        QApplication.processEvents()
        
        # Verify button states updated
        assert not view.open_button.isEnabled()
        assert view.close_button.isEnabled()
        assert view.add_cash_button.isEnabled()
        assert view.remove_cash_button.isEnabled()
        
    finally:
        # Aggressive cleanup
        if view:
            view.close()
            view.deleteLater()
            for _ in range(5):
                QApplication.processEvents()

def test_open_drawer_canceled():
    """Test open drawer dialog canceled."""
    # Create mock service
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
    
    # Configure dialog mock to be canceled
    mock_dialog_instance.exec.return_value = False  # Dialog rejected
    
    # Create view
    view = None
    try:
        view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
        
        # Click the open button
        view.open_button.click()
        QApplication.processEvents()
        
        # Verify dialog was shown
        mock_dialog_instance.exec.assert_called_once()
        
        # Service should not be called when dialog is canceled
        mock_service.open_drawer.assert_not_called()
        
        # Button states should not change
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

def test_open_drawer_service_error():
    """Test handling of service errors when opening drawer."""
    # Create mock service
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
    
    # Configure service to raise an exception
    mock_service.open_drawer.side_effect = Exception("Service error")
    
    # Configure dialog mock
    mock_dialog_instance.exec.return_value = True  # Dialog accepted
    mock_dialog_instance.get_initial_amount.return_value = Decimal('100.00')
    
    # Create view
    view = None
    try:
        view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
        
        # Click the open button
        view.open_button.click()
        QApplication.processEvents()
        
        # Verify dialog was shown
        mock_dialog_instance.exec.assert_called_once()
        
        # Verify service was called but failed
        mock_service.open_drawer.assert_called_once()
        
        # Error message should be shown
        mock_message_box.critical.assert_called_once()
        
        # Button states should not change because operation failed
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

# Clean up patches at the end
for p in patches:
    p.stop() 