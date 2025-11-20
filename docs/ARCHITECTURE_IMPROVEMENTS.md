# Architecture Improvements - Learning from Best Practices

This document describes the architectural improvements applied to the Eleventa POS system based on patterns from industry-leading resources like "Architecture Patterns with Python" (Cosmic Python) and Domain-Driven Design.

## Table of Contents

1. [Overview](#overview)
2. [Domain Events Pattern](#domain-events-pattern)
3. [Unit of Work Enhancement](#unit-of-work-enhancement)
4. [Event Handlers](#event-handlers)
5. [Usage Examples](#usage-examples)
6. [Testing](#testing)
7. [Future Improvements](#future-improvements)
8. [Learning Resources](#learning-resources)

---

## Overview

The Eleventa POS system already had excellent foundations:
- ✅ Repository Pattern
- ✅ Unit of Work Pattern
- ✅ Service Layer Pattern
- ✅ Clean separation of Domain and Infrastructure

We've enhanced it with:
- ✨ **Domain Events** - Decoupled, event-driven architecture
- ✨ **Message Bus** - Coordinated event publishing after transactions
- ✨ **Event Handlers** - Reactive side-effect processing
- ✨ **Aggregate Base Classes** - Support for domain event collection

### Key Benefits

1. **Decoupling**: Services no longer need to know about side effects
2. **Extensibility**: Add new features by subscribing to events
3. **Testability**: Mock event publishing to test in isolation
4. **Audit Trail**: All business operations generate events
5. **Scalability**: Events can be queued for async processing

---

## Domain Events Pattern

### What Are Domain Events?

Domain events represent something that happened in the domain that domain experts care about. They are **immutable facts about the past**.

```python
@dataclass(frozen=True)
class ProductPriceChanged(DomainEvent):
    """Event raised when a product's price changes."""
    product_id: UUID
    code: str
    old_price: Decimal
    new_price: Decimal
    price_change_percent: Decimal
    user_id: UUID
```

### Event Types

We've defined events for all key aggregates:

#### Product Events (`core/events/product_events.py`)
- `ProductCreated` - New product added
- `ProductUpdated` - Product details changed
- `ProductPriceChanged` - Price modified
- `ProductStockChanged` - Inventory quantity changed
- `ProductDeleted` - Product removed

#### Sale Events (`core/events/sale_events.py`)
- `SaleStarted` - Transaction initiated
- `SaleItemAdded` - Item added to sale
- `SaleItemRemoved` - Item removed from sale
- `SaleCompleted` - Sale finalized
- `SaleCancelled` - Sale cancelled
- `PaymentReceived` - Payment processed

#### Customer Events (`core/events/customer_events.py`)
- `CustomerCreated` - New customer registered
- `CustomerUpdated` - Customer details changed
- `CustomerCreditLimitChanged` - Credit limit modified
- `CustomerBalanceChanged` - Balance updated

#### Inventory Events (`core/events/inventory_events.py`)
- `InventoryAdjusted` - Manual stock adjustment
- `LowStockDetected` - Stock below minimum
- `StockReplenished` - Stock increased

### Creating Custom Events

```python
from dataclasses import dataclass
from core.domain_events import DomainEvent
from uuid import UUID
from decimal import Decimal

@dataclass(frozen=True)
class DiscountApplied(DomainEvent):
    """Event raised when a discount is applied to a sale."""
    sale_id: UUID
    discount_percent: Decimal
    discount_amount: Decimal
    reason: str
```

---

## Unit of Work Enhancement

The Unit of Work has been enhanced to automatically collect and publish domain events after successful commits.

### How It Works

```python
from infrastructure.persistence.unit_of_work import unit_of_work

with unit_of_work() as uow:
    # 1. Perform business operations
    product = uow.products.get_by_id(product_id)
    product.sell_price = new_price
    uow.products.update(product)

    # 2. Register events (services do this automatically)
    event = ProductPriceChanged(
        product_id=product.id,
        code=product.code,
        old_price=old_price,
        new_price=new_price,
        price_change_percent=Decimal('10'),
        user_id=current_user_id
    )
    uow.add_event(event)

    # 3. On successful exit, events are published automatically
```

### Event Flow

```
1. Service creates UnitOfWork
2. Service performs operations
3. Service registers events via uow.add_event()
4. UnitOfWork.__exit__() is called
5. If no exception:
   a. Commit database transaction
   b. Publish all collected events
   c. Event handlers execute
6. If exception:
   a. Rollback database
   b. Clear events (don't publish failed operations)
```

### Key Methods

```python
class UnitOfWork:
    def add_event(self, event: DomainEvent) -> None:
        """Manually add a domain event to be published after commit."""

    def collect_events(self, aggregate) -> None:
        """Collect domain events from an aggregate."""

    def _publish_events(self) -> None:
        """Publish all collected events (called automatically)."""
```

---

## Event Handlers

Event handlers are functions that react to specific domain events. They implement **side effects** without coupling services together.

### Subscribing to Events

```python
from core.domain_events import EventPublisher
from core.events.product_events import ProductPriceChanged

@EventPublisher.subscribe(ProductPriceChanged)
def notify_manager_of_price_change(event: ProductPriceChanged):
    """Send notification when price changes significantly."""
    if abs(event.price_change_percent) > Decimal('10'):
        email_service.send_alert(
            to="manager@company.com",
            subject=f"Large Price Change: {event.code}",
            message=f"Price changed by {event.price_change_percent}%"
        )
```

### Global Handlers

Subscribe to ALL events for cross-cutting concerns:

```python
@EventPublisher.subscribe_all
def audit_logger(event: DomainEvent):
    """Log all domain events to audit trail."""
    audit_log.record({
        'event_type': type(event).__name__,
        'occurred_at': event.occurred_at,
        'event_id': event.event_id,
        'data': event.__dict__
    })
```

### Existing Handlers

See `core/event_handlers.py` for example handlers:

- **Price Change Notifications** - Alert on significant price changes
- **Low Stock Alerts** - Notify purchasing when stock is low
- **Sales Analytics** - Update real-time dashboards
- **Product Lifecycle Tracking** - Log all product changes

### Activating Handlers

```python
# In your main.py or application startup:
import core.event_handlers  # Auto-registers all handlers

# Or explicitly:
from core.event_handlers import initialize_event_handlers
initialize_event_handlers()
```

---

## Usage Examples

### Example 1: Service Publishing Events

```python
from core.services.product_service import ProductService
from core.models.product import Product
from decimal import Decimal
from uuid import UUID

product_service = ProductService()

# Create a new product
new_product = Product(
    code="LAPTOP001",
    description="Dell Laptop 15\"",
    sell_price=Decimal('999.99'),
    cost_price=Decimal('750.00'),
    department_id=electronics_dept_id
)

# Service automatically publishes ProductCreated event
created_product = product_service.add_product(
    new_product,
    user_id=current_user_id
)

# Event handlers automatically execute:
# - Product catalog updated
# - Analytics tracked
# - Audit log recorded
```

### Example 2: Bulk Price Update with Events

```python
# Update all products in Electronics department by 10%
product_service.update_prices_by_percentage(
    percentage=Decimal('10'),
    department_id=electronics_dept_id,
    user_id=current_user_id
)

# Publishes ProductPriceChanged event for EACH product
# Handlers automatically:
# - Alert manager on large changes
# - Update price labels
# - Record price history
```

### Example 3: Custom Event Handler

```python
from core.domain_events import EventPublisher
from core.events.sale_events import SaleCompleted

@EventPublisher.subscribe(SaleCompleted)
def award_loyalty_points(event: SaleCompleted):
    """Award loyalty points when a customer makes a purchase."""
    if event.customer_id:
        # Calculate points (1 point per dollar)
        points = int(event.total_amount)

        # Update customer loyalty points
        loyalty_service.add_points(
            customer_id=event.customer_id,
            points=points,
            reason=f"Sale {event.sale_id}"
        )

        logger.info(f"Awarded {points} loyalty points to customer {event.customer_id}")
```

### Example 4: Testing with Events

```python
import pytest
from unittest.mock import patch
from core.domain_events import EventPublisher

@pytest.fixture(autouse=True)
def clear_event_handlers():
    """Clear handlers before/after each test."""
    EventPublisher.clear_handlers()
    yield
    EventPublisher.clear_handlers()

def test_product_creation_publishes_event():
    """Test that creating a product publishes the correct event."""
    events_received = []

    # Subscribe to events in test
    @EventPublisher.subscribe(ProductCreated)
    def capture_event(event):
        events_received.append(event)

    # Create product
    product_service.add_product(test_product, user_id=test_user_id)

    # Verify event was published
    assert len(events_received) == 1
    assert events_received[0].code == test_product.code
    assert events_received[0].user_id == test_user_id
```

---

## Testing

### Testing Event Publishing

```python
from core.domain_events import EventPublisher
from core.events.product_events import ProductCreated

def test_product_service_publishes_events():
    """Verify ProductService publishes events correctly."""
    published_events = []

    @EventPublisher.subscribe(ProductCreated)
    def capture_event(event):
        published_events.append(event)

    # Execute service operation
    product_service.add_product(test_product)

    # Verify event published
    assert len(published_events) == 1
    assert isinstance(published_events[0], ProductCreated)
```

### Testing Event Handlers

```python
def test_price_change_notification():
    """Test that large price changes trigger notifications."""
    with patch('email_service.send_alert') as mock_email:
        # Trigger event
        event = ProductPriceChanged(
            product_id=UUID('12345678-1234-5678-1234-567812345678'),
            code='TEST001',
            old_price=Decimal('100'),
            new_price=Decimal('150'),  # 50% increase
            price_change_percent=Decimal('50'),
            user_id=test_user_id
        )

        # Publish event
        EventPublisher.publish(event)

        # Verify notification sent
        mock_email.assert_called_once()
```

### Isolating Tests

```python
@pytest.fixture
def isolated_events():
    """Isolate event handlers between tests."""
    # Store original handlers
    original_handlers = EventPublisher._handlers.copy()
    original_global = EventPublisher._global_handlers.copy()

    yield

    # Restore
    EventPublisher._handlers = original_handlers
    EventPublisher._global_handlers = original_global
```

---

## Future Improvements

### Phase 2: Application Layer / Use Cases

Create explicit use case classes for complex workflows:

```python
class ProcessSaleUseCase:
    """
    Use case for processing a complete sale transaction.

    Orchestrates multiple services and publishes events.
    """
    def execute(self, request: ProcessSaleRequest) -> ProcessSaleResponse:
        # 1. Validate customer (if credit sale)
        # 2. Check inventory availability
        # 3. Create sale
        # 4. Update inventory
        # 5. Process payment
        # 6. Generate receipt
        # 7. Events published automatically
        pass
```

### Phase 3: CQRS (Command Query Responsibility Segregation)

Separate read and write models:

```python
# Commands (writes)
class CreateProductCommand:
    code: str
    description: str
    price: Decimal

class CreateProductCommandHandler:
    def handle(self, command: CreateProductCommand) -> Product:
        # Business logic, validation, event publishing
        pass

# Queries (reads)
class ProductQueries:
    def get_products_with_low_stock(self) -> List[ProductStockDTO]:
        # Optimized read query, no events
        pass
```

### Phase 4: Specification Pattern

Composable query specifications:

```python
# Define reusable specifications
low_stock = LowStockSpec()
electronics = InDepartmentSpec(dept_id=1)
active = ActiveProductSpec()

# Compose them
spec = low_stock.and_(electronics).and_(active)

# Use in repository
products = repository.find_by_spec(spec)
```

### Phase 5: Async Event Processing

For high-volume events, use async message queue:

```python
# Current: Synchronous
EventPublisher.publish(event)  # Handlers run immediately

# Future: Asynchronous
event_queue.enqueue(event)  # Process in background
```

---

## Learning Resources

### Books & Articles

1. **"Architecture Patterns with Python" (Cosmic Python)**
   - Repository: https://github.com/cosmicpython/code
   - Book: https://www.cosmicpython.com/book/
   - Chapters 6-8 cover Unit of Work and Events

2. **Domain-Driven Design Resources**
   - https://github.com/qu3vipon/python-ddd
   - https://github.com/runemalm/ddd-for-python

3. **POS System Examples**
   - https://github.com/Nadeera3784/POS_System
   - https://github.com/frappe/erpnext

### Key Patterns Used

| Pattern | Purpose | Implementation |
|---------|---------|----------------|
| **Domain Events** | Decouple services | `core/domain_events.py` |
| **Event Publisher** | Observer pattern | `EventPublisher` class |
| **Message Bus** | Coordinate events | `MessageBus` class |
| **Unit of Work** | Transaction + Events | `infrastructure/persistence/unit_of_work.py` |
| **Event Handlers** | Side effects | `core/event_handlers.py` |
| **Aggregate Root** | Event collection | `core/models/base.py` |

### Related Concepts

- **CQRS** - Command Query Responsibility Segregation
- **Event Sourcing** - Store events as source of truth
- **Saga Pattern** - Distributed transactions via events
- **Outbox Pattern** - Reliable event publishing

---

## Summary

The Eleventa POS system now features:

✅ **Domain Events Infrastructure** - Fully functional event system
✅ **Enhanced Unit of Work** - Automatic event publishing
✅ **Event Handlers** - Decoupled side-effect processing
✅ **Example Implementations** - ProductService with events
✅ **Comprehensive Documentation** - This guide
✅ **Testing Patterns** - Event testing examples

### Quick Start

1. **Import handlers** at startup:
   ```python
   import core.event_handlers
   ```

2. **Services automatically publish events**:
   ```python
   product_service.add_product(product, user_id=user_id)
   # ProductCreated event published automatically
   ```

3. **Subscribe to events**:
   ```python
   @EventPublisher.subscribe(ProductPriceChanged)
   def my_handler(event):
       # React to price changes
       pass
   ```

4. **Events published after successful commit**:
   ```python
   with unit_of_work() as uow:
       # Operations...
       uow.add_event(my_event)
       # On exit: commit → publish events
   ```

---

**For questions or improvements, see the source code comments and examples in:**
- `core/domain_events.py`
- `core/events/`
- `core/event_handlers.py`
- `infrastructure/persistence/unit_of_work.py`
