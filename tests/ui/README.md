# UI Testing Guidelines

This directory contains UI tests for the application using PySide6 (Qt) and pytest-qt.

## Stable UI Testing Approach

We've adopted a strategic approach to UI testing to avoid common issues like access violations, crashes, and hanging tests:

1. **Focus on Critical Workflows**: We maintain a core set of smoke tests in `tests/ui/smoke_tests.py` covering essential user workflows
2. **Prefer Direct Method Calls**: Instead of simulating user input (clicks, key presses), we call widget methods directly
3. **Proper Widget Lifecycle Management**: Ensure all widgets are properly shown, hidden, and deleted
4. **Timeout Controls**: Use timeouts to prevent tests from hanging indefinitely

## Running UI Tests

```bash
# Run only the smoke tests (most stable)
pytest -m smoke

# Run all UI tests (including skipped tests)
pytest tests/ui -k "not skip"

# Run a specific UI test file
pytest tests/ui/smoke_tests.py
```

## Using the Qt Test Utilities

We've developed a set of utilities in `qt_test_utils.py` to make UI testing more stable:

### Safe Button Clicks

```python
from tests.ui.qt_test_utils import safe_click_button

# Instead of: qtbot.mouseClick(button, Qt.LeftButton)
safe_click_button(button)
```

### Safe Style Application

```python
from tests.ui.qt_test_utils import safely_apply_styles

# Map widgets to style names
widgets_and_styles = {
    button: 'button_primary',
    text_input: 'text_input'
}

# Apply styles safely with automatic cleanup
safely_apply_styles(qtbot, widgets_and_styles)
```

### Event Processing Control

```python
from tests.ui.qt_test_utils import process_events, wait_for

# Process pending events
process_events()

# Wait a short time (in milliseconds)
wait_for(50)
```

### Timeout Protection

```python
from tests.ui.qt_test_utils import with_timeout

# Run a function with timeout protection
result = with_timeout(my_function, timeout_ms=5000, arg1, arg2)
```

### Testing UI Styling Functions

```python
from tests.ui.qt_test_utils import safely_test_styling_function

def test_my_styling_function(qtbot):
    # Create a widget and apply styling safely
    widget, _ = safely_test_styling_function(qtbot, QLineEdit, apply_my_style, text="Initial text")
    
    # Check styling was applied correctly
    assert "border: 1px solid" in widget.styleSheet()
    assert widget.minimumHeight() == 28
```

### Using Mocks for UI Testing

For tests that are particularly prone to access violations, avoid using actual Qt widgets:

```python
from unittest.mock import MagicMock

def test_widget_styling(monkeypatch):
    # Create mock widget and layout
    mock_layout = MagicMock()
    mock_widget = MagicMock()
    mock_widget.layout.return_value = mock_layout
    
    # Apply styling function to mock
    apply_style_to_widget(mock_widget)
    
    # Verify correct methods were called
    mock_layout.setContentsMargins.assert_called_once_with(10, 10, 10, 10)
    mock_layout.setSpacing.assert_called_once_with(10)
```

This approach completely avoids Qt rendering and event loop issues.

## Test Fixtures

Use our standard fixture pattern to ensure proper widget lifecycle management:

```python
@pytest.fixture
def my_dialog(qtbot):
    """Create a dialog fixture with proper cleanup."""
    # Create the dialog
    dialog = MyDialog()
    qtbot.addWidget(dialog)
    
    # Show but don't wait for exposure
    dialog.show()
    process_events()
    
    yield dialog
    
    # Clean up resources
    dialog.hide()
    process_events()
    dialog.deleteLater()
    process_events()
```

## Marking Tests to Skip

To skip unstable tests during regular test runs but still maintain them for targeted testing:

```python
import sys
import pytest

# Skip in general UI testing to avoid access violations
pytestmark = [
    pytest.mark.skipif("ui" in sys.argv, reason="Skip for general UI test runs to avoid access violations")
]
```

## Smoke Tests

Our smoke tests focus on the most critical user workflows while minimizing UI interaction:
- Customer selection workflow 
- Cash drawer operations
- Basic sales flow

These tests verify that the UI components can be instantiated and key functions work, without extensive UI interaction that could cause test failures.