from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from typing import Optional, List
from pydantic import BaseModel, Field
from decimal import Decimal

class Purchase(BaseModel):
    id: Optional[int] = None
    product_id: int
    supplier_id: int
    quantity: Decimal = Field(..., max_digits=10, decimal_places=2)
    unit_price: Decimal = Field(..., max_digits=10, decimal_places=2)
    purchase_date: datetime = Field(default_factory=datetime.utcnow)
    invoice_number: Optional[str] = Field(default=None, max_length=100)

    class Config:
        from_attributes = True

class PurchaseOrderItem(BaseModel):
    """Item within a purchase order."""
    id: Optional[int] = None
    product_id: int
    product_code: Optional[str] = None
    product_description: Optional[str] = None
    quantity_ordered: Decimal = Field(..., max_digits=10, decimal_places=2)
    unit_price: Decimal = Field(..., max_digits=10, decimal_places=2)
    quantity_received: Decimal = Field(default=Decimal('0.00'), max_digits=10, decimal_places=2)
        
    @property
    def total(self) -> Decimal:
        """Calculate the total price for this item."""
        return (self.quantity_ordered * self.unit_price).quantize(Decimal("0.01"))

    class Config:
        from_attributes = True

class PurchaseOrder(BaseModel):
    """Purchase order model representing an order to a supplier."""
    id: Optional[int] = None
    supplier_id: int
    order_date: datetime = Field(default_factory=datetime.utcnow)
    expected_delivery_date: Optional[datetime] = None
    status: str = Field(default="PENDING", max_length=50)
    notes: Optional[str] = Field(default=None)
    items: List[PurchaseOrderItem] = Field(default_factory=list)

    class Config:
        from_attributes = True
