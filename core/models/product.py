from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base
from core.models.department import Department
import datetime

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), nullable=False, unique=True)
    description = Column(String(255), nullable=False)
    cost_price = Column(Float, nullable=False)
    sell_price = Column(Float, nullable=False)
    wholesale_price = Column(Float)  # Price 2
    special_price = Column(Float)  # Price 3
    department_id = Column(Integer, ForeignKey('departments.id'))
    unit = Column(String(50), default="Unidad")
    uses_inventory = Column(Boolean, default=True)
    quantity_in_stock = Column(Float, default=0.0)
    min_stock = Column(Float, default=0.0)
    max_stock = Column(Float)
    last_updated = Column(DateTime)
    notes = Column(String(500))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    department = relationship("Department", back_populates="products")
    inventory_movements = relationship("InventoryMovement", back_populates="product")
    purchases = relationship("Purchase", back_populates="product")
    # Consider adding fields like:
    # tax_rate: float = 0.0
    # image_path: Optional[str] = None
    # created_at: Optional[datetime.datetime] = None

    def __init__(self, code="", description="", cost_price=0.0, sell_price=0.0, 
                 wholesale_price=None, special_price=None, department_id=None, 
                 department=None, unit="Unidad", uses_inventory=True, 
                 quantity_in_stock=0.0, min_stock=0.0, max_stock=None, 
                 last_updated=None, notes=None, is_active=True, id=None):
        """
        Initialize a new Product.
        
        Args:
            code (str, optional): Product code or SKU. Defaults to empty string.
            description (str, optional): Product description. Defaults to empty string.
            cost_price (float, optional): Cost price of the product.
            sell_price (float, optional): Selling price of the product.
            wholesale_price (float, optional): Wholesale price.
            special_price (float, optional): Special price.
            department_id (int, optional): ID of the department this product belongs to.
            department (Department, optional): The Department object this product belongs to.
            unit (str, optional): Unit of measure, defaults to "Unidad".
            uses_inventory (bool, optional): Whether this product uses inventory tracking.
            quantity_in_stock (float, optional): Current quantity in stock.
            min_stock (float, optional): Minimum stock level.
            max_stock (float, optional): Maximum stock level.
            last_updated (datetime, optional): Last update timestamp.
            notes (str, optional): Additional notes about the product.
            is_active (bool, optional): Whether the product is active.
            id (int, optional): The product ID (typically set by the database).
        """
        self.code = code
        self.description = description
        self.cost_price = cost_price
        self.sell_price = sell_price
        self.wholesale_price = wholesale_price
        self.special_price = special_price
        self.department_id = department_id
        self.department = department
        self.unit = unit
        self.uses_inventory = uses_inventory
        self.quantity_in_stock = quantity_in_stock
        self.min_stock = min_stock
        self.max_stock = max_stock
        self.last_updated = last_updated
        self.notes = notes
        self.is_active = is_active
        if id is not None:
            self.id = id
