from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from core.database import Base

class Supplier(Base):
    __tablename__ = 'suppliers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    contact_person = Column(String(100))
    phone = Column(String(20))
    email = Column(String(100))
    address = Column(String(255))
    cuit = Column(String(20))  # Clave Única de Identificación Tributaria (Argentina)
    notes = Column(String(500))
    is_active = Column(Boolean, default=True)  # Track supplier status
    
    # Add the missing relationship
    purchases = relationship("Purchase", back_populates="supplier")
