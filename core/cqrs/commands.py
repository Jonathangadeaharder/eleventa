"""
Commands - Write Operations

Commands represent the intent to change the system's state.
They are imperative (CreateProduct, UpdateProduct) and may fail.

Key Principles:
- Commands are task-based, not data-centric
- Commands can fail (validation, business rules)
- Commands publish domain events on success
- Commands should be processed within a transaction
- One command = one business operation

Usage:
    command = CreateProductCommand(
        code="LAPTOP001",
        description="Dell Laptop",
        sell_price=Decimal('999.99'),
        user_id=current_user_id
    )

    result = command_handler.handle(command)

    if result.is_success:
        product_id = result.data
    else:
        print(result.error)
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from abc import ABC


class Command(ABC):
    """
    Base class for all commands.

    Commands represent intent to change state and are named
    in the imperative form (Create, Update, Delete, Process).
    """

    pass


# Product Commands


@dataclass(frozen=True)
class CreateProductCommand(Command):
    """
    Command to create a new product.

    This command will:
    1. Validate the product data
    2. Create the product
    3. Publish ProductCreated event
    """

    code: str
    description: str
    sell_price: Decimal
    cost_price: Optional[Decimal] = None
    department_id: Optional[UUID] = None
    uses_inventory: bool = True
    quantity_in_stock: Decimal = Decimal("0")
    min_stock: Optional[Decimal] = None
    max_stock: Optional[Decimal] = None
    unit_id: Optional[UUID] = None
    user_id: Optional[UUID] = None


@dataclass(frozen=True)
class UpdateProductCommand(Command):
    """
    Command to update an existing product.

    This command will:
    1. Fetch the existing product
    2. Validate the changes
    3. Apply the updates
    4. Publish ProductUpdated and/or ProductPriceChanged events
    """

    product_id: UUID
    code: Optional[str] = None
    description: Optional[str] = None
    sell_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    department_id: Optional[UUID] = None
    uses_inventory: Optional[bool] = None
    quantity_in_stock: Optional[Decimal] = None
    min_stock: Optional[Decimal] = None
    max_stock: Optional[Decimal] = None
    user_id: Optional[UUID] = None


@dataclass(frozen=True)
class DeleteProductCommand(Command):
    """
    Command to delete a product.

    This command will:
    1. Verify the product exists
    2. Check if deletion is allowed (no stock)
    3. Delete the product
    4. Publish ProductDeleted event
    """

    product_id: UUID
    user_id: Optional[UUID] = None


@dataclass(frozen=True)
class AdjustProductInventoryCommand(Command):
    """
    Command to adjust product inventory.

    This command will:
    1. Validate the product exists
    2. Adjust the inventory quantity
    3. Publish InventoryAdjusted event
    4. Publish LowStockDetected if below minimum
    """

    product_id: UUID
    adjustment_quantity: Decimal  # Positive = increase, negative = decrease
    reason: str
    user_id: Optional[UUID] = None


@dataclass(frozen=True)
class BulkUpdateProductPricesCommand(Command):
    """
    Command to update multiple product prices by percentage.

    This command will:
    1. Fetch products (optionally filtered by department)
    2. Calculate new prices
    3. Update all products
    4. Publish ProductPriceChanged for each product
    """

    percentage: Decimal
    department_id: Optional[UUID] = None
    user_id: Optional[UUID] = None


# Sale Commands


@dataclass(frozen=True)
class SaleItemCommand:
    """Item to add to a sale."""

    product_code: str
    quantity: Decimal
    unit_price: Optional[Decimal] = None


@dataclass(frozen=True)
class ProcessSaleCommand(Command):
    """
    Command to process a complete sale transaction.

    This command will:
    1. Validate all products exist and are in stock
    2. Validate customer credit (if credit sale)
    3. Validate payment
    4. Create the sale
    5. Update inventory
    6. Update customer balance (if credit)
    7. Publish SaleStarted, SaleItemAdded, SaleCompleted events
    """

    items: List[SaleItemCommand]
    customer_id: Optional[UUID] = None
    payment_type: str = "cash"  # cash, credit, card
    paid_amount: Decimal = Decimal("0")
    notes: Optional[str] = None
    user_id: Optional[UUID] = None


@dataclass(frozen=True)
class CancelSaleCommand(Command):
    """
    Command to cancel a sale.

    This command will:
    1. Verify sale exists and can be cancelled
    2. Restore inventory
    3. Reverse customer balance changes
    4. Publish SaleCancelled event
    """

    sale_id: UUID
    reason: str
    user_id: Optional[UUID] = None


# Customer Commands


@dataclass(frozen=True)
class CreateCustomerCommand(Command):
    """
    Command to create a new customer.

    This command will:
    1. Validate customer data
    2. Create the customer
    3. Publish CustomerCreated event
    """

    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    credit_limit: Decimal = Decimal("0")
    user_id: Optional[UUID] = None


@dataclass(frozen=True)
class UpdateCustomerCommand(Command):
    """Command to update customer details."""

    customer_id: UUID
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    user_id: Optional[UUID] = None


@dataclass(frozen=True)
class UpdateCustomerCreditLimitCommand(Command):
    """
    Command to update customer credit limit.

    This command will:
    1. Validate the new limit
    2. Update the credit limit
    3. Publish CustomerCreditLimitChanged event
    """

    customer_id: UUID
    new_credit_limit: Decimal
    user_id: Optional[UUID] = None


@dataclass(frozen=True)
class RecordCustomerPaymentCommand(Command):
    """
    Command to record a customer payment.

    This command will:
    1. Validate the customer and amount
    2. Update customer balance
    3. Create payment record
    4. Publish CustomerBalanceChanged event
    """

    customer_id: UUID
    amount: Decimal
    payment_type: str = "cash"
    notes: Optional[str] = None
    user_id: Optional[UUID] = None


# Inventory Commands


@dataclass(frozen=True)
class PerformInventoryCountCommand(Command):
    """
    Command to perform physical inventory count.

    This command will:
    1. Record actual counts
    2. Calculate variances
    3. Adjust inventory to actual
    4. Publish InventoryAdjusted events
    """

    counts: dict  # {product_id: actual_quantity}
    department_id: Optional[UUID] = None
    notes: Optional[str] = None
    user_id: Optional[UUID] = None
