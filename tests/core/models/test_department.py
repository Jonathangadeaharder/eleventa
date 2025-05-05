import pytest

from core.models.department import Department

def test_department_initialization():
    """Test initializing a Department object."""
    dept_id = 1
    dept_name = "Electronics"
    dept_desc = "Gadgets and gizmos"
    
    dept = Department(id=dept_id, name=dept_name, description=dept_desc)
    
    assert dept.id == dept_id
    assert dept.name == dept_name
    assert dept.description == dept_desc

def test_department_initialization_with_defaults():
    """Test initializing a Department object with default values (None)."""
    dept = Department()
    
    assert dept.id is None
    assert dept.name == ""
    assert dept.description is None

def test_department_initialization_some_values():
    """Test initializing a Department object with only some values."""
    dept_id = 2
    dept_name = "Groceries"
    
    dept = Department(id=dept_id, name=dept_name)
    
    assert dept.id == dept_id
    assert dept.name == dept_name
    assert dept.description is None # Default description should be None 