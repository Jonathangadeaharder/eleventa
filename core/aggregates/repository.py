"""
Aggregate Repository Interfaces

Repositories for aggregates follow specific patterns:
- Load entire aggregate as a unit
- Save entire aggregate as a unit
- Publish domain events after save
- Support optimistic locking

The repository is responsible for:
1. Reconstituting aggregates from persistence
2. Saving aggregate state atomically
3. Publishing domain events
4. Handling concurrency
"""

from abc import ABC, abstractmethod
from typing import Optional, TypeVar, Generic, List
from core.aggregates.base import AggregateRoot, DomainEvent

T = TypeVar('T', bound=AggregateRoot)


class IAggregateRepository(ABC, Generic[T]):
    """
    Base interface for aggregate repositories.

    Aggregate repositories:
    - Load and save entire aggregates
    - Publish domain events after save
    - Support optimistic locking
    - Maintain transactional consistency

    Usage:
        class IOrderRepository(IAggregateRepository[Order]):
            '''Repository for Order aggregate.'''

            @abstractmethod
            def get_by_customer_id(self, customer_id: UUID) -> List[Order]:
                '''Find orders for customer.'''
                pass

        # Implementation
        class OrderRepository(IOrderRepository):
            def __init__(self, session, event_publisher):
                self.session = session
                self.event_publisher = event_publisher

            def get_by_id(self, order_id: UUID) -> Optional[Order]:
                # Load aggregate with all entities
                order_orm = self.session.query(OrderOrm).filter(
                    OrderOrm.id == order_id
                ).first()

                if not order_orm:
                    return None

                return self._orm_to_aggregate(order_orm)

            def save(self, order: Order) -> None:
                # Save entire aggregate
                order_orm = self._aggregate_to_orm(order)
                self.session.add(order_orm)
                self.session.flush()

                # Publish domain events
                for event in order.get_domain_events():
                    self.event_publisher.publish(event)

                order.clear_domain_events()
                order._increment_version()
    """

    @abstractmethod
    def get_by_id(self, aggregate_id) -> Optional[T]:
        """
        Retrieve aggregate by ID.

        Loads the entire aggregate including all internal entities.

        Args:
            aggregate_id: The aggregate's unique identifier

        Returns:
            The aggregate or None if not found

        Usage:
            order = order_repository.get_by_id(order_id)
            if order:
                order.add_item(product_id, quantity, price)
                order_repository.save(order)
        """
        pass  # pragma: no cover

    @abstractmethod
    def save(self, aggregate: T) -> None:
        """
        Save aggregate.

        This should:
        1. Save the entire aggregate atomically
        2. Publish domain events
        3. Clear published events
        4. Increment version for optimistic locking

        Args:
            aggregate: The aggregate to save

        Raises:
            ConcurrencyError: If aggregate was modified by another transaction

        Usage:
            order.add_item(product_id, quantity, price)
            order_repository.save(order)  # Saves order + publishes events
        """
        pass  # pragma: no cover

    @abstractmethod
    def delete(self, aggregate: T) -> None:
        """
        Delete aggregate.

        Removes the aggregate and all its internal entities.

        Args:
            aggregate: The aggregate to delete

        Usage:
            order = order_repository.get_by_id(order_id)
            if order.can_be_cancelled():
                order_repository.delete(order)
        """
        pass  # pragma: no cover

    def exists(self, aggregate_id) -> bool:
        """
        Check if aggregate exists.

        Args:
            aggregate_id: The aggregate's unique identifier

        Returns:
            True if aggregate exists

        Usage:
            if not order_repository.exists(order_id):
                raise AggregateNotFoundError(f"Order {order_id} not found")
        """
        return self.get_by_id(aggregate_id) is not None


class EventPublisher(ABC):
    """
    Interface for publishing domain events.

    Event publishers are used by repositories to publish
    domain events after aggregate is saved.

    Usage:
        class EventPublisher:
            def __init__(self, event_bus):
                self.event_bus = event_bus

            def publish(self, event: DomainEvent):
                self.event_bus.publish(event)

            def publish_batch(self, events: List[DomainEvent]):
                for event in events:
                    self.publish(event)
    """

    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        """
        Publish a single domain event.

        Args:
            event: The event to publish
        """
        pass  # pragma: no cover

    @abstractmethod
    def publish_batch(self, events: List[DomainEvent]) -> None:
        """
        Publish multiple domain events.

        Args:
            events: The events to publish
        """
        pass  # pragma: no cover


class InMemoryEventPublisher(EventPublisher):
    """
    In-memory event publisher for testing.

    Stores published events in memory for verification.

    Usage:
        publisher = InMemoryEventPublisher()
        repository = OrderRepository(session, publisher)

        order.add_item(...)
        repository.save(order)

        # Verify events published
        assert len(publisher.published_events) == 1
        assert isinstance(publisher.published_events[0], OrderItemAdded)
    """

    def __init__(self):
        self.published_events: List[DomainEvent] = []

    def publish(self, event: DomainEvent) -> None:
        """Publish event to in-memory list."""
        self.published_events.append(event)

    def publish_batch(self, events: List[DomainEvent]) -> None:
        """Publish multiple events."""
        self.published_events.extend(events)

    def clear(self) -> None:
        """Clear published events."""
        self.published_events.clear()

    def get_events_of_type(self, event_type: type) -> List[DomainEvent]:
        """
        Get events of specific type.

        Args:
            event_type: The event class to filter by

        Returns:
            List of events of that type
        """
        return [e for e in self.published_events if isinstance(e, event_type)]


class AggregateRepositoryBase(IAggregateRepository[T], Generic[T]):
    """
    Base implementation for aggregate repositories.

    Provides common functionality:
    - Event publishing after save
    - Version management
    - Template methods for subclasses

    Subclasses implement:
    - _load_aggregate(aggregate_id) -> Optional[T]
    - _save_aggregate(aggregate: T) -> None
    - _delete_aggregate(aggregate: T) -> None

    Usage:
        class OrderRepository(AggregateRepositoryBase[Order]):
            def __init__(self, session, event_publisher):
                super().__init__(event_publisher)
                self.session = session

            def _load_aggregate(self, order_id: UUID) -> Optional[Order]:
                # Load from database
                order_orm = self.session.query(OrderOrm).filter(
                    OrderOrm.id == order_id
                ).first()

                if not order_orm:
                    return None

                return self._orm_to_aggregate(order_orm)

            def _save_aggregate(self, order: Order) -> None:
                # Save to database
                order_orm = self._aggregate_to_orm(order)
                self.session.merge(order_orm)
    """

    def __init__(self, event_publisher: EventPublisher):
        """
        Initialize repository.

        Args:
            event_publisher: Publisher for domain events
        """
        self.event_publisher = event_publisher

    def get_by_id(self, aggregate_id) -> Optional[T]:
        """
        Load aggregate by ID.

        Delegates to _load_aggregate() implemented by subclass.

        Args:
            aggregate_id: The aggregate ID

        Returns:
            The aggregate or None
        """
        return self._load_aggregate(aggregate_id)

    def save(self, aggregate: T) -> None:
        """
        Save aggregate and publish events.

        Template method that:
        1. Saves aggregate (via _save_aggregate)
        2. Publishes domain events
        3. Clears events
        4. Increments version

        Args:
            aggregate: The aggregate to save
        """
        # Save aggregate state
        self._save_aggregate(aggregate)

        # Publish domain events
        if aggregate.has_domain_events():
            events = aggregate.get_domain_events()
            self.event_publisher.publish_batch(events)
            aggregate.clear_domain_events()

        # Increment version for optimistic locking
        aggregate._increment_version()

    def delete(self, aggregate: T) -> None:
        """
        Delete aggregate.

        Delegates to _delete_aggregate() implemented by subclass.

        Args:
            aggregate: The aggregate to delete
        """
        self._delete_aggregate(aggregate)

    # Abstract methods for subclasses

    @abstractmethod
    def _load_aggregate(self, aggregate_id) -> Optional[T]:
        """
        Load aggregate from persistence.

        Subclasses implement this to load from database.

        Args:
            aggregate_id: The aggregate ID

        Returns:
            The aggregate or None
        """
        pass  # pragma: no cover

    @abstractmethod
    def _save_aggregate(self, aggregate: T) -> None:
        """
        Save aggregate to persistence.

        Subclasses implement this to save to database.

        Args:
            aggregate: The aggregate to save
        """
        pass  # pragma: no cover

    @abstractmethod
    def _delete_aggregate(self, aggregate: T) -> None:
        """
        Delete aggregate from persistence.

        Subclasses implement this to delete from database.

        Args:
            aggregate: The aggregate to delete
        """
        pass  # pragma: no cover


# In-memory repository for testing

class InMemoryAggregateRepository(IAggregateRepository[T], Generic[T]):
    """
    In-memory repository for testing.

    Stores aggregates in memory with simple dict.

    Usage:
        repository = InMemoryAggregateRepository[Order]()

        order = Order(customer_id)
        order.add_item(product_id, 1, Money(Decimal('10'), 'USD'))
        repository.save(order)

        loaded = repository.get_by_id(order.id)
        assert loaded == order
    """

    def __init__(self, event_publisher: Optional[EventPublisher] = None):
        """
        Initialize in-memory repository.

        Args:
            event_publisher: Optional event publisher
        """
        self._storage: dict = {}
        self.event_publisher = event_publisher or InMemoryEventPublisher()

    def get_by_id(self, aggregate_id) -> Optional[T]:
        """Get aggregate from memory."""
        return self._storage.get(aggregate_id)

    def save(self, aggregate: T) -> None:
        """Save aggregate to memory."""
        # Store aggregate
        self._storage[aggregate.id] = aggregate

        # Publish events
        if aggregate.has_domain_events():
            events = aggregate.get_domain_events()
            self.event_publisher.publish_batch(events)
            aggregate.clear_domain_events()

        # Increment version
        aggregate._increment_version()

    def delete(self, aggregate: T) -> None:
        """Delete aggregate from memory."""
        if aggregate.id in self._storage:
            del self._storage[aggregate.id]

    def get_all(self) -> List[T]:
        """Get all aggregates (for testing)."""
        return list(self._storage.values())

    def clear(self) -> None:
        """Clear all aggregates (for testing)."""
        self._storage.clear()

    def count(self) -> int:
        """Count aggregates (for testing)."""
        return len(self._storage)
