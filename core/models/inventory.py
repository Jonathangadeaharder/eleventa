from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base
from datetime import datetime

class InventoryMovement(Base):
    __tablename__ = 'inventory_movements'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    movement_type = Column(String(50), nullable=False)  # 'in' or 'out'
    date = Column(DateTime, default=datetime.utcnow)
    description = Column(String(255))
    
    product = relationship("Product", back_populates="inventory_movements")
    
    def __init__(self, product_id=None, quantity=None, movement_type=None, 
                 description=None, user_id=None, timestamp=None, 
                 related_id=None, id=None):
        """
        Initialize a new inventory movement.
        
        Args:
            product_id (int): The ID of the product.
            quantity (float): The quantity of the movement.
            movement_type (str): The type of movement (PURCHASE, SALE, ADJUST, etc).
            description (str, optional): Description of the movement.
            user_id (int, optional): ID of the user who made the movement.
            timestamp (datetime, optional): When the movement occurred.
            related_id (int, optional): ID of related entity (sale, purchase).
            id (int, optional): The movement ID.
        """
        self.product_id = product_id
        self.quantity = quantity
        self.movement_type = movement_type
        self.description = description
        self.user_id = user_id
        self.timestamp = timestamp
        self.related_id = related_id
        if id is not None:
            self.id = id
