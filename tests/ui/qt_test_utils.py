import importlib.util
import os
import time
from PySide6.QtCore import QTimer, QEventLoop, Qt
from PySide6.QtWidgets import QApplication, QPushButton, QMainWindow, QMessageBox, QWidget, QInputDialog, QLabel

"""
Qt Test Utilities for Stable UI Testing

This module provides utility functions for stable UI testing that avoids access violations
and crashes that can occur with traditional UI testing approaches.

Key principles:
1. Prefer direct method/signal calls over simulated input (clicks, keypresses)
2. Ensure proper cleanup of Qt resources
3. Control event processing explicitly
4. Provide safer alternatives to common UI testing patterns
"""

def import_widget_safely(widget_path):
    try:
        spec = importlib.util.spec_from_file_location(
            os.path.basename(widget_path), 
            os.path.abspath(widget_path)
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except ImportError as e:
        raise RuntimeError(f"Failed to import widget from {widget_path}: {e}") from e

def process_events(qapp=None):
    """Process pending events for the QApplication instance."""
    if qapp is None:
        qapp = QApplication.instance()
    
    if qapp is not None:
        qapp.processEvents()

def wait_for(milliseconds):
    """Wait for the specified milliseconds."""
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec_()

def wait_until(condition_func, timeout=5000, interval=50):
    """Wait until a condition is true or timeout occurs.
    
    Args:
        condition_func: Function that returns True when condition is met
        timeout: Maximum time to wait in milliseconds
        interval: Check interval in milliseconds
        
    Returns:
        True if condition was met, False if timeout occurred
    """
    start_time = time.time()
    while (time.time() - start_time) * 1000 < timeout:
        if condition_func():
            return True
        wait_for(interval)
    return False

def get_widget_text(widget):
    """Get the text from a widget.
    
    This is a utility function that handles different widget types.
    
    Args:
        widget: The widget to get text from
        
    Returns:
        The text of the widget, or an empty string if no text is available
    """
    try:
        if hasattr(widget, 'text') and callable(widget.text):
            return widget.text()
        elif hasattr(widget, 'toPlainText') and callable(widget.toPlainText):
            return widget.toPlainText()
        elif hasattr(widget, 'currentText') and callable(widget.currentText):
            return widget.currentText()
        elif hasattr(widget, 'title') and callable(widget.title):
            return widget.title()
        elif hasattr(widget, 'placeholderText') and callable(widget.placeholderText):
            return widget.placeholderText()
        else:
            return ""
    except (RuntimeError, AttributeError):
        return ""

def set_widget_text(widget, text):
    """Set the text of a widget.
    
    This is a utility function that handles different widget types.
    
    Args:
        widget: The widget to set text on
        text: The text to set
    """
    try:
        if hasattr(widget, 'setText') and callable(widget.setText):
            widget.setText(text)
        elif hasattr(widget, 'setPlainText') and callable(widget.setPlainText):
            widget.setPlainText(text)
        elif hasattr(widget, 'setCurrentText') and callable(widget.setCurrentText):
            widget.setCurrentText(text)
        elif hasattr(widget, 'setTitle') and callable(widget.setTitle):
            widget.setTitle(text)
    except (RuntimeError, AttributeError):
        pass

def find_widget_by_text(parent, widget_type, text):
    """Find a widget of the given type with the specified text."""
    for widget in parent.findChildren(widget_type):
        if get_widget_text(widget) == text:
            return widget
    return None

def click_button_by_text(qtbot, parent, text):
    """Find and click a button with the given text."""
    button = find_widget_by_text(parent, QPushButton, text)
    if button:
        qtbot.mouseClick(button, Qt.LeftButton)
        return True
    return False

def safe_click_button(button):
    """Safely click a button using direct signals rather than mouse events.
    
    This is more reliable in tests and avoids access violations that can occur
    with mouse events.
    
    Args:
        button: The button to click
        
    Returns:
        True if the button was clicked, False otherwise
    """
    try:
        if button and hasattr(button, 'click') and callable(button.click):
            button.click()
            process_events()
            return True
    except (RuntimeError, AttributeError):
        pass
    return False

def safe_click_button_by_text(parent, text):
    """Find and safely click a button with the given text using direct signals.
    
    Args:
        parent: The parent widget to search for buttons
        text: The button text to search for
        
    Returns:
        True if the button was found and clicked, False otherwise
    """
    button = find_widget_by_text(parent, QPushButton, text)
    return safe_click_button(button)

def find_all_widgets(parent, widget_type):
    """Find all widgets of a given type in a parent widget."""
    return parent.findChildren(widget_type)

def find_widget_by_name(parent, widget_type, name):
    """Find a widget by its object name."""
    for widget in parent.findChildren(widget_type):
        if widget.objectName() == name:
            return widget
    return None

def find_button(parent, text=None, name=None):
    """Find a button by text or name."""
    if text:
        return find_widget_by_text(parent, QPushButton, text)
    elif name:
        return find_widget_by_name(parent, QPushButton, name)
    return None

def find_label(parent, text=None, name=None):
    """Find a label by text or name."""
    if text:
        return find_widget_by_text(parent, QLabel, text)
    elif name:
        return find_widget_by_name(parent, QLabel, name)
    return None

def wait_for_signal(signal, timeout=1000):
    """Wait for a Qt signal to be emitted."""
    loop = QEventLoop()
    signal.connect(loop.quit)
    QTimer.singleShot(timeout, loop.quit)
    loop.exec_()

def capture_dialogs(accept=True):
    """Context manager to capture dialogs."""
    class DialogCapture:
        def __init__(self, accept):
            self.accept = accept
            self.dialogs = []
            
        def __enter__(self):
            return self.dialogs
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
    
    return DialogCapture(accept)

def safe_setup_fixture(qtbot, widget_class, *args, **kwargs):
    """Safely set up a fixture for a Qt widget with proper cleanup.
    
    This is a template function for creating widget fixtures that handles
    proper initialization and cleanup to avoid access violations.
    
    Args:
        qtbot: The Qt testing robot
        widget_class: The widget class to instantiate
        *args: Positional arguments to pass to the widget constructor
        **kwargs: Keyword arguments to pass to the widget constructor
        
    Returns:
        The created widget instance
    """
    # Create the widget
    widget = widget_class(*args, **kwargs)
    qtbot.addWidget(widget)
    
    # Show the widget but don't wait for it to be exposed
    widget.show()
    process_events()
    
    yield widget
    
    # Clean up safely
    widget.hide()
    process_events()
    widget.deleteLater()
    process_events()

def simulate_combo_box_selection(combo_box, index):
    """Safely select an item in a combo box without using mouse events.
    
    Args:
        combo_box: The combo box widget
        index: The index to select
        
    Returns:
        True if selection was successful, False otherwise
    """
    try:
        if combo_box and hasattr(combo_box, 'setCurrentIndex') and callable(combo_box.setCurrentIndex):
            combo_box.setCurrentIndex(index)
            # Manually trigger the currentIndexChanged signal if needed
            if hasattr(combo_box, 'currentIndexChanged') and hasattr(combo_box.currentIndexChanged, 'emit'):
                combo_box.currentIndexChanged.emit(index)
            process_events()
            return True
    except (RuntimeError, AttributeError, IndexError):
        pass
    return False

def trigger_action(action):
    """Safely trigger a QAction without using mouse events.
    
    Args:
        action: The QAction to trigger
        
    Returns:
        True if action was triggered, False otherwise
    """
    try:
        if action and hasattr(action, 'trigger') and callable(action.trigger):
            action.trigger()
            process_events()
            return True
    except (RuntimeError, AttributeError):
        pass
    return False

def safely_apply_styles(qtbot, widgets_and_styles, show_widgets=True):
    """Safely apply styles to a collection of widgets, with proper cleanup.
    
    This utility handles the entire lifecycle of applying styles to widgets including:
    - Adding widgets to qtbot for proper event handling
    - Optionally showing widgets
    - Applying styles
    - Processing events after style changes
    - Handling cleanup
    
    Args:
        qtbot: The Qt testing robot
        widgets_and_styles: A dictionary mapping widgets to style names
        show_widgets: Whether to show the widgets (default: True)
        
    Example:
        safely_apply_styles(qtbot, {
            button: 'button_primary', 
            line_edit: 'text_input'
        })
    """
    widgets = list(widgets_and_styles.keys())
    
    # Add widgets to qtbot
    for widget in widgets:
        if widget:
            qtbot.addWidget(widget)
    
    try:
        # Show widgets if requested
        if show_widgets:
            for widget in widgets:
                if widget:
                    widget.show()
            process_events()
        
        # Apply styles
        for widget, style_name in widgets_and_styles.items():
            if widget and style_name:
                # Assume apply_style is a function that applies a style to a widget
                from ui.styles import apply_style
                apply_style(widget, style_name)
        
        # Process events after style changes
        process_events()
        
        # Wait briefly for styles to be applied
        wait_for(50)
        
        # Return the widgets for any additional processing
        return widgets
    
    finally:
        # Clean up widgets if they were shown
        if show_widgets:
            for widget in widgets:
                if widget:
                    widget.hide()
                    process_events()
                    widget.deleteLater()
                    process_events()

def with_timeout(func, timeout_ms=5000, *args, **kwargs):
    """Run a function with a timeout.
    
    If the function does not complete within the specified timeout,
    the function will be interrupted and False will be returned.
    
    Args:
        func: The function to run
        timeout_ms: The timeout in milliseconds
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        The result of the function if it completes within the timeout,
        or False if the timeout occurs
    """
    result = [False]
    completed = [False]
    
    def run_function():
        try:
            result[0] = func(*args, **kwargs)
            completed[0] = True
        except Exception as e:
            result[0] = e
            completed[0] = True
    
    # Create event loop for timeout
    loop = QEventLoop()
    
    # Start timer for timeout
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    
    # Create timer for function execution
    function_timer = QTimer()
    function_timer.setSingleShot(True)
    function_timer.timeout.connect(run_function)
    
    # Start timers
    timer.start(timeout_ms)
    function_timer.start(0)
    
    # Wait for either function completion or timeout
    while not completed[0] and timer.isActive():
        loop.exec_()
        if completed[0]:
            timer.stop()
            return result[0]
    
    return False

def safely_test_styling_function(qtbot, widget_class, style_function, **kwargs):
    """Safely test a styling function on a widget.
    
    This utility helps test UI styling functions in a safe way that prevents
    access violations and properly cleans up resources.
    
    NOTE: For tests that are highly unstable or prone to access violations,
    consider using mock objects instead of real Qt widgets. See the README
    section on "Using Mocks for UI Testing" for examples.
    
    Args:
        qtbot: The Qt testing robot
        widget_class: The widget class to instantiate and test
        style_function: The styling function to apply to the widget
        **kwargs: Additional keyword arguments to pass to the widget constructor
        
    Example:
        def test_my_style_function(qtbot):
            # Test that apply_my_style sets the correct properties
            widget, result = safely_test_styling_function(
                qtbot, QLineEdit, apply_my_style, text="Initial text"
            )
            
            # Check styling was applied
            assert widget.styleSheet() != ""
            assert "border: 1px solid" in widget.styleSheet()
    
    Returns:
        A tuple of (widget, result) where result is the return value of the style function
    """
    # Create the widget
    widget = widget_class(**kwargs)
    qtbot.addWidget(widget)
    result = None
    
    try:
        # Show the widget but don't wait for exposure
        widget.show()
        process_events()
        
        # Apply the style function and capture any return value
        result = style_function(widget)
        process_events()
        
        return widget, result
        
    finally:
        # Clean up resources
        widget.hide()
        process_events()
        widget.deleteLater()
        process_events()