"""
Minimal UI test file for edge-case or smoke testing.
Focus: Ensures test infrastructure is operational and basic UI instantiation works without error.

This test suite provides a minimal set of tests to verify that:
- Qt test infrastructure is working correctly
- Basic UI components can be instantiated
- Mock services can be integrated with UI components
- Events are properly processed
"""

# Standard library imports
import sys
import os

# Testing frameworks
import pytest
from unittest.mock import MagicMock, patch

# Qt components
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer

# Test utilities for stable UI testing
from tests.ui.qt_test_utils import process_events, safe_click_button

# Set timeout to prevent hanging tests
pytestmark = [
    pytest.mark.timeout(5),
    # Skip in general UI testing to avoid access violations
    pytest.mark.skipif("ui" in sys.argv, reason="Skip for general UI test runs to avoid access violations")
]

class MinimalTestWidget(QWidget):
    """A minimal widget for testing the Qt test infrastructure."""
    
    def __init__(self, service=None):
        """Initialize the minimal test widget with optional service dependency."""
        super().__init__()
        self.setWindowTitle("Minimal Test Widget")
        self.setupUi()
        self.service = service or MagicMock()
        self.button_clicked = False
        
    def setupUi(self):
        """Set up the UI components."""
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        self.label = QLabel("Test Label")
        self.layout.addWidget(self.label)
        
        self.button = QPushButton("Test Button")
        self.button.clicked.connect(self.handleButtonClick)
        self.layout.addWidget(self.button)
        
    def handleButtonClick(self):
        """Handle button click event."""
        self.button_clicked = True
        self.service.performAction()
        self.label.setText("Button Clicked")

class MockService:
    """A mock service for testing."""
    
    def __init__(self):
        """Initialize the mock service."""
        self.action_performed = False
        
    def performAction(self):
        """Perform a mock action."""
        self.action_performed = True
        return True

@pytest.fixture
def mock_service():
    """Create a mock service for testing."""
    return MockService()

@pytest.fixture
def minimal_widget(qtbot, mock_service, monkeypatch):
    """Create a minimal widget for testing with qtbot.
    
    Parameters:
        qtbot: The Qt Robot test helper
        mock_service: The mock service to inject
        monkeypatch: For patching widget methods
        
    Returns:
        A MinimalTestWidget instance with the mock service injected
    """
    # Create widget with mock service
    widget = MinimalTestWidget(service=mock_service)
    qtbot.addWidget(widget)
    
    # Show the widget but don't wait for it to appear
    widget.show()
    process_events()
    
    yield widget
    
    # Clean up resources safely
    widget.hide()  # Hide first to avoid rendering issues during deletion
    process_events()
    widget.deleteLater()
    process_events()

def test_minimal_widget_instantiates(minimal_widget):
    """
    Test that the minimal widget instantiates correctly.
    
    Verifies that the widget and its components are created properly.
    """
    assert minimal_widget is not None
    assert minimal_widget.windowTitle() == "Minimal Test Widget"
    assert minimal_widget.label.text() == "Test Label"
    assert minimal_widget.button.text() == "Test Button"
    assert isinstance(minimal_widget.layout, QVBoxLayout)

def test_button_click_updates_ui(minimal_widget):
    """
    Test that clicking the button updates the UI correctly.
    
    Verifies that clicking the button changes the label text and updates internal state.
    """
    # Initial state
    assert minimal_widget.button_clicked is False
    assert minimal_widget.label.text() == "Test Label"
    
    # Use safe button click instead of mouse click
    safe_click_button(minimal_widget.button)
    process_events()
    
    # Check updated state
    assert minimal_widget.button_clicked is True
    assert minimal_widget.label.text() == "Button Clicked"

def test_service_interaction(minimal_widget, mock_service):
    """
    Test that the widget interacts with the service correctly.
    
    Verifies that clicking the button calls the service method and receives the response.
    """
    # Initial state
    assert mock_service.action_performed is False
    
    # Use safe button click
    safe_click_button(minimal_widget.button)
    process_events()
    
    # Verify service was called
    assert mock_service.action_performed is True

def test_widget_with_mocked_methods(minimal_widget, monkeypatch):
    """
    Test the widget with mocked methods to verify interactions.
    
    Shows how to use monkeypatch to mock methods of the widget under test.
    """
    # Mock the handleButtonClick method
    mock_handler = MagicMock()
    monkeypatch.setattr(minimal_widget, "handleButtonClick", mock_handler)
    
    # Use safe button click
    safe_click_button(minimal_widget.button)
    process_events()
    
    # Verify the mock was called
    mock_handler.assert_called_once()