from sqlalchemy import (Column, Integer, String, Float, Boolean, DateTime, 
                        ForeignKey, UniqueConstraint, Table, Numeric, Text, Enum, DECIMAL, JSON)
from sqlalchemy.orm import relationship, registry, mapper
import datetime
import uuid

# Import the Base directly from database (modified to avoid circular import)
# import infrastructure.persistence.sqlite.database as db
# Base = db.Base
from infrastructure.persistence.sqlite.database import Base

# Import the SQLiteUUID type
from .types import SQLiteUUID

# Import core models after Base is initialized
from core.models.product import Product as CoreProduct, Department as CoreDepartment
from core.models.inventory import InventoryMovement as CoreInventoryMovement
from core.models.sale import Sale as CoreSale, SaleItem as CoreSaleItem
from core.models.customer import Customer as CoreCustomer
from core.models.credit_payment import CreditPayment as CoreCreditPayment
from core.models.user import User as CoreUser
from core.models.invoice import Invoice as CoreInvoice
from core.models.enums import PaymentType

# Import core models for reference if needed, but avoid direct coupling in ORM definitions
#  as CoreSupplier
# Order as CorePurchaseOrder, PurchaseOrderItem as CorePurchaseOrderItem

# Base.metadata is used implicitly by declarative classes inheriting from Base
mapper_registry = registry(metadata=Base.metadata)

# --- User --- (define UserOrm first to avoid circular references)
class UserOrm(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    email = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    # Define relationships with strings to avoid circular references
    sales = relationship("SaleOrm", back_populates="user")
    inventory_movements = relationship("InventoryMovementOrm", back_populates="user")
    credit_payments = relationship("CreditPaymentOrm", back_populates="user")
    cash_drawer_entries = relationship("CashDrawerEntryOrm", back_populates="user")

    def __repr__(self):
        return f"<UserOrm(id={self.id}, username='{self.username}', is_active={self.is_active})>"

class DepartmentOrm(Base):
    __tablename__ = "departments"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    # Relationship: One-to-Many (One Department has Many Products)
    products = relationship("ProductOrm", back_populates="department")

    def __repr__(self):
        return f"<DepartmentOrm(id={self.id}, name='{self.name}')>"

class ProductOrm(Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint('code', name='uq_product_code'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=False)
    cost_price = Column(Numeric(10, 2), nullable=False, default=0.0)
    sell_price = Column(Numeric(10, 2), nullable=False, default=0.0)
    wholesale_price = Column(Numeric(10, 2), nullable=True) # Price 2
    special_price = Column(Numeric(10, 2), nullable=True) # Price 3
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    unit = Column(String, nullable=False, default="Unidad")
    uses_inventory = Column(Boolean, nullable=False, default=True)
    quantity_in_stock = Column(Numeric(10, 3), nullable=False, default=0.0) # Allow 3 decimal places for quantity
    min_stock = Column(Numeric(10, 3), nullable=True, default=0.0) # Allow 3 decimal places for quantity
    max_stock = Column(Numeric(10, 3), nullable=True) # Allow 3 decimal places for quantity
    last_updated = Column(DateTime, nullable=True, onupdate=datetime.datetime.now)
    notes = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    # created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationship: Many-to-One (Many Products belong to One Department)
    department = relationship("DepartmentOrm", back_populates="products")

    def __repr__(self):
        return f"<ProductOrm(id={self.id}, code='{self.code}', description='{self.description}')>"

class InventoryMovementOrm(Base):
    __tablename__ = "inventory_movements"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True) # User performing the movement
    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.now, index=True)
    movement_type = Column(String, nullable=False, index=True) # 'SALE', 'PURCHASE', 'ADJUSTMENT', 'INITIAL'
    quantity = Column(Numeric(10, 3), nullable=False) # Positive for addition, negative for removal, 3 decimal places
    description = Column(String, nullable=True)
    related_id = Column(Integer, nullable=True, index=True) # e.g., Sale ID, Purchase ID

    # Relationship: Many-to-One (Many Movements belong to One Product)
    product = relationship("ProductOrm") # No back_populates needed if ProductOrm doesn't track movements directly

    # Relationship: Many-to-One (Many Movements performed by one User)
    user = relationship("UserOrm", back_populates="inventory_movements")

    def __repr__(self):
        return f"<InventoryMovementOrm(id={self.id}, product_id={self.product_id}, type='{self.movement_type}', qty={self.quantity})>"

class SaleOrm(Base):
    __tablename__ = "sales"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    date_time = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, index=True)
    total_amount = Column(Numeric(12, 2), nullable=False, default=0.0) # Calculated from items
    customer_id = Column(SQLiteUUID, ForeignKey('customers.id'), nullable=True, index=True)
    is_credit_sale = Column(Boolean, nullable=False, default=False) # Added credit flag
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True) # User who performed the sale
    payment_type = Column(Enum(PaymentType), nullable=True, index=True)

    # Relationship: One-to-Many (One Sale has Many SaleItems)
    items = relationship(
        "SaleItemOrm",
        back_populates="sale",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Relationship: Many-to-One (Many Sales belong to one Customer)
    customer = relationship("CustomerOrm", back_populates="sales")

    # Relationship: Many-to-One (Many Sales performed by one User)
    user = relationship("UserOrm", back_populates="sales")

    def __repr__(self):
        return f"<SaleOrm(id={self.id}, timestamp='{self.date_time}', total={self.total_amount})>"

class SaleItemOrm(Base):
    __tablename__ = "sale_items"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    quantity = Column(Numeric(10, 3), nullable=False) # Allow 3 decimal places for quantity
    unit_price = Column(Numeric(10, 2), nullable=False) # Price at the time of sale
    product_code = Column(String, nullable=True) # Denormalized
    product_description = Column(String, nullable=True) # Denormalized
    product_unit = Column(String, nullable=True, default="Unidad") # Unit of measure

    # Relationship: Many-to-One (Many SaleItems belong to One Sale)
    sale = relationship("SaleOrm", back_populates="items")

    # Relationship: Many-to-One (Many SaleItems relate to One Product)
    # We don't strictly need full product object here often, just ID is key.
    # A relationship can be added if needed for reporting joins.
    product = relationship("ProductOrm") # No back_populates unless Product needs SaleItems

    def __repr__(self):
        return f"<SaleItemOrm(id={self.id}, sale_id={self.sale_id}, product_id={self.product_id}, qty={self.quantity})>"

# New ORM Model for Customer
class CustomerOrm(Base):
    __tablename__ = 'customers'
    __table_args__ = {'extend_existing': True}

    id = Column(SQLiteUUID, primary_key=True, index=True, default=uuid.uuid4)
    name = Column(String, nullable=False, index=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True, index=True)
    address = Column(String, nullable=True)
    cuit = Column(String, nullable=True, unique=True, index=True) # Often unique
    iva_condition = Column(String, nullable=True)
    credit_limit = Column(Numeric(12, 2), default=0.0, nullable=False)
    credit_balance = Column(Numeric(12, 2), default=0.0, nullable=False) # Current debt
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.datetime.now)
    is_active = Column(Boolean, default=True, index=True)

    # Relationships
    # Add back-population for the Sale relationship
    sales = relationship("SaleOrm", back_populates="customer")
    # invoices = relationship("InvoiceOrm", back_populates="customer") # Add later
    credit_payments = relationship("CreditPaymentOrm", back_populates="customer") # Added CreditPayment relationship

    def __repr__(self):
        return f"<CustomerOrm(id={self.id}, name='{self.name}', phone='{self.phone}', email='{self.email}', cuit='{self.cuit}')>"

# New ORM Model for CreditPayment
class CreditPaymentOrm(Base):
    __tablename__ = 'credit_payments'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(SQLiteUUID, ForeignKey('customers.id'), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.now, index=True)
    notes = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True) # User registering the payment

    # Relationship: Many-to-One (Many Payments belong to One Customer)
    customer = relationship("CustomerOrm", back_populates="credit_payments")

    # Relationship: Many-to-One (Many Payments made by One User)
    user = relationship("UserOrm", back_populates="credit_payments")

    def __repr__(self):
        return f"<CreditPaymentOrm(id={self.id}, customer_id={self.customer_id}, amount={self.amount})>"

class InvoiceOrm(Base):
    __tablename__ = "invoices"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False, unique=True, index=True)  # One invoice per sale
    customer_id = Column(SQLiteUUID, ForeignKey('customers.id'), nullable=True, index=True)
    invoice_number = Column(String(20), nullable=True, unique=True, index=True)
    invoice_date = Column(DateTime, nullable=False, default=datetime.datetime.now, index=True)
    invoice_type = Column(String(1), default="B", index=True)  # A, B, or C
    
    # Customer details snapshot (serialized)
    customer_details = Column(Text, nullable=True)  # JSON serialized
    
    # Financial data
    subtotal = Column(Numeric(10, 2), nullable=False, default=0)
    iva_amount = Column(Numeric(10, 2), nullable=False, default=0)
    total = Column(Numeric(10, 2), nullable=False, default=0)
    
    # IVA condition
    iva_condition = Column(String(50), nullable=False, default="Consumidor Final")
    
    # AFIP data
    cae = Column(String(50), nullable=True)
    cae_due_date = Column(DateTime, nullable=True)
    
    # Other fields
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    sale = relationship("SaleOrm", backref="invoice")  # One-to-one relationship with sale

    def __repr__(self):
        return f"<InvoiceOrm(id={self.id}, sale_id={self.sale_id}, invoice_number='{self.invoice_number}')>"

class UnitOrm(Base):
    """ORM mapping for custom units."""
    __tablename__ = "units"
    __table_args__ = (
        UniqueConstraint('name', name='uq_unit_name'),
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True, index=True)
    abbreviation = Column(String(10), nullable=True)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.datetime.now)
    
    def __repr__(self):
        return f"<UnitOrm(id={self.id}, name='{self.name}', abbreviation='{self.abbreviation}')>"

class CashDrawerEntryOrm(Base):
    """ORM mapping for cash drawer entries."""
    __tablename__ = "cash_drawer_entries"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    entry_type = Column(String, nullable=False, index=True) # Will be mapped to CashDrawerEntryType enum
    amount = Column(Numeric(12, 2), nullable=False) 
    description = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    drawer_id = Column(Integer, nullable=True, index=True)
    
    # Relationship to User
    user = relationship("UserOrm", back_populates="cash_drawer_entries")

    def __repr__(self):
        return f"<CashDrawerEntryOrm(id={self.id}, type='{self.entry_type}', amount={self.amount})>"

def ensure_all_models_mapped():
    """
    Ensure all ORM model classes inheriting from Base are recognized by SQLAlchemy's metadata.
    This function now primarily serves as a verification step. The actual mapping
    happens when the classes are defined inheriting from Base.
    """
    # List all expected ORM model classes
    model_classes = [
        UserOrm, DepartmentOrm, ProductOrm, InventoryMovementOrm,
        SaleOrm, SaleItemOrm, CustomerOrm, CreditPaymentOrm,
        InvoiceOrm, UnitOrm, CashDrawerEntryOrm
    ]

    print(f"Verifying mapping for {len(model_classes)} models...")
    all_mapped = True
    missing_tables = []

    # Check if Base.metadata exists and has tables
    if not hasattr(Base, 'metadata') or not hasattr(Base.metadata, 'tables'):
         print("ERROR: Base.metadata or Base.metadata.tables not found!")
         return False

    tables_in_metadata = list(Base.metadata.tables.keys())
    print(f"Tables currently in Base.metadata: {tables_in_metadata}")

    for model in model_classes:
        # Check if the class itself exists and has a __tablename__
        if not hasattr(model, '__tablename__'):
            print(f"  - ERROR: Model {model.__name__} missing __tablename__ attribute.")
            all_mapped = False
            continue # Skip further checks for this model

        table_name = model.__tablename__

        # Check if the table name is registered in the metadata
        if table_name not in tables_in_metadata:
            print(f"  - ERROR: Model {model.__name__} table '{table_name}' not found in Base.metadata.")
            all_mapped = False
            missing_tables.append(table_name)
        else:
            print(f"  - Model {model.__name__} correctly mapped to table '{table_name}'")

    if not all_mapped:
        # Attempting to access __table__ might trigger registration if it hasn't happened
        # but the primary issue is usually the import order or Base inheritance.
        print(f"Attempting to force registration by accessing __table__...")
        try:
            for model in model_classes:
                if hasattr(model, '__tablename__'):
                    _ = model.__table__ # Access __table__
            # Re-check metadata
            tables_in_metadata = list(Base.metadata.tables.keys())
            print(f"Tables in Base.metadata after forced registration: {tables_in_metadata}")
            remaining_missing = [m.__tablename__ for m in model_classes if hasattr(m, '__tablename__') and m.__tablename__ not in tables_in_metadata]
            if remaining_missing:
                 raise RuntimeError(f"SQLAlchemy mapping failed. Missing tables in metadata after attempt: {remaining_missing}")
            else:
                 print("All tables seem registered after explicit access.")
                 all_mapped = True # Mark as mapped if successful
        except Exception as e:
             print(f"Error during forced registration: {e}")
             # Keep all_mapped as False

    if not all_mapped:
         # Provide more specific advice if mapping failed
         print("\nMapping Error Detected:")
         print("Please ensure:")
         print("  1. All ORM classes in models_mapping.py inherit from the 'Base' defined in database.py.")
         print("  2. The 'infrastructure.persistence.sqlite.database' module correctly initializes 'Base'.")
         print("  3. Imports are handled correctly to avoid circular dependencies.")
         raise RuntimeError(f"SQLAlchemy mapping verification failed. Missing tables: {missing_tables}")


    print(f"Successfully verified {len(model_classes)} models mapped to {len(tables_in_metadata)} tables in Base.metadata.")
    return True

def map_models():
    """
    Explicitly maps all ORM models to ensure they are registered with SQLAlchemy metadata.
    
    This function forces the registration of all models by accessing their __table__ attribute
    which ensures SQLAlchemy registers them with Base.metadata. This is particularly important
    for tests to ensure all tables are created properly.
    """
    # Explicitly map all models by accessing their __table__ attribute to trigger model registration
    tables = []
    
    # Get a list of all ORM classes that inherit from Base
    orm_classes = [
        UserOrm, DepartmentOrm, ProductOrm, InventoryMovementOrm, SaleOrm, 
        SaleItemOrm, CustomerOrm, CreditPaymentOrm,
        InvoiceOrm, UnitOrm,
        CashDrawerEntryOrm # Ensure CashDrawerEntryOrm is included here
    ]
    
    # Access __table__ attributes to ensure registration with metadata
    for cls in orm_classes:
        try:
            tables.append(cls.__table__)
        except Exception as e:
            print(f"Warning: Could not access __table__ for {cls.__name__}: {e}")
    
    # Optional: Log the number of tables found in metadata for verification
    # print(f"Models mapped. Found {len(Base.metadata.tables)} tables in metadata.")
    # print(f"Mapped table names: {[t.name for t in tables]}")

# Ensure map_models() is called when the module is imported,
# although it's also called in test_conftest.py fixture setup.
# map_models()
