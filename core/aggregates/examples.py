"""
Example Aggregate Implementations

This module provides reference implementations of the Aggregate pattern
to demonstrate best practices.

Included Examples:
1. Order Aggregate - E-commerce order with line items
2. ShoppingCart Aggregate - Shopping cart before order placement
3. Customer Aggregate - Customer with addresses

These examples demonstrate:
- How to structure aggregates
- How to enforce business rules
- How to raise domain events
- How to handle internal entities
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from core.aggregates.base import AggregateRoot, Entity, DomainEvent, DomainError
from core.value_objects.money import Money
from core.value_objects.email import Email
from core.value_objects.address import Address


# ============================================================================
# ORDER AGGREGATE EXAMPLE
# ============================================================================

# Domain Events for Order

class OrderCreated(DomainEvent):
    """Event raised when order is created."""

    def __init__(self, order_id: UUID, customer_id: UUID):
        super().__init__(order_id)
        self.customer_id = customer_id


class OrderItemAdded(DomainEvent):
    """Event raised when item added to order."""

    def __init__(self, order_id: UUID, product_id: UUID, quantity: int, price: Money):
        super().__init__(order_id)
        self.product_id = product_id
        self.quantity = quantity
        self.price = price


class OrderItemRemoved(DomainEvent):
    """Event raised when item removed from order."""

    def __init__(self, order_id: UUID, item_id: UUID):
        super().__init__(order_id)
        self.item_id = item_id


class OrderSubmitted(DomainEvent):
    """Event raised when order is submitted."""

    def __init__(self, order_id: UUID, total: Money):
        super().__init__(order_id)
        self.total = total


class OrderCancelled(DomainEvent):
    """Event raised when order is cancelled."""

    def __init__(self, order_id: UUID, reason: str):
        super().__init__(order_id)
        self.reason = reason


# Order Line Item (Entity within Order aggregate)

class OrderItem(Entity):
    """
    Order line item entity.

    This is an entity within the Order aggregate.
    It has identity but is only accessed through the Order root.
    """

    def __init__(
        self,
        product_id: UUID,
        product_name: str,
        quantity: int,
        unit_price: Money
    ):
        """
        Create order item.

        Args:
            product_id: ID of the product
            product_name: Name of the product
            quantity: Quantity ordered
            unit_price: Price per unit
        """
        self.id = uuid4()
        self.product_id = product_id
        self.product_name = product_name
        self.quantity = quantity
        self.unit_price = unit_price

    @property
    def subtotal(self) -> Money:
        """Calculate line item subtotal."""
        return self.unit_price.multiply(self.quantity)

    def change_quantity(self, new_quantity: int) -> None:
        """
        Change quantity.

        Args:
            new_quantity: New quantity

        Raises:
            DomainError: If quantity invalid
        """
        if new_quantity <= 0:
            raise DomainError("Quantity must be positive")
        self.quantity = new_quantity

    def __repr__(self) -> str:
        return f"OrderItem(id={self.id}, product={self.product_name}, qty={self.quantity})"


# Order Aggregate Root

class Order(AggregateRoot):
    """
    Order aggregate root.

    The Order aggregate represents a customer's order with line items.
    It enforces business rules such as:
    - Minimum order amount
    - Cannot modify submitted orders
    - Must have at least one item to submit

    This demonstrates:
    - Aggregate root controlling access to entities
    - Business rule enforcement
    - Domain event emission
    - State management
    """

    # Order statuses
    STATUS_DRAFT = 'draft'
    STATUS_SUBMITTED = 'submitted'
    STATUS_CANCELLED = 'cancelled'

    # Business rules
    MINIMUM_ORDER_AMOUNT = Money(Decimal('10'), 'USD')
    MAX_ITEMS = 100

    def __init__(self, customer_id: UUID, currency: str = 'USD'):
        """
        Create new order.

        Args:
            customer_id: ID of the customer placing order
            currency: Currency for order (default: USD)
        """
        super().__init__()
        self.id = uuid4()
        self.customer_id = customer_id
        self.currency = currency
        self.status = self.STATUS_DRAFT
        self.items: List[OrderItem] = []
        self.submitted_at: Optional[datetime] = None
        self.cancelled_at: Optional[datetime] = None
        self.cancellation_reason: Optional[str] = None

        # Raise domain event
        self.add_domain_event(OrderCreated(self.id, customer_id))

    # Query methods

    @property
    def total(self) -> Money:
        """
        Calculate order total.

        Returns:
            Total amount
        """
        if not self.items:
            return Money.zero(self.currency)

        # Calculate total using Money.add() method
        total = Money.zero(self.currency)
        for item in self.items:
            total = total.add(item.subtotal)
        return total

    @property
    def item_count(self) -> int:
        """Get total number of items."""
        return sum(item.quantity for item in self.items)

    def get_item(self, item_id: UUID) -> Optional[OrderItem]:
        """
        Get item by ID.

        Args:
            item_id: Item ID

        Returns:
            Order item or None
        """
        for item in self.items:
            if item.id == item_id:
                return item
        return None

    def has_item(self, product_id: UUID) -> bool:
        """
        Check if order has item for product.

        Args:
            product_id: Product ID

        Returns:
            True if order has item
        """
        return any(item.product_id == product_id for item in self.items)

    # Command methods (enforce business rules)

    def add_item(
        self,
        product_id: UUID,
        product_name: str,
        quantity: int,
        unit_price: Money
    ) -> OrderItem:
        """
        Add item to order.

        Enforces:
        - Order must be in draft status
        - Maximum items limit
        - Currency consistency

        Args:
            product_id: Product ID
            product_name: Product name
            quantity: Quantity
            unit_price: Price per unit

        Returns:
            The created order item

        Raises:
            DomainError: If business rules violated
        """
        # Enforce: can only add items to draft orders
        if self.status != self.STATUS_DRAFT:
            raise DomainError(
                f"Cannot add items to {self.status} order"
            )

        # Enforce: maximum items limit
        if len(self.items) >= self.MAX_ITEMS:
            raise DomainError(
                f"Order cannot exceed {self.MAX_ITEMS} items"
            )

        # Enforce: currency consistency
        if unit_price.currency != self.currency:
            raise DomainError(
                f"Item currency {unit_price.currency} doesn't match order currency {self.currency}"
            )

        # Enforce: positive quantity
        if quantity <= 0:
            raise DomainError("Quantity must be positive")

        # Check if item already exists for this product
        for item in self.items:
            if item.product_id == product_id:
                # Update existing item quantity
                item.change_quantity(item.quantity + quantity)
                self.add_domain_event(
                    OrderItemAdded(self.id, product_id, quantity, unit_price)
                )
                return item

        # Create new item
        item = OrderItem(product_id, product_name, quantity, unit_price)
        self.items.append(item)

        # Raise domain event
        self.add_domain_event(
            OrderItemAdded(self.id, product_id, quantity, unit_price)
        )

        return item

    def remove_item(self, item_id: UUID) -> None:
        """
        Remove item from order.

        Args:
            item_id: Item ID to remove

        Raises:
            DomainError: If business rules violated
        """
        # Enforce: can only remove from draft orders
        if self.status != self.STATUS_DRAFT:
            raise DomainError(
                f"Cannot remove items from {self.status} order"
            )

        # Find and remove item
        for i, item in enumerate(self.items):
            if item.id == item_id:
                self.items.pop(i)
                self.add_domain_event(OrderItemRemoved(self.id, item_id))
                return

        raise DomainError(f"Item {item_id} not found in order")

    def change_item_quantity(self, item_id: UUID, new_quantity: int) -> None:
        """
        Change quantity of an item.

        Args:
            item_id: Item ID
            new_quantity: New quantity

        Raises:
            DomainError: If business rules violated
        """
        # Enforce: can only modify draft orders
        if self.status != self.STATUS_DRAFT:
            raise DomainError(
                f"Cannot modify {self.status} order"
            )

        # Find item
        item = self.get_item(item_id)
        if not item:
            raise DomainError(f"Item {item_id} not found")

        # Change quantity (item validates positive quantity)
        item.change_quantity(new_quantity)

    def submit(self) -> None:
        """
        Submit order for processing.

        Enforces:
        - Must be in draft status
        - Must have at least one item
        - Must meet minimum order amount

        Raises:
            DomainError: If business rules violated
        """
        # Enforce: must be draft
        if self.status != self.STATUS_DRAFT:
            raise DomainError(
                f"Cannot submit {self.status} order"
            )

        # Enforce: must have items
        if not self.items:
            raise DomainError(
                "Cannot submit order with no items"
            )

        # Enforce: minimum order amount
        if self.total < self.MINIMUM_ORDER_AMOUNT:
            raise DomainError(
                f"Order total {self.total} is below minimum {self.MINIMUM_ORDER_AMOUNT}"
            )

        # Change status
        self.status = self.STATUS_SUBMITTED
        self.submitted_at = datetime.utcnow()

        # Raise domain event
        self.add_domain_event(OrderSubmitted(self.id, self.total))

    def cancel(self, reason: str) -> None:
        """
        Cancel order.

        Args:
            reason: Cancellation reason

        Raises:
            DomainError: If cannot be cancelled
        """
        # Enforce: can only cancel draft or submitted orders
        if self.status == self.STATUS_CANCELLED:
            raise DomainError("Order already cancelled")

        # Cancel
        self.status = self.STATUS_CANCELLED
        self.cancelled_at = datetime.utcnow()
        self.cancellation_reason = reason

        # Raise domain event
        self.add_domain_event(OrderCancelled(self.id, reason))

    # Invariant checks

    def _check_invariants(self) -> None:
        """
        Check aggregate invariants.

        Called to validate aggregate is in valid state.
        """
        # All items must have same currency
        for item in self.items:
            if item.unit_price.currency != self.currency:
                raise DomainError("All items must have same currency")

        # Submitted orders must have items
        if self.status == self.STATUS_SUBMITTED and not self.items:
            raise DomainError("Submitted order must have items")

    def __repr__(self) -> str:
        return f"Order(id={self.id}, status={self.status}, items={len(self.items)}, total={self.total})"


# ============================================================================
# SHOPPING CART AGGREGATE EXAMPLE
# ============================================================================

class CartItemAdded(DomainEvent):
    """Event raised when item added to cart."""

    def __init__(self, cart_id: UUID, product_id: UUID, quantity: int):
        super().__init__(cart_id)
        self.product_id = product_id
        self.quantity = quantity


class CartCleared(DomainEvent):
    """Event raised when cart is cleared."""

    def __init__(self, cart_id: UUID):
        super().__init__(cart_id)


class CartItem(Entity):
    """Cart item entity."""

    def __init__(self, product_id: UUID, quantity: int):
        self.id = uuid4()
        self.product_id = product_id
        self.quantity = quantity
        self.added_at = datetime.utcnow()


class ShoppingCart(AggregateRoot):
    """
    Shopping cart aggregate.

    Simpler than Order - demonstrates a lightweight aggregate.
    """

    MAX_ITEMS_PER_PRODUCT = 99

    def __init__(self, customer_id: UUID):
        """Create shopping cart."""
        super().__init__()
        self.id = uuid4()
        self.customer_id = customer_id
        self.items: List[CartItem] = []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def add_item(self, product_id: UUID, quantity: int = 1) -> None:
        """Add item to cart."""
        if quantity <= 0:
            raise DomainError("Quantity must be positive")

        # Find existing item
        for item in self.items:
            if item.product_id == product_id:
                new_quantity = item.quantity + quantity
                if new_quantity > self.MAX_ITEMS_PER_PRODUCT:
                    raise DomainError(
                        f"Cannot add more than {self.MAX_ITEMS_PER_PRODUCT} of same product"
                    )
                item.quantity = new_quantity
                self.updated_at = datetime.utcnow()
                self.add_domain_event(CartItemAdded(self.id, product_id, quantity))
                return

        # Create new item
        item = CartItem(product_id, quantity)
        self.items.append(item)
        self.updated_at = datetime.utcnow()
        self.add_domain_event(CartItemAdded(self.id, product_id, quantity))

    def remove_item(self, product_id: UUID) -> None:
        """Remove item from cart."""
        for i, item in enumerate(self.items):
            if item.product_id == product_id:
                self.items.pop(i)
                self.updated_at = datetime.utcnow()
                return

        raise DomainError(f"Product {product_id} not in cart")

    def clear(self) -> None:
        """Clear all items from cart."""
        self.items.clear()
        self.updated_at = datetime.utcnow()
        self.add_domain_event(CartCleared(self.id))

    @property
    def item_count(self) -> int:
        """Get total quantity of items."""
        return sum(item.quantity for item in self.items)

    def __repr__(self) -> str:
        return f"ShoppingCart(id={self.id}, items={len(self.items)})"


# ============================================================================
# CUSTOMER AGGREGATE EXAMPLE (Demonstrates value object integration)
# ============================================================================

class CustomerRegistered(DomainEvent):
    """Event raised when customer registers."""

    def __init__(self, customer_id: UUID, email: str):
        super().__init__(customer_id)
        self.email = email


class CustomerAddressAdded(DomainEvent):
    """Event raised when address added."""

    def __init__(self, customer_id: UUID, address_id: UUID):
        super().__init__(customer_id)
        self.address_id = address_id


class CustomerAddress(Entity):
    """Customer address entity."""

    def __init__(self, address: Address, is_default: bool = False):
        self.id = uuid4()
        self.address = address  # Value Object!
        self.is_default = is_default
        self.added_at = datetime.utcnow()


class Customer(AggregateRoot):
    """
    Customer aggregate.

    Demonstrates integration with value objects.
    """

    def __init__(self, email: Email, name: str):
        """
        Create customer.

        Args:
            email: Customer email (value object)
            name: Customer name
        """
        super().__init__()
        self.id = uuid4()
        self.email = email  # Value Object
        self.name = name
        self.addresses: List[CustomerAddress] = []
        self.registered_at = datetime.utcnow()

        self.add_domain_event(CustomerRegistered(self.id, str(email)))

    def add_address(self, address: Address, make_default: bool = False) -> CustomerAddress:
        """
        Add address to customer.

        Args:
            address: Address value object
            make_default: Make this the default address

        Returns:
            The customer address entity
        """
        # If making default, unset other defaults
        if make_default:
            for addr in self.addresses:
                addr.is_default = False

        # If first address, make it default
        if not self.addresses:
            make_default = True

        customer_address = CustomerAddress(address, make_default)
        self.addresses.append(customer_address)

        self.add_domain_event(CustomerAddressAdded(self.id, customer_address.id))

        return customer_address

    def get_default_address(self) -> Optional[Address]:
        """Get default address."""
        for addr in self.addresses:
            if addr.is_default:
                return addr.address
        return None

    def set_default_address(self, address_id: UUID) -> None:
        """Set address as default."""
        found = False
        for addr in self.addresses:
            if addr.id == address_id:
                addr.is_default = True
                found = True
            else:
                addr.is_default = False

        if not found:
            raise DomainError(f"Address {address_id} not found")

    def __repr__(self) -> str:
        return f"Customer(id={self.id}, email={self.email}, name={self.name})"
