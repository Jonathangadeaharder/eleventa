"""
Event Handlers for Domain Events

This module demonstrates the power of domain events by providing
decoupled handlers that react to business events without tight
coupling between services.

Based on the Message Bus pattern from "Architecture Patterns with Python"
(Cosmic Python), these handlers subscribe to domain events and perform
side effects like notifications, logging, analytics, etc.

To activate these handlers, simply import this module during app startup:
    import core.event_handlers  # Registers all handlers
"""

import logging
from decimal import Decimal

from core.domain_events import EventPublisher
from core.events.product_events import (
    ProductCreated,
    ProductPriceChanged,
    ProductDeleted,
)
from core.events.inventory_events import (
    LowStockDetected,
    StockReplenished,
)
from core.events.sale_events import (
    SaleCompleted,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Product Event Handlers
# =============================================================================

@EventPublisher.subscribe(ProductCreated)
def on_product_created(event: ProductCreated) -> None:
    """
    Handle ProductCreated events.

    Example actions:
    - Send notification to inventory manager
    - Update product catalog displays
    - Log to analytics system
    """
    logger.info(
        f"📦 New product created: {event.code} - {event.description} "
        f"at ${event.sell_price}"
    )

    # Example: Could send email notification
    # email_service.send_notification(
    #     to="inventory@company.com",
    #     subject=f"New Product: {event.code}",
    #     body=f"Product {event.description} has been added to the system."
    # )

    # Example: Could update external systems
    # analytics_service.track_product_created(event)


@EventPublisher.subscribe(ProductPriceChanged)
def on_product_price_changed(event: ProductPriceChanged) -> None:
    """
    Handle ProductPriceChanged events.

    Example actions:
    - Notify managers of significant price changes
    - Update price tags/labels
    - Record in price history
    - Trigger repricing of pending orders
    """
    change_percent = abs(event.price_change_percent)
    direction = "increased" if event.new_price > event.old_price else "decreased"

    logger.info(
        f"💰 Price changed for {event.code}: "
        f"${event.old_price} → ${event.new_price} ({direction} by {change_percent}%)"
    )

    # Alert on significant price changes (>10%)
    if change_percent > Decimal('10'):
        logger.warning(
            f"⚠️  SIGNIFICANT PRICE CHANGE: {event.code} price {direction} by {change_percent}%"
        )
        # Example: Send alert to managers
        # notification_service.send_alert(
        #     level="warning",
        #     title=f"Large Price Change: {event.code}",
        #     message=f"Price {direction} by {change_percent}%"
        # )

    # Example: Update external price label system
    # label_printer_service.queue_price_label_update(event.product_id)


@EventPublisher.subscribe(ProductDeleted)
def on_product_deleted(event: ProductDeleted) -> None:
    """
    Handle ProductDeleted events.

    Example actions:
    - Archive product data
    - Remove from displays
    - Update reports
    """
    logger.info(f"🗑️  Product deleted: {event.code} - {event.description}")

    # Example: Archive to long-term storage
    # archive_service.archive_product(event.product_id, event)


# =============================================================================
# Inventory Event Handlers
# =============================================================================

@EventPublisher.subscribe(LowStockDetected)
def on_low_stock_detected(event: LowStockDetected) -> None:
    """
    Handle LowStockDetected events.

    Example actions:
    - Send reorder notifications
    - Create purchase orders automatically
    - Alert warehouse manager
    """
    logger.warning(
        f"⚠️  LOW STOCK: {event.product_code} - {event.product_description} "
        f"(Current: {event.current_quantity}, Min: {event.minimum_stock})"
    )

    # Example: Send notification to purchasing
    # notification_service.send_alert(
    #     to="purchasing@company.com",
    #     level="warning",
    #     title=f"Low Stock: {event.product_code}",
    #     message=f"Product {event.product_description} is below minimum stock level. "
    #             f"Current: {event.current_quantity}, Minimum: {event.minimum_stock}"
    # )

    # Example: Auto-create purchase order if enabled
    # if auto_reorder_enabled(event.product_id):
    #     purchase_order_service.create_reorder(
    #         product_id=event.product_id,
    #         quantity=event.reorder_point
    #     )


@EventPublisher.subscribe(StockReplenished)
def on_stock_replenished(event: StockReplenished) -> None:
    """
    Handle StockReplenished events.

    Example actions:
    - Update availability displays
    - Notify sales team
    - Resume out-of-stock notifications
    """
    logger.info(
        f"📈 Stock replenished: {event.product_code} "
        f"(+{event.quantity_added} units, total: {event.new_quantity})"
    )

    # Example: Notify sales team
    # if event.new_quantity >= product.reorder_point:
    #     notification_service.notify_sales_team(
    #         f"Product {event.product_code} is back in stock!"
    #     )


# =============================================================================
# Sales Event Handlers
# =============================================================================

@EventPublisher.subscribe(SaleCompleted)
def on_sale_completed(event: SaleCompleted) -> None:
    """
    Handle SaleCompleted events.

    Example actions:
    - Update sales analytics
    - Process loyalty points
    - Send receipt via email
    - Update customer purchase history
    """
    logger.info(
        f"💵 Sale completed: ${event.total_amount} "
        f"(Payment: {event.payment_type}, Customer: {event.customer_id or 'None'})"
    )

    # Example: Update real-time dashboard
    # dashboard_service.update_sales_metrics(event.total_amount)

    # Example: Process loyalty points for customer sales
    # if event.customer_id:
    #     loyalty_service.award_points(
    #         customer_id=event.customer_id,
    #         amount=event.total_amount
    #     )

    # Example: Send digital receipt if email available
    # if event.customer_id:
    #     customer = customer_service.get_by_id(event.customer_id)
    #     if customer.email:
    #         email_service.send_receipt(customer.email, event.sale_id)


# =============================================================================
# Analytics and Reporting Handler (subscribes to all events)
# =============================================================================

@EventPublisher.subscribe_all
def analytics_handler(event) -> None:
    """
    Global analytics handler that tracks all domain events.

    This demonstrates how you can have cross-cutting concerns
    that react to all events without coupling to specific types.
    """
    event_type = type(event).__name__

    # Example: Send to analytics system
    # analytics_service.track_event(
    #     event_type=event_type,
    #     timestamp=event.occurred_at,
    #     data=event.__dict__
    # )

    # For now, just log a summary
    logger.debug(f"[ANALYTICS] {event_type} occurred at {event.occurred_at}")


# =============================================================================
# Usage Example
# =============================================================================

def initialize_event_handlers():
    """
    Initialize all event handlers.

    Call this function during application startup to ensure
    all handlers are registered.

    Example:
        # In your main.py or app initialization:
        from core.event_handlers import initialize_event_handlers
        initialize_event_handlers()
    """
    # All handlers are registered via decorators when this module is imported
    # This function serves as an explicit initialization point
    logger.info("✅ Event handlers initialized successfully")

    # Log registered handlers
    from core.domain_events import EventPublisher
    for event_type, handlers in EventPublisher._handlers.items():
        handler_names = [h.__name__ for h in handlers]
        logger.debug(f"  {event_type.__name__}: {', '.join(handler_names)}")


# Auto-register handlers when module is imported
# Comment this out if you want explicit control over when handlers are registered
logger.info("Event handlers module loaded - handlers registered")
