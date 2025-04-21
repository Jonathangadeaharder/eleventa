"""
Tests for the ViewBase UI component.
Focus: Base view initialization, methods, and widget behavior.

This test suite verifies the functionality of the ViewBase component, including:
- UI initialization and widget availability
- Search functionality
- Table view configuration
- Button creation and styling
- Helper methods for error handling and user interaction
"""

# Standard library imports
import sys
from decimal import Decimal

# Testing frameworks
import pytest
from unittest.mock import MagicMock, patch

# Qt components
from PySide6.QtWidgets import (
    QApplication, QTableView, QPushButton, QFrame, 
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QAbstractItemView
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QIcon

# Application components
from ui.views.view_base import ViewBase
from ui.utils import show_error_message, show_info_message, ask_confirmation

# Test utilities
import sys
import os
# Add root directory to path to import patch_resources
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from tests.ui import patch_resources

# Apply timeout to all tests to prevent hanging
pytestmark = pytest.mark.timeout(5)

# Mock classes for testing
class MockTableModel(QAbstractTableModel):
    """Mock table model for testing table view functionality."""
    
    def __init__(self):
        super().__init__()
        self.data_list = [{"id": 1, "name": "Test Item 1"}, {"id": 2, "name": "Test Item 2"}]
    
    def rowCount(self, parent=QModelIndex()):
        return len(self.data_list)
    
    def columnCount(self, parent=QModelIndex()):
        return 2
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
            
        if role == Qt.DisplayRole:
            item = self.data_list[index.row()]
            if index.column() == 0:
                return item["id"]
            elif index.column() == 1:
                return item["name"]
                
        if role == Qt.UserRole:
            return self.data_list[index.row()]
            
        return None
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == 0:
                return "ID"
            elif section == 1:
                return "Name"
        return None

@pytest.fixture
def mock_table_view():
    """Create a mock table view for testing."""
    return QTableView()

@pytest.fixture
def view_base(qtbot, monkeypatch):
    """Create a ViewBase instance for testing with mocked components."""
    # Patch dialogs to prevent hanging tests
    monkeypatch.setattr(
        'ui.utils.show_error_message', 
        MagicMock(return_value=None)
    )
    monkeypatch.setattr(
        'ui.utils.show_info_message',
        MagicMock(return_value=None)
    )
    monkeypatch.setattr(
        'ui.utils.ask_confirmation',
        MagicMock(return_value=True)  # Always return True for confirmation dialogs
    )
    
    # Initialize view with aggressive event processing
    view = None
    try:
        view = ViewBase()
        qtbot.addWidget(view)
        view.show()
        
        # Process events to ensure UI is ready
        for _ in range(3):  # Process events multiple times for stability
            QApplication.processEvents()
            qtbot.wait(50)  # Short wait to process any pending events
        
        yield view
    
    finally:
        # Ensure resources are always cleaned up, even if test fails
        if view is not None:
            try:
                view.close()
                view.deleteLater()
                for _ in range(3):  # Process events multiple times for cleanup
                    QApplication.processEvents()
                    qtbot.wait(50)
            except Exception as e:
                print(f"Error during cleanup: {e}")
                # Continue with cleanup despite errors

# INITIALIZATION TESTS

def test_view_base_initialization(view_base):
    """
    Test that ViewBase initializes correctly with all expected widgets and layouts.
    
    Verifies the base structure and widgets are created correctly.
    """
    # Check that main components exist
    assert hasattr(view_base, 'main_layout')
    assert hasattr(view_base, 'header_frame')
    assert hasattr(view_base, 'header_layout')
    assert hasattr(view_base, 'content_frame')
    assert hasattr(view_base, 'content_layout')
    assert hasattr(view_base, 'footer_frame')
    assert hasattr(view_base, 'footer_layout')
    
    # Check that view title exists
    assert hasattr(view_base, 'view_title')
    assert isinstance(view_base.view_title, QLabel)
    assert view_base.view_title.text() == "View Title"
    
    # Check that search components exist
    assert hasattr(view_base, 'search_container')
    assert hasattr(view_base, 'search_entry')
    assert hasattr(view_base, 'search_label')
    assert isinstance(view_base.search_entry, QLineEdit)
    assert view_base.search_label.text() == "Buscar:"

def test_view_base_layout_structure(view_base):
    """
    Test that the layout structure is correctly set up.
    
    Verifies that layouts are nested correctly and have appropriate properties.
    """
    # Main layout checks
    assert isinstance(view_base.main_layout, QVBoxLayout)
    
    # Extract margins as individual values
    margins = view_base.main_layout.contentsMargins()
    assert margins.left() == 12
    assert margins.top() == 12
    assert margins.right() == 12
    assert margins.bottom() == 12
    
    assert view_base.main_layout.spacing() == 10
    
    # Header layout checks
    assert isinstance(view_base.header_layout, QHBoxLayout)
    
    # Content layout checks
    assert isinstance(view_base.content_layout, QVBoxLayout)
    
    # Footer layout checks
    assert isinstance(view_base.footer_layout, QHBoxLayout)

# FUNCTIONALITY TESTS

def test_set_view_title(view_base):
    """
    Test setting the view title.
    
    Verifies that the set_view_title method updates the title label.
    """
    # Initial title
    assert view_base.view_title.text() == "View Title"
    
    # Update title
    view_base.set_view_title("New Title")
    
    # Check updated title
    assert view_base.view_title.text() == "New Title"

def test_setup_table_view(view_base, mock_table_view):
    """
    Test the setup_table_view method.
    
    Verifies that a table view is configured correctly with standard settings.
    """
    # Create a mock model
    model = MockTableModel()
    
    # Set up the table view
    view_base.setup_table_view(mock_table_view, model)
    
    # Check that the model was set
    assert mock_table_view.model() == model
    
    # Check selection settings
    assert mock_table_view.selectionBehavior() == QAbstractItemView.SelectionBehavior.SelectRows
    assert mock_table_view.selectionMode() == QAbstractItemView.SelectionMode.SingleSelection
    
    # Check edit triggers
    assert mock_table_view.editTriggers() == QAbstractItemView.EditTrigger.NoEditTriggers
    
    # Check other settings
    assert mock_table_view.alternatingRowColors() is True

def test_setup_table_view_with_editing(view_base, mock_table_view):
    """
    Test the setup_table_view method with editing enabled.
    
    Verifies that a table view is configured correctly with editing enabled.
    """
    # Create a mock model
    model = MockTableModel()
    
    # Set up the table view with editing enabled
    view_base.setup_table_view(mock_table_view, model, enable_editing=True)
    
    # Check edit triggers allow editing
    assert mock_table_view.editTriggers() != QAbstractItemView.EditTrigger.NoEditTriggers

def test_add_action_button(view_base, qtbot):
    """
    Test adding an action button.
    
    Verifies that the add_action_button method creates a button and connects it.
    """
    # Mock slot
    mock_slot = MagicMock()
    
    # Add a button
    button = view_base.add_action_button("Test Button", connected_slot=mock_slot)
    
    # Check button properties
    assert isinstance(button, QPushButton)
    assert button.text() == "Test Button"
    
    # Click the button and check if the slot was called
    qtbot.mouseClick(button, Qt.LeftButton)
    QApplication.processEvents()
    mock_slot.assert_called_once()

def test_add_primary_action_button(view_base):
    """
    Test adding a primary action button.
    
    Verifies that the add_action_button method with is_primary=True creates a differently styled button.
    """
    # Add a primary button
    button = view_base.add_action_button("Primary Button", is_primary=True)
    
    # Check button properties
    assert isinstance(button, QPushButton)
    assert button.text() == "Primary Button"
    
    # Primary buttons have different styling, but we can't easily check stylesheet contents directly
    # At minimum, verify that stylesheet is not empty
    assert button.styleSheet() != ""

def test_get_selected_row_data(view_base, mock_table_view, monkeypatch):
    """
    Test getting selected row data.
    
    Verifies that the get_selected_row_data method returns the correct data from a selected row.
    """
    # Create a mock model
    model = MockTableModel()
    mock_table_view.setModel(model)
    
    # Create a mock selection model
    mock_selection_model = MagicMock()
    mock_index = QModelIndex()
    
    # Setup mock to simulate a selected row
    def mock_data(role):
        if role == Qt.UserRole:
            return {"id": 1, "name": "Test Item 1"}
        return None
    
    # Patch the model index data method
    mock_index.data = mock_data
    mock_selection_model.selectedRows.return_value = [mock_index]
    mock_table_view.selectionModel = MagicMock(return_value=mock_selection_model)
    
    # Get the selected row data
    result = view_base.get_selected_row_data(mock_table_view)
    
    # Check the result
    assert result == {"id": 1, "name": "Test Item 1"}

def test_get_selected_row_data_no_selection(view_base, mock_table_view):
    """
    Test getting selected row data when no row is selected.
    
    Verifies that the get_selected_row_data method returns None when no row is selected.
    """
    # Create a mock model
    model = MockTableModel()
    mock_table_view.setModel(model)
    
    # Create a mock selection model with no selection
    mock_selection_model = MagicMock()
    mock_selection_model.selectedRows.return_value = []
    mock_table_view.selectionModel = MagicMock(return_value=mock_selection_model)
    
    # Get the selected row data
    result = view_base.get_selected_row_data(mock_table_view)
    
    # Check the result
    assert result is None

# ERROR HANDLING TESTS

def test_error_handling_methods_exist(view_base):
    """
    Test that error handling methods exist and are callable.
    
    Since directly testing the calls to dialog display is challenging in a UI environment,
    we simply verify the methods exist and are callable.
    """
    # Check methods exist
    assert hasattr(view_base, 'show_error')
    assert hasattr(view_base, 'show_info')
    assert hasattr(view_base, 'ask_confirmation')
    
    # Check they are callable
    assert callable(view_base.show_error)
    assert callable(view_base.show_info)
    assert callable(view_base.ask_confirmation)
    
    # Call methods without raising exceptions (with mocked behavior via fixture)
    view_base.show_error("Error Title", "Error Message")
    view_base.show_info("Info Title", "Info Message")
    result = view_base.ask_confirmation("Confirm Title", "Confirm Message")
    
    # Check confirmation returns a boolean (from our mocked version)
    assert isinstance(result, bool)

# SEARCH FUNCTIONALITY TESTS

def test_hide_search(view_base):
    """
    Test hiding the search container.
    
    Verifies that the hide_search method correctly hides the search container.
    """
    # Initially visible
    assert view_base.search_container.isVisible() is True
    
    # Hide search
    view_base.hide_search()
    
    # Check visibility
    assert view_base.search_container.isVisible() is False

def test_show_search(view_base):
    """
    Test showing the search container after hiding it.
    
    Verifies that the show_search method correctly shows the search container.
    """
    # First hide it
    view_base.hide_search()
    assert view_base.search_container.isVisible() is False
    
    # Show search
    view_base.show_search()
    
    # Check visibility
    assert view_base.search_container.isVisible() is True

def test_search_signal(view_base, qtbot, monkeypatch):
    """
    Test the search functionality.
    
    Verifies that pressing Enter in the search field triggers the _on_search method.
    """
    # Mock the _on_search method
    mock_on_search = MagicMock()
    monkeypatch.setattr(view_base, '_on_search', mock_on_search)
    
    # Enter text and press Enter
    qtbot.keyClicks(view_base.search_entry, "test search")
    qtbot.keyPress(view_base.search_entry, Qt.Key_Return)
    QApplication.processEvents()
    
    # Check if _on_search was called
    mock_on_search.assert_called_once() 