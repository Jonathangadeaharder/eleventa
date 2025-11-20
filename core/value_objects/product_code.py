"""
ProductCode Value Object

Represents a product code/SKU with validation.

Product codes are value objects because they're immutable and
compared by value.

Usage:
    code = ProductCode('ABC-123')

    # Validation
    try:
        invalid = ProductCode('')  # Raises ValidationError
    except ValidationError as e:
        print(e.message)

    # Comparison
    code1 = ProductCode('ABC123')
    code2 = ProductCode('abc123')  # Case insensitive
    assert code1 == code2  # True
"""

from dataclasses import dataclass
import re
from core.value_objects.base import (
    ValueObject,
    ValidationError,
    validate_not_empty,
    validate_length,
)


@dataclass(frozen=True)
class ProductCode(ValueObject):
    """
    Represents a product code/SKU.

    Product codes are normalized to uppercase and can contain:
    - Letters (A-Z)
    - Numbers (0-9)
    - Hyphens (-)
    - Underscores (_)

    Attributes:
        value: The normalized product code

    Raises:
        ValidationError: If product code format is invalid

    Examples:
        >>> code = ProductCode('ABC-123')
        >>> str(code)
        'ABC-123'

        >>> code.has_prefix('ABC')
        True

        >>> ProductCode('abc-123') == ProductCode('ABC-123')
        True  # Case insensitive
    """

    value: str

    # Product code pattern: alphanumeric, hyphens, underscores
    CODE_PATTERN = re.compile(r"^[A-Z0-9\-_]+$")

    def __post_init__(self):
        """Validate product code on creation."""
        # Check not empty
        validate_not_empty(self.value, "Product code")

        # Normalize to uppercase and trim
        normalized = self.value.strip().upper()

        # Validate length
        validate_length(normalized, 1, 50, "Product code")

        # Validate format
        if not self.CODE_PATTERN.match(normalized):
            raise ValidationError(
                f"Product code can only contain letters, numbers, hyphens, and underscores (got '{self.value}')",
                field="product_code",
            )

        # Validate doesn't start/end with separator
        if normalized.startswith(("-", "_")) or normalized.endswith(("-", "_")):
            raise ValidationError(
                "Product code cannot start or end with separator", field="product_code"
            )

        # Validate no consecutive separators
        if "--" in normalized or "__" in normalized:
            raise ValidationError(
                "Product code cannot contain consecutive separators",
                field="product_code",
            )

        # Store normalized value
        object.__setattr__(self, "value", normalized)

    @property
    def prefix(self) -> str:
        """
        Get the prefix (part before first separator).

        Returns:
            Prefix or full code if no separator

        Examples:
            >>> ProductCode('ABC-123').prefix
            'ABC'
            >>> ProductCode('SIMPLE').prefix
            'SIMPLE'
        """
        for sep in ["-", "_"]:
            if sep in self.value:
                return self.value.split(sep)[0]
        return self.value

    @property
    def suffix(self) -> str:
        """
        Get the suffix (part after last separator).

        Returns:
            Suffix or full code if no separator

        Examples:
            >>> ProductCode('ABC-123').suffix
            '123'
            >>> ProductCode('SIMPLE').suffix
            'SIMPLE'
        """
        for sep in ["-", "_"]:
            if sep in self.value:
                return self.value.split(sep)[-1]
        return self.value

    def has_prefix(self, prefix: str) -> bool:
        """
        Check if code starts with given prefix.

        Args:
            prefix: Prefix to check

        Returns:
            True if code has prefix

        Examples:
            >>> ProductCode('ABC-123').has_prefix('ABC')
            True
            >>> ProductCode('ABC-123').has_prefix('XYZ')
            False
        """
        return self.value.startswith(prefix.upper())

    def has_suffix(self, suffix: str) -> bool:
        """
        Check if code ends with given suffix.

        Args:
            suffix: Suffix to check

        Returns:
            True if code has suffix

        Examples:
            >>> ProductCode('ABC-123').has_suffix('123')
            True
            >>> ProductCode('ABC-123').has_suffix('456')
            False
        """
        return self.value.endswith(suffix.upper())

    def contains(self, substring: str) -> bool:
        """
        Check if code contains substring.

        Args:
            substring: Substring to search for

        Returns:
            True if code contains substring

        Examples:
            >>> ProductCode('ABC-123-XYZ').contains('123')
            True
            >>> ProductCode('ABC-123-XYZ').contains('456')
            False
        """
        return substring.upper() in self.value

    def __str__(self) -> str:
        """
        String representation.

        Returns:
            Product code

        Examples:
            >>> str(ProductCode('ABC-123'))
            'ABC-123'
        """
        return self.value

    def __repr__(self) -> str:
        """
        Developer-friendly representation.

        Returns:
            ProductCode representation

        Examples:
            >>> ProductCode('ABC-123')
            ProductCode('ABC-123')
        """
        return f"ProductCode('{self.value}')"

    @classmethod
    def generate_sku(cls, prefix: str, number: int, suffix: str = "") -> "ProductCode":
        """
        Generate a product code from components.

        Args:
            prefix: Code prefix (e.g., 'PROD')
            number: Sequential number
            suffix: Optional suffix (e.g., 'XL')

        Returns:
            ProductCode instance

        Examples:
            >>> code = ProductCode.generate_sku('PROD', 123)
            >>> str(code)
            'PROD-123'

            >>> code = ProductCode.generate_sku('SHIRT', 42, 'XL')
            >>> str(code)
            'SHIRT-42-XL'
        """
        parts = [prefix, str(number)]
        if suffix:
            parts.append(suffix)

        sku = "-".join(parts)
        return cls(sku)

    @classmethod
    def is_valid_code(cls, code: str) -> bool:
        """
        Check if string is a valid product code without raising exception.

        Args:
            code: String to validate

        Returns:
            True if valid product code

        Examples:
            >>> ProductCode.is_valid_code('ABC-123')
            True
            >>> ProductCode.is_valid_code('invalid@code')
            False
        """
        try:
            cls(code)
            return True
        except ValidationError:
            return False
