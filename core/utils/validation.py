"""
Common validation functions for data validation across services.
"""

from decimal import Decimal
from typing import Optional, Any


def validate_required_field(value: Any, field_name: str) -> None:
    """Validates that a field is not empty or None."""
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"{field_name} cannot be empty")


def validate_positive_number(value: Optional[Decimal], field_name: str) -> None:
    """Validates that a number is positive (or None)."""
    if value is not None and value < 0:
        raise ValueError(f"{field_name} must be positive")


def validate_unique_field(
    exists: bool, field_name: str, field_value: str, is_update: bool = False
) -> None:
    """Validates that a field value is unique based on existence check."""
    if exists:
        error_suffix = " for another record" if is_update else ""
        raise ValueError(f"{field_name} '{field_value}' already exists{error_suffix}")


def validate_non_zero_quantity(quantity: Decimal, operation_name: str) -> None:
    """Validates that a quantity is greater than zero."""
    if quantity <= 0:
        raise ValueError(f"Quantity for {operation_name} must be greater than zero")


def validate_exists(exists: bool, entity_type: str, entity_id: Any) -> None:
    """Validates that an entity exists."""
    if not exists:
        raise ValueError(f"{entity_type} with ID {entity_id} does not exist")


def validate_sufficient_stock(
    available: Decimal, requested: Decimal, product_code: str
) -> None:
    """Validates that there is sufficient stock for an operation."""
    if available < requested:
        raise ValueError(
            f"Insufficient stock for '{product_code}'. Available: {available}, Requested: {requested}"
        )
