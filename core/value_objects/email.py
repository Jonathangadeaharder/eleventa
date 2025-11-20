"""
Email Value Object

Represents an email address with validation.

Email addresses are value objects because they're immutable and
compared by value. Two Email('john@example.com') are equal.

Usage:
    email = Email('customer@example.com')

    # Validation happens on creation
    try:
        bad_email = Email('invalid-email')  # Raises ValidationError
    except ValidationError as e:
        print(e.message)

    # Equality by value
    email1 = Email('john@example.com')
    email2 = Email('john@example.com')
    assert email1 == email2  # True
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
class Email(ValueObject):
    """
    Represents an email address.

    Attributes:
        value: The email address string

    Raises:
        ValidationError: If email format is invalid

    Examples:
        >>> email = Email('customer@example.com')
        >>> str(email)
        'customer@example.com'

        >>> email.domain
        'example.com'

        >>> email.local_part
        'customer'
    """

    value: str

    # Email validation regex (simplified but reasonable)
    EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    def __post_init__(self):
        """Validate email on creation."""
        # Check not empty
        validate_not_empty(self.value, "Email")

        # Normalize to lowercase
        normalized = self.value.strip().lower()
        object.__setattr__(self, "value", normalized)

        # Check length
        validate_length(self.value, 3, 254, "Email")

        # Validate format
        if not self.EMAIL_REGEX.match(self.value):
            raise ValidationError(
                f"Invalid email format: '{self.value}'", field="email"
            )

        # Additional validations
        local, domain = self.value.rsplit("@", 1)

        if len(local) > 64:
            raise ValidationError(
                "Email local part cannot exceed 64 characters", field="email"
            )

        if ".." in self.value:
            raise ValidationError(
                "Email cannot contain consecutive dots", field="email"
            )

    @property
    def local_part(self) -> str:
        """
        Get the local part of the email (before @).

        Returns:
            Local part of email

        Examples:
            >>> Email('john.doe@example.com').local_part
            'john.doe'
        """
        return self.value.split("@")[0]

    @property
    def domain(self) -> str:
        """
        Get the domain part of the email (after @).

        Returns:
            Domain part of email

        Examples:
            >>> Email('john@example.com').domain
            'example.com'
        """
        return self.value.split("@")[1]

    def is_from_domain(self, domain: str) -> bool:
        """
        Check if email is from specified domain.

        Args:
            domain: Domain to check

        Returns:
            True if email is from domain

        Examples:
            >>> email = Email('john@example.com')
            >>> email.is_from_domain('example.com')
            True
            >>> email.is_from_domain('other.com')
            False
        """
        return self.domain.lower() == domain.lower()

    def obfuscate(self) -> str:
        """
        Obfuscate email for display (privacy).

        Returns:
            Obfuscated email string

        Examples:
            >>> Email('john.doe@example.com').obfuscate()
            'j***e@example.com'

            >>> Email('a@example.com').obfuscate()
            'a***@example.com'
        """
        local = self.local_part
        if len(local) <= 2:
            return f"{local[0]}***@{self.domain}"
        else:
            return f"{local[0]}***{local[-1]}@{self.domain}"

    def __str__(self) -> str:
        """
        String representation.

        Returns:
            Email address string

        Examples:
            >>> str(Email('john@example.com'))
            'john@example.com'
        """
        return self.value

    def __repr__(self) -> str:
        """
        Developer-friendly representation.

        Returns:
            Email representation

        Examples:
            >>> Email('john@example.com')
            Email('john@example.com')
        """
        return f"Email('{self.value}')"

    @classmethod
    def is_valid_email(cls, email: str) -> bool:
        """
        Check if string is a valid email without raising exception.

        Args:
            email: String to validate

        Returns:
            True if valid email format

        Examples:
            >>> Email.is_valid_email('john@example.com')
            True
            >>> Email.is_valid_email('invalid-email')
            False
        """
        try:
            cls(email)
            return True
        except ValidationError:
            return False
