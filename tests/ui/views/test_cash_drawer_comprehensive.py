"""
Comprehensive tests for CashDrawerView with aggressive patching.

This test file:
1. Uses aggressive patching to prevent tests from hanging
2. Covers the specific code paths identified in the coverage report
3. Follows the pattern from test_cash_drawer_minimal.py which has proven successful
4. Incorporates targeted test cases from test_cash_drawer_view_improved.py
"""

import sys
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import datetime

# Import QApplication first to ensure it's created before any QWidgets
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
app = QApplication.instance() or QApplication(sys.argv)

# Create patches before importing CashDrawerView
patches = [
    # Mock dialog classes
    patch('ui.dialogs.cash_drawer_dialogs.OpenDrawerDialog', MagicMock()),
    patch('ui.dialogs.cash_drawer_dialogs.AddRemoveCashDialog', MagicMock()),
    patch('ui.dialogs.cash_drawer_dialogs.CashMovementDialog', MagicMock()),
    # Mock QMessageBox to prevent any dialog displays
    patch('ui.views.cash_drawer_view.QMessageBox', MagicMock()),
    # Patch QTableView and QTableView methods that might cause issues
    patch('PySide6.QtWidgets.QTableView.setModel', MagicMock()),
]

# Apply all patches
patchers = [p.start() for p in patches]
mock_open_dialog, mock_remove_dialog, mock_cash_movement_dialog, mock_message_box, _ = patchers

# Now it's safe to import
from ui.views.cash_drawer_view import CashDrawerView
from core.services.cash_drawer_service import CashDrawerService
from core.models.cash_drawer import CashDrawerEntry, CashDrawerEntryType

# Very short timeout
pytestmark = pytest.mark.timeout(3)

# --- Helper Functions ---

def create_drawer_entry(id=1, 
                      entry_type=CashDrawerEntryType.START, 
                      amount=Decimal('100.00'), 
                      description="Test entry", 
                      user_id=1, 
                      timestamp=None):
    """Create a test cash drawer entry."""
    if timestamp is None:
        timestamp = datetime.now()
        
    entry = MagicMock(spec=CashDrawerEntry)
    entry.id = id
    entry.entry_type = entry_type
    entry.amount = amount
    entry.description = description
    entry.user_id = user_id
    entry.timestamp = timestamp
    entry.drawer_id = None
    
    return entry

def create_drawer_summary(is_open=False, 
                         current_balance=Decimal('100.00'),
                         initial_amount=Decimal('100.00'),
                         total_in=Decimal('0.00'),
                         total_out=Decimal('0.00'),
                         entries=None,
                         opened_at=None,
                         opened_by=None):
    """Create a test cash drawer summary."""
    if entries is None:
        entries = []
        
    if opened_at is None and is_open:
        opened_at = datetime.now()
        
    if opened_by is None and is_open:
        opened_by = 1
        
    return {
        'is_open': is_open,
        'current_balance': current_balance,
        'initial_amount': initial_amount,
        'total_in': total_in,
        'total_out': total_out,
        'entries_today': entries,
        'opened_at': opened_at,
        'opened_by': opened_by
    }

def cleanup_view(view):
    """Aggressively clean up a view to prevent hanging."""
    if view:
        view.close()
        view.deleteLater()
        # Process events multiple times to ensure cleanup
        for _ in range(5):
            QApplication.processEvents()

# --- Tests ---

def test_close_drawer_dialog():
    """
    Test Case: Verify the close drawer dialog.
    
    This test covers line 206 and tests the branch for closing
    an open drawer, which shows an information dialog since
    the feature is not implemented.
    """
    # Create mock service
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=True)
    
    # Create view
    view = None
    try:
        view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
        
        # Click the open/close button (which should now be "Cerrar Caja")
        view.open_button.click()
        QApplication.processEvents()
        
        # Verify the information dialog was shown with the correct message
        mock_message_box.information.assert_called_once()
        title_arg = mock_message_box.information.call_args[0][1]
        assert "Cierre de Caja" in title_arg
        
        # Reset mock for next test
        mock_message_box.reset_mock()
    finally:
        cleanup_view(view)

def test_open_drawer_value_error():
    """
    Test Case: Verify the error handling in _handle_open_drawer.
    
    This test covers lines 224-247 and tests what happens when
    a ValueError is raised during the drawer opening process.
    """
    # Create mock service
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
    
    # Configure the dialog to return invalid input
    mock_dialog = MagicMock()
    mock_dialog.exec.return_value = True
    mock_dialog.amount_edit.text.return_value = "invalid_amount"  # This will cause a ValueError
    mock_dialog.description_edit.text.return_value = "Test Description"
    mock_open_dialog.return_value = mock_dialog
    
    # Create view
    view = None
    try:
        view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
        
        # Click the open button
        view.open_button.click()
        QApplication.processEvents()
        
        # Verify the error message was shown
        mock_message_box.warning.assert_called_once()
        title_arg = mock_message_box.warning.call_args[0][1]
        assert "Error" in title_arg
        
        # Reset mocks for next test
        mock_message_box.reset_mock()
    finally:
        cleanup_view(view)

def test_add_cash_to_closed_drawer():
    """
    Test Case: Verify _handle_add_cash when drawer is closed.
    
    This test covers lines 254-255 and tests the case when 
    a user tries to add cash to a closed drawer.
    """
    # Create mock service
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
    
    # Create view
    view = None
    try:
        view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
        
        # Try to add cash through the method directly (button would be disabled)
        view._handle_add_cash()
        QApplication.processEvents()
        
        # Verify the error message was shown
        mock_message_box.warning.assert_called_once()
        title_arg = mock_message_box.warning.call_args[0][1]
        msg_arg = mock_message_box.warning.call_args[0][2]
        assert "Error" in title_arg
        assert "caja debe estar abierta" in msg_arg
        
        # Reset mocks for next test
        mock_message_box.reset_mock()
    finally:
        cleanup_view(view)

def test_remove_cash_insufficient_balance():
    """
    Test Case: Verify _handle_remove_cash when insufficient balance.
    
    This test covers lines 279-280 and tests what happens when
    a user tries to remove more cash than is available.
    """
    # Create mock service
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary(
        is_open=True, 
        current_balance=Decimal('100.00')
    )
    
    # Configure the dialog to return an amount greater than the balance
    mock_dialog = MagicMock()
    mock_dialog.exec.return_value = True
    mock_dialog.amount_edit.text.return_value = "200.00"  # More than available
    mock_dialog.description_edit.text.return_value = "Test Withdrawal"
    mock_cash_movement_dialog.return_value = mock_dialog
    
    # Create view
    view = None
    try:
        view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
        
        # Call the remove cash method
        view.remove_cash_button.click()
        QApplication.processEvents()
        
        # Verify the error message was shown
        mock_message_box.warning.assert_called_once()
        title_arg = mock_message_box.warning.call_args[0][1]
        msg_arg = mock_message_box.warning.call_args[0][2]
        assert "Error" in title_arg
        assert "No hay suficiente efectivo" in msg_arg
        
        # Verify the service's remove_cash method was not called
        mock_service.remove_cash.assert_not_called()
        
        # Reset mocks for next test
        mock_message_box.reset_mock()
    finally:
        cleanup_view(view)

def test_remove_cash_value_error():
    """
    Test Case: Verify error handling in _handle_remove_cash.
    
    This test covers lines 287-288 and tests what happens when
    a ValueError is raised during cash removal.
    """
    # Create mock service
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=True)
    
    # Configure the dialog to return invalid input
    mock_dialog = MagicMock()
    mock_dialog.exec.return_value = True
    mock_dialog.amount_edit.text.return_value = "invalid_amount"  # This will cause a ValueError
    mock_dialog.description_edit.text.return_value = "Test Description"
    mock_cash_movement_dialog.return_value = mock_dialog
    
    # Create view
    view = None
    try:
        view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
        
        # Click the remove cash button
        view.remove_cash_button.click()
        QApplication.processEvents()
        
        # Verify the error message was shown
        mock_message_box.warning.assert_called_once()
        title_arg = mock_message_box.warning.call_args[0][1]
        assert "Error" in title_arg
        
        # Reset mocks for next test
        mock_message_box.reset_mock()
    finally:
        cleanup_view(view)

def test_print_report():
    """
    Test Case: Verify the print report functionality.
    
    This test covers lines 299-304 and tests the _print_report method
    which shows an information dialog.
    """
    # Create mock service
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=True)
    
    # Create view
    view = None
    try:
        view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
        
        # Click the print report button
        view.print_report_button.click()
        QApplication.processEvents()
        
        # Verify the information message was shown
        mock_message_box.information.assert_called_once()
        title_arg = mock_message_box.information.call_args[0][1]
        assert "Imprimir Reporte" in title_arg
        
        # Reset mocks for next test
        mock_message_box.reset_mock()
    finally:
        cleanup_view(view)

def test_remove_cash_from_closed_drawer():
    """
    Test Case: Verify _handle_remove_cash when drawer is closed.
    
    This provides additional coverage by testing another error case
    in the remove cash functionality.
    """
    # Create mock service
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
    
    # Create view
    view = None
    try:
        view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
        
        # Try to remove cash through the method directly (button would be disabled)
        view._handle_remove_cash()
        QApplication.processEvents()
        
        # Verify the error message was shown
        mock_message_box.warning.assert_called_once()
        title_arg = mock_message_box.warning.call_args[0][1]
        msg_arg = mock_message_box.warning.call_args[0][2]
        assert "Error" in title_arg
        assert "caja debe estar abierta" in msg_arg
    finally:
        cleanup_view(view)

# Clean up all patches at the end of the module
for p in patches:
    p.stop() 