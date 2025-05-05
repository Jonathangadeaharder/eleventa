from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from core.database import Base
from datetime import datetime
import uuid
from infrastructure.persistence.sqlite.types import SQLiteUUID

class CreditPayment(Base):
    __tablename__ = 'credit_payments'
    
    id = Column(Integer, primary_key=True)
    amount = Column(Numeric(10, 2), nullable=False)
    customer_id = Column(SQLiteUUID, ForeignKey('customers.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    payment_date = Column(DateTime, default=datetime.utcnow)
    description = Column(String(255))
    
    # Temporarily remove relationship references to simplify testing
    # customer = relationship("CustomerOrm")
    # user = relationship("UserOrm")
    # invoice = relationship("Invoice", uselist=False, back_populates="credit_payment")
