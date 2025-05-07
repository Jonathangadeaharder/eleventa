from typing import List, Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime, timedelta, date
from decimal import Decimal
import json
import uuid
import logging

from sqlalchemy import select, func, delete, insert, update, and_, or_, not_, desc, asc, text
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import functions

# Adjust path to import interfaces and models
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.interfaces.repository_interfaces import (
    IDepartmentRepository, IProductRepository, IInventoryRepository, ISaleRepository, ICustomerRepository,
    ICreditPaymentRepository, ISupplierRepository, IPurchaseOrderRepository, IUserRepository,
    IInvoiceRepository, ICashDrawerRepository
)
from core.models.product import Department, Product
from core.models.inventory import InventoryMovement
from core.models.sale import Sale, SaleItem
from core.models.customer import Customer
from core.models.credit import CreditPayment
from core.models.supplier import Supplier
from core.models.purchase import PurchaseOrder, PurchaseOrderItem
from core.models.user import User
from core.models.invoice import Invoice
from core.models.cash_drawer import CashDrawerEntry, CashDrawerEntryType
from infrastructure.persistence.sqlite.database import Base

# Import specific ORM classes directly
from infrastructure.persistence.sqlite.models_mapping import (
    UserOrm, ProductOrm, DepartmentOrm, CustomerOrm, SaleOrm, SaleItemOrm,
    InventoryMovementOrm, SupplierOrm, PurchaseOrderOrm, PurchaseOrderItemOrm,
    InvoiceOrm, CashDrawerEntryOrm, CreditPaymentOrm
)

from ..utils import session_scope
from sqlalchemy.orm import joinedload
from sqlalchemy import or_

# --- Helper Function for ORM to Domain Model Mapping ---

def _map_department_orm_to_model(dept_orm: "DepartmentOrm") -> Department:
    """Maps the DepartmentOrm object to the Department domain model."""
    if not dept_orm:
        return None
    return Department(
        id=dept_orm.id,
        name=dept_orm.name
    )

# --- Helper Function for Product ORM to Domain Model Mapping ---

def _map_product_orm_to_model(prod_orm: "ProductOrm") -> Product:
    """Maps the ProductOrm object to the Product domain model."""
    if not prod_orm:
        return None
    # Map the related DepartmentOrm to Department model if it exists
    department_model = _map_department_orm_to_model(prod_orm.department) if prod_orm.department else None

    return Product(
        id=prod_orm.id,
        code=prod_orm.code,
        description=prod_orm.description,
        cost_price=prod_orm.cost_price,
        sell_price=prod_orm.sell_price,
        wholesale_price=prod_orm.wholesale_price,
        special_price=prod_orm.special_price,
        department_id=prod_orm.department_id,
        department=department_model, # Assign the mapped Department model
        unit=prod_orm.unit,
        uses_inventory=prod_orm.uses_inventory,
        quantity_in_stock=prod_orm.quantity_in_stock,
        min_stock=prod_orm.min_stock,
        max_stock=prod_orm.max_stock,
        last_updated=prod_orm.last_updated,
        notes=prod_orm.notes,
        is_active=prod_orm.is_active
    )

# --- Helper Function for Inventory Movement ORM to Domain Model Mapping ---

def _map_movement_orm_to_model(move_orm: "InventoryMovementOrm") -> InventoryMovement:
    """Maps the InventoryMovementOrm object to the InventoryMovement domain model."""
    if not move_orm:
        return None
    return InventoryMovement(
        id=move_orm.id,
        product_id=move_orm.product_id,
        user_id=move_orm.user_id,
        timestamp=move_orm.timestamp,
        movement_type=move_orm.movement_type,
        quantity=move_orm.quantity,
        description=move_orm.description,
        related_id=move_orm.related_id
    )

# --- Helper Functions for Sale ORM to Domain Model Mapping ---

def _map_sale_item_orm_to_model(item_orm: "SaleItemOrm") -> SaleItem:
    """
    Maps the SaleItemOrm object to the SaleItem domain model.
    
    Note: This converts float values from ORM to Decimal in the domain model.
    There is a potential for precision loss when the ORM stores values as float.
    For critical financial calculations, consider using a more precise storage type.
    """
    if not item_orm:
        return None
    return SaleItem(
        id=item_orm.id,
        sale_id=item_orm.sale_id,
        product_id=item_orm.product_id,
        quantity=Decimal(str(item_orm.quantity)), # Convert float back to Decimal
        unit_price=Decimal(str(item_orm.unit_price)), # Convert float back to Decimal
        product_code=item_orm.product_code,
        product_description=item_orm.product_description
    )

def _map_sale_orm_to_model(sale_orm: "SaleOrm") -> Sale:
    """Maps the SaleOrm object to the Sale domain model."""
    if not sale_orm:
        return None
    # Map related items using the item mapper
    # Ensure items are loaded (e.g., via lazy='selectin' or joinedload)
    items_model = [_map_sale_item_orm_to_model(item) for item in sale_orm.items] if sale_orm.items else []

    return Sale(
        id=sale_orm.id,
        timestamp=sale_orm.date_time,
        items=items_model,
        customer_id=sale_orm.customer_id, # Map customer_id
        is_credit_sale=sale_orm.is_credit_sale, # Map is_credit_sale
        user_id=sale_orm.user_id, # Map user_id
        payment_type=sale_orm.payment_type # Map payment_type
        # total is a calculated property
    )

# --- Helper Function for Customer ORM to Domain Model Mapping ---

def _map_customer_orm_to_model(cust_orm: "CustomerOrm") -> Optional[Customer]:
    """Maps the CustomerOrm object to the Customer domain model."""
    if not cust_orm:
        return None
    return Customer(
        id=cust_orm.id,
        name=cust_orm.name,
        phone=cust_orm.phone,
        email=cust_orm.email,
        address=cust_orm.address,
        cuit=cust_orm.cuit,
        iva_condition=cust_orm.iva_condition,
        credit_limit=cust_orm.credit_limit,
        credit_balance=cust_orm.credit_balance,
        is_active=cust_orm.is_active
    )

# --- Helper Function for CreditPayment ORM to Domain Model Mapping ---

def _map_credit_payment_orm_to_model(payment_orm: "CreditPaymentOrm") -> Optional[CreditPayment]:
    """
    Maps the CreditPaymentOrm object to the CreditPayment domain model.
    
    Note: Converting from float to Decimal may result in precision issues.
    For financial data, consider updating the ORM schema to use Numeric types.
    """
    if not payment_orm:
        return None
    return CreditPayment(
        id=payment_orm.id,
        customer_id=payment_orm.customer_id,
        amount=Decimal(str(payment_orm.amount)), # Convert float back to Decimal
        timestamp=payment_orm.timestamp,
        notes=payment_orm.notes,
        user_id=payment_orm.user_id
    )

# --- Helper Functions for Supplier/Purchase ORM to Domain Model Mapping ---

def _map_supplier_orm_to_model(supplier_orm: "SupplierOrm") -> Optional[Supplier]:
    """Maps the SupplierOrm object to the Supplier domain model."""
    if not supplier_orm:
        return None
    return Supplier(
        id=supplier_orm.id,
        name=supplier_orm.name,
        contact_person=supplier_orm.contact_person,
        phone=supplier_orm.phone,
        email=supplier_orm.email,
        address=supplier_orm.address,
        cuit=supplier_orm.cuit,
        notes=supplier_orm.notes
    )

def _map_purchase_order_item_orm_to_model(item_orm: "PurchaseOrderItemOrm") -> Optional[PurchaseOrderItem]:
    """Maps the PurchaseOrderItemOrm object to the PurchaseOrderItem domain model."""
    if not item_orm:
        return None
    return PurchaseOrderItem(
        id=item_orm.id,
        order_id=item_orm.purchase_order_id, # Correct argument name
        product_id=item_orm.product_id,
        product_code=item_orm.product_code,
        product_description=item_orm.product_description,
        quantity=item_orm.quantity_ordered, # Correct keyword for ORM
        unit_price=item_orm.cost_price, # Use unit_price from core model
        quantity_received=item_orm.quantity_received
    )

def _map_purchase_order_orm_to_model(po_orm: "PurchaseOrderOrm") -> Optional[PurchaseOrder]:
    """Maps the PurchaseOrderOrm object to the PurchaseOrder domain model."""
    if not po_orm:
        return None

    # Map related items and supplier if loaded
    items_model = [_map_purchase_order_item_orm_to_model(item) for item in po_orm.items] if po_orm.items else []
    supplier_model = _map_supplier_orm_to_model(po_orm.supplier) if po_orm.supplier else None

    return PurchaseOrder(
        id=po_orm.id,
        supplier_id=po_orm.supplier_id,
        date=po_orm.order_date, # Correct keyword
        expected_delivery_date=po_orm.expected_delivery_date,
        status=po_orm.status,
        notes=po_orm.notes,
        items=items_model,
        # created_at=po_orm.created_at, # Remove - not in domain model __init__
        # updated_at=po_orm.updated_at, # Remove - not in domain model __init__
        # Assign mapped supplier if available
        # supplier=supplier_model # Core model doesn't have supplier object directly
    )

# --- Helper Function for User ORM to Domain Model Mapping ---

def _map_user_orm_to_model(user_orm: "UserOrm") -> Optional[User]:
    """Maps the UserOrm object to the User domain model."""
    if not user_orm:
        return None
    return User(
        id=user_orm.id,
        username=user_orm.username,
        password_hash=user_orm.password_hash,
        is_active=user_orm.is_active,
        email=user_orm.email,
        is_admin=user_orm.is_admin
    )

# --- Helper Function for Invoice ORM to Domain Model Mapping ---
def _map_invoice_orm_to_model(invoice_orm: "InvoiceOrm") -> Optional[Invoice]:
    """Maps the InvoiceOrm object to the Invoice domain model."""
    if not invoice_orm:
        return None
    
    # Parse customer details from JSON if present
    customer_details = {}
    if invoice_orm.customer_details:
        try:
            customer_details = json.loads(invoice_orm.customer_details)
        except json.JSONDecodeError:
            # Handle invalid JSON - log error or use empty dict
            pass
    
    return Invoice(
        id=invoice_orm.id,
        sale_id=invoice_orm.sale_id,
        customer_id=invoice_orm.customer_id,
        invoice_number=invoice_orm.invoice_number,
        invoice_date=invoice_orm.invoice_date,
        invoice_type=invoice_orm.invoice_type,
        customer_details=customer_details,
        subtotal=Decimal(str(invoice_orm.subtotal)),
        iva_amount=Decimal(str(invoice_orm.iva_amount)),
        total=Decimal(str(invoice_orm.total)),
        iva_condition=invoice_orm.iva_condition,
        cae=invoice_orm.cae,
        cae_due_date=invoice_orm.cae_due_date,
        notes=invoice_orm.notes,
        is_active=invoice_orm.is_active
    )

# --- Helper Function for Invoice Domain Model to ORM Mapping ---
def _map_invoice_model_to_orm(invoice: Invoice, invoice_orm: Optional["InvoiceOrm"] = None) -> "InvoiceOrm":
    """Maps the Invoice domain model to the InvoiceOrm object."""
    if invoice_orm is None:
        invoice_orm = InvoiceOrm()
    
    invoice_orm.sale_id = invoice.sale_id
    invoice_orm.customer_id = invoice.customer_id
    invoice_orm.invoice_number = invoice.invoice_number
    invoice_orm.invoice_date = invoice.invoice_date
    invoice_orm.invoice_type = invoice.invoice_type
    
    # Serialize customer details to JSON
    if invoice.customer_details:
        invoice_orm.customer_details = json.dumps(invoice.customer_details)
    else:
        invoice_orm.customer_details = None
    
    invoice_orm.subtotal = float(invoice.subtotal) if invoice.subtotal is not None else 0
    invoice_orm.iva_amount = float(invoice.iva_amount) if invoice.iva_amount is not None else 0
    invoice_orm.total = float(invoice.total) if invoice.total is not None else 0
    invoice_orm.iva_condition = invoice.iva_condition
    invoice_orm.cae = invoice.cae
    invoice_orm.cae_due_date = invoice.cae_due_date
    invoice_orm.notes = invoice.notes
    invoice_orm.is_active = invoice.is_active
    
    return invoice_orm

# --- Repository Implementation ---

class SqliteDepartmentRepository(IDepartmentRepository):
    """SQLite implementation of the Department repository."""
    
    def __init__(self, session: Session):
        """Initialize with a database session.
        
        Args:
            session: The SQLAlchemy session to use
        """
        self.session = session
        
    def add(self, department: Department) -> Department:
        """Add a new department to the database."""
        # Check if a department with the same name already exists
        existing = self.session.query(DepartmentOrm).filter_by(name=department.name).first()
        if existing:
            raise ValueError(f"Department with name '{department.name}' already exists")
            
        # Create ORM object
        dept_orm = DepartmentOrm(
            name=department.name
        )
        
        # Add to session
        self.session.add(dept_orm)
        self.session.flush()  # Get ID immediately
        
        # Map the created ORM object back to a Department model and return it
        return _map_department_orm_to_model(dept_orm)
    
    def get_by_id(self, department_id: int) -> Optional[Department]:
        """Get a department by its ID."""
        dept_orm = self.session.query(DepartmentOrm).filter_by(id=department_id).first()
        return _map_department_orm_to_model(dept_orm)
    
    def get_by_name(self, name: str) -> Optional[Department]:
        """Get a department by its name."""
        dept_orm = self.session.query(DepartmentOrm).filter_by(name=name).first()
        return _map_department_orm_to_model(dept_orm)
    
    def get_all(self) -> List[Department]:
        """Get all departments."""
        dept_orms = self.session.query(DepartmentOrm).all()
        return [_map_department_orm_to_model(dept_orm) for dept_orm in dept_orms]
    
    def update(self, department: Department) -> Department:
        """Update an existing department."""
        # Check if the department exists
        existing = self.session.query(DepartmentOrm).filter_by(id=department.id).first()
        if not existing:
            raise ValueError(f"Department with ID {department.id} not found for update")
            
        # Check if the name is being changed and if it would conflict
        if department.name != existing.name:
            name_conflict = self.session.query(DepartmentOrm).filter_by(name=department.name).first()
            if name_conflict and name_conflict.id != department.id:
                raise ValueError(f"Department with name '{department.name}' already exists")
        
        # Update fields
        existing.name = department.name
        
        # Update in session
        self.session.add(existing)
        self.session.flush()
        
        # Return the updated department
        return _map_department_orm_to_model(existing)
    
    def delete(self, department_id: int) -> None:
        """Delete a department by its ID."""
        # First check if department exists
        existing = self.session.query(DepartmentOrm).filter_by(id=department_id).first()
        if not existing:
            raise ValueError(f"Department with ID {department_id} does not exist")
        
        # Check if any products reference this department
        products = self.session.query(ProductOrm).filter_by(department_id=department_id).count()
        if products > 0:
            raise ValueError(f"Departamento con ID {department_id} no puede ser eliminado, está en uso")
        
        # Delete the department
        result = self.session.query(DepartmentOrm).filter_by(id=department_id).delete()
        self.session.flush()  # Ensure changes are visible to current transaction

# Add other repository implementations (e.g., SqliteProductRepository) below

# --- Product Repository Implementation ---

class SqliteProductRepository(IProductRepository):
    """SQLite implementation of the product repository interface."""
    def __init__(self, session: Session):
        """Inject the database session."""
        self.session = session

    def _create_product_orm(self, product: Product) -> ProductOrm:
        """Helper method to create a ProductOrm from a Product domain model."""
        # Create ProductOrm object with attribute assignment
        product_orm = ProductOrm()
        product_orm.code = product.code
        product_orm.description = product.description
        product_orm.cost_price = product.cost_price
        product_orm.sell_price = product.sell_price
        product_orm.wholesale_price = product.wholesale_price
        product_orm.special_price = product.special_price
        product_orm.department_id = product.department_id
        product_orm.unit = product.unit
        product_orm.uses_inventory = product.uses_inventory
        product_orm.quantity_in_stock = product.quantity_in_stock
        product_orm.min_stock = product.min_stock
        product_orm.max_stock = product.max_stock
        product_orm.notes = product.notes
        product_orm.is_active = product.is_active
        return product_orm

    def add(self, product: Product) -> Product:
        """Add a new product to the repository."""
        try:
            # Create a new ProductOrm from the Product domain model
            product_orm = self._create_product_orm(product)
            
            # Add the product to the session and flush to get the ID
            self.session.add(product_orm)
            self.session.flush()
            
            # Update the product with its new ID
            product.id = product_orm.id
            
            return product
        except IntegrityError as e:
            # Don't rollback here - transaction management is handled by session scope
            # For unique constraint on code
            if "UNIQUE constraint failed: products.code" in str(e):
                raise ValueError(f"Product code '{product.code}' already exists")
            raise ValueError(f"Error adding product: {e}")

    def get_by_id(self, product_id: int) -> Optional[Product]:
        # Use joinedload to eager load department
        stmt = select(ProductOrm).options(joinedload(ProductOrm.department)).where(ProductOrm.id == product_id)
        prod_orm = self.session.execute(stmt).scalar_one_or_none()
        return _map_product_orm_to_model(prod_orm)

    def get_by_code(self, code: str) -> Optional[Product]:
        try:
            # Use joinedload to eager load department
            stmt = select(ProductOrm).options(joinedload(ProductOrm.department)).where(ProductOrm.code == code)
            prod_orm = self.session.execute(stmt).scalar_one_or_none()
            return _map_product_orm_to_model(prod_orm)
        except Exception as e:
            logging.error(f"Repository operation get_by_code failed: {e}")
            # Log exception but return None for missing product instead of raising error
            return None

    def get_all(self, filter_params: Optional[Dict[str, Any]] = None, 
                sort_by: Optional[str] = None, limit: Optional[int] = None, 
                offset: Optional[int] = None, sort_params: Optional[Dict[str, Any]] = None,
                pagination_params: Optional[Dict[str, Any]] = None) -> List[Product]:
        """Retrieve products with optional filtering, sorting, and pagination."""
        stmt = select(ProductOrm).options(joinedload(ProductOrm.department))
        
        # Filters
        if filter_params:
            for field, value in filter_params.items():
                stmt = stmt.where(getattr(ProductOrm, field) == value)
        
        # Sorting (handle both old sort_by and new sort_params approaches)
        if sort_params:
            field_name = sort_params.get('sort_by', 'description')
            direction = sort_params.get('sort_order', 'asc')
            column = getattr(ProductOrm, field_name, None)
            if column is not None:
                if direction.lower() == 'asc':
                    stmt = stmt.order_by(column.asc())
                elif direction.lower() == 'desc':
                    stmt = stmt.order_by(column.desc())
        elif sort_by:
            parts = sort_by.rsplit('_', 1)
            if len(parts) == 2:
                field_name, direction = parts
                column = getattr(ProductOrm, field_name, None)
                if column is not None:
                    if direction.lower() == 'asc':
                        stmt = stmt.order_by(column.asc())
                    elif direction.lower() == 'desc':
                        stmt = stmt.order_by(column.desc())
        else:
            stmt = stmt.order_by(ProductOrm.description)
            
        # Pagination (handle both old limit/offset and new pagination_params)
        if pagination_params:
            page = pagination_params.get('page', 1)
            page_size = pagination_params.get('page_size', 10)
            if page and page_size:
                stmt = stmt.limit(page_size).offset((page - 1) * page_size)
        else:
            # Original pagination
            if limit is not None:
                stmt = stmt.limit(limit)
            if offset is not None:
                stmt = stmt.offset(offset)
                
        results = self.session.execute(stmt).scalars().all()
        return [_map_product_orm_to_model(prod_orm) for prod_orm in results]

    def get_by_department_id(self, department_id: int) -> List[Product]:
        """Retrieves all products belonging to a specific department."""
        stmt = select(ProductOrm).options(joinedload(ProductOrm.department)).where(
            ProductOrm.department_id == department_id,
            ProductOrm.is_active == True # Optionally filter by active products
        ).order_by(ProductOrm.description)
        results = self.session.execute(stmt).scalars().all()
        return [_map_product_orm_to_model(prod_orm) for prod_orm in results]

    def update(self, product: Product) -> Product:
        """Update an existing product."""
        # Check if product exists
        if not product.id:
            raise ValueError("Product ID is required for update")
            
        product_orm = self.session.get(ProductOrm, product.id)
        if not product_orm:
            raise ValueError(f"Product with ID {product.id} not found")
            
        # Update product attributes
        product_orm.code = product.code
        product_orm.description = product.description
        product_orm.cost_price = float(product.cost_price)
        product_orm.sell_price = float(product.sell_price)
        product_orm.wholesale_price = float(product.wholesale_price) if product.wholesale_price else None
        product_orm.special_price = float(product.special_price) if product.special_price else None
        product_orm.department_id = product.department_id
        product_orm.unit = product.unit
        product_orm.uses_inventory = product.uses_inventory
        product_orm.quantity_in_stock = float(product.quantity_in_stock)
        product_orm.min_stock = float(product.min_stock) if product.min_stock else None
        product_orm.max_stock = float(product.max_stock) if product.max_stock else None
        product_orm.notes = product.notes
        product_orm.is_active = product.is_active
        product_orm.last_updated = datetime.now()
        
        try:
            self.session.flush()
            # Return a new instance of the domain model mapped from the ORM
            return _map_product_orm_to_model(product_orm)
        except IntegrityError as e:
            # Don't rollback here - transaction management is handled by session scope
            if "UNIQUE constraint failed: products.code" in str(e):
                raise ValueError(f"Product code '{product.code}' already exists")
            raise ValueError(f"Error updating product: {e}")

    def delete(self, product_id: int) -> None:
        """Delete a product by its ID."""
        prod_orm = self.session.get(ProductOrm, product_id)
        if not prod_orm:
            return
        self.session.delete(prod_orm)
        self.session.flush()

    def search(self, term: str) -> List[Product]:
        search_pattern = f"%{term.lower()}%"
        stmt = select(ProductOrm).options(joinedload(ProductOrm.department)).where(
            ProductOrm.is_active == True,
            or_(
                func.lower(ProductOrm.code).like(search_pattern),
                func.lower(ProductOrm.description).like(search_pattern)
                # Add other searchable fields if needed (e.g., department name via join)
            )
        ).order_by(ProductOrm.description)
        results = self.session.execute(stmt).scalars().all()
        return [_map_product_orm_to_model(prod_orm) for prod_orm in results]

    def get_low_stock(self, threshold: Optional[float] = None) -> List[Product]:
        """Retrieves products that are low in stock."""
        stmt = select(ProductOrm).options(joinedload(ProductOrm.department)).where(
            ProductOrm.is_active == True,
            ProductOrm.uses_inventory == True,
            ProductOrm.min_stock.isnot(None),
            ProductOrm.quantity_in_stock <= ProductOrm.min_stock
        )
        # Apply explicit threshold if provided
        if threshold is not None:
            stmt = stmt.where(ProductOrm.quantity_in_stock <= threshold)
        stmt = stmt.order_by(ProductOrm.description)

        results = self.session.execute(stmt).scalars().all()
        return [_map_product_orm_to_model(prod_orm) for prod_orm in results]

    def update_stock(self, product_id: int, new_quantity: float, cost_price: Optional[float] = None) -> None:
        """
        Update the stock quantity of a product, and optionally its cost price.
        
        Note: This method uses float for quantities which is consistent with the ORM schema,
        but may introduce precision issues for exact financial calculations. Consider
        using Decimal in the business logic and only converting to float at the ORM boundary.
        """
        prod_orm = self.session.get(ProductOrm, product_id)
        if prod_orm:
            # Convert Decimal to float if needed
            if hasattr(new_quantity, "__float__"):
                new_quantity = float(new_quantity)
                
            prod_orm.quantity_in_stock = new_quantity
            
            if cost_price is not None:
                # Convert Decimal to float if needed
                if hasattr(cost_price, "__float__"):
                    cost_price = float(cost_price)
                prod_orm.cost_price = cost_price
                
            # Use flush instead of commit to respect transaction boundaries
            self.session.flush()

# --- Inventory Movement Repository Implementation ---

class SqliteInventoryRepository(IInventoryRepository):
    """SQLite implementation of the Inventory repository."""
    
    def __init__(self, session: Session):
        """Initialize with a database session.
        
        Args:
            session: The SQLAlchemy session to use
        """
        self.session = session
    
    def add_movement(self, movement: InventoryMovement) -> InventoryMovement:
        """Add a new inventory movement record."""
        # Only set id if it is not None and is an integer
        movement_kwargs = dict(
            product_id=movement.product_id,
            user_id=movement.user_id,
            timestamp=movement.timestamp or datetime.now(),
            movement_type=movement.movement_type,
            quantity=movement.quantity,
            description=movement.description,
            related_id=movement.related_id
        )
        if movement.id is not None:
            if isinstance(movement.id, int):
                movement_kwargs['id'] = movement.id
            else:
                raise ValueError("InventoryMovement.id must be an integer or None.")
        movement_orm = InventoryMovementOrm(**movement_kwargs)
        # Add to session
        self.session.add(movement_orm)
        self.session.flush()  # Get ID immediately
        # Return the mapped model with the assigned ID
        return _map_movement_orm_to_model(movement_orm)
    
    def get_movements_for_product(self, product_id: int) -> List[InventoryMovement]:
        """Get all inventory movements for a specific product."""
        movements = self.session.query(InventoryMovementOrm).filter_by(product_id=product_id).order_by(InventoryMovementOrm.timestamp.desc()).all()
        return [_map_movement_orm_to_model(m) for m in movements]
    
    def get_all_movements(self) -> List[InventoryMovement]:
        """Get all inventory movements."""
        movements = self.session.query(InventoryMovementOrm).order_by(InventoryMovementOrm.timestamp.desc()).all()
        return [_map_movement_orm_to_model(m) for m in movements]

# --- Sale Repository Implementation ---

class SqliteSaleRepository(ISaleRepository):
    """SQLite implementation of the sale repository interface."""

    def __init__(self, session):
        """Initialize with database session."""
        self.session = session

    def add_sale(self, sale: Sale) -> Sale:
        """Adds a new sale to the repository."""
        # Create ORM model from core model
        sale_orm = SaleOrm(
            date_time=sale.timestamp,  # Use date_time which is the column name in SaleOrm
            customer_id=sale.customer_id,
            is_credit_sale=sale.is_credit_sale,
            user_id=sale.user_id,
            payment_type=sale.payment_type
        )
        
        # Convert sale items to ORM models
        total_amount = 0.0
        for item in sale.items:
            item_orm = SaleItemOrm(
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                product_code=item.product_code,
                product_description=item.product_description
            )
            # Calculate the subtotal for this item and add to total
            subtotal = float(item.quantity) * float(item.unit_price)
            total_amount += subtotal
            sale_orm.items.append(item_orm)
        
        # Set the calculated total amount
        sale_orm.total_amount = total_amount
        
        # Add to session and flush to get IDs
        self.session.add(sale_orm)
        self.session.flush()
        
        # Map the persisted ORM object back to the domain model to ensure IDs are correct
        persisted_sale = _map_sale_orm_to_model(sale_orm)
        return persisted_sale # Return the newly mapped object with IDs

    def get_by_id(self, sale_id: int) -> Optional[Sale]:
        """Retrieves a sale by its unique ID."""
        try:
            stmt = select(SaleOrm).filter(SaleOrm.id == sale_id).options(joinedload(SaleOrm.items))
            sale_orm = self.session.execute(stmt).unique().scalar_one_or_none()
            return _map_sale_orm_to_model(sale_orm)
        except Exception as e:
            # Log error but don't crash - handle gracefully for concurrent access
            print(f"Error retrieving sale: {e}")
            return None

    def get_sale_by_id(self, sale_id: int) -> Optional[Sale]:
        """Legacy method - use get_by_id instead."""
        return self.get_by_id(sale_id)

    def get_sales_by_period(self, start_date, end_date) -> List[Sale]:
        """Gets all sales within a specific time period."""
        # Convert date objects to datetime if needed
        if not isinstance(start_date, datetime):
            start_time = datetime.combine(start_date, datetime.min.time())
        else:
            start_time = start_date
            
        if not isinstance(end_date, datetime):
            end_time = datetime.combine(end_date, datetime.max.time())
        else:
            end_time = end_date
            
        sale_orms = self.session.query(SaleOrm).filter(
            SaleOrm.date_time >= start_time,
            SaleOrm.date_time <= end_time
        ).order_by(SaleOrm.date_time).all()
        
        # Convert ORM models to core models
        sales = []
        for sale_orm in sale_orms:
            # Create Sale object
            sale = Sale(
                id=sale_orm.id,
                timestamp=sale_orm.date_time,
                customer_id=sale_orm.customer_id,
                is_credit_sale=sale_orm.is_credit_sale,
                user_id=sale_orm.user_id,
                payment_type=sale_orm.payment_type
            )
            
            # Add items
            items = []
            for item_orm in sale_orm.items:
                item = SaleItem(
                    id=item_orm.id,
                    sale_id=item_orm.sale_id,
                    product_id=item_orm.product_id,
                    quantity=item_orm.quantity,
                    unit_price=item_orm.unit_price,
                    product_code=item_orm.product_code,
                    product_description=item_orm.product_description
                )
                items.append(item)
            
            sale.items = items
            sales.append(sale)
        
        return sales
    
    def get_sales_summary_by_period(self, start_date=None, end_date=None, 
                                  group_by: str = 'day') -> List[Dict[str, Any]]:
        """Gets aggregated sales data grouped by a time period."""
        # Set default dates if not provided
        if start_date is None:
            start_date = datetime.now().date() - timedelta(days=30)  # Default to last 30 days
        if end_date is None:
            end_date = datetime.now().date()
            
        # Convert date objects to datetime if needed
        if not isinstance(start_date, datetime):
            start_time = datetime.combine(start_date, datetime.min.time())
        else:
            start_time = start_date
            
        if not isinstance(end_date, datetime):
            end_time = datetime.combine(end_date, datetime.max.time())
        else:
            end_time = end_date
            
        from sqlalchemy import func, text
        
        # Define the date grouping based on the group_by parameter
        if group_by == 'day':
            # Use strftime for SQLite compatibility
            date_group = func.strftime('%Y-%m-%d', SaleOrm.date_time)
            date_format = '%Y-%m-%d'
        elif group_by == 'week':
            # Group by week as string
            date_group = func.strftime('%Y-%W', SaleOrm.date_time)
            date_format = '%Y-W%W' # Year-week format
        elif group_by == 'month':
            # Group by month as string
            date_group = func.strftime('%Y-%m', SaleOrm.date_time)
            date_format = '%Y-%m' # Year-month format
        else:
            # Default to day if invalid group_by
            date_group = func.strftime('%Y-%m-%d', SaleOrm.date_time)
            date_format = '%Y-%m-%d'
        
        # Use SQLAlchemy query builder instead of raw SQL for better compatibility
        results = self.session.query(
            date_group.label('date'),
            func.count(func.distinct(SaleOrm.id)).label('num_sales'),
            func.sum(SaleOrm.total_amount).label('total_sales')
        ).filter(
            SaleOrm.date_time >= start_time,
            SaleOrm.date_time <= end_time
        ).group_by(
            date_group
        ).order_by(
            date_group
        ).all()
        
        # Convert query results to dictionary list
        summary = []
        for row in results:
            date_str = row.date if row.date else 'Unknown'
            
            summary.append({
                'date': date_str,
                'total_sales': float(row.total_sales) if row.total_sales else 0.0,
                'num_sales': row.num_sales
            })
        
        return summary
    
    def get_sales_by_payment_type(self, start_date=None, end_date=None) -> List[Dict[str, Any]]:
        """Gets sales data aggregated by payment type for a period."""
        # Set default dates if not provided
        if start_date is None:
            start_date = datetime.now().date() - timedelta(days=30)  # Default to last 30 days
        if end_date is None:
            end_date = datetime.now().date()
            
        # Convert date objects to datetime if needed
        if not isinstance(start_date, datetime):
            start_time = datetime.combine(start_date, datetime.min.time())
        else:
            start_time = start_date
            
        if not isinstance(end_date, datetime):
            end_time = datetime.combine(end_date, datetime.max.time())
        else:
            end_time = end_date
            
        from sqlalchemy import func
        
        # Query for aggregated data by payment type
        results = self.session.query(
            SaleOrm.payment_type,
            func.sum(SaleItemOrm.quantity * SaleItemOrm.unit_price).label('total_amount'),
            func.count(func.distinct(SaleOrm.id)).label('num_sales')
        ).join(
            SaleItemOrm, SaleOrm.id == SaleItemOrm.sale_id
        ).filter(
            SaleOrm.date_time >= start_time,
            SaleOrm.date_time <= end_time
        ).group_by(
            SaleOrm.payment_type
        ).order_by(
            func.sum(SaleItemOrm.quantity * SaleItemOrm.unit_price).desc()
        ).all()
        
        # Convert query results to dictionary list
        payment_summary = []
        for row in results:
            payment_type = row.payment_type if row.payment_type else "Sin especificar"
            payment_summary.append({
                'payment_type': payment_type,
                'total_amount': float(row.total_amount) if row.total_amount else 0.0,
                'total_sales': float(row.total_amount) if row.total_amount else 0.0,  # Alias for the test
                'num_sales': row.num_sales
            })
        
        return payment_summary
    
    def get_sales_by_department(self, start_date=None, end_date=None) -> List[Dict[str, Any]]:
        """Gets sales data aggregated by product department for a period."""
        # Set default dates if not provided
        if start_date is None:
            start_date = datetime.now().date() - timedelta(days=30)  # Default to last 30 days
        if end_date is None:
            end_date = datetime.now().date()
            
        # Convert date objects to datetime if needed
        if not isinstance(start_date, datetime):
            start_time = datetime.combine(start_date, datetime.min.time())
        else:
            start_time = start_date
            
        if not isinstance(end_date, datetime):
            end_time = datetime.combine(end_date, datetime.max.time())
        else:
            end_time = end_date
            
        from sqlalchemy import func
        
        # Query for aggregated data by department
        results = self.session.query(
            DepartmentOrm.id.label('department_id'),
            DepartmentOrm.name.label('department_name'),
            func.sum(SaleItemOrm.quantity * SaleItemOrm.unit_price).label('total_amount'),
            func.sum(SaleItemOrm.quantity).label('num_items')
        ).join(
            ProductOrm, ProductOrm.id == SaleItemOrm.product_id
        ).outerjoin(
            DepartmentOrm, DepartmentOrm.id == ProductOrm.department_id
        ).join(
            SaleOrm, SaleOrm.id == SaleItemOrm.sale_id
        ).filter(
            SaleOrm.date_time >= start_time,
            SaleOrm.date_time <= end_time
        ).group_by(
            DepartmentOrm.id, DepartmentOrm.name
        ).order_by(
            func.sum(SaleItemOrm.quantity * SaleItemOrm.unit_price).desc()
        ).all()
        
        # Convert query results to dictionary list
        department_summary = []
        for row in results:
            department_summary.append({
                'department_id': row.department_id,
                'department_name': row.department_name if row.department_name else "Sin departamento",
                'total_amount': float(row.total_amount) if row.total_amount else 0.0,
                'total_sales': float(row.total_amount) if row.total_amount else 0.0,  # Alias for test compatibility
                'num_items': float(row.num_items) if row.num_items else 0.0
            })
        
        return department_summary
    
    def get_sales_by_customer(self, start_date=None, end_date=None, limit: int = 10) -> List[Dict[str, Any]]:
        """Gets sales data aggregated by customer for a period."""
        # Set default dates if not provided
        if start_date is None:
            start_date = datetime.now().date() - timedelta(days=30)  # Default to last 30 days
        if end_date is None:
            end_date = datetime.now().date()
            
        # Convert date objects to datetime if needed
        if not isinstance(start_date, datetime):
            start_time = datetime.combine(start_date, datetime.min.time())
        else:
            start_time = start_date
            
        if not isinstance(end_date, datetime):
            end_time = datetime.combine(end_date, datetime.max.time())
        else:
            end_time = end_date
            
        from sqlalchemy import func
        
        # Query for aggregated data by customer
        results = self.session.query(
            SaleOrm.customer_id,
            CustomerOrm.name.label('customer_name'),
            func.sum(SaleItemOrm.quantity * SaleItemOrm.unit_price).label('total_amount'),
            func.count(func.distinct(SaleOrm.id)).label('num_sales')
        ).join(
            SaleItemOrm, SaleOrm.id == SaleItemOrm.sale_id
        ).outerjoin(
            CustomerOrm, CustomerOrm.id == SaleOrm.customer_id
        ).filter(
            SaleOrm.date_time >= start_time,
            SaleOrm.date_time <= end_time,
            SaleOrm.customer_id != None  # Only include sales with customers
        ).group_by(
            SaleOrm.customer_id, CustomerOrm.name
        ).order_by(
            func.sum(SaleItemOrm.quantity * SaleItemOrm.unit_price).desc()
        ).limit(limit).all()
        
        # Convert query results to dictionary list
        customer_summary = []
        for row in results:
            customer_summary.append({
                'customer_id': row.customer_id,
                'customer_name': row.customer_name if row.customer_name else f"Cliente #{row.customer_id}",
                'total_amount': float(row.total_amount) if row.total_amount else 0.0,
                'total_sales': float(row.total_amount) if row.total_amount else 0.0,  # Alias for test
                'num_sales': row.num_sales
            })
        
        return customer_summary
    
    def get_top_selling_products(self, start_date=None, end_date=None, limit: int = 10) -> List[Dict[str, Any]]:
        """Gets the top selling products for a period."""
        # Set default dates if not provided
        if start_date is None:
            start_date = datetime.now().date() - timedelta(days=30)  # Default to last 30 days
        if end_date is None:
            end_date = datetime.now().date()
            
        # Convert date objects to datetime if needed
        if not isinstance(start_date, datetime):
            start_time = datetime.combine(start_date, datetime.min.time())
        else:
            start_time = start_date
            
        if not isinstance(end_date, datetime):
            end_time = datetime.combine(end_date, datetime.max.time())
        else:
            end_time = end_date
            
        from sqlalchemy import func
        
        # Query for top selling products
        results = self.session.query(
            SaleItemOrm.product_id,
            SaleItemOrm.product_code,
            SaleItemOrm.product_description,
            func.sum(SaleItemOrm.quantity).label('quantity_sold'),
            func.sum(SaleItemOrm.quantity * SaleItemOrm.unit_price).label('total_amount')
        ).join(
            SaleOrm, SaleOrm.id == SaleItemOrm.sale_id
        ).filter(
            SaleOrm.date_time >= start_time,
            SaleOrm.date_time <= end_time
        ).group_by(
            SaleItemOrm.product_id, SaleItemOrm.product_code, SaleItemOrm.product_description
        ).order_by(
            func.sum(SaleItemOrm.quantity).desc()
        ).limit(limit).all()
        
        # Convert query results to dictionary list
        product_summary = []
        for row in results:
            product_summary.append({
                'product_id': row.product_id,
                'product_code': row.product_code,
                'product_description': row.product_description,
                'quantity_sold': float(row.quantity_sold) if row.quantity_sold else 0.0,
                'units_sold': float(row.quantity_sold) if row.quantity_sold else 0.0,  # Alias for the test
                'total_amount': float(row.total_amount) if row.total_amount else 0.0
            })
        
        return product_summary
    
    def calculate_profit_for_period(self, start_date=None, end_date=None) -> Dict[str, Any]:
        """Calculates the total profit for a period (revenue - cost)."""
        # Set default dates if not provided
        if start_date is None:
            start_date = datetime.now().date() - timedelta(days=30)  # Default to last 30 days
        if end_date is None:
            end_date = datetime.now().date()
            
        # Convert date objects to datetime if needed
        if not isinstance(start_date, datetime):
            start_time = datetime.combine(start_date, datetime.min.time())
        else:
            start_time = start_date
            
        if not isinstance(end_date, datetime):
            end_time = datetime.combine(end_date, datetime.max.time())
        else:
            end_time = end_date
            
        from sqlalchemy import func
        
        # Query for total revenue
        revenue_result = self.session.query(
            func.sum(SaleItemOrm.quantity * SaleItemOrm.unit_price).label('total_revenue')
        ).join(
            SaleOrm, SaleOrm.id == SaleItemOrm.sale_id
        ).filter(
            SaleOrm.date_time >= start_time,
            SaleOrm.date_time <= end_time
        ).scalar()
        
        # Convert to float or default to 0.0
        total_revenue = float(revenue_result) if revenue_result else 0.0
        
        # Query for total cost - we need to join with ProductOrm to get cost prices
        cost_result = self.session.query(
            func.sum(SaleItemOrm.quantity * ProductOrm.cost_price).label('total_cost')
        ).join(
            SaleOrm, SaleOrm.id == SaleItemOrm.sale_id
        ).join(
            ProductOrm, ProductOrm.id == SaleItemOrm.product_id
        ).filter(
            SaleOrm.date_time >= start_time,
            SaleOrm.date_time <= end_time
        ).scalar()
        
        # Convert to float or default to 0.0
        total_cost = float(cost_result) if cost_result else 0.0
        
        # Calculate profit and margin
        profit = total_revenue - total_cost
        margin = profit / total_revenue if total_revenue > 0 else 0
        
        return {
            'revenue': total_revenue,
            'cost': total_cost,
            'profit': profit,
            'margin': margin
        }

    def get_sales_for_customer(self, customer_id, limit=None) -> List[Sale]:
        """Gets sales associated with a specific customer."""
        query = self.session.query(SaleOrm).filter(
            SaleOrm.customer_id == customer_id
        ).order_by(
            SaleOrm.date_time.desc()
        )
        
        if limit:
            query = query.limit(limit)
            
        sale_orms = query.all()
        
        # Convert to domain models
        return [self._orm_to_model(sale_orm) for sale_orm in sale_orms]
    
    def get_latest_sales(self, limit: int = 10) -> List[Sale]:
        """Gets the most recent sales."""
        sale_orms = self.session.query(SaleOrm).order_by(
            SaleOrm.date_time.desc()
        ).limit(limit).all()
        
        # Convert to domain models
        return [self._orm_to_model(sale_orm) for sale_orm in sale_orms]

# --- Customer Repository Implementation ---

class SqliteCustomerRepository(ICustomerRepository):
    """SQLite implementation of the customer repository interface."""
    def __init__(self, session: Session):
        """Inject the database session."""
        self.session = session

    def add(self, customer: Customer) -> Customer:
        """Add a new customer to the repository."""
        try:
            # LOGGING: Print type and value of customer.id and customer.cuit before adding
            print(f"[DEBUG] Adding customer: customer.id={customer.id} (type={type(customer.id)}), customer.cuit={customer.cuit} (type={type(customer.cuit)})")
            # Check for duplicates
            if customer.cuit:  # Only check if CUIT is provided
                # Use text SQL for simpler and more reliable query
                existing = self.session.execute(
                    text("SELECT id FROM customers WHERE cuit = :cuit"),
                    {"cuit": customer.cuit}
                ).scalar_one_or_none()
                
                if existing:
                    raise ValueError(f"Customer with CUIT {customer.cuit} already exists")

            # Check for duplicate email
            if customer.email:
                existing_email = self.session.execute(
                    text("SELECT id FROM customers WHERE email = :email"),
                    {"email": customer.email}
                ).scalar_one_or_none()
                if existing_email:
                    raise ValueError(f"Customer with email {customer.email} already exists")

            # Create a new CustomerOrm object and set attributes individually
            customer_orm = CustomerOrm()
            # Assign customer.id directly (should be uuid.UUID)
            if customer.id is not None:
                customer_orm.id = customer.id
            customer_orm.name = customer.name
            customer_orm.phone = customer.phone
            customer_orm.email = customer.email
            customer_orm.address = customer.address
            customer_orm.cuit = customer.cuit
            customer_orm.iva_condition = customer.iva_condition
            customer_orm.credit_limit = customer.credit_limit
            customer_orm.credit_balance = customer.credit_balance
            customer_orm.is_active = customer.is_active

            # LOGGING: Print type and value of customer_orm before adding
            print(f"[DEBUG] CustomerOrm before add: id={customer_orm.id} (type={type(customer_orm.id)})")

            # Add to session
            self.session.add(customer_orm)
            self.session.flush()  # Flush to get the generated ID

            # LOGGING: Print type and value of customer_orm.id after flush
            print(f"[DEBUG] CustomerOrm after flush: id={customer_orm.id} (type={type(customer_orm.id)})")

            # Map the generated UUID back to the domain model
            customer.id = customer_orm.id

            return customer
        except Exception as e:
            # Removed self.session.rollback() - let the caller's session_scope handle it
            if isinstance(e, ValueError):
                raise  # Re-raise already formatted errors
            raise ValueError(f"Error adding customer: {e}")

    def get_by_id(self, customer_id: uuid.UUID) -> Optional[Customer]: # Changed type hint to uuid.UUID
        # Use filter for UUID comparison as session.get might not work reliably with custom types/UUIDs
        cust_orm = self.session.query(CustomerOrm).filter(CustomerOrm.id == customer_id).first()
        return _map_customer_orm_to_model(cust_orm)

    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None, page: Optional[int] = None, page_size: Optional[int] = 10) -> List[Customer]:
        """Retrieve all active customers with optional pagination."""
        stmt = select(CustomerOrm).where(CustomerOrm.is_active == True).order_by(CustomerOrm.name)
        
        # Handle new pagination style (page-based)
        if page is not None:
            if page_size is None:
                page_size = 10
            stmt = stmt.limit(page_size).offset((page - 1) * page_size)
        # Handle old pagination style (limit/offset)
        else:
            if limit is not None:
                stmt = stmt.limit(limit)
            if offset is not None:
                stmt = stmt.offset(offset)
                
        results = self.session.execute(stmt).scalars().all()
        return [_map_customer_orm_to_model(cust_orm) for cust_orm in results]

    def update(self, customer: Customer) -> Customer:
        if not customer.id:
            raise ValueError("Cannot update customer without an ID.")

        cust_orm = self.session.get(CustomerOrm, customer.id)
        if not cust_orm:
            return None  # Return None instead of raising an exception

        # Update attributes from the domain model
        cust_orm.name = customer.name
        cust_orm.phone = customer.phone
        cust_orm.email = customer.email
        cust_orm.address = customer.address
        cust_orm.cuit = customer.cuit
        cust_orm.iva_condition = customer.iva_condition
        cust_orm.credit_limit = customer.credit_limit
        cust_orm.credit_balance = customer.credit_balance  # Include credit_balance update
        cust_orm.is_active = customer.is_active

        try:
            self.session.flush()
            self.session.refresh(cust_orm)
            return _map_customer_orm_to_model(cust_orm)
        except IntegrityError as e:
            # Removed self.session.rollback() - let the caller's session_scope handle it
            raise ValueError(f"Error updating customer {customer.id}: Possible duplicate data (e.g., CUIT). {e}")

    def delete(self, customer_id: int) -> bool:
        # Check if exists first
        cust_orm = self.session.get(CustomerOrm, customer_id)
        if not cust_orm:
            return False # Return False if not found

        # Consider setting is_active=False instead of hard delete?
        # For now, perform hard delete
        self.session.delete(cust_orm)
        self.session.flush()
        return True # Successfully deleted

    def search(self, filters: Optional[Dict[str, Any]] = None, sort_by: Optional[str] = None, 
               limit: Optional[int] = None, offset: Optional[int] = None, 
               search_term: Optional[str] = None, iva_condition: Optional[str] = None,
               is_active: Optional[bool] = None, sort_order: Optional[str] = None) -> List[Customer]:
        """Search customers with filtering, sorting, and pagination."""
        stmt = select(CustomerOrm)
        
        # Handle search term parameter (for backward compatibility)
        if search_term is not None:
            search_pattern = f"%{search_term.lower()}%"
            stmt = stmt.where(func.lower(CustomerOrm.name).like(search_pattern))
            
        # Handle IVA condition filtering (for backward compatibility)
        if iva_condition is not None:
            stmt = stmt.where(CustomerOrm.iva_condition == iva_condition)
        
        # Handle is_active parameter (for backward compatibility)
        if is_active is not None:
            stmt = stmt.where(CustomerOrm.is_active == is_active)
            
        # Apply filters
        if filters:
            for field, value in filters.items():
                stmt = stmt.where(getattr(CustomerOrm, field) == value)
                
        # Apply sorting - check for combined field_direction format first
        if sort_by:
            if sort_by.endswith('_asc') or sort_by.endswith('_desc'):
                parts = sort_by.rsplit('_', 1)
                if len(parts) == 2:
                    field_name, direction = parts
                    column = getattr(CustomerOrm, field_name, None)
                    if column is not None:
                        if direction.lower() == 'asc':
                            stmt = stmt.order_by(column.asc())
                        elif direction.lower() == 'desc':
                            stmt = stmt.order_by(column.desc())
            # Handle separate sort_by and sort_order parameters
            elif sort_order:
                column = getattr(CustomerOrm, sort_by, None)
                if column is not None:
                    if sort_order.lower() == 'asc':
                        stmt = stmt.order_by(column.asc())
                    elif sort_order.lower() == 'desc':
                        stmt = stmt.order_by(column.desc())
            else:
                # Default to ascending if no direction specified
                column = getattr(CustomerOrm, sort_by, None)
                if column is not None:
                    stmt = stmt.order_by(column.asc())
        else:
            # Default order by name
            stmt = stmt.order_by(CustomerOrm.name)
            
        # Apply pagination
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)
            
        results = self.session.execute(stmt).scalars().all()
        return [_map_customer_orm_to_model(cust_orm) for cust_orm in results]

    def search_by_name(self, name: str) -> List[Customer]:
        """Search customers by name (case-insensitive, partial match)."""
        search_pattern = f"%{name.lower()}%"
        stmt = select(CustomerOrm).where(
            CustomerOrm.is_active == True,
            func.lower(CustomerOrm.name).like(search_pattern)
        ).order_by(CustomerOrm.name)
        results = self.session.execute(stmt).scalars().all()
        return [_map_customer_orm_to_model(cust_orm) for cust_orm in results]

    def get_by_cuit(self, cuit: str) -> Optional[Customer]:
        if not cuit: return None
        stmt = select(CustomerOrm).where(CustomerOrm.cuit == cuit)
        cust_orm = self.session.execute(stmt).scalar_one_or_none()
        return _map_customer_orm_to_model(cust_orm)

    def update_balance(self, customer_id: int, new_balance: float) -> bool:
        """
        Update the credit balance of a customer.
        
        Note: This operation deals with financial data but uses float.
        While this matches the ORM schema, consider ensuring precision by using
        Decimal for all calculations and only convert to float at the database boundary.
        """
        cust_orm = self.session.get(CustomerOrm, customer_id)
        if not cust_orm:
            return False
        cust_orm.credit_balance = new_balance
        self.session.commit()
        return True

# --- Credit Payment Repository Implementation ---
class SqliteCreditPaymentRepository(ICreditPaymentRepository):
    """SQLite implementation of the Credit Payment repository."""
    
    def __init__(self, session: Session):
        """Initialize with a database session.
        
        Args:
            session: The SQLAlchemy session to use
        """
        self.session = session
    
    def add(self, payment: CreditPayment) -> CreditPayment:
        """Add a new credit payment record."""
        # Create ORM object from the model
        payment_orm = CreditPaymentOrm(
            customer_id=payment.customer_id,
            amount=float(payment.amount),  # Convert Decimal to float
            timestamp=payment.timestamp or datetime.now(),
            notes=payment.notes,
            user_id=payment.user_id
        )
        
        # Add to session
        self.session.add(payment_orm)
        self.session.flush()  # Get ID immediately
        self.session.refresh(payment_orm)  # Refresh to populate the auto-generated integer ID
        
        # Return the mapped model
        return _map_credit_payment_orm_to_model(payment_orm)
    
    def get_by_id(self, payment_id: int) -> Optional[CreditPayment]:
        """Get a credit payment by its ID."""
        payment_orm = self.session.query(CreditPaymentOrm).filter_by(id=payment_id).first()
        return _map_credit_payment_orm_to_model(payment_orm)
    
    def get_for_customer(self, customer_id: int) -> List[CreditPayment]:
        """Get all credit payments for a customer."""
        payments = self.session.query(CreditPaymentOrm).filter_by(customer_id=customer_id).order_by(CreditPaymentOrm.timestamp.desc()).all()
        return [_map_credit_payment_orm_to_model(p) for p in payments]

# --- Supplier Repository Implementation ---

class SqliteSupplierRepository(ISupplierRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, supplier: Supplier) -> Supplier:
        """Add a new supplier."""
        supplier_orm = SupplierOrm(
            name=supplier.name,
            contact_person=supplier.contact_person,
            phone=supplier.phone,
            email=supplier.email,
            address=supplier.address,
            cuit=supplier.cuit,
            notes=supplier.notes,
            is_active=supplier.is_active
        )
        
        try:
            self.session.add(supplier_orm)
            self.session.flush()
            
            # Set the new ID on the supplier object
            supplier.id = supplier_orm.id
            return supplier
        except IntegrityError as e:
            # Don't rollback here - transaction management is handled by session scope
            if "UNIQUE constraint failed: suppliers.name" in str(e):
                raise ValueError(f"Supplier name '{supplier.name}' already exists")
            elif "UNIQUE constraint failed: suppliers.cuit" in str(e):
                raise ValueError(f"Supplier with CUIT '{supplier.cuit}' already exists")
            raise ValueError(f"Error adding supplier: {e}")

    def get_by_id(self, supplier_id: int) -> Optional[Supplier]:
        supplier_orm = self.session.get(SupplierOrm, supplier_id)
        return _map_supplier_orm_to_model(supplier_orm)

    def get_by_name(self, name: str) -> Optional[Supplier]:
        stmt = select(SupplierOrm).where(func.lower(SupplierOrm.name) == func.lower(name))
        supplier_orm = self.session.scalar(stmt)
        return _map_supplier_orm_to_model(supplier_orm)

    def get_by_cuit(self, cuit: str) -> Optional[Supplier]:
        if not cuit: # Avoid searching empty string if cuit is optional
            return None
        stmt = select(SupplierOrm).where(SupplierOrm.cuit == cuit)
        supplier_orm = self.session.scalar(stmt)
        return _map_supplier_orm_to_model(supplier_orm)

    def get_all(self) -> List[Supplier]:
        stmt = select(SupplierOrm).order_by(SupplierOrm.name)
        suppliers_orm = self.session.scalars(stmt).all()
        return [_map_supplier_orm_to_model(s) for s in suppliers_orm]

    def update(self, supplier: Supplier) -> Optional[Supplier]:
        """Update an existing supplier."""
        if not supplier.id:
            raise ValueError("Supplier ID is required for update")
            
        supplier_orm = self.session.get(SupplierOrm, supplier.id)
        if not supplier_orm:
            return None
            
        supplier_orm.name = supplier.name
        supplier_orm.contact_person = supplier.contact_person
        supplier_orm.phone = supplier.phone
        supplier_orm.email = supplier.email
        supplier_orm.address = supplier.address
        supplier_orm.cuit = supplier.cuit
        supplier_orm.notes = supplier.notes
        supplier_orm.is_active = supplier.is_active
        
        try:
            self.session.flush()
            return supplier
        except IntegrityError as e:
            # Don't rollback here - transaction management is handled by session scope
            if "UNIQUE constraint failed: suppliers.name" in str(e):
                raise ValueError(f"Supplier name '{supplier.name}' already exists")
            elif "UNIQUE constraint failed: suppliers.cuit" in str(e):
                raise ValueError(f"Supplier with CUIT '{supplier.cuit}' already exists")
            raise ValueError(f"Error updating supplier: {e}")

    def delete(self, supplier_id: int) -> bool:
        # Check if supplier is used in Purchase Orders first? (Optional constraint)
        # po_stmt = select(func.count(PurchaseOrderOrm.id)).where(PurchaseOrderOrm.supplier_id == supplier_id)
        # if self.session.scalar(po_stmt) > 0:
        #     raise ValueError("Cannot delete supplier with existing purchase orders.")

        # Option 1: Use ORM-style delete (safer, preferred)
        supplier_orm = self.session.get(SupplierOrm, supplier_id)
        if not supplier_orm:
            return False
        
        self.session.delete(supplier_orm)
        self.session.flush()
        return True
        
        # Option 2: If using SQL delete, use the model class:
        # stmt = delete(SupplierOrm).where(SupplierOrm.id == supplier_id)
        # result = self.session.execute(stmt)
        # self.session.flush()
        # return result.rowcount == 1

    def search(self, query: str) -> List[Supplier]:
        search_term = f"%{query.lower()}%"
        stmt = select(SupplierOrm).where(
            or_(
                func.lower(SupplierOrm.name).like(search_term),
                func.lower(SupplierOrm.contact_person).like(search_term), # Use correct field name
                func.lower(SupplierOrm.cuit).like(search_term),
                func.lower(SupplierOrm.phone).like(search_term),
                func.lower(SupplierOrm.email).like(search_term)
            )
        ).order_by(SupplierOrm.name)
        suppliers_orm = self.session.scalars(stmt).all()
        return [_map_supplier_orm_to_model(s) for s in suppliers_orm]

# --- Purchase Order Repository Implementation ---

class SqlitePurchaseOrderRepository(IPurchaseOrderRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, purchase_order: PurchaseOrder) -> PurchaseOrder:
        # Map PurchaseOrder core model to ORM
        po_orm = PurchaseOrderOrm(
            supplier_id=purchase_order.supplier_id,
            order_date=purchase_order.date, # Correct keyword for ORM model
            expected_delivery_date=purchase_order.expected_delivery_date,
            status=purchase_order.status,
            notes=purchase_order.notes
            # created_at/updated_at have defaults
        )

        # Map PurchaseOrderItem core models to ORM
        item_orms = []
        for item_core in purchase_order.items:
            item_orm = PurchaseOrderItemOrm(
                product_id=item_core.product_id,
                product_code=item_core.product_code, # Assumes service provides this
                product_description=item_core.product_description, # Assumes service provides this
                quantity_ordered=item_core.quantity, # Correct keyword for ORM
                cost_price=item_core.unit_price, # Use unit_price from core model
                quantity_received=item_core.quantity_received
            )
            item_orms.append(item_orm)

        # Associate items with the order
        po_orm.items = item_orms

        try:
            self.session.add(po_orm)
            self.session.flush() # Assigns ID to po_orm and item_orms
            self.session.refresh(po_orm) # Refresh to load relationships if needed by mapping
            # Eager load supplier and items for the returned object mapping
            stmt = select(PurchaseOrderOrm).options(
                joinedload(PurchaseOrderOrm.supplier),
                joinedload(PurchaseOrderOrm.items) # Ensure items are loaded for mapping
            ).where(PurchaseOrderOrm.id == po_orm.id)
            refreshed_po_orm = self.session.scalar(stmt)
            return _map_purchase_order_orm_to_model(refreshed_po_orm) # Correct indentation
        except IntegrityError as e: # Add except block
            # Don't rollback here - transaction management is handled by session scope
            raise ValueError(f"Error adding purchase order: {e}")

    # Methods belonging to SqlitePurchaseOrderRepository (Moved inside the class)
    def get_by_id(self, po_id: int) -> Optional[PurchaseOrder]:
        stmt = (
            select(PurchaseOrderOrm)
            .options(
                joinedload(PurchaseOrderOrm.supplier),
                joinedload(PurchaseOrderOrm.items)
            )
            .where(PurchaseOrderOrm.id == po_id)
        )
        po_orm = self.session.scalar(stmt)
        return _map_purchase_order_orm_to_model(po_orm)

    def get_all(self, status: str | None = None, supplier_id: int | None = None) -> List[PurchaseOrder]:
        stmt = select(PurchaseOrderOrm).options(
            joinedload(PurchaseOrderOrm.supplier) # Load supplier for mapping
            # Items are NOT loaded here by default for performance in lists
        ).order_by(PurchaseOrderOrm.order_date.desc())

        if status:
            stmt = stmt.where(PurchaseOrderOrm.status == status)
        if supplier_id:
            stmt = stmt.where(PurchaseOrderOrm.supplier_id == supplier_id)

        pos_orm = self.session.scalars(stmt).all()
        return [_map_purchase_order_orm_to_model(po) for po in pos_orm]

    def update_status(self, po_id: int, status: str) -> bool:
        """Update the status of a purchase order."""
        stmt = update(PurchaseOrderOrm).where(PurchaseOrderOrm.id == po_id).values(
            status=status,
            updated_at=datetime.now()
        )
        self.session.execute(stmt)
        self.session.flush()
        return True

    def update_item_received_quantity(self, item_id: int, quantity_received: float) -> bool:
        """
        Update the quantity_received for a purchase order item.
        
        Args:
            item_id: The ID of the purchase order item
            quantity_received: The additional quantity received (will be added to current value)
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Get current item to ensure it exists and to calculate new quantity
        item_orm = self.session.get(PurchaseOrderItemOrm, item_id)
        if not item_orm:
            return False
            
        # Update with the new quantity_received (adding to existing value)
        new_qty = item_orm.quantity_received + quantity_received
        stmt = update(PurchaseOrderItemOrm).where(PurchaseOrderItemOrm.id == item_id).values(
            quantity_received=new_qty
        )
        self.session.execute(stmt)
        self.session.flush()
        return True

    def get_items(self, po_id: int) -> List[PurchaseOrderItem]:
        """Get the items for a purchase order."""
        po_orm = self.get_po_orm_by_id(po_id)
        if not po_orm:
            return []
        return [_map_purchase_order_item_orm_to_model(item) for item in po_orm.items]

# --- User Repository Implementation ---

class SqliteUserRepository(IUserRepository):
    """SQLite implementation of the user repository."""

    def __init__(self, session):
        self._session = session

    def add(self, user: User) -> User:
        """Add a new user to the repository."""
        try:
            # Check for existing username
            existing = self._session.query(UserOrm).filter(UserOrm.username == user.username).first()
            if existing:
                raise ValueError(f"Username '{user.username}' already exists")

            # Hash the password with bcrypt if it's the 'password' attribute
            import bcrypt
            password_hash = None
            
            # Get the password from the user object (from the password attribute, not password_hash)
            if hasattr(user, 'password') and user.password:
                # Hash the plain password
                password = user.password
                password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                password_hash = password_hash.decode('utf-8')  # Convert bytes to string for storage
            elif user.password_hash:
                # If already hashed, use as-is
                password_hash = user.password_hash
            else:
                raise ValueError("User must have either 'password' or 'password_hash' set")

            # Create new user ORM object with the generated hash
            user_orm = UserOrm(
                username=user.username,
                password_hash=password_hash,  # Use the generated hash
                is_active=user.is_active,
                email=user.email,
                is_admin=user.is_admin
            )
            
            # Add to session and get ID
            self._session.add(user_orm)
            self._session.flush()  # Get ID without committing transaction

            # Update domain object with new ID and hashed password
            user.id = user_orm.id
            user.password_hash = password_hash  # Update the domain model with the hash
            
            return user
        except Exception as e:
            # Don't rollback here, let the session_scope handle it
            if isinstance(e, ValueError):
                raise  # Re-raise our custom error
            raise ValueError(f"Error adding user: {e}")

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        try:
            user_orm = self._session.query(UserOrm).filter(UserOrm.id == user_id).first()
            return _map_user_orm_to_model(user_orm)
        except Exception as e:
            # Log the error but don't rollback
            print(f"Error getting user by ID: {e}")
            return None

    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        try:
            user_orm = self._session.query(UserOrm).filter(UserOrm.username == username).first()
            return _map_user_orm_to_model(user_orm)
        except Exception as e:
            # Log the error but don't rollback
            print(f"Error getting user by username: {e}")
            return None

    def update(self, user: User) -> Optional[User]:
        """Update an existing user."""
        try:
            user_orm = self._session.query(UserOrm).filter(UserOrm.id == user.id).first()
            if not user_orm:
                raise ValueError(f"User with ID {user.id} not found for update.")

            # Update fields - be careful about password hash updates
            user_orm.username = user.username
            if user.password_hash: # Only update hash if a new one is provided
                user_orm.password_hash = user.password_hash
            user_orm.is_active = user.is_active
            user_orm.email = user.email
            user_orm.is_admin = user.is_admin

            self._session.flush()
            return _map_user_orm_to_model(user_orm)
        except IntegrityError as e:
            self._session.rollback()
            raise ValueError(f"Error updating user {user.id}: Username '{user.username}' may already exist. {e}")
        except Exception as e:
            self._session.rollback()
            raise ValueError(f"Error updating user: {e}")

    def delete(self, user_id: int) -> bool:
        """Delete user by ID."""
        try:
            user_orm = self._session.query(UserOrm).filter(UserOrm.id == user_id).first()
            if not user_orm:
                return False
                
            self._session.delete(user_orm)
            self._session.flush()
            return True
        except Exception as e:
            # Don't rollback here
            raise ValueError(f"Error deleting user: {e}")

    def get_all(self) -> List[User]:
        """Get all users."""
        try:
            users_orm = self._session.query(UserOrm).order_by(UserOrm.username).all()
            return [_map_user_orm_to_model(u) for u in users_orm]
        except Exception as e:
            # Don't rollback here
            raise ValueError(f"Error getting all users: {e}")

# --- Invoice Repository Implementation ---
class SqliteInvoiceRepository(IInvoiceRepository):
    """SQLite implementation of the invoice repository interface."""
    
    def __init__(self, session: Session):
        """Initialize with a SQLAlchemy session."""
        self.session = session
    
    def add(self, invoice: Invoice) -> Invoice:
        """Adds a new invoice to the repository."""
        # Check for duplicate sale_id
        existing = self.get_by_sale_id(invoice.sale_id)
        if existing:
            raise ValueError(f"Invoice for sale ID {invoice.sale_id} already exists")
        
        # Map domain model to ORM
        invoice_orm = _map_invoice_model_to_orm(invoice)
        
        # Add to session
        self.session.add(invoice_orm)
        self.session.flush()  # Flush to get the ID
        
        # Set the ID and return the domain model
        invoice.id = invoice_orm.id
        return invoice
    
    def get_by_id(self, invoice_id: int) -> Optional[Invoice]:
        """Retrieves an invoice by its unique ID."""
        invoice_orm = self.session.query(InvoiceOrm).filter(InvoiceOrm.id == invoice_id).first()
        return _map_invoice_orm_to_model(invoice_orm)
    
    def get_by_sale_id(self, sale_id: int) -> Optional[Invoice]:
        """Retrieves an invoice by its associated sale ID."""
        invoice_orm = self.session.query(InvoiceOrm).filter(InvoiceOrm.sale_id == sale_id).first()
        return _map_invoice_orm_to_model(invoice_orm)
    
    def get_all(self) -> List[Invoice]:
        """Retrieves all invoices."""
        invoice_orms = self.session.query(InvoiceOrm).all()
        return [_map_invoice_orm_to_model(orm) for orm in invoice_orms]

    def delete(self, invoice_id: int) -> bool:
        """Deletes an invoice by its ID."""
        invoice_orm = self.session.get(InvoiceOrm, invoice_id)
        if not invoice_orm:
            return False
        
        self.session.delete(invoice_orm)
        self.session.flush()
        return True

# --- Cash Drawer Repository Implementation ---
class SqliteCashDrawerRepository(ICashDrawerRepository):
    """SQLite implementation of the Cash Drawer Repository interface."""
    
    def __init__(self, session: Session):
        """Initialize with a SQLAlchemy session."""
        self.session = session
        
    def _orm_to_model(self, orm_entry: CashDrawerEntryOrm) -> CashDrawerEntry:
        """Convert ORM object to domain model."""
        if not orm_entry:
            return None
            
        entry = CashDrawerEntry(
            id=orm_entry.id,
            timestamp=orm_entry.timestamp,
            # Handle potential string enum value from DB
            entry_type=CashDrawerEntryType(orm_entry.entry_type) if isinstance(orm_entry.entry_type, str) else orm_entry.entry_type, 
            amount=Decimal(str(orm_entry.amount)), # Convert potentially imprecise float back to Decimal
            description=orm_entry.description,
            user_id=orm_entry.user_id,
            drawer_id=orm_entry.drawer_id
        )
        return entry
        
    def _model_to_orm(self, model_entry: CashDrawerEntry) -> CashDrawerEntryOrm:
        """Convert domain model to ORM object."""
        orm_entry = CashDrawerEntryOrm()
        orm_entry.timestamp = model_entry.timestamp
        orm_entry.entry_type = model_entry.entry_type.value # Store enum value as string
        orm_entry.amount = float(model_entry.amount) # Store as float now
        orm_entry.description = model_entry.description
        orm_entry.user_id = model_entry.user_id
        orm_entry.drawer_id = model_entry.drawer_id
        return orm_entry
        
    def add_entry(self, entry: CashDrawerEntry) -> CashDrawerEntry:
        """Add a new cash drawer entry."""
        try:
            db_entry = self._model_to_orm(entry)
            self.session.add(db_entry)
            self.session.flush()
            entry.id = db_entry.id
            return entry
        except Exception as e:
            raise ValueError(f"Error adding cash drawer entry: {e}")
        
    def get_entries_by_date_range(self, start_date: datetime, end_date: datetime) -> List[CashDrawerEntry]:
        """Get all cash drawer entries within a date range."""
        stmt = (
            select(CashDrawerEntryOrm)
            .where(CashDrawerEntryOrm.timestamp >= start_date)
            .where(CashDrawerEntryOrm.timestamp <= end_date)
            .order_by(CashDrawerEntryOrm.timestamp)
        )
        orm_entries = self.session.scalars(stmt).all()
        return [self._orm_to_model(orm_entry) for orm_entry in orm_entries]
        
        
    def get_entries_by_type(self, entry_type: str, start_date: Optional[datetime] = None, 
                            end_date: Optional[datetime] = None) -> List[CashDrawerEntry]:
        """Get cash drawer entries by type within an optional date range."""
        # Determine the actual string value to use for the query
        actual_value_to_query: Optional[str] = None
        if isinstance(entry_type, CashDrawerEntryType):
            actual_value_to_query = entry_type.value
        elif isinstance(entry_type, str):
            # Validate if the string is a valid CashDrawerEntryType value
            try:
                actual_value_to_query = CashDrawerEntryType(entry_type).value # Ensures it's a valid key and gets the value
            except ValueError:
                # Log or handle invalid string entry_type
                logging.warning(f"Invalid string value for CashDrawerEntryType: {entry_type} in get_entries_by_type")
                return []
        else:
            # Log or handle unsupported type for entry_type
            logging.error(f"Unsupported type for entry_type: {type(entry_type)} in get_entries_by_type")
            return []

        if actual_value_to_query is None: # Should not happen if logic above is correct
            return []

        # Start building the query
        query = self.session.query(CashDrawerEntryOrm).filter(
            CashDrawerEntryOrm.entry_type == actual_value_to_query
        )
        
        # Add date range filters if provided
        if start_date:
            query = query.filter(CashDrawerEntryOrm.timestamp >= start_date)
        if end_date:
            query = query.filter(CashDrawerEntryOrm.timestamp <= end_date)
            
        # Execute query and convert results
        orm_entries = query.order_by(CashDrawerEntryOrm.timestamp).all()
        return [self._orm_to_model(orm_entry) for orm_entry in orm_entries]
        
    def get_last_start_entry(self, drawer_id: Optional[int] = None) -> Optional[CashDrawerEntry]:
        """Get the most recent START entry for a drawer."""
        # Build query for START entries
        query = (self.session.query(CashDrawerEntryOrm)
                .filter(CashDrawerEntryOrm.entry_type == CashDrawerEntryType.START.value)) # Use .value here
                
        # Add drawer filter if provided
        if drawer_id is not None:
            query = query.filter(CashDrawerEntryOrm.drawer_id == drawer_id)
            
        # Get the most recent entry
        orm_entry = query.order_by(desc(CashDrawerEntryOrm.timestamp)).first()
        
        # Convert to domain model if found
        return self._orm_to_model(orm_entry) if orm_entry else None
        
    def get_entry_by_id(self, entry_id: int) -> Optional[CashDrawerEntry]:
        """Get a cash drawer entry by ID."""
        orm_entry = self.session.query(CashDrawerEntryOrm).filter(CashDrawerEntryOrm.id == entry_id).first()
        return self._orm_to_model(orm_entry) if orm_entry else None
