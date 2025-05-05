from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

Base = declarative_base()

def create_schema(engine):
    """Create database schema with all tables."""
    # Import all models to ensure all tables are created
    from core.models import (  # noqa: F401
        department, product, cash_drawer, user, customer, sale, 
        credit_payment, inventory, invoice, purchase
    )
    Base.metadata.create_all(bind=engine)
