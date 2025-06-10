# UI Test Standardization Guide

## Overview
This document defines the standard structure and patterns for UI component tests in the Eleventa application. Following these guidelines ensures consistency, maintainability, and reliability across all UI tests.

## Test File Structure

### 1. Module Docstring
Every test file should begin with a clear docstring that:
- Identifies the UI component being tested
- Explains the focus/purpose of the tests
- Lists key functionality being verified

Example:
```python
"""
Tests for the ProductsView UI component.
Focus: Product listing, selection, and UI interaction.

This test suite verifies the functionality of the ProductsView component, including:
- UI initialization and widget availability
- Button interactions and dialog openings
- Product model updates and view refreshing
- Error handling for various scenarios
"""
```

### 2. Imports
Organize imports in the following order:
1. Standard library imports
2. Third-party imports (pytest, PySide6, etc.)
3. Application imports (grouped by module)
4. Test utility/mock imports

Example:
```python
# Standard library
import sys
from decimal import Decimal
from datetime import datetime, date

# Testing frameworks
import pytest
from unittest.mock import MagicMock, patch

# Qt components
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtTest import QTest as QtTest

# Application components
from ui.views.products_view import ProductsView
from ui.dialogs.product_dialog import ProductDialog
from core.services.product_service import ProductService
from core.models.product import Product

# Test utilities
import tests.ui.patch_resources  # For resource patching
```

### 3. Mock Classes and Helpers
Define mock classes and helper functions:
- Use docstrings to explain their purpose
- Organize into logical groups
- Name clearly with descriptive prefix (e.g., `Mock`, `Dummy`, etc.)

Example:
```python
class MockProductTableModel(QtCore.QAbstractTableModel):
    """Mock implementation of ProductTableModel for testing.
    
    Provides a simplified table model that doesn't depend on the real
    implementation but maintains the interface for Widget testing.
    """
    # Implementation...

def create_test_product(id=1, code="P001", description="Test Product"):
    """Create a test product with default values for testing."""
    # Implementation...
```

### 4. Fixtures
Define fixtures that:
- Have clear, descriptive docstrings
- Use appropriate scope
- Handle clean setup and teardown
- Mock dependencies consistently

Example:
```python
@pytest.fixture
def product_service():
    """Create a mock product service for testing."""
    service = MagicMock(spec=ProductService)
    service.get_all_products.return_value = [
        create_test_product(1, "P001", "Test Product 1"),
        create_test_product(2, "P002", "Test Product 2"),
    ]
    return service

@pytest.fixture
def products_view(qtbot, product_service, monkeypatch):
    """Create a ProductsView instance with patched components.
    
    Patches dialog execution to prevent hanging and uses a mock table model.
    Disables auto-refresh for predictable testing.
    """
    # Patch implementations...
    
    view = ProductsView(product_service=product_service, enable_auto_refresh=False)
    qtbot.addWidget(view)
    view.show()
    
    # Process events for stability
    QApplication.processEvents()
    
    yield view
    
    # Clean up resources
    view.close()
    view.deleteLater()
    QApplication.processEvents()
```

### 5. Test Functions
Organize test functions that:
- Follow naming convention: `test_<functionality>_<scenario>_<expected_result>`
- Have clear docstrings explaining what is being tested
- Contain clear setup, action, and assertion sections
- Use appropriate assertions with descriptive messages
- Process Qt events appropriately

Example:
```python
def test_add_product_button_opens_dialog(products_view, qtbot, monkeypatch):
    """
    Test that clicking the 'Add Product' button opens the ProductDialog.
    
    Verifies that the action of clicking the button properly triggers the dialog
    and that the dialog is correctly initialized.
    """
    # Setup: mock the dialog to capture how it's called
    mock_dialog = MagicMock(return_value=QDialog.Accepted)
    monkeypatch.setattr('ui.views.products_view.ProductDialog', mock_dialog)
    
    # Action: click the button
    qtbot.mouseClick(products_view.add_button, Qt.LeftButton)
    QApplication.processEvents()
    
    # Assert: dialog was created with correct parameters
    mock_dialog.assert_called_once()
    assert mock_dialog.call_args[0][0] == products_view.product_service
```

## Test Categories

For each UI component, include tests for these categories where applicable:

### 1. Initialization Tests
- Test that the UI component initializes correctly
- Verify that widgets, layouts, and initial state are correct

### 2. Interaction Tests
- Test button clicks, menu selections, and other user interactions
- Verify that dialogs open and close properly
- Test form submission and validation

### 3. Data Display Tests
- Test that data is correctly displayed in tables, lists, etc.
- Verify sorting, filtering, and pagination if applicable
- Test data updates are reflected in the UI

### 4. Error Handling Tests
- Test validation errors and error messages
- Verify that UI handles exceptions gracefully
- Test boundary conditions and edge cases

## Best Practices

1. **Isolation**: Ensure tests are isolated and don't depend on other tests
2. **Deterministic**: Avoid non-deterministic behavior (e.g., random data, timers)
3. **Mocking**: Mock external dependencies and services
4. **Resource Management**: Clean up resources in fixture teardown
5. **Event Processing**: Process Qt events after actions to ensure UI updates
6. **Documentation**: Document complex test scenarios and edge cases
7. **Coverage**: Aim for comprehensive coverage of UI functionality

## Anti-Patterns to Avoid

1. **Flaky Tests**: Tests that sometimes pass and sometimes fail
2. **Slow Tests**: Tests that take too long to execute
3. **Over-mocking**: Mocking too much makes tests less valuable
4. **Fragile Tests**: Tests that break when UI details change
5. **Inadequate Assertions**: Only asserting that code runs without errors