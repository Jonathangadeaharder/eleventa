"""
Improved tests for the CashDrawerView UI component.

This file contains tests for the CashDrawerView component with improved stability:
1. Uses pytest-qt fixtures for QApplication management
2. Properly mocks service classes and dialogs
3. Contains simplified tests focusing on core functionality
"""

import sys
import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import MagicMock, patch

# Import Qt support module first - this sets up the environment
from tests.ui.qt_support import (
    Qt, QApplication, QMessageBox, QT_IMPORTS_AVAILABLE
)

# Skip all tests if Qt imports aren't available
pytestmark = [
    pytest.mark.skipif(not QT_IMPORTS_AVAILABLE, reason="PySide6 imports not available"),
    pytest.mark.timeout(5)  # Set timeout to prevent hanging tests
]

# Import application components after Qt environment is configured
from ui.views.cash_drawer_view import CashDrawerView
from core.services.cash_drawer_service import CashDrawerService
from core.models.cash_drawer import CashDrawerEntry, CashDrawerEntryType
from ui.dialogs.cash_drawer_dialogs import OpenDrawerDialog, CashMovementDialog

# --- Helper Functions ---

def create_drawer_summary(is_open=False, balance=Decimal('100.00')):
    """Create a mock drawer summary for testing."""
    return {
        'is_open': is_open,
        'current_balance': balance,
        'initial_amount': Decimal('100.00'),
        'total_in': Decimal('0.00'),
        'total_out': Decimal('0.00'),
        'entries_today': [],
        'opened_at': datetime.now() if is_open else None,
        'opened_by': 1 if is_open else None
    }

# --- Fixtures ---

@pytest.fixture
def mock_cash_drawer_service():
    """Create a mock cash drawer service."""
    service = MagicMock(spec=CashDrawerService)
    service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
    return service

# --- Tests ---

# Simple test to check if the module loads properly
def test_module_loads():
    """Simple test to ensure module loads properly."""
    assert True

@pytest.mark.skipif(not QT_IMPORTS_AVAILABLE, reason="PySide6 imports not available")
@patch('ui.views.cash_drawer_view.OpenDrawerDialog')
@patch('ui.views.cash_drawer_view.CashMovementDialog')
@patch('ui.views.cash_drawer_view.QMessageBox')
def test_cash_drawer_closed_state(mock_message_box, mock_movement_dialog, 
                                 mock_open_dialog, qtbot, mock_cash_drawer_service):
    """Test the CashDrawerView in closed state."""
    # Configure mock service to return a closed drawer
    mock_cash_drawer_service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
    
    # Configure dialog mocks
    mock_open_dialog_instance = MagicMock()
    mock_open_dialog.return_value = mock_open_dialog_instance
    mock_open_dialog_instance.exec.return_value = False  # Dialog canceled by default
    
    # Create the view
    view = CashDrawerView(cash_drawer_service=mock_cash_drawer_service, user_id=1)
    qtbot.addWidget(view)
    
    try:
        # Test initial state
        assert view.status_label.text() == "Cerrada"
        assert not view.add_cash_button.isEnabled()
        assert not view.remove_cash_button.isEnabled()
        assert view.open_close_button.text() == "Abrir caja"
        assert view.open_close_button.isEnabled()
        
        # Verify service was called
        mock_cash_drawer_service.get_drawer_summary.assert_called_once()
    finally:
        # Cleanup
        view.close()
        view.deleteLater()
        qtbot.wait(50)  # Allow events to process

@patch('ui.views.cash_drawer_view.QMessageBox')
def test_close_drawer_dialog(mock_message_box, cash_drawer_view, mock_cash_drawer_service, qtbot):
    """
    Test Case: Verify the close drawer dialog.
    
    This test covers line 206 and tests the branch for closing
    an open drawer, which shows an information dialog since
    the feature is not implemented.
    """
    # Configure an open drawer
    mock_cash_drawer_service.get_drawer_summary.return_value = create_drawer_summary(is_open=True)
    cash_drawer_view._refresh_data()
    
    # Click the open/close button (which should now be "Cerrar Caja")
    qtbot.mouseClick(cash_drawer_view.open_button, Qt.LeftButton)
    
    # Verify the information dialog was shown with the correct message
    mock_message_box.information.assert_called_once()
    title_arg = mock_message_box.information.call_args[0][1]
    msg_arg = mock_message_box.information.call_args[0][2]
    assert "Cierre de Caja" in title_arg
    assert "no está implementado" in msg_arg


@patch('ui.views.cash_drawer_view.OpenDrawerDialog')
@patch('ui.views.cash_drawer_view.QMessageBox')
def test_open_drawer_value_error(mock_message_box, mock_dialog_class, cash_drawer_view, mock_cash_drawer_service, qtbot):
    """
    Test Case: Verify the error handling in _handle_open_drawer.
    
    This test covers lines 224-247 and tests what happens when
    a ValueError is raised during the drawer opening process.
    """
    # Configure a closed drawer
    mock_cash_drawer_service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
    cash_drawer_view._refresh_data()
    
    # Configure the dialog to return invalid input
    mock_dialog = MagicMock()
    mock_dialog.exec.return_value = True
    mock_dialog.amount_edit.text.return_value = "invalid_amount"  # This will cause a ValueError
    mock_dialog.description_edit.text.return_value = "Test Description"
    mock_dialog_class.return_value = mock_dialog
    
    # Click the open button
    qtbot.mouseClick(cash_drawer_view.open_button, Qt.LeftButton)
    
    # Verify the error message was shown
    mock_message_box.warning.assert_called_once()
    title_arg = mock_message_box.warning.call_args[0][1]
    assert "Error" in title_arg


@patch('ui.views.cash_drawer_view.QMessageBox')
def test_add_cash_to_closed_drawer(mock_message_box, cash_drawer_view, mock_cash_drawer_service, qtbot):
    """
    Test Case: Verify _handle_add_cash when drawer is closed.
    
    This test covers lines 254-255 and tests the case when 
    a user tries to add cash to a closed drawer.
    """
    # Configure a closed drawer
    mock_cash_drawer_service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
    cash_drawer_view._refresh_data()
    
    # Try to add cash (button should be disabled, so we call the method directly)
    cash_drawer_view._handle_add_cash()
    
    # Verify the error message was shown
    mock_message_box.warning.assert_called_once()
    title_arg = mock_message_box.warning.call_args[0][1]
    msg_arg = mock_message_box.warning.call_args[0][2]
    assert "Error" in title_arg
    assert "caja debe estar abierta" in msg_arg


@patch('ui.views.cash_drawer_view.CashMovementDialog')
@patch('ui.views.cash_drawer_view.QMessageBox')
def test_remove_cash_insufficient_balance(mock_message_box, mock_dialog_class, cash_drawer_view, mock_cash_drawer_service, qtbot):
    """
    Test Case: Verify _handle_remove_cash when insufficient balance.
    
    This test covers lines 279-280 and tests what happens when
    a user tries to remove more cash than is available.
    """
    # Configure an open drawer with a specific balance
    current_balance = Decimal('100.00')
    mock_cash_drawer_service.get_drawer_summary.return_value = create_drawer_summary(
        is_open=True, 
        current_balance=current_balance
    )
    cash_drawer_view._refresh_data()
    
    # Configure the dialog to return an amount greater than the balance
    mock_dialog = MagicMock()
    mock_dialog.exec.return_value = True
    mock_dialog.amount_edit.text.return_value = "200.00"  # More than available
    mock_dialog.description_edit.text.return_value = "Test Withdrawal"
    mock_dialog_class.return_value = mock_dialog
    
    # Click the remove cash button
    qtbot.mouseClick(cash_drawer_view.remove_cash_button, Qt.LeftButton)
    
    # Verify the error message was shown
    mock_message_box.warning.assert_called_once()
    title_arg = mock_message_box.warning.call_args[0][1]
    msg_arg = mock_message_box.warning.call_args[0][2]
    assert "Error" in title_arg
    assert "No hay suficiente efectivo" in msg_arg
    
    # Verify the service's remove_cash method was not called
    mock_cash_drawer_service.remove_cash.assert_not_called()


@patch('ui.views.cash_drawer_view.CashMovementDialog')
@patch('ui.views.cash_drawer_view.QMessageBox')
def test_remove_cash_value_error(mock_message_box, mock_dialog_class, cash_drawer_view, mock_cash_drawer_service, qtbot):
    """
    Test Case: Verify error handling in _handle_remove_cash.
    
    This test covers lines 287-288 and tests what happens when
    a ValueError is raised during cash removal.
    """
    # Configure an open drawer
    mock_cash_drawer_service.get_drawer_summary.return_value = create_drawer_summary(is_open=True)
    cash_drawer_view._refresh_data()
    
    # Configure the dialog to return invalid input
    mock_dialog = MagicMock()
    mock_dialog.exec.return_value = True
    mock_dialog.amount_edit.text.return_value = "invalid_amount"  # This will cause a ValueError
    mock_dialog.description_edit.text.return_value = "Test Description"
    mock_dialog_class.return_value = mock_dialog
    
    # Click the remove cash button
    qtbot.mouseClick(cash_drawer_view.remove_cash_button, Qt.LeftButton)
    
    # Verify the error message was shown
    mock_message_box.warning.assert_called_once()
    title_arg = mock_message_box.warning.call_args[0][1]
    assert "Error" in title_arg


@patch('ui.views.cash_drawer_view.QMessageBox')
def test_print_report(mock_message_box, cash_drawer_view, mock_cash_drawer_service, qtbot):
    """
    Test Case: Verify the print report functionality.
    
    This test covers lines 299-304 and tests the _print_report method
    which shows an information dialog.
    """
    # Configure an open drawer to enable the button
    mock_cash_drawer_service.get_drawer_summary.return_value = create_drawer_summary(is_open=True)
    cash_drawer_view._refresh_data()
    
    # Click the print report button
    qtbot.mouseClick(cash_drawer_view.print_report_button, Qt.LeftButton)
    
    # Verify the information message was shown
    mock_message_box.information.assert_called_once()
    title_arg = mock_message_box.information.call_args[0][1]
    msg_arg = mock_message_box.information.call_args[0][2]
    assert "Imprimir Reporte" in title_arg
    assert "no está implementada" in msg_arg


@patch('ui.views.cash_drawer_view.QMessageBox')
def test_remove_cash_from_closed_drawer(mock_message_box, cash_drawer_view, mock_cash_drawer_service, qtbot):
    """
    Test Case: Verify _handle_remove_cash when drawer is closed.
    
    This provides additional coverage by testing another error case
    in the remove cash functionality.
    """
    # Configure a closed drawer
    mock_cash_drawer_service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
    cash_drawer_view._refresh_data()
    
    # Try to remove cash (button should be disabled, so we call the method directly)
    cash_drawer_view._handle_remove_cash()
    
    # Verify the error message was shown
    mock_message_box.warning.assert_called_once()
    title_arg = mock_message_box.warning.call_args[0][1]
    msg_arg = mock_message_box.warning.call_args[0][2]
    assert "Error" in title_arg
    assert "caja debe estar abierta" in msg_arg 