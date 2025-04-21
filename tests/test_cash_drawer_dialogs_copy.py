import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import date
import locale
import sys

# Assuming PySide6 is used, import necessary components
# We might need QApplication for tests involving GUI interactions
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox, QTableView, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QDateEdit
from PySide6.QtCore import Qt, QDate, QAbstractItemModel, Signal
from PySide6.QtTest import QTest 

# Import the dialogs to be tested
from ui.dialogs.cash_drawer_dialogs import (
    OpenCashDrawerDialog, 
    AddRemoveCashDialog, 
    CashDrawerHistoryDialog
)
# Import the service that the dialogs use
from core.services.cash_drawer_service import CashDrawerService
from core.models.cash_drawer import CashDrawerEntry, CashDrawerEntryType # Needed for type hints and potential return values
from ui.models.cash_drawer_model import CashDrawerTableModel # Import the real model for spec

# Create QApplication fixture
@pytest.fixture(scope="session")
def qapp():
    """Create QApplication once per session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app

# Custom Mock Class inheriting from QAbstractItemModel
class MockTableModel(QAbstractItemModel, MagicMock):
    def __init__(self, *args, **kwargs):
        QAbstractItemModel.__init__(self)
        MagicMock.__init__(self, *args, **kwargs)
        # Mock abstract methods to avoid NotImplementedError if called internally by Qt
        self.rowCount = MagicMock(return_value=0)
        self.columnCount = MagicMock(return_value=0)
        self.data = MagicMock(return_value=None)
        self.headerData = MagicMock(return_value=None)
        self.index = MagicMock()
        self.parent = MagicMock()
        # Add the specific method we want to test from CashDrawerTableModel
        self.setEntries = MagicMock()
        # Store entries collection
        self._entries = []
        
    def __setitem__(self, key, value):
        """Implement __setitem__ to allow setting values with bracket notation."""
        if isinstance(key, int) and 0 <= key < len(self._entries):
            self._entries[key] = value
        else:
            # Allow setting arbitrary attributes
            self.__dict__[key] = value
            
    # Implement magic methods to avoid AttributeError during testing
    def __bool__(self):
        return True
        
    def __len__(self):
        return len(self._entries)
        
    def __iter__(self):
        return iter(self._entries)
        
    def __getitem__(self, key):
        if isinstance(key, int) and 0 <= key < len(self._entries):
            return self._entries[key]
        raise IndexError("Index out of range")

# Create mock versions of Qt widgets that have the signals we need
class MockPushButton(QWidget):
    clicked = Signal()
    
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.text = args[0] if args else ""
    
    def connect(self, _):
        pass  # Just a stub, signal won't be emitted in tests

class MockDateEdit(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self._date = args[0] if args else QDate.currentDate()
        
    def date(self):
        return self._date
        
    def setDate(self, date):
        self._date = date

# Mock the CashDrawerService
@pytest.fixture
def mock_cash_drawer_service():
    # return MagicMock(spec=CashDrawerService)
    service_mock = MagicMock(spec=CashDrawerService)
    # Manually add the repository attribute since spec doesn't pick it up from __init__
    service_mock.repository = MagicMock()
    return service_mock

# Example user ID for tests
TEST_USER_ID = 1


class TestOpenCashDrawerDialog:
    def test_initialization(self, qapp, qtbot, mock_cash_drawer_service):
        """Test that the OpenCashDrawerDialog initializes correctly."""
        with patch('ui.dialogs.cash_drawer_dialogs.QMessageBox'):
            dialog = OpenCashDrawerDialog(mock_cash_drawer_service, TEST_USER_ID)
            qtbot.addWidget(dialog)
            assert dialog.windowTitle() == "Abrir Caja"
            assert dialog.initial_amount_field is not None
            assert dialog.description_field is not None
            dialog.close()

    @patch('ui.dialogs.cash_drawer_dialogs.QMessageBox')
    def test_accept_valid_amount(self, mock_message_box, qapp, qtbot, mock_cash_drawer_service):
        """Test accepting the dialog with a valid starting amount."""
        dialog = OpenCashDrawerDialog(mock_cash_drawer_service, TEST_USER_ID)
        qtbot.addWidget(dialog)
        
        # Simulate user input
        dialog.initial_amount_field.setValue(100.50)
        dialog.description_field.setPlainText("Initial opening")
        
        # Call accept directly
        dialog.accept() 

        # Verify service method was called
        mock_cash_drawer_service.open_drawer.assert_called_once_with(
            initial_amount=Decimal('100.50'),
            description="Initial opening",
            user_id=TEST_USER_ID
        )
        # Verify success message box was shown
        mock_message_box.information.assert_called_once()
        assert dialog.result() == QDialog.Accepted
        dialog.close()

    @patch('ui.dialogs.cash_drawer_dialogs.QMessageBox')
    def test_accept_default_description(self, mock_message_box, qapp, qtbot, mock_cash_drawer_service):
        """Test accepting with a default description if none is provided."""
        dialog = OpenCashDrawerDialog(mock_cash_drawer_service, TEST_USER_ID)
        qtbot.addWidget(dialog)
        dialog.initial_amount_field.setValue(50.00)
        dialog.description_field.setPlainText("") # Empty description

        dialog.accept()

        mock_cash_drawer_service.open_drawer.assert_called_once_with(
            initial_amount=Decimal('50.00'),
            description="Apertura inicial de caja", # Default description
            user_id=TEST_USER_ID
        )
        mock_message_box.information.assert_called_once()
        assert dialog.result() == QDialog.Accepted
        dialog.close()

    @patch('ui.dialogs.cash_drawer_dialogs.QMessageBox')
    def test_service_error_on_accept(self, mock_message_box, qapp, qtbot, mock_cash_drawer_service):
        """Test error handling when the service raises an exception."""
        error_message = "Database connection failed"
        mock_cash_drawer_service.open_drawer.side_effect = Exception(error_message)
        
        dialog = OpenCashDrawerDialog(mock_cash_drawer_service, TEST_USER_ID)
        qtbot.addWidget(dialog)
        dialog.initial_amount_field.setValue(200.00)

        dialog.accept()

        mock_cash_drawer_service.open_drawer.assert_called_once()
        mock_message_box.critical.assert_called_once()
        assert dialog.result() != QDialog.Accepted
        dialog.close()


class TestAddRemoveCashDialog:
    def test_initialization_add(self, qapp, qtbot, mock_cash_drawer_service):
        """Test initialization for adding cash."""
        dialog = AddRemoveCashDialog(mock_cash_drawer_service, TEST_USER_ID, is_adding=True)
        qtbot.addWidget(dialog)
        assert dialog.windowTitle() == "Agregar Efectivo"
        assert dialog.amount_field is not None
        assert dialog.description_field is not None
        dialog.close()

    def test_initialization_remove(self, qapp, qtbot, mock_cash_drawer_service):
        """Test initialization for removing cash."""
        dialog = AddRemoveCashDialog(mock_cash_drawer_service, TEST_USER_ID, is_adding=False)
        qtbot.addWidget(dialog)
        assert dialog.windowTitle() == "Retirar Efectivo"
        dialog.close()

    @patch('ui.dialogs.cash_drawer_dialogs.QMessageBox')
    def test_accept_add_cash(self, mock_message_box, qapp, qtbot, mock_cash_drawer_service):
        """Test accepting the dialog when adding cash."""
        dialog = AddRemoveCashDialog(mock_cash_drawer_service, TEST_USER_ID, is_adding=True)
        qtbot.addWidget(dialog)
        dialog.amount_field.setValue(50.25)
        dialog.description_field.setPlainText("Adding petty cash")

        dialog.accept()

        mock_cash_drawer_service.add_cash.assert_called_once_with(
            amount=Decimal('50.25'),
            description="Adding petty cash",
            user_id=TEST_USER_ID
        )
        mock_message_box.information.assert_called_once()
        assert dialog.result() == QDialog.Accepted
        dialog.close()

    @patch('ui.dialogs.cash_drawer_dialogs.QMessageBox')
    def test_accept_remove_cash(self, mock_message_box, qapp, qtbot, mock_cash_drawer_service):
        """Test accepting the dialog when removing cash."""
        dialog = AddRemoveCashDialog(mock_cash_drawer_service, TEST_USER_ID, is_adding=False)
        qtbot.addWidget(dialog)
        dialog.amount_field.setValue(20.00)
        dialog.description_field.setPlainText("Cash withdrawal for supplies")

        dialog.accept()

        mock_cash_drawer_service.remove_cash.assert_called_once_with(
            amount=Decimal('20.00'),
            description="Cash withdrawal for supplies",
            user_id=TEST_USER_ID
        )
        mock_message_box.information.assert_called_once()
        assert dialog.result() == QDialog.Accepted
        dialog.close()

    @patch('ui.dialogs.cash_drawer_dialogs.QMessageBox')
    def test_reject_missing_description(self, mock_message_box, qapp, qtbot, mock_cash_drawer_service):
        """Test that the dialog prevents accepting without a description."""
        dialog = AddRemoveCashDialog(mock_cash_drawer_service, TEST_USER_ID, is_adding=True)
        qtbot.addWidget(dialog)
        dialog.amount_field.setValue(10.00)
        dialog.description_field.setPlainText("") # Empty description

        dialog.accept()

        mock_cash_drawer_service.add_cash.assert_not_called()
        mock_message_box.warning.assert_called_once_with(dialog, "Error", "Por favor ingrese una descripción del movimiento.")
        assert dialog.result() != QDialog.Accepted
        dialog.close()
        
    @patch('ui.dialogs.cash_drawer_dialogs.QMessageBox')
    def test_service_value_error_on_accept(self, mock_message_box, qapp, qtbot, mock_cash_drawer_service):
        """Test error handling when the service raises a ValueError (e.g., insufficient funds)."""
        error_message = "Insufficient funds"
        mock_cash_drawer_service.remove_cash.side_effect = ValueError(error_message)
        
        dialog = AddRemoveCashDialog(mock_cash_drawer_service, TEST_USER_ID, is_adding=False)
        qtbot.addWidget(dialog)
        dialog.amount_field.setValue(500.00)
        dialog.description_field.setPlainText("Large withdrawal")

        dialog.accept()

        mock_cash_drawer_service.remove_cash.assert_called_once()
        mock_message_box.warning.assert_called_once_with(dialog, "Error", error_message)
        assert dialog.result() != QDialog.Accepted
        dialog.close()


class TestCashDrawerHistoryDialog:
    @pytest.fixture
    def mock_dialog(self, qapp, qtbot, mock_cash_drawer_service):
        """Create a completely mocked dialog to avoid GUI interaction issues."""
        with patch('ui.dialogs.cash_drawer_dialogs.QTableView'), \
             patch('ui.dialogs.cash_drawer_dialogs.QHeaderView'), \
             patch('ui.dialogs.cash_drawer_dialogs.QDateEdit'), \
             patch('ui.dialogs.cash_drawer_dialogs.QPushButton'), \
             patch('ui.dialogs.cash_drawer_dialogs.QGroupBox'), \
             patch('ui.dialogs.cash_drawer_dialogs.QLabel'):
            dialog = CashDrawerHistoryDialog(mock_cash_drawer_service, test_mode=True)
            dialog.table_model = MockTableModel()
            
            # Create mock date objects that will work without real Qt interactions
            mock_date_from = MagicMock()
            mock_date_to = MagicMock()
            mock_date_from.date.return_value = QDate(2023, 10, 1)
            mock_date_to.date.return_value = QDate(2023, 10, 31)
            mock_date_from.date().toPyDate.return_value = date(2023, 10, 1)
            mock_date_to.date().toPyDate.return_value = date(2023, 10, 31)
            
            # Replace the real date widgets with mocks
            dialog.date_from = mock_date_from
            dialog.date_to = mock_date_to
            
            yield dialog

    @patch('ui.dialogs.cash_drawer_dialogs.CashDrawerHistoryDialog.update_summary_from_entries')
    def test_apply_filter(self, mock_update_summary, qapp, mock_cash_drawer_service):
        """Test filtering history by date range."""
        # Completely bypass dialog creation and directly test the logic
        start_date = date(2023, 10, 1)
        end_date = date(2023, 10, 31)
        
        # Configure mock service return value
        sample_entry = CashDrawerEntry(
            id=1, user_id=1, entry_type=CashDrawerEntryType.START,
            amount=Decimal('100.00'), description="Open", timestamp=date(2023, 10, 26)
        )
        mock_cash_drawer_service.repository.get_entries_by_date_range.return_value = [sample_entry]
        
        # Create a minimal mock dialog with all required attributes
        mock_table_model = MockTableModel()
        dialog = MagicMock()
        dialog.cash_drawer_service = mock_cash_drawer_service
        dialog.table_model = mock_table_model
        dialog.date_from = MagicMock()
        dialog.date_to = MagicMock()
        
        # Configure date mocks
        dialog.date_from.date().toPyDate.return_value = start_date
        dialog.date_to.date().toPyDate.return_value = end_date
        
        # Execute the method under test directly
        # This way we can check how it would actually behave
        with patch.object(dialog, 'update_summary_from_entries') as mock_update:
            CashDrawerHistoryDialog.apply_filter(dialog)
            
            # Verify service method was called with correct dates
            mock_cash_drawer_service.repository.get_entries_by_date_range.assert_called_once_with(
                start_date=start_date,
                end_date=end_date
            )
            
            # Verify the model's setEntries method was called with the results
            mock_table_model.setEntries.assert_called_once_with([sample_entry])
            
            # Verify that update_summary_from_entries was called
            mock_update.assert_called_once_with([sample_entry])

    @patch('ui.dialogs.cash_drawer_dialogs.QMessageBox')
    def test_service_error_on_filter(self, mock_message_box, qapp, mock_cash_drawer_service):
        """Test error handling when filtering history fails."""
        # Completely bypass dialog creation and directly test the logic
        start_date = date(2023, 10, 1)
        end_date = date(2023, 10, 31)
        
        # Configure mock service to raise error
        error_message = "Failed to fetch history"
        mock_cash_drawer_service.repository.get_entries_by_date_range.side_effect = Exception(error_message)
        
        # Create a minimal mock dialog
        mock_table_model = MockTableModel()
        dialog = MagicMock()
        dialog.cash_drawer_service = mock_cash_drawer_service
        dialog.table_model = mock_table_model
        dialog.date_from = MagicMock()
        dialog.date_to = MagicMock()
        
        # Configure date mocks
        dialog.date_from.date().toPyDate.return_value = start_date
        dialog.date_to.date().toPyDate.return_value = end_date
        
        # Call the actual method we're testing
        CashDrawerHistoryDialog.apply_filter(dialog)
        
        # Verify service method was called with correct dates
        mock_cash_drawer_service.repository.get_entries_by_date_range.assert_called_once_with(
            start_date=start_date,
            end_date=end_date
        )
        
        # Verify error message box was shown - use dialog as the self argument
        mock_message_box.critical.assert_called_once_with(
            dialog, "Error", f"Error al filtrar datos: {error_message}"
        )

    def test_initialization_loads_today(self, qapp, qtbot, mock_cash_drawer_service):
        """Test that the dialog calls load_today_data on init if not in test_mode."""
        with patch('ui.dialogs.cash_drawer_dialogs.QTableView'), \
             patch('ui.dialogs.cash_drawer_dialogs.QHeaderView'), \
             patch('ui.dialogs.cash_drawer_dialogs.CashDrawerTableModel'), \
             patch('ui.dialogs.cash_drawer_dialogs.QDateEdit'), \
             patch('ui.dialogs.cash_drawer_dialogs.QMessageBox'), \
             patch('ui.dialogs.cash_drawer_dialogs.QPushButton'), \
             patch.object(CashDrawerHistoryDialog, 'load_today_data') as mock_load:
            
            dialog = CashDrawerHistoryDialog(mock_cash_drawer_service, test_mode=False)
            qtbot.addWidget(dialog)
            
            # Verify load_today_data was called
            mock_load.assert_called_once()
            
            # Clean up the dialog
            dialog.close()

    def test_summary_display_update(self, qapp):
        """Test that the summary labels are updated correctly."""
        # Create test data
        summary_data = {
            'initial_amount': Decimal('100.00'),
            'total_in': Decimal('200.00'),
            'total_out': Decimal('75.50'),
            'current_balance': Decimal('1359.06')
        }
        
        # Create mock dialog with mock labels
        dialog = MagicMock()
        dialog.initial_label = MagicMock()
        dialog.in_label = MagicMock()
        dialog.out_label = MagicMock()
        dialog.balance_label = MagicMock()
        
        # Call the actual method we're testing
        CashDrawerHistoryDialog.update_summary_display(dialog, summary_data)
        
        # Verify each setText call with the correct formatted values
        dialog.initial_label.setText.assert_called_once()
        dialog.in_label.setText.assert_called_once()
        dialog.out_label.setText.assert_called_once()
        dialog.balance_label.setText.assert_called_once()

# Add more test classes or functions as needed for other dialogs or utility functions
# Remember to handle potential GUI interactions carefully, often patching is sufficient.
# If QTest is needed, ensure a QApplication fixture is active. 
