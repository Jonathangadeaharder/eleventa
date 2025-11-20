#!/usr/bin/env python
"""Simple test runner for architectural patterns - no pytest needed."""

import sys
from decimal import Decimal
from uuid import uuid4

print("="*70)
print("TESTING ARCHITECTURAL PATTERNS")
print("="*70)

# Test counter
tests_passed = 0
tests_failed = 0

def test(description):
    """Decorator for test functions."""
    def decorator(func):
        def wrapper():
            global tests_passed, tests_failed
            try:
                func()
                tests_passed += 1
                print(f"✓ {description}")
                return True
            except AssertionError as e:
                tests_failed += 1
                print(f"✗ {description}: {e}")
                return False
            except Exception as e:
                tests_failed += 1
                print(f"✗ {description}: ERROR - {e}")
                return False
        return wrapper
    return decorator

# ============================================================================
# VALUE OBJECTS TESTS
# ============================================================================

print("\n" + "="*70)
print("VALUE OBJECTS")
print("="*70)

from core.value_objects import Money, Email, Address, Percentage, ProductCode

@test("Money: Create valid money")
def test_money_create():
    money = Money(Decimal('10.50'), 'USD')
    assert money.amount == Decimal('10.50')
    assert money.currency == 'USD'

test_money_create()

@test("Money: Add same currency")
def test_money_add():
    m1 = Money(Decimal('10'), 'USD')
    m2 = Money(Decimal('5'), 'USD')
    result = m1.add(m2)
    assert result.amount == Decimal('15')

test_money_add()

@test("Money: Multiply by scalar")
def test_money_multiply():
    money = Money(Decimal('10'), 'USD')
    result = money.multiply(2)
    assert result.amount == Decimal('20')

test_money_multiply()

@test("Money: Equality by value")
def test_money_equality():
    m1 = Money(Decimal('10'), 'USD')
    m2 = Money(Decimal('10'), 'USD')
    assert m1 == m2

test_money_equality()

@test("Email: Create valid email")
def test_email_create():
    email = Email('test@example.com')
    assert email.value == 'test@example.com'

test_email_create()

@test("Email: Normalize to lowercase")
def test_email_normalize():
    email = Email('TEST@EXAMPLE.COM')
    assert email.value == 'test@example.com'

test_email_normalize()

@test("Email: Extract domain")
def test_email_domain():
    email = Email('john@example.com')
    assert email.domain == 'example.com'

test_email_domain()

@test("Address: Create valid address")
def test_address_create():
    address = Address(
        street='123 Main St',
        city='Springfield',
        postal_code='62701',
        country='USA'
    )
    assert address.street == '123 Main St'

test_address_create()

@test("Percentage: Create valid percentage")
def test_percentage_create():
    pct = Percentage(Decimal('10'))
    assert pct.value == Decimal('10')

test_percentage_create()

@test("Percentage: Calculate percentage of amount")
def test_percentage_of():
    pct = Percentage(Decimal('10'))
    result = pct.of(Decimal('100'))
    assert result == Decimal('10')

test_percentage_of()

@test("Percentage: Add to amount")
def test_percentage_add_to():
    pct = Percentage(Decimal('10'))
    result = pct.add_to(Decimal('100'))
    assert result == Decimal('110')

test_percentage_add_to()

@test("ProductCode: Create valid code")
def test_product_code():
    code = ProductCode('ABC-123')
    assert code.value == 'ABC-123'

test_product_code()

@test("ProductCode: Normalize to uppercase")
def test_product_code_normalize():
    code = ProductCode('abc-123')
    assert code.value == 'ABC-123'

test_product_code_normalize()

# ============================================================================
# SPECIFICATIONS TESTS
# ============================================================================

print("\n" + "="*70)
print("SPECIFICATIONS")
print("="*70)

from core.models.product import Product
from core.specifications.base import Specification, AndSpecification

class SimpleProductInStockSpec(Specification[Product]):
    """Simple in-stock specification for testing."""
    def is_satisfied_by(self, product):
        return product.quantity_in_stock > 0

    def to_sqlalchemy_filter(self):
        return None

@test("Specification: Check is_satisfied_by")
def test_spec_is_satisfied():
    spec = SimpleProductInStockSpec()
    product = Product(code="P001", description="Test", quantity_in_stock=Decimal('10'))
    assert spec.is_satisfied_by(product)

test_spec_is_satisfied()

@test("Specification: AND composition")
def test_spec_and():
    spec1 = SimpleProductInStockSpec()
    spec2 = SimpleProductInStockSpec()
    composed = spec1.and_(spec2)
    assert isinstance(composed, AndSpecification)

test_spec_and()

# ============================================================================
# AGGREGATES TESTS
# ============================================================================

print("\n" + "="*70)
print("AGGREGATES")
print("="*70)

from core.aggregates.examples import Order, ShoppingCart, Customer
from core.aggregates.base import DomainError

@test("Order: Create order")
def test_order_create():
    customer_id = uuid4()
    order = Order(customer_id)
    assert order.id is not None
    assert order.customer_id == customer_id

test_order_create()

@test("Order: Add item to order")
def test_order_add_item():
    order = Order(uuid4())
    order.add_item(
        uuid4(),
        "Widget",
        2,
        Money(Decimal('10'), 'USD')
    )
    assert len(order.items) == 1
    assert order.total == Money(Decimal('20'), 'USD')

test_order_add_item()

@test("Order: Submit order")
def test_order_submit():
    order = Order(uuid4())
    order.add_item(uuid4(), "Widget", 1, Money(Decimal('20'), 'USD'))
    order.submit()
    assert order.status == Order.STATUS_SUBMITTED

test_order_submit()

@test("Order: Cannot submit empty order")
def test_order_cannot_submit_empty():
    order = Order(uuid4())
    try:
        order.submit()
        assert False, "Should raise DomainError"
    except DomainError:
        pass  # Expected

test_order_cannot_submit_empty()

@test("Order: Domain events raised")
def test_order_events():
    order = Order(uuid4())
    assert order.has_domain_events()
    assert len(order.get_domain_events()) > 0

test_order_events()

@test("ShoppingCart: Create cart")
def test_cart_create():
    cart = ShoppingCart(uuid4())
    assert cart.id is not None
    assert len(cart.items) == 0

test_cart_create()

@test("ShoppingCart: Add item")
def test_cart_add_item():
    cart = ShoppingCart(uuid4())
    cart.add_item(uuid4(), quantity=2)
    assert len(cart.items) == 1

test_cart_add_item()

@test("Customer: Create customer")
def test_customer_create():
    customer = Customer(Email('test@example.com'), "John Doe")
    assert customer.id is not None
    assert customer.name == "John Doe"

test_customer_create()

@test("Customer: Add address")
def test_customer_add_address():
    customer = Customer(Email('test@example.com'), "John Doe")
    address = Address('123 Main St', 'Springfield', '62701', 'USA')
    customer.add_address(address)
    assert len(customer.addresses) == 1

test_customer_add_address()

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"Tests passed: {tests_passed}")
print(f"Tests failed: {tests_failed}")
print(f"Total tests: {tests_passed + tests_failed}")
print("="*70)

if tests_failed == 0:
    print("✓ ALL TESTS PASSED!")
    sys.exit(0)
else:
    print("✗ SOME TESTS FAILED")
    sys.exit(1)
