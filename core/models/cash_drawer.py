from sqlalchemy import Column, Integer, String, DateTime, Numeric, Enum as SQLEnum
from core.database import Base
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


class CashDrawerEntry(Base):
    """Model representing a cash drawer entry."""
    __tablename__ = 'cash_drawer_entries'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    entry_type = Column(SQLEnum(CashDrawerEntryType), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    description = Column(String(255), nullable=False)
    user_id = Column(Integer, nullable=False)
    drawer_id = Column(Integer, nullable=True)
    
    def __init__(self, timestamp=None, entry_type=None, amount=None, 
                 description=None, user_id=None, drawer_id=None):
        """
        Initialize a new CashDrawerEntry.
        
        Args:
            timestamp (datetime): When the entry was created
            entry_type (CashDrawerEntryType): Type of entry
            amount (Decimal): Amount of money involved
            description (str): Description of the entry
            user_id (int): ID of the user who made the entry
            drawer_id (int, optional): ID of the drawer involved
        """
        self.timestamp = timestamp or datetime.now()
        self.entry_type = entry_type
        self.amount = amount
        self.description = description
        self.user_id = user_id
        self.drawer_id = drawer_id
        
        # Convert string amount to Decimal if needed
        if not isinstance(self.amount, Decimal):
            self.amount = Decimal(str(self.amount))
            
        # Convert string entry type to enum if needed
        if isinstance(self.entry_type, str):
            self.entry_type = CashDrawerEntryType(self.entry_type)
