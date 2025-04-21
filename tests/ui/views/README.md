# UI Views Testing Guide

This directory contains tests for UI view components of the application. 

## Testing Approaches

Different views have different complexity levels and may require different testing approaches:

### Standard Method (for simple views)

Most view components can be tested using the standard `pytest-qt` approach with the `qtbot` fixture:

```python
def test_simple_view(qtbot):
    # Create the view
    view = SimpleView()
    qtbot.addWidget(view)
    
    # Test interactions
    qtbot.mouseClick(view.some_button, Qt.LeftButton)
    
    # Verify results
    assert view.some_label.text() == "Expected Text"
```

### Complex Method (for views with dialog dependencies)

Some views like `CashDrawerView` have complex dependencies and initialization requirements that cause tests to hang when using the standard approach. For these views, use the pattern demonstrated in `test_cash_drawer_minimal.py`:

1. Initialize QApplication at module level before importing the view
2. Aggressively patch all dialog classes and QMessageBox
3. Keep tests minimal and focused on core functionality
4. Use short timeouts and aggressive cleanup

Example:
```python
# Initialize QApplication first
app = QApplication.instance() or QApplication(sys.argv)

# Apply patches before importing
patches = [
    patch('ui.dialogs.some_dialog.SomeDialog', MagicMock()),
    patch('ui.views.complex_view.QMessageBox', MagicMock()),
]
for p in patches:
    p.start()

# Then import the view
from ui.views.complex_view import ComplexView

def test_complex_view():
    # Create and test the view
    view = ComplexView()
    assert view is not None
    
    # Cleanup
    view.close()
    view.deleteLater()
    QApplication.processEvents()
    
    # Stop patches
    for p in patches:
        p.stop()
```

## Troubleshooting Test Hangs

If a test is hanging, consider:

1. Is the test trying to create QWidgets before a QApplication exists?
2. Are there dialog classes being instantiated that aren't properly mocked?
3. Are there message boxes or other modal dialogs blocking the test?
4. Is there an event loop that's not exiting properly?

See `test_cash_drawer_minimal.py` and `debug_cash_drawer_view.py` for examples of troubleshooting these issues.

## Coverage Targets

The project aims for ≥80% test coverage of UI views. Some complex views may be difficult to test comprehensively, but even minimal tests (like for CashDrawerView) can achieve significant coverage.

## Resources

- [pytest-qt Documentation](https://pytest-qt.readthedocs.io/en/latest/)
- [Qt Testing Best Practices](https://doc.qt.io/qt-5/qtest-overview.html) 