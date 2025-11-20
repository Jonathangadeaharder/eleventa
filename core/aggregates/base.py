"""
Base Aggregate Classes

Provides foundation for implementing aggregates in Domain-Driven Design.

Aggregate Pattern:
- AggregateRoot: Main entity that controls the aggregate
- Entity: Objects with identity within the aggregate
- Consistency Boundary: Business rules enforced by aggregate

Key Differences from Entities:
- Entities have identity but may belong to aggregates
- Aggregate Roots are special entities that control access
- Only aggregate roots are retrieved from repositories
- Invariants are enforced at aggregate boundary
"""

from abc import ABC
from typing import List, Any
from datetime import datetime


class DomainEvent:
    """
    Base class for domain events.

    Domain events represent something that happened in the domain
    that domain experts care about.

    Attributes:
        occurred_at: When the event occurred
        aggregate_id: ID of the aggregate that raised the event
    """

    def __init__(self, aggregate_id: Any):
        self.occurred_at = datetime.utcnow()
        self.aggregate_id = aggregate_id

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(aggregate_id={self.aggregate_id}, occurred_at={self.occurred_at})"


class DomainError(Exception):
    """
    Exception for domain rule violations.

    Raised when an operation would violate business rules.

    Usage:
        if order.total < minimum_order_amount:
            raise DomainError("Order total below minimum")
    """

    pass


class Entity(ABC):
    """
    Base class for entities within aggregates.

    Entities have:
    - Identity (tracked by ID)
    - Lifecycle (created, modified, deleted)
    - Can be compared by ID

    Entities vs Value Objects:
    - Entities: Identity-based equality (same ID = same entity)
    - Value Objects: Value-based equality (same values = same object)

    Usage:
        class OrderItem(Entity):
            def __init__(self, product_id, quantity, price):
                self.id = uuid4()
                self.product_id = product_id
                self.quantity = quantity
                self.price = price

            @property
            def subtotal(self):
                return self.quantity * self.price
    """

    id: Any  # Entity ID - can be UUID, int, etc.

    def __eq__(self, other: Any) -> bool:
        """
        Entities are equal if they have the same ID.

        Args:
            other: Object to compare with

        Returns:
            True if same ID
        """
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """
        Hash based on ID.

        Returns:
            Hash of entity ID
        """
        return hash(self.id)

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(id={self.id})"


class AggregateRoot(Entity):
    """
    Base class for aggregate roots.

    Aggregate roots:
    - Are special entities that control access to the aggregate
    - Enforce consistency boundaries
    - Raise domain events
    - Are the only objects retrieved from repositories

    Responsibilities:
    1. Enforce business rules (invariants)
    2. Control access to internal entities
    3. Emit domain events for important changes
    4. Maintain consistency within the aggregate

    Usage:
        class Order(AggregateRoot):
            def __init__(self, customer_id):
                super().__init__()
                self.id = uuid4()
                self.customer_id = customer_id
                self.items = []
                self._total = Decimal('0')
                self.status = 'draft'

            def add_item(self, product_id, quantity, price):
                '''Add item - enforces business rules.'''
                if self.status != 'draft':
                    raise DomainError("Cannot modify finalized order")

                item = OrderItem(product_id, quantity, price)
                self.items.append(item)
                self._recalculate_total()

                # Emit domain event
                self.add_domain_event(OrderItemAdded(self.id, item.id))

            def finalize(self):
                '''Finalize order - enforces minimum total.'''
                if self._total < Decimal('10'):
                    raise DomainError("Order total must be at least $10")

                self.status = 'finalized'
                self.add_domain_event(OrderFinalized(self.id))

    Best Practices:
    1. Keep aggregates small (only what needs consistency)
    2. Reference other aggregates by ID only
    3. Update only one aggregate per transaction
    4. Use domain events for cross-aggregate coordination
    """

    def __init__(self):
        """Initialize aggregate root."""
        self._domain_events: List[DomainEvent] = []
        self._version: int = 0  # For optimistic locking

    @property
    def version(self) -> int:
        """
        Get aggregate version for optimistic locking.

        Returns:
            Current version number
        """
        return self._version

    def _increment_version(self) -> None:
        """Increment version (called by repository after save)."""
        self._version += 1

    def add_domain_event(self, event: DomainEvent) -> None:
        """
        Add a domain event.

        Domain events are raised when something important happens
        that other parts of the system might need to react to.

        Args:
            event: The domain event to add

        Usage:
            self.add_domain_event(OrderCreated(self.id, self.customer_id))
        """
        self._domain_events.append(event)

    def get_domain_events(self) -> List[DomainEvent]:
        """
        Get all pending domain events.

        Returns:
            List of domain events

        Note:
            Called by repository to publish events after save.
        """
        return self._domain_events.copy()

    def clear_domain_events(self) -> None:
        """
        Clear pending domain events.

        Called by repository after events are published.
        """
        self._domain_events.clear()

    def has_domain_events(self) -> bool:
        """
        Check if aggregate has pending domain events.

        Returns:
            True if there are pending events
        """
        return len(self._domain_events) > 0


class AggregateNotFoundError(Exception):
    """
    Exception raised when aggregate not found in repository.

    Usage:
        order = order_repository.get_by_id(order_id)
        if not order:
            raise AggregateNotFoundError(f"Order {order_id} not found")
    """

    pass


class ConcurrencyError(Exception):
    """
    Exception raised when concurrent modification detected.

    This is raised when optimistic locking detects that the aggregate
    has been modified by another transaction.

    Usage:
        # Repository implementation
        if aggregate.version != db_version:
            raise ConcurrencyError(
                f"Aggregate has been modified by another transaction"
            )
    """

    pass


# Helper functions for aggregate design


def ensure_aggregate_invariants(aggregate: AggregateRoot) -> None:
    """
    Validate aggregate invariants.

    This is a helper that can be called after operations to ensure
    the aggregate is in a valid state.

    Args:
        aggregate: The aggregate to validate

    Raises:
        DomainError: If invariants are violated

    Usage:
        class Order(AggregateRoot):
            def add_item(self, item):
                self.items.append(item)
                ensure_aggregate_invariants(self)

            def _check_invariants(self):
                if len(self.items) == 0:
                    raise DomainError("Order must have at least one item")
                if self.total <= 0:
                    raise DomainError("Order total must be positive")
    """
    if hasattr(aggregate, "_check_invariants"):
        aggregate._check_invariants()


def create_aggregate_snapshot(aggregate: AggregateRoot) -> dict:
    """
    Create a snapshot of aggregate state.

    Useful for:
    - Memento pattern
    - Auditing
    - Debugging

    Args:
        aggregate: The aggregate to snapshot

    Returns:
        Dictionary with aggregate state

    Usage:
        snapshot = create_aggregate_snapshot(order)
        # Later, restore from snapshot
        order = restore_aggregate_from_snapshot(Order, snapshot)
    """
    # This is a simplified version - real implementation would use
    # proper serialization
    return {
        "type": aggregate.__class__.__name__,
        "id": aggregate.id,
        "version": aggregate.version,
        "state": aggregate.__dict__.copy(),
    }


# Aggregate design guidelines (as constants for documentation)

AGGREGATE_DESIGN_RULES = """
Aggregate Design Rules:

1. **Small Aggregates**: Keep aggregates as small as possible
   - Only include what needs consistency
   - Use domain events for coordination across aggregates

2. **Reference by ID**: Reference other aggregates by ID only
   - Don't hold object references to other aggregates
   - Load other aggregates separately when needed

3. **One Aggregate Per Transaction**: Update only one aggregate per transaction
   - Use eventual consistency for multi-aggregate operations
   - Coordinate with domain events

4. **Enforce Invariants**: Aggregate root enforces all business rules
   - Validate in methods, not constructors
   - Throw DomainError for violations

5. **Raise Domain Events**: Emit events for important changes
   - Events are facts (past tense: OrderCreated, not CreateOrder)
   - Other aggregates can react to events

6. **Protect Boundaries**: Don't expose internal entities
   - External code calls methods on root
   - Root controls access to internal entities

Examples:

✅ Good: Small, focused aggregate
class Order(AggregateRoot):
    def __init__(self, customer_id):
        self.customer_id = customer_id  # Reference by ID
        self.items = []  # Internal entities

    def add_item(self, product_id, quantity, price):
        # Business rule enforcement
        if len(self.items) >= 100:
            raise DomainError("Order cannot exceed 100 items")

        item = OrderItem(product_id, quantity, price)
        self.items.append(item)
        self.add_domain_event(OrderItemAdded(self.id, item.id))

❌ Bad: Large aggregate with dependencies
class Order(AggregateRoot):
    def __init__(self):
        self.customer = Customer(...)  # Don't embed other aggregates!
        self.products = [Product(...), ...]  # Don't load all products!
        self.inventory = Inventory(...)  # Crosses consistency boundary!
"""
