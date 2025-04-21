import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import Qt, QModelIndex
from datetime import datetime
from decimal import Decimal
import locale

from ui.models.cash_drawer_model import CashDrawerTableModel
from core.models.cash_drawer import CashDrawerEntry, CashDrawerEntryType


@pytest.fixture
def sample_entries():
    """Fixture providing sample cash drawer entries for testing."""
    return [
        CashDrawerEntry(
            id=1,
            timestamp=datetime(2023, 1, 1, 8, 0, 0),
            entry_type=CashDrawerEntryType.START,
            amount=Decimal('1000.00'),
            description="Opening",
            user_id=1,
            drawer_id=None
        ),
        CashDrawerEntry(
            id=2,
            timestamp=datetime(2023, 1, 1, 10, 30, 0),
            entry_type=CashDrawerEntryType.IN,
            amount=Decimal('500.00'),
            description="Cash deposit",
            user_id=1,
            drawer_id=None
        ),
        CashDrawerEntry(
            id=3,
            timestamp=datetime(2023, 1, 1, 14, 45, 0),
            entry_type=CashDrawerEntryType.OUT,
            amount=Decimal('-200.00'),
            description="Withdrawal",
            user_id=2,
            drawer_id=None
        )
    ]


@pytest.fixture
def model(sample_entries):
    """Fixture providing a CashDrawerTableModel with sample entries."""
    return CashDrawerTableModel(sample_entries)


class TestCashDrawerTableModel:
    
    def test_initialization_without_entries(self):
        """Test model initialization without entries."""
        model = CashDrawerTableModel()
        assert model.rowCount() == 0
        assert model.columnCount() == 6  # 6 columns in the model
        
    def test_initialization_with_entries(self, sample_entries):
        """Test model initialization with entries."""
        model = CashDrawerTableModel(sample_entries)
        assert model.rowCount() == 3
        assert model.columnCount() == 6
        
    def test_row_count(self, model):
        """Test rowCount method."""
        assert model.rowCount() == 3
        
        # Test with parent
        parent = QModelIndex()
        assert model.rowCount(parent) == 3
        
    def test_column_count(self, model):
        """Test columnCount method."""
        assert model.columnCount() == 6
        
        # Test with parent
        parent = QModelIndex()
        assert model.columnCount(parent) == 6
        
    def test_header_data(self, model):
        """Test headerData method."""
        expected_headers = ["ID", "Fecha y Hora", "Tipo", "Monto", "Descripción", "Usuario"]
        
        # Test horizontal headers
        for i, header in enumerate(expected_headers):
            result = model.headerData(i, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
            assert result == header
            
        # Test invalid section
        result = model.headerData(len(expected_headers), Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        assert result is None
        
        # Test non-display role
        result = model.headerData(0, Qt.Orientation.Horizontal, Qt.ItemDataRole.EditRole)
        assert result is None
        
        # Test vertical orientation
        result = model.headerData(0, Qt.Orientation.Vertical, Qt.ItemDataRole.DisplayRole)
        assert result is None
        
    def test_data_display_role(self, model, sample_entries):
        """Test data method with DisplayRole."""
        # Test ID column
        index = model.index(0, 0)
        result = model.data(index, Qt.ItemDataRole.DisplayRole)
        assert result == "1"
        
        # Test Timestamp column
        index = model.index(0, 1)
        result = model.data(index, Qt.ItemDataRole.DisplayRole)
        assert result == "2023-01-01 08:00:00"
        
        # Test Type column
        index = model.index(0, 2)
        result = model.data(index, Qt.ItemDataRole.DisplayRole)
        assert result == "Apertura"
        
        index = model.index(1, 2)
        result = model.data(index, Qt.ItemDataRole.DisplayRole)
        assert result == "Entrada"
        
        index = model.index(2, 2)
        result = model.data(index, Qt.ItemDataRole.DisplayRole)
        assert result == "Salida"
        
        # Test Amount column with locale formatting
        index = model.index(0, 3)
        result = model.data(index, Qt.ItemDataRole.DisplayRole)
        # Check the amount is formatted as currency, with some part of the number included
        assert "1000" in result.replace(",", "").replace(".", "")
        
        # Test Description column
        index = model.index(0, 4)
        result = model.data(index, Qt.ItemDataRole.DisplayRole)
        assert result == "Opening"
        
        # Test User column
        index = model.index(0, 5)
        result = model.data(index, Qt.ItemDataRole.DisplayRole)
        assert result == "1"  # Raw user_id since we're not mocking user_name
        
    def test_data_text_alignment_role(self, model):
        """Test data method with TextAlignmentRole."""
        # ID column
        index = model.index(0, 0)
        result = model.data(index, Qt.ItemDataRole.TextAlignmentRole)
        assert result == (Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        # Amount column
        index = model.index(0, 3)
        result = model.data(index, Qt.ItemDataRole.TextAlignmentRole)
        assert result == (Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
    def test_data_background_role(self, model):
        """Test data method with BackgroundRole."""
        # START entry
        index = model.index(0, 0)
        brush = model.data(index, Qt.ItemDataRole.BackgroundRole)
        assert brush is not None
        color = brush.color()
        assert color.red() == 230 and color.green() == 255 and color.blue() == 230
        
        # IN entry
        index = model.index(1, 0)
        brush = model.data(index, Qt.ItemDataRole.BackgroundRole)
        assert brush is not None
        color = brush.color()
        assert color.red() == 230 and color.green() == 230 and color.blue() == 255
        
        # OUT entry
        index = model.index(2, 0)
        brush = model.data(index, Qt.ItemDataRole.BackgroundRole)
        assert brush is not None
        color = brush.color()
        assert color.red() == 255 and color.green() == 230 and color.blue() == 230
        
    def test_invalid_index(self, model):
        """Test data method with invalid index."""
        invalid_index = QModelIndex()
        result = model.data(invalid_index, Qt.ItemDataRole.DisplayRole)
        assert result is None
        
        # Invalid row index
        out_of_bounds_index = model.index(100, 0)
        result = model.data(out_of_bounds_index, Qt.ItemDataRole.DisplayRole)
        assert result is None
        
    def test_set_entries(self, model):
        """Test setEntries method."""
        new_entries = [
            CashDrawerEntry(
                id=10,
                timestamp=datetime(2023, 1, 2, 9, 0, 0),
                entry_type=CashDrawerEntryType.START,
                amount=Decimal('2000.00'),
                description="New day",
                user_id=3,
                drawer_id=None
            )
        ]
        
        # Update model
        model.setEntries(new_entries)
        
        # Check row count changed
        assert model.rowCount() == 1
        
        # Check data was updated
        index = model.index(0, 0)
        result = model.data(index, Qt.ItemDataRole.DisplayRole)
        assert result == "10" 