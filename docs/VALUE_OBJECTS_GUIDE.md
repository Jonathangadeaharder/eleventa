# Value Objects Guide

## Table of Contents
1. [Overview](#overview)
2. [What are Value Objects?](#what-are-value-objects)
3. [Value Objects vs Entities](#value-objects-vs-entities)
4. [Creating Value Objects](#creating-value-objects)
5. [Available Value Objects](#available-value-objects)
6. [Usage Examples](#usage-examples)
7. [Best Practices](#best-practices)
8. [Testing](#testing)
9. [Integration](#integration)

## Overview

**Value Objects** are a fundamental pattern in Domain-Driven Design that represent concepts through their attributes rather than identity. They are immutable, self-validating, and compared by value.

### Key Benefits

- **Type Safety**: Catch errors at compile time
- **Immutability**: Cannot be changed after creation
- **Self-Validating**: Business rules enforced at creation
- **Expressive**: Code reads like business language
- **Testable**: Easy to unit test
- **Reusable**: Use same value object across domain

### When to Use

✅ **Use Value Objects For:**
- Money amounts (price, tax, total)
- Contact information (email, phone, address)
- Identification numbers (tax ID, product code)
- Measurements (percentage, weight, distance)
- Dates and time periods
- Concepts identified by attributes, not identity

❌ **Don't Use Value Objects For:**
- Entities with identity (Customer, Product, Sale)
- Mutable state
- Large complex objects with behavior
- Objects that need to be tracked over time

## What are Value Objects?

### Characteristics

1. **Immutable**: Cannot be modified after creation
2. **Value Equality**: Two objects with same values are equal
3. **Self-Validating**: Enforces invariants on creation
4. **Side-Effect Free**: Operations return new instances
5. **Replaceable**: Can swap with another equal instance

### Example: Money

```python
# Traditional approach (primitive obsession)
price = 19.99  # What currency? Can be negative?
tax = 2.00
total = price + tax  # Float precision issues!

# Value Object approach
price = Money(Decimal('19.99'), 'USD')
tax = Money(Decimal('2.00'), 'USD')
total = price.add(tax)  # Type-safe, validated, precise
```

## Value Objects vs Entities

### Entities
- **Identity-based**: Tracked by unique ID
- **Mutable**: Can change over time
- **Lifecycle**: Created, modified, deleted
- **Example**: Customer, Product, Sale

```python
# Entities - same ID = same object
customer1 = Customer(id=123, name="John")
customer2 = Customer(id=123, name="John Doe")  # Still same customer!
assert customer1 == customer2  # True (same ID)
```

### Value Objects
- **Value-based**: Identified by attributes
- **Immutable**: Cannot change
- **No lifecycle**: Just values
- **Example**: Money, Email, Address

```python
# Value Objects - same values = same object
email1 = Email('john@example.com')
email2 = Email('john@example.com')
assert email1 == email2  # True (same value)
assert email1 is not email2  # Different instances, same value
```

## Creating Value Objects

### Basic Structure

```python
from dataclasses import dataclass
from decimal import Decimal
from core.value_objects.base import ValueObject, ValidationError

@dataclass(frozen=True)  # frozen=True makes it immutable
class Money(ValueObject):
    """Represents a monetary amount."""

    amount: Decimal
    currency: str

    def __post_init__(self):
        """Validate on creation."""
        if self.amount < 0:
            raise ValidationError("Amount cannot be negative")
        if not self.currency:
            raise ValidationError("Currency is required")

        # Normalize
        object.__setattr__(self, 'currency', self.currency.upper())

    def add(self, other: 'Money') -> 'Money':
        """Add money - returns NEW instance."""
        if self.currency != other.currency:
            raise ValidationError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)
```

### Key Points

1. **Use `@dataclass(frozen=True)`**: Provides immutability
2. **Validate in `__post_init__`**: Enforce business rules
3. **Return new instances**: Never modify self
4. **Use `object.__setattr__`**: To set attributes in frozen dataclass
5. **Provide meaningful operations**: Make usage natural

## Available Value Objects

### 1. Money

Represents monetary amounts with currency.

```python
from core.value_objects import Money
from decimal import Decimal

# Create money
price = Money(Decimal('19.99'), 'USD')
tax = Money(Decimal('2.00'), 'USD')

# Arithmetic
total = price.add(tax)  # Money(21.99, 'USD')
discount = price.multiply(Decimal('0.1'))  # Money(1.999, 'USD')

# Comparison
if price > Money(Decimal('10'), 'USD'):
    print("Expensive")

# Allocation (split bills)
bill = Money(Decimal('100'), 'USD')
shares = bill.allocate([1, 1, 1])  # Split 3 ways
# [Money(33.34), Money(33.33), Money(33.33)]

# Currency conversion
eur = price.convert_to('EUR', Decimal('0.85'))
```

**Features:**
- Precision with Decimal
- Currency validation
- Safe arithmetic
- Money allocation (no rounding errors)
- Comparison operators

### 2. Address

Represents physical addresses.

```python
from core.value_objects import Address

# Create address
address = Address(
    street='123 Main Street',
    city='Springfield',
    state='IL',
    postal_code='62701',
    country='USA',
    apartment='Apt 4B'  # optional
)

# Display
print(str(address))
# "123 Main Street, Apt 4B, Springfield, IL 62701, USA"

print(address.to_multiline())
# 123 Main Street, Apt 4B
# Springfield, IL 62701
# USA

# Queries
if address.is_in_country('USA'):
    print("Domestic address")

if address.is_in_state('IL'):
    print("Illinois address")
```

**Features:**
- Multiline formatting
- Location queries
- Validation
- Normalization

### 3. Email

Represents email addresses with validation.

```python
from core.value_objects import Email

# Create and validate
email = Email('customer@example.com')

# Access parts
print(email.local_part)  # 'customer'
print(email.domain)      # 'example.com'

# Queries
if email.is_from_domain('example.com'):
    print("Internal email")

# Privacy
print(email.obfuscate())  # 'c******r@example.com'

# Validation without exception
if Email.is_valid_email('test@example.com'):
    email = Email('test@example.com')
```

**Features:**
- RFC-compliant validation
- Domain extraction
- Obfuscation for privacy
- Normalization (lowercase)

### 4. PhoneNumber

Represents phone numbers.

```python
from core.value_objects import PhoneNumber

# Create (accepts various formats)
phone = PhoneNumber('+1-555-123-4567')
phone = PhoneNumber('555-123-4567')
phone = PhoneNumber('(555) 123-4567')

# Formatting
print(phone.format('international'))  # '+1-555-123-4567'
print(phone.format('national'))       # '(555) 123-4567'
print(phone.format('compact'))        # '+15551234567'

# Access parts
print(phone.digits)        # '15551234567'
print(phone.country_code)  # '1'

# Create from parts
phone = PhoneNumber.from_parts('555', '123', '4567', country_code='1')
```

**Features:**
- Flexible input formats
- Multiple display formats
- Normalization
- Country code extraction

### 5. TaxId (CUIT)

Represents Argentine tax identification numbers.

```python
from core.value_objects import TaxId

# Create with validation
cuit = TaxId('20-12345678-9')

# Access parts
print(cuit.type_code)        # '20'
print(cuit.document_number)  # '12345678'
print(cuit.check_digit)      # '9'

# Format
print(cuit.format())      # '20-12345678-9'
print(cuit.format('/'))   # '20/12345678/9'

# Type checking
if cuit.is_person():
    print("Individual")
if cuit.is_company():
    print("Company")

# Create from DNI
cuit = TaxId.from_dni('12345678', gender='M')
```

**Features:**
- Check digit validation
- Type identification
- DNI conversion
- Flexible formatting

### 6. ProductCode

Represents product codes/SKUs.

```python
from core.value_objects import ProductCode

# Create
code = ProductCode('ABC-123')

# Access parts
print(code.prefix)  # 'ABC'
print(code.suffix)  # '123'

# Queries
if code.has_prefix('ABC'):
    print("ABC series")

if code.contains('123'):
    print("Contains 123")

# Generate codes
code = ProductCode.generate_sku('PROD', 123)  # 'PROD-123'
code = ProductCode.generate_sku('SHIRT', 42, 'XL')  # 'SHIRT-42-XL'

# Case insensitive
assert ProductCode('abc-123') == ProductCode('ABC-123')
```

**Features:**
- Alphanumeric validation
- Prefix/suffix extraction
- Case normalization
- SKU generation

### 7. Percentage

Represents percentage values.

```python
from core.value_objects import Percentage, Money
from decimal import Decimal

# Create percentage
tax_rate = Percentage(Decimal('8.25'))  # 8.25%
discount = Percentage(Decimal('15'))     # 15%

# Apply to amounts
price = Money(Decimal('100'), 'USD')
tax = tax_rate.of(price)  # Money(8.25, 'USD')

# Add to amount
total = tax_rate.add_to(price)  # Money(108.25, 'USD')

# Subtract from amount
final = discount.subtract_from(price)  # Money(85, 'USD')

# Arithmetic
combined = tax_rate.add(Percentage(Decimal('2')))  # 10.25%

# Convert to decimal
decimal_form = tax_rate.as_decimal()  # Decimal('0.0825')

# Special values
zero = Percentage.zero()  # 0%
full = Percentage.full()  # 100%

# From decimal
pct = Percentage.from_decimal(0.15)  # 15%

# From ratio
pct = Percentage.from_ratio(1, 4)  # 25%
```

**Features:**
- Precision with Decimal
- Works with Money value objects
- Range validation (0-100)
- Multiple creation methods

## Usage Examples

### Example 1: Product with Price

```python
from core.value_objects import Money, ProductCode, Percentage
from decimal import Decimal

class Product:
    def __init__(
        self,
        code: ProductCode,
        name: str,
        base_price: Money,
        tax_rate: Percentage
    ):
        self.code = code
        self.name = name
        self.base_price = base_price
        self.tax_rate = tax_rate

    @property
    def price_with_tax(self) -> Money:
        """Calculate price including tax."""
        return self.tax_rate.add_to(self.base_price)

    def apply_discount(self, discount: Percentage) -> Money:
        """Apply discount to base price."""
        return discount.subtract_from(self.base_price)

# Usage
product = Product(
    code=ProductCode('ABC-123'),
    name='Widget',
    base_price=Money(Decimal('100'), 'USD'),
    tax_rate=Percentage(Decimal('8.25'))
)

print(product.price_with_tax)  # USD 108.25

discounted = product.apply_discount(Percentage(Decimal('10')))
print(discounted)  # USD 90.00
```

### Example 2: Customer with Contact Info

```python
from core.value_objects import Email, PhoneNumber, Address, TaxId

class Customer:
    def __init__(
        self,
        id: int,
        name: str,
        email: Email,
        phone: PhoneNumber,
        address: Address,
        tax_id: TaxId
    ):
        self.id = id
        self.name = name
        self.email = email
        self.phone = phone
        self.address = address
        self.tax_id = tax_id

    def send_confirmation(self):
        """Send email confirmation."""
        print(f"Sending to {self.email}")
        print(f"SMS to {self.phone.format('national')}")

    def is_local(self) -> bool:
        """Check if customer is local."""
        return self.address.is_in_country('USA')

# Usage
customer = Customer(
    id=123,
    name="John Doe",
    email=Email('john@example.com'),
    phone=PhoneNumber('+1-555-123-4567'),
    address=Address(
        street='123 Main St',
        city='Springfield',
        state='IL',
        postal_code='62701',
        country='USA'
    ),
    tax_id=TaxId('20-12345678-9')
)

customer.send_confirmation()
```

### Example 3: Sale with Money Calculations

```python
from core.value_objects import Money, Percentage
from decimal import Decimal

class SaleItem:
    def __init__(self, product_name: str, price: Money, quantity: int):
        self.product_name = product_name
        self.price = price
        self.quantity = quantity

    @property
    def subtotal(self) -> Money:
        return self.price.multiply(self.quantity)

class Sale:
    def __init__(self, tax_rate: Percentage):
        self.items: list[SaleItem] = []
        self.tax_rate = tax_rate

    def add_item(self, item: SaleItem):
        self.items.append(item)

    @property
    def subtotal(self) -> Money:
        if not self.items:
            return Money.zero('USD')
        return sum(
            (item.subtotal for item in self.items),
            start=Money.zero('USD')
        )

    @property
    def tax(self) -> Money:
        return self.tax_rate.of(self.subtotal)

    @property
    def total(self) -> Money:
        return self.subtotal.add(self.tax)

    def apply_discount(self, discount: Percentage):
        """Apply discount to subtotal."""
        discounted_subtotal = discount.subtract_from(self.subtotal)
        tax_on_discounted = self.tax_rate.of(discounted_subtotal)
        return discounted_subtotal.add(tax_on_discounted)

# Usage
sale = Sale(tax_rate=Percentage(Decimal('8.25')))

sale.add_item(SaleItem(
    'Widget',
    Money(Decimal('19.99'), 'USD'),
    quantity=2
))
sale.add_item(SaleItem(
    'Gadget',
    Money(Decimal('9.99'), 'USD'),
    quantity=1
))

print(f"Subtotal: {sale.subtotal}")  # USD 49.97
print(f"Tax: {sale.tax}")             # USD 4.12
print(f"Total: {sale.total}")         # USD 54.09

# Apply 10% discount
final = sale.apply_discount(Percentage(Decimal('10')))
print(f"With discount: {final}")  # USD 48.71
```

### Example 4: Splitting Bill

```python
from core.value_objects import Money
from decimal import Decimal

def split_bill(total: Money, num_people: int) -> list[Money]:
    """Split bill evenly among people."""
    ratios = [1] * num_people  # Equal ratios
    return total.allocate(ratios)

# Usage
bill = Money(Decimal('100'), 'USD')
shares = split_bill(bill, 3)

for i, share in enumerate(shares, 1):
    print(f"Person {i}: {share}")

# Person 1: USD 33.34
# Person 2: USD 33.33
# Person 3: USD 33.33
# Total: USD 100.00 (no money lost to rounding!)
```

## Best Practices

### 1. Prefer Value Objects Over Primitives

```python
# ❌ Bad: Primitive Obsession
def calculate_tax(amount: float, rate: float) -> float:
    return amount * rate

total = calculate_tax(100.50, 0.0825)  # What currency? What precision?

# ✅ Good: Value Objects
def calculate_tax(amount: Money, rate: Percentage) -> Money:
    return rate.of(amount)

total = calculate_tax(
    Money(Decimal('100.50'), 'USD'),
    Percentage(Decimal('8.25'))
)
```

### 2. Make Value Objects Immutable

```python
# ❌ Bad: Mutable
class Money:
    def __init__(self, amount, currency):
        self.amount = amount  # Can be changed!
        self.currency = currency

price = Money(10, 'USD')
price.amount = 20  # Dangerous mutation!

# ✅ Good: Immutable
@dataclass(frozen=True)
class Money(ValueObject):
    amount: Decimal
    currency: str

price = Money(Decimal('10'), 'USD')
# price.amount = Decimal('20')  # Error!
```

### 3. Validate in Constructor

```python
# ❌ Bad: No Validation
class Email:
    def __init__(self, value: str):
        self.value = value  # No validation!

email = Email('not-an-email')  # Accepted!

# ✅ Good: Validate on Creation
@dataclass(frozen=True)
class Email(ValueObject):
    value: str

    def __post_init__(self):
        if '@' not in self.value:
            raise ValidationError("Invalid email format")

# email = Email('not-an-email')  # Raises ValidationError immediately!
```

### 4. Provide Meaningful Operations

```python
# ❌ Bad: Expose internals
money = Money(Decimal('10'), 'USD')
result = Money(money.amount + Decimal('5'), money.currency)

# ✅ Good: Provide operations
money = Money(Decimal('10'), 'USD')
result = money.add(Money(Decimal('5'), 'USD'))
```

### 5. Use Factory Methods for Complex Creation

```python
# ✅ Good: Factory methods
class PhoneNumber(ValueObject):
    @classmethod
    def from_parts(cls, area: str, exchange: str, number: str):
        return cls(f"+1{area}{exchange}{number}")

phone = PhoneNumber.from_parts('555', '123', '4567')
```

### 6. Make Equality Based on Value

```python
# ✅ Good: Value equality (automatic with dataclass)
@dataclass(frozen=True)
class Money(ValueObject):
    amount: Decimal
    currency: str

m1 = Money(Decimal('10'), 'USD')
m2 = Money(Decimal('10'), 'USD')
assert m1 == m2  # True - same value
assert m1 is not m2  # True - different objects
```

### 7. Keep Value Objects Focused

```python
# ❌ Bad: Too many responsibilities
class Address(ValueObject):
    def validate(self): ...
    def geocode(self): ...  # External service call!
    def calculate_shipping_cost(self): ...  # Business logic!

# ✅ Good: Single responsibility
class Address(ValueObject):
    # Just represents an address
    street: str
    city: str
    # ...

# Use services for additional behavior
class GeocodeService:
    def geocode(self, address: Address): ...

class ShippingService:
    def calculate_cost(self, address: Address): ...
```

## Testing

### Testing Value Objects

```python
import pytest
from decimal import Decimal
from core.value_objects import Money, Email, Percentage
from core.value_objects.base import ValidationError

class TestMoney:
    """Test Money value object."""

    def test_create_valid_money(self):
        """Test creating valid money."""
        money = Money(Decimal('10'), 'USD')
        assert money.amount == Decimal('10')
        assert money.currency == 'USD'

    def test_negative_amount_raises_error(self):
        """Test that negative amounts are rejected."""
        with pytest.raises(ValidationError):
            Money(Decimal('-10'), 'USD')

    def test_invalid_currency_raises_error(self):
        """Test that invalid currency is rejected."""
        with pytest.raises(ValidationError):
            Money(Decimal('10'), 'INVALID')

    def test_add_same_currency(self):
        """Test adding money with same currency."""
        m1 = Money(Decimal('10'), 'USD')
        m2 = Money(Decimal('5'), 'USD')
        result = m1.add(m2)

        assert result.amount == Decimal('15')
        assert result.currency == 'USD'

    def test_add_different_currency_raises_error(self):
        """Test that adding different currencies raises error."""
        m1 = Money(Decimal('10'), 'USD')
        m2 = Money(Decimal('5'), 'EUR')

        with pytest.raises(ValidationError):
            m1.add(m2)

    def test_equality(self):
        """Test value equality."""
        m1 = Money(Decimal('10'), 'USD')
        m2 = Money(Decimal('10'), 'USD')
        m3 = Money(Decimal('5'), 'USD')

        assert m1 == m2  # Same value
        assert m1 is not m2  # Different objects
        assert m1 != m3  # Different value

    def test_immutability(self):
        """Test that money is immutable."""
        money = Money(Decimal('10'), 'USD')

        with pytest.raises(AttributeError):
            money.amount = Decimal('20')


class TestEmail:
    """Test Email value object."""

    def test_create_valid_email(self):
        """Test creating valid email."""
        email = Email('test@example.com')
        assert email.value == 'test@example.com'

    def test_invalid_email_raises_error(self):
        """Test that invalid email raises error."""
        with pytest.raises(ValidationError):
            Email('not-an-email')

    def test_normalization(self):
        """Test email normalization."""
        email = Email('TEST@EXAMPLE.COM')
        assert email.value == 'test@example.com'  # Lowercase

    def test_domain_extraction(self):
        """Test domain extraction."""
        email = Email('user@example.com')
        assert email.domain == 'example.com'
        assert email.local_part == 'user'


class TestPercentage:
    """Test Percentage value object."""

    def test_create_valid_percentage(self):
        """Test creating valid percentage."""
        pct = Percentage(Decimal('10'))
        assert pct.value == Decimal('10')

    def test_percentage_above_100_raises_error(self):
        """Test that percentage > 100 raises error."""
        with pytest.raises(ValidationError):
            Percentage(Decimal('150'))

    def test_percentage_below_0_raises_error(self):
        """Test that percentage < 0 raises error."""
        with pytest.raises(ValidationError):
            Percentage(Decimal('-10'))

    def test_of_amount(self):
        """Test calculating percentage of amount."""
        pct = Percentage(Decimal('10'))
        result = pct.of(Decimal('100'))
        assert result == Decimal('10')

    def test_of_money(self):
        """Test calculating percentage of money."""
        pct = Percentage(Decimal('10'))
        money = Money(Decimal('100'), 'USD')
        result = pct.of(money)

        assert result == Money(Decimal('10'), 'USD')
```

## Integration

### Using Value Objects in Domain Models

```python
from dataclasses import dataclass
from uuid import UUID
from core.value_objects import Money, ProductCode

@dataclass
class Product:
    """Product entity (has identity)."""
    id: UUID
    code: ProductCode  # Value Object
    name: str
    price: Money  # Value Object

    def apply_discount(self, discount_percentage: Percentage) -> Money:
        """Calculate discounted price."""
        return discount_percentage.subtract_from(self.price)
```

### Using Value Objects in DTOs

```python
from dataclasses import dataclass
from core.value_objects import Email, PhoneNumber, Address

@dataclass
class CreateCustomerRequest:
    """DTO for creating customer."""
    name: str
    email: Email  # Value Object ensures valid email
    phone: PhoneNumber  # Value Object ensures valid phone
    address: Address  # Value Object ensures valid address
```

### Using Value Objects in Repositories

```python
from core.value_objects import Email, TaxId

class CustomerRepository:
    def find_by_email(self, email: Email) -> Optional[Customer]:
        """Find customer by email."""
        # email is validated, normalized
        return self.session.query(Customer).filter(
            Customer.email == str(email)
        ).first()

    def find_by_tax_id(self, tax_id: TaxId) -> Optional[Customer]:
        """Find customer by tax ID."""
        # tax_id is validated with check digit
        return self.session.query(Customer).filter(
            Customer.tax_id == str(tax_id)
        ).first()
```

## Summary

Value Objects are a powerful pattern for:
- **Eliminating Primitive Obsession**: Replace raw types with meaningful objects
- **Enforcing Business Rules**: Validation at creation time
- **Improving Code Quality**: Type-safe, self-documenting code
- **Reducing Bugs**: Immutability prevents accidental changes

### Key Takeaways

1. **Use value objects for concepts identified by attributes**, not identity
2. **Make them immutable** with `@dataclass(frozen=True)`
3. **Validate in `__post_init__`** to enforce business rules
4. **Provide meaningful operations** that return new instances
5. **Test thoroughly** to ensure correctness
6. **Use throughout the domain** for consistency

### Next Steps

1. Review existing code for primitive obsession
2. Replace primitives with value objects
3. Add value objects to DTOs and domain models
4. Write tests for value objects
5. Document domain-specific value objects

### Related Patterns

- **Entity Pattern**: Objects with identity
- **Aggregate Pattern**: Consistency boundaries
- **Specification Pattern**: Business rules
- **Factory Pattern**: Complex object creation

### Resources

- [Domain-Driven Design](https://www.domainlanguage.com/ddd/) by Eric Evans
- [Implementing Domain-Driven Design](https://vaughnvernon.com/?page_id=168) by Vaughn Vernon
- [Value Object](https://martinfowler.com/bliki/ValueObject.html) by Martin Fowler
