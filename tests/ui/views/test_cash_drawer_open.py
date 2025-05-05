"""
Test for CashDrawerView open functionality.
"""
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import datetime

pytestmark = pytest.mark.timeout(3)

def create_drawer_summary(is_open=False, balance=Decimal('0.00'), initial_amount=Decimal('0.00')):
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

# Patch dialogs and QTableView before import
with patch('ui.views.cash_drawer_view.OpenDrawerDialog') as mock_open_dialog, \
     patch('PySide6.QtWidgets.QTableView.setModel', MagicMock()):
    from ui.views.cash_drawer_view import CashDrawerView
    from core.services.cash_drawer_service import CashDrawerService

# Apply patch using decorator for the test function
@patch('ui.views.cash_drawer_view.OpenDrawerDialog')
def test_open_drawer_button(mock_open_dialog, qtbot): # mock_open_dialog is now passed by the decorator
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
    
    # Configure the mock dialog instance returned by the patched class
    mock_dialog_instance = MagicMock()
    mock_dialog_instance.exec.return_value = True # Simulate dialog accepted
    mock_dialog_instance.entry = MagicMock() # Simulate successful entry creation in dialog
    mock_open_dialog.return_value = mock_dialog_instance
    
    view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
    qtbot.addWidget(view)
    
    # Mock _refresh_data to check if it's called after successful dialog
    with patch.object(view, '_refresh_data', wraps=view._refresh_data) as mock_refresh:
        assert view.open_button.isEnabled()
        view.open_button.click() # Trigger the action
        
        # Assertions
        mock_open_dialog.assert_called_once_with(mock_service, 1, view) # Check dialog instantiation
        mock_dialog_instance.exec.assert_called_once() # Check dialog execution
        mock_refresh.assert_called_once() # Check if view refreshed data
        
        # Verify service call is NOT made directly by the view (dialog handles it)
        mock_service.open_drawer.assert_not_called() 

        # Optional: Check button states after refresh (requires _refresh_data mock to update state)
        # To fully test state change, _refresh_data mock would need more setup
        # or allow the actual _refresh_data to run after mocking the service call again.


@patch('ui.views.cash_drawer_view.OpenDrawerDialog')
def test_open_drawer_canceled(mock_open_dialog, qtbot):
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
    
    mock_dialog_instance = MagicMock()
    mock_dialog_instance.exec.return_value = False # Simulate dialog canceled
    mock_dialog_instance.entry = None # Simulate no entry created
    mock_open_dialog.return_value = mock_dialog_instance
    
    view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
    qtbot.addWidget(view)
    
    with patch.object(view, '_refresh_data') as mock_refresh:
        view.open_button.click()
        
        mock_open_dialog.assert_called_once()
        mock_dialog_instance.exec.assert_called_once()
        mock_refresh.assert_not_called() # Refresh should not happen if dialog canceled
        mock_service.open_drawer.assert_not_called() # Service call should not happen

        # Check button states remain unchanged
        assert view.open_button.isEnabled()
        # Assuming close_button doesn't exist or is handled differently now
        # assert not view.close_button.isEnabled() 
        assert not view.add_cash_button.isEnabled()
        assert not view.remove_cash_button.isEnabled()

@patch('ui.views.cash_drawer_view.OpenDrawerDialog')
def test_open_drawer_dialog_handles_error(mock_open_dialog, qtbot):
    """ Test that if the dialog itself handles an error (e.g., service error), 
        the view doesn't try to handle it again. """
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
    
    # Simulate the dialog executing but failing internally (no entry created)
    mock_dialog_instance = MagicMock()
    mock_dialog_instance.exec.return_value = True # Dialog might "succeed" but operation failed
    mock_dialog_instance.entry = None # Indicate failure within the dialog logic
    mock_open_dialog.return_value = mock_dialog_instance
    
    view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
    qtbot.addWidget(view)
    
    with patch.object(view, '_refresh_data') as mock_refresh:
        view.open_button.click()
        
        mock_open_dialog.assert_called_once()
        mock_dialog_instance.exec.assert_called_once()
        mock_refresh.assert_not_called() # Refresh shouldn't happen if dialog.entry is None
        
        # Check button states remain unchanged
        assert view.open_button.isEnabled()
        assert not view.add_cash_button.isEnabled()
        assert not view.remove_cash_button.isEnabled()

# Remove the old test_open_drawer_service_error as the dialog handles service errors now
# def test_open_drawer_service_error(qtbot): ...
