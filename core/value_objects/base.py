"""
Base Value Object Implementation

Provides the foundation for all value objects in the system.

Value Objects vs Entities:
- Value Objects: Equality by value, immutable, no identity
- Entities: Equality by identity, mutable, have unique IDs

Examples:
- Value Object: Money($10), Email(joe@example.com), Address
- Entity: Customer(id=123), Product(id=456), Sale(id=789)
"""

from abc import ABC
from typing import Any, Tuple, Optional


class ValueObject(ABC):
    """
    Base class for all Value Objects.

    Value Objects are immutable and compared by value rather than identity.

    Subclasses should:
    1. Use @dataclass(frozen=True) for immutability
    2. Implement validation in __post_init__
    3. Provide meaningful operations that return new instances

    Example:
        @dataclass(frozen=True)
        class Money(ValueObject):
            amount: Decimal
            currency: str

            def __post_init__(self):
                if self.amount < 0:
                    raise ValueError("Amount cannot be negative")
                if not self.currency:
                    raise ValueError("Currency is required")

            def add(self, other: 'Money') -> 'Money':
                if self.currency != other.currency:
                    raise ValueError("Cannot add different currencies")
                return Money(self.amount + other.amount, self.currency)
    """

    def __eq__(self, other: Any) -> bool:
        """
        Value objects are equal if their values are equal.

        This is implemented automatically by dataclass, but we
        document it here for clarity.
        """
        if not isinstance(other, self.__class__):
            return False
        return self._get_equality_components() == other._get_equality_components()

    def __hash__(self) -> int:
        """
        Value objects must be hashable for use in sets and dicts.

        This is implemented automatically by frozen dataclass.
        """
        return hash(self._get_equality_components())

    def _get_equality_components(self) -> Tuple:
        """
        Get the components used for equality comparison.

        Returns:
            Tuple of values used for equality comparison

        Note:
            This is typically handled automatically by dataclass,
            but can be overridden for complex equality logic.
        """
        # For dataclasses, we can use __dict__ or vars()
        # This works because frozen dataclasses are immutable
        return tuple(sorted(self.__dict__.items()))

    def __repr__(self) -> str:
        """
        String representation of the value object.

        This is implemented automatically by dataclass.
        """
        class_name = self.__class__.__name__
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{class_name}({attrs})"


class ValueObjectError(Exception):
    """Base exception for value object errors."""

    pass


class ValidationError(ValueObjectError):
    """Raised when value object validation fails."""

    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(message)


# Validation helper functions


def validate_not_empty(value: str, field_name: str) -> None:
    """
    Validate that a string is not empty.

    Args:
        value: The string to validate
        field_name: Name of the field for error messages

    Raises:
        ValidationError: If value is empty or whitespace
    """
    if not value or not value.strip():
        raise ValidationError(f"{field_name} cannot be empty", field=field_name)


def validate_positive(value: Any, field_name: str) -> None:
    """
    Validate that a numeric value is positive.

    Args:
        value: The numeric value to validate
        field_name: Name of the field for error messages

    Raises:
        ValidationError: If value is not positive
    """
    if value <= 0:
        raise ValidationError(
            f"{field_name} must be positive (got {value})", field=field_name
        )


def validate_non_negative(value: Any, field_name: str) -> None:
    """
    Validate that a numeric value is non-negative.

    Args:
        value: The numeric value to validate
        field_name: Name of the field for error messages

    Raises:
        ValidationError: If value is negative
    """
    if value < 0:
        raise ValidationError(
            f"{field_name} cannot be negative (got {value})", field=field_name
        )


def validate_range(value: Any, min_value: Any, max_value: Any, field_name: str) -> None:
    """
    Validate that a value is within a range.

    Args:
        value: The value to validate
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        field_name: Name of the field for error messages

    Raises:
        ValidationError: If value is outside range
    """
    if value < min_value or value > max_value:
        raise ValidationError(
            f"{field_name} must be between {min_value} and {max_value} (got {value})",
            field=field_name,
        )


def validate_length(
    value: str, min_length: int, max_length: int, field_name: str
) -> None:
    """
    Validate string length.

    Args:
        value: The string to validate
        min_length: Minimum length (inclusive)
        max_length: Maximum length (inclusive)
        field_name: Name of the field for error messages

    Raises:
        ValidationError: If length is outside range
    """
    length = len(value)
    if length < min_length or length > max_length:
        raise ValidationError(
            f"{field_name} length must be between {min_length} and {max_length} "
            f"(got {length})",
            field=field_name,
        )


def validate_regex(
    value: str, pattern: str, field_name: str, message: Optional[str] = None
) -> None:
    """
    Validate string against regex pattern.

    Args:
        value: The string to validate
        pattern: Regex pattern to match
        field_name: Name of the field for error messages
        message: Custom error message (optional)

    Raises:
        ValidationError: If value doesn't match pattern
    """
    import re

    if not re.match(pattern, value):
        error_msg = message or f"{field_name} has invalid format"
        raise ValidationError(error_msg, field=field_name)
