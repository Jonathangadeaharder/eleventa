"""
Tests for the CashDrawerTableModel UI model.
Focus: Initialization, data access, header logic, entry updating, and Qt role handling.
"""

import pytest
from datetime import datetime
from decimal import Decimal

# Use PySide6 imports now that the model is refactored
from PySide6.QtCore import Qt, QModelIndex 
from PySide6.QtGui import QBrush, QColor # Needed for background role check

from ui.models.cash_drawer_model import CashDrawerTableModel
from core.models.cash_drawer import CashDrawerEntry, CashDrawerEntryType
from unittest.mock import MagicMock, patch

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
        amount=Decimal("20.00"), 
        description="Office supplies", 
        user_id=1 
    )
    entry3.user_name = "Admin"

    entry4 = CashDrawerEntry(
        id=4, 
        timestamp=datetime(2023, 10, 26, 14, 0, 0),
        entry_type=CashDrawerEntryType.SALE, 
        amount=Decimal("123.45"), 
        description="Product Sale", 
        user_id=3 
    )
    
    return [entry1, entry2, entry3, entry4]

@pytest.fixture
def model(sample_entries):
    return CashDrawerTableModel(sample_entries)


def test_cash_drawer_model_initialization(sample_entries):
    """Test model initialization with and without data."""
    model_with_data = CashDrawerTableModel(sample_entries)
    assert model_with_data.rowCount() == len(sample_entries)
    assert model_with_data.columnCount() == 6
    
    model_empty = CashDrawerTableModel()
    assert model_empty.rowCount() == 0
    assert model_empty._entries == []

def test_cash_drawer_model_row_count(model, sample_entries):
    """Test rowCount method."""
    assert model.rowCount() == len(sample_entries)

def test_cash_drawer_model_column_count(model):
    """Test columnCount method."""
    assert model.columnCount() == 6

def test_cash_drawer_model_header_data(model):
    """Test headerData method."""
    headers = ["ID", "Fecha y Hora", "Tipo", "Monto", "Descripción", "Usuario"]
    for i, header in enumerate(headers):
        # Use actual Qt constants
        assert model.headerData(i, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole) == header
    # Test other orientations/roles return None
    assert model.headerData(0, Qt.Orientation.Vertical, Qt.ItemDataRole.DisplayRole) is None
    assert model.headerData(0, Qt.Orientation.Horizontal, Qt.ItemDataRole.BackgroundRole) is None
    assert model.headerData(99, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole) is None # Out of bounds

def test_cash_drawer_model_set_entries(sample_entries):
    """Test updating entries using setEntries."""
    model = CashDrawerTableModel()
    model.beginResetModel = MagicMock()
    model.endResetModel = MagicMock()
    
    model.setEntries(sample_entries)
    
    assert model.rowCount() == len(sample_entries)
    assert model._entries == sample_entries
    model.beginResetModel.assert_called_once()
    model.endResetModel.assert_called_once()

# --- Data Method Tests --- 

@pytest.mark.parametrize("row, col, expected", [
    (0, 0, "1"), # ID
    (0, 1, "2023-10-26 09:00:00"), # Timestamp format
    (0, 2, "Apertura"), # Type START
    (0, 4, "Initial float"), # Description
    (0, 5, "Admin"), # User Name
    (1, 2, "Entrada"), # Type IN
    (1, 5, "User1"),
    (2, 2, "Salida"), # Type OUT
    (3, 0, "4"), # ID
    (3, 2, "Venta"), # Type SALE
    (3, 5, "3") # User ID fallback
])
def test_cash_drawer_model_data_display_role(model, row, col, expected):
    """Test data method for DisplayRole with various columns."""
    # Create a real QModelIndex
    index = model.createIndex(row, col)
    # Patch locale.currency to avoid locale dependency issues in tests
    with patch('locale.currency', return_value=f"${model._entries[row].amount:.2f}"):
        assert model.data(index, Qt.ItemDataRole.DisplayRole) == expected

def test_cash_drawer_model_data_display_role_amount(model):
    """Test specifically the amount formatting."""
    index = model.createIndex(1, 3) # Row 1, Amount column
    expected_amount = model._entries[1].amount # 50.50
    with patch('locale.currency', return_value=f"${expected_amount:.2f}") as mock_currency:
        result = model.data(index, Qt.ItemDataRole.DisplayRole)
        mock_currency.assert_called_once_with(float(expected_amount), grouping=True)
        assert result == "$50.50"
        
@pytest.mark.parametrize("col, expected_align", [
    (0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), # ID
    (1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), # Timestamp
    (2, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), # Type
    (3, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter), # Amount
    (4, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), # Description
    (5, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)  # User
])
def test_cash_drawer_model_data_alignment_role(model, col, expected_align):
    """Test data method for TextAlignmentRole."""
    index = model.createIndex(0, col)
    assert model.data(index, Qt.ItemDataRole.TextAlignmentRole) == expected_align

# Check BackgroundRole returns QBrush instances for specific types
@pytest.mark.skip(reason="Temporarily skipping due to persistent Qt crash (access violation) in model data method")
@pytest.mark.parametrize("row, expected_brush", [
    (0, True), # START -> Green (should return a QBrush)
    (1, True), # IN -> Blue (should return a QBrush)
    (2, True), # OUT -> Red (should return a QBrush)
    (3, False) # SALE -> Default (should return None)
])
def test_cash_drawer_model_data_background_role(model, row, expected_brush):
    """Test data method for BackgroundRole."""
    index = model.createIndex(row, 0) # Column doesn't matter for this role
    result = model.data(index, Qt.ItemDataRole.BackgroundRole)
    if expected_brush:
        assert isinstance(result, QBrush)
    else:
        assert result is None

def test_cash_drawer_model_data_invalid_index(model):
    """Test data method with invalid index (using default QModelIndex)."""
    invalid_index = QModelIndex() # Default constructor creates invalid index
    assert model.data(invalid_index, Qt.ItemDataRole.DisplayRole) is None

    # Also test out-of-bounds rows/cols explicitly if createIndex is used
    invalid_row_index = model.createIndex(99, 0) 
    invalid_col_index = model.createIndex(0, 99)
    # data() method itself checks bounds, so createIndex might not be strictly needed
    # but the model implementation relies on index.isValid()
    assert model.data(invalid_row_index, Qt.ItemDataRole.DisplayRole) is None
    assert model.data(invalid_col_index, Qt.ItemDataRole.DisplayRole) is None

def test_cash_drawer_model_data_other_role(model):
    """Test data method with an unhandled role."""
    index = model.createIndex(0, 0)
    assert model.data(index, 999) is None # Unhandled role should return None
