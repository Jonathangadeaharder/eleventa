"""
Simple integration test to verify basic test setup.

This test validates that our test configuration is working correctly.
"""
import pytest


@pytest.mark.integration
def test_simple():
    """Test that pytest is running correctly with our configuration."""
    assert True, "Basic assertion should pass"


@pytest.mark.integration
def test_import_exceptions():
    """Test that the core exceptions module can be imported."""
    from core.exceptions import ValidationError
    assert ValidationError is not None, "Core exceptions should be importable"


@pytest.mark.integration
def test_import_department():
    """Test that the department model can be imported."""
    from core.models.department import Department
    assert Department is not None, "Department model should be importable" 