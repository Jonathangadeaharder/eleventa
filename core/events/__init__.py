"""
Domain Events for Eleventa POS

This package contains all domain events that can occur in the system.
Events are organized by aggregate root.
"""

from core.events.product_events import (
    ProductCreated,
    ProductUpdated,
    ProductPriceChanged,
    ProductStockChanged,
    ProductDeleted,
)

from core.events.sale_events import (
    SaleStarted,
    SaleItemAdded,
    SaleItemRemoved,
    SaleCompleted,
    SaleCancelled,
    PaymentReceived,
)

from core.events.customer_events import (
    CustomerCreated,
    CustomerUpdated,
    CustomerCreditLimitChanged,
    CustomerBalanceChanged,
)

from core.events.inventory_events import (
    InventoryAdjusted,
    LowStockDetected,
    StockReplenished,
)

__all__ = [
    # Product events
    'ProductCreated',
    'ProductUpdated',
    'ProductPriceChanged',
    'ProductStockChanged',
    'ProductDeleted',
    # Sale events
    'SaleStarted',
    'SaleItemAdded',
    'SaleItemRemoved',
    'SaleCompleted',
    'SaleCancelled',
    'PaymentReceived',
    # Customer events
    'CustomerCreated',
    'CustomerUpdated',
    'CustomerCreditLimitChanged',
    'CustomerBalanceChanged',
    # Inventory events
    'InventoryAdjusted',
    'LowStockDetected',
    'StockReplenished',
]
