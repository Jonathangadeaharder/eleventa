# Stable UI Testing Guide

This guide outlines best practices for writing stable UI tests that avoid access violations and crashes in Qt applications.

## Key Principles

1. **Prefer direct method and signal calls over simulated input**
   - Call button's `click()` or emit `clicked` signal instead of `qtbot.mouseClick()`
   - Set widget properties directly rather than simulating user input

2. **Proper Widget Lifecycle Management**
   - Add widgets to `qtbot` to ensure proper cleanup
   - Properly hide/close widgets before deletion
   - Process events after state changes

3. **Minimize UI Interaction Depth**
   - Focus on testing key functionality over comprehensive UI testing
   - Test smallest possible units at a time
   - Mock complex dependencies

4. **Safe Setup and Teardown**
   - Create robust fixtures that safely initialize and clean up widgets
   - Use proper error handling to prevent test cascade failures

## Safer Alternatives to Common UI Testing Patterns

| Unstable Pattern | Stable Alternative |
|------------------|-------------------|
| `qtbot.mouseClick(button, Qt.LeftButton)` | `safe_click_button(button)` or `button.clicked.emit()` |
| `qtbot.keyClick(widget, Qt.Key_Enter)` | Direct method calls like `widget.submit()` |
| `qtbot.waitExposed(widget)` | `process_events()` without waiting for exposure |
| Deep widget hierarchy inspection | Mock dependencies and verify method calls |
| Testing full UI flows | Break down into smaller, targeted tests |

## Example: Stable Button Click Testing

```python
# Unstable approach (can cause access violations)
def test_unstable_button_click(qtbot):
    dialog = MyDialog()
    qtbot.addWidget(dialog)
    dialog.show()
    
    # May cause access violations
    qtbot.mouseClick(dialog.submit_button, Qt.LeftButton)
    
    assert dialog.result() == QDialog.Accepted

# Stable approach
def test_stable_button_click(qtbot):
    dialog = MyDialog()
    qtbot.addWidget(dialog)
    dialog.show()
    process_events()
    
    # Directly emit the signal without mouse events
    dialog.submit_button.clicked.emit()
    process_events()
    
    assert dialog.result() == QDialog.Accepted
```

## Using the Safe Testing Utilities

Our `qt_test_utils.py` module provides several functions for safer UI testing:

```python
from tests.ui.qt_test_utils import (
    process_events,
    safe_click_button,
    set_widget_text,
    safe_setup_fixture
)

def test_example_with_utilities(qtbot):
    # Create and set up widget
    dialog = MyDialog()
    qtbot.addWidget(dialog)
    dialog.show()
    process_events()
    
    # Set text directly instead of typing
    set_widget_text(dialog.name_input, "Test User")
    
    # Click button safely
    safe_click_button(dialog.submit_button)
    
    # Verify result
    assert dialog.submitted is True
```

## Test Isolation with Skip Markers

For unstable tests that you still want to maintain but exclude from automated runs:

```python
# Skip in general UI testing to avoid access violations
pytestmark = [
    pytest.mark.skipif("ui" in sys.argv, reason="Skip for general UI test runs to avoid access violations")
]
```

This allows you to run these tests individually when needed but skip them during general test runs.

## Creating Stable UI Test Fixtures

```python
@pytest.fixture
def stable_dialog(qtbot):
    """Create a dialog with safe setup and teardown."""
    # Create dialog with mocked dependencies
    dialog = MyDialog(mock_service)
    qtbot.addWidget(dialog)
    
    # Show but don't wait for exposure
    dialog.show()
    process_events()
    
    yield dialog
    
    # Clean up safely
    dialog.hide()
    process_events()
    dialog.deleteLater()
    process_events()
```

## Running UI Tests Safely

### Best Practices

1. Run smoke tests before running comprehensive UI tests
2. Run unstable UI tests in isolation
3. Use the appropriate level of testing (unit, integration, ui) for each feature
4. Prefer targeted tests over broad test suites

### Commands

```bash
# Run only the smoke tests (most stable)
python -m pytest -m smoke

# Run a specific UI test file (when needed)
python -m pytest tests/ui/dialogs/specific_test.py

# Run all non-UI tests (for CI/CD)
python -m pytest -k "not ui"
``` 