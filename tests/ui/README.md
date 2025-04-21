# UI Testing Strategy

This directory contains tests for UI components in the application. Testing Qt-based UI components presents unique challenges, particularly when dealing with complex widgets, dialogs, and event loop interactions.

## Challenges in UI Testing

1. **Qt Initialization**: Qt widgets require proper QApplication initialization before they can be used.
2. **Event Loop Handling**: Tests involving the Qt event loop may hang indefinitely.
3. **Dialog Dependencies**: UI components that create dialogs can cause tests to block.
4. **Resource Management**: Improper cleanup of Qt resources can cause failures in subsequent tests.
5. **Signal/Slot Connections**: Testing asynchronous behavior from signals and slots can be tricky.

## Testing Approaches

We've developed several approaches to handle these challenges, from least to most aggressive:

### 1. Standard pytest-qt (for simple components)
- Use the `qtbot` fixture from pytest-qt
- Suitable for simple components without complex dialog dependencies
- Example: `tests/ui/styles/test_styles.py`

### 2. Timeouts and Aggressive Cleanup
- Add explicit timeouts to prevent hanging
- Use aggressive cleanup with multiple `processEvents()` calls
- Example: `tests/ui/views/test_view_base.py`

### 3. Standalone Test Scripts
- For components that consistently hang with pytest
- Implement a forceful kill switch with threading
- Patch all Qt dependencies before import
- Example: `tests/ui/views/direct_cash_drawer_test.py`

## Best Practices

1. **Always Create QApplication First**
   ```python
   from PySide6.QtWidgets import QApplication
   app = QApplication.instance() or QApplication(sys.argv)
   # Now safe to import UI components
   ```

2. **Use Appropriate Timeouts**
   ```python
   # Module level timeout
   pytestmark = pytest.mark.timeout(5)
   
   # Function level timeout
   @pytest.mark.timeout(1)
   def test_something():
      pass
   ```

3. **Process Events Safely**
   ```python
   def process_events_with_timeout(max_time=0.5):
       start = time.time()
       while time.time() - start < max_time:
           QApplication.processEvents()
           time.sleep(0.01)
   ```

4. **Aggressive Cleanup**
   ```python
   try:
       if view:
           view.close()
           view.deleteLater()
           process_events_with_timeout(0.1)
   except Exception as e:
       print(f"Error during cleanup: {e}")
   ```

5. **Mock Dialogs Before Import**
   ```python
   patches = [
       patch('ui.dialogs.SomeDialog', MagicMock()),
       patch('PySide6.QtWidgets.QMessageBox', MagicMock()),
   ]
   for p in patches:
       p.start()
   # Now safe to import
   ```

## Test Types

1. **Style Tests**: Testing styles, colors, and appearance
2. **View Tests**: Testing the UI components that display data
3. **Dialog Tests**: Testing modal dialogs and forms
4. **Event Tests**: Testing user interaction events

## Coverage Goals

- UI components should aim for at least 85% coverage
- Focus on testing critical business logic and user workflows
- Document cases where coverage cannot be improved due to Qt limitations

## Further Documentation

For more specific testing challenges and solutions:
- [Cash Drawer Testing Challenges](./views/cash_drawer_testing_challenges.md) 