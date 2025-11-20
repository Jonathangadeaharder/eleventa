"""
Money Value Object

Represents a monetary amount with currency.

Money is a classic example of a Value Object. It's immutable,
compared by value, and provides operations that return new instances.

Usage:
    # Create money instances
    price = Money(Decimal('19.99'), 'USD')
    tax = Money(Decimal('2.00'), 'USD')

    # Arithmetic operations
    total = price.add(tax)  # Money(21.99, 'USD')
    discount = price.multiply(Decimal('0.1'))  # Money(1.999, 'USD')

    # Comparison
    if price > Money(Decimal('10.00'), 'USD'):
        print("Expensive")

    # Currency conversion (requires exchange rate)
    price_eur = price.convert_to('EUR', Decimal('0.85'))
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Union
from core.value_objects.base import ValueObject, ValidationError, validate_non_negative


@dataclass(frozen=True)
class Money(ValueObject):
    """
    Represents a monetary amount with currency.

    Attributes:
        amount: The monetary amount (must be non-negative)
        currency: ISO 4217 currency code (e.g., 'USD', 'EUR', 'ARS')

    Raises:
        ValidationError: If amount is negative or currency is invalid

    Examples:
        >>> price = Money(Decimal('19.99'), 'USD')
        >>> str(price)
        'USD 19.99'

        >>> total = price.add(Money(Decimal('5.00'), 'USD'))
        >>> total
        Money(amount=Decimal('24.99'), currency='USD')
    """

    amount: Decimal
    currency: str

    def __post_init__(self):
        """Validate money on creation."""
        # Ensure amount is Decimal
        if not isinstance(self.amount, Decimal):
            # Convert to Decimal if possible
            object.__setattr__(self, 'amount', Decimal(str(self.amount)))

        # Validate amount
        validate_non_negative(self.amount, "Amount")

        # Validate currency
        if not self.currency or not isinstance(self.currency, str):
            raise ValidationError("Currency must be a non-empty string", field="currency")

        # Normalize currency to uppercase
        object.__setattr__(self, 'currency', self.currency.upper())

        # Validate currency code format (3 letters)
        if len(self.currency) != 3 or not self.currency.isalpha():
            raise ValidationError(
                f"Currency must be a 3-letter ISO code (got '{self.currency}')",
                field="currency"
            )

    def add(self, other: 'Money') -> 'Money':
        """
        Add two money amounts.

        Args:
            other: Money to add

        Returns:
            New Money instance with sum

        Raises:
            ValidationError: If currencies don't match

        Examples:
            >>> price = Money(Decimal('10'), 'USD')
            >>> tax = Money(Decimal('2'), 'USD')
            >>> total = price.add(tax)
            >>> total.amount
            Decimal('12')
        """
        self._assert_same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def subtract(self, other: 'Money') -> 'Money':
        """
        Subtract money amount.

        Args:
            other: Money to subtract

        Returns:
            New Money instance with difference

        Raises:
            ValidationError: If currencies don't match or result is negative

        Examples:
            >>> price = Money(Decimal('10'), 'USD')
            >>> discount = Money(Decimal('2'), 'USD')
            >>> final = price.subtract(discount)
            >>> final.amount
            Decimal('8')
        """
        self._assert_same_currency(other)
        result = self.amount - other.amount
        if result < 0:
            raise ValidationError(
                f"Cannot subtract {other.amount} from {self.amount}: result would be negative"
            )
        return Money(result, self.currency)

    def multiply(self, multiplier: Union[Decimal, int, float]) -> 'Money':
        """
        Multiply money by a scalar.

        Args:
            multiplier: Scalar value to multiply by

        Returns:
            New Money instance with product

        Examples:
            >>> price = Money(Decimal('10'), 'USD')
            >>> double = price.multiply(2)
            >>> double.amount
            Decimal('20')

            >>> with_tax = price.multiply(Decimal('1.08'))
            >>> with_tax.amount
            Decimal('10.80')
        """
        if not isinstance(multiplier, Decimal):
            multiplier = Decimal(str(multiplier))

        return Money(self.amount * multiplier, self.currency)

    def divide(self, divisor: Union[Decimal, int, float]) -> 'Money':
        """
        Divide money by a scalar.

        Args:
            divisor: Scalar value to divide by

        Returns:
            New Money instance with quotient

        Raises:
            ValidationError: If divisor is zero

        Examples:
            >>> price = Money(Decimal('10'), 'USD')
            >>> half = price.divide(2)
            >>> half.amount
            Decimal('5')
        """
        if not isinstance(divisor, Decimal):
            divisor = Decimal(str(divisor))

        if divisor == 0:
            raise ValidationError("Cannot divide by zero")

        return Money(self.amount / divisor, self.currency)

    def round(self, decimal_places: int = 2) -> 'Money':
        """
        Round money to specified decimal places.

        Args:
            decimal_places: Number of decimal places (default: 2)

        Returns:
            New Money instance with rounded amount

        Examples:
            >>> price = Money(Decimal('10.556'), 'USD')
            >>> rounded = price.round(2)
            >>> rounded.amount
            Decimal('10.56')
        """
        from decimal import ROUND_HALF_UP

        rounded_amount = self.amount.quantize(
            Decimal(10) ** -decimal_places,
            rounding=ROUND_HALF_UP
        )
        return Money(rounded_amount, self.currency)

    def allocate(self, ratios: list[Union[int, Decimal]]) -> list['Money']:
        """
        Allocate money according to ratios.

        This is useful for splitting amounts (e.g., split bill among people).
        Ensures no money is lost due to rounding.

        Args:
            ratios: List of ratios to split by

        Returns:
            List of Money instances

        Examples:
            >>> total = Money(Decimal('100'), 'USD')
            >>> # Split equally among 3 people
            >>> shares = total.allocate([1, 1, 1])
            >>> [s.amount for s in shares]
            [Decimal('33.34'), Decimal('33.33'), Decimal('33.33')]
        """
        if not ratios:
            raise ValidationError("At least one ratio is required")

        # Convert all ratios to Decimal
        ratios = [Decimal(str(r)) for r in ratios]
        total_ratio = sum(ratios)

        if total_ratio == 0:
            raise ValidationError("Sum of ratios cannot be zero")

        # Calculate shares
        remainder = self.amount
        results = []

        for ratio in ratios[:-1]:
            share = (self.amount * ratio / total_ratio).quantize(
                Decimal('0.01')
            )
            results.append(Money(share, self.currency))
            remainder -= share

        # Last share gets the remainder to avoid rounding errors
        results.append(Money(remainder, self.currency))

        return results

    def convert_to(self, target_currency: str, exchange_rate: Decimal) -> 'Money':
        """
        Convert money to another currency.

        Args:
            target_currency: Target currency code
            exchange_rate: Exchange rate to target currency

        Returns:
            New Money instance in target currency

        Examples:
            >>> usd = Money(Decimal('100'), 'USD')
            >>> # Convert USD to EUR at rate 0.85
            >>> eur = usd.convert_to('EUR', Decimal('0.85'))
            >>> eur.amount
            Decimal('85')
        """
        if not isinstance(exchange_rate, Decimal):
            exchange_rate = Decimal(str(exchange_rate))

        validate_non_negative(exchange_rate, "Exchange rate")

        converted_amount = self.amount * exchange_rate
        return Money(converted_amount, target_currency)

    def is_zero(self) -> bool:
        """
        Check if amount is zero.

        Returns:
            True if amount is zero

        Examples:
            >>> Money(Decimal('0'), 'USD').is_zero()
            True
            >>> Money(Decimal('0.01'), 'USD').is_zero()
            False
        """
        return self.amount == 0

    def is_positive(self) -> bool:
        """
        Check if amount is positive.

        Returns:
            True if amount is positive

        Examples:
            >>> Money(Decimal('10'), 'USD').is_positive()
            True
            >>> Money(Decimal('0'), 'USD').is_positive()
            False
        """
        return self.amount > 0

    # Comparison operators

    def __lt__(self, other: 'Money') -> bool:
        """Less than comparison."""
        self._assert_same_currency(other)
        return self.amount < other.amount

    def __le__(self, other: 'Money') -> bool:
        """Less than or equal comparison."""
        self._assert_same_currency(other)
        return self.amount <= other.amount

    def __gt__(self, other: 'Money') -> bool:
        """Greater than comparison."""
        self._assert_same_currency(other)
        return self.amount > other.amount

    def __ge__(self, other: 'Money') -> bool:
        """Greater than or equal comparison."""
        self._assert_same_currency(other)
        return self.amount >= other.amount

    # String representation

    def __str__(self) -> str:
        """
        String representation.

        Examples:
            >>> str(Money(Decimal('19.99'), 'USD'))
            'USD 19.99'
        """
        return f"{self.currency} {self.amount}"

    def __repr__(self) -> str:
        """
        Developer-friendly representation.

        Examples:
            >>> Money(Decimal('19.99'), 'USD')
            Money(amount=Decimal('19.99'), currency='USD')
        """
        return f"Money(amount={self.amount!r}, currency={self.currency!r})"

    # Helper methods

    def _assert_same_currency(self, other: 'Money') -> None:
        """
        Assert that two Money instances have the same currency.

        Args:
            other: Money instance to compare

        Raises:
            ValidationError: If currencies don't match
        """
        if self.currency != other.currency:
            raise ValidationError(
                f"Cannot operate on different currencies: {self.currency} vs {other.currency}"
            )

    @classmethod
    def zero(cls, currency: str) -> 'Money':
        """
        Create a zero money amount.

        Args:
            currency: Currency code

        Returns:
            Money instance with zero amount

        Examples:
            >>> zero_usd = Money.zero('USD')
            >>> zero_usd.amount
            Decimal('0')
        """
        return cls(Decimal('0'), currency)

    @classmethod
    def from_float(cls, amount: float, currency: str) -> 'Money':
        """
        Create Money from float (not recommended for precision).

        Args:
            amount: Float amount
            currency: Currency code

        Returns:
            Money instance

        Warning:
            Using floats for money can lead to precision errors.
            Prefer using Decimal or string amounts.

        Examples:
            >>> money = Money.from_float(19.99, 'USD')
            >>> money.amount
            Decimal('19.99')
        """
        return cls(Decimal(str(amount)), currency)

    @classmethod
    def from_string(cls, amount: str, currency: str) -> 'Money':
        """
        Create Money from string amount.

        Args:
            amount: String representation of amount
            currency: Currency code

        Returns:
            Money instance

        Examples:
            >>> money = Money.from_string('19.99', 'USD')
            >>> money.amount
            Decimal('19.99')
        """
        return cls(Decimal(amount), currency)
