# qt_test_utils Module Documentation

The `qt_test_utils` module provides the foundation for testing Qt UI components in the eleventa application. This document explains the implementation details and design patterns used in the module.

## BaseQtTest Class

### Overview

The `BaseQtTest` class is designed as a base class for all Qt UI tests. It handles:

- Widget lifecycle management
- Event processing
- Widget finding and interaction
- Common assertions for UI testing
- Dialog capture functionality

### Implementation Details

#### Widget Management

```python
def setup_method(self, method):
    """Initialize test environment for each test method."""
    self._widgets = []
    self._app = QApplication.instance() or QApplication([])
    self._captured_dialogs = []

def add_widget(self, widget):
    """Add a widget to be cleaned up during teardown."""
    self._widgets.append(widget)
    return widget

def teardown_method(self, method):
    """Clean up after each test method."""
    for widget in self._widgets:
        widget.close()
        widget.deleteLater()
    self._widgets.clear()
    self.process_events()
```

The `setup_method` and `teardown_method` follow pytest's fixture pattern. `setup_method` initializes the Qt application instance if needed, while `teardown_method` ensures all widgets are properly closed and deleted.

#### Event Processing

```python
def process_events(self, ms=10):
    """Process Qt events for the specified time."""
    start = time.time()
    while time.time() - start < ms / 1000:
        QApplication.instance().processEvents()
```

This method is crucial for Qt testing as it ensures events are processed, allowing UI updates to occur.

#### Finding Widgets

Widget finding uses recursive search through the widget tree:

```python
def find_widgets(self, parent, widget_type):
    """Find all widgets of a specific type in the parent widget."""
    return parent.findChildren(widget_type)

def find_widget_by_name(self, parent, widget_type, name):
    """Find a widget of a specific type by its object name."""
    widgets = self.find_widgets(parent, widget_type)
    for widget in widgets:
        if widget.objectName() == name:
            return widget
    return None
```

Specialized finders are provided for common widgets:

```python
def find_button(self, parent, text=None, name=None):
    """Find a button with the specified text or name."""
    # Implementation details
    
def find_label(self, parent, text=None, name=None):
    """Find a label with the specified text or name."""
    # Implementation details
```

#### Interacting with Widgets

Methods are provided for common interactions:

```python
def click_button(self, parent, text=None, name=None):
    """Click a button identified by text or name."""
    button = self.find_button(parent, text, name)
    if button:
        button.click()
    else:
        raise ValueError(f"Button with text={text} or name={name} not found")
    self.process_events()

def set_text(self, widget, text):
    """Set the text of a text input widget."""
    widget.setText(text)
    self.process_events()
```

#### Assertions

Assertion methods provide clear error messages:

```python
def assert_visible(self, widget):
    """Assert that a widget is visible."""
    assert widget.isVisible(), f"Widget {widget} is not visible"

def assert_text_equals(self, widget, expected_text):
    """Assert that a widget's text equals the expected text."""
    if hasattr(widget, 'text'):
        actual_text = widget.text()
    elif hasattr(widget, 'toPlainText'):
        actual_text = widget.toPlainText()
    else:
        raise ValueError(f"Widget {widget} has no text property")
    
    assert actual_text == expected_text, f"Expected text '{expected_text}', got '{actual_text}'"
```

#### Dialog Capture

Dialog capture uses a context manager and event filter:

```python
@contextmanager
def capture_dialogs(self):
    """Context manager to capture dialogs shown during the enclosed code."""
    self._captured_dialogs = []
    
    class DialogFilter(QObject):
        def eventFilter(self_filter, obj, event):
            if event.type() == QEvent.Type.Show and isinstance(obj, QDialog):
                self._captured_dialogs.append(obj)
            return False
    
    dialog_filter = DialogFilter()
    QApplication.instance().installEventFilter(dialog_filter)
    
    try:
        yield
    finally:
        QApplication.instance().removeEventFilter(dialog_filter)
```

#### Waiting and Signals

Signal waiting is implemented using Qt's signal-slot mechanism:

```python
def wait_for_signal(self, signal, timeout_ms=1000):
    """Wait for a signal to be emitted."""
    loop = QEventLoop()
    timer = QTimer()
    timer.setSingleShot(True)
    
    # Connect signal to quit the event loop
    signal.connect(loop.quit)
    
    # Connect timer timeout to quit the event loop
    timer.timeout.connect(loop.quit)
    
    # Start the timer
    timer.start(timeout_ms)
    
    # Run the event loop until the signal is emitted or timeout
    loop.exec()
    
    # Return True if the timer is still active (signal was emitted)
    return timer.isActive()
```

## Design Patterns

### Builder Pattern

The `BaseQtTest` class employs a builder-like pattern by providing methods to construct and manipulate widgets in a fluent interface.

### Facade Pattern

The module presents a simplified interface to the complex Qt testing functionality, hiding implementation details.

### Observer Pattern

Dialog capturing and signal waiting implement the observer pattern to detect UI changes.

## Usage Guidelines

1. Always inherit from `BaseQtTest` for Qt UI tests
2. Follow the setup/teardown pattern by calling the super methods
3. Add all widgets to the widget list using `add_widget()`
4. Use the provided assertion methods for clearer error messages
5. Process events after UI operations using `process_events()`

## Integration with Pytest

The `BaseQtTest` class is designed to work with pytest. Tests can be written as regular pytest test classes:

```python
class TestMyDialog(BaseQtTest):
    def setup_method(self, method):
        super().setup_method(method)
        self.dialog = MyDialog()
        self.add_widget(self.dialog)
        self.dialog.show()
        self.process_events()
    
    def test_dialog_ok(self):
        self.click_button(self.dialog, text="OK")
        assert self.dialog.result() == QDialog.DialogCode.Accepted
```

## Thread Safety

The Qt UI tests should be run in the main thread as Qt widgets are not thread-safe. The module does not provide thread synchronization as it's expected to be used in a single-threaded testing environment. 