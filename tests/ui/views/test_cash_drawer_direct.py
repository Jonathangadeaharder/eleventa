"""
Direct method testing for CashDrawerView.

This file doesn't try to test the full component or UI logic, but just
directly tests specific methods that have low coverage.

It simply patched the QApplication creation at top level to allow importing
the view class without errors.
"""

import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import datetime

# Create a fake QApplication
with patch('PySide6.QtWidgets.QApplication'):
    # Import what we need
    from ui.views.cash_drawer_view import CashDrawerView, QMessageBox
    from core.services.cash_drawer_service import CashDrawerService
    
# Utility functions
def create_drawer_summary(is_open=False, current_balance=Decimal('100.00')):
    return {
        'is_open': is_open,
        'current_balance': current_balance,
        'initial_amount': Decimal('100.00'),
        'total_in': Decimal('0.00'),
        'total_out': Decimal('0.00'),
        'entries_today': [],
        'opened_at': datetime.now() if is_open else None,
        'opened_by': 1 if is_open else None
    }

# Create a direct test class to access methods without UI creation
class DirectMethodTester:
    """Helper that exposes methods without UI construction."""
    def __init__(self, service):
        self.cash_drawer_service = service
        self.user_id = 1
        self.current_drawer_id = None
        
        # We don't create UI elements, just mock what methods would access
        self._refresh_data = MagicMock()
        
    def test_handle_open_drawer_when_open(self):
        """Test _handle_open_drawer when drawer is open."""
        with patch.object(QMessageBox, 'information') as mock_info:
            # Create a CashDrawerView instance but patch its __init__ to do nothing
            view = CashDrawerView.__new__(CashDrawerView)
            view.cash_drawer_service = self.cash_drawer_service
            view.current_drawer_id = None
            view.user_id = 1
            
            # Call the method directly
            result = CashDrawerView._handle_open_drawer(view)
            
            # Check that QMessageBox.information was called
            mock_info.assert_called_once()
            title = mock_info.call_args[0][1]
            assert "Cierre de Caja" in title
            
    def test_add_cash_to_closed_drawer(self):
        """Test _handle_add_cash when drawer is closed."""
        with patch.object(QMessageBox, 'warning') as mock_warning:
            # Create a CashDrawerView instance but patch its __init__ to do nothing
            view = CashDrawerView.__new__(CashDrawerView)
            view.cash_drawer_service = self.cash_drawer_service
            view.current_drawer_id = None
            view.user_id = 1
            
            # Call the method directly
            result = CashDrawerView._handle_add_cash(view)
            
            # Check that QMessageBox.warning was called
            mock_warning.assert_called_once()
            msg = mock_warning.call_args[0][2]
            assert "caja debe estar abierta" in msg
            
    def test_remove_cash_from_closed_drawer(self):
        """Test _handle_remove_cash when drawer is closed."""
        with patch.object(QMessageBox, 'warning') as mock_warning:
            # Create a CashDrawerView instance but patch its __init__ to do nothing
            view = CashDrawerView.__new__(CashDrawerView)
            view.cash_drawer_service = self.cash_drawer_service
            view.current_drawer_id = None
            view.user_id = 1
            
            # Call the method directly
            result = CashDrawerView._handle_remove_cash(view)
            
            # Check that QMessageBox.warning was called
            mock_warning.assert_called_once()
            msg = mock_warning.call_args[0][2]
            assert "caja debe estar abierta" in msg
            
    def test_print_report(self):
        """Test _print_report method."""
        with patch.object(QMessageBox, 'information') as mock_info:
            # Create a CashDrawerView instance but patch its __init__ to do nothing
            view = CashDrawerView.__new__(CashDrawerView)
            
            # Call the method directly
            result = CashDrawerView._print_report(view)
            
            # Check that QMessageBox.information was called
            mock_info.assert_called_once()
            title = mock_info.call_args[0][1]
            assert "Imprimir Reporte" in title

# Tests
@pytest.mark.timeout(1)  # Short timeout
def test_handle_open_drawer_when_open():
    """Test the close drawer dialog (line 206)."""
    service = MagicMock(spec=CashDrawerService)
    service.get_drawer_summary.return_value = create_drawer_summary(is_open=True)
    
    tester = DirectMethodTester(service)
    tester.test_handle_open_drawer_when_open()

@pytest.mark.timeout(1)
def test_add_cash_to_closed_drawer():
    """Test add cash to closed drawer (lines 254-255)."""
    service = MagicMock(spec=CashDrawerService)
    service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
    
    tester = DirectMethodTester(service)
    tester.test_add_cash_to_closed_drawer()

@pytest.mark.timeout(1)
def test_remove_cash_from_closed_drawer():
    """Test remove cash from closed drawer."""
    service = MagicMock(spec=CashDrawerService)
    service.get_drawer_summary.return_value = create_drawer_summary(is_open=False)
    
    tester = DirectMethodTester(service)
    tester.test_remove_cash_from_closed_drawer()

@pytest.mark.timeout(1)
def test_print_report():
    """Test print report (lines 299-304)."""
    tester = DirectMethodTester(None)
    tester.test_print_report() 