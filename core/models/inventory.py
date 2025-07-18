from datetime import datetime
from decimal import Decimal # For precise quantity representation
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from core.models.enums import InventoryMovementType

class InventoryMovement(BaseModel):
    id: Optional[int] = None
    product_id: int
    quantity: Decimal = Field(..., max_digits=10, decimal_places=2) # Positive for in, negative for out
    movement_type: InventoryMovementType = Field(...) # Type of inventory movement
    timestamp: datetime = Field(default_factory=datetime.utcnow) # Renamed from 'date' for clarity and consistency
    description: Optional[str] = Field(default=None, max_length=255)
    user_id: Optional[int] = None # User performing the movement
    related_id: Optional[int] = None # e.g., Sale ID, Purchase ID

    model_config = ConfigDict(from_attributes=True)
