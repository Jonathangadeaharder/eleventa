"""
Percentage Value Object

Represents a percentage value with validation and operations.

Percentages are value objects that encapsulate percentage calculations
and ensure validity.

Usage:
    # Create percentage
    tax_rate = Percentage(Decimal('8.25'))  # 8.25%
    discount = Percentage(Decimal('15'))    # 15%

    # Apply to amounts
    tax = tax_rate.of(Money(Decimal('100'), 'USD'))
    # Returns Money(Decimal('8.25'), 'USD')

    # Arithmetic
    total_rate = tax_rate.add(Percentage(Decimal('2')))
    # Returns Percentage(Decimal('10.25'))
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Union
from core.value_objects.base import ValueObject, ValidationError, validate_range


@dataclass(frozen=True)
class Percentage(ValueObject):
    """
    Represents a percentage value.

    Internally stores percentage as a decimal number (e.g., 8.5 for 8.5%).
    Can be used for tax rates, discounts, interest rates, etc.

    Attributes:
        value: The percentage value (0-100)

    Raises:
        ValidationError: If percentage is outside valid range

    Examples:
        >>> tax = Percentage(Decimal('8.25'))
        >>> str(tax)
        '8.25%'

        >>> tax.as_decimal()
        Decimal('0.0825')

        >>> from core.value_objects import Money
        >>> price = Money(Decimal('100'), 'USD')
        >>> tax_amount = tax.of(price)
        >>> tax_amount.amount
        Decimal('8.25')
    """

    value: Decimal

    def __post_init__(self):
        """Validate percentage on creation."""
        # Ensure value is Decimal
        if not isinstance(self.value, Decimal):
            object.__setattr__(self, "value", Decimal(str(self.value)))

        # Validate range (0-100)
        validate_range(self.value, Decimal("0"), Decimal("100"), "Percentage")

    def as_decimal(self) -> Decimal:
        """
        Convert percentage to decimal form.

        Returns:
            Percentage as decimal (e.g., 8.5% -> 0.085)

        Examples:
            >>> Percentage(Decimal('8.5')).as_decimal()
            Decimal('0.085')

            >>> Percentage(Decimal('100')).as_decimal()
            Decimal('1.0')
        """
        return self.value / Decimal("100")

    def as_fraction(self) -> str:
        """
        Express percentage as a fraction string.

        Returns:
            Fraction representation

        Examples:
            >>> Percentage(Decimal('50')).as_fraction()
            '1/2'

            >>> Percentage(Decimal('25')).as_fraction()
            '1/4'
        """
        from fractions import Fraction

        # Convert to fraction
        frac = Fraction(float(self.as_decimal())).limit_denominator(100)
        return f"{frac.numerator}/{frac.denominator}"

    def of(self, amount):
        """
        Calculate percentage of an amount.

        Args:
            amount: Amount to calculate percentage of
                   Can be Decimal, int, float, or Money

        Returns:
            Result in same type as input

        Examples:
            >>> Percentage(Decimal('10')).of(Decimal('100'))
            Decimal('10')

            >>> from core.value_objects import Money
            >>> tax = Percentage(Decimal('8.5'))
            >>> price = Money(Decimal('100'), 'USD')
            >>> tax.of(price)
            Money(amount=Decimal('8.5'), currency='USD')
        """
        # Handle Money value objects
        if hasattr(amount, "multiply"):
            return amount.multiply(self.as_decimal())

        # Handle numeric values
        if isinstance(amount, (int, float)):
            amount = Decimal(str(amount))

        return amount * self.as_decimal()

    def add_to(self, amount):
        """
        Add percentage to amount (amount + percentage of amount).

        Args:
            amount: Base amount

        Returns:
            Amount plus percentage

        Examples:
            >>> Percentage(Decimal('10')).add_to(Decimal('100'))
            Decimal('110')

            >>> from core.value_objects import Money
            >>> tax = Percentage(Decimal('8'))
            >>> price = Money(Decimal('100'), 'USD')
            >>> tax.add_to(price)
            Money(amount=Decimal('108'), currency='USD')
        """
        # Handle Money value objects
        if hasattr(amount, "add") and hasattr(amount, "multiply"):
            return amount.add(amount.multiply(self.as_decimal()))

        # Handle numeric values
        if isinstance(amount, (int, float)):
            amount = Decimal(str(amount))

        return amount + (amount * self.as_decimal())

    def subtract_from(self, amount):
        """
        Subtract percentage from amount (amount - percentage of amount).

        Args:
            amount: Base amount

        Returns:
            Amount minus percentage

        Examples:
            >>> Percentage(Decimal('10')).subtract_from(Decimal('100'))
            Decimal('90')

            >>> from core.value_objects import Money
            >>> discount = Percentage(Decimal('20'))
            >>> price = Money(Decimal('100'), 'USD')
            >>> discount.subtract_from(price)
            Money(amount=Decimal('80'), currency='USD')
        """
        # Handle Money value objects
        if hasattr(amount, "subtract") and hasattr(amount, "multiply"):
            return amount.subtract(amount.multiply(self.as_decimal()))

        # Handle numeric values
        if isinstance(amount, (int, float)):
            amount = Decimal(str(amount))

        return amount - (amount * self.as_decimal())

    def add(self, other: "Percentage") -> "Percentage":
        """
        Add two percentages.

        Args:
            other: Percentage to add

        Returns:
            Sum of percentages

        Raises:
            ValidationError: If result exceeds 100%

        Examples:
            >>> p1 = Percentage(Decimal('8'))
            >>> p2 = Percentage(Decimal('2'))
            >>> p1.add(p2)
            Percentage(value=Decimal('10'))
        """
        result = self.value + other.value
        if result > 100:
            raise ValidationError(f"Percentage sum cannot exceed 100% (got {result}%)")
        return Percentage(result)

    def subtract(self, other: "Percentage") -> "Percentage":
        """
        Subtract percentage.

        Args:
            other: Percentage to subtract

        Returns:
            Difference of percentages

        Raises:
            ValidationError: If result is negative

        Examples:
            >>> p1 = Percentage(Decimal('10'))
            >>> p2 = Percentage(Decimal('3'))
            >>> p1.subtract(p2)
            Percentage(value=Decimal('7'))
        """
        result = self.value - other.value
        if result < 0:
            raise ValidationError(f"Percentage cannot be negative (got {result}%)")
        return Percentage(result)

    def multiply(self, multiplier: Union[Decimal, int, float]) -> "Percentage":
        """
        Multiply percentage by scalar.

        Args:
            multiplier: Scalar to multiply by

        Returns:
            Result percentage

        Raises:
            ValidationError: If result exceeds 100%

        Examples:
            >>> Percentage(Decimal('5')).multiply(2)
            Percentage(value=Decimal('10'))
        """
        if not isinstance(multiplier, Decimal):
            multiplier = Decimal(str(multiplier))

        result = self.value * multiplier
        if result > 100:
            raise ValidationError(f"Percentage cannot exceed 100% (got {result}%)")
        return Percentage(result)

    def is_zero(self) -> bool:
        """
        Check if percentage is zero.

        Returns:
            True if zero

        Examples:
            >>> Percentage(Decimal('0')).is_zero()
            True
            >>> Percentage(Decimal('1')).is_zero()
            False
        """
        return self.value == 0

    def is_full(self) -> bool:
        """
        Check if percentage is 100%.

        Returns:
            True if 100%

        Examples:
            >>> Percentage(Decimal('100')).is_full()
            True
            >>> Percentage(Decimal('50')).is_full()
            False
        """
        return self.value == 100

    # Comparison operators

    def __lt__(self, other: "Percentage") -> bool:
        """Less than comparison."""
        return self.value < other.value

    def __le__(self, other: "Percentage") -> bool:
        """Less than or equal comparison."""
        return self.value <= other.value

    def __gt__(self, other: "Percentage") -> bool:
        """Greater than comparison."""
        return self.value > other.value

    def __ge__(self, other: "Percentage") -> bool:
        """Greater than or equal comparison."""
        return self.value >= other.value

    # String representation

    def __str__(self) -> str:
        """
        String representation.

        Returns:
            Percentage with % symbol

        Examples:
            >>> str(Percentage(Decimal('8.25')))
            '8.25%'
        """
        return f"{self.value}%"

    def __repr__(self) -> str:
        """
        Developer-friendly representation.

        Returns:
            Percentage representation

        Examples:
            >>> Percentage(Decimal('8.25'))
            Percentage(value=Decimal('8.25'))
        """
        return f"Percentage(value={self.value!r})"

    @classmethod
    def zero(cls) -> "Percentage":
        """
        Create zero percentage.

        Returns:
            Percentage of 0%

        Examples:
            >>> Percentage.zero()
            Percentage(value=Decimal('0'))
        """
        return cls(Decimal("0"))

    @classmethod
    def full(cls) -> "Percentage":
        """
        Create 100% percentage.

        Returns:
            Percentage of 100%

        Examples:
            >>> Percentage.full()
            Percentage(value=Decimal('100'))
        """
        return cls(Decimal("100"))

    @classmethod
    def from_decimal(cls, decimal_value: Union[Decimal, float]) -> "Percentage":
        """
        Create percentage from decimal form.

        Args:
            decimal_value: Decimal form (e.g., 0.085 for 8.5%)

        Returns:
            Percentage instance

        Examples:
            >>> Percentage.from_decimal(0.085)
            Percentage(value=Decimal('8.5'))

            >>> Percentage.from_decimal(Decimal('0.5'))
            Percentage(value=Decimal('50'))
        """
        if not isinstance(decimal_value, Decimal):
            decimal_value = Decimal(str(decimal_value))

        percentage_value = decimal_value * Decimal("100")
        return cls(percentage_value)

    @classmethod
    def from_ratio(
        cls, numerator: Union[int, Decimal], denominator: Union[int, Decimal]
    ) -> "Percentage":
        """
        Create percentage from ratio.

        Args:
            numerator: Numerator
            denominator: Denominator

        Returns:
            Percentage instance

        Examples:
            >>> Percentage.from_ratio(1, 4)
            Percentage(value=Decimal('25'))

            >>> Percentage.from_ratio(3, 8)
            Percentage(value=Decimal('37.5'))
        """
        if denominator == 0:
            raise ValidationError("Denominator cannot be zero")

        if not isinstance(numerator, Decimal):
            numerator = Decimal(str(numerator))
        if not isinstance(denominator, Decimal):
            denominator = Decimal(str(denominator))

        percentage_value = (numerator / denominator) * Decimal("100")
        return cls(percentage_value)
