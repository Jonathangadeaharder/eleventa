"""
Aggregates Module

Aggregates are a core pattern in Domain-Driven Design that define
consistency boundaries and enforce business rules.

Key Concepts:
- Aggregate Root: The main entity that controls access to the aggregate
- Entity: Objects with identity within the aggregate
- Consistency Boundary: Business rules enforced within the aggregate
- Transactional Consistency: Changes are committed as a unit

Available Components:
- AggregateRoot: Base class for aggregate roots
- Entity: Base class for entities within aggregates
- AggregateRepository: Repository pattern for aggregates

Usage:
    from core.aggregates import AggregateRoot, Entity
    from uuid import uuid4

    class Order(AggregateRoot):
        '''Order aggregate root.'''

        def __init__(self, customer_id):
            super().__init__()
            self.id = uuid4()
            self.customer_id = customer_id
            self.items = []
            self._total = Decimal('0')

        def add_item(self, product_id, quantity, price):
            '''Add item to order - enforces business rules.'''
            if self.is_finalized:
                raise DomainError("Cannot add items to finalized order")

            item = OrderItem(product_id, quantity, price)
            self.items.append(item)
            self._recalculate_total()

            self.add_domain_event(OrderItemAdded(self.id, item))

        def finalize(self):
            '''Finalize order - enforces minimum total rule.'''
            if self._total < Decimal('10'):
                raise DomainError("Order total must be at least $10")

            self.is_finalized = True
            self.add_domain_event(OrderFinalized(self.id, self._total))

Design Principles:
1. Aggregate roots control all access to entities within
2. External objects hold references only to the root
3. Business rules are enforced by the aggregate
4. All changes go through the aggregate root
5. Aggregates are loaded and saved as a unit
"""

from core.aggregates.base import AggregateRoot, Entity
from core.aggregates.repository import IAggregateRepository

__all__ = [
    'AggregateRoot',
    'Entity',
    'IAggregateRepository',
]
