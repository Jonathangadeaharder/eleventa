"""
Test for CashDrawerView differences display.
"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone

pytestmark = pytest.mark.timeout(3)

# Import view and service
from ui.views.cash_drawer_view import CashDrawerView
from core.services.cash_drawer_service import CashDrawerService

# Create fixed datetime for testing
FIXED_TIME = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

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

def test_cash_drawer_difference_display(qtbot, mocker):
    """Test the display of cash drawer differences (negative and positive)."""
    mock_service = mocker.MagicMock(spec=CashDrawerService)
    negative_diff_summary = {
        'is_open': True,
        'current_balance': Decimal('80.00'),  # Changed from 90 to show negative difference
        'initial_amount': Decimal('100.00'),
        'total_in': Decimal('0.00'),
        'total_out': Decimal('10.00'),
        'entries_today': [],
        'opened_at': FIXED_TIME,
        'opened_by': 1
    }
    mock_service.get_drawer_summary.return_value = negative_diff_summary
    view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
    qtbot.addWidget(view)
    
    # Verify negative difference display (flexible formatting)
    diff_text = view.difference_label.text()
    assert "-" in diff_text or "(" in diff_text  # Check for negative value in accounting format
    assert "10" in diff_text.replace(",", "").replace("$", "").replace("(", "").replace(")", "")
    assert "red" in view.difference_label.styleSheet().lower()
    
    # Test positive difference
    positive_diff_summary = {
        'is_open': True,
        'current_balance': Decimal('120.00'),  # Changed from 110 to show positive difference
        'initial_amount': Decimal('100.00'),
        'total_in': Decimal('10.00'),
        'total_out': Decimal('0.00'),
        'entries_today': [],
        'opened_at': FIXED_TIME,
        'opened_by': 1
    }
    mock_service.get_drawer_summary.return_value = positive_diff_summary
    view._refresh_data()
    
    # Verify positive difference display (flexible formatting)
    diff_text = view.difference_label.text()
    assert "10" in diff_text.replace(",", "").replace("$", "")  # Check for positive value
    assert not diff_text.startswith("-")  # Should not be negative
    assert "blue" in view.difference_label.styleSheet().lower()
    
    # Clean up
    view.close()
    view.deleteLater()

def test_zero_difference_display(qtbot, mocker):
    """Test the display when there's no difference."""
    mock_service = mocker.MagicMock(spec=CashDrawerService)
    zero_diff_summary = {
        'is_open': True,
        'current_balance': Decimal('100.00'),
        'initial_amount': Decimal('100.00'),
        'total_in': Decimal('0.00'),
        'total_out': Decimal('0.00'),
        'entries_today': [],
        'opened_at': FIXED_TIME,
        'opened_by': 1
    }
    mock_service.get_drawer_summary.return_value = zero_diff_summary
    view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
    qtbot.addWidget(view)
    
    # Verify zero difference display (flexible formatting)
    diff_text = view.difference_label.text()
    assert "0" in diff_text.replace(",", "").replace(".", "")  # Check for zero
    assert "black" in view.difference_label.styleSheet().lower()
    
    # Clean up
    view.close()
    view.deleteLater()
