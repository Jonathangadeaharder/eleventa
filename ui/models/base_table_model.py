from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from typing import List, Any, Optional


class BaseTableModel(QAbstractTableModel):
    """Base class for table models to reduce code duplication."""

    HEADERS = []  # Should be overridden by subclasses

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Returns the number of rows."""
        return len(self._data)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Returns the number of columns."""
        return len(self.HEADERS)

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """Returns the header data."""
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            try:
                return self.HEADERS[section]
            except IndexError:
                return None
        return None

    def update_data(self, data: List):
        """Updates the model's data and refreshes the view."""
        self.beginResetModel()
        self._data = data
        self.endResetModel()

    def get_item_at_row(self, row: int) -> Optional[Any]:
        """Gets the item at a specific model row."""
        if 0 <= row < len(self._data):
            return self._data[row]
        return None
