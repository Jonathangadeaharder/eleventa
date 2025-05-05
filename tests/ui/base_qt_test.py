"""
Base Qt Test

This module provides the BaseQtTest class, which serves as the foundation
for all Qt UI tests in the application. It provides common setup, teardown,
and utility methods for testing Qt widgets and dialogs.
"""

import os
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

import pytest
from PySide6.QtCore import QObject, QTimer, Qt, QEventLoop
from PySide6.QtWidgets import (
    QApplication, QDialog, QLabel, QLineEdit, QPushButton, 
    QWidget, QMessageBox, QMainWindow
)

from .qt_test_utils import (
    process_events, wait_until, get_widget_text, set_widget_text,
    find_all_widgets, find_widget_by_name, find_button, find_label,
    wait_for_signal, capture_dialogs
)

T = TypeVar('T')

# Ensure project root is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

class BaseQtTest:
    """
    Base class for Qt UI tests providing common functionality.
    
    This class manages widget lifecycle, provides methods for finding and 
    interacting with widgets, and includes assertion methods for testing UI state.
    """
    
    @pytest.fixture(autouse=True)
    def setup_test(self, qapp, qtbot):
        """Set up the test with QApplication and qtbot."""
        self.app = qapp
        self.qtbot = qtbot
        self.setup_method()
    
    def setup_method(self):
        """
        Set up each test method by initializing a clean widget state.
        """
        self._widgets = []
        self._app = QApplication.instance() or QApplication([])
    
    def teardown_method(self):
        """
        Clean up after each test method by deleting widgets.
        """
        for widget in self._widgets:
            if widget and not widget.isHidden():
                widget.hide()
                widget.deleteLater()
        
        process_events(100)  # Process events to complete deletion
        self._widgets = []
    
    def add_widget(self, widget: QWidget) -> QWidget:
        """
        Add a widget to be managed by the test class.
        
        Args:
            widget: The widget to add and manage
            
        Returns:
            The same widget for chaining
        """
        self._widgets.append(widget)
        return widget
    
    def process_events(self):
        """Process Qt events."""
        process_events(self.app)
    
    def wait_until(self, condition: Callable[[], bool], timeout: int = 5000, interval: int = 50) -> bool:
        """
        Wait until a condition is true or timeout expires.
        
        Args:
            condition: Function that returns True when condition is met
            timeout: Maximum time to wait in milliseconds
            interval: Check interval in milliseconds
            
        Returns:
            True if condition was met, False if timeout occurred
        """
        return wait_until(condition, timeout, interval)
    
    def find_widgets(self, parent: QWidget, widget_type: Type[T]) -> List[T]:
        """
        Find all widgets of a specific type within a parent widget.
        
        Args:
            parent: The parent widget to search within
            widget_type: The type of widget to find
            
        Returns:
            List of widgets of the specified type
        """
        return find_all_widgets(parent, widget_type)
    
    def find_widget_by_name(self, parent: QWidget, widget_type: Type[T], name: str) -> Optional[T]:
        """
        Find a widget by its object name.
        
        Args:
            parent: The parent widget to search within
            widget_type: The type of widget to find
            name: The object name to search for
            
        Returns:
            The found widget or None
        """
        return find_widget_by_name(parent, widget_type, name)
    
    def find_button(self, parent: QWidget, text: Optional[str] = None, name: Optional[str] = None) -> Optional[QPushButton]:
        """
        Find a button by text or name.
        
        Args:
            parent: The parent widget to search within
            text: Button text to search for
            name: Button object name to search for
            
        Returns:
            The found button or None
        """
        return find_button(parent, text, name)
    
    def find_label(self, parent: QWidget, text: Optional[str] = None, name: Optional[str] = None) -> Optional[QLabel]:
        """
        Find a label by text or name.
        
        Args:
            parent: The parent widget to search within
            text: Label text to search for
            name: Label object name to search for
            
        Returns:
            The found label or None
        """
        return find_label(parent, text, name)
    
    def click_button(self, button):
        """Click a button."""
        if button:
            self.qtbot.mouseClick(button, Qt.LeftButton)
            self.process_events()
            return True
        return False
    
    def set_text(self, widget: QWidget, text: str) -> None:
        """
        Set the text of a widget in a type-appropriate way.
        
        Args:
            widget: The widget to set text on
            text: The text to set
        """
        set_widget_text(widget, text)
        self.process_events()
    
    def get_text(self, widget: QWidget) -> str:
        """
        Get the text from a widget in a type-appropriate way.
        
        Args:
            widget: The widget to get text from
            
        Returns:
            The widget's text content
        """
        return get_widget_text(widget)
    
    def wait_for(self, milliseconds: int) -> None:
        """
        Wait for a specified number of milliseconds.
        
        Args:
            milliseconds: Time to wait, in milliseconds
        """
        start_time = time.time()
        while (time.time() - start_time) * 1000 < milliseconds:
            self.process_events()
    
    def wait_for_signal(self, signal, timeout: int = 1000):
        """
        Wait for a signal to be emitted.
        
        Args:
            signal: The Qt signal to wait for
            timeout: Maximum time to wait in milliseconds
            
        Returns:
            A context manager for waiting on the signal
        """
        return wait_for_signal(signal, timeout)
    
    def capture_dialogs(self, accept: bool = True):
        """
        Capture and automatically handle dialogs.
        
        Args:
            accept: Whether to accept or reject the dialog
            
        Returns:
            A context manager that yields captured dialogs
        """
        return capture_dialogs(accept)
    
    # Assertion Methods
    
    def assert_visible(self, widget: QWidget) -> None:
        """
        Assert that a widget is visible.
        
        Args:
            widget: The widget to check
            
        Raises:
            AssertionError: If the widget is not visible
        """
        assert widget.isVisible(), f"Widget {widget} should be visible"
    
    def assert_hidden(self, widget: QWidget) -> None:
        """
        Assert that a widget is hidden.
        
        Args:
            widget: The widget to check
            
        Raises:
            AssertionError: If the widget is visible
        """
        assert not widget.isVisible(), f"Widget {widget} should be hidden"
    
    def assert_enabled(self, widget: QWidget) -> None:
        """
        Assert that a widget is enabled.
        
        Args:
            widget: The widget to check
            
        Raises:
            AssertionError: If the widget is disabled
        """
        assert widget.isEnabled(), f"Widget {widget} should be enabled"
    
    def assert_disabled(self, widget: QWidget) -> None:
        """
        Assert that a widget is disabled.
        
        Args:
            widget: The widget to check
            
        Raises:
            AssertionError: If the widget is enabled
        """
        assert not widget.isEnabled(), f"Widget {widget} should be disabled"
    
    def assert_text_equals(self, widget: QWidget, expected_text: str) -> None:
        """
        Assert that a widget's text equals the expected text.
        
        Args:
            widget: The widget to check
            expected_text: The expected text
            
        Raises:
            AssertionError: If the widget's text doesn't match
        """
        actual_text = self.get_text(widget)
        assert actual_text == expected_text, f"Widget text '{actual_text}' does not match expected '{expected_text}'"
    
    def assert_text_contains(self, widget: QWidget, substring: str) -> None:
        """
        Assert that a widget's text contains a substring.
        
        Args:
            widget: The widget to check
            substring: The substring to look for
            
        Raises:
            AssertionError: If the widget's text doesn't contain the substring
        """
        actual_text = self.get_text(widget)
        assert substring in actual_text, f"Widget text '{actual_text}' does not contain '{substring}'"
    
    def assert_dialog_shown(self, dialog_type: Type[QDialog] = QDialog) -> None:
        """
        Assert that a dialog was shown.
        
        Args:
            dialog_type: The expected dialog type
            
        Raises:
            AssertionError: If no dialog was shown
        """
        with self.capture_dialogs() as dialogs:
            # Force a dummy action to ensure the dialog would have been shown
            self.process_events()
            assert len(dialogs) > 0, f"Expected a dialog of type {dialog_type.__name__} to be shown, but none was"
            assert isinstance(dialogs[0], dialog_type), \
                f"Expected a dialog of type {dialog_type.__name__}, got {type(dialogs[0]).__name__}"
    
    def try_except_dialog(self, action: Callable, accept: bool = True) -> List[QDialog]:
        """
        Execute an action and capture any dialogs it shows.
        
        Args:
            action: The action to execute
            accept: Whether to accept or reject the dialog
            
        Returns:
            List of captured dialogs
        """
        with self.capture_dialogs(accept=accept) as dialogs:
            action()
            self.process_events(100)  # Give time for dialogs to appear
            return dialogs

    def find_button_by_text(self, parent, text):
        """Find a button with the given text."""
        for button in parent.findChildren(QPushButton):
            if button.text() == text:
                return button
        return None
        
    def click_button_by_text(self, parent, text):
        """Find and click a button with the given text."""
        button = self.find_button_by_text(parent, text)
        return self.click_button(button) 