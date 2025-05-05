"""
Example Qt UI test demonstrating the BaseQtTest class and qt_test_utils module.
"""

import pytest
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from tests.ui.base_qt_test import BaseQtTest


class SimpleForm(QWidget):
    """A simple form widget for testing."""
    
    submitted = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Form")
        self.setObjectName("simple_form")
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # Add a title label
        self.title_label = QLabel("Enter your name:")
        self.title_label.setObjectName("title_label")
        self.layout.addWidget(self.title_label)
        
        # Add a name input field
        self.name_input = QLineEdit()
        self.name_input.setObjectName("name_input")
        self.name_input.setPlaceholderText("Your name here")
        self.layout.addWidget(self.name_input)
        
        # Add submit button
        self.submit_button = QPushButton("Submit")
        self.submit_button.setObjectName("submit_button")
        self.submit_button.clicked.connect(self.on_submit)
        self.layout.addWidget(self.submit_button)
        
        # Add a clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.setObjectName("clear_button")
        self.clear_button.clicked.connect(self.on_clear)
        self.layout.addWidget(self.clear_button)
        
        # Add a result label
        self.result_label = QLabel("")
        self.result_label.setObjectName("result_label")
        self.layout.addWidget(self.result_label)
        
        # Initially disable the submit button
        self.submit_button.setEnabled(False)
        
        # Connect the text changed signal to enable/disable the submit button
        self.name_input.textChanged.connect(self.on_text_changed)
    
    def on_text_changed(self, text):
        """Enable the submit button only if there is text."""
        self.submit_button.setEnabled(len(text) > 0)
    
    def on_submit(self):
        """Handle form submission."""
        name = self.name_input.text()
        self.result_label.setText(f"Hello, {name}!")
        self.submitted.emit(name)
    
    def on_clear(self):
        """Clear the form."""
        self.name_input.clear()
        self.result_label.clear()
    
    def show_confirmation(self):
        """Show a confirmation dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Confirmation")
        layout = QVBoxLayout(dialog)
        
        label = QLabel("Form data has been processed.")
        layout.addWidget(label)
        
        button = QPushButton("OK")
        button.clicked.connect(dialog.accept)
        layout.addWidget(button)
        
        # Use a timer to show the dialog after a short delay
        QTimer.singleShot(100, dialog.exec)
        

class TestSimpleForm(BaseQtTest):
    """Test case for the SimpleForm widget."""
    
    def setup_method(self, method):
        """Set up the test fixture."""
        super().setup_method(method)
        self.form = SimpleForm()
        self.add_widget(self.form)
        self.form.show()
        self.process_events()
    
    def test_initial_state(self):
        """Test the initial state of the form."""
        self.assert_visible(self.form)
        self.assert_text_equals(self.form.title_label, "Enter your name:")
        self.assert_text_equals(self.form.name_input, "")
        self.assert_disabled(self.form.submit_button)
        self.assert_enabled(self.form.clear_button)
        self.assert_text_equals(self.form.result_label, "")
    
    def test_submit_button_enable_disable(self):
        """Test that the submit button is enabled/disabled based on input."""
        # Initially disabled
        self.assert_disabled(self.form.submit_button)
        
        # Enter text to enable the button
        self.set_text(self.form.name_input, "John Doe")
        self.assert_enabled(self.form.submit_button)
        
        # Clear text to disable the button
        self.set_text(self.form.name_input, "")
        self.assert_disabled(self.form.submit_button)
    
    def test_form_submission(self):
        """Test submitting the form."""
        # Set up signal capture
        with self.wait_for_signal(self.form.submitted):
            # Enter name and submit
            self.set_text(self.form.name_input, "Jane Smith")
            self.click_button(self.form, text="Submit")
        
        # Verify result
        self.assert_text_equals(self.form.result_label, "Hello, Jane Smith!")
    
    def test_form_clear(self):
        """Test clearing the form."""
        # Setup form with data
        self.set_text(self.form.name_input, "Test User")
        self.click_button(self.form, text="Submit")
        
        # Verify data is present
        self.assert_text_equals(self.form.name_input, "Test User")
        self.assert_text_equals(self.form.result_label, "Hello, Test User!")
        
        # Clear the form
        self.click_button(self.form, text="Clear")
        
        # Verify form is cleared
        self.assert_text_equals(self.form.name_input, "")
        self.assert_text_equals(self.form.result_label, "")
    
    def test_dialog_capture(self):
        """Test capturing a dialog."""
        with self.capture_dialogs() as dialogs:
            # Trigger the dialog
            self.form.show_confirmation()
            self.process_events(200)  # Allow time for dialog to appear
            
            # Verify dialog was shown and captured
            assert len(dialogs) == 1
            assert dialogs[0].windowTitle() == "Confirmation"
            
            # Find and verify dialog contents
            label = self.find_widget_by_name(dialogs[0], QLabel, "")
            assert label is not None
            self.assert_text_equals(label, "Form data has been processed.")
    
    def test_finding_widgets(self):
        """Test widget finding utilities."""
        # Find by type
        labels = self.find_widgets(self.form, QLabel)
        assert len(labels) == 2  # title_label and result_label
        
        # Find by name
        name_input = self.find_widget_by_name(self.form, QLineEdit, "name_input")
        assert name_input is self.form.name_input
        
        # Find button by text
        submit_button = self.find_button(self.form, text="Submit")
        assert submit_button is self.form.submit_button
        
        # Find button by name
        clear_button = self.find_button(self.form, name="clear_button")
        assert clear_button is self.form.clear_button
    
    def test_wait_until(self):
        """Test the wait_until utility."""
        # Set up a delayed action
        QTimer.singleShot(200, lambda: self.set_text(self.form.name_input, "Delayed Text"))
        
        # Wait for the condition to be true
        result = self.wait_until(lambda: self.form.name_input.text() == "Delayed Text")
        
        # Verify the wait succeeded
        assert result is True
        self.assert_text_equals(self.form.name_input, "Delayed Text") 