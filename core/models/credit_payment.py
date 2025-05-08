from datetime import datetime
from decimal import Decimal
from typing import Optional
import uuid
from pydantic import BaseModel, Field

class CreditPayment(BaseModel):
    id: Optional[int] = None
    customer_id: uuid.UUID # Assuming Customer ID is UUID from Customer domain model
    user_id: Optional[int] = None # Make user_id optional
    amount: Decimal = Field(..., max_digits=10, decimal_places=2)
    payment_date: datetime = Field(default_factory=datetime.utcnow)
    description: Optional[str] = Field(default=None, max_length=255)
    
    class Config:
        from_attributes = True # Updated from orm_mode to from_attributes for Pydantic v2
