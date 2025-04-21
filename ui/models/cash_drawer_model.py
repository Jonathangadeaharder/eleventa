from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QBrush, QColor
from datetime import datetime
import locale
from decimal import Decimal

from core.models.cash_drawer import CashDrawerEntry, CashDrawerEntryType

# Configure locale for currency formatting
locale.setlocale(locale.LC_ALL, '')


class CashDrawerTableModel(QAbstractTableModel):
    """Table model for displaying cash drawer entries."""
    
    def __init__(self, entries=None):
        super().__init__()
        self._entries = entries or []
        self._headers = ["ID", "Fecha y Hora", "Tipo", "Monto", "Descripción", "Usuario"]
        
    def rowCount(self, parent=QModelIndex()):
        """Return the number of rows."""
        return len(self._entries)
        
    def columnCount(self, parent=QModelIndex()):
        """Return the number of columns."""
        return len(self._headers)
        
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """Return the data at the given index."""
        if not index.isValid() or not (0 <= index.row() < len(self._entries)):
            # In PySide6, return None for invalid/unhandled roles
            return None 
            
        entry = self._entries[index.row()]
        column = index.column()
        
        if role == Qt.ItemDataRole.DisplayRole:
            # Format the data for display
            if column == 0:  # ID
                return str(entry.id) if entry.id else ""
                
            elif column == 1:  # Timestamp
                if isinstance(entry.timestamp, datetime):
                    return entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                return str(entry.timestamp)
                
            elif column == 2:  # Type
                type_map = {
                    CashDrawerEntryType.START: "Apertura",
                    CashDrawerEntryType.IN: "Entrada",
                    CashDrawerEntryType.OUT: "Salida",
                    CashDrawerEntryType.SALE: "Venta",
                    CashDrawerEntryType.RETURN: "Retorno",
                    CashDrawerEntryType.CLOSE: "Cierre"
                }
                return type_map.get(entry.entry_type, str(entry.entry_type))
                
            elif column == 3:  # Amount
                if isinstance(entry.amount, (Decimal, float, int)):
                    return locale.currency(float(entry.amount), grouping=True)
                return str(entry.amount)
                
            elif column == 4:  # Description
                return entry.description
                
            elif column == 5:  # User
                # Use getattr for safer access
                return getattr(entry, 'user_name', str(entry.user_id))
                
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if column in (0, 1, 2, 5):  # ID, Timestamp, Type, User
                return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            elif column == 3:  # Amount
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                
        elif role == Qt.ItemDataRole.BackgroundRole:
            # Color rows based on entry type
            if entry.entry_type == CashDrawerEntryType.START:
                return QBrush(QColor(230, 255, 230))  # Light green
            elif entry.entry_type == CashDrawerEntryType.IN:
                return QBrush(QColor(230, 230, 255))  # Light blue
            elif entry.entry_type == CashDrawerEntryType.OUT:
                return QBrush(QColor(255, 230, 230))  # Light red
                
        # Return None for unhandled roles/cases
        return None
        
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        """Return the header data."""
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            # Check bounds
            if 0 <= section < len(self._headers):
                return self._headers[section]
        # Return None for other cases
        return None
        
    def setEntries(self, entries):
        """Update the entries in the model."""
        self.beginResetModel()
        self._entries = entries
        self.endResetModel()