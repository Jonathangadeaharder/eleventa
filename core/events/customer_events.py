"""
Customer-related domain events.

Events related to customer lifecycle and credit management.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import UUID

from core.domain_events import DomainEvent


@dataclass(frozen=True)
class CustomerCreated(DomainEvent):
    """
    Event raised when a new customer is registered.

    Can trigger:
    - Welcome notifications
    - Loyalty program enrollment
    - CRM system updates
    """

    customer_id: UUID
    name: str
    email: Optional[str]
    phone: Optional[str]
    user_id: UUID


@dataclass(frozen=True)
class CustomerUpdated(DomainEvent):
    """
    Event raised when customer details are updated.
    """

    customer_id: UUID
    updated_fields: dict
    user_id: UUID


@dataclass(frozen=True)
class CustomerCreditLimitChanged(DomainEvent):
    """
    Event raised when a customer's credit limit changes.

    Important for:
    - Risk management
    - Approval workflows
    - Credit monitoring
    """

    customer_id: UUID
    customer_name: str
    old_limit: Decimal
    new_limit: Decimal
    user_id: UUID


@dataclass(frozen=True)
class CustomerBalanceChanged(DomainEvent):
    """
    Event raised when customer's credit balance changes.

    Can trigger:
    - Balance alerts
    - Payment reminders
    - Credit limit checks
    """

    customer_id: UUID
    customer_name: str
    old_balance: Decimal
    new_balance: Decimal
    change_amount: Decimal
    reason: str  # 'sale', 'payment', 'adjustment'
    user_id: UUID
