from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum, auto
from typing import Optional, List


class CashDrawerEntryType(Enum):
    """Types of cash drawer entries."""
    START = "START"  # Opening the drawer
    IN = "IN"        # Adding cash
    OUT = "OUT"      # Removing cash
    SALE = "SALE"    # Cash from a sale
    RETURN = "RETURN" # Cash from a return
    CLOSE = "CLOSE"  # Closing the drawer


@dataclass
class CashDrawerEntry:
    """Model representing a cash drawer entry."""
    timestamp: datetime
    entry_type: CashDrawerEntryType
    amount: Decimal
    description: str
    user_id: int
    drawer_id: Optional[int] = None
    id: Optional[int] = None
    
    def __post_init__(self):
        """Convert string amount to Decimal if needed."""
        if not isinstance(self.amount, Decimal):
            self.amount = Decimal(str(self.amount))
            
        # Convert string entry type to enum if needed
        if isinstance(self.entry_type, str):
            self.entry_type = CashDrawerEntryType(self.entry_type)