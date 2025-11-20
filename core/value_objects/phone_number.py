"""
PhoneNumber Value Object

Represents a phone number with validation.

Phone numbers are value objects because they're immutable and
compared by value.

Usage:
    # International format
    phone = PhoneNumber('+1-555-123-4567')

    # Formatted display
    print(phone.format())  # '+1-555-123-4567'

    # Comparison
    phone1 = PhoneNumber('+15551234567')
    phone2 = PhoneNumber('+1-555-123-4567')
    # These are equal (same digits)
"""

from dataclasses import dataclass
import re
from typing import Optional
from core.value_objects.base import (
    ValueObject,
    ValidationError,
    validate_not_empty,
)


@dataclass(frozen=True)
class PhoneNumber(ValueObject):
    """
    Represents a phone number.

    Phone numbers are stored in normalized format (digits only with optional + prefix)
    and can be formatted for display.

    Attributes:
        value: The normalized phone number (digits only with optional + prefix)

    Raises:
        ValidationError: If phone number format is invalid

    Examples:
        >>> phone = PhoneNumber('+15551234567')
        >>> str(phone)
        '+15551234567'

        >>> phone.format()
        '+1-555-123-4567'

        >>> phone.country_code
        '1'
    """

    value: str

    # Phone number validation regex (allows various formats)
    # Accepts: +1234567890, 1234567890, +1-234-567-890, etc.
    PHONE_REGEX = re.compile(r"^\+?[\d\s\-\(\)\.]+$")

    def __post_init__(self):
        """Validate phone number on creation."""
        # Check not empty
        validate_not_empty(self.value, "Phone number")

        # Remove whitespace for validation
        test_value = self.value.strip()

        # Validate format
        if not self.PHONE_REGEX.match(test_value):
            raise ValidationError(
                f"Invalid phone number format: '{test_value}'", field="phone_number"
            )

        # Normalize: keep only digits and +
        normalized = re.sub(r"[^\d+]", "", test_value)

        # Validate length (min 7, max 15 digits per E.164)
        digit_count = len(normalized.replace("+", ""))
        if digit_count < 7 or digit_count > 15:
            raise ValidationError(
                f"Phone number must have 7-15 digits (got {digit_count})",
                field="phone_number",
            )

        # Ensure + only at start
        if "+" in normalized and not normalized.startswith("+"):
            raise ValidationError(
                "'+' can only appear at the beginning", field="phone_number"
            )

        # Store normalized value
        object.__setattr__(self, "value", normalized)

    @property
    def digits(self) -> str:
        """
        Get phone number as digits only (no + sign).

        Returns:
            Phone number digits

        Examples:
            >>> PhoneNumber('+15551234567').digits
            '15551234567'
        """
        return self.value.replace("+", "")

    @property
    def country_code(self) -> Optional[str]:
        """
        Extract country code if present.

        Returns:
            Country code or None

        Examples:
            >>> PhoneNumber('+15551234567').country_code
            '1'
            >>> PhoneNumber('5551234567').country_code is None
            True
        """
        if not self.value.startswith("+"):
            return None

        # Common country code lengths: 1-3 digits
        digits = self.digits
        if len(digits) >= 10:  # Assume 1-digit country code for 10+ digit numbers
            return digits[0]
        elif len(digits) >= 9:  # Could be 2-digit country code
            return digits[:2]
        elif len(digits) >= 8:  # Could be 3-digit country code
            return digits[:3]
        else:
            return None

    def format(self, style: str = "international") -> str:
        """
        Format phone number for display.

        Args:
            style: Format style ('international', 'national', 'compact')

        Returns:
            Formatted phone number

        Examples:
            >>> phone = PhoneNumber('+15551234567')
            >>> phone.format('international')
            '+1-555-123-4567'

            >>> phone.format('national')
            '(555) 123-4567'

            >>> phone.format('compact')
            '+15551234567'
        """
        if style == "compact":
            return self.value

        digits = self.digits

        # Handle different lengths
        if len(digits) == 10:  # US number without country code
            if style == "international":
                return f"+1-{digits[0:3]}-{digits[3:6]}-{digits[6:]}"
            else:  # national
                return f"({digits[0:3]}) {digits[3:6]}-{digits[6:]}"

        elif len(digits) == 11:  # Number with country code
            if style == "international":
                return f"+{digits[0]}-{digits[1:4]}-{digits[4:7]}-{digits[7:]}"
            else:  # national (remove country code)
                return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"

        else:
            # Generic formatting
            if self.value.startswith("+"):
                return self.value
            else:
                return f"+{self.value}"

    def is_mobile(self) -> bool:
        """
        Heuristic check if number might be mobile.

        Note: This is a simplified heuristic and not reliable.
        Real implementation would need carrier database.

        Returns:
            Best guess if number is mobile

        Examples:
            >>> PhoneNumber('+15551234567').is_mobile()
            False  # Just a heuristic
        """
        # This is a placeholder - real implementation would check against
        # mobile number ranges for specific countries
        return True  # Default to True as most numbers today are mobile

    def __str__(self) -> str:
        """
        String representation.

        Returns:
            Normalized phone number

        Examples:
            >>> str(PhoneNumber('+1-555-123-4567'))
            '+15551234567'
        """
        return self.value

    def __repr__(self) -> str:
        """
        Developer-friendly representation.

        Returns:
            PhoneNumber representation

        Examples:
            >>> PhoneNumber('+15551234567')
            PhoneNumber('+15551234567')
        """
        return f"PhoneNumber('{self.value}')"

    @classmethod
    def from_parts(
        cls, area_code: str, exchange: str, number: str, country_code: str = "1"
    ) -> "PhoneNumber":
        """
        Create phone number from parts.

        Args:
            area_code: Area code (3 digits)
            exchange: Exchange (3 digits)
            number: Number (4 digits)
            country_code: Country code (default: '1' for US)

        Returns:
            PhoneNumber instance

        Examples:
            >>> phone = PhoneNumber.from_parts('555', '123', '4567')
            >>> phone.format()
            '+1-555-123-4567'
        """
        full_number = f"+{country_code}{area_code}{exchange}{number}"
        return cls(full_number)

    @classmethod
    def is_valid_phone(cls, phone: str) -> bool:
        """
        Check if string is a valid phone number without raising exception.

        Args:
            phone: String to validate

        Returns:
            True if valid phone number

        Examples:
            >>> PhoneNumber.is_valid_phone('+15551234567')
            True
            >>> PhoneNumber.is_valid_phone('invalid')
            False
        """
        try:
            cls(phone)
            return True
        except ValidationError:
            return False
