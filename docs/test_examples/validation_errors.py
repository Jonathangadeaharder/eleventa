"""
Example of standardized validation error testing across services.

This file demonstrates best practices for testing validation errors
consistently across different services, ensuring validation logic 
is thoroughly tested and error messages are consistently verified.

NOTE: This is an example file for reference only and is not intended to be run
as an actual test. The imports and class references may need to be adapted
to your specific project structure.
"""
import pytest
from unittest.mock import MagicMock
from decimal import Decimal

# Example exception class - adapt to match your project's actual exceptions
class ValidationError(Exception): pass

# Example models - adapt to match your project's actual models
class Product:
    def __init__(self, id=None, name=None, code=None, price=None, department_id=None):
        self.id = id
        self.name = name
        self.code = code
        self.price = price
        self.department_id = department_id

class Customer:
    def __init__(self, id=None, name=None, email=None, phone=None):
        self.id = id
        self.name = name
        self.email = email
        self.phone = phone

class Sale:
    def __init__(self, id=None, customer_id=None, items=None, payment_method=None, total=None):
        self.id = id
        self.customer_id = customer_id
        self.items = items or []
        self.payment_method = payment_method
        self.total = total

class InventoryMovement:
    def __init__(self, id=None, product_id=None, quantity=None, movement_type=None, notes=None):
        self.id = id
        self.product_id = product_id
        self.quantity = quantity
        self.movement_type = movement_type
        self.notes = notes

# Example service classes - adapt to match your project's actual services
class ProductService:
    def __init__(self, product_repo, department_repo):
        self.product_repo = product_repo
        self.department_repo = department_repo
    
    def add_product(self, name, code, price, department_id):
        if not code:
            raise ValidationError("Code cannot be empty.")
        if not name:
            raise ValidationError("Name cannot be empty.")
        if price < Decimal("0"):
            raise ValidationError("Price cannot be negative.")
        # Additional validation and processing...
        return Product(id=1, name=name, code=code, price=price, department_id=department_id)

class CustomerService:
    def __init__(self, customer_repo):
        self.customer_repo = customer_repo
    
    def add_customer(self, name, email, phone):
        if not name:
            raise ValidationError("Name cannot be empty.")
        if not email:
            raise ValidationError("Email cannot be empty.")
        if not self._is_valid_email(email):
            raise ValidationError("Invalid email format.")
        if phone and not phone.isdigit():
            raise ValidationError("Phone number must contain only digits.")
        # Additional validation and processing...
        return Customer(id=1, name=name, email=email, phone=phone)
    
    def _is_valid_email(self, email):
        return "@" in email and "." in email

class SaleService:
    def __init__(self, sale_repo, product_repo, customer_repo):
        self.sale_repo = sale_repo
        self.product_repo = product_repo
        self.customer_repo = customer_repo
    
    def create_sale(self, customer_id, items, payment_method):
        if not items:
            raise ValidationError("Sale must have at least one item.")
        if not payment_method:
            raise ValidationError("Payment method cannot be empty.")
        
        valid_payment_methods = ["cash", "card", "transfer"]
        if payment_method not in valid_payment_methods:
            raise ValidationError(f"Invalid payment method. Allowed values are: {', '.join(valid_payment_methods)}.")
            
        for item in items:
            if item.get("quantity", 0) <= 0:
                raise ValidationError("Item quantity cannot be negative or zero.")
        
        # Additional validation and processing...
        return Sale(id=1, customer_id=customer_id, items=items, payment_method=payment_method)

class InventoryService:
    def __init__(self, inventory_repo, product_repo):
        self.inventory_repo = inventory_repo
        self.product_repo = product_repo
    
    def add_inventory(self, product_id, quantity, movement_type, notes=None):
        if not product_id:
            raise ValidationError("Product ID cannot be empty.")
        if quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")
        if not movement_type:
            raise ValidationError("Movement type cannot be empty.")
        
        # Additional validation and processing...
        return InventoryMovement(
            id=1, product_id=product_id, quantity=quantity, 
            movement_type=movement_type, notes=notes
        )

# Utility function for error testing
def assert_exception_with_message(callable_obj, expected_exception, expected_message, *args, **kwargs):
    with pytest.raises(expected_exception) as excinfo:
        callable_obj(*args, **kwargs)
    
    actual_message = str(excinfo.value)
    assert actual_message == expected_message, f"Expected '{expected_message}' but got '{actual_message}'"
    return excinfo.value

# Example test fixtures
@pytest.fixture
def mock_repositories():
    """Create mock repositories for all services."""
    return {
        'product_repo': MagicMock(),
        'department_repo': MagicMock(),
        'customer_repo': MagicMock(),
        'sale_repo': MagicMock(),
        'inventory_repo': MagicMock()
    }

@pytest.fixture
def services(mock_repositories):
    """Create service instances with mock repositories."""
    return {
        'product_service': ProductService(
            mock_repositories['product_repo'], 
            mock_repositories['department_repo']
        ),
        'customer_service': CustomerService(mock_repositories['customer_repo']),
        'sale_service': SaleService(
            mock_repositories['sale_repo'], 
            mock_repositories['product_repo'],
            mock_repositories['customer_repo']
        ),
        'inventory_service': InventoryService(
            mock_repositories['inventory_repo'],
            mock_repositories['product_repo']
        )
    }

# Example test class for empty field validation
class TestEmptyRequiredFields:
    """Tests for empty required fields across services."""
    
    @pytest.mark.parametrize("service_name,method_name,field_name,test_data,expected_message", [
        # Product service validation tests
        ('product_service', 'add_product', 'code', {
            'name': 'Test Product', 'code': '', 'price': Decimal('10.00'), 'department_id': 1
        }, "Code cannot be empty."),
        ('product_service', 'add_product', 'name', {
            'name': '', 'code': 'TEST001', 'price': Decimal('10.00'), 'department_id': 1
        }, "Name cannot be empty."),
        
        # Customer service validation tests
        ('customer_service', 'add_customer', 'name', {
            'name': '', 'email': 'test@example.com', 'phone': '1234567890'
        }, "Name cannot be empty."),
        ('customer_service', 'add_customer', 'email', {
            'name': 'Test Customer', 'email': '', 'phone': '1234567890'
        }, "Email cannot be empty."),
        
        # Sale service validation tests
        ('sale_service', 'create_sale', 'items', {
            'customer_id': 1, 'items': [], 'payment_method': 'cash'
        }, "Sale must have at least one item."),
        ('sale_service', 'create_sale', 'payment_method', {
            'customer_id': 1, 'items': [{'product_id': 1, 'quantity': 1}], 'payment_method': ''
        }, "Payment method cannot be empty."),
        
        # Inventory service validation tests
        ('inventory_service', 'add_inventory', 'product_id', {
            'product_id': None, 'quantity': 10, 'movement_type': 'purchase', 'notes': 'Test'
        }, "Product ID cannot be empty."),
        ('inventory_service', 'add_inventory', 'quantity', {
            'product_id': 1, 'quantity': 0, 'movement_type': 'purchase', 'notes': 'Test'
        }, "Quantity must be greater than zero.")
    ])
    def test_empty_required_field_raises_validation_error(
        self, services, service_name, method_name, field_name, test_data, expected_message
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

# Example test class for invalid format validation
class TestInvalidFormatValidation:
    """Tests for invalid format validation across services."""
    
    @pytest.mark.parametrize("service_name,method_name,field_name,invalid_value,expected_message", [
        # Email format validation
        ('customer_service', 'add_customer', 'email', 'not-an-email', 
         "Invalid email format."),
        
        # Phone format validation
        ('customer_service', 'add_customer', 'phone', 'abc', 
         "Phone number must contain only digits."),
        
        # Payment method validation
        ('sale_service', 'create_sale', 'payment_method', 'invalid-method', 
         "Invalid payment method. Allowed values are: cash, card, transfer.")
    ])
    def test_invalid_format_raises_validation_error(
        self, services, service_name, method_name, field_name, invalid_value, expected_message
    ):
        """Test that invalid formats raise ValidationError with specific messages."""
        service = services[service_name]
        method = getattr(service, method_name)
        
        # Prepare valid test data and then override with invalid value
        test_data = {}
        if service_name == 'product_service':
            test_data = {
                'name': 'Test Product', 
                'code': 'TEST001', 
                'price': Decimal('10.00'), 
                'department_id': 1
            }
        elif service_name == 'customer_service':
            test_data = {
                'name': 'Test Customer',
                'email': 'valid@example.com',
                'phone': '1234567890'
            }
        elif service_name == 'sale_service':
            test_data = {
                'customer_id': 1, 
                'items': [{'product_id': 1, 'quantity': 1}],
                'payment_method': 'cash'
            }
        elif service_name == 'inventory_service':
            test_data = {
                'product_id': 1,
                'quantity': 10,
                'movement_type': 'purchase',
                'notes': 'Test'
            }
            
        # Override with invalid value
        test_data[field_name] = invalid_value
        
        assert_exception_with_message(
            method,
            ValidationError,
            expected_message,
            **test_data
        )

# Example test class for negative value validation
class TestNegativeValueValidation:
    """Tests for negative value validation across services."""
    
    @pytest.mark.parametrize("service_name,method_name,field_name,negative_value,expected_message", [
        # Negative price validation
        ('product_service', 'add_product', 'price', Decimal('-10.00'), 
         "Price cannot be negative."),
        
        # Negative item quantity validation
        ('sale_service', 'create_sale', 'items', [{'product_id': 1, 'quantity': -1}], 
         "Item quantity cannot be negative or zero.")
    ])
    def test_negative_values_raise_validation_error(
        self, services, service_name, method_name, field_name, negative_value, expected_message
    ):
        """Test that negative values raise ValidationError with specific messages."""
        service = services[service_name]
        method = getattr(service, method_name)
        
        # Prepare valid test data and then override with negative value
        test_data = {}
        if service_name == 'product_service':
            test_data = {
                'name': 'Test Product', 
                'code': 'TEST001', 
                'price': Decimal('10.00'), 
                'department_id': 1
            }
        elif service_name == 'sale_service':
            test_data = {
                'customer_id': 1, 
                'items': [{'product_id': 1, 'quantity': 1}],
                'payment_method': 'cash'
            }
            
        # Override with negative value
        test_data[field_name] = negative_value
        
        assert_exception_with_message(
            method,
            ValidationError,
            expected_message,
            **test_data
        ) 