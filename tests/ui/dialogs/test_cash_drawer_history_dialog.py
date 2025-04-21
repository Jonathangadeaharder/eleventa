"""
Tests for the CashDrawerHistoryDialog UI component.
Focus: Initialization, filtering, summary calculation, and correct interaction with service and model mocks.
"""

import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import datetime

from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtWidgets import QApplication, QDialog, QTableView, QHeaderView, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QDateEdit, QLabel, QGroupBox, QFormLayout

from core.models.cash_drawer import CashDrawerEntry, CashDrawerEntryType
from ui.dialogs.cash_drawer_dialogs import CashDrawerHistoryDialog
from tests.ui.models.mock_cash_drawer_model import MockCashDrawerTableModel

# Create mock versions of Qt widgets that have the signals we need
class MockPushButton(QWidget):
    clicked = Signal()
    
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.text = args[0] if args else ""
    
    def get_clicked(self):
        """Return a mock signal that can be connected to."""
        class MockSignal:
            def connect(self, handler):
                pass  # Just a stub, signal won't be emitted in tests
        return MockSignal()
        
    clicked = property(get_clicked)

class MockDateEdit(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self._date = args[0] if args else QDate.currentDate()
        
    def date(self):
        return self._date
        
    def setDate(self, date):
        self._date = date

# Add a QApplication fixture that all tests will use
@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


# Sample data for testing
@pytest.fixture
def sample_entries():
    entry1 = CashDrawerEntry(
        id=1, 
        timestamp=datetime(2023, 10, 26, 9, 0, 0),
        entry_type=CashDrawerEntryType.START, 
        amount=Decimal("100.00"), 
        description="Initial float", 
        user_id=1 
    )
    entry1.user_name = "Admin"

    entry2 = CashDrawerEntry(
        id=2, 
        timestamp=datetime(2023, 10, 26, 10, 30, 15),
        entry_type=CashDrawerEntryType.IN, 
        amount=Decimal("50.50"), 
        description="Cash payment", 
        user_id=2 
    )
    entry2.user_name = "User1"

    entry3 = CashDrawerEntry(
        id=3, 
        timestamp=datetime(2023, 10, 26, 11, 15, 0),
        entry_type=CashDrawerEntryType.OUT, 
        amount=Decimal("-20.00"), 
        description="Office supplies", 
        user_id=1 
    )
    entry3.user_name = "Admin"

    return [entry1, entry2, entry3]


# Mock Qt dependencies
@pytest.fixture
def mock_all_qt_dependencies():
    """Mock all Qt dependencies for isolated testing."""
    with patch('ui.dialogs.cash_drawer_dialogs.QDialog'), \
         patch('ui.dialogs.cash_drawer_dialogs.QTableView'), \
         patch('ui.dialogs.cash_drawer_dialogs.QHeaderView'), \
         patch('ui.dialogs.cash_drawer_dialogs.QLabel'), \
         patch('ui.dialogs.cash_drawer_dialogs.QDateEdit'), \
         patch('ui.dialogs.cash_drawer_dialogs.QGroupBox'), \
         patch('ui.dialogs.cash_drawer_dialogs.QFormLayout'), \
         patch('ui.dialogs.cash_drawer_dialogs.QHBoxLayout'), \
         patch('ui.dialogs.cash_drawer_dialogs.QVBoxLayout'), \
         patch('ui.dialogs.cash_drawer_dialogs.QPushButton'):
        yield


# Patch the table model with our custom mock
@pytest.fixture
def mock_table_model():
    mock_model = MockCashDrawerTableModel(spec=MockCashDrawerTableModel)
    return mock_model


@pytest.fixture
def mock_cash_drawer_service(sample_entries):
    """Create a mock for the CashDrawerService."""
    mock_service = MagicMock()
    
    # Configure the service to return summary data
    mock_summary = {
        'entries_today': sample_entries,
        'initial_amount': Decimal('100.00'),
        'total_in': Decimal('50.50'),
        'total_out': Decimal('20.00'),
        'current_balance': Decimal('130.50')
    }
    mock_service.get_drawer_summary.return_value = mock_summary
    
    # Mock the repository
    mock_repository = MagicMock()
    mock_repository.get_entries_by_date_range.return_value = sample_entries
    mock_service.repository = mock_repository
    
    return mock_service


class TestCashDrawerHistoryDialog:
    """Test cases for the CashDrawerHistoryDialog."""
    
    def test_initialization_loads_today(self, mock_cash_drawer_service, qapp, sample_entries):
        """Test that the dialog initializes and loads today's data."""
        with patch('ui.dialogs.cash_drawer_dialogs.CashDrawerTableModel') as mock_table_model_cls, \
             patch('ui.dialogs.cash_drawer_dialogs.QVBoxLayout') as mock_vbox, \
             patch('ui.dialogs.cash_drawer_dialogs.QHBoxLayout') as mock_hbox, \
             patch('ui.dialogs.cash_drawer_dialogs.QTableView') as mock_table_view, \
             patch('ui.dialogs.cash_drawer_dialogs.QHeaderView') as mock_header_view, \
             patch('ui.dialogs.cash_drawer_dialogs.QLabel', return_value=QWidget()) as mock_label, \
             patch('ui.dialogs.cash_drawer_dialogs.QDateEdit', side_effect=lambda *args: MockDateEdit(*args)) as mock_date_edit, \
             patch('ui.dialogs.cash_drawer_dialogs.QPushButton', side_effect=lambda *args: MockPushButton(*args)) as mock_button, \
             patch('ui.dialogs.cash_drawer_dialogs.QGroupBox', return_value=QWidget()) as mock_group, \
             patch('ui.dialogs.cash_drawer_dialogs.QFormLayout') as mock_form, \
             patch('ui.dialogs.cash_drawer_dialogs.QFont') as mock_font, \
             patch('ui.dialogs.cash_drawer_dialogs.locale') as mock_locale:
            
            # Configure mock QTableView
            mock_table_view_instance = MagicMock()
            mock_header = MagicMock()
            mock_table_view_instance.horizontalHeader.return_value = mock_header
            mock_table_view.return_value = mock_table_view_instance
            
            # Set up the mock model class to return our mock instance
            mock_model_instance = MockCashDrawerTableModel()
            mock_table_model_cls.return_value = mock_model_instance
            
            # Mock locale.currency to return predictable strings
            mock_locale.currency.side_effect = lambda val, grouping: f'${val:.2f}'
            
            # Create mock for update_summary_display method to avoid UI operations
            with patch.object(CashDrawerHistoryDialog, 'update_summary_display'):
                # Initialize dialog without test_mode to ensure load_today_data gets called
                dialog = CashDrawerHistoryDialog(mock_cash_drawer_service, test_mode=False)
                
                # Verify service was called to get summary for today
                mock_cash_drawer_service.get_drawer_summary.assert_called_once()
                
                # Verify model's setEntries was called with the entries from the summary
                mock_model_instance.setEntries.assert_called_once()
                entries_arg = mock_model_instance.setEntries.call_args[0][0]
                assert entries_arg == mock_cash_drawer_service.get_drawer_summary.return_value['entries_today']
    
    def test_apply_filter(self, mock_cash_drawer_service, qapp, sample_entries):
        """Test that the apply_filter method fetches and displays filtered data."""
        with patch('ui.dialogs.cash_drawer_dialogs.CashDrawerTableModel') as mock_table_model_cls, \
             patch('ui.dialogs.cash_drawer_dialogs.QVBoxLayout') as mock_vbox, \
             patch('ui.dialogs.cash_drawer_dialogs.QHBoxLayout') as mock_hbox, \
             patch('ui.dialogs.cash_drawer_dialogs.QTableView') as mock_table_view, \
             patch('ui.dialogs.cash_drawer_dialogs.QHeaderView') as mock_header_view, \
             patch('ui.dialogs.cash_drawer_dialogs.QLabel', return_value=QWidget()) as mock_label, \
             patch('ui.dialogs.cash_drawer_dialogs.QDateEdit', side_effect=lambda *args: MockDateEdit(*args)) as mock_date_edit, \
             patch('ui.dialogs.cash_drawer_dialogs.QPushButton', side_effect=lambda *args: MockPushButton(*args)) as mock_button, \
             patch('ui.dialogs.cash_drawer_dialogs.QGroupBox', return_value=QWidget()) as mock_group, \
             patch('ui.dialogs.cash_drawer_dialogs.QFormLayout') as mock_form, \
             patch('ui.dialogs.cash_drawer_dialogs.QFont') as mock_font, \
             patch('ui.dialogs.cash_drawer_dialogs.locale') as mock_locale, \
             patch('ui.dialogs.cash_drawer_dialogs.QDate') as mock_qdate:
            
            # Configure mock QTableView
            mock_table_view_instance = MagicMock()
            mock_header = MagicMock()
            mock_table_view_instance.horizontalHeader.return_value = mock_header
            mock_table_view.return_value = mock_table_view_instance
            
            # Set up the mock model
            mock_model_instance = MockCashDrawerTableModel()
            mock_table_model_cls.return_value = mock_model_instance
            
            # Mock QDate to return controlled values
            mock_qdate.currentDate.return_value = QDate(2023, 10, 27)
            mock_from_date = MagicMock()
            mock_from_date.toPyDate.return_value = datetime(2023, 10, 25).date()
            mock_to_date = MagicMock()
            mock_to_date.toPyDate.return_value = datetime(2023, 10, 27).date()
            
            # Mock locale for currency formatting
            mock_locale.currency.side_effect = lambda val, grouping: f'${val:.2f}'
            
            # Create the dialog with patched methods to avoid UI operations and use test_mode
            with patch.object(CashDrawerHistoryDialog, 'update_summary_display'), \
                 patch.object(CashDrawerHistoryDialog, 'update_summary_from_entries'):
                
                dialog = CashDrawerHistoryDialog(mock_cash_drawer_service, test_mode=True)
                
                # Set the model explicitly since we're in test mode
                dialog.table_model = mock_model_instance
                
                # Mock the date fields in the dialog
                dialog.date_from = MagicMock()
                dialog.date_from.date.return_value = mock_from_date
                dialog.date_to = MagicMock()
                dialog.date_to.date.return_value = mock_to_date
                
                # Call the method we're testing
                dialog.apply_filter()
                
                # Verify repository was called with the correct date range
                mock_cash_drawer_service.repository.get_entries_by_date_range.assert_called_with(
                    start_date=mock_from_date.toPyDate.return_value,
                    end_date=mock_to_date.toPyDate.return_value
                )
                
                # Verify model was updated with new entries
                mock_model_instance.setEntries.assert_called_once_with(sample_entries)
        
    def test_update_summary_from_entries(self, qapp, sample_entries):
        """Test that the summary is correctly calculated from entries."""
        with patch('ui.dialogs.cash_drawer_dialogs.CashDrawerTableModel') as mock_table_model_cls, \
             patch('ui.dialogs.cash_drawer_dialogs.QVBoxLayout') as mock_vbox, \
             patch('ui.dialogs.cash_drawer_dialogs.QHBoxLayout') as mock_hbox, \
             patch('ui.dialogs.cash_drawer_dialogs.QTableView') as mock_table_view, \
             patch('ui.dialogs.cash_drawer_dialogs.QHeaderView') as mock_header_view, \
             patch('ui.dialogs.cash_drawer_dialogs.QLabel', return_value=QWidget()) as mock_label, \
             patch('ui.dialogs.cash_drawer_dialogs.QDateEdit', side_effect=lambda *args: MockDateEdit(*args)) as mock_date_edit, \
             patch('ui.dialogs.cash_drawer_dialogs.QPushButton', side_effect=lambda *args: MockPushButton(*args)) as mock_button, \
             patch('ui.dialogs.cash_drawer_dialogs.QGroupBox', return_value=QWidget()) as mock_group, \
             patch('ui.dialogs.cash_drawer_dialogs.QFormLayout') as mock_form, \
             patch('ui.dialogs.cash_drawer_dialogs.QFont') as mock_font, \
             patch('ui.dialogs.cash_drawer_dialogs.locale') as mock_locale, \
             patch('ui.dialogs.cash_drawer_dialogs.QDate') as mock_qdate, \
             patch('ui.dialogs.cash_drawer_dialogs.CashDrawerHistoryDialog.load_today_data'):
            
            # Mock locale for currency formatting
            mock_locale.currency.side_effect = lambda val, grouping: f'${val:.2f}'
            
            # Setup dialog with test_mode to avoid UI operations
            mock_service = MagicMock()
            dialog = CashDrawerHistoryDialog(mock_service, test_mode=True)
            
            # Setup mock labels
            dialog.initial_label = MagicMock()
            dialog.in_label = MagicMock()
            dialog.out_label = MagicMock()
            dialog.balance_label = MagicMock()
            
            # Test the method
            dialog.update_summary_from_entries(sample_entries)
            
            # Verify the labels are set correctly
            dialog.initial_label.setText.assert_called_with('$100.00')
            dialog.in_label.setText.assert_called_with('$50.50')
            dialog.out_label.setText.assert_called_with('$20.00')
            dialog.balance_label.setText.assert_called_with('$130.50') 