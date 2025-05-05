"""
Test for CashDrawerView open state.
"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone

pytestmark = pytest.mark.timeout(3)

# Create fixed datetime for testing
FIXED_TIME = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

# Import the classes we need to test
from ui.views.cash_drawer_view import CashDrawerView
from core.services.cash_drawer_service import CashDrawerService
from core.models.cash_drawer import CashDrawerEntry, CashDrawerEntryType

# Mock Qt components as needed
@pytest.fixture(autouse=True)
def patch_qt(monkeypatch, mocker):
    # Mock Qt dialogs to prevent them from showing
    mocker.patch('ui.views.cash_drawer_view.OpenDrawerDialog')
    mocker.patch('ui.views.cash_drawer_view.CashMovementDialog')
    mocker.patch('ui.views.cash_drawer_view.QMessageBox')
    # Ensure QHeaderView.setSectionResizeMode doesn't cause issues
    header_mock = mocker.MagicMock()
    monkeypatch.setattr('PySide6.QtWidgets.QHeaderView.setSectionResizeMode', header_mock)
    return header_mock

def create_open_drawer_summary():
    """Create a summary for an open cash drawer."""
    entries = [
        {
            'id': 1,
            'type': 'open',
            'amount': Decimal('100.00'),
            'reason': 'Initial amount',
            'timestamp': FIXED_TIME,
            'user_id': 1
        },
        {
            'id': 2,
            'type': 'add',
            'amount': Decimal('50.00'),
            'reason': 'Deposit',
            'timestamp': FIXED_TIME,
            'user_id': 1
        }
    ]
    
    return {
        'is_open': True,
        'current_balance': Decimal('150.00'),
        'initial_amount': Decimal('100.00'),
        'total_in': Decimal('50.00'),
        'total_out': Decimal('0.00'),
        'entries_today': entries,
        'opened_at': FIXED_TIME,
        'opened_by': 1
    }

def test_cash_drawer_open_state(qtbot, mocker):
    """Test the view's state when the cash drawer is open."""
    # Setup the mock service
    mock_service = mocker.MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_open_drawer_summary()
    
    # Create the view
    view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
    qtbot.addWidget(view)
    
    # Verify the open state is displayed correctly
    assert view.status_label.text() == "Abierta"
    assert "color: green" in view.status_label.styleSheet()
    assert view.add_cash_button.isEnabled()
    assert view.remove_cash_button.isEnabled()
    assert view.print_report_button.isEnabled()
    assert view.open_button.text() == "Cerrar Caja"
    assert "$150.00" in view.balance_label.text()
    assert "$100.00" in view.initial_amount_label.text()
    assert "$50.00" in view.total_in_label.text()
    assert "$0.00" in view.total_out_label.text()
    
    # Testing add cash functionality with dialog
    mock_dialog = mocker.MagicMock()
    mock_dialog.exec.return_value = True
    mock_dialog.entry = True  # Simulate successful dialog operation
    
    # Set up the CashMovementDialog mock
    mocker.patch('ui.views.cash_drawer_view.CashMovementDialog', return_value=mock_dialog)
    
    # Simulate clicking the add cash button
    view.add_cash_button.click()
    
    # Verify the dialog was created with correct parameters
    from ui.views.cash_drawer_view import CashMovementDialog
    CashMovementDialog.assert_called_once()
    assert CashMovementDialog.call_args[0][0] == mock_service
    assert CashMovementDialog.call_args[0][1] == 1  # user_id
    assert CashMovementDialog.call_args[1]['is_adding'] == True
    
    # Verify the dialog was executed
    mock_dialog.exec.assert_called_once()
    
    # Clean up
    view.close()
    view.deleteLater()

def test_open_button_behavior_when_open(qtbot, mocker):
    """Test the behavior of the open button when drawer is already open."""
    # Setup the mock service
    mock_service = mocker.MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_open_drawer_summary()
    
    # Create the view
    view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
    qtbot.addWidget(view)
    
    # Open button should be labeled as "Cerrar Caja" when drawer is open
    assert view.open_button.text() == "Cerrar Caja"
    
    # Setup QMessageBox mock
    message_box_mock = mocker.patch('ui.views.cash_drawer_view.QMessageBox')
    
    # Test click behavior
    view.open_button.click()
    
    # Verify information dialog shown
    message_box_mock.information.assert_called_once()
    assert "Cierre de Caja" in message_box_mock.information.call_args[0][1]
    
    # Clean up
    view.close()
    view.deleteLater()
