import importlib.util
import os
import time
from PySide6.QtCore import QTimer, QEventLoop, Qt
from PySide6.QtWidgets import QApplication, QPushButton, QMainWindow, QMessageBox, QWidget, QInputDialog, QLabel

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