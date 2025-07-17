import pytest
from decimal import Decimal
from core.utils.validation import (
    validate_required_field,
    validate_positive_number,
    validate_unique_field,
    validate_non_zero_quantity,
    validate_exists,
    validate_sufficient_stock
)

# Tests for validate_required_field
@pytest.mark.parametrize("value, field_name", [
    ("some value", "Nombre"),
    (123, "ID"),
    (0, "Cantidad"), # Zero is a value
    (False, "Activo") # False is a value
])
def test_validate_required_field_valid(value, field_name):
    validate_required_field(value, field_name) # Should not raise

@pytest.mark.parametrize("value, field_name, expected_message_part", [
    (None, "Name", "Name cannot be empty"),
    ("", "Description", "Description cannot be empty"),
    ("   ", "Code", "Code cannot be empty"),
])
def test_validate_required_field_invalid(value, field_name, expected_message_part):
    with pytest.raises(ValueError, match=expected_message_part):
        validate_required_field(value, field_name)

# Tests for validate_positive_number
@pytest.mark.parametrize("value, field_name", [
    (Decimal("10.5"), "Precio"),
    (Decimal("0.0"), "Descuento"), # Zero is non-negative
    (None, "Límite") # None is allowed
])
def test_validate_positive_number_valid(value, field_name):
    validate_positive_number(value, field_name) # Should not raise

@pytest.mark.parametrize("value, field_name, expected_message_part", [
    (Decimal("-5"), "Quantity", "Quantity must be positive"),
    (Decimal("-0.01"), "Price", "Price must be positive"),
])
def test_validate_positive_number_invalid(value, field_name, expected_message_part):
    with pytest.raises(ValueError, match=expected_message_part):
        validate_positive_number(value, field_name)

# Tests for validate_unique_field
def test_validate_unique_field_not_exists():
    validate_unique_field(False, "Código", "P001") # Should not raise

def test_validate_unique_field_exists_create():
    with pytest.raises(ValueError, match="Code 'P001' already exists"):
        validate_unique_field(True, "Code", "P001", is_update=False)

def test_validate_unique_field_exists_update():
    with pytest.raises(ValueError, match="Code 'P001' already exists for another record"):
        validate_unique_field(True, "Code", "P001", is_update=True)

# Tests for validate_non_zero_quantity
@pytest.mark.parametrize("quantity, operation_name", [
    (Decimal("1"), "venta"),
    (Decimal("0.01"), "compra"),
])
def test_validate_non_zero_quantity_valid(quantity, operation_name):
    validate_non_zero_quantity(quantity, operation_name) # Should not raise

@pytest.mark.parametrize("quantity, operation_name, expected_message_part", [
    (Decimal("0"), "sale", "Quantity for sale must be greater than zero"),
    (Decimal("-1"), "adjustment", "Quantity for adjustment must be greater than zero"),
])
def test_validate_non_zero_quantity_invalid(quantity, operation_name, expected_message_part):
    with pytest.raises(ValueError, match=expected_message_part):
        validate_non_zero_quantity(quantity, operation_name)

# Tests for validate_exists
def test_validate_exists_true():
    validate_exists(True, "Producto", 123) # Should not raise

def test_validate_exists_false():
    with pytest.raises(ValueError, match="Product with ID 123 does not exist"):
        validate_exists(False, "Product", 123)

# Tests for validate_sufficient_stock
def test_validate_sufficient_stock_valid():
    validate_sufficient_stock(Decimal("10"), Decimal("5"), "PROD001") # Should not raise
    validate_sufficient_stock(Decimal("5"), Decimal("5"), "PROD002") # Equal is sufficient

def test_validate_sufficient_stock_invalid():
    with pytest.raises(ValueError, match="Insufficient stock for 'PROD003'. Available: 5, Requested: 10"):
        validate_sufficient_stock(Decimal("5"), Decimal("10"), "PROD003")