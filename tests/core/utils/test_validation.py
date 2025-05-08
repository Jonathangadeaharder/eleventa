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
    (None, "Nombre", "Nombre es requerido"),
    ("", "Descripción", "Descripción es requerido"),
    ("   ", "Código", "Código es requerido"),
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
    (Decimal("-5"), "Cantidad", "Cantidad debe ser positivo"),
    (Decimal("-0.01"), "Precio", "Precio debe ser positivo"),
])
def test_validate_positive_number_invalid(value, field_name, expected_message_part):
    with pytest.raises(ValueError, match=expected_message_part):
        validate_positive_number(value, field_name)

# Tests for validate_unique_field
def test_validate_unique_field_not_exists():
    validate_unique_field(False, "Código", "P001") # Should not raise

def test_validate_unique_field_exists_create():
    with pytest.raises(ValueError, match="Código 'P001' ya existe"):
        validate_unique_field(True, "Código", "P001", is_update=False)

def test_validate_unique_field_exists_update():
    with pytest.raises(ValueError, match="Código 'P001' ya existe para otro registro"):
        validate_unique_field(True, "Código", "P001", is_update=True)

# Tests for validate_non_zero_quantity
@pytest.mark.parametrize("quantity, operation_name", [
    (Decimal("1"), "venta"),
    (Decimal("0.01"), "compra"),
])
def test_validate_non_zero_quantity_valid(quantity, operation_name):
    validate_non_zero_quantity(quantity, operation_name) # Should not raise

@pytest.mark.parametrize("quantity, operation_name, expected_message_part", [
    (Decimal("0"), "venta", "La cantidad para venta debe ser mayor a cero"),
    (Decimal("-1"), "ajuste", "La cantidad para ajuste debe ser mayor a cero"),
])
def test_validate_non_zero_quantity_invalid(quantity, operation_name, expected_message_part):
    with pytest.raises(ValueError, match=expected_message_part):
        validate_non_zero_quantity(quantity, operation_name)

# Tests for validate_exists
def test_validate_exists_true():
    validate_exists(True, "Producto", 123) # Should not raise

def test_validate_exists_false():
    with pytest.raises(ValueError, match="Producto con ID 123 no existe"):
        validate_exists(False, "Producto", 123)

# Tests for validate_sufficient_stock
def test_validate_sufficient_stock_valid():
    validate_sufficient_stock(Decimal("10"), Decimal("5"), "PROD001") # Should not raise
    validate_sufficient_stock(Decimal("5"), Decimal("5"), "PROD002") # Equal is sufficient

def test_validate_sufficient_stock_invalid():
    with pytest.raises(ValueError, match="Stock insuficiente para 'PROD003'. Disponible: 5, Solicitado: 10"):
        validate_sufficient_stock(Decimal("5"), Decimal("10"), "PROD003") 