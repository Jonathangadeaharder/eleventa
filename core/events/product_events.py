"""
Product-related domain events.

Events that can occur during the lifecycle of a Product aggregate.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import UUID

from core.domain_events import DomainEvent


@dataclass(frozen=True)
class ProductCreated(DomainEvent):
    """
    Event raised when a new product is created in the system.

    This event can trigger:
    - Notification to inventory management
    - Update to product catalog displays
    - Audit log entry
    """

    product_id: UUID
    code: str
    description: str
    sell_price: Decimal
    department_id: Optional[UUID]
    user_id: UUID  # User who created the product


@dataclass(frozen=True)
class ProductUpdated(DomainEvent):
    """
    Event raised when product details are updated.

    This is a general update event. More specific events like
    ProductPriceChanged should be used for important changes.
    """

    product_id: UUID
    updated_fields: dict  # Fields that were changed
    user_id: UUID


@dataclass(frozen=True)
class ProductPriceChanged(DomainEvent):
    """
    Event raised when a product's price changes.

    This is important enough to be its own event because it can trigger:
    - Price history tracking
    - Notification to managers
    - Update to price tags/labels
    - Analytics updates
    """

    product_id: UUID
    code: str
    old_price: Decimal
    new_price: Decimal
    price_change_percent: Decimal
    user_id: UUID

    def __post_init__(self):
        super().__post_init__()

        # Calculate price change percentage
        if self.old_price > 0:
            change = ((self.new_price - self.old_price) / self.old_price) * 100
            object.__setattr__(self, 'price_change_percent', round(change, 2))
        else:
            object.__setattr__(self, 'price_change_percent', Decimal('0'))


@dataclass(frozen=True)
class ProductStockChanged(DomainEvent):
    """
    Event raised when product stock quantity changes.

    Can trigger:
    - Low stock alerts
    - Reorder point checks
    - Inventory reports update
    """

    product_id: UUID
    code: str
    old_quantity: Decimal
    new_quantity: Decimal
    reason: str  # 'sale', 'purchase', 'adjustment', etc.
    user_id: UUID


@dataclass(frozen=True)
class ProductDeleted(DomainEvent):
    """
    Event raised when a product is deleted (soft delete).

    Can trigger:
    - Archive operations
    - Cleanup of related data
    - Audit logging
    """

    product_id: UUID
    code: str
    description: str
    user_id: UUID
