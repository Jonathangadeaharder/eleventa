"""
Sale-related domain events.

Events that occur during the sales process.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import UUID

from core.domain_events import DomainEvent


@dataclass(frozen=True)
class SaleStarted(DomainEvent):
    """
    Event raised when a new sale transaction is initiated.

    Marks the beginning of a sale transaction before items are added.
    """

    sale_id: UUID
    customer_id: Optional[UUID]
    user_id: UUID


@dataclass(frozen=True)
class SaleItemAdded(DomainEvent):
    """
    Event raised when an item is added to a sale.

    Can trigger:
    - Real-time inventory checks
    - Price verification
    - Promotion application
    """

    sale_id: UUID
    product_id: UUID
    product_code: str
    quantity: Decimal
    unit_price: Decimal
    subtotal: Decimal


@dataclass(frozen=True)
class SaleItemRemoved(DomainEvent):
    """
    Event raised when an item is removed from a sale.

    Can trigger:
    - Inventory adjustment reversal
    - Discount recalculation
    """

    sale_id: UUID
    product_id: UUID
    product_code: str
    quantity: Decimal


@dataclass(frozen=True)
class SaleCompleted(DomainEvent):
    """
    Event raised when a sale is finalized.

    This is a critical event that triggers:
    - Inventory deduction
    - Payment processing
    - Receipt generation
    - Loyalty points calculation
    - Sales analytics update
    - Customer balance update (for credit sales)
    """

    sale_id: UUID
    customer_id: Optional[UUID]
    total_amount: Decimal
    payment_type: str  # 'cash', 'credit', 'card', etc.
    paid_amount: Decimal
    change_amount: Decimal
    user_id: UUID
    has_credit: bool  # Whether this sale involved customer credit


@dataclass(frozen=True)
class SaleCancelled(DomainEvent):
    """
    Event raised when a sale is cancelled.

    Can trigger:
    - Inventory restoration
    - Payment reversal
    - Audit logging
    """

    sale_id: UUID
    reason: str
    user_id: UUID


@dataclass(frozen=True)
class PaymentReceived(DomainEvent):
    """
    Event raised when payment is received for a sale.

    For credit sales, this can happen after the sale is completed.
    """

    sale_id: UUID
    customer_id: Optional[UUID]
    amount: Decimal
    payment_type: str
    user_id: UUID
