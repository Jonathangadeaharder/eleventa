"""
Extra test cases for cash drawer view focusing on edge cases and error handling.
"""

from unittest.mock import patch, MagicMock
import pytest
from decimal import Decimal

pytestmark = pytest.mark.timeout(3)

# Patch QMessageBox before importing the view
with patch('ui.views.cash_drawer_view.QMessageBox.warning', MagicMock()):
    from ui.views.cash_drawer_view import CashDrawerView
    from core.services.cash_drawer_service import CashDrawerService

def create_drawer_summary(is_open=False, current_balance=Decimal('100.00')):
    """Helper to create a drawer summary."""
    return {
        'is_open': is_open,
        'current_balance': current_balance,
        'initial_amount': Decimal('100.00') if is_open else Decimal('0.00'),
        'total_in': Decimal('0.00'),
        'total_out': Decimal('0.00'),
        'entries_today': []
    }

def test_add_cash_to_closed_drawer(qtbot):
    """Test adding cash to a closed drawer shows appropriate error."""
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
    view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
    qtbot.addWidget(view)
    view.current_drawer_id = 1
    with patch('ui.views.cash_drawer_view.QMessageBox.warning') as mock_warning:
        view._handle_add_cash()
        mock_warning.assert_called_once()
        assert "caja debe estar abierta" in mock_warning.call_args[0][2]
    view.close()
    view.deleteLater()

def test_invalid_amount_format(qtbot):
    """Test handling invalid amount format."""
    with patch('ui.views.cash_drawer_view.CashMovementDialog') as mock_dialog_class:
        mock_service = MagicMock(spec=CashDrawerService)
        mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=True)
        
        # Setup mock dialog with invalid amount
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = True
        mock_dialog.amount_edit = MagicMock()
        mock_dialog.amount_edit.value.return_value = "invalid-amount"
        mock_dialog.description_edit = MagicMock()
        mock_dialog.description_edit.text.return_value = "Test"
        mock_dialog.entry = None  # Dialog failed to create an entry
        mock_dialog_class.return_value = mock_dialog
        
        view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
        qtbot.addWidget(view)
        view.current_drawer_id = 1
        
        # The view delegates input validation and warning to the dialog.
        # We need to verify the dialog is called.
        view.add_cash_button.click()
        mock_dialog_class.assert_called_once()
        mock_dialog.exec.assert_called_once()
        
        # The service should NOT be called if the dialog handles the error
        mock_service.add_cash.assert_not_called()
        
        view.close()
        view.deleteLater()

def test_insufficient_funds_for_removal(qtbot):
    """Test handling insufficient funds when removing cash."""
    with patch('ui.views.cash_drawer_view.CashMovementDialog') as mock_dialog_class, \
         patch('ui.views.cash_drawer_view.QMessageBox', MagicMock()) as mock_message_box:
        mock_service = MagicMock(spec=CashDrawerService)
        mock_service.get_drawer_summary.return_value = create_drawer_summary(
            is_open=True, 
            current_balance=Decimal('50.00')
        )
        
        # Setup mock dialog with amount greater than balance
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = True
        mock_dialog.amount_edit = MagicMock()
        mock_dialog.amount_edit.value.return_value = 100.00  # Greater than balance
        mock_dialog.description_edit = MagicMock()
        mock_dialog.description_edit.text.return_value = "Test withdrawal"
        mock_dialog.entry = None  # Dialog failed to create an entry
        mock_dialog_class.return_value = mock_dialog
        
        view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
        qtbot.addWidget(view)
        view.current_drawer_id = 1
        
        # Remove cash button should call the dialog
        view.remove_cash_button.click()
        mock_dialog_class.assert_called_once()
        mock_dialog.exec.assert_called_once()
        
        # Verify the service should NOT be called (handled by the dialog)
        mock_service.remove_cash.assert_not_called()
        
        view.close()
        view.deleteLater()

def test_service_error_handling(qtbot):
    """Test handling errors from cash drawer service."""
    with patch('ui.views.cash_drawer_view.CashMovementDialog') as mock_dialog_class, \
         patch('ui.views.cash_drawer_view.QMessageBox', MagicMock()) as mock_message_box:
        mock_service = MagicMock(spec=CashDrawerService)
        mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=True)
        
        # Setup mock dialog
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = True
        mock_dialog.amount_edit = MagicMock()
        mock_dialog.amount_edit.value.return_value = 50.00
        mock_dialog.description_edit = MagicMock()
        mock_dialog.description_edit.text.return_value = "Test"
        mock_dialog.entry = None  # Dialog failed because service threw an exception
        mock_dialog_class.return_value = mock_dialog
        
        view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
        qtbot.addWidget(view)
        view.current_drawer_id = 1
        
        # The view delegates error handling to the dialog
        view.add_cash_button.click()
        mock_dialog_class.assert_called_once()
        mock_dialog.exec.assert_called_once()
        
        # The view doesn't call the service directly
        mock_service.add_cash.assert_not_called()
        
        view.close()
        view.deleteLater()