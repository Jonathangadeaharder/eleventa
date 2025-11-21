"""
Base classes for domain models.

Implements the Aggregate pattern from Domain-Driven Design,
allowing entities to collect domain events during their operations.
"""

from typing import List
from core.domain_events import DomainEvent


class DomainModel:
    """
    Base class for domain models that can raise domain events.

    This implements the Aggregate pattern where entities can accumulate
    events during business operations. These events are later collected
    and published by the Unit of Work or Message Bus.

    Usage:
        class Product(DomainModel):
            def change_price(self, new_price: Decimal):
                old_price = self.sell_price
                self.sell_price = new_price
                self._add_domain_event(
                    ProductPriceChanged(
                        product_id=self.id,
                        old_price=old_price,
                        new_price=new_price
                    )
                )
    """

    def __init__(self):
        self._domain_events: List[DomainEvent] = []

    def _add_domain_event(self, event: DomainEvent) -> None:
        """
        Add a domain event to this aggregate's event list.

        Args:
            event: The domain event to add
        """
        self._domain_events.append(event)

    def _clear_domain_events(self) -> None:
        """Clear all domain events from this aggregate."""
        self._domain_events.clear()

    def get_domain_events(self) -> List[DomainEvent]:
        """
        Get all domain events raised by this aggregate.

        Returns:
            List of domain events
        """
        return self._domain_events.copy()

    def collect_domain_events(self) -> List[DomainEvent]:
        """
        Collect and clear all domain events from this aggregate.

        This is typically called by the Unit of Work after committing.

        Returns:
            List of domain events
        """
        events = self._domain_events.copy()
        self._clear_domain_events()
        return events


class AggregateRoot(DomainModel):
    """
    Marker class for aggregate roots.

    An aggregate root is the main entity in an aggregate that controls
    access to all other entities within the aggregate. Only aggregate
    roots should be directly accessed by repositories.

    Examples of aggregate roots in this system:
    - Product
    - Sale (with SaleItems)
    - Customer
    - Invoice
    """

    pass
