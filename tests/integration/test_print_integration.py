"""
Integration tests for the printing functionality in the UI views.
Tests the interaction between the UI, services, and the PrintManager.
"""
import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from ui.views.cash_drawer_view import CashDrawerView
from ui.views.corte_view import CorteView
from infrastructure.reporting.print_utility import PrintType, PrintDestination


@pytest.fixture
def mock_print_manager():
    """Create a mock PrintManager instance for testing."""
    mock_pm = MagicMock()
    mock_pm.print.return_value = True
    return mock_pm


@pytest.mark.integration
def test_cash_drawer_print_button(qtbot, mock_cash_drawer_service, mock_print_manager):
    """Test that the print button in the cash drawer view calls the print manager."""
    # Set up mock service to return a drawer summary
    mock_cash_drawer_service.get_drawer_summary.return_value = {
        'is_open': True,
        'current_balance': Decimal('300.01'),
        'initial_amount': Decimal('100.00'),
        'total_in': Decimal('300.01'),
        'total_out': Decimal('100.00'),
        'opened_at': datetime.now(),
        'opened_by': 1,
        'entries_today': []
    }
    
    # Create the cash drawer view
    view = CashDrawerView(mock_cash_drawer_service, user_id=1, print_manager=mock_print_manager)
    qtbot.addWidget(view)
    
    # Verify the print button is enabled (since the drawer is open)
    assert view.print_report_button.isEnabled()
    
    # Click the print button - with message box mocked to prevent showing
    with patch.object(QMessageBox, 'warning', return_value=QMessageBox.Ok) as mock_message, \
         patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok) as mock_error:
        
        qtbot.mouseClick(view.print_report_button, Qt.LeftButton)
        
        # Verify PrintManager.print was called with the correct arguments
        mock_print_manager.print.assert_called_once()
        args, kwargs = mock_print_manager.print.call_args
        
        # Verify the print type and destination
        assert kwargs['print_type'] == PrintType.CASH_DRAWER
        assert kwargs['destination'] == PrintDestination.PREVIEW
        
        # Verify the data contains needed information
        assert 'drawer_id' in kwargs['data']
        assert 'drawer_data' in kwargs['data']
        assert kwargs['data']['drawer_data'] == mock_cash_drawer_service.get_drawer_summary.return_value
        
        # No warning or error messages should have been shown
        mock_message.assert_not_called()
        mock_error.assert_not_called()


@pytest.mark.integration
def test_cash_drawer_print_closed_drawer(qtbot, mock_cash_drawer_service, mock_print_manager):
    """Test that the print button shows a warning when trying to print a closed drawer."""
    # Set up mock service to return a closed drawer
    mock_cash_drawer_service.get_drawer_summary.return_value = {
        'is_open': False,
        'current_balance': Decimal('0.00'),
        'initial_amount': Decimal('0.00'),
        'total_in': Decimal('0.00'),
        'total_out': Decimal('0.00'),
        'opened_at': None,
        'opened_by': None,
        'entries_today': []
    }
    
    # Create the cash drawer view
    view = CashDrawerView(mock_cash_drawer_service, user_id=1, print_manager=mock_print_manager)
    qtbot.addWidget(view)
    
    # Verify the print button is disabled (since the drawer is closed)
    assert not view.print_report_button.isEnabled()
    
    # Force enable the button for testing
    view.print_report_button.setEnabled(True)
    
    # Click the print button - with message box mocked to prevent showing
    with patch.object(QMessageBox, 'warning', return_value=QMessageBox.Ok) as mock_message:
        qtbot.mouseClick(view.print_report_button, Qt.LeftButton)
        
        # Verify that a warning message was shown
        mock_message.assert_called_once()
        
        # Verify PrintManager.print was not called
        mock_print_manager.print.assert_not_called()


@pytest.mark.integration
def test_cash_drawer_print_error_handling(qtbot, mock_cash_drawer_service, mock_print_manager):
    """Test error handling in the cash drawer print functionality."""
    # Set up mock service to return a drawer summary
    mock_cash_drawer_service.get_drawer_summary.return_value = {
        'is_open': True,
        'current_balance': Decimal('300.01'),
        'initial_amount': Decimal('100.00'),
        'total_in': Decimal('300.01'),
        'total_out': Decimal('100.00'),
        'opened_at': datetime.now(),
        'opened_by': 1,
        'entries_today': []
    }
    
    # Create the cash drawer view
    view = CashDrawerView(mock_cash_drawer_service, user_id=1, print_manager=mock_print_manager)
    qtbot.addWidget(view)
    
    # Set up PrintManager to fail
    mock_print_manager.print.return_value = False
    
    # Click the print button - with message box mocked to prevent showing
    with patch.object(QMessageBox, 'warning', return_value=QMessageBox.Ok) as mock_warning:
        qtbot.mouseClick(view.print_report_button, Qt.LeftButton)
        
        # Verify PrintManager.print was called
        mock_print_manager.print.assert_called_once()
        
        # Verify that a warning message was shown
        mock_warning.assert_called_once()
        
    # Set up PrintManager to raise an exception
    mock_print_manager.reset_mock()
    mock_print_manager.print.side_effect = Exception("Test error")
    
    # Click the print button again - with message box mocked to prevent showing
    with patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok) as mock_critical:
        qtbot.mouseClick(view.print_report_button, Qt.LeftButton)
        
        # Verify PrintManager.print was called
        mock_print_manager.print.assert_called_once()
        
        # Verify that an error message was shown
        mock_critical.assert_called_once()


@pytest.fixture
def mock_corte_service():
    """Create a mock CorteService for testing."""
    mock_service = MagicMock()
    
    # Set up some default mock data
    mock_service.calculate_corte_data.return_value = {
        'total_sales': Decimal('1000.00'),
        'num_sales': 10,
        'sales_by_payment_type': {
            'Efectivo': Decimal('500.00'),
            'Tarjeta': Decimal('300.00'),
            'Otro': Decimal('200.00')
        },
        'starting_balance': Decimal('100.00'),
        'cash_in_total': Decimal('50.00'),
        'cash_out_total': Decimal('30.00'),
        'cash_in_entries': [],
        'cash_out_entries': []
    }
    
    return mock_service


@pytest.mark.integration
def test_corte_print_button(qtbot, mock_corte_service, mock_print_manager):
    """Test that the print button in the corte view calls the print manager."""
    # Create the corte view with mock data
    view = CorteView(mock_corte_service, user_id=1, print_manager=mock_print_manager)
    qtbot.addWidget(view)
    
    # Manually set current_data to avoid refresh error
    view.current_data = mock_corte_service.calculate_corte_data()
    
    # Mock the period_filter to return a valid date range
    with patch.object(view.period_filter, 'get_period_range', return_value=(
        datetime.now() - timedelta(days=1), 
        datetime.now()
    )) as mock_period_range, \
         patch.object(QMessageBox, 'warning', return_value=QMessageBox.Ok) as mock_warning, \
         patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok) as mock_error:
        
        qtbot.mouseClick(view.print_report_btn, Qt.LeftButton)
        
        # Verify PrintManager.print was called with the correct arguments
        mock_print_manager.print.assert_called_once()
        args, kwargs = mock_print_manager.print.call_args
        
        # Verify the print type and destination
        assert kwargs['print_type'] == PrintType.REPORT
        assert kwargs['destination'] == PrintDestination.PREVIEW
        
        # Check that the data contains the required fields
        assert 'title' in kwargs['data']
        assert 'report_type' in kwargs['data'] and kwargs['data']['report_type'] == 'corte'
        assert 'timestamp' in kwargs['data']
        assert 'total_sales' in kwargs['data']
        assert 'sales_by_payment_type' in kwargs['data']
        
        # No warning or error messages should have been shown
        mock_warning.assert_not_called()
        mock_error.assert_not_called()


@pytest.mark.integration
def test_corte_print_no_data(qtbot, mock_corte_service, mock_print_manager):
    """Test that a warning is shown when trying to print with no data."""
    # Create the corte view but don't populate current_data
    view = CorteView(mock_corte_service, user_id=1, print_manager=mock_print_manager)
    qtbot.addWidget(view)
    
    # Ensure current_data is None
    view.current_data = None
    
    # Click the print button - with message box mocked to prevent showing
    with patch.object(QMessageBox, 'warning', return_value=QMessageBox.Ok) as mock_warning:
        qtbot.mouseClick(view.print_report_btn, Qt.LeftButton)
        
        # Verify that a warning message was shown
        mock_warning.assert_called_once()
        
        # Verify PrintManager.print was not called
        mock_print_manager.print.assert_not_called()


@pytest.mark.integration
def test_corte_print_error_handling(qtbot, mock_corte_service, mock_print_manager):
    """Test error handling in the corte print functionality."""
    # Create the corte view
    view = CorteView(mock_corte_service, user_id=1, print_manager=mock_print_manager)
    qtbot.addWidget(view)
    
    # Manually set current_data to avoid refresh error
    view.current_data = mock_corte_service.calculate_corte_data()
    
    # Mock the period_filter to return a valid date range
    with patch.object(view.period_filter, 'get_period_range', return_value=(
        datetime.now() - timedelta(days=1), 
        datetime.now()
    )) as mock_period_range:
        
        # Set up PrintManager to fail
        mock_print_manager.print.return_value = False
        
        # Click the print button - with message box mocked to prevent showing
        with patch.object(QMessageBox, 'warning', return_value=QMessageBox.Ok) as mock_warning:
            qtbot.mouseClick(view.print_report_btn, Qt.LeftButton)
            
            # Verify PrintManager.print was called
            mock_print_manager.print.assert_called_once()
            
            # Verify that a warning message was shown
            mock_warning.assert_called_once()
        
        # Set up PrintManager to raise an exception
        mock_print_manager.reset_mock()
        mock_print_manager.print.side_effect = Exception("Test error")
        
        # Click the print button again - with message box mocked to prevent showing
        with patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok) as mock_critical:
            qtbot.mouseClick(view.print_report_btn, Qt.LeftButton)
            
            # Verify PrintManager.print was called
            mock_print_manager.print.assert_called_once()
            
            # Verify that an error message was shown
            mock_critical.assert_called_once()


if __name__ == '__main__':
    pytest.main(['-xvs', __file__]) 