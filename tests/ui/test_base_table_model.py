import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import Qt, QModelIndex
from ui.models.base_table_model import BaseTableModel


class TestBaseTableModel:
    @pytest.fixture
    def base_model(self):
        # Create a concrete subclass for testing
        class ConcreteTableModel(BaseTableModel):
            def __init__(self):
                super().__init__()
                self._headers = ["ID", "Name", "Value"]
                self._data = [
                    [1, "Item 1", 100],
                    [2, "Item 2", 200],
                    [3, "Item 3", 300],
                ]
                
            def _get_item_data(self, row):
                return self._data[row]
                
            def refresh_data(self):
                # Simple implementation for testing
                pass
                
        return ConcreteTableModel()
    
    def test_row_count(self, base_model):
        # Test rowCount method
        assert base_model.rowCount() == 3
        
        # Test with parent
        parent = QModelIndex()
        assert base_model.rowCount(parent) == 3
        
    def test_column_count(self, base_model):
        # Test columnCount method
        assert base_model.columnCount() == 3
        
        # Test with parent
        parent = QModelIndex()
        assert base_model.columnCount(parent) == 3
        
    def test_data(self, base_model):
        # Test data method with display role
        for row in range(3):
            for col in range(3):
                index = base_model.index(row, col)
                data = base_model.data(index, Qt.DisplayRole)
                assert data == base_model._data[row][col]
                
        # Test with invalid index
        invalid_index = QModelIndex()
        assert base_model.data(invalid_index, Qt.DisplayRole) is None
        
        # Test with invalid row
        invalid_row_index = base_model.index(10, 0)  # Row out of bounds
        assert base_model.data(invalid_row_index, Qt.DisplayRole) is None
        
    def test_header_data(self, base_model):
        # Test headerData method with horizontal orientation
        for section in range(3):
            header = base_model.headerData(section, Qt.Horizontal, Qt.DisplayRole)
            assert header == base_model._headers[section]
            
        # Test with vertical orientation (should return section number + 1)
        for section in range(3):
            header = base_model.headerData(section, Qt.Vertical, Qt.DisplayRole)
            assert header == section + 1
            
        # Test with invalid orientation
        assert base_model.headerData(0, 3, Qt.DisplayRole) is None
        
        # Test with invalid role
        assert base_model.headerData(0, Qt.Horizontal, Qt.EditRole) is None
        
    def test_refresh_data(self, base_model):
        # Since refresh_data is abstract, we're just testing that it can be called
        base_model.refresh_data()
        
    def test_get_item_at_row(self, base_model):
        # Test _get_item_data method
        for row in range(3):
            item_data = base_model._get_item_data(row)
            assert item_data == base_model._data[row] 