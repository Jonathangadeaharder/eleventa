"""
Base module for Qt testing.
"""
import os
import sys
import pytest
from unittest.mock import MagicMock
from contextlib import contextmanager
import time

# Make sure project root is in the path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import Qt classes directly to avoid import issues
from PySide6.QtCore import Qt, QTimer, QEventLoop
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QDialog, QWidget, QPushButton, 
    QTableView, QLineEdit, QMessageBox
)

# Import local test utilities
from .qt_test_utils import process_events, wait_for

class BaseQtTest:
    """Base class for Qt tests."""
    
    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        """Set up test with qtbot."""
        self.qtbot = qtbot
        # Make sure we have an application instance
        self.app = QApplication.instance()
        if not self.app:
            self.app = QApplication([])
        # Initialize widgets list
        self._widgets = []
    
    def teardown_method(self):
        """Clean up widgets after each test."""
        for widget in self._widgets:
            if widget and not widget.isHidden():
                widget.hide()
                widget.deleteLater()
        
        self.process_events()
        
    def add_widget(self, widget):
        """Add a widget to be managed by the test class."""
        self._widgets.append(widget)
        return widget
            
    def process_events(self):
        """Process application events."""
        process_events(self.app)
        
    def wait(self, ms):
        """Wait for the specified milliseconds."""
        wait_for(ms)
    
    def wait_for(self, condition_func, timeout=5000, interval=50):
        """Wait for a condition to be true, with timeout."""
        start = time.time()
        while (time.time() - start) * 1000 < timeout:
            if condition_func():
                return True
            self.process_events()
            time.sleep(interval / 1000)
        return False
        
    def find_button(self, parent, text):
        """Find a button with the given text."""
        for btn in parent.findChildren(QPushButton):
            if btn.text() == text:
                return btn
        return None
        
    def click_button(self, button):
        """Click a button."""
        if button:
            self.qtbot.mouseClick(button, Qt.LeftButton)
            self.process_events()
            return True
        return False
    
    @contextmanager
    def wait_signal(self, signal, timeout=1000):
        """Wait for a Qt signal to be emitted."""
        loop = QEventLoop()
        signal.connect(loop.quit)
        
        yield
        
        # Start a timer to end the loop if signal is not received
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        timer.start(timeout)
        
        # Wait for signal or timeout
        loop.exec()
        
        # Clean up
        timer.stop()
        if hasattr(signal, "disconnect"):
            try:
                signal.disconnect(loop.quit)
            except:
                pass
    
    def capture_exceptions(self, func, *args, **kwargs):
        """Capture exceptions from a function execution.
        
        Returns:
            tuple: (result, exception) - result is None if an exception occurred
        """
        try:
            result = func(*args, **kwargs)
            return result, None
        except Exception as e:
            return None, e 