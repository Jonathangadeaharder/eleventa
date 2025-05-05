"""
Example test to demonstrate the usage of the BaseQtTest class.

This test shows how to:
- Set up a test case with BaseQtTest
- Create and interact with widgets
- Use helper methods for common assertions
- Test dialog interactions
"""
import pytest
from PySide6.QtCore import Slot, Signal, QTimer
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton, 
    QLineEdit, QLabel, QMessageBox
)

from tests.ui.base_qt_test import BaseQtTest


class ExampleWidget(QWidget):
    """A simple widget for testing purposes."""
    
    textSubmitted = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ExampleWidget")
        
        self.layout = QVBoxLayout(self)
        
        self.label = QLabel("Enter some text:")
        self.label.setObjectName("instructionLabel")
        self.layout.addWidget(self.label)
        
        self.input = QLineEdit()
        self.input.setObjectName("textInput")
        self.layout.addWidget(self.input)
        
        self.submit_btn = QPushButton("Submit")
        self.submit_btn.setObjectName("submitButton")
        self.submit_btn.setEnabled(False)
        self.layout.addWidget(self.submit_btn)
        
        self.show_dialog_btn = QPushButton("Show Dialog")
        self.show_dialog_btn.setObjectName("dialogButton")
        self.layout.addWidget(self.show_dialog_btn)
        
        self.result_label = QLabel("")
        self.result_label.setObjectName("resultLabel")
        self.layout.addWidget(self.result_label)
        
        # Connect signals
        self.input.textChanged.connect(self._on_text_changed)
        self.submit_btn.clicked.connect(self._on_submit)
        self.show_dialog_btn.clicked.connect(self._show_dialog)
        
    @Slot(str)
    def _on_text_changed(self, text):
        """Enable submit button if text is not empty"""
        self.submit_btn.setEnabled(bool(text))
        
    @Slot()
    def _on_submit(self):
        """Process the submitted text"""
        text = self.input.text()
        self.result_label.setText(f"You entered: {text}")
        self.textSubmitted.emit(text)
        
    @Slot()
    def _show_dialog(self):
        """Show a simple message dialog"""
        QMessageBox.information(
            self, 
            "Information", 
            "This is a test dialog message"
        )


class TestExampleWidget(BaseQtTest):
    """Test case for the ExampleWidget."""
    
    def setup_method(self):
        """Set up the test environment before each test method."""
        self.widget = ExampleWidget()
        self.add_widget(self.widget)
        self.widget.show()
        
    def test_initial_state(self):
        """Test the initial state of the widget."""
        # Submit button should be disabled initially
        self.assert_disabled(self.widget.submit_btn)
        
        # Result label should be empty
        self.assert_text_equals(self.widget.result_label, "")
        
    def test_input_enables_button(self):
        """Test that entering text enables the submit button."""
        # Initially disabled
        self.assert_disabled(self.widget.submit_btn)
        
        # Enter text
        self.qtbot.keyClicks(self.widget.input, "Hello, World!")
        
        # Button should now be enabled
        self.assert_enabled(self.widget.submit_btn)
        
    def test_submit_updates_result(self):
        """Test that submitting text updates the result label."""
        test_text = "Test Input"
        
        # Enter text
        self.qtbot.keyClicks(self.widget.input, test_text)
        
        # Click submit
        self.click_button(self.widget, "Submit")
        
        # Check result label
        expected_text = f"You entered: {test_text}"
        self.assert_text_equals(self.widget.result_label, expected_text)
        
    def test_signal_emission(self):
        """Test that the textSubmitted signal is emitted."""
        test_text = "Signal Test"
        
        # Set up signal spy
        with self.qtbot.waitSignal(self.widget.textSubmitted, timeout=1000) as signal_spy:
            # Enter text
            self.qtbot.keyClicks(self.widget.input, test_text)
            
            # Click submit
            self.click_button(self.widget, "Submit")
            
        # Verify signal was emitted with correct argument
        assert signal_spy.args[0] == test_text
        
    def test_dialog_shown(self):
        """Test that clicking the dialog button shows a dialog."""
        # Click the dialog button
        self.click_button(self.widget, name="dialogButton")
        
        # Assert dialog was shown with expected title and message
        self.assert_dialog_shown(
            title="Information", 
            message="This is a test dialog message"
        )
        
    def test_find_widgets(self):
        """Test the widget finding methods."""
        # Find button by text
        submit_btn = self.find_button(self.widget, text="Submit")
        assert submit_btn is not None
        assert submit_btn.objectName() == "submitButton"
        
        # Find button by name
        dialog_btn = self.find_button(self.widget, name="dialogButton")
        assert dialog_btn is not None
        assert dialog_btn.text() == "Show Dialog"
        
        # Find widget by type and name
        label = self.find_widget_by_name(self.widget, QLabel, "resultLabel")
        assert label is not None
        
        # Find all labels
        labels = self.find_widgets(self.widget, QLabel)
        assert len(labels) == 2 