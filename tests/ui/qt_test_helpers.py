"""
Helper functions and classes for Qt testing.
"""
import os
import time
from contextlib import contextmanager

from PySide6.QtCore import QTimer, QEventLoop, Qt, QObject, Signal
from PySide6.QtWidgets import (
    QApplication, QMessageBox, QDialog, QInputDialog, QFileDialog
)

def process_events(timeout=10):
    """Process pending Qt events for a short period."""
    app = QApplication.instance()
    if not app:
        return
        
    start = time.time()
    while time.time() - start < timeout / 1000:
        app.processEvents()

def wait_for(condition_func, timeout=5000, interval=50):
    """Wait for a condition to be true, with timeout."""
    start = time.time()
    while (time.time() - start) * 1000 < timeout:
        if condition_func():
            return True
        process_events(interval)
    return False

class MockDialogHandler(QObject):
    """Mock dialog handler for testing."""
    
    def __init__(self):
        super().__init__()
        self.reset()
        
    def reset(self):
        """Reset all mocked dialog state."""
        self.message_shown = False
        self.last_title = ""
        self.last_message = ""
        self.last_buttons = QMessageBox.StandardButton.Ok
        self.input_result = ""
        self.file_result = ""
        self.dir_result = ""
    
    def mock_information(self, parent, title, text, buttons=QMessageBox.StandardButton.Ok, defaultButton=QMessageBox.StandardButton.NoButton):
        """Mock QMessageBox.information."""
        self.message_shown = True
        self.last_title = title
        self.last_message = text
        self.last_buttons = buttons
        # Return the default button or Ok
        return defaultButton if defaultButton != QMessageBox.StandardButton.NoButton else QMessageBox.StandardButton.Ok
    
    def mock_warning(self, parent, title, text, buttons=QMessageBox.StandardButton.Ok, defaultButton=QMessageBox.StandardButton.NoButton):
        """Mock QMessageBox.warning."""
        self.message_shown = True
        self.last_title = title
        self.last_message = text
        self.last_buttons = buttons
        # Return the default button or Ok
        return defaultButton if defaultButton != QMessageBox.StandardButton.NoButton else QMessageBox.StandardButton.Ok
    
    def mock_critical(self, parent, title, text, buttons=QMessageBox.StandardButton.Ok, defaultButton=QMessageBox.StandardButton.NoButton):
        """Mock QMessageBox.critical."""
        self.message_shown = True
        self.last_title = title
        self.last_message = text
        self.last_buttons = buttons
        # Return the default button or Ok
        return defaultButton if defaultButton != QMessageBox.StandardButton.NoButton else QMessageBox.StandardButton.Ok
    
    def mock_question(self, parent, title, text, buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, defaultButton=QMessageBox.StandardButton.NoButton):
        """Mock QMessageBox.question."""
        self.message_shown = True
        self.last_title = title
        self.last_message = text
        self.last_buttons = buttons
        # Return the default button or Yes
        return defaultButton if defaultButton != QMessageBox.StandardButton.NoButton else QMessageBox.StandardButton.Yes
        
    def mock_input_dialog_text(self, parent, title, label, mode=0, text=""):
        """Mock QInputDialog.getText.
        
        mode=0 is equivalent to QInputDialog.Normal in older versions
        """
        self.message_shown = True
        self.last_title = title
        self.last_message = label
        # Return the predefined input result and True (for "OK" clicked)
        return self.input_result, True
        
    def mock_file_dialog(self, parent, title, directory, filter=""):
        """Mock QFileDialog.getOpenFileName."""
        self.message_shown = True
        self.last_title = title
        # Return the predefined file result and selected filter
        return self.file_result, filter
        
    def mock_dir_dialog(self, parent, title, directory):
        """Mock QFileDialog.getExistingDirectory."""
        self.message_shown = True
        self.last_title = title
        # Return the predefined directory result
        return self.dir_result


@contextmanager
def mock_dialogs():
    """Context manager to mock Qt dialogs during testing."""
    # Create the mock dialog handler
    handler = MockDialogHandler()
    
    # Save the original methods
    original_information = QMessageBox.information
    original_warning = QMessageBox.warning
    original_critical = QMessageBox.critical
    original_question = QMessageBox.question
    original_get_text = QInputDialog.getText
    original_get_file = QFileDialog.getOpenFileName
    original_get_dir = QFileDialog.getExistingDirectory
    
    try:
        # Replace with our mocks
        QMessageBox.information = handler.mock_information
        QMessageBox.warning = handler.mock_warning
        QMessageBox.critical = handler.mock_critical
        QMessageBox.question = handler.mock_question
        QInputDialog.getText = handler.mock_input_dialog_text
        QFileDialog.getOpenFileName = handler.mock_file_dialog
        QFileDialog.getExistingDirectory = handler.mock_dir_dialog
        
        # Yield the handler for the test to use
        yield handler
        
    finally:
        # Restore the original methods
        QMessageBox.information = original_information
        QMessageBox.warning = original_warning
        QMessageBox.critical = original_critical
        QMessageBox.question = original_question
        QInputDialog.getText = original_get_text
        QFileDialog.getOpenFileName = original_get_file
        QFileDialog.getExistingDirectory = original_get_dir
