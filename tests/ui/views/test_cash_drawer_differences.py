"""
Test for CashDrawerView differences display.
"""
import sys
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

# Import QApplication first to ensure it's created before any QWidgets
from PySide6.QtWidgets import QApplication
app = QApplication.instance() or QApplication(sys.argv)

# Create patches before importing CashDrawerView
patches = [
    # Mock dialog classes
    patch('ui.dialogs.cash_drawer_dialogs.OpenCashDrawerDialog', MagicMock()),
    patch('ui.dialogs.cash_drawer_dialogs.AddRemoveCashDialog', MagicMock()),
    # Mock QMessageBox to prevent any dialog displays
    patch('ui.views.cash_drawer_view.QMessageBox', MagicMock()),
    # Patch QTableView and QTableView methods that might cause issues
    patch('PySide6.QtWidgets.QTableView.setModel', MagicMock()),
]

# Apply all patches
for p in patches:
    p.start()

# Now it's safe to import
from ui.views.cash_drawer_view import CashDrawerView
from core.services.cash_drawer_service import CashDrawerService

# Very short timeout
pytestmark = pytest.mark.timeout(3)

def test_cash_drawer_difference_display():
    """Test that cash differences are displayed with appropriate styling."""
    # Create mock service
    mock_service = MagicMock(spec=CashDrawerService)
    
    # Test with negative difference (shortage)
    negative_diff_summary = {
        'is_open': True,
        'current_balance': Decimal('90.00'),
        'initial_amount': Decimal('100.00'),
        'total_in': Decimal('0.00'),
        'total_out': Decimal('10.00'),
        'entries_today': [],
        'opened_at': None,
        'opened_by': 1
    }
    mock_service.get_drawer_summary.return_value = negative_diff_summary
    
    # Create view
    view = None
    try:
        view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
        
        # Verify negative difference
        assert "-$10.00" in view.difference_label.text()
        assert "color: red" in view.difference_label.styleSheet()
        
        # Test with positive difference (surplus)
        positive_diff_summary = {
            'is_open': True,
            'current_balance': Decimal('110.00'),
            'initial_amount': Decimal('100.00'),
            'total_in': Decimal('10.00'),
            'total_out': Decimal('0.00'),
            'entries_today': [],
            'opened_at': None,
            'opened_by': 1
        }
        mock_service.get_drawer_summary.return_value = positive_diff_summary
        
        # Call refresh directly to update the view
        view._refresh_data()
        QApplication.processEvents()
        
        # Verify positive difference
        assert "$10.00" in view.difference_label.text()
        assert "color: blue" in view.difference_label.styleSheet()
        
    finally:
        # Aggressive cleanup
        if view:
            view.close()
            view.deleteLater()
            for _ in range(5):
                QApplication.processEvents()
    
    # Clean up patches
    for p in patches:
        p.stop() 