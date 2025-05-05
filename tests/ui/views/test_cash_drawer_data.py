"""
Test for CashDrawerView data display and refresh functionality.
"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone

# Set a reasonable timeout for tests
pytestmark = pytest.mark.timeout(3)

def create_drawer_summary(is_open=True, balance=Decimal('100.00'), initial_amount=Decimal('100.00'), total_in=Decimal('50.00'), total_out=Decimal('25.00'), entries=None):
    # Use a fixed datetime instead of datetime.now() to avoid test flakiness
    fixed_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    
    if entries is None:
        entries = [
            {
                'id': 1,
                'type': 'add',
                'amount': Decimal('50.00'),
                'reason': 'Deposit',
                'timestamp': fixed_time,
                'user_id': 1
            },
            {
                'id': 2,
                'type': 'remove',
                'amount': Decimal('25.00'),
                'reason': 'Withdrawal',
                'timestamp': fixed_time,
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
        'opened_at': fixed_time if is_open else None,
        'opened_by': 1 if is_open else None
    }

# Import the view and service after defining test data
from ui.views.cash_drawer_view import CashDrawerView
from core.services.cash_drawer_service import CashDrawerService

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

def test_refresh_data_display(qtbot, mocker):
    """Test that the view refreshes data correctly."""
    mock_service = mocker.MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary()
    view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
    qtbot.addWidget(view)
    
    # Check initial display
    assert "$100.00" in view.balance_label.text()
    assert "$100.00" in view.initial_amount_label.text()
    assert "$50.00" in view.total_in_label.text()
    assert "$25.00" in view.total_out_label.text()
    
    # Change data and refresh
    mock_service.get_drawer_summary.return_value = create_drawer_summary(
        balance=Decimal('200.00'),
        initial_amount=Decimal('150.00'),
        total_in=Decimal('100.00'),
        total_out=Decimal('50.00')
    )
    view._refresh_data()
    
    # Verify updated display
    assert "$200.00" in view.balance_label.text()
    assert "$150.00" in view.initial_amount_label.text()
    assert "$100.00" in view.total_in_label.text()
    assert "$50.00" in view.total_out_label.text()
    
    # Verify service was called twice (once on init, once on refresh)
    assert mock_service.get_drawer_summary.call_count == 2
    
    # Clean up
    view.close()
    view.deleteLater()

def test_drawer_state_transitions(qtbot, mocker):
    """Test the UI state transitions between open and closed drawer."""
    mock_service = mocker.MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
    view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
    qtbot.addWidget(view)
    
    # Test initial state (closed drawer)
    assert view.open_button.isEnabled()
    assert not view.add_cash_button.isEnabled()
    assert not view.remove_cash_button.isEnabled()
    
    # Change to open drawer state
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=True)
    view._refresh_data()
    
    # Test updated state (open drawer)
    assert "Cerrar" in view.open_button.text()  # Text changes to "Close Drawer"
    assert view.add_cash_button.isEnabled()
    assert view.remove_cash_button.isEnabled()
    
    # Change back to closed drawer state
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
    view._refresh_data()
    
    # Test final state (closed drawer again)
    assert "Abrir" in view.open_button.text()  # Text changes to "Open Drawer"
    assert not view.add_cash_button.isEnabled()
    assert not view.remove_cash_button.isEnabled()
    
    # Clean up
    view.close()
    view.deleteLater()

def test_empty_entries(qtbot, mocker):
    """Test that the view handles empty entries properly."""
    mock_service = mocker.MagicMock(spec=CashDrawerService)
    mock_service.get_drawer_summary.return_value = create_drawer_summary(entries=[])
    view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
    qtbot.addWidget(view)
    
    # Verify the table exists and has been initialized
    assert view.entries_table is not None
    
    # Check that the model is updated with empty entries
    assert view.table_model.rowCount() == 0
    
    # Clean up
    view.close()
    view.deleteLater()

def test_add_cash_warning(qtbot, mocker):
    """Test add cash warning for closed drawer."""
    mock_message_box = mocker.patch('ui.views.cash_drawer_view.QMessageBox')
    mock_service = mocker.MagicMock(spec=CashDrawerService)
    # Set drawer as closed
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
    
    view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
    qtbot.addWidget(view)
    
    view._handle_add_cash()
    mock_message_box.warning.assert_called_once()
    # Verify warning message contains expected text
    assert "caja debe estar abierta" in mock_message_box.warning.call_args[0][2]
    
    # Clean up
    view.close()
    view.deleteLater()

def test_remove_cash_warning(qtbot, mocker):
    """Test remove cash warning for closed drawer."""
    mock_message_box = mocker.patch('ui.views.cash_drawer_view.QMessageBox')
    mock_service = mocker.MagicMock(spec=CashDrawerService)
    # Set drawer as closed
    mock_service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
    
    view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
    qtbot.addWidget(view)
    
    view._handle_remove_cash()
    mock_message_box.warning.assert_called_once()
    # Verify warning message contains expected text
    assert "caja debe estar abierta" in mock_message_box.warning.call_args[0][2]
    
    # Clean up
    view.close()
    view.deleteLater() 