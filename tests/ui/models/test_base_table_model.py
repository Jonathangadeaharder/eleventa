"""
Tests for the BaseTableModel and its concrete subclass.
Focus: Initialization, data access, header logic, updating, and row retrieval.
"""

import pytest
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from ui.models.base_table_model import BaseTableModel
from unittest.mock import MagicMock

# Concrete subclass for testing
class ConcreteTableModel(BaseTableModel):
    HEADERS = ["ID", "Name", "Value"]

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> object:
        # Basic implementation for testing purposes
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        
        row_data = self._data[index.row()]
        col = index.column()

        if col == 0:
            return row_data.get("id")
        elif col == 1:
            return row_data.get("name")
        elif col == 2:
            return row_data.get("value")
        return None

@pytest.fixture
def test_data():
    return [
        {"id": 1, "name": "Item 1", "value": 100},
        {"id": 2, "name": "Item 2", "value": 200},
        {"id": 3, "name": "Item 3", "value": 300},
    ]

@pytest.fixture
def model(test_data):
    m = ConcreteTableModel()
    m.update_data(test_data)
    return m

def test_base_table_model_initialization():
    """Test that the model initializes correctly."""
    model = ConcreteTableModel()
    assert model.rowCount() == 0
    assert model.columnCount() == 3 # Based on ConcreteTableModel.HEADERS
    assert model._data == []

def test_base_table_model_row_count(model, test_data):
    """Test the rowCount method."""
    assert model.rowCount() == len(test_data)

def test_base_table_model_column_count(model):
    """Test the columnCount method."""
    assert model.columnCount() == len(ConcreteTableModel.HEADERS)

def test_base_table_model_header_data_horizontal(model):
    """Test headerData for horizontal orientation."""
    assert model.headerData(0, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole) == "ID"
    assert model.headerData(1, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole) == "Name"
    assert model.headerData(2, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole) == "Value"

def test_base_table_model_header_data_out_of_bounds(model):
    """Test headerData with an out-of-bounds section index."""
    assert model.headerData(99, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole) is None

def test_base_table_model_header_data_vertical(model):
    """Test headerData for vertical orientation (should return None)."""
    assert model.headerData(0, Qt.Orientation.Vertical, Qt.ItemDataRole.DisplayRole) is None

def test_base_table_model_header_data_other_role(model):
    """Test headerData with a role other than DisplayRole."""
    assert model.headerData(0, Qt.Orientation.Horizontal, Qt.ItemDataRole.EditRole) is None

def test_base_table_model_update_data(test_data):
    """Test the update_data method and signal emission."""
    model = ConcreteTableModel()
    # Mock the signals to ensure they are emitted
    model.beginResetModel = MagicMock()
    model.endResetModel = MagicMock()
    
    model.update_data(test_data)
    
    assert model._data == test_data
    assert model.rowCount() == len(test_data)
    model.beginResetModel.assert_called_once()
    model.endResetModel.assert_called_once()

def test_base_table_model_get_item_at_row(model, test_data):
    """Test getting the underlying data item for a specific row."""
    assert model.get_item_at_row(0) == test_data[0]
    assert model.get_item_at_row(1) == test_data[1]
    assert model.get_item_at_row(2) == test_data[2]

def test_base_table_model_get_item_at_row_out_of_bounds(model):
    """Test get_item_at_row with invalid row indices."""
    assert model.get_item_at_row(-1) is None
    assert model.get_item_at_row(99) is None
    
# Minimal test for the dummy 'data' method in ConcreteTableModel
def test_concrete_table_model_data_method(model, test_data):
    """Test the basic data retrieval in the concrete implementation."""
    # Test getting data for row 1, column 1 (Name)
    index = model.index(1, 1) 
    assert model.data(index, Qt.ItemDataRole.DisplayRole) == test_data[1]["name"]

    # Test invalid index
    invalid_index = QModelIndex()
    assert model.data(invalid_index, Qt.ItemDataRole.DisplayRole) is None

    # Test incorrect role
    index = model.index(0, 0)
    assert model.data(index, Qt.ItemDataRole.EditRole) is None

    # Test out-of-bounds column in concrete implementation
    index = model.index(0, 99)
    assert model.data(index, Qt.ItemDataRole.DisplayRole) is None