from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from core.models.product import Product # Assuming Product model exists
from core.models.supplier import Supplier # Assuming Supplier model exists

@dataclass
class PurchaseOrderItem:
    """Represents an item within a purchase order."""
    id: Optional[int] = None
    purchase_order_id: Optional[int] = None
    product_id: int = 0
    product_code: str = "" # Denormalized for easier display
    product_description: str = "" # Denormalized for easier display
    quantity_ordered: float = 0.0
    cost_price: float = 0.0 # Cost price at the time of order
    quantity_received: float = 0.0 # Track received quantity separately

    @property
    def subtotal(self) -> float:
        return self.quantity_ordered * self.cost_price

@dataclass
class PurchaseOrder:
    """Represents a purchase order placed with a supplier."""
    id: Optional[int] = None
    supplier_id: int = 0
    supplier_name: str = "" # Denormalized for easier display
    order_date: datetime = field(default_factory=datetime.now)
    expected_delivery_date: Optional[datetime] = None
    status: str = "PENDING" # e.g., PENDING, PARTIALLY_RECEIVED, RECEIVED, CANCELLED
    notes: Optional[str] = None
    items: List[PurchaseOrderItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def total_amount(self) -> float:
        return sum(item.subtotal for item in self.items)
