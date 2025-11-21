"""
Tests for Domain Events Infrastructure

Tests the EventPublisher, domain events, and integration with Unit of Work.
"""

import pytest
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID, uuid4

from core.domain_events import DomainEvent, EventPublisher, MessageBus
from core.events.product_events import ProductCreated, ProductPriceChanged
from core.models.base import DomainModel, AggregateRoot


# Test fixtures

@pytest.fixture(autouse=True)
def clear_event_handlers():
    """Clear event handlers before and after each test for isolation."""
    EventPublisher.clear_handlers()
    yield
    EventPublisher.clear_handlers()


@dataclass(frozen=True)
class TestEvent(DomainEvent):
    """Simple test event."""
    test_data: str


class TestAggregate(DomainModel):
    """Test aggregate that can raise events."""

    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def do_something(self):
        """Perform an action and raise an event."""
        event = TestEvent(test_data=f"{self.name} did something")
        self._add_domain_event(event)


# Test cases

class TestDomainEventBase:
    """Test base DomainEvent functionality."""

    def test_domain_event_has_id(self):
        """Verify that domain events automatically get unique IDs."""
        event1 = TestEvent(test_data="test1")
        event2 = TestEvent(test_data="test2")

        assert hasattr(event1, 'event_id')
        assert isinstance(event1.event_id, UUID)
        assert event1.event_id != event2.event_id

    def test_domain_event_has_timestamp(self):
        """Verify that domain events have timestamps."""
        event = TestEvent(test_data="test")

        assert hasattr(event, 'occurred_at')
        assert event.occurred_at is not None

    def test_domain_event_is_immutable(self):
        """Verify that domain events are frozen (immutable)."""
        event = TestEvent(test_data="test")

        with pytest.raises(Exception):  # FrozenInstanceError
            event.test_data = "modified"


class TestEventPublisher:
    """Test EventPublisher functionality."""

    def test_subscribe_to_specific_event(self):
        """Test subscribing to a specific event type."""
        received_events = []

        @EventPublisher.subscribe(TestEvent)
        def handler(event: TestEvent):
            received_events.append(event)

        # Publish event
        event = TestEvent(test_data="test")
        EventPublisher.publish(event)

        # Verify handler was called
        assert len(received_events) == 1
        assert received_events[0] == event

    def test_multiple_handlers_for_same_event(self):
        """Test that multiple handlers can subscribe to the same event."""
        handler1_calls = []
        handler2_calls = []

        @EventPublisher.subscribe(TestEvent)
        def handler1(event: TestEvent):
            handler1_calls.append(event)

        @EventPublisher.subscribe(TestEvent)
        def handler2(event: TestEvent):
            handler2_calls.append(event)

        # Publish event
        event = TestEvent(test_data="test")
        EventPublisher.publish(event)

        # Both handlers should be called
        assert len(handler1_calls) == 1
        assert len(handler2_calls) == 1

    def test_subscribe_all_receives_all_events(self):
        """Test that subscribe_all receives all event types."""
        all_events = []

        @EventPublisher.subscribe_all
        def global_handler(event: DomainEvent):
            all_events.append(event)

        # Publish different event types
        event1 = TestEvent(test_data="test1")
        event2 = TestEvent(test_data="test2")

        EventPublisher.publish(event1)
        EventPublisher.publish(event2)

        # Global handler receives all
        assert len(all_events) == 2
        assert event1 in all_events
        assert event2 in all_events

    def test_handler_exception_doesnt_stop_other_handlers(self):
        """Test that if one handler fails, others still execute."""
        successful_calls = []

        @EventPublisher.subscribe(TestEvent)
        def failing_handler(event: TestEvent):
            raise ValueError("Handler failed!")

        @EventPublisher.subscribe(TestEvent)
        def successful_handler(event: TestEvent):
            successful_calls.append(event)

        # Publish event
        event = TestEvent(test_data="test")
        EventPublisher.publish(event)  # Should not raise

        # Successful handler should still be called
        assert len(successful_calls) == 1

    def test_clear_handlers(self):
        """Test that clear_handlers removes all subscriptions."""
        received_events = []

        @EventPublisher.subscribe(TestEvent)
        def handler(event: TestEvent):
            received_events.append(event)

        # Clear handlers
        EventPublisher.clear_handlers()

        # Publish event
        event = TestEvent(test_data="test")
        EventPublisher.publish(event)

        # Handler should not be called
        assert len(received_events) == 0

    def test_get_handlers(self):
        """Test retrieving handlers for an event type."""
        @EventPublisher.subscribe(TestEvent)
        def handler1(event):
            pass

        @EventPublisher.subscribe(TestEvent)
        def handler2(event):
            pass

        handlers = EventPublisher.get_handlers(TestEvent)

        assert len(handlers) == 2
        assert handler1 in handlers
        assert handler2 in handlers


class TestDomainModel:
    """Test DomainModel aggregate functionality."""

    def test_aggregate_can_raise_events(self):
        """Test that aggregates can raise domain events."""
        aggregate = TestAggregate(name="TestAgg")

        # Perform action that raises event
        aggregate.do_something()

        # Verify event was added
        events = aggregate.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], TestEvent)
        assert events[0].test_data == "TestAgg did something"

    def test_collect_domain_events_clears_list(self):
        """Test that collecting events clears the aggregate's event list."""
        aggregate = TestAggregate(name="TestAgg")
        aggregate.do_something()

        # Collect events
        events = aggregate.collect_domain_events()
        assert len(events) == 1

        # Event list should now be empty
        remaining_events = aggregate.get_domain_events()
        assert len(remaining_events) == 0

    def test_multiple_events_from_aggregate(self):
        """Test that aggregates can accumulate multiple events."""
        aggregate = TestAggregate(name="TestAgg")

        # Perform multiple actions
        aggregate.do_something()
        aggregate.do_something()
        aggregate.do_something()

        # Should have 3 events
        events = aggregate.get_domain_events()
        assert len(events) == 3


class TestProductEvents:
    """Test product-specific domain events."""

    def test_product_created_event(self):
        """Test ProductCreated event creation."""
        event = ProductCreated(
            product_id=uuid4(),
            code="TEST001",
            description="Test Product",
            sell_price=Decimal('99.99'),
            department_id=uuid4(),
            user_id=uuid4()
        )

        assert event.code == "TEST001"
        assert event.sell_price == Decimal('99.99')
        assert hasattr(event, 'event_id')
        assert hasattr(event, 'occurred_at')

    def test_product_price_changed_calculates_percentage(self):
        """Test that ProductPriceChanged calculates price change percentage."""
        event = ProductPriceChanged(
            product_id=uuid4(),
            code="TEST001",
            old_price=Decimal('100.00'),
            new_price=Decimal('150.00'),
            price_change_percent=Decimal('0'),  # Should be calculated
            user_id=uuid4()
        )

        # Should calculate 50% increase
        assert event.price_change_percent == Decimal('50.00')

    def test_price_changed_event_with_decrease(self):
        """Test price change percentage calculation for price decrease."""
        event = ProductPriceChanged(
            product_id=uuid4(),
            code="TEST001",
            old_price=Decimal('100.00'),
            new_price=Decimal('75.00'),
            price_change_percent=Decimal('0'),
            user_id=uuid4()
        )

        # Should calculate -25% (decrease)
        assert event.price_change_percent == Decimal('-25.00')


class TestEventPublisherIntegration:
    """Integration tests for event publishing workflow."""

    def test_complete_event_workflow(self):
        """Test a complete event publishing workflow."""
        published_events = []
        global_events = []

        # Set up handlers
        @EventPublisher.subscribe(ProductCreated)
        def product_handler(event: ProductCreated):
            published_events.append(event)

        @EventPublisher.subscribe_all
        def audit_handler(event: DomainEvent):
            global_events.append(event)

        # Create and publish event
        event = ProductCreated(
            product_id=uuid4(),
            code="LAPTOP001",
            description="Dell Laptop",
            sell_price=Decimal('999.99'),
            department_id=uuid4(),
            user_id=uuid4()
        )

        EventPublisher.publish(event)

        # Verify both handlers received the event
        assert len(published_events) == 1
        assert published_events[0] == event
        assert len(global_events) == 1
        assert global_events[0] == event

    def test_event_handler_can_be_decorated(self):
        """Test that event handlers work as decorators."""
        received = []

        @EventPublisher.subscribe(TestEvent)
        def my_handler(event: TestEvent):
            received.append(event.test_data)

        EventPublisher.publish(TestEvent(test_data="test1"))
        EventPublisher.publish(TestEvent(test_data="test2"))

        assert received == ["test1", "test2"]


# Note: Integration tests with Unit of Work are in
# tests/infrastructure/test_unit_of_work_events.py
