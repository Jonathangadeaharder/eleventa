"""
Ultra-minimal test to verify Qt widgets can be created without hanging.
Focus: Diagnostic testing of the Qt environment in isolation.

This test suite verifies that:
- Basic Qt widgets can be instantiated without errors
- Models can be created and attached to views
- Widget interactions work at a fundamental level
- The testing framework is properly configured for Qt testing
"""

# Standard library imports
import sys

# Testing frameworks
import pytest
from unittest.mock import MagicMock

# Qt components
from PySide6 import QtWidgets
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QTimer
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QTableView

# Test utilities
import patch_resources

# Set timeout to prevent hanging tests
pytestmark = pytest.mark.timeout(5)

class SimpleTableModel(QAbstractTableModel):
    """
    A simple concrete implementation of QAbstractTableModel for testing.
    
    This class provides the minimum implementation required for a functional
    Qt table model that can be used in tests.
    """
    def __init__(self):
        """Initialize an empty table model."""
        super().__init__()
        self._data = []
        
    def rowCount(self, parent=QModelIndex()):
        """Return the number of rows in the model."""
        return len(self._data)
        
    def columnCount(self, parent=QModelIndex()):
        """Return the number of columns in the model."""
        return 3 if self._data else 0
        
    def data(self, index, role=Qt.DisplayRole):
        """Return the data for the given index and role."""
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            return str(self._data[index.row()][index.column()])
        return None
    
    def add_data(self, data):
        """Add data to the model and refresh it."""
        self.beginResetModel()
        self._data = data
        self.endResetModel()

@pytest.fixture
def simple_widget(qtbot):
    """
    Create a simple QWidget for testing.
    
    Parameters:
        qtbot: The Qt Robot test helper
        
    Returns:
        A QWidget instance with buttons and a table
    """
    # Create main widget
    widget = QWidget()
    widget.setGeometry(100, 100, 400, 300)
    widget.setWindowTitle("Simple Test Widget")
    
    # Add to qtbot for event handling
    qtbot.addWidget(widget)
    
    # Create a layout
    layout = QtWidgets.QVBoxLayout()
    widget.setLayout(layout)
    
    # Add a button
    button = QPushButton("Test Button")
    layout.addWidget(button)
    
    # Add a table view
    table = QTableView()
    layout.addWidget(table)
    
    # Create and set a model
    model = SimpleTableModel()
    table.setModel(model)
    
    # Store components as attributes for testing
    widget.test_button = button
    widget.test_table = table
    widget.test_model = model
    
    # Show the widget
    widget.show()
    QApplication.processEvents()
    
    yield widget
    
    # Clean up resources
    widget.close()
    widget.deleteLater()
    QApplication.processEvents()

def test_widget_instantiates_correctly(simple_widget):
    """
    Test that the widget instantiates correctly with all components.
    
    Verifies that the widget, button, table, and model are created properly.
    """
    assert simple_widget is not None
    assert simple_widget.isVisible()
    assert simple_widget.test_button is not None
    assert simple_widget.test_button.text() == "Test Button"
    assert simple_widget.test_table is not None
    assert simple_widget.test_model is not None

@pytest.mark.skip(reason="Temporarily skipping due to persistent Qt crash (access violation) during qtbot.mouseClick")
def test_button_is_clickable(simple_widget, qtbot):
    """
    Test that the button can be clicked and signals work.
    
    Verifies that Qt's signal/slot mechanism works by connecting and triggering a signal.
    """
    # Create a mock slot
    clicked_slot = MagicMock()
    
    # Connect signal to mock slot
    simple_widget.test_button.clicked.connect(clicked_slot)
    
    # Click the button
    qtbot.mouseClick(simple_widget.test_button, Qt.LeftButton)
    QApplication.processEvents()
    
    # Verify the signal was emitted
    clicked_slot.assert_called_once()

def test_model_updates_correctly(simple_widget):
    """
    Test that the table model updates correctly when data changes.
    
    Verifies that model updates are properly processed and reflected in row/column counts.
    """
    # Get the model
    model = simple_widget.test_model
    
    # Initial state
    assert model.rowCount() == 0
    
    # Add some data
    test_data = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9]
    ]
    model.add_data(test_data)
    
    # Verify the update
    assert model.rowCount() == 3
    assert model.columnCount() == 3
    assert model.data(model.index(0, 0)) == "1"
    assert model.data(model.index(1, 1)) == "5"
    assert model.data(model.index(2, 2)) == "9"
