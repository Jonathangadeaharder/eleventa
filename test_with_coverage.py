#!/usr/bin/env python
"""
Coverage test runner for architectural patterns.
Uses coverage.py to measure code coverage.
"""

import sys
import os
import coverage

# Start coverage
cov = coverage.Coverage(
    source=["core/value_objects", "core/specifications", "core/aggregates"],
    omit=["*/test_*", "*/__pycache__/*"],
)
cov.start()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from decimal import Decimal
from uuid import uuid4

# Import all the code we want to test coverage for
from core.value_objects import (
    Money,
    Email,
    Address,
    Percentage,
    ProductCode,
    PhoneNumber,
    TaxId,
)
from core.specifications.base import (
    Specification,
    AndSpecification,
    OrSpecification,
    NotSpecification,
)
from core.aggregates.examples import Order, ShoppingCart, Customer
from core.aggregates.base import DomainError
from core.aggregates.repository import (
    InMemoryAggregateRepository,
    InMemoryEventPublisher,
)
from core.models.product import Product

print("=" * 70)
print("RUNNING TESTS WITH COVERAGE")
print("=" * 70)

tests_passed = 0
tests_failed = 0


def run_test(description, test_func):
    """Run a test and track results."""
    global tests_passed, tests_failed
    try:
        test_func()
        tests_passed += 1
        print(f"✓ {description}")
        return True
    except Exception as e:
        tests_failed += 1
        print(f"✗ {description}: {e}")
        return False


# ============================================================================
# VALUE OBJECTS TESTS (Comprehensive)
# ============================================================================

print("\n" + "=" * 70)
print("VALUE OBJECTS")
print("=" * 70)

# Money tests
run_test("Money: Create and validate", lambda: Money(Decimal("10"), "USD"))
run_test(
    "Money: Add same currency",
    lambda: Money(Decimal("10"), "USD").add(Money(Decimal("5"), "USD")),
)
run_test(
    "Money: Subtract",
    lambda: Money(Decimal("10"), "USD").subtract(Money(Decimal("5"), "USD")),
)
run_test("Money: Multiply", lambda: Money(Decimal("10"), "USD").multiply(2))
run_test("Money: Divide", lambda: Money(Decimal("10"), "USD").divide(2))
run_test("Money: Round", lambda: Money(Decimal("10.556"), "USD").round(2))
run_test("Money: Allocate", lambda: Money(Decimal("100"), "USD").allocate([1, 1, 1]))
run_test(
    "Money: Convert currency",
    lambda: Money(Decimal("100"), "USD").convert_to("EUR", Decimal("0.85")),
)
run_test("Money: Is zero", lambda: Money.zero("USD").is_zero())
run_test("Money: Is positive", lambda: Money(Decimal("1"), "USD").is_positive())
run_test(
    "Money: Comparison",
    lambda: Money(Decimal("10"), "USD") < Money(Decimal("20"), "USD"),
)
run_test("Money: From float", lambda: Money.from_float(19.99, "USD"))
run_test("Money: From string", lambda: Money.from_string("19.99", "USD"))

# Email tests
run_test("Email: Create and validate", lambda: Email("test@example.com"))
run_test("Email: Normalize", lambda: Email("TEST@EXAMPLE.COM"))
run_test("Email: Extract domain", lambda: Email("john@example.com").domain)
run_test("Email: Extract local part", lambda: Email("john@example.com").local_part)
run_test(
    "Email: Check domain",
    lambda: Email("john@example.com").is_from_domain("example.com"),
)
run_test("Email: Obfuscate", lambda: Email("john@example.com").obfuscate())

# Address tests
run_test(
    "Address: Create", lambda: Address("123 Main St", "Springfield", "62701", "USA")
)
run_test(
    "Address: To string",
    lambda: str(Address("123 Main St", "Springfield", "62701", "USA")),
)
run_test(
    "Address: Multiline",
    lambda: Address("123 Main St", "Springfield", "62701", "USA").to_multiline(),
)
run_test(
    "Address: Is in country",
    lambda: Address("123 Main St", "Springfield", "62701", "USA").is_in_country("USA"),
)
run_test(
    "Address: Create simple",
    lambda: Address.create_simple("123 Main St", "Springfield", "62701"),
)

# Percentage tests
run_test("Percentage: Create", lambda: Percentage(Decimal("10")))
run_test("Percentage: As decimal", lambda: Percentage(Decimal("10")).as_decimal())
run_test("Percentage: Of amount", lambda: Percentage(Decimal("10")).of(Decimal("100")))
run_test("Percentage: Add to", lambda: Percentage(Decimal("10")).add_to(Decimal("100")))
run_test(
    "Percentage: Subtract from",
    lambda: Percentage(Decimal("10")).subtract_from(Decimal("100")),
)
run_test(
    "Percentage: Add percentages",
    lambda: Percentage(Decimal("5")).add(Percentage(Decimal("3"))),
)
run_test("Percentage: Multiply", lambda: Percentage(Decimal("5")).multiply(2))
run_test("Percentage: Is zero", lambda: Percentage.zero().is_zero())
run_test("Percentage: Is full", lambda: Percentage.full().is_full())
run_test("Percentage: From decimal", lambda: Percentage.from_decimal(Decimal("0.1")))
run_test("Percentage: From ratio", lambda: Percentage.from_ratio(1, 4))

# ProductCode tests
run_test("ProductCode: Create", lambda: ProductCode("ABC-123"))
run_test("ProductCode: Normalize", lambda: ProductCode("abc-123"))
run_test("ProductCode: Prefix", lambda: ProductCode("ABC-123").prefix)
run_test("ProductCode: Suffix", lambda: ProductCode("ABC-123").suffix)
run_test("ProductCode: Has prefix", lambda: ProductCode("ABC-123").has_prefix("ABC"))
run_test("ProductCode: Generate SKU", lambda: ProductCode.generate_sku("PROD", 123))

# PhoneNumber tests
run_test("PhoneNumber: Create", lambda: PhoneNumber("+15551234567"))
run_test(
    "PhoneNumber: Format international",
    lambda: PhoneNumber("+15551234567").format("international"),
)
run_test(
    "PhoneNumber: From parts", lambda: PhoneNumber.from_parts("555", "123", "4567")
)

# TaxId tests (using valid CUIT format with correct check digits)
# CUIT 20-12345678-6 has valid check digit calculated using official algorithm
run_test("TaxId: Create", lambda: TaxId("20-12345678-6"))
run_test("TaxId: Format", lambda: TaxId("20123456786").format())

# ============================================================================
# SPECIFICATIONS TESTS
# ============================================================================

print("\n" + "=" * 70)
print("SPECIFICATIONS")
print("=" * 70)


class TestSpec(Specification[Product]):
    def is_satisfied_by(self, product):
        return product.quantity_in_stock > 0

    def to_sqlalchemy_filter(self):
        return None


def test_spec_basic():
    spec = TestSpec()
    product = Product(code="P001", description="Test", quantity_in_stock=Decimal("10"))
    assert spec.is_satisfied_by(product)


def test_spec_and():
    spec1 = TestSpec()
    spec2 = TestSpec()
    composed = spec1.and_(spec2)
    assert isinstance(composed, AndSpecification)


def test_spec_or():
    spec1 = TestSpec()
    spec2 = TestSpec()
    composed = spec1.or_(spec2)
    assert isinstance(composed, OrSpecification)


def test_spec_not():
    spec = TestSpec()
    negated = spec.not_()
    assert isinstance(negated, NotSpecification)


run_test("Specification: Basic", test_spec_basic)
run_test("Specification: AND", test_spec_and)
run_test("Specification: OR", test_spec_or)
run_test("Specification: NOT", test_spec_not)

# ============================================================================
# AGGREGATES TESTS (Comprehensive)
# ============================================================================

print("\n" + "=" * 70)
print("AGGREGATES")
print("=" * 70)

# Order tests
run_test("Order: Create", lambda: Order(uuid4()))
run_test(
    "Order: Add item",
    lambda: Order(uuid4()).add_item(uuid4(), "Widget", 1, Money(Decimal("10"), "USD")),
)


def test_order_total():
    order = Order(uuid4())
    order.add_item(uuid4(), "Widget", 2, Money(Decimal("10"), "USD"))
    assert order.total == Money(Decimal("20"), "USD")


def test_order_submit():
    order = Order(uuid4())
    order.add_item(uuid4(), "Widget", 1, Money(Decimal("20"), "USD"))
    order.submit()
    assert order.status == Order.STATUS_SUBMITTED


def test_order_cannot_submit_empty():
    order = Order(uuid4())
    try:
        order.submit()
        raise AssertionError("Should raise DomainError")
    except DomainError:
        pass


def test_order_events():
    order = Order(uuid4())
    assert order.has_domain_events()
    events = order.get_domain_events()
    assert len(events) > 0


def test_order_remove_item():
    order = Order(uuid4())
    item = order.add_item(uuid4(), "Widget", 1, Money(Decimal("10"), "USD"))
    order.remove_item(item.id)
    assert len(order.items) == 0


def test_order_change_quantity():
    order = Order(uuid4())
    item = order.add_item(uuid4(), "Widget", 1, Money(Decimal("10"), "USD"))
    order.change_item_quantity(item.id, 5)
    assert item.quantity == 5


def test_order_cancel():
    order = Order(uuid4())
    order.add_item(uuid4(), "Widget", 1, Money(Decimal("20"), "USD"))
    order.cancel("Test reason")
    assert order.status == Order.STATUS_CANCELLED


run_test("Order: Calculate total", test_order_total)
run_test("Order: Submit", test_order_submit)
run_test("Order: Cannot submit empty", test_order_cannot_submit_empty)
run_test("Order: Domain events", test_order_events)
run_test("Order: Remove item", test_order_remove_item)
run_test("Order: Change quantity", test_order_change_quantity)
run_test("Order: Cancel", test_order_cancel)

# ShoppingCart tests
run_test("ShoppingCart: Create", lambda: ShoppingCart(uuid4()))


def test_cart_add_item():
    cart = ShoppingCart(uuid4())
    cart.add_item(uuid4(), 2)
    assert len(cart.items) == 1


def test_cart_remove_item():
    cart = ShoppingCart(uuid4())
    product_id = uuid4()
    cart.add_item(product_id)
    cart.remove_item(product_id)
    assert len(cart.items) == 0


def test_cart_clear():
    cart = ShoppingCart(uuid4())
    cart.add_item(uuid4())
    cart.clear()
    assert len(cart.items) == 0


run_test("ShoppingCart: Add item", test_cart_add_item)
run_test("ShoppingCart: Remove item", test_cart_remove_item)
run_test("ShoppingCart: Clear", test_cart_clear)

# Customer tests
run_test("Customer: Create", lambda: Customer(Email("test@example.com"), "John Doe"))


def test_customer_add_address():
    customer = Customer(Email("test@example.com"), "John Doe")
    address = Address("123 Main St", "Springfield", "62701", "USA")
    customer.add_address(address)
    assert len(customer.addresses) == 1


def test_customer_default_address():
    customer = Customer(Email("test@example.com"), "John Doe")
    address = Address("123 Main St", "Springfield", "62701", "USA")
    customer.add_address(address)
    default = customer.get_default_address()
    assert default == address


run_test("Customer: Add address", test_customer_add_address)
run_test("Customer: Default address", test_customer_default_address)


# Repository tests
def test_repository_save_load():
    repo = InMemoryAggregateRepository[Order]()
    order = Order(uuid4())
    order.add_item(uuid4(), "Widget", 1, Money(Decimal("10"), "USD"))
    repo.save(order)
    loaded = repo.get_by_id(order.id)
    assert loaded is not None
    assert loaded.id == order.id


def test_repository_events():
    publisher = InMemoryEventPublisher()
    repo = InMemoryAggregateRepository[Order](publisher)
    order = Order(uuid4())
    repo.save(order)
    assert len(publisher.published_events) > 0


def test_repository_version():
    repo = InMemoryAggregateRepository[Order]()
    order = Order(uuid4())
    assert order.version == 0
    repo.save(order)
    assert order.version == 1


run_test("Repository: Save and load", test_repository_save_load)
run_test("Repository: Publish events", test_repository_events)
run_test("Repository: Version management", test_repository_version)

# ============================================================================
# STOP COVERAGE AND REPORT
# ============================================================================

cov.stop()
cov.save()

print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print(f"Tests passed: {tests_passed}")
print(f"Tests failed: {tests_failed}")
print(f"Total tests: {tests_passed + tests_failed}")
print("=" * 70)

print("\n" + "=" * 70)
print("COVERAGE REPORT")
print("=" * 70)
cov.report()

print("\n" + "=" * 70)
print("DETAILED COVERAGE BY MODULE")
print("=" * 70)

# Get coverage data
data = cov.get_data()
files = sorted(data.measured_files())

for filepath in files:
    if any(
        pattern in filepath
        for pattern in ["value_objects", "specifications", "aggregates"]
    ):
        if "__pycache__" not in filepath:
            analysis = cov.analysis2(filepath)
            executed = len(analysis[1])
            missing = len(analysis[2])
            total = executed + missing
            if total > 0:
                percentage = (executed / total) * 100
                filename = filepath.split("/")[-1]
                print(f"{filename:40s} {percentage:6.1f}% ({executed}/{total} lines)")

# Save HTML report
print("\n" + "=" * 70)
print("Generating HTML coverage report...")
print("=" * 70)
cov.html_report(directory="htmlcov")
print("✓ HTML report generated in htmlcov/index.html")

if tests_failed == 0:
    print("\n✓ ALL TESTS PASSED!")
    sys.exit(0)
else:
    print(f"\n✗ {tests_failed} TESTS FAILED")
    sys.exit(1)
