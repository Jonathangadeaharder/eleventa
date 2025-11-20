"""
Address Value Object

Represents a physical address.

Addresses are value objects because two addresses with the same
values are considered equal, regardless of which customer they belong to.

Usage:
    address = Address(
        street='123 Main Street',
        city='Springfield',
        state='IL',
        postal_code='62701',
        country='USA'
    )

    # Immutable
    # address.street = '456 Oak Ave'  # Error!

    # Equality by value
    addr1 = Address('123 Main St', 'Springfield', 'IL', '62701', 'USA')
    addr2 = Address('123 Main St', 'Springfield', 'IL', '62701', 'USA')
    assert addr1 == addr2  # True
"""

from dataclasses import dataclass
from typing import Optional
from core.value_objects.base import (
    ValueObject,
    validate_not_empty,
    validate_length,
)


@dataclass(frozen=True)
class Address(ValueObject):
    """
    Represents a physical address.

    Attributes:
        street: Street address (required)
        city: City name (required)
        state: State/Province (optional)
        postal_code: Postal/ZIP code (required)
        country: Country name or code (required)
        apartment: Apartment/unit number (optional)

    Raises:
        ValidationError: If any required field is empty

    Examples:
        >>> address = Address(
        ...     street='123 Main St',
        ...     city='Springfield',
        ...     state='IL',
        ...     postal_code='62701',
        ...     country='USA'
        ... )
        >>> str(address)
        '123 Main St, Springfield, IL 62701, USA'
    """

    street: str
    city: str
    postal_code: str
    country: str
    state: Optional[str] = None
    apartment: Optional[str] = None

    def __post_init__(self):
        """Validate address on creation."""
        # Validate required fields
        validate_not_empty(self.street, "Street")
        validate_not_empty(self.city, "City")
        validate_not_empty(self.postal_code, "Postal code")
        validate_not_empty(self.country, "Country")

        # Validate field lengths
        validate_length(self.street, 1, 200, "Street")
        validate_length(self.city, 1, 100, "City")
        validate_length(self.postal_code, 1, 20, "Postal code")
        validate_length(self.country, 2, 100, "Country")

        if self.state:
            validate_length(self.state, 1, 100, "State")

        if self.apartment:
            validate_length(self.apartment, 1, 50, "Apartment")

        # Normalize fields
        object.__setattr__(self, "street", self.street.strip())
        object.__setattr__(self, "city", self.city.strip())
        object.__setattr__(self, "postal_code", self.postal_code.strip())
        object.__setattr__(self, "country", self.country.strip())

        if self.state:
            object.__setattr__(self, "state", self.state.strip())

        if self.apartment:
            object.__setattr__(self, "apartment", self.apartment.strip())

    def __str__(self) -> str:
        """
        Format address as a single line.

        Returns:
            Formatted address string

        Examples:
            >>> address = Address('123 Main St', 'Springfield', 'IL', '62701', 'USA')
            >>> str(address)
            '123 Main St, Springfield, IL 62701, USA'
        """
        parts = [self.street]

        if self.apartment:
            parts[0] = f"{self.street}, Apt {self.apartment}"

        parts.append(self.city)

        if self.state:
            parts.append(self.state)

        parts.append(self.postal_code)
        parts.append(self.country)

        return ", ".join(parts)

    def to_multiline(self) -> str:
        """
        Format address as multiple lines.

        Returns:
            Multiline formatted address

        Examples:
            >>> address = Address('123 Main St', 'Springfield', 'IL', '62701', 'USA')
            >>> print(address.to_multiline())
            123 Main St
            Springfield, IL 62701
            USA
        """
        lines = []

        # Line 1: Street + Apartment
        if self.apartment:
            lines.append(f"{self.street}, Apt {self.apartment}")
        else:
            lines.append(self.street)

        # Line 2: City, State ZIP
        city_line = self.city
        if self.state:
            city_line += f", {self.state}"
        city_line += f" {self.postal_code}"
        lines.append(city_line)

        # Line 3: Country
        lines.append(self.country)

        return "\n".join(lines)

    def is_in_country(self, country: str) -> bool:
        """
        Check if address is in specified country.

        Args:
            country: Country name or code to check

        Returns:
            True if address is in country

        Examples:
            >>> address = Address('123 Main St', 'Springfield', 'IL', '62701', 'USA')
            >>> address.is_in_country('USA')
            True
            >>> address.is_in_country('Canada')
            False
        """
        return self.country.upper() == country.upper()

    def is_in_state(self, state: str) -> bool:
        """
        Check if address is in specified state.

        Args:
            state: State name or code to check

        Returns:
            True if address is in state

        Examples:
            >>> address = Address('123 Main St', 'Springfield', 'IL', '62701', 'USA')
            >>> address.is_in_state('IL')
            True
            >>> address.is_in_state('California')
            False
        """
        if not self.state:
            return False
        return self.state.upper() == state.upper()

    def is_in_city(self, city: str) -> bool:
        """
        Check if address is in specified city.

        Args:
            city: City name to check

        Returns:
            True if address is in city

        Examples:
            >>> address = Address('123 Main St', 'Springfield', 'IL', '62701', 'USA')
            >>> address.is_in_city('Springfield')
            True
        """
        return self.city.upper() == city.upper()

    @classmethod
    def create_simple(
        cls, street: str, city: str, postal_code: str, country: str = "USA"
    ) -> "Address":
        """
        Create a simple address without state/apartment.

        Args:
            street: Street address
            city: City name
            postal_code: Postal code
            country: Country (default: USA)

        Returns:
            Address instance

        Examples:
            >>> address = Address.create_simple(
            ...     '123 Main St',
            ...     'Springfield',
            ...     '62701'
            ... )
            >>> address.country
            'USA'
        """
        return cls(
            street=street,
            city=city,
            postal_code=postal_code,
            country=country,
            state=None,
            apartment=None,
        )
