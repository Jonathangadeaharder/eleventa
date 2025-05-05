"""
Sample test demonstrating how to use the Qt test helpers and base test class.
This test creates a simple window and tests some basic interactions.
"""
import pytest
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QVBoxLayout, QLineEdit, QLabel
)
from PySide6.QtCore import Signal, Slot, Qt, QTimer

from tests.ui.qt_test_base import BaseQtTest
from tests.ui.qt_test_helpers import process_events, mock_dialogs

@pytest.fixture
def mock_dialogs_fixture():
    """Fixture for mock dialogs."""
    with mock_dialogs() as dialogs:
        yield dialogs

class SampleWindow(QMainWindow):
    """A simple window for demonstration purposes."""
    
    data_changed = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sample Window")
        self.resize(300, 200)
        
        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)
        
        # Add widgets
        self.label = QLabel("Enter text:")
        self.text_input = QLineEdit()
        self.submit_button = QPushButton("Submit")
        self.clear_button = QPushButton("Clear")
        
        # Connect signals
        self.submit_button.clicked.connect(self.on_submit)
        self.clear_button.clicked.connect(self.on_clear)
        
        # Add widgets to layout
        layout.addWidget(self.label)
        layout.addWidget(self.text_input)
        layout.addWidget(self.submit_button)
        layout.addWidget(self.clear_button)
        
        # Track state
        self.submission_count = 0
        self.last_text = ""
        
    def on_submit(self):
        """Handle submit button click."""
        text = self.text_input.text()
        if text:
            self.submission_count += 1
            self.last_text = text
            self.data_changed.emit(text)
            
            # Show confirmation message
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(
                self, "Submission", f"Text submitted: {text}"
            )
    
    def on_clear(self):
        """Handle clear button click."""
        self.text_input.clear()


class TestSampleWindow(BaseQtTest):
    """Test the SampleWindow class using the BaseQtTest class."""
    
    def test_window_creation(self):
        """Test that the window can be created successfully."""
        # Create the window
        window = self.add_widget(SampleWindow())
        
        # Check that the window has the expected title
        assert window.windowTitle() == "Sample Window"
        
        # Check that the window has the expected widgets
        assert isinstance(window.text_input, QLineEdit)
        assert isinstance(window.submit_button, QPushButton)
        assert isinstance(window.clear_button, QPushButton)
    
    def test_button_interactions(self, qtbot, mock_dialogs_fixture):
        """Test button interactions with the window."""
        # Create the window
        window = self.add_widget(SampleWindow())
        window.show()
        
        # Make sure the window is visible
        process_events()
        assert window.isVisible()
        
        # Initially, submission count should be 0
        assert window.submission_count == 0
        
        # Type text in the input field
        test_text = "Hello, World!"
        qtbot.keyClicks(window.text_input, test_text)
        
        # Verify text was entered
        assert window.text_input.text() == test_text
        
        # Use signal capture with context manager
        with self.wait_signal(window.data_changed, timeout=1000):
            # Click the submit button
            qtbot.mouseClick(window.submit_button, Qt.LeftButton)
        
        # Verify the submission was counted
        assert window.submission_count == 1
        assert window.last_text == test_text
        
        # Check that the dialog was mocked (no real dialogs appeared)
        assert mock_dialogs_fixture.message_shown
        assert "Hello, World!" in mock_dialogs_fixture.last_message
        
        # Click the clear button
        qtbot.mouseClick(window.clear_button, Qt.LeftButton)
        
        # Verify the input was cleared
        assert window.text_input.text() == ""
    
    def test_wait_for_condition(self, qtbot):
        """Test the wait_for method to handle async operations."""
        # Create the window
        window = self.add_widget(SampleWindow())
        
        # Set up a test that will pass after a delay
        def delayed_operation():
            window.text_input.setText("Delayed Text")
            
        # Schedule the operation to run shortly
        QTimer.singleShot(100, delayed_operation)
        
        # Wait for the condition using the utility method
        result = self.wait_for(
            lambda: window.text_input.text() == "Delayed Text",
            timeout=1000
        )
        
        # Verify that the wait was successful
        assert result is True
        assert window.text_input.text() == "Delayed Text"
        
    def test_exception_handling(self):
        """Test the exception handling utility."""
        def function_that_raises():
            raise ValueError("Test exception")
            
        # Capture the exception
        result, exception = self.capture_exceptions(function_that_raises)
        
        # Verify the exception was captured
        assert result is None
        assert isinstance(exception, ValueError)
        assert str(exception) == "Test exception" 