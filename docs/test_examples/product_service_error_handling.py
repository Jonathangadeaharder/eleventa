"""
Example of enhanced error handling tests for a ProductService.

This file demonstrates best practices for testing service-level error handling:
- Testing specific exception types and messages
- Testing boundary conditions for validation
- Testing database error handling

NOTE: This is an example file for reference only and is not intended to be run
as an actual test. The imports and class references may need to be adapted
to your specific project structure.
"""
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

# NOTE: Replace these imports with your actual project imports
# Example exception types - adapt to match your project's actual exceptions
class ValidationError(Exception): pass
class ResourceNotFoundError(Exception): pass
class DuplicateResourceError(Exception): pass
class DatabaseError(Exception): pass

# Example models - adapt to match your project's actual models
class Product:
    def __init__(self, id=None, name=None, code=None, price=None, department_id=None):
        self.id = id
        self.name = name
        self.code = code
        self.price = price
        self.department_id = department_id

class Department:
    def __init__(self, id=None, name=None):
        self.id = id
        self.name = name

# Example service - adapt to match your project's actual service
class ProductService:
    def __init__(self, product_repo, department_repo):
        self.product_repo = product_repo
        self.department_repo = department_repo
        
    def add_product(self, name, code, price, department_id):
        # Validation logic
        if not code:
            raise ValidationError("Product code cannot be empty.")
        if not name:
            raise ValidationError("Product name cannot be empty.")
        if price <= Decimal("0"):
            raise ValidationError("Price cannot be negative or zero.")
            
        # Check for existing product
        existing = self.product_repo.get_by_code(code)
        if existing:
            raise DuplicateResourceError(f"Product with code '{code}' already exists.")
            
        # Check for department
        department = self.department_repo.get_by_id(department_id)
        if not department:
            raise ResourceNotFoundError(f"Department with ID {department_id} does not exist.")
            
        # Create product
        try:
            product = Product(name=name, code=code, price=price, department_id=department_id)
            return self.product_repo.add(product)
        except Exception as e:
            raise DatabaseError(f"Failed to add product: {str(e)}")

# Utility functions for error testing
def assert_exception_with_message(callable_obj, expected_exception, expected_message, *args, **kwargs):
    with pytest.raises(expected_exception) as excinfo:
        callable_obj(*args, **kwargs)
    
    actual_message = str(excinfo.value)
    assert actual_message == expected_message, f"Expected '{expected_message}' but got '{actual_message}'"
    return excinfo.value

def assert_exception_contains_message(callable_obj, expected_exception, expected_partial_message, *args, **kwargs):
    with pytest.raises(expected_exception) as excinfo:
        callable_obj(*args, **kwargs)
    
    actual_message = str(excinfo.value)
    assert expected_partial_message in actual_message, f"Expected '{expected_partial_message}' in '{actual_message}'"
    return excinfo.value

def test_boundary_conditions(callable_obj, valid_cases, boundary_cases, **kwargs):
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

# Example test cases
class TestAddProductErrorHandling:
    """Tests for error handling in the add_product method."""
    
    @pytest.fixture
    def mock_product_repo(self):
        return MagicMock()
    
    @pytest.fixture
    def mock_department_repo(self):
        return MagicMock()
    
    @pytest.fixture
    def product_service(self, mock_product_repo, mock_department_repo):
        return ProductService(mock_product_repo, mock_department_repo)
    
    def test_add_product_with_empty_code_raises_specific_error(self, product_service):
        """Test that add_product with empty code raises ValidationError with specific message."""
        # Arrange
        product_data = {
            "name": "Test Product",
            "code": "",  # Empty code
            "price": Decimal("10.00"),
            "department_id": 1
        }
        expected_message = "Product code cannot be empty."
        
        # Act & Assert
        assert_exception_with_message(
            product_service.add_product,
            ValidationError,
            expected_message,
            **product_data
        )
    
    def test_add_product_with_duplicate_code_raises_specific_error(self, product_service, mock_product_repo):
        """Test that add_product with duplicate code raises DuplicateResourceError with specific message."""
        # Arrange
        product_code = "ABC123"
        product_data = {
            "name": "Test Product",
            "code": product_code,
            "price": Decimal("10.00"),
            "department_id": 1
        }
        
        # Setup mock to return an existing product with the same code
        existing_product = Product(id=1, name="Existing", code=product_code, price=Decimal("15.00"), department_id=1)
        mock_product_repo.get_by_code.return_value = existing_product
        
        expected_message = f"Product with code '{product_code}' already exists."
        
        # Act & Assert
        assert_exception_with_message(
            product_service.add_product,
            DuplicateResourceError,
            expected_message,
            **product_data
        )
        
        # Verify repository was called correctly
        mock_product_repo.get_by_code.assert_called_once_with(product_code)
    
    def test_add_product_price_boundary_conditions(self, product_service, mock_product_repo, mock_department_repo):
        """Test boundary conditions for product price validation."""
        # Setup mocks for normal validation
        mock_product_repo.get_by_code.return_value = None
        mock_department_repo.get_by_id.return_value = Department(id=1, name="Test Department")
        
        # Define a helper function for the test_boundary_conditions utility
        def add_product_with_price(price):
            return product_service.add_product(
                name="Test Product",
                code="TEST001",
                price=price,
                department_id=1
            )
        
        # Define valid and boundary cases
        valid_cases = [
            (Decimal("0.01"),),  # Minimum valid price
            (Decimal("1.00"),),
            (Decimal("9999.99"),),  # Some arbitrary high price
        ]
        
        boundary_cases = {
            (Decimal("0.00"),): ValidationError,   # Zero price (invalid)
            (Decimal("-0.01"),): ValidationError,  # Negative price (invalid)
            (Decimal("1000000.00"),): None,        # Very high price (valid but boundary)
        }
        
        # Test all cases
        test_boundary_conditions(
            add_product_with_price,
            valid_cases,
            boundary_cases
        ) 