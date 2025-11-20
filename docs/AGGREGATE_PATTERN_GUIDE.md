# Aggregate Pattern Guide

## Table of Contents
1. [Overview](#overview)
2. [What are Aggregates?](#what-are-aggregates)
3. [Why Use Aggregates?](#why-use-aggregates)
4. [Core Concepts](#core-concepts)
5. [Design Guidelines](#design-guidelines)
6. [Creating Aggregates](#creating-aggregates)
7. [Examples](#examples)
8. [Repository Integration](#repository-integration)
9. [Best Practices](#best-practices)
10. [Common Pitfalls](#common-pitfalls)
11. [Testing](#testing)

## Overview

**Aggregates** are a fundamental pattern in Domain-Driven Design that define consistency boundaries and enforce business rules. They group related entities and value objects into clusters that are treated as a unit for data changes.

### Key Benefits

- **Consistency**: Enforces business rules within boundaries
- **Transactional Integrity**: Changes are atomic
- **Clear Boundaries**: Defines what changes together
- **Encapsulation**: Hides internal structure
- **Testability**: Easy to unit test business logic

### When to Use

✅ **Use Aggregates For:**
- Groups of objects that must change together
- Complex business rules spanning multiple entities
- Transactional consistency boundaries
- Domain model with rich behavior

❌ **Don't Use Aggregates For:**
- Simple CRUD operations
- Entities with no business rules
- Read-only data
- Cross-cutting concerns

## What are Aggregates?

### Definition

An **Aggregate** is a cluster of domain objects (entities and value objects) that can be treated as a single unit. One entity in the cluster is the **Aggregate Root**, which is the only entry point for operations on the aggregate.

### Components

1. **Aggregate Root**: The main entity that controls the aggregate
2. **Entities**: Objects with identity within the aggregate
3. **Value Objects**: Objects identified by their values
4. **Consistency Boundary**: The scope where business rules are enforced

### Example: Order Aggregate

```
Order (Aggregate Root)
├── OrderItems (Entities)
│   ├── OrderItem 1
│   ├── OrderItem 2
│   └── OrderItem 3
└── ShippingAddress (Value Object)
```

External objects:
- Hold reference to Order ID only
- Call methods on Order root
- Cannot directly modify OrderItems

## Why Use Aggregates?

### Problem: Without Aggregates

```python
# ❌ Problem: No consistency boundary

# Anyone can modify order items directly
order_item = order_item_repository.get(item_id)
order_item.quantity = 10  # No validation!
order_item.price = Money(Decimal('-100'), 'USD')  # Negative price!
order_item_repository.save(order_item)

# Order total is now inconsistent
order = order_repository.get(order_id)
print(order.total)  # Wrong! Doesn't include item changes
```

**Problems:**
- No business rule enforcement
- Inconsistent state
- Scattered logic
- Race conditions

### Solution: With Aggregates

```python
# ✅ Solution: Aggregate enforces rules

order = order_repository.get(order_id)

# All changes go through aggregate root
order.change_item_quantity(item_id, 10)  # Validated!

# Business rules enforced
try:
    order.change_item_quantity(item_id, -1)
except DomainError as e:
    print("Quantity must be positive")  # Caught!

# Total is automatically consistent
print(order.total)  # Correct!

# Save entire aggregate atomically
order_repository.save(order)
```

## Core Concepts

### 1. Aggregate Root

The **Aggregate Root** is the only entity that external objects can hold references to.

```python
from core.aggregates import AggregateRoot, Entity, DomainEvent

class Order(AggregateRoot):
    '''Order aggregate root.'''

    def __init__(self, customer_id):
        super().__init__()
        self.id = uuid4()
        self.customer_id = customer_id
        self.items = []  # Internal entities
        self.status = 'draft'

    def add_item(self, product_id, quantity, price):
        '''Add item - enforces business rules.'''
        if self.status != 'draft':
            raise DomainError("Cannot modify finalized order")

        item = OrderItem(product_id, quantity, price)
        self.items.append(item)

        self.add_domain_event(OrderItemAdded(self.id, item.id))
```

**Responsibilities:**
- Enforce business rules
- Control access to internal entities
- Emit domain events
- Maintain consistency

### 2. Entities Within Aggregates

**Entities** within aggregates have identity but are accessed through the root.

```python
class OrderItem(Entity):
    '''Entity within Order aggregate.'''

    def __init__(self, product_id, quantity, unit_price):
        self.id = uuid4()
        self.product_id = product_id
        self.quantity = quantity
        self.unit_price = unit_price

    @property
    def subtotal(self):
        return self.unit_price.multiply(self.quantity)
```

**Key Points:**
- Have identity (ID)
- Only accessed through aggregate root
- Cannot be retrieved independently from repository
- Part of aggregate's consistency boundary

### 3. Consistency Boundary

The **consistency boundary** defines what must be consistent at any point in time.

```python
class Order(AggregateRoot):
    def _check_invariants(self):
        '''Enforce invariants.'''
        # All items must have same currency
        currencies = {item.unit_price.currency for item in self.items}
        if len(currencies) > 1:
            raise DomainError("All items must have same currency")

        # Submitted orders must have items
        if self.status == 'submitted' and not self.items:
            raise DomainError("Submitted order must have items")
```

**Rules:**
- Invariants enforced within boundary
- Changes are atomic
- External consistency is eventual

### 4. Domain Events

Aggregates raise **domain events** for significant changes.

```python
class OrderSubmitted(DomainEvent):
    '''Event raised when order submitted.'''

    def __init__(self, order_id, total):
        super().__init__(order_id)
        self.total = total

class Order(AggregateRoot):
    def submit(self):
        # Validate
        if not self.items:
            raise DomainError("Cannot submit empty order")

        # Change state
        self.status = 'submitted'

        # Raise event
        self.add_domain_event(OrderSubmitted(self.id, self.total))
```

**Purpose:**
- Notify other parts of system
- Enable eventual consistency
- Decouple aggregates
- Audit trail

## Design Guidelines

### Rule 1: Keep Aggregates Small

✅ **Good: Small aggregate**
```python
class Order(AggregateRoot):
    def __init__(self, customer_id):
        self.customer_id = customer_id  # Reference by ID!
        self.items = []  # Just the items
```

❌ **Bad: Large aggregate**
```python
class Order(AggregateRoot):
    def __init__(self):
        self.customer = Customer(...)  # Don't embed!
        self.products = [Product(...)]  # Don't load all products!
        self.inventory = Inventory(...)  # Wrong boundary!
```

**Guideline**: Include only what must be consistent.

### Rule 2: Reference Other Aggregates by ID

✅ **Good: Reference by ID**
```python
class Order(AggregateRoot):
    def __init__(self, customer_id: UUID):
        self.customer_id = customer_id  # Just the ID
```

❌ **Bad: Embed aggregate**
```python
class Order(AggregateRoot):
    def __init__(self, customer: Customer):
        self.customer = customer  # Don't embed other aggregates!
```

**Guideline**: Hold references to other aggregate roots by ID only.

### Rule 3: Update One Aggregate Per Transaction

✅ **Good: Single aggregate**
```python
# Transaction 1
order = order_repo.get(order_id)
order.submit()
order_repo.save(order)
# Emits OrderSubmitted event

# Transaction 2 (triggered by event)
inventory = inventory_repo.get(product_id)
inventory.reserve(quantity)
inventory_repo.save(inventory)
```

❌ **Bad: Multiple aggregates**
```python
# Don't do this!
order = order_repo.get(order_id)
inventory = inventory_repo.get(product_id)

order.submit()
inventory.reserve(quantity)

order_repo.save(order)
inventory_repo.save(inventory)  # Two aggregates in one transaction!
```

**Guideline**: One aggregate per transaction. Use events for coordination.

### Rule 4: Enforce Invariants at Aggregate Boundary

✅ **Good: Root enforces rules**
```python
class Order(AggregateRoot):
    MINIMUM_TOTAL = Money(Decimal('10'), 'USD')

    def submit(self):
        # Enforce business rule
        if self.total < self.MINIMUM_TOTAL:
            raise DomainError(f"Order total must be at least {self.MINIMUM_TOTAL}")

        self.status = 'submitted'
```

❌ **Bad: External validation**
```python
# Don't do this!
order = order_repo.get(order_id)

# Validation outside aggregate
if order.total < MINIMUM_TOTAL:
    raise Error("Total too low")

order.status = 'submitted'  # Direct state change!
```

**Guideline**: Business rules enforced by aggregate methods.

### Rule 5: Protect Internal Structure

✅ **Good: Encapsulated**
```python
class Order(AggregateRoot):
    def __init__(self):
        self._items = []  # Private!

    def add_item(self, product_id, quantity, price):
        # Controlled access with validation
        item = OrderItem(product_id, quantity, price)
        self._items.append(item)

    @property
    def items(self):
        # Return copy to prevent modification
        return self._items.copy()
```

❌ **Bad: Exposed internals**
```python
class Order(AggregateRoot):
    def __init__(self):
        self.items = []  # Public list!

# External code can bypass validation
order.items.append(invalid_item)  # No validation!
```

**Guideline**: Expose behavior, not data.

## Creating Aggregates

### Step 1: Identify Consistency Boundary

Ask: **"What must be consistent at any point in time?"**

Example: Order
- Order + OrderItems must be consistent
- Order total must match sum of items
- Cannot submit empty order

### Step 2: Choose Aggregate Root

The root is the entity that:
- Makes most sense as entry point
- Controls the lifecycle
- Others naturally belong to

Example: `Order` is root, `OrderItems` belong to it.

### Step 3: Define Business Rules

List the invariants:
```python
class Order(AggregateRoot):
    # Business rules:
    # 1. Items must have same currency
    # 2. Total >= minimum amount to submit
    # 3. Cannot modify submitted orders
    # 4. Must have >= 1 item to submit
```

### Step 4: Implement Aggregate

```python
from core.aggregates import AggregateRoot, Entity
from core.value_objects import Money

class OrderItem(Entity):
    def __init__(self, product_id, quantity, unit_price: Money):
        self.id = uuid4()
        self.product_id = product_id
        self.quantity = quantity
        self.unit_price = unit_price

    @property
    def subtotal(self) -> Money:
        return self.unit_price.multiply(self.quantity)

class Order(AggregateRoot):
    MINIMUM_TOTAL = Money(Decimal('10'), 'USD')

    def __init__(self, customer_id):
        super().__init__()
        self.id = uuid4()
        self.customer_id = customer_id
        self.items = []
        self.status = 'draft'

    @property
    def total(self) -> Money:
        if not self.items:
            return Money.zero('USD')
        return sum((item.subtotal for item in self.items),
                   start=Money.zero('USD'))

    def add_item(self, product_id, quantity, unit_price: Money):
        # Enforce: can only add to draft
        if self.status != 'draft':
            raise DomainError("Cannot modify submitted order")

        # Enforce: currency consistency
        if self.items and unit_price.currency != self.items[0].unit_price.currency:
            raise DomainError("All items must have same currency")

        item = OrderItem(product_id, quantity, unit_price)
        self.items.append(item)

        self.add_domain_event(OrderItemAdded(self.id, product_id))

    def submit(self):
        # Enforce: must be draft
        if self.status != 'draft':
            raise DomainError("Order already submitted")

        # Enforce: must have items
        if not self.items:
            raise DomainError("Cannot submit empty order")

        # Enforce: minimum total
        if self.total < self.MINIMUM_TOTAL:
            raise DomainError(f"Total must be at least {self.MINIMUM_TOTAL}")

        self.status = 'submitted'
        self.add_domain_event(OrderSubmitted(self.id, self.total))
```

## Examples

### Example 1: Order Aggregate (Complete)

See `core/aggregates/examples.py` for full implementation.

Key features:
- Enforces business rules
- Manages internal entities
- Raises domain events
- Maintains consistency

Usage:
```python
# Create order
order = Order(customer_id)

# Add items
order.add_item(
    product_id=product_id,
    product_name="Widget",
    quantity=2,
    unit_price=Money(Decimal('19.99'), 'USD')
)

# Submit (validates rules)
order.submit()

# Save aggregate
order_repository.save(order)  # Atomic + publishes events
```

### Example 2: Shopping Cart Aggregate

Simpler aggregate demonstrating the pattern:

```python
class ShoppingCart(AggregateRoot):
    def __init__(self, customer_id):
        super().__init__()
        self.id = uuid4()
        self.customer_id = customer_id
        self.items = []

    def add_item(self, product_id, quantity=1):
        # Find existing
        for item in self.items:
            if item.product_id == product_id:
                item.quantity += quantity
                return

        # Add new
        self.items.append(CartItem(product_id, quantity))
        self.add_domain_event(CartItemAdded(self.id, product_id))

    def clear(self):
        self.items.clear()
        self.add_domain_event(CartCleared(self.id))
```

Usage:
```python
cart = ShoppingCart(customer_id)
cart.add_item(product_id, quantity=2)
cart.add_item(other_product_id)

# Convert to order
order = Order(customer_id)
for cart_item in cart.items:
    product = product_repo.get(cart_item.product_id)
    order.add_item(product.id, product.name, cart_item.quantity, product.price)

cart.clear()

cart_repo.save(cart)
order_repo.save(order)
```

### Example 3: Customer Aggregate (with Value Objects)

Demonstrates integration with value objects:

```python
from core.value_objects import Email, Address

class Customer(AggregateRoot):
    def __init__(self, email: Email, name: str):
        super().__init__()
        self.id = uuid4()
        self.email = email  # Value Object!
        self.name = name
        self.addresses = []

    def add_address(self, address: Address, make_default=False):
        customer_address = CustomerAddress(address, make_default)
        self.addresses.append(customer_address)

        self.add_domain_event(CustomerAddressAdded(self.id, customer_address.id))

        return customer_address

    def get_default_address(self) -> Optional[Address]:
        for addr in self.addresses:
            if addr.is_default:
                return addr.address
        return None
```

Usage:
```python
# Create customer with value objects
customer = Customer(
    email=Email('john@example.com'),
    name='John Doe'
)

# Add address (value object)
address = Address(
    street='123 Main St',
    city='Springfield',
    postal_code='62701',
    country='USA'
)
customer.add_address(address, make_default=True)

customer_repo.save(customer)
```

## Repository Integration

### Repository Contract

Repositories for aggregates:
```python
class IOrderRepository(IAggregateRepository[Order]):
    '''Repository for Order aggregate.'''

    def get_by_id(self, order_id: UUID) -> Optional[Order]:
        '''Load entire aggregate.'''
        pass

    def save(self, order: Order) -> None:
        '''Save aggregate + publish events.'''
        pass

    def delete(self, order: Order) -> None:
        '''Delete entire aggregate.'''
        pass
```

### Repository Implementation Pattern

```python
from core.aggregates.repository import AggregateRepositoryBase

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

        # Reconstruct aggregate
        order = Order(order_orm.customer_id)
        order.id = order_orm.id
        order.status = order_orm.status

        # Load items (entities within aggregate)
        for item_orm in order_orm.items:
            order._items.append(self._orm_to_order_item(item_orm))

        return order

    def _save_aggregate(self, order: Order) -> None:
        # Convert to ORM
        order_orm = self._aggregate_to_orm(order)

        # Save
        self.session.merge(order_orm)
        self.session.flush()

    def _delete_aggregate(self, order: Order) -> None:
        self.session.query(OrderOrm).filter(
            OrderOrm.id == order.id
        ).delete()
```

**Key Points:**
- Load entire aggregate (root + entities)
- Save atomically
- Publish events after save
- Handle optimistic locking

## Best Practices

### 1. Design Small Aggregates

✅ **Good:**
```python
class Order(AggregateRoot):
    # Just what needs consistency
    - order data
    - order items
    - order total
```

❌ **Bad:**
```python
class Order(AggregateRoot):
    # Too much!
    - order data
    - customer details
    - product catalog
    - inventory levels
    - shipping calculations
```

**Rule**: If it doesn't need immediate consistency, it doesn't belong.

### 2. Use Domain Events for Coordination

✅ **Good:**
```python
# Order aggregate
order.submit()  # Raises OrderSubmitted event
order_repo.save(order)

# Inventory aggregate (reacts to event)
@event_handler(OrderSubmitted)
def reserve_inventory(event):
    inventory = inventory_repo.get(event.product_id)
    inventory.reserve(event.quantity)
    inventory_repo.save(inventory)
```

❌ **Bad:**
```python
# Don't update multiple aggregates in one transaction
order.submit()
inventory.reserve(quantity)  # Wrong!

order_repo.save(order)
inventory_repo.save(inventory)  # Two aggregates!
```

### 3. Make Implicit Concepts Explicit

✅ **Good:**
```python
class Order(AggregateRoot):
    def submit(self):
        # Named method makes concept explicit
        self._validate_can_submit()
        self._change_to_submitted_status()
        self._raise_submitted_event()
```

❌ **Bad:**
```python
class Order(AggregateRoot):
    def process(self):  # Vague name
        # What does this do?
        pass
```

### 4. Validate in Methods, Not Constructors

✅ **Good:**
```python
class Order(AggregateRoot):
    def __init__(self, customer_id):
        # Minimal validation
        self.customer_id = customer_id
        self.items = []
        self.status = 'draft'

    def submit(self):
        # Validate here
        if not self.items:
            raise DomainError("Cannot submit empty order")
```

❌ **Bad:**
```python
class Order(AggregateRoot):
    def __init__(self, customer_id, items):
        if not items:
            raise DomainError("Order must have items")
        # Hard to create empty order for building up!
```

### 5. Use Value Objects Within Aggregates

✅ **Good:**
```python
from core.value_objects import Money, Address

class Order(AggregateRoot):
    def __init__(self):
        self.shipping_address = Address(...)  # Value Object
        self.total = Money(Decimal('0'), 'USD')  # Value Object
```

**Benefits**: Type safety, validation, immutability

## Common Pitfalls

### Pitfall 1: Aggregates Too Large

**Problem:**
```python
class Order(AggregateRoot):
    def __init__(self):
        self.customer = Customer(...)  # Entire customer!
        self.products = [...]  # All products!
        self.inventory = Inventory(...)  # Inventory system!
        # This is huge!
```

**Solution**: Reference by ID
```python
class Order(AggregateRoot):
    def __init__(self, customer_id):
        self.customer_id = customer_id  # Just ID
```

### Pitfall 2: Anemic Aggregates

**Problem:**
```python
class Order(AggregateRoot):
    # Just getters/setters, no behavior
    def get_status(self):
        return self.status

    def set_status(self, status):
        self.status = status  # No validation!
```

**Solution**: Rich behavior
```python
class Order(AggregateRoot):
    def submit(self):
        # Business logic here
        self._validate()
        self.status = 'submitted'
        self.add_domain_event(OrderSubmitted(self.id))
```

### Pitfall 3: Breaking Encapsulation

**Problem:**
```python
# External code modifies internal state
order.items.append(invalid_item)  # Bypasses validation!
```

**Solution**: Controlled access
```python
class Order(AggregateRoot):
    @property
    def items(self):
        return self._items.copy()  # Return copy

    def add_item(self, ...):
        # Only way to add items
```

### Pitfall 4: Not Using Domain Events

**Problem:**
```python
order.submit()
order_repo.save(order)

# How do other parts of system know?
# Manual coordination required!
inventory.reserve(...)
notification.send(...)
```

**Solution**: Domain events
```python
order.submit()  # Raises OrderSubmitted event
order_repo.save(order)

# Event handlers react automatically
@event_handler(OrderSubmitted)
def reserve_inventory(event): ...

@event_handler(OrderSubmitted)
def send_notification(event): ...
```

## Testing

### Testing Aggregates

```python
import pytest
from core.aggregates.examples import Order, OrderItem
from core.aggregates.base import DomainError
from core.value_objects import Money
from decimal import Decimal

class TestOrder:
    def test_create_order(self):
        order = Order(customer_id=uuid4())

        assert order.id is not None
        assert order.status == 'draft'
        assert len(order.items) == 0

    def test_add_item_to_order(self):
        order = Order(customer_id=uuid4())

        order.add_item(
            product_id=uuid4(),
            product_name="Widget",
            quantity=2,
            unit_price=Money(Decimal('10'), 'USD')
        )

        assert len(order.items) == 1
        assert order.total == Money(Decimal('20'), 'USD')

    def test_cannot_add_item_to_submitted_order(self):
        order = Order(customer_id=uuid4())
        order.add_item(uuid4(), "Widget", 1, Money(Decimal('10'), 'USD'))
        order.submit()

        with pytest.raises(DomainError):
            order.add_item(uuid4(), "Gadget", 1, Money(Decimal('5'), 'USD'))

    def test_submit_requires_minimum_total(self):
        order = Order(customer_id=uuid4())
        order.add_item(uuid4(), "Cheap", 1, Money(Decimal('1'), 'USD'))

        with pytest.raises(DomainError):
            order.submit()  # Below minimum

    def test_submit_raises_domain_event(self):
        order = Order(customer_id=uuid4())
        order.add_item(uuid4(), "Widget", 1, Money(Decimal('20'), 'USD'))

        order.submit()

        events = order.get_domain_events()
        assert len(events) > 0
        assert any(isinstance(e, OrderSubmitted) for e in events)
```

### Testing with Repository

```python
def test_order_with_repository():
    # Arrange
    publisher = InMemoryEventPublisher()
    repository = InMemoryAggregateRepository[Order](publisher)

    order = Order(customer_id=uuid4())
    order.add_item(uuid4(), "Widget", 1, Money(Decimal('20'), 'USD'))

    # Act
    order.submit()
    repository.save(order)

    # Assert
    loaded = repository.get_by_id(order.id)
    assert loaded.status == 'submitted'
    assert len(publisher.published_events) > 0
```

## Summary

Aggregates are powerful for:
- **Enforcing business rules** within consistency boundaries
- **Maintaining transactional integrity**
- **Encapsulating domain logic**
- **Coordinating with domain events**

### Key Takeaways

1. **Aggregate Root** is the only entry point
2. **Keep aggregates small** - only what needs consistency
3. **Reference by ID** - don't embed other aggregates
4. **One aggregate per transaction** - use events for coordination
5. **Enforce invariants** - business rules in aggregate methods
6. **Raise domain events** - for cross-aggregate coordination

### Next Steps

1. Review existing code for aggregate boundaries
2. Identify consistency requirements
3. Extract aggregates from existing entities
4. Implement domain events
5. Test business rules

### Related Patterns

- **Entity Pattern**: Objects with identity
- **Value Object Pattern**: Objects identified by values
- **Repository Pattern**: Persistence for aggregates
- **Domain Events**: Cross-aggregate coordination
- **Specification Pattern**: Complex business rules

### Resources

- [Domain-Driven Design](https://www.domainlanguage.com/ddd/) by Eric Evans
- [Implementing Domain-Driven Design](https://vaughnvernon.com/?page_id=168) by Vaughn Vernon
- [Effective Aggregate Design](https://vaughnvernon.com/?p=838) by Vaughn Vernon
- [Aggregates](https://martinfowler.com/bliki/DDD_Aggregate.html) by Martin Fowler
