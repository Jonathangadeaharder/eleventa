"""
Tests for Aggregate Pattern

Tests cover:
- AggregateRoot base class
- Domain event management
- Entity identity
- Business rule enforcement
- Order aggregate example
- ShoppingCart aggregate example
- Customer aggregate example
- Repository integration
"""

import pytest
from decimal import Decimal
from uuid import uuid4

from core.aggregates.base import (
    AggregateRoot,
    Entity,
    DomainEvent,
    DomainError,
    ensure_aggregate_invariants,
)
from core.aggregates.repository import (
    InMemoryAggregateRepository,
    InMemoryEventPublisher,
)
from core.aggregates.examples import (
    Order,
    OrderItem,
    OrderCreated,
    OrderItemAdded,
    OrderSubmitted,
    OrderCancelled,
    ShoppingCart,
    CartItemAdded,
    Customer,
    CustomerRegistered,
)
from core.value_objects import Money, Email, Address


class TestEntity:
    """Tests for Entity base class."""

    def test_entity_equality_by_id(self):
        """Test that entities are equal if they have same ID."""

        class TestEntity(Entity):
            def __init__(self, id, name):
                self.id = id
                self.name = name

        id1 = uuid4()
        e1 = TestEntity(id1, "Test 1")
        e2 = TestEntity(id1, "Test 2")  # Different name, same ID
        e3 = TestEntity(uuid4(), "Test 1")  # Different ID

        assert e1 == e2  # Same ID
        assert e1 != e3  # Different ID

    def test_entity_hash(self):
        """Test that entities can be used in sets."""

        class TestEntity(Entity):
            def __init__(self, id):
                self.id = id

        id1 = uuid4()
        e1 = TestEntity(id1)
        e2 = TestEntity(id1)

        # Can use in sets
        entity_set = {e1, e2}
        assert len(entity_set) == 1  # Same ID, only one in set


class TestAggregateRoot:
    """Tests for AggregateRoot base class."""

    def test_aggregate_version_starts_at_zero(self):
        """Test that aggregate version starts at 0."""

        class TestAggregate(AggregateRoot):
            def __init__(self):
                super().__init__()
                self.id = uuid4()

        aggregate = TestAggregate()
        assert aggregate.version == 0

    def test_add_domain_event(self):
        """Test adding domain events."""

        class TestEvent(DomainEvent):
            pass

        class TestAggregate(AggregateRoot):
            def __init__(self):
                super().__init__()
                self.id = uuid4()

        aggregate = TestAggregate()
        event = TestEvent(aggregate.id)

        aggregate.add_domain_event(event)

        assert len(aggregate.get_domain_events()) == 1
        assert aggregate.has_domain_events()

    def test_clear_domain_events(self):
        """Test clearing domain events."""

        class TestEvent(DomainEvent):
            pass

        class TestAggregate(AggregateRoot):
            def __init__(self):
                super().__init__()
                self.id = uuid4()

        aggregate = TestAggregate()
        aggregate.add_domain_event(TestEvent(aggregate.id))

        assert aggregate.has_domain_events()

        aggregate.clear_domain_events()

        assert not aggregate.has_domain_events()
        assert len(aggregate.get_domain_events()) == 0


class TestOrder:
    """Tests for Order aggregate."""

    def test_create_order(self):
        """Test creating an order."""
        customer_id = uuid4()
        order = Order(customer_id)

        assert order.id is not None
        assert order.customer_id == customer_id
        assert order.status == Order.STATUS_DRAFT
        assert len(order.items) == 0

    def test_create_order_raises_event(self):
        """Test that creating order raises OrderCreated event."""
        customer_id = uuid4()
        order = Order(customer_id)

        events = order.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], OrderCreated)
        assert events[0].customer_id == customer_id

    def test_add_item_to_order(self):
        """Test adding item to order."""
        order = Order(uuid4())

        product_id = uuid4()
        order.add_item(
            product_id=product_id,
            product_name="Widget",
            quantity=2,
            unit_price=Money(Decimal('10'), 'USD')
        )

        assert len(order.items) == 1
        assert order.items[0].product_id == product_id
        assert order.items[0].quantity == 2
        assert order.total == Money(Decimal('20'), 'USD')

    def test_add_item_raises_event(self):
        """Test that adding item raises event."""
        order = Order(uuid4())
        order.clear_domain_events()  # Clear creation event

        product_id = uuid4()
        order.add_item(product_id, "Widget", 1, Money(Decimal('10'), 'USD'))

        events = order.get_domain_events()
        assert any(isinstance(e, OrderItemAdded) for e in events)

    def test_cannot_add_item_to_submitted_order(self):
        """Test that cannot add items to submitted order."""
        order = Order(uuid4())
        order.add_item(uuid4(), "Widget", 1, Money(Decimal('20'), 'USD'))
        order.submit()

        with pytest.raises(DomainError):
            order.add_item(uuid4(), "Gadget", 1, Money(Decimal('10'), 'USD'))

    def test_cannot_add_item_with_different_currency(self):
        """Test that all items must have same currency."""
        order = Order(uuid4(), currency='USD')
        order.add_item(uuid4(), "Widget", 1, Money(Decimal('10'), 'USD'))

        with pytest.raises(DomainError):
            order.add_item(uuid4(), "Gadget", 1, Money(Decimal('10'), 'EUR'))

    def test_cannot_add_item_exceeding_max(self):
        """Test that order cannot exceed max items."""
        order = Order(uuid4())

        # Add max items
        for i in range(Order.MAX_ITEMS):
            order.add_item(uuid4(), f"Item {i}", 1, Money(Decimal('1'), 'USD'))

        # Try to add one more
        with pytest.raises(DomainError):
            order.add_item(uuid4(), "Too many", 1, Money(Decimal('1'), 'USD'))

    def test_add_same_product_increases_quantity(self):
        """Test that adding same product increases quantity."""
        order = Order(uuid4())
        product_id = uuid4()

        order.add_item(product_id, "Widget", 1, Money(Decimal('10'), 'USD'))
        order.add_item(product_id, "Widget", 2, Money(Decimal('10'), 'USD'))

        assert len(order.items) == 1
        assert order.items[0].quantity == 3

    def test_remove_item_from_order(self):
        """Test removing item from order."""
        order = Order(uuid4())
        item = order.add_item(uuid4(), "Widget", 1, Money(Decimal('10'), 'USD'))

        order.remove_item(item.id)

        assert len(order.items) == 0

    def test_cannot_remove_item_from_submitted_order(self):
        """Test cannot remove from submitted order."""
        order = Order(uuid4())
        item = order.add_item(uuid4(), "Widget", 1, Money(Decimal('20'), 'USD'))
        order.submit()

        with pytest.raises(DomainError):
            order.remove_item(item.id)

    def test_change_item_quantity(self):
        """Test changing item quantity."""
        order = Order(uuid4())
        item = order.add_item(uuid4(), "Widget", 1, Money(Decimal('10'), 'USD'))

        order.change_item_quantity(item.id, 5)

        assert item.quantity == 5
        assert order.total == Money(Decimal('50'), 'USD')

    def test_submit_order(self):
        """Test submitting an order."""
        order = Order(uuid4())
        order.add_item(uuid4(), "Widget", 1, Money(Decimal('20'), 'USD'))

        order.submit()

        assert order.status == Order.STATUS_SUBMITTED
        assert order.submitted_at is not None

    def test_submit_order_raises_event(self):
        """Test that submitting order raises event."""
        order = Order(uuid4())
        order.add_item(uuid4(), "Widget", 1, Money(Decimal('20'), 'USD'))
        order.clear_domain_events()

        order.submit()

        events = order.get_domain_events()
        assert any(isinstance(e, OrderSubmitted) for e in events)

    def test_cannot_submit_empty_order(self):
        """Test that cannot submit empty order."""
        order = Order(uuid4())

        with pytest.raises(DomainError):
            order.submit()

    def test_cannot_submit_order_below_minimum(self):
        """Test that cannot submit order below minimum."""
        order = Order(uuid4())
        order.add_item(uuid4(), "Cheap", 1, Money(Decimal('1'), 'USD'))

        with pytest.raises(DomainError):
            order.submit()

    def test_cannot_submit_already_submitted_order(self):
        """Test that cannot submit already submitted order."""
        order = Order(uuid4())
        order.add_item(uuid4(), "Widget", 1, Money(Decimal('20'), 'USD'))
        order.submit()

        with pytest.raises(DomainError):
            order.submit()

    def test_cancel_order(self):
        """Test cancelling an order."""
        order = Order(uuid4())
        order.add_item(uuid4(), "Widget", 1, Money(Decimal('20'), 'USD'))

        order.cancel("Customer requested cancellation")

        assert order.status == Order.STATUS_CANCELLED
        assert order.cancellation_reason is not None

    def test_cancel_order_raises_event(self):
        """Test that cancelling order raises event."""
        order = Order(uuid4())
        order.add_item(uuid4(), "Widget", 1, Money(Decimal('20'), 'USD'))
        order.clear_domain_events()

        order.cancel("Test reason")

        events = order.get_domain_events()
        assert any(isinstance(e, OrderCancelled) for e in events)

    def test_order_total_calculation(self):
        """Test that order total is calculated correctly."""
        order = Order(uuid4())

        order.add_item(uuid4(), "Widget", 2, Money(Decimal('10'), 'USD'))
        order.add_item(uuid4(), "Gadget", 1, Money(Decimal('5'), 'USD'))

        assert order.total == Money(Decimal('25'), 'USD')

    def test_order_item_count(self):
        """Test item count calculation."""
        order = Order(uuid4())

        order.add_item(uuid4(), "Widget", 2, Money(Decimal('10'), 'USD'))
        order.add_item(uuid4(), "Gadget", 3, Money(Decimal('5'), 'USD'))

        assert order.item_count == 5

    def test_has_item(self):
        """Test checking if order has item for product."""
        order = Order(uuid4())
        product_id = uuid4()

        order.add_item(product_id, "Widget", 1, Money(Decimal('10'), 'USD'))

        assert order.has_item(product_id)
        assert not order.has_item(uuid4())


class TestShoppingCart:
    """Tests for ShoppingCart aggregate."""

    def test_create_cart(self):
        """Test creating shopping cart."""
        customer_id = uuid4()
        cart = ShoppingCart(customer_id)

        assert cart.id is not None
        assert cart.customer_id == customer_id
        assert len(cart.items) == 0

    def test_add_item_to_cart(self):
        """Test adding item to cart."""
        cart = ShoppingCart(uuid4())
        product_id = uuid4()

        cart.add_item(product_id, quantity=2)

        assert len(cart.items) == 1
        assert cart.items[0].product_id == product_id
        assert cart.items[0].quantity == 2

    def test_add_same_item_increases_quantity(self):
        """Test that adding same item increases quantity."""
        cart = ShoppingCart(uuid4())
        product_id = uuid4()

        cart.add_item(product_id, quantity=2)
        cart.add_item(product_id, quantity=3)

        assert len(cart.items) == 1
        assert cart.items[0].quantity == 5

    def test_cannot_exceed_max_items_per_product(self):
        """Test that cannot exceed max items per product."""
        cart = ShoppingCart(uuid4())
        product_id = uuid4()

        cart.add_item(product_id, quantity=ShoppingCart.MAX_ITEMS_PER_PRODUCT)

        with pytest.raises(DomainError):
            cart.add_item(product_id, quantity=1)

    def test_remove_item_from_cart(self):
        """Test removing item from cart."""
        cart = ShoppingCart(uuid4())
        product_id = uuid4()

        cart.add_item(product_id)
        cart.remove_item(product_id)

        assert len(cart.items) == 0

    def test_clear_cart(self):
        """Test clearing cart."""
        cart = ShoppingCart(uuid4())

        cart.add_item(uuid4())
        cart.add_item(uuid4())

        cart.clear()

        assert len(cart.items) == 0

    def test_clear_cart_raises_event(self):
        """Test that clearing cart raises event."""
        cart = ShoppingCart(uuid4())
        cart.add_item(uuid4())
        cart.clear_domain_events()

        cart.clear()

        events = cart.get_domain_events()
        assert any(isinstance(e, CartCleared) for e in events)

    def test_item_count(self):
        """Test item count calculation."""
        cart = ShoppingCart(uuid4())

        cart.add_item(uuid4(), quantity=2)
        cart.add_item(uuid4(), quantity=3)

        assert cart.item_count == 5


class TestCustomer:
    """Tests for Customer aggregate."""

    def test_create_customer(self):
        """Test creating customer."""
        email = Email('test@example.com')
        customer = Customer(email, "John Doe")

        assert customer.id is not None
        assert customer.email == email
        assert customer.name == "John Doe"
        assert len(customer.addresses) == 0

    def test_create_customer_raises_event(self):
        """Test that creating customer raises event."""
        email = Email('test@example.com')
        customer = Customer(email, "John Doe")

        events = customer.get_domain_events()
        assert any(isinstance(e, CustomerRegistered) for e in events)

    def test_add_address_to_customer(self):
        """Test adding address to customer."""
        customer = Customer(Email('test@example.com'), "John Doe")

        address = Address(
            street='123 Main St',
            city='Springfield',
            postal_code='62701',
            country='USA'
        )

        customer_address = customer.add_address(address)

        assert len(customer.addresses) == 1
        assert customer_address.address == address

    def test_first_address_is_default(self):
        """Test that first address is made default."""
        customer = Customer(Email('test@example.com'), "John Doe")

        address = Address(
            street='123 Main St',
            city='Springfield',
            postal_code='62701',
            country='USA'
        )

        customer_address = customer.add_address(address)

        assert customer_address.is_default

    def test_get_default_address(self):
        """Test getting default address."""
        customer = Customer(Email('test@example.com'), "John Doe")

        address = Address(
            street='123 Main St',
            city='Springfield',
            postal_code='62701',
            country='USA'
        )

        customer.add_address(address)

        default = customer.get_default_address()
        assert default == address

    def test_set_default_address(self):
        """Test setting address as default."""
        customer = Customer(Email('test@example.com'), "John Doe")

        addr1 = Address('123 Main St', 'Springfield', '62701', 'USA')
        addr2 = Address('456 Oak Ave', 'Chicago', '60601', 'USA')

        ca1 = customer.add_address(addr1)
        ca2 = customer.add_address(addr2)

        customer.set_default_address(ca2.id)

        assert not ca1.is_default
        assert ca2.is_default


class TestAggregateRepository:
    """Tests for aggregate repository."""

    def test_save_and_load_aggregate(self):
        """Test saving and loading aggregate."""
        repository = InMemoryAggregateRepository[Order]()

        order = Order(uuid4())
        order.add_item(uuid4(), "Widget", 1, Money(Decimal('10'), 'USD'))

        repository.save(order)

        loaded = repository.get_by_id(order.id)

        assert loaded is not None
        assert loaded.id == order.id
        assert len(loaded.items) == 1

    def test_repository_publishes_events(self):
        """Test that repository publishes events on save."""
        publisher = InMemoryEventPublisher()
        repository = InMemoryAggregateRepository[Order](publisher)

        order = Order(uuid4())
        order.add_item(uuid4(), "Widget", 1, Money(Decimal('10'), 'USD'))

        repository.save(order)

        # Events should be published
        assert len(publisher.published_events) > 0

    def test_repository_clears_events_after_save(self):
        """Test that repository clears events after save."""
        repository = InMemoryAggregateRepository[Order]()

        order = Order(uuid4())
        order.add_item(uuid4(), "Widget", 1, Money(Decimal('10'), 'USD'))

        repository.save(order)

        # Events should be cleared
        assert not order.has_domain_events()

    def test_repository_increments_version(self):
        """Test that repository increments version."""
        repository = InMemoryAggregateRepository[Order]()

        order = Order(uuid4())
        assert order.version == 0

        repository.save(order)
        assert order.version == 1

        repository.save(order)
        assert order.version == 2

    def test_delete_aggregate(self):
        """Test deleting aggregate."""
        repository = InMemoryAggregateRepository[Order]()

        order = Order(uuid4())
        repository.save(order)

        repository.delete(order)

        loaded = repository.get_by_id(order.id)
        assert loaded is None

    def test_exists(self):
        """Test checking if aggregate exists."""
        repository = InMemoryAggregateRepository[Order]()

        order = Order(uuid4())
        repository.save(order)

        assert repository.exists(order.id)
        assert not repository.exists(uuid4())


class TestEventPublisher:
    """Tests for event publisher."""

    def test_publish_event(self):
        """Test publishing event."""
        publisher = InMemoryEventPublisher()

        event = OrderCreated(uuid4(), uuid4())
        publisher.publish(event)

        assert len(publisher.published_events) == 1
        assert publisher.published_events[0] == event

    def test_publish_batch(self):
        """Test publishing multiple events."""
        publisher = InMemoryEventPublisher()

        events = [
            OrderCreated(uuid4(), uuid4()),
            OrderItemAdded(uuid4(), uuid4(), 1, Money(Decimal('10'), 'USD'))
        ]

        publisher.publish_batch(events)

        assert len(publisher.published_events) == 2

    def test_get_events_of_type(self):
        """Test filtering events by type."""
        publisher = InMemoryEventPublisher()

        publisher.publish(OrderCreated(uuid4(), uuid4()))
        publisher.publish(OrderItemAdded(uuid4(), uuid4(), 1, Money(Decimal('10'), 'USD')))
        publisher.publish(OrderCreated(uuid4(), uuid4()))

        created_events = publisher.get_events_of_type(OrderCreated)

        assert len(created_events) == 2
        assert all(isinstance(e, OrderCreated) for e in created_events)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
