from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from core.database import Base
from datetime import datetime
import uuid

class Purchase(Base):
    __tablename__ = 'purchases'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    purchase_date = Column(DateTime, default=datetime.utcnow)
    invoice_number = Column(String(100))
    
    product = relationship("Product", back_populates="purchases")
    supplier = relationship("Supplier", back_populates="purchases")

class PurchaseOrder:
    """Purchase order model representing an order to a supplier."""
    
    def __init__(self, 
                 id=None, 
                 supplier_id=None, 
                 date=None, 
                 status="draft", 
                 notes="", 
                 total=0, 
                 items=None,
                 expected_delivery_date=None):
        self.id = id
        self.supplier_id = supplier_id
        self.date = date or datetime.now()
        self.status = status  # draft, sent, received, cancelled
        self.notes = notes
        self.total = total
        self.items = items or []
        self.expected_delivery_date = expected_delivery_date

class PurchaseOrderItem:
    """Item within a purchase order."""
    
    def __init__(self, 
                 id=None, 
                 order_id=None, 
                 product_id=None, 
                 quantity=0, 
                 unit_price=0, 
                 quantity_received=0,
                 product_code=None,
                 product_description=None):
        self.id = id
        self.order_id = order_id
        self.product_id = product_id
        self.product_code = product_code
        self.product_description = product_description
        self.quantity = quantity
        self.unit_price = unit_price
        self.quantity_received = quantity_received
        
    @property
    def total(self):
        """Calculate the total price for this item."""
        return self.quantity * self.unit_price
        
    @property
    def received_status(self):
        """Calculate the received status as a percentage."""
        if self.quantity == 0:
            return 0
        return min(100, (self.quantity_received / self.quantity) * 100)
