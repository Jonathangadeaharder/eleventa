"""
Ultra-minimal tests for CashDrawerView focused purely on code coverage.

This file completely avoids any UI rendering or event loops by:
1. Mocking all QWidget methods that might cause UI display
2. Directly calling methods instead of using UI interactions
3. Patching all external classes aggressively
4. Never calling show() on any widget
5. Focusing only on code paths identified in the coverage report
"""

import sys
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import datetime

# Set up patches BEFORE importing any Qt modules
patches = [
    # Pre-patch QApplication
    patch('PySide6.QtWidgets.QApplication', MagicMock()),
    # Pre-patch QWidget methods that cause UI display
    patch('PySide6.QtWidgets.QWidget.show', MagicMock()),
    patch('PySide6.QtWidgets.QWidget.close', MagicMock()),
    patch('PySide6.QtWidgets.QWidget.deleteLater', MagicMock()),
    # Pre-patch event processing
    patch('PySide6.QtWidgets.QApplication.processEvents', MagicMock()),
    # Pre-patch PySide layouts
    patch('PySide6.QtWidgets.QVBoxLayout', MagicMock()),
    patch('PySide6.QtWidgets.QHBoxLayout', MagicMock()),
    patch('PySide6.QtWidgets.QGridLayout', MagicMock()),
    # Pre-patch widgets
    patch('PySide6.QtWidgets.QLabel', MagicMock()),
    patch('PySide6.QtWidgets.QPushButton', MagicMock()),
    patch('PySide6.QtWidgets.QTableView', MagicMock()),
]

# Apply all pre-patches
for p in patches:
    p.start()

# Now import Qt-related modules
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt

# Apply more specific patches
more_patches = [
    # Mock dialog classes
    patch('ui.dialogs.cash_drawer_dialogs.OpenDrawerDialog', MagicMock()),
    patch('ui.dialogs.cash_drawer_dialogs.AddRemoveCashDialog', MagicMock()),
    patch('ui.dialogs.cash_drawer_dialogs.CashMovementDialog', MagicMock()),
    # Mock QMessageBox
    patch('ui.views.cash_drawer_view.QMessageBox', MagicMock()),
    # Patch QTableView methods
    patch('ui.views.cash_drawer_view.QTableView', MagicMock()),
]

# Apply all specific patches
for p in more_patches:
    p.start()

# Now it's safe to import our target
from ui.views.cash_drawer_view import CashDrawerView
from core.services.cash_drawer_service import CashDrawerService
from core.models.cash_drawer import CashDrawerEntry, CashDrawerEntryType

# Extremely short timeout
pytestmark = pytest.mark.timeout(1)

# --- Helper Functions ---

def create_drawer_summary(is_open=False, 
                         current_balance=Decimal('100.00'),
                         initial_amount=Decimal('100.00'),
                         total_in=Decimal('0.00'),
                         total_out=Decimal('0.00')):
    """Create a minimal test cash drawer summary."""
    return {
        'is_open': is_open,
        'current_balance': current_balance,
        'initial_amount': initial_amount,
        'total_in': total_in,
        'total_out': total_out,
        'entries_today': [],
        'opened_at': datetime.now() if is_open else None,
        'opened_by': 1 if is_open else None
    }

# --- Tests ---

def test_close_drawer_dialog():
    """Test the close drawer dialog path (lines 206)."""
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=True)
    
    # Create view but do NOT show it
    view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
    
    # Call the method directly instead of clicking
    view._handle_open_drawer()
    
    # Verify the information dialog would be shown
    from ui.views.cash_drawer_view import QMessageBox
    QMessageBox.information.assert_called_once()

def test_open_drawer_value_error():
    """Test ValueError handling in open drawer (lines 224-247)."""
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
    
    # Mock the dialog
    dialog_mock = MagicMock()
    dialog_mock.exec.return_value = True
    dialog_mock.amount_edit.text.return_value = "invalid"
    dialog_mock.description_edit.text.return_value = "test"
    
    # Create view but don't show it
    view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
    
    # Patch the dialog class inside this test
    with patch('ui.views.cash_drawer_view.OpenDrawerDialog', return_value=dialog_mock):
        # Call the method directly
        view._handle_open_drawer()
        
        # Verify warning was shown
        from ui.views.cash_drawer_view import QMessageBox
        QMessageBox.warning.assert_called_once()

def test_add_cash_closed_drawer():
    """Test add cash to closed drawer (lines 254-255)."""
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
    
    # Create view but don't show it
    view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
    
    # Call the method directly
    view._handle_add_cash()
    
    # Verify warning was shown
    from ui.views.cash_drawer_view import QMessageBox
    QMessageBox.warning.assert_called_once()

def test_remove_cash_insufficient_balance():
    """Test insufficient balance in remove cash (lines 279-280)."""
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=True)
    
    # Mock the dialog
    dialog_mock = MagicMock()
    dialog_mock.exec.return_value = True
    dialog_mock.amount_edit.text.return_value = "200.00"  # More than the 100.00 balance
    dialog_mock.description_edit.text.return_value = "test"
    
    # Create view but don't show it
    view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
    
    # Patch the dialog class inside this test
    with patch('ui.views.cash_drawer_view.CashMovementDialog', return_value=dialog_mock):
        # Call the method directly
        view._handle_remove_cash()
        
        # Verify warning was shown
        from ui.views.cash_drawer_view import QMessageBox
        QMessageBox.warning.assert_called_once()
        # Verify remove_cash was not called
        mock_service.remove_cash.assert_not_called()

def test_remove_cash_value_error():
    """Test ValueError in remove cash (lines 287-288)."""
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=True)
    
    # Mock the dialog
    dialog_mock = MagicMock()
    dialog_mock.exec.return_value = True
    dialog_mock.amount_edit.text.return_value = "invalid"  # Will cause ValueError
    dialog_mock.description_edit.text.return_value = "test"
    
    # Create view but don't show it
    view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
    
    # Patch the dialog class inside this test
    with patch('ui.views.cash_drawer_view.CashMovementDialog', return_value=dialog_mock):
        # Call the method directly
        view._handle_remove_cash()
        
        # Verify warning was shown
        from ui.views.cash_drawer_view import QMessageBox
        QMessageBox.warning.assert_called_once()

def test_print_report():
    """Test print report dialog (lines 299-304)."""
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=True)
    
    # Create view but don't show it
    view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
    
    # Call the method directly
    view._print_report()
    
    # Verify information dialog was shown
    from ui.views.cash_drawer_view import QMessageBox
    QMessageBox.information.assert_called_once()

def test_remove_cash_closed_drawer():
    """Test remove cash from closed drawer."""
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
    
    # Create view but don't show it
    view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
    
    # Call the method directly
    view._handle_remove_cash()
    
    # Verify warning was shown
    from ui.views.cash_drawer_view import QMessageBox
    QMessageBox.warning.assert_called_once()

# Clean up all patches to avoid affecting other tests
for p in patches + more_patches:
    p.stop() 