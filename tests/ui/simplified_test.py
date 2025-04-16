"""
Ultra-minimal test to verify Qt widgets can be created without hanging.
"""
import pytest
from PySide6 import QtWidgets
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex

# Create a simple concrete model implementation
class SimpleTableModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self._data = []
        
    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
        
    def columnCount(self, parent=QModelIndex()):
        return 3 if self._data else 0
        
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            return str(self._data[index.row()][index.column()])
        return None

# Test if we can create a basic widget
def test_basic_widget(qtbot):
    """Test that we can create and show a basic widget."""
    widget = QtWidgets.QWidget()
    qtbot.addWidget(widget)
    widget.show()
    assert widget.isVisible()
    
    # Create a button
    button = QtWidgets.QPushButton("Test Button", widget)
    assert button is not None
    
    # Create a table
    table = QtWidgets.QTableView(widget)
    model = SimpleTableModel()
    table.setModel(model)
    assert table is not None
    
    # Test passes if it reaches here without hanging 