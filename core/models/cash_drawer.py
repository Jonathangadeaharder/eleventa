from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class CashDrawerEntryType(Enum):
    """Types of cash drawer entries."""
    START = "START"  # Opening the drawer
    IN = "IN"        # Adding cash
    OUT = "OUT"      # Removing cash
    SALE = "SALE"    # Cash from a sale
    RETURN = "RETURN" # Cash from a return
    CLOSE = "CLOSE"  # Closing the drawer


class CashDrawerEntry(BaseModel):
    """Domain model representing a cash drawer entry."""
    id: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    entry_type: CashDrawerEntryType
    amount: Decimal = Field(..., max_digits=10, decimal_places=2)
    description: str = Field(..., max_length=255)
    user_id: int # Assuming user_id is always present for a domain entry
    drawer_id: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)
