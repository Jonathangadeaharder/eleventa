"""
Test for CashDrawerView open state.
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
from core.models.cash_drawer import CashDrawerEntry, CashDrawerEntryType

# Very short timeout
pytestmark = pytest.mark.timeout(3)

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

def test_cash_drawer_open_state():
    """Test that the view correctly displays an open cash drawer."""
    # Create mock service with an open drawer
    mock_service = MagicMock(spec=CashDrawerService)
    
    # Create an open drawer with some entries
    timestamp = datetime(2023, 5, 15, 8, 30)
    entries = [
        create_drawer_entry(timestamp=timestamp, amount=Decimal('100.00')),
        create_drawer_entry(id=2, entry_type=CashDrawerEntryType.IN, amount=Decimal('50.00'), timestamp=timestamp)
    ]
    
    open_summary = {
        'is_open': True, 
        'current_balance': Decimal('150.00'), 
        'initial_amount': Decimal('100.00'),
        'total_in': Decimal('50.00'),
        'total_out': Decimal('0.00'),
        'entries_today': entries,
        'opened_at': timestamp,
        'opened_by': 1
    }
    
    mock_service.get_drawer_summary.return_value = open_summary
    
    # Create view
    view = None
    try:
        view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
        
        # Tests for open drawer state
        assert view.status_label.text() == "Abierta"
        assert "color: green" in view.status_label.styleSheet()
        assert view.add_cash_button.isEnabled()
        assert view.remove_cash_button.isEnabled()
        assert view.print_report_button.isEnabled()
        assert view.open_button.text() == "Cerrar Caja"
        
        # Test summary display 
        assert "$150.00" in view.balance_label.text()
        assert "$100.00" in view.initial_amount_label.text()
        assert "$50.00" in view.total_in_label.text()
        assert "$0.00" in view.total_out_label.text()
        
        # Mock button clicks with QMessageBox patched
        with patch('ui.views.cash_drawer_view.QMessageBox.information'):
            # Test add_cash_button click
            mock_dialog = MagicMock()
            mock_dialog.exec.return_value = True
            mock_dialog.amount_edit.text.return_value = "25.00"
            mock_dialog.description_edit.text.return_value = "Test deposit"
            
            with patch('ui.views.cash_drawer_view.CashMovementDialog', return_value=mock_dialog):
                view.add_cash_button.click()
                QApplication.processEvents()
                mock_service.add_cash.assert_called_once()
        
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