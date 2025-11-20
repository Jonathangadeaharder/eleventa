"""
Value Objects Module

Value Objects are immutable objects that represent concepts through their
attributes rather than identity. They are a core pattern in Domain-Driven Design.

Key Characteristics:
- Immutable (cannot be changed after creation)
- Equality by value (not identity)
- Self-validating (enforce invariants)
- Side-effect free (operations return new instances)
- Replaceable (can be swapped with another equal instance)

Available Value Objects:
- Money: Represents currency amounts
- Address: Represents physical addresses
- Email: Represents email addresses
- PhoneNumber: Represents phone numbers
- TaxId: Represents tax identification numbers (CUIT)
- ProductCode: Represents product codes
- Percentage: Represents percentage values

Usage:
    from core.value_objects import Money, Email, Address

    # Create value objects
    price = Money(Decimal('19.99'), 'USD')
    email = Email('customer@example.com')
    address = Address(
        street='123 Main St',
        city='Springfield',
        state='IL',
        postal_code='62701',
        country='USA'
    )

    # Value objects are immutable
    # price.amount = Decimal('29.99')  # This would raise an error

    # Equality by value
    price1 = Money(Decimal('19.99'), 'USD')
    price2 = Money(Decimal('19.99'), 'USD')
    assert price1 == price2  # True - same value

    # Operations return new instances
    total = price.add(Money(Decimal('5.00'), 'USD'))
    assert total == Money(Decimal('24.99'), 'USD')
"""

from core.value_objects.base import ValueObject
from core.value_objects.money import Money
from core.value_objects.address import Address
from core.value_objects.email import Email
from core.value_objects.phone_number import PhoneNumber
from core.value_objects.tax_id import TaxId
from core.value_objects.product_code import ProductCode
from core.value_objects.percentage import Percentage

__all__ = [
    "ValueObject",
    "Money",
    "Address",
    "Email",
    "PhoneNumber",
    "TaxId",
    "ProductCode",
    "Percentage",
]
