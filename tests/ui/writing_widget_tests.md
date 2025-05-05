# Writing UI Tests for PyQt6 Widgets

This guide explains how to write effective tests for PyQt6 widgets in the Eleventa application.

## Core Principles

1. **Isolation**: Each test should test one widget or component in isolation
2. **Independence**: Tests should not depend on the state of other tests
3. **Reproducibility**: Tests should produce the same results on each run
4. **Simplicity**: Keep tests focused and simple

## Test Structure

### Setting Up Test Classes

All UI tests should inherit from `BaseQtTest`, which provides utility methods for testing Qt widgets:

```python
from tests.ui.qt_test_utils import BaseQtTest

class TestMyWidget(BaseQtTest):
    def setup_method(self):
        # Create your widget
        self.widget = MyWidget()
        # Register it for cleanup
        self.add_widget(self.widget)
        # Show the widget
        self.widget.show()
        # Process events
        self.process_events()
```

### Basic Test Method Structure

Each test method should:
1. Find or access the widgets to test
2. Perform actions on those widgets
3. Verify the results

```python
def test_button_click(self):
    # Find button
    button = self.find_widget("buttonObjectName", QPushButton)
    
    # Perform action
    self.click_button(button)
    self.process_events()
    
    # Verify results
    label = self.find_widget("labelObjectName", QLabel)
    assert label.text() == "Expected Text"
```

## Widget Identification

Widgets must have unique object names for testing. Always set the `objectName` property:

```python
# In your widget's __init__ method:
self.button = QPushButton("Click Me")
self.button.setObjectName("myButton")  # Important for testing
```

## Common Testing Operations

### Finding Widgets

```python
# Find by object name and type
button = self.find_widget("buttonName", QPushButton)

# Find by type only (returns the first matching widget)
label = self.find_widget_by_type(self.widget, QLabel)

# Find all widgets of a type
all_buttons = self.find_widgets_by_type(self.widget, QPushButton)
```

### Widget Interaction

```python
# Click a button
self.click_button(button)

# Enter text in a line edit
self.enter_text(line_edit, "sample text")

# Select item in combo box
self.select_combo_item(combo_box, "Item Text")
self.select_combo_index(combo_box, 2)

# Check/uncheck checkbox
self.set_checkbox_state(checkbox, True)  # Check
self.set_checkbox_state(checkbox, False)  # Uncheck
```

### Assertions

```python
# Assert text equality
assert label.text() == "Expected Text"

# Assert visibility
assert button.isVisible()
assert not hidden_widget.isVisible()

# Assert enabled/disabled state
assert button.isEnabled()
assert not disabled_button.isEnabled()

# Assert checkbox state
assert checkbox.isChecked()
```

## Event Processing

Always process events after actions that might trigger async behavior:

```python
# Click a button
self.click_button(button)
# Process events to allow signals to be handled
self.process_events()
```

## Testing Signals

To test signal emission:

```python
# Connect a counter to track signal emissions
counter = 0
def signal_handler():
    nonlocal counter
    counter += 1

widget.some_signal.connect(signal_handler)

# Perform action that should emit signal
self.click_button(button)
self.process_events()

# Verify signal was emitted
assert counter == 1
```

## Writing Testable Widgets

1. **Use object names**: Give meaningful object names to all widgets
2. **Keep UI and logic separate**: Follow MVP/MVVM patterns
3. **Make widgets composable**: Easier to test in isolation
4. **Use signals and slots**: Makes behavior testable
5. **Avoid global state**: Increases test reliability

## Debugging UI Tests

If your tests are failing:

1. **Add print statements**: Use `print()` to see widget state
2. **Use QTest.qWait()**: Add delays to see UI changes
3. **Check object names**: Verify object names match what you're searching for
4. **Check widget hierarchy**: Make sure widgets are created in the expected parent

## Example

See `example_button_test.py` for a complete working example of PyQt6 widget tests.

## Common Pitfalls

1. **Not processing events**: Always call `self.process_events()` after UI changes
2. **Widget not found**: Check object names and widget hierarchy
3. **Event loop issues**: Use `wait_for_signal()` for async operations
4. **State leakage**: Ensure widgets are properly cleaned up between tests 