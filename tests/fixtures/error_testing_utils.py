"""
Utilities for standardized error handling testing.

This module provides utility functions and fixtures to standardize 
error handling tests across the codebase, ensuring consistent patterns
for testing exceptions, boundary conditions, and error messages.
"""
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
    
    Args:
        callable_obj: The callable to test
        expected_exception: The exception type expected
        expected_message: The expected exception message
        *args, **kwargs: Arguments to pass to the callable
        
    Returns:
        The caught exception object for further assertions if needed
        
    Raises:
        AssertionError: If the exception is not raised or has an unexpected message
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
    
    Args:
        callable_obj: The callable to test
        expected_exception: The exception type expected
        expected_partial_message: Substring expected to be in the exception message
        *args, **kwargs: Arguments to pass to the callable
        
    Returns:
        The caught exception object for further assertions if needed
        
    Raises:
        AssertionError: If the exception is not raised or doesn't contain the expected message
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
    
    Args:
        callable_obj: The callable to test
        valid_cases: List of tuples containing valid inputs
        boundary_cases: Dict mapping boundary inputs to expected exception types (None if no exception)
        **kwargs: Additional keyword arguments to pass to the callable
        
    Example:
        test_boundary_conditions(
            divide, 
            valid_cases=[(10, 2), (10, 5)],
            boundary_cases={
                (10, 0): ZeroDivisionError,
                (0, 5): None  # Valid but boundary case
            }
        )
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