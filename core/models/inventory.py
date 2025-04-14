from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class InventoryMovement:
    """Represents a change in the stock level of a product."""

    product_id: int
    quantity: float # Positive for addition, negative for removal
    movement_type: str # e.g., 'SALE', 'PURCHASE', 'ADJUSTMENT', 'INITIAL'
    timestamp: datetime = field(default_factory=datetime.now)
    description: Optional[str] = None # Optional description or notes
    user_id: Optional[int] = None # User performing the action, if applicable
    related_id: Optional[int] = None # ID of related entity (e.g., Sale ID, Purchase ID), if applicable
    id: Optional[int] = None # Database ID, assigned after saving 