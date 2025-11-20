"""
Inventory-related domain events.

Events for inventory management and stock tracking.
"""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from core.domain_events import DomainEvent


@dataclass(frozen=True)
class InventoryAdjusted(DomainEvent):
    """
    Event raised when inventory is manually adjusted.

    Can trigger:
    - Audit trail updates
    - Variance reports
    - Cost accounting updates
    """

    product_id: UUID
    product_code: str
    adjustment_quantity: Decimal  # Positive for increase, negative for decrease
    new_quantity: Decimal
    reason: str
    user_id: UUID


@dataclass(frozen=True)
class LowStockDetected(DomainEvent):
    """
    Event raised when product stock falls below minimum threshold.

    Can trigger:
    - Reorder notifications
    - Purchase order generation
    - Manager alerts
    """

    product_id: UUID
    product_code: str
    product_description: str
    current_quantity: Decimal
    minimum_stock: Decimal
    reorder_point: Decimal


@dataclass(frozen=True)
class StockReplenished(DomainEvent):
    """
    Event raised when stock is replenished (purchase or transfer).

    Can trigger:
    - Inventory reports update
    - Cost basis updates
    - Stock availability notifications
    """

    product_id: UUID
    product_code: str
    quantity_added: Decimal
    new_quantity: Decimal
    cost_per_unit: Decimal
    total_cost: Decimal
    user_id: UUID
