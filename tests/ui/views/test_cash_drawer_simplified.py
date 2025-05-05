"""
Simplified test file for cash drawer operations with minimalistic mocking.
This version focuses on testing core functionality with less complex setup.
"""

from unittest.mock import patch, MagicMock
import pytest
from decimal import Decimal

pytestmark = pytest.mark.timeout(3)

def create_drawer_summary(is_open=False, current_balance=Decimal('100.00')):
    """Helper to create a simplified drawer summary."""
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
    from ui.views.cash_drawer_view import CashDrawerView
    from core.services.cash_drawer_service import CashDrawerService
    
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

def test_remove_cash_from_closed_drawer(qtbot):
    """Test removing cash from a closed drawer shows appropriate error."""
    from ui.views.cash_drawer_view import CashDrawerView
    from core.services.cash_drawer_service import CashDrawerService
    
    mock_service = MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
    
    view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
    qtbot.addWidget(view)
    view.current_drawer_id = 1
    
    with patch('ui.views.cash_drawer_view.QMessageBox.warning') as mock_warning:
        view._handle_remove_cash()
        mock_warning.assert_called_once()
        assert "caja debe estar abierta" in mock_warning.call_args[0][2]
    
    view.close()
    view.deleteLater()

def test_add_cash_success(qtbot):
    """Test successfully adding cash to an open drawer."""
    from ui.views.cash_drawer_view import CashDrawerView
    from core.services.cash_drawer_service import CashDrawerService
    
    with patch('ui.views.cash_drawer_view.CashMovementDialog') as mock_dialog_class:
        mock_service = MagicMock(spec=CashDrawerService)
        mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=True)
        
        # Setup mock dialog
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = True
        mock_dialog.entry = True  # Simulate successful entry
        mock_dialog_class.return_value = mock_dialog
        
        view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
        qtbot.addWidget(view)
        view.current_drawer_id = 1
        
        # Add cash
        view.add_cash_button.click()
        
        # The dialog is responsible for calling the service, so we check dialog instantiation
        mock_dialog_class.assert_called_once_with(mock_service, 1, is_adding=True, parent=view)
        assert mock_dialog.exec.called
        
        view.close()
        view.deleteLater()

# Add more tests as needed for remove_cash, etc.