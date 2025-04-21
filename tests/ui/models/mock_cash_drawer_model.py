from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QBrush, QColor
from unittest.mock import MagicMock

from ui.models.cash_drawer_model import CashDrawerTableModel
from core.models.cash_drawer import CashDrawerEntry, CashDrawerEntryType


class MockCashDrawerTableModel(QAbstractTableModel, MagicMock):
    """
    A mock implementation of CashDrawerTableModel for testing.
    
    This class combines Qt's QAbstractTableModel with Python's MagicMock to create
    a mock table model that can be used in tests without relying on the actual Qt component
    implementation while still being compatible with Qt's model/view architecture.
    """
    def __init__(self, *args, **kwargs):
        QAbstractTableModel.__init__(self)
        MagicMock.__init__(self, *args, **kwargs)
        
        # Mock the abstract methods that must be implemented
        self.rowCount = MagicMock(return_value=0)
        self.columnCount = MagicMock(return_value=6)  # Match CashDrawerTableModel's column count
        self.data = MagicMock(return_value=None)
        self.headerData = MagicMock(return_value=None)
        self.index = MagicMock(return_value=QModelIndex())
        self.parent = MagicMock(return_value=QModelIndex())
        
        # Add specific methods from CashDrawerTableModel
        self.setEntries = MagicMock()
        
        # Store entries for potential access during tests
        self._entries = []
        self._headers = ["ID", "Fecha y Hora", "Tipo", "Monto", "Descripción", "Usuario"]
    
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
    
    def configure_data_responses(self, data_map=None):
        """
        Configure the data method to return specific values based on row, column and role.
        
        Args:
            data_map: A dictionary with keys as tuples (row, column, role) and values 
                     as the data to return. If None, default responses are configured.
        """
        if data_map is None:
            data_map = {}
        
        # Update the data method to use the map
        def mock_data(index, role=Qt.ItemDataRole.DisplayRole):
            key = (index.row(), index.column(), role)
            if key in data_map:
                return data_map[key]
            return None
            
        self.data = MagicMock(side_effect=mock_data)
    
    def simulate_entries(self, entries):
        """
        Store entries and update rowCount to simulate having data.
        
        Args:
            entries: A list of CashDrawerEntry objects to simulate
        """
        self._entries = entries
        self.rowCount = MagicMock(return_value=len(entries))
        
        # Automatically configure some basic data responses
        data_map = {}
        for row, entry in enumerate(entries):
            # ID column
            data_map[(row, 0, Qt.ItemDataRole.DisplayRole)] = str(entry.id) if entry.id else ""
            
            # Entry type column
            type_map = {
                CashDrawerEntryType.START: "Apertura",
                CashDrawerEntryType.IN: "Entrada",
                CashDrawerEntryType.OUT: "Salida",
                CashDrawerEntryType.SALE: "Venta",
                CashDrawerEntryType.RETURN: "Retorno",
                CashDrawerEntryType.CLOSE: "Cierre"
            }
            data_map[(row, 2, Qt.ItemDataRole.DisplayRole)] = type_map.get(entry.entry_type, str(entry.entry_type))
            
            # Description column
            data_map[(row, 4, Qt.ItemDataRole.DisplayRole)] = entry.description
            
        self.configure_data_responses(data_map)
    
    def get_entry_at_row(self, row):
        """
        Get the entry at the specified row, if it exists.
        
        Args:
            row: The row index
            
        Returns:
            The CashDrawerEntry object at the specified row, or None if not found
        """
        if 0 <= row < len(self._entries):
            return self._entries[row]
        return None 