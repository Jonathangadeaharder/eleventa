from datetime import datetime
from decimal import Decimal
from typing import Optional, Union
import uuid
from pydantic import BaseModel, Field

class CreditPayment(BaseModel):
    id: Optional[int] = None
    customer_id: Union[uuid.UUID, str] # UUID or string to handle both formats
    user_id: int # Make user_id required
    amount: Decimal = Field(..., max_digits=10, decimal_places=2)
    timestamp: datetime = Field(default_factory=datetime.utcnow) # Changed from payment_date to match ORM
    notes: Optional[str] = Field(default=None, max_length=255) # Changed from description to match ORM
    
    class Config:
        from_attributes = True # Updated from orm_mode to from_attributes for Pydantic v2
