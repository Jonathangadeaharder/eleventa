# Error Handling Test Guidelines

## Overview

This document provides guidelines and patterns for implementing comprehensive error handling tests throughout the codebase. These patterns will help ensure that error conditions are consistently tested and verified, improving the robustness of the application.

## Table of Contents

1. [Utility Functions](#utility-functions)
2. [Testing Exception Types and Messages](#testing-exception-types-and-messages)
3. [Testing Boundary Conditions](#testing-boundary-conditions)
4. [Testing UI Error Handling](#testing-ui-error-handling)
5. [Standardized Validation Error Testing](#standardized-validation-error-testing)
6. [Implementation Examples](#implementation-examples)

## Utility Functions

To standardize exception testing, create utility functions in your test fixtures that can be reused across tests:

```python
import pytest
from typing import Type, Optional, Callable, Any, Dict, List, Tuple

def assert_exception_with_message(
    callable_obj: Callable,
    expected_exception: Type[Exception],
    expected_message: str,
    *args, **kwargs
) -> Exception:
    """
    Assert that a callable raises a specific exception with a specific message.
    """
    with pytest.raises(expected_exception) as excinfo:
        callable_obj(*args, **kwargs)
    
    # Check if the exception message matches exactly
    actual_message = str(excinfo.value)
    assert actual_message == expected_message, (
        f"Expected message '{expected_message}' but got '{actual_message}'"
    )
    
    return excinfo.value

def assert_exception_contains_message(
    callable_obj: Callable,
    expected_exception: Type[Exception],
    expected_partial_message: str,
    *args, **kwargs
) -> Exception:
    """
    Assert that a callable raises a specific exception with a message containing a substring.
    """
    with pytest.raises(expected_exception) as excinfo:
        callable_obj(*args, **kwargs)
    
    # Check if the exception message contains the expected substring
    actual_message = str(excinfo.value)
    assert expected_partial_message in actual_message, (
        f"Expected message to contain '{expected_partial_message}' but got '{actual_message}'"
    )
    
    return excinfo.value

def test_boundary_conditions(
    callable_obj: Callable,
    valid_cases: List[Tuple[Any, ...]],
    boundary_cases: Dict[Tuple[Any, ...], Optional[Type[Exception]]],
    **kwargs
) -> None:
    """
    Test a function with valid and boundary cases.
    """
    # Test valid cases
    for args in valid_cases:
        try:
            callable_obj(*args, **kwargs)
        except Exception as e:
            pytest.fail(f"Failed with valid input {args}: {e}")
    
    # Test boundary cases
    for args, expected_exception in boundary_cases.items():
        if expected_exception:
            with pytest.raises(expected_exception):
                callable_obj(*args, **kwargs)
        else:
            try:
                callable_obj(*args, **kwargs)
            except Exception as e:
                pytest.fail(f"Failed with boundary input {args}: {e}")
```

## Testing Exception Types and Messages

When testing error conditions, follow these principles:

1. **Test for specific exception types**: Don't just check that an exception is raised, verify it's the correct type.
2. **Verify error messages**: Error messages should be clear and specific to help troubleshooting.
3. **Document error scenarios**: Each error test should have a clear docstring explaining the scenario.

Example pattern:

```python
def test_some_function_with_invalid_input_raises_specific_error(service):
    """Test that some_function with invalid input raises a ValidationError with specific message."""
    # Arrange
    invalid_data = {
        "field1": "valid",
        "field2": ""  # Empty field that should cause validation error
    }
    expected_message = "Field2 cannot be empty."
    
    # Act & Assert
    assert_exception_with_message(
        service.some_function,
        ValidationError,
        expected_message,
        **invalid_data
    )
```

## Testing Boundary Conditions

Boundary conditions are values at the edges of valid input ranges. Testing these cases ensures your validation logic handles edge cases correctly.

Example pattern:

```python
def test_function_with_boundary_values(service):
    """Test boundary conditions for input validation."""
    # Define a helper function if needed
    def call_with_value(value):
        return service.some_function(
            field1="valid",
            field2=value
        )
    
    # Define valid and boundary cases
    valid_cases = [
        (1,),       # Minimum valid value
        (100,),     # Normal valid value
        (1000,),    # Maximum valid value
    ]
    
    boundary_cases = {
        (0,): ValidationError,    # Just below minimum (invalid)
        (1001,): ValidationError, # Just above maximum (invalid)
        (None,): ValidationError, # Invalid type
    }
    
    # Test all cases
    test_boundary_conditions(
        call_with_value,
        valid_cases,
        boundary_cases
    )
```

## Testing UI Error Handling

For UI components, error handling tests should verify:

1. **Correct error messages are displayed**: Test that UI shows appropriate messages to users.
2. **UI state after error**: Verify the UI is in the expected state after an error occurs.
3. **Error recovery**: Test that users can correct errors and proceed.

Example pattern:

```python
def test_empty_field_shows_specific_error_message(dialog, qtbot):
    """Test that submitting with an empty required field shows a specific error message."""
    # Arrange - Set up valid data except for the field being tested
    dialog.field1_input.setText("valid")
    dialog.field2_input.setText("")  # Empty field
    
    # Mock message display mechanism (e.g., QMessageBox)
    with patch.object(QMessageBox, 'warning') as mock_warning:
        # Act - Trigger submission
        qtbot.mouseClick(dialog.submit_button, Qt.LeftButton)
        
        # Assert - Verify warning was shown with correct message
        mock_warning.assert_called_once()
        call_args = mock_warning.call_args[0]
        assert "Field2 cannot be empty" in call_args[1]
        # Verify dialog wasn't accepted
        assert not dialog.result()
```

## Standardized Validation Error Testing

For consistent validation testing across multiple services, use parametrized tests:

```python
@pytest.mark.parametrize("service_name,method_name,field_name,test_data,expected_message", [
    # Service 1 validation tests
    ('service1', 'method1', 'field1', {'field1': '', 'field2': 'valid'}, 
     "Field1 cannot be empty."),
    
    # Service 2 validation tests
    ('service2', 'method1', 'field3', {'field3': '', 'field4': 'valid'}, 
     "Field3 cannot be empty."),
])
def test_empty_required_field_raises_validation_error(
    services, service_name, method_name, field_name, test_data, expected_message
):
    """Test that empty required fields raise ValidationError with specific messages."""
    service = services[service_name]
    method = getattr(service, method_name)
    
    assert_exception_with_message(
        method,
        ValidationError,
        expected_message,
        **test_data
    )
```

## Implementation Examples

### Service-Level Error Handling Test

Here's a simplified example for a service method:

```python
def test_add_item_with_invalid_price_raises_error(item_service):
    """Test that adding an item with a negative price raises ValidationError."""
    # Prepare invalid data
    item_data = {
        "name": "Test Item",
        "price": -10.00,  # Negative price
    }
    
    # Verify exception and message
    with pytest.raises(ValidationError) as excinfo:
        item_service.add_item(**item_data)
    
    # Check message content
    assert "Price cannot be negative" in str(excinfo.value)
```

### UI Error Handling Test

Here's a simplified example for a UI component:

```python
def test_form_with_invalid_input_shows_error(form_dialog, qtbot):
    """Test that form validation shows appropriate error for invalid input."""
    # Setup form with invalid data
    form_dialog.name_input.setText("Valid Name")
    form_dialog.email_input.setText("not-an-email")  # Invalid email
    
    # Mock error display
    with patch.object(QMessageBox, 'warning') as mock_warning:
        # Submit form
        qtbot.mouseClick(form_dialog.submit_button, Qt.LeftButton)
        
        # Verify error was displayed
        mock_warning.assert_called_once()
        assert "Invalid email format" in mock_warning.call_args[0][1]
```

### Boundary Testing Example

Here's a simplified example for testing numeric boundaries:

```python
def test_quantity_boundaries(inventory_service):
    """Test boundary values for quantity validation."""
    # Test valid values
    inventory_service.add_inventory(item_id=1, quantity=1)  # Minimum
    inventory_service.add_inventory(item_id=1, quantity=100)  # Normal
    inventory_service.add_inventory(item_id=1, quantity=1000)  # Maximum
    
    # Test invalid values
    with pytest.raises(ValidationError):
        inventory_service.add_inventory(item_id=1, quantity=0)  # Zero
    
    with pytest.raises(ValidationError):
        inventory_service.add_inventory(item_id=1, quantity=-1)  # Negative
    
    with pytest.raises(ValidationError):
        inventory_service.add_inventory(item_id=1, quantity=1001)  # Exceeds maximum
```

## Adapting These Patterns

When implementing these patterns in your codebase:

1. **Use your actual exception types**: Replace generic `ValidationError` with your application's specific exception classes.
2. **Match your module structure**: Adjust import paths to match your codebase organization.
3. **Respect existing conventions**: Follow naming and formatting conventions already established in your test suite.
4. **Start with critical paths**: Prioritize testing error handling in core services and frequently used UI components. 