# Qt UI Testing Migration Plan

This document outlines the steps needed to transition all UI tests to use the new testing helpers and patterns established with `test_filter_dropdowns.py`.

## Migration Goals

- Improve test reliability
- Fix import issues with UI components
- Add proper mocking for dependencies
- Standardize test patterns
- Increase test coverage
- Make tests more maintainable

## Migration Tasks

### 1. Environment Setup

- [x] Create `test_filter_dropdowns.py` as a reference implementation
- [ ] Update `ui/__init__.py` and `ui/widgets/__init__.py` to handle imports properly
- [ ] Add unit test dependencies to `requirements-dev.txt`
- [ ] Document the migration approach in README

### 2. Utility Improvements

- [ ] Update `conftest.py` to handle proper import paths
- [ ] Fix the fixture implementation to work with direct imports
- [ ] Create utility functions for common mocking patterns
- [ ] Add helper methods for widget imports with proper error handling
- [ ] Implement robust module loading that works consistently in tests

### 3. Mock Implementation

- [ ] Create a standard mock factory for UI utilities
- [ ] Build a collection of common mock implementations for:
  - [ ] Dialog handling
  - [ ] Icons and resources
  - [ ] Styling utilities
  - [ ] Database connections used in UI
- [ ] Document the mocking approach with examples

### 4. Test Migration

#### Core Components

- [ ] Migrate tests for basic widgets first:
  - [ ] Button tests
  - [ ] Label tests
  - [ ] Input field tests
- [ ] Update dialog tests to use new helpers
- [ ] Convert view tests to use the new pattern

#### Specific Files to Migrate

- [ ] `test_login.py`
- [ ] `test_login_dialog.py`
- [ ] `test_product_dialog.py`
- [ ] `test_add_inventory_dialog.py`
- [ ] `test_department_dialog.py`
- [ ] `test_ui_noninteractive_components.py`
- [ ] `test_sales_view.py`
- [ ] `test_products_view.py`
- [ ] `test_minimal_widget.py`
- [ ] `test_keyboard_shortcuts.py`
- [ ] `test_corte_view.py`
- [ ] `test_table_models.py`
- [ ] `test_customers_view.py`

### 5. Test Coverage Improvements

- [ ] Identify components with low coverage
- [ ] Add tests for edge cases that weren't previously covered
- [ ] Implement signal/slot testing more thoroughly
- [ ] Add tests for asynchronous UI behaviors

### 6. Documentation and Standards

- [ ] Update `writing_widget_tests.md` with new patterns
- [ ] Create an example directory with reference implementations
- [ ] Document common pitfalls and solutions
- [ ] Add comments to test files explaining the patterns used

### 7. CI/CD Integration

- [ ] Update GitHub workflow to run UI tests
- [ ] Configure X virtual framebuffer for headless testing
- [ ] Add test coverage reporting to CI pipeline
- [ ] Set up test failure notifications

## Implementation Strategy

### Phase 1: Infrastructure (Weeks 1-2)

Focus on setting up the foundation:
- Environment setup
- Utility improvements 
- Mock implementation

### Phase 2: Core Migration (Weeks 3-4)

Migrate the most critical tests:
- Simple widgets
- Core dialogs
- Main views

### Phase 3: Complete Migration (Weeks 5-6)

Finish migration and improve coverage:
- Remaining tests
- Coverage improvements
- Documentation

### Phase 4: CI/CD and Finalization (Week 7)

- CI/CD integration
- Final testing and verification
- Team training

## Testing Approach

For each migrated test:

1. Run the original test to verify functionality
2. Create a new version using the new pattern
3. Run the new test to verify equivalent behavior
4. Replace the old test once the new one is verified

## Common Patterns to Apply

### Import Pattern

```python
# Import this way for testing
import importlib.util
from unittest.mock import MagicMock

# Mock dependencies
sys.modules['ui.utils'] = MagicMock()

# Import the module directly
spec = importlib.util.spec_from_file_location(
    "module_name", 
    os.path.abspath("path/to/module.py")
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Get classes from the module
ClassName = module.ClassName
```

### Widget Test Template

```python
class TestSomeWidget(BaseQtTest):
    def setup_method(self, method):
        super().setup_method(method)
        self.widget = SomeWidget()
        self.add_widget(self.widget)
        self.widget.show()
        self.process_events()
    
    def test_initial_state(self):
        # Test initial state
        
    def test_interactions(self):
        # Test interactions
        
    def test_signals(self):
        # Test signals
```

## Utility Functions to Implement

To facilitate the migration, we should implement these utility functions:

### 1. Module Import Utilities

```python
def import_ui_module(module_path, dependencies_to_mock=None):
    """
    Import a UI module with proper dependency mocking.
    
    Args:
        module_path: Path to the module relative to project root
        dependencies_to_mock: Dict of dependencies to mock {module_name: mock_obj}
    
    Returns:
        The imported module
    """
    # Implementation
```

### 2. Mock Factory Functions

```python
def create_style_mocks():
    """Create standard mocks for styling functions."""
    
def create_dialog_mocks():
    """Create standard mocks for dialogs."""
    
def create_icon_mocks():
    """Create standard mocks for icons and resources."""
```

### 3. Signal Testing Helpers

```python
def capture_signal_emissions(signal, callback=None):
    """
    Capture all emissions of a signal.
    
    Args:
        signal: The Qt signal to capture
        callback: Optional callback to run when signal is emitted
        
    Returns:
        List of captured emissions (args, kwargs)
    """
    # Implementation
```

### 4. Widget Testing Shortcuts

```python
def verify_widget_tree(parent_widget, expected_structure):
    """
    Verify a widget contains the expected structure of child widgets.
    
    Args:
        parent_widget: The widget to check
        expected_structure: Dict describing expected children
        
    Returns:
        True if structure matches, False otherwise
    """
    # Implementation
```

### 5. Test Data Generators

```python
def create_test_model_data(model_class, num_rows=10):
    """
    Create test data for a model class.
    
    Args:
        model_class: The Qt model class to create data for
        num_rows: Number of data rows to generate
        
    Returns:
        Data suitable for the model
    """
    # Implementation
```

## Common Pitfalls and Troubleshooting

During the migration, you may encounter these common issues:

### Import Issues

**Problem**: `ModuleNotFoundError: No module named 'ui.widgets'`  
**Solution**: Use the direct import approach with `importlib.util` instead of package imports.

```python
# Instead of:
from ui.widgets.my_widget import MyWidget

# Use:
spec = importlib.util.spec_from_file_location(
    "my_widget", 
    os.path.abspath("ui/widgets/my_widget.py")
)
my_widget_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(my_widget_module)
MyWidget = my_widget_module.MyWidget
```

### Missing Mocks

**Problem**: `AttributeError: module 'ui.utils' has no attribute 'some_function'`  
**Solution**: Ensure all required functions are mocked.

```python
# Create a complete mock with all required functions
utils_mock = MagicMock()
utils_mock.some_function = MagicMock()
utils_mock.another_function = MagicMock()
sys.modules['ui.utils'] = utils_mock
```

### Widget Not Found

**Problem**: `AssertionError: Button with name=button_name not found`  
**Solution**: Verify widget names and use alternative finding methods.

```python
# Instead of looking by name, find by type and then check properties
buttons = self.find_widgets(parent, QPushButton)
button = next((b for b in buttons if b.text() == "Expected Text"), None)
assert button is not None
```

### Event Processing

**Problem**: Events not being processed properly leading to test failures  
**Solution**: Add explicit event processing after interactions.

```python
# Always call process_events after UI interactions
self.click_button(button)
self.process_events()

# For complex interactions, add more processing time
self.process_events(200)  # 200ms
```

### Dialog Testing

**Problem**: Tests hang when dialogs are shown  
**Solution**: Use the dialog patching or capturing mechanisms.

```python
# Capture dialogs and automatically handle them
with self.capture_dialogs(accept=True) as dialogs:
    self.click_button(button_that_shows_dialog)
    self.process_events()
    
    # Verify dialog properties
    assert len(dialogs) == 1
    assert dialogs[0].windowTitle() == "Expected Title"
```

### Signal Connection Issues

**Problem**: Signal connections not working in tests  
**Solution**: Explicitly track signal emissions.

```python
# Track signal emissions manually
emissions = []
def slot(*args):
    emissions.append(args)

widget.some_signal.connect(slot)
# Trigger signal
assert len(emissions) > 0
```

### Window Focus Issues

**Problem**: Focus-related tests failing  
**Solution**: Explicitly set focus on widgets.

```python
# Ensure widget has focus
widget.setFocus()
self.process_events()
assert widget.hasFocus()
```

### Resources Not Found

**Problem**: Icons, images or other resources not loading  
**Solution**: Mock resource loading functions.

```python
# Mock QIcon to return a dummy icon
QIcon_mock = MagicMock()
QIcon_mock.return_value = MagicMock()  # Returns a dummy icon
monkeypatch.setattr("PySide6.QtGui.QIcon", QIcon_mock)
```

## References

- [Qt Test Documentation](https://doc.qt.io/qt-6/qtest.html)
- [pytest-qt Documentation](https://pytest-qt.readthedocs.io/)
- [Example: test_filter_dropdowns.py](tests/ui/test_filter_dropdowns.py) 