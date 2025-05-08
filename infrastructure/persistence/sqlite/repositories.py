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
from core.models.credit_payment import CreditPayment
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

from infrastructure.persistence.sqlite.cash_drawer_repository import SQLiteCashDrawerRepository

import bcrypt

# --- Helper Function for ORM to Domain Model Mapping ---

def _map_department_orm_to_model(dept_orm: "DepartmentOrm") -> Optional[Department]:
    """Maps the DepartmentOrm object to the Department domain model."""
    if not dept_orm:
        return None
    # Department Pydantic model has id, name, description
    return Department(
        id=dept_orm.id,
        name=dept_orm.name,
        description=getattr(dept_orm, 'description', None) # Assuming description might not exist in older ORM versions
    )

# --- Helper Function for Product ORM to Domain Model Mapping ---

def _map_product_orm_to_model(prod_orm: "ProductOrm") -> Optional[Product]:
    """Maps the ProductOrm object to the Product domain model."""
    if not prod_orm:
        return None
    # Map the related DepartmentOrm to Department model if it exists
    department_model = _map_department_orm_to_model(prod_orm.department) if prod_orm.department else None

    # Numeric fields from ORM map directly to Decimal fields in Pydantic model
    return Product(
        id=prod_orm.id,
        code=prod_orm.code,
        description=prod_orm.description,
        cost_price=prod_orm.cost_price, # Numeric -> Decimal
        sell_price=prod_orm.sell_price, # Numeric -> Decimal
        wholesale_price=prod_orm.wholesale_price, # Numeric -> Decimal
        special_price=prod_orm.special_price, # Numeric -> Decimal
        department_id=prod_orm.department_id,
        department=department_model, # Assign the mapped Department model
        unit=prod_orm.unit,
        uses_inventory=prod_orm.uses_inventory,
        quantity_in_stock=prod_orm.quantity_in_stock, # Numeric -> Decimal
        min_stock=prod_orm.min_stock, # Numeric -> Decimal
        max_stock=prod_orm.max_stock, # Numeric -> Decimal
        last_updated=prod_orm.last_updated,
        notes=prod_orm.notes,
        is_active=prod_orm.is_active
    )

# --- Helper Function for Inventory Movement ORM to Domain Model Mapping ---

def _map_movement_orm_to_model(move_orm: "InventoryMovementOrm") -> Optional[InventoryMovement]:
    """Maps the InventoryMovementOrm object to the InventoryMovement domain model."""
    if not move_orm:
        return None
    return InventoryMovement(
        id=move_orm.id,
        product_id=move_orm.product_id,
        user_id=move_orm.user_id,
        timestamp=move_orm.timestamp,
        movement_type=move_orm.movement_type,
        quantity=move_orm.quantity, # Numeric -> Decimal
        description=move_orm.description,
        related_id=move_orm.related_id
    )

# --- Helper Functions for Sale ORM to Domain Model Mapping ---

def _map_sale_item_orm_to_model(item_orm: "SaleItemOrm") -> Optional[SaleItem]:
    """
    Maps the SaleItemOrm object to the SaleItem domain model.
    Numeric types map to Decimal.
    """
    if not item_orm:
        return None
    return SaleItem(
        id=item_orm.id,
        sale_id=item_orm.sale_id,
        product_id=item_orm.product_id,
        quantity=item_orm.quantity, # Numeric -> Decimal
        unit_price=item_orm.unit_price, # Numeric -> Decimal
        product_code=item_orm.product_code,
        product_description=item_orm.product_description
    )

def _map_sale_orm_to_model(sale_orm: "SaleOrm") -> Optional[Sale]:
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
        # total is a calculated property in Sale domain model
    )

# --- Helper Function for Customer ORM to Domain Model Mapping ---

def _map_customer_orm_to_model(cust_orm: "CustomerOrm") -> Optional[Customer]:
    """Maps the CustomerOrm object to the Customer domain model."""
    if not cust_orm:
        return None
    return Customer(
        id=cust_orm.id, # UUID
        name=cust_orm.name,
        phone=cust_orm.phone,
        email=cust_orm.email,
        address=cust_orm.address,
        cuit=cust_orm.cuit,
        iva_condition=cust_orm.iva_condition,
        credit_limit=cust_orm.credit_limit, # Numeric -> Decimal/float (check Customer model)
        credit_balance=cust_orm.credit_balance, # Numeric -> Decimal/float (check Customer model)
        is_active=cust_orm.is_active
    )

# --- Helper Function for CreditPayment ORM to Domain Model Mapping ---

def _map_credit_payment_orm_to_model(payment_orm: "CreditPaymentOrm") -> Optional[CreditPayment]:
    """
    Maps the CreditPaymentOrm object to the CreditPayment domain model.
    Numeric maps to Decimal.
    """
    if not payment_orm:
        return None
    return CreditPayment(
        id=payment_orm.id,
        customer_id=payment_orm.customer_id, # UUID
        amount=payment_orm.amount, # Numeric -> Decimal
        payment_date=payment_orm.timestamp, # Map timestamp to payment_date
        description=payment_orm.notes, # Map notes to description
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
        notes=supplier_orm.notes,
        is_active=getattr(supplier_orm, 'is_active', True) # Handle potential missing field
    )

def _map_purchase_order_item_orm_to_model(item_orm: "PurchaseOrderItemOrm") -> Optional[PurchaseOrderItem]:
    """Maps the PurchaseOrderItemOrm object to the PurchaseOrderItem domain model."""
    if not item_orm:
        return None
    return PurchaseOrderItem(
        id=item_orm.id,
        # order_id is not part of the domain model constructor, inferred from list context
        product_id=item_orm.product_id,
        product_code=item_orm.product_code,
        product_description=item_orm.product_description,
        quantity_ordered=item_orm.quantity_ordered, # Numeric -> Decimal
        unit_price=item_orm.cost_price, # Map cost_price ORM to unit_price domain
        quantity_received=item_orm.quantity_received # Numeric -> Decimal
    )

def _map_purchase_order_orm_to_model(po_orm: "PurchaseOrderOrm") -> Optional[PurchaseOrder]:
    """Maps the PurchaseOrderOrm object to the PurchaseOrder domain model."""
    if not po_orm:
        return None

    # Map related items
    items_model = [_map_purchase_order_item_orm_to_model(item) for item in po_orm.items] if po_orm.items else []
    # Supplier object is not directly in the domain model, only supplier_id

    return PurchaseOrder(
        id=po_orm.id,
        supplier_id=po_orm.supplier_id,
        order_date=po_orm.order_date,
        expected_delivery_date=po_orm.expected_delivery_date,
        status=po_orm.status,
        notes=po_orm.notes,
        items=items_model,
        # created_at / updated_at are not in the domain model
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
        email=user_orm.email, # Added email
        is_active=user_orm.is_active,
        is_admin=user_orm.is_admin # Added is_admin
    )

# --- Helper Function for Invoice ORM to Domain Model Mapping ---

def _map_invoice_orm_to_model(invoice_orm: "InvoiceOrm") -> Optional[Invoice]:
    """Maps the InvoiceOrm object to the Invoice domain model."""
    if not invoice_orm:
        return None

    # Deserialize customer_details if it's stored as JSON string
    customer_details_dict = {}
    if invoice_orm.customer_details:
        try:
            customer_details_dict = json.loads(invoice_orm.customer_details)
        except json.JSONDecodeError:
            logging.warning(f"Could not decode customer_details JSON for invoice {invoice_orm.id}")
            customer_details_dict = {} # Default to empty dict on error

    return Invoice(
        id=invoice_orm.id,
        sale_id=invoice_orm.sale_id,
        customer_id=invoice_orm.customer_id,
        invoice_number=invoice_orm.invoice_number,
        invoice_date=invoice_orm.invoice_date,
        invoice_type=invoice_orm.invoice_type,
        customer_details=customer_details_dict,
        subtotal=invoice_orm.subtotal, # Numeric -> Decimal
        iva_amount=invoice_orm.iva_amount, # Numeric -> Decimal
        total=invoice_orm.total, # Numeric -> Decimal
        iva_condition=invoice_orm.iva_condition,
        cae=invoice_orm.cae,
        cae_due_date=invoice_orm.cae_due_date,
        notes=invoice_orm.notes,
        is_active=invoice_orm.is_active
    )

# --- Helper Function for mapping Domain Invoice to ORM --- 
# (Useful for add/update methods)

def _map_invoice_model_to_orm(invoice: Invoice, invoice_orm: Optional["InvoiceOrm"] = None) -> "InvoiceOrm":
    """Maps the Invoice domain model object to an InvoiceOrm object."""
    if not invoice_orm: 
        invoice_orm = InvoiceOrm() # Create new ORM instance if not updating

    # Assign attributes from domain model to ORM model
    # ID is usually handled by DB or not set on creation
    invoice_orm.sale_id = invoice.sale_id
    invoice_orm.customer_id = invoice.customer_id
    invoice_orm.invoice_number = invoice.invoice_number
    invoice_orm.invoice_date = invoice.invoice_date
    invoice_orm.invoice_type = invoice.invoice_type
    
    # Serialize customer_details dictionary to JSON string
    try:
        invoice_orm.customer_details = json.dumps(invoice.customer_details)
    except TypeError:
        logging.warning(f"Could not serialize customer_details for invoice related to sale {invoice.sale_id}")
        invoice_orm.customer_details = "{}" # Default to empty JSON object
        
    invoice_orm.subtotal = invoice.subtotal
    invoice_orm.iva_amount = invoice.iva_amount
    invoice_orm.total = invoice.total
    invoice_orm.iva_condition = invoice.iva_condition
    invoice_orm.cae = invoice.cae
    invoice_orm.cae_due_date = invoice.cae_due_date
    invoice_orm.notes = invoice.notes
    invoice_orm.is_active = invoice.is_active

    return invoice_orm

# --- Repository Implementation ---

class SqliteDepartmentRepository(IDepartmentRepository):
    """SQLite implementation of the department repository interface."""

    def __init__(self, session: Session):
        """Initializes the repository with a database session."""
        if not isinstance(session, Session):
            raise TypeError("Session must be a SQLAlchemy Session object")
        self.session = session

    def add(self, department: Department) -> Department:
        """Adds a new department to the database."""
        # Check for existing name
        existing = self.get_by_name(department.name)
        if existing:
            raise ValueError(f"Department name '{department.name}' already exists.")
            
        try:
            # Map domain model to ORM model
            department_orm = DepartmentOrm(
                name=department.name,
                # description=department.description # Add if description is in ORM
            )
            # Add ORM model to session
            self.session.add(department_orm)
            self.session.flush() # Flush to get the ID assigned by the database
            self.session.refresh(department_orm)
            # Map the ORM model (with ID) back to domain model and return
            return _map_department_orm_to_model(department_orm)
        except IntegrityError as e:
            self.session.rollback()
            # Log error or handle specific constraint violations
            logging.error(f"Database integrity error adding department: {e}")
            raise ValueError(f"Could not add department: {e}")
        except Exception as e:
            self.session.rollback()
            logging.error(f"Unexpected error adding department: {e}")
            raise

    def get_by_id(self, department_id: int) -> Optional[Department]: # Changed type hint to int
        """Retrieves a department by its ID."""
        department_orm = self.session.get(DepartmentOrm, department_id)
        return _map_department_orm_to_model(department_orm)

    def get_by_name(self, name: str) -> Optional[Department]:
        """Retrieves a department by its name."""
        stmt = select(DepartmentOrm).where(DepartmentOrm.name == name)
        department_orm = self.session.scalars(stmt).first()
        return _map_department_orm_to_model(department_orm)

    def get_all(self) -> List[Department]:
        """Retrieves all departments, ordered by name."""
        stmt = select(DepartmentOrm).order_by(DepartmentOrm.name)
        results_orm = self.session.scalars(stmt).all()
        return [_map_department_orm_to_model(dept) for dept in results_orm]

    def update(self, department: Department) -> Department:
        """Updates an existing department."""
        if department.id is None:
            raise ValueError("Department ID is required for update.")
            
        # Check for name collision if name is being changed
        existing_by_name = self.get_by_name(department.name)
        if existing_by_name and existing_by_name.id != department.id:
            raise ValueError(f"Another department with name '{department.name}' already exists.")

        department_orm = self.session.get(DepartmentOrm, department.id)
        if not department_orm:
            raise ValueError(f"Department with ID {department.id} not found.")
            
        try:
            # Update ORM attributes from domain model
            department_orm.name = department.name
            # department_orm.description = department.description # Add if description is in ORM
            
            self.session.flush()
            self.session.refresh(department_orm)
            return _map_department_orm_to_model(department_orm)
        except IntegrityError as e:
            self.session.rollback()
            logging.error(f"Database integrity error updating department {department.id}: {e}")
            raise ValueError(f"Could not update department: {e}")
        except Exception as e:
            self.session.rollback()
            logging.error(f"Unexpected error updating department {department.id}: {e}")
            raise

    def delete(self, department_id: int) -> bool: # Changed type hint to int
        """Deletes a department by its ID."""
        department_orm = self.session.get(DepartmentOrm, department_id)
        if not department_orm:
            raise ValueError(f"Department with ID {department_id} not found")
        
        try:
            # Check if department is used by products (optional constraint)
            product_count = self.session.scalar(
                select(func.count(ProductOrm.id)).where(ProductOrm.department_id == department_id)
            )
            if product_count > 0:
                raise ValueError(f"Departamento {department_id} no puede ser eliminado, está en uso por {product_count} productos.")
            
            self.session.delete(department_orm)
            self.session.flush()
            return True
        except IntegrityError as e:
            self.session.rollback()
            # This might happen if there's a DB-level constraint not checked above
            logging.error(f"Integrity error deleting department {department_id}: {e}")
            raise ValueError(f"Cannot delete department. It might be in use.")
        except Exception as e:
            self.session.rollback()
            logging.error(f"Unexpected error deleting department {department_id}: {e}")
            raise

# Add other repository implementations (e.g., SqliteProductRepository) below

# --- Product Repository Implementation ---

class SqliteProductRepository(IProductRepository):
    """SQLite implementation of the product repository interface."""

    def __init__(self, session: Session):
        self.session = session

    def _create_product_orm(self, product: Product) -> ProductOrm:
        """Helper to map Product domain model to ProductOrm."""
        # Ensure department exists if ID is provided
        if product.department_id and not self.session.get(DepartmentOrm, product.department_id):
             raise ValueError(f"Department with ID {product.department_id} not found.")

        # Get all data from the product model
        data = product.model_dump(exclude={'id', 'department'}) # Use model_dump for Pydantic v2+
        
        # Filter out fields that don't exist in the ProductOrm model
        # Only include fields that are in the ProductOrm model
        orm_fields = {
            'code', 'description', 'cost_price', 'sell_price', 'wholesale_price', 
            'special_price', 'department_id', 'unit', 'uses_inventory', 
            'quantity_in_stock', 'min_stock', 'max_stock', 'last_updated', 
            'notes', 'is_active'
        }
        
        # Filter the data to only include fields that exist in the ORM
        orm_data = {k: v for k, v in data.items() if k in orm_fields}
        
        return ProductOrm(**orm_data)

    def add(self, product: Product) -> Product:
        """Adds a new product to the database."""
        # Check for existing code
        existing = self.get_by_code(product.code)
        if existing:
            raise ValueError(f"Product code '{product.code}' already exists.")
            
        try:
            product_orm = self._create_product_orm(product)
            self.session.add(product_orm)
            self.session.flush()
            self.session.refresh(product_orm, attribute_names=['id', 'department']) # Refresh to get ID and potentially loaded department
            return _map_product_orm_to_model(product_orm)
        except IntegrityError as e:
            self.session.rollback()
            logging.error(f"Database integrity error adding product: {e}")
            raise ValueError(f"Could not add product: {e}")
        except Exception as e:
            self.session.rollback()
            logging.error(f"Unexpected error adding product: {e}")
            raise

    def get_by_id(self, product_id: int) -> Optional[Product]: # ID is int
        """Retrieves a product by its ID, eagerly loading the department."""
        # Use joinedload to eager load department
        stmt = select(ProductOrm).options(joinedload(ProductOrm.department)).where(ProductOrm.id == product_id)
        product_orm = self.session.scalars(stmt).first()
        return _map_product_orm_to_model(product_orm)

    def get_by_code(self, code: str) -> Optional[Product]:
        """Retrieves a product by its code, eagerly loading the department."""
        stmt = select(ProductOrm).options(joinedload(ProductOrm.department)).where(ProductOrm.code == code)
        product_orm = self.session.scalars(stmt).first()
        # Check if product is found
        if product_orm is None:
            return None
            
        # Map ORM to domain model
        return _map_product_orm_to_model(product_orm)
        
    def get_all(self, filter_params: Optional[Dict[str, Any]] = None, 
                sort_by: Optional[str] = None, limit: Optional[int] = None, 
                offset: Optional[int] = None, sort_params: Optional[Dict[str, Any]] = None,
                pagination_params: Optional[Dict[str, Any]] = None) -> List[Product]:
        """Retrieves all products with optional filtering, sorting, and pagination."""
        stmt = select(ProductOrm).options(joinedload(ProductOrm.department))
        
        # Filtering (example: filter by active status)
        if filter_params and 'is_active' in filter_params:
            stmt = stmt.where(ProductOrm.is_active == filter_params['is_active'])
        # Add more filters as needed based on filter_params
        
        # Sorting
        if sort_params:
            sort_by = sort_params.get('sort_by', 'description')
            sort_column = getattr(ProductOrm, sort_by, None)
            if sort_column:
                if sort_params.get('sort_order', 'asc') == 'desc':
                    stmt = stmt.order_by(desc(sort_column))
                else:
                    stmt = stmt.order_by(asc(sort_column))
        elif sort_by:
             sort_column = getattr(ProductOrm, sort_by, None)
             if sort_column:
                 if sort_params and sort_params.get('order', 'asc') == 'desc':
                     stmt = stmt.order_by(desc(sort_column))
                 else:
                     stmt = stmt.order_by(asc(sort_column))
        else:
            # Default sort
            stmt = stmt.order_by(ProductOrm.description)
            
        # Pagination
        if pagination_params:
            page = pagination_params.get('page', 1)
            page_size = pagination_params.get('page_size', 10) # Default page size
            offset = (page - 1) * page_size
            limit = page_size
            
        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
            
        results_orm = self.session.scalars(stmt).all()
        return [_map_product_orm_to_model(prod) for prod in results_orm]

    def get_by_department_id(self, department_id: int) -> List[Product]:
        """Retrieves all products for a specific department."""
        stmt = select(ProductOrm).where(ProductOrm.department_id == department_id).order_by(ProductOrm.description)
        results_orm = self.session.scalars(stmt).all()
        # Map ORM objects to domain models
        return [_map_product_orm_to_model(prod) for prod in results_orm]

    def update(self, product: Product) -> Product:
        """Updates an existing product."""
        if product.id is None:
            raise ValueError("Product ID is required for update.")

        # Check for code collision if code is being changed
        if product.code:
             existing_by_code = self.get_by_code(product.code)
             if existing_by_code and existing_by_code.id != product.id:
                 raise ValueError(f"Another product with code '{product.code}' already exists.")

        product_orm = self.session.get(ProductOrm, product.id)
        if not product_orm:
            raise ValueError(f"Product with ID {product.id} not found.")
            
        # Ensure department exists if ID is provided and changing
        if product.department_id is not None and product.department_id != product_orm.department_id: 
            if not self.session.get(DepartmentOrm, product.department_id):
                 raise ValueError(f"Department with ID {product.department_id} not found.")

        try:
            # Get all data from the product model
            data = product.model_dump(exclude={'id', 'department'})
            
            # Filter out fields that don't exist in the ProductOrm model
            # Only include fields that are in the ProductOrm model
            orm_fields = {
                'code', 'description', 'cost_price', 'sell_price', 'wholesale_price', 
                'special_price', 'department_id', 'unit', 'uses_inventory', 
                'quantity_in_stock', 'min_stock', 'max_stock', 'last_updated', 
                'notes', 'is_active'
            }
            
            # Filter the data to only include fields that exist in the ORM
            filtered_data = {k: v for k, v in data.items() if k in orm_fields}
            
            # Update ORM attributes from domain model
            for key, value in filtered_data.items():
                setattr(product_orm, key, value)
                
            product_orm.last_updated = datetime.now() # Explicitly set last_updated
            
            self.session.flush()
            self.session.refresh(product_orm, attribute_names=['department']) # Refresh to get loaded department
            return _map_product_orm_to_model(product_orm)
        except IntegrityError as e:
            self.session.rollback()
            logging.error(f"Database integrity error updating product {product.id}: {e}")
            raise ValueError(f"Could not update product: {e}")
        except Exception as e:
            self.session.rollback()
            logging.error(f"Unexpected error updating product {product.id}: {e}")
            raise

    def delete(self, product_id: int) -> bool:
        """Deletes a product by its ID."""
        # Consider adding checks for related entities (sales, inventory) if needed
        product_orm = self.session.get(ProductOrm, product_id)
        if product_orm:
            try:
                self.session.delete(product_orm)
                self.session.flush()
                return True
            except Exception as e:
                 self.session.rollback()
                 logging.error(f"Error deleting product {product_id}: {e}")
                 raise
        return False

    def search(self, term: str) -> List[Product]:
        """Searches products by code or description."""
        search_term = f"%{term}%"
        stmt = select(ProductOrm).options(joinedload(ProductOrm.department)).where(
            or_(
                ProductOrm.code.ilike(search_term),
                ProductOrm.description.ilike(search_term)
            )
        ).order_by(ProductOrm.description)
        results_orm = self.session.scalars(stmt).all()
        return [_map_product_orm_to_model(prod) for prod in results_orm]

    def get_low_stock(self, threshold: Optional[Decimal] = None) -> List[Product]: # Changed threshold to Decimal
        """Retrieves products where stock <= min_stock or below optional threshold."""
        stmt = select(ProductOrm).options(joinedload(ProductOrm.department))
        
        # Only include products that use inventory
        stmt = stmt.where(ProductOrm.uses_inventory == True)
        
        if threshold is not None:
            stmt = stmt.where(ProductOrm.quantity_in_stock <= threshold)
        else:
            # Default: stock <= min_stock (handle potential None for min_stock if nullable)
            stmt = stmt.where(
                or_(
                   ProductOrm.min_stock == None, # Include products where min_stock is not set
                   ProductOrm.quantity_in_stock <= ProductOrm.min_stock
                )
            )
            
        stmt = stmt.order_by(ProductOrm.description)
        results_orm = self.session.scalars(stmt).all()
        return [_map_product_orm_to_model(prod) for prod in results_orm]

    def update_stock(self, product_id: int, quantity_change: Decimal, cost_price: Optional[Decimal] = None) -> Optional[Product]: # Changed types to Decimal
        """Updates the stock quantity and optionally the cost price of a specific product."""
        product_orm = self.session.get(ProductOrm, product_id)
        if product_orm:
            try:
                # Ensure quantity_in_stock is treated as Decimal if it comes from DB as Numeric
                current_stock = product_orm.quantity_in_stock if isinstance(product_orm.quantity_in_stock, Decimal) else Decimal(str(product_orm.quantity_in_stock))
                # Set the new quantity directly (assume quantity_change is the new total)
                product_orm.quantity_in_stock = quantity_change
                
                if cost_price is not None:
                     # Ensure cost_price is Decimal for assignment to Numeric column
                     product_orm.cost_price = cost_price if isinstance(cost_price, Decimal) else Decimal(str(cost_price))
                     
                product_orm.last_updated = datetime.now()
                self.session.flush()
                self.session.refresh(product_orm, attribute_names=['department'])
                return _map_product_orm_to_model(product_orm)
            except Exception as e:
                 self.session.rollback()
                 logging.error(f"Error updating stock for product {product_id}: {e}")
                 raise
        return None

# --- Inventory Movement Repository Implementation ---

class SqliteInventoryRepository(IInventoryRepository):
    """SQLite implementation of the inventory repository interface."""

    def __init__(self, session: Session):
        """Initialize with a database session."""
        self.session = session

    def add_movement(self, movement: InventoryMovement) -> InventoryMovement:
        """Adds a new inventory movement record."""
        try:
            # Map domain model to ORM
            movement_orm = InventoryMovementOrm(
                product_id=movement.product_id,
                user_id=movement.user_id,
                timestamp=movement.timestamp,
                movement_type=movement.movement_type,
                quantity=movement.quantity, # Assign Decimal directly to Numeric
                description=movement.description,
                related_id=movement.related_id
            )
            self.session.add(movement_orm)
            self.session.flush()
            self.session.refresh(movement_orm)
            return _map_movement_orm_to_model(movement_orm)
        except Exception as e:
            self.session.rollback()
            logging.error(f"Error adding inventory movement: {e}")
            raise

    def get_movements_for_product(self, product_id: int, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[InventoryMovement]:
        """Retrieves all inventory movements for a specific product, ordered by timestamp."""
        stmt = select(InventoryMovementOrm).where(InventoryMovementOrm.product_id == product_id)
        if start_date:
            stmt = stmt.where(InventoryMovementOrm.timestamp >= start_date)
        if end_date:
            stmt = stmt.where(InventoryMovementOrm.timestamp <= end_date)
        stmt = stmt.order_by(InventoryMovementOrm.timestamp.desc())
        results_orm = self.session.scalars(stmt).all()
        return [_map_movement_orm_to_model(move) for move in results_orm]

    def get_all_movements(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[InventoryMovement]:
        """Retrieves all inventory movements within an optional date range."""
        stmt = select(InventoryMovementOrm)
        if start_date:
            stmt = stmt.where(InventoryMovementOrm.timestamp >= start_date)
        if end_date:
            stmt = stmt.where(InventoryMovementOrm.timestamp <= end_date)
        stmt = stmt.order_by(InventoryMovementOrm.timestamp.desc())
        results_orm = self.session.scalars(stmt).all()
        return [_map_movement_orm_to_model(move) for move in results_orm]

# --- Sale Repository Implementation ---

class SqliteSaleRepository(ISaleRepository):
    """SQLite implementation of the sale repository interface."""

    def __init__(self, session: Session): # Changed from __init__(self, session)
        self.session = session

    def add_sale(self, sale: Sale) -> Sale:
        """Adds a new sale and its items to the database."""
        try:
            # Map Sale domain model to SaleOrm
            sale_orm = SaleOrm(
                date_time=sale.timestamp,
                customer_id=sale.customer_id,
                is_credit_sale=sale.is_credit_sale,
                user_id=sale.user_id,
                payment_type=sale.payment_type,
                total_amount=sale.total # Assuming total is calculated and passed in Sale model?
            )
            
            # Map SaleItem domain models to SaleItemOrm and associate with SaleOrm
            for item_model in sale.items:
                 item_orm = SaleItemOrm(
                     product_id=item_model.product_id,
                     quantity=item_model.quantity, # Decimal -> Numeric
                     unit_price=item_model.unit_price, # Decimal -> Numeric
                     product_code=item_model.product_code,
                     product_description=item_model.product_description
                 )
                 sale_orm.items.append(item_orm)
                 
            self.session.add(sale_orm)
            self.session.flush()
            self.session.refresh(sale_orm)
            # Need to eager load items when refreshing/mapping back if required by caller
            # Or map back manually here including items
            return _map_sale_orm_to_model(sale_orm)
        except Exception as e:
            self.session.rollback()
            logging.error(f"Error adding sale: {e}")
            raise
            
    def get_by_id(self, sale_id: int) -> Optional[Sale]:
        """Retrieves a single sale by its ID, including its items."""
        stmt = select(SaleOrm).options(joinedload(SaleOrm.items)).where(SaleOrm.id == sale_id)
        sale_orm = self.session.scalars(stmt).first()
        return _map_sale_orm_to_model(sale_orm)

    # Keeping the duplicate method name as it was in the original file
    def get_sale_by_id(self, sale_id: int) -> Optional[Sale]:
        """Retrieves a single sale by its ID (alternative method name)."""
        return self.get_by_id(sale_id)

    def get_sales_by_period(self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> List[Sale]:
        """Retrieves all sales within the specified time period."""
        stmt = select(SaleOrm).options(joinedload(SaleOrm.items))
        if start_time:
            stmt = stmt.where(SaleOrm.date_time >= start_time)
        if end_time:
             # Add a small delta for inclusive end_time check if needed
             # end_time_inclusive = end_time + timedelta(seconds=1) 
             stmt = stmt.where(SaleOrm.date_time <= end_time)
        stmt = stmt.order_by(SaleOrm.date_time.desc())
        
        # Use unique() to handle eager loading with collections
        results_orm = self.session.scalars(stmt).unique().all()
        return [_map_sale_orm_to_model(sale) for sale in results_orm]

    # Aggregation methods remain largely the same, as they return Dicts, not domain models directly
    # (Ensure they query the ORM models correctly)
    def get_sales_summary_by_period(self, start_date=None, end_date=None, 
                                  group_by: str = 'day') -> List[Dict[str, Any]]:
        """Retrieves aggregated sales data grouped by a time period."""
        # Convert date objects to datetime if needed
        if start_date and not isinstance(start_date, datetime):
            start_date = datetime.combine(start_date, datetime.min.time())
        if end_date and not isinstance(end_date, datetime):
            end_date = datetime.combine(end_date, datetime.max.time())
            
        # Date formatting depends on the database engine (SQLite specific functions)
        if group_by == 'day':
            date_format_str = '%Y-%m-%d'
            date_func = func.strftime(date_format_str, SaleOrm.date_time)
        elif group_by == 'month':
            date_format_str = '%Y-%m'
            date_func = func.strftime(date_format_str, SaleOrm.date_time)
        elif group_by == 'year':
             date_format_str = '%Y'
             date_func = func.strftime(date_format_str, SaleOrm.date_time)
        else:
             raise ValueError("Invalid group_by value. Use 'day', 'month', or 'year'.")

        # MANUALLY BUILD data by iterating over all sales in the period
        query = self.session.query(SaleOrm)
        if start_date:
            query = query.filter(SaleOrm.date_time >= start_date)
        if end_date:
            query = query.filter(SaleOrm.date_time <= end_date)
            
        sales = query.all()
        
        # Group sales by date
        summary_by_date = {}
        for sale in sales:
            # Format date according to group_by
            date_str = None
            if group_by == 'day':
                date_str = sale.date_time.strftime('%Y-%m-%d')
            elif group_by == 'month':
                date_str = sale.date_time.strftime('%Y-%m')
            elif group_by == 'year':
                date_str = sale.date_time.strftime('%Y')
                
            # Initialize if this date hasn't been seen yet
            if date_str not in summary_by_date:
                summary_by_date[date_str] = {
                    'date': date_str,
                    'total_sales': 0.0,
                    'num_sales': 0
                }
                
            # Add this sale to the summary
            summary_by_date[date_str]['total_sales'] += float(sale.total_amount)
            summary_by_date[date_str]['num_sales'] += 1
        
        # Convert dict to list and sort by date
        result_list = list(summary_by_date.values())
        result_list.sort(key=lambda x: x['date'])
        
        # Debug print the raw results
        print(f"Raw query results: {result_list}")
        
        return result_list

    def get_sales_by_payment_type(self, start_date=None, end_date=None) -> List[Dict[str, Any]]:
        """Retrieves sales data aggregated by payment type for a period."""
        stmt = select(
            SaleOrm.payment_type.label('payment_type'),
            func.sum(SaleOrm.total_amount).label('total_amount'),
            func.count(SaleOrm.id).label('num_sales')
        ).group_by(SaleOrm.payment_type).order_by(desc('total_amount'))

        if start_date:
            stmt = stmt.where(SaleOrm.date_time >= start_date)
        if end_date:
            stmt = stmt.where(SaleOrm.date_time <= end_date)

        results = self.session.execute(stmt).mappings().all()
        return [
            {
                'payment_type': row['payment_type'] if row['payment_type'] else 'Desconocido',
                'total_sales': float(row['total_amount']) if row['total_amount'] else 0.0,  # Convert to float and use total_sales key
                'num_sales': row['num_sales']
            } for row in results
        ]
        
    def get_sales_by_department(self, start_date=None, end_date=None) -> List[Dict[str, Any]]:
        """Retrieves sales data aggregated by product department for a period."""
        stmt = select(
            DepartmentOrm.id.label('department_id'),
            DepartmentOrm.name.label('department_name'),
            func.sum(SaleItemOrm.quantity * SaleItemOrm.unit_price).label('total_amount'),
            func.sum(SaleItemOrm.quantity).label('quantity_sold'),
            func.count(SaleOrm.id).label('num_sales') # Count distinct sales
        )
        stmt = stmt.select_from(SaleOrm)
        stmt = stmt.join(SaleItemOrm, SaleOrm.id == SaleItemOrm.sale_id)
        stmt = stmt.join(ProductOrm, SaleItemOrm.product_id == ProductOrm.id)
        stmt = stmt.join(DepartmentOrm, ProductOrm.department_id == DepartmentOrm.id)
        
        if start_date:
            stmt = stmt.where(SaleOrm.date_time >= start_date)
        if end_date:
            stmt = stmt.where(SaleOrm.date_time <= end_date)
            
        stmt = stmt.group_by(DepartmentOrm.id, DepartmentOrm.name).order_by(desc('total_amount'))
        
        results = self.session.execute(stmt).mappings().all()
        return [
            {
                 'department_id': row['department_id'],
                 'department_name': row['department_name'],
                 'total_sales': float(row['total_amount']) if row['total_amount'] else 0.0,  # Convert to float and use total_sales key
                 'quantity_sold': float(row['quantity_sold']) if row['quantity_sold'] else 0.0,  # Convert to float for consistency
                 'num_sales': row['num_sales']
            } for row in results
        ]

    def get_sales_by_customer(self, start_date=None, end_date=None, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves sales data aggregated by customer for a period."""
        stmt = select(
            CustomerOrm.id.label('customer_id'),
            CustomerOrm.name.label('customer_name'),
            func.sum(SaleOrm.total_amount).label('total_amount'),
            func.count(SaleOrm.id).label('num_sales')
        )
        stmt = stmt.select_from(SaleOrm)
        stmt = stmt.join(CustomerOrm, SaleOrm.customer_id == CustomerOrm.id)

        if start_date:
            stmt = stmt.where(SaleOrm.date_time >= start_date)
        if end_date:
            stmt = stmt.where(SaleOrm.date_time <= end_date)
            
        stmt = stmt.group_by(CustomerOrm.id, CustomerOrm.name).order_by(desc('total_amount')).limit(limit)
        
        results = self.session.execute(stmt).mappings().all()
        return [
             {
                 'customer_id': row['customer_id'],
                 'customer_name': row['customer_name'],
                 'total_sales': float(row['total_amount']) if row['total_amount'] else 0.0,  # Convert to float and use total_sales key
                 'num_sales': row['num_sales']
             } for row in results
        ]
        
    def get_top_selling_products(self, start_date=None, end_date=None, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves the top selling products for a period by quantity."""
        stmt = select(
            ProductOrm.id.label('product_id'),
            ProductOrm.code.label('product_code'),
            ProductOrm.description.label('product_description'),
            func.sum(SaleItemOrm.quantity).label('quantity_sold')
        ).select_from(SaleOrm).join(
            SaleItemOrm, SaleOrm.id == SaleItemOrm.sale_id
        ).join(
            ProductOrm, SaleItemOrm.product_id == ProductOrm.id
        )
        
        if start_date:
            stmt = stmt.where(SaleOrm.date_time >= start_date)
        if end_date:
            stmt = stmt.where(SaleOrm.date_time <= end_date)
            
        stmt = stmt.group_by(ProductOrm.id, ProductOrm.code, ProductOrm.description).order_by(
            desc('quantity_sold')
        ).limit(limit)
        
        results = self.session.execute(stmt).mappings().all()
        return [
            {
                'product_id': row['product_id'],
                'product_code': row['product_code'],
                'product_description': row['product_description'],
                'quantity_sold': row['quantity_sold']  # Keep as Decimal
            } for row in results
        ]
        
    def calculate_profit_for_period(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """
        Calculates the total profit for a period (revenue - cost).
        
        Args:
            start_time: The start of the period
            end_time: The end of the period
            
        Returns:
            Dictionary with profit data
            Example: {'revenue': 5000.0, 'cost': 3000.0, 'profit': 2000.0, 'margin': 0.4}
        """
        # Convert date objects to datetime if needed
        if not isinstance(start_time, datetime):
            start_time = datetime.combine(start_time, datetime.min.time())
        if not isinstance(end_time, datetime):
            end_time = datetime.combine(end_time, datetime.max.time())
            
        # Initialize result values
        total_revenue = Decimal('0.00')
        total_cost = Decimal('0.00')
            
        # Use join load to get all sales with their items in a single query
        sales_with_items = (self.session.query(SaleOrm)
            .options(joinedload(SaleOrm.items))
            .filter(SaleOrm.date_time >= start_time)
            .filter(SaleOrm.date_time <= end_time)
            .all())
        
        # Calculate revenue from all sale items
        for sale in sales_with_items:
            for item in sale.items:
                total_revenue += item.quantity * item.unit_price
                
                # Get the product cost price and calculate cost
                product = self.session.query(ProductOrm).filter(ProductOrm.id == item.product_id).first()
                if product and product.cost_price:
                    item_cost = product.cost_price * item.quantity
                    total_cost += item_cost
        
        # Calculate profit
        total_profit = total_revenue - total_cost
        
        # Calculate profit margin (as a decimal)
        profit_margin = Decimal('0.00')
        if total_revenue > Decimal('0.00'):
            profit_margin = total_profit / total_revenue
            
        # Convert all Decimal values to float to avoid type comparison issues
        return {
            'revenue': float(total_revenue),
            'cost': float(total_cost),
            'profit': float(total_profit),
            'margin': float(profit_margin)
        }
        
    def get_cash_drawer_entries(self, start_date=None, end_date=None, drawer_id=None) -> List[CashDrawerEntry]:
        """Get all cash drawer entries for a time period and optionally a specific drawer."""
        # Build base query
        query = self.session.query(CashDrawerEntryOrm)
        
        # Apply filters if provided
        if start_date:
            query = query.filter(CashDrawerEntryOrm.timestamp >= start_date)
        if end_date:
            query = query.filter(CashDrawerEntryOrm.timestamp <= end_date)
        if drawer_id is not None:
            query = query.filter(CashDrawerEntryOrm.drawer_id == drawer_id)
            
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

class SqliteCustomerRepository(ICustomerRepository):
    """SQLite implementation of the customer repository interface."""
    
    def __init__(self, session: Session):
        self.session = session
        
    def add(self, customer: Customer) -> Customer:
        """Add a new customer to the repository."""
        try:
            # LOGGING: Print type and value of customer.id and customer.cuit before adding
            print(f"[DEBUG] Adding customer: customer.id={customer.id} (type={type(customer.id)}), customer.cuit={customer.cuit} (type={type(customer.cuit)})")
            
            # Check for duplicate CUIT
            if customer.cuit:  # Only check if CUIT is provided
                existing_cuit = self.session.execute(
                    text("SELECT id FROM customers WHERE cuit = :cuit"),
                    {"cuit": customer.cuit}
                ).scalar_one_or_none()
                
                if existing_cuit:
                    raise ValueError(f"Customer with CUIT {customer.cuit} already exists")

            # Check for duplicate email
            if customer.email: # Only check if email is provided
                existing_email = self.session.execute(
                    text("SELECT id FROM customers WHERE email = :email"),
                    {"email": customer.email}
                ).scalar_one_or_none()

                if existing_email:
                    raise ValueError(f"Customer with email {customer.email} already exists")

            # Create a new CustomerOrm object and set attributes individually
            if customer.id is None:
                # New customer to be created with auto-ID
                customer_orm = CustomerOrm(
                    name=customer.name,
                    phone=customer.phone,
                    email=customer.email,
                    address=customer.address,
                    cuit=customer.cuit,
                    iva_condition=customer.iva_condition,
                    credit_limit=customer.credit_limit,
                    credit_balance=customer.credit_balance,
                    is_active=customer.is_active
                )
            else:
                # Customer with pre-defined ID (e.g., migration)
                customer_orm = CustomerOrm(
                    id=customer.id,
                    name=customer.name,
                    phone=customer.phone,
                    email=customer.email,
                    address=customer.address,
                    cuit=customer.cuit,
                    iva_condition=customer.iva_condition,
                    credit_limit=customer.credit_limit,
                    credit_balance=customer.credit_balance,
                    is_active=customer.is_active
                )
            
            # Add to session
            self.session.add(customer_orm)
            self.session.flush()
            self.session.refresh(customer_orm)
            
            # Map back to domain model
            return _map_customer_orm_to_model(customer_orm)
        except Exception as e:
            # Log the error
            logging.error(f"Error adding customer: {e}")
            raise
            
    def get_by_id(self, customer_id) -> Optional[Customer]:
        """Get a customer by ID."""
        customer_orm = self.session.query(CustomerOrm).filter(CustomerOrm.id == customer_id).first()
        return _map_customer_orm_to_model(customer_orm)
        
    def get_by_cuit(self, cuit: str) -> Optional[Customer]:
        """Get a customer by CUIT."""
        if not cuit:
            return None
        customer_orm = self.session.query(CustomerOrm).filter(CustomerOrm.cuit == cuit).first()
        return _map_customer_orm_to_model(customer_orm)
        
    def search(self, term: str, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Customer]:
        """Search for customers by name, phone, email, or CUIT, with optional pagination."""
        if not term:
            return []
            
        # Case-insensitive search on all text fields
        query = self.session.query(CustomerOrm).filter(
            or_(
                CustomerOrm.name.ilike(f"%{term}%"),
                CustomerOrm.phone.ilike(f"%{term}%"),
                CustomerOrm.email.ilike(f"%{term}%"),
                CustomerOrm.cuit.ilike(f"%{term}%")
            )
        ).order_by(CustomerOrm.name)

        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
        
        results = query.all()
        return [_map_customer_orm_to_model(orm) for orm in results]
        
    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Customer]:
        """Get all customers, with optional pagination."""
        query = self.session.query(CustomerOrm).order_by(CustomerOrm.name)
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
        customers_orm = query.all()
        return [_map_customer_orm_to_model(orm) for orm in customers_orm]
        
    def update(self, customer: Customer) -> Customer:
        """Update an existing customer."""
        try:
            # Get the existing customer
            customer_orm = self.session.query(CustomerOrm).filter(CustomerOrm.id == customer.id).first()
            if not customer_orm:
                raise ValueError(f"Customer with ID {customer.id} not found")
                
            # Update properties
            customer_orm.name = customer.name
            customer_orm.phone = customer.phone
            customer_orm.email = customer.email
            customer_orm.address = customer.address
            customer_orm.cuit = customer.cuit
            customer_orm.iva_condition = customer.iva_condition
            customer_orm.credit_limit = customer.credit_limit
            customer_orm.credit_balance = customer.credit_balance # Added this line
            # We typically don't update credit_balance directly through update()
            # It should be managed through dedicated operations that log the changes
            customer_orm.is_active = customer.is_active
            
            # Flush changes
            self.session.flush()
            self.session.refresh(customer_orm)
            
            # Return updated customer
            return _map_customer_orm_to_model(customer_orm)
        except Exception as e:
            # Log the error
            logging.error(f"Error updating customer: {e}")
            raise
            
    def update_balance(self, customer_id, new_balance: Decimal) -> bool:
        """Update a customer's credit balance."""
        try:
            # Get the customer
            customer_orm = self.session.query(CustomerOrm).filter(CustomerOrm.id == customer_id).first()
            if not customer_orm:
                return False
                
            # Update the balance
            customer_orm.credit_balance = new_balance
            
            # Flush changes
            self.session.flush()
            
            return True
        except Exception as e:
            # Log the error
            logging.error(f"Error updating customer balance: {e}")
            raise
            
    def delete(self, customer_id) -> bool:
        """Delete a customer by ID."""
        try:
            # Get the customer
            customer_orm = self.session.query(CustomerOrm).filter(CustomerOrm.id == customer_id).first()
            if not customer_orm:
                return False
                
            # Delete the customer
            self.session.delete(customer_orm)
            self.session.flush()
            
            return True
        except Exception as e:
            # Log the error
            logging.error(f"Error deleting customer: {e}")
            raise

class SqliteInvoiceRepository(IInvoiceRepository):
    """SQLite implementation of the invoice repository interface."""
    
    def __init__(self, session: Session):
        self.session = session

    def add(self, invoice: Invoice) -> Invoice:
        """Add a new invoice to the database."""
        try:
            # Check if the sale already has an invoice
            if self.get_by_sale_id(invoice.sale_id):
                raise ValueError(f"Invoice for sale ID {invoice.sale_id} already exists")
            
            # Map to ORM 
            invoice_orm = _map_invoice_model_to_orm(invoice)
            
            # Add to session
            self.session.add(invoice_orm)
            self.session.flush()
            self.session.refresh(invoice_orm)
            
            # Map back to domain model and return
            return _map_invoice_orm_to_model(invoice_orm)
        except Exception as e:
            # Log error and re-raise
            logging.error(f"Error adding invoice: {e}")
            raise
    
    def get_by_id(self, invoice_id: int) -> Optional[Invoice]:
        """Get an invoice by its ID."""
        invoice_orm = self.session.query(InvoiceOrm).filter(InvoiceOrm.id == invoice_id).first()
        return _map_invoice_orm_to_model(invoice_orm)
    
    def get_by_sale_id(self, sale_id: int) -> Optional[Invoice]:
        """Get an invoice for a specific sale."""
        invoice_orm = self.session.query(InvoiceOrm).filter(InvoiceOrm.sale_id == sale_id).first()
        return _map_invoice_orm_to_model(invoice_orm)
        
    def get_by_invoice_number(self, invoice_number: str) -> Optional[Invoice]:
        """Get an invoice by its number."""
        invoice_orm = self.session.query(InvoiceOrm).filter(InvoiceOrm.invoice_number == invoice_number).first()
        return _map_invoice_orm_to_model(invoice_orm)
    
    def get_all(self) -> List[Invoice]:
        """Get all invoices."""
        invoice_orms = self.session.query(InvoiceOrm).all()
        return [_map_invoice_orm_to_model(orm) for orm in invoice_orms if orm is not None]
    
    def update(self, invoice: Invoice) -> Invoice:
        """Update an existing invoice."""
        try:
            # Find the existing invoice
            existing_orm = self.session.query(InvoiceOrm).filter(InvoiceOrm.id == invoice.id).first()
            if not existing_orm:
                raise ValueError(f"Invoice with ID {invoice.id} not found")
            
            # Update the ORM object with new values
            updated_orm = _map_invoice_model_to_orm(invoice, existing_orm)
            
            # Flush to ensure changes are reflected
            self.session.flush()
            self.session.refresh(updated_orm)
            
            # Return mapped domain model
            return _map_invoice_orm_to_model(updated_orm)
        except Exception as e:
            # Log error and re-raise
            logging.error(f"Error updating invoice: {e}")
            raise
    
    def delete(self, invoice_id: int) -> bool:
        """Delete an invoice by its ID."""
        try:
            invoice_orm = self.session.query(InvoiceOrm).filter(InvoiceOrm.id == invoice_id).first()
            if not invoice_orm:
                return False
            
            self.session.delete(invoice_orm)
            self.session.flush()
            return True
        except Exception as e:
            # Log error and re-raise
            logging.error(f"Error deleting invoice: {e}")
            raise

class SqliteCreditPaymentRepository(ICreditPaymentRepository):
    """SQLite implementation of the credit payment repository interface."""
    
    def __init__(self, session: Session):
        self.session = session
        
    def add(self, payment: CreditPayment) -> CreditPayment:
        """Adds a new credit payment to the database."""
        try:
            # Verify customer exists
            customer_exists = self.session.query(CustomerOrm).filter(CustomerOrm.id == payment.customer_id).first()
            if not customer_exists:
                raise ValueError(f"Customer with ID {payment.customer_id} not found.")
                
            # Map the domain model to ORM
            payment_orm = CreditPaymentOrm(
                customer_id=payment.customer_id,
                amount=payment.amount,
                timestamp=payment.payment_date if payment.payment_date else datetime.datetime.now(),
                notes=payment.description,
                user_id=payment.user_id
            )
            
            # Add to session
            self.session.add(payment_orm)
            self.session.flush()
            self.session.refresh(payment_orm)
            
            # Map back to domain model
            return _map_credit_payment_orm_to_model(payment_orm)
        except Exception as e:
            logging.error(f"Error adding credit payment: {e}")
            raise
    
    def get_by_id(self, payment_id: int) -> Optional[CreditPayment]:
        """Gets a credit payment by its ID."""
        payment_orm = self.session.query(CreditPaymentOrm).filter(CreditPaymentOrm.id == payment_id).first()
        return _map_credit_payment_orm_to_model(payment_orm)
        
    def get_for_customer(self, customer_id) -> List[CreditPayment]:
        """Gets all credit payments for a specific customer."""
        payments_orm = self.session.query(CreditPaymentOrm).filter(
            CreditPaymentOrm.customer_id == customer_id
        ).order_by(CreditPaymentOrm.timestamp.desc()).all()
        
        return [_map_credit_payment_orm_to_model(orm) for orm in payments_orm]

class SqliteUserRepository(IUserRepository):
    """SQLite implementation of the user repository interface."""
    
    def __init__(self, session: Session):
        self.session = session
        
    def _hash_password(self, password: str) -> str:
        """Hash the password using bcrypt."""
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_bytes = bcrypt.hashpw(password_bytes, salt)
        return hashed_bytes.decode('utf-8')
        
    def add(self, user: User) -> User:
        """Adds a new user to the database."""
        try:
            # Check if username already exists
            if self.get_by_username(user.username):
                raise ValueError(f"Username '{user.username}' already exists.")
            
            # If password is provided but no password_hash, hash the password
            if getattr(user, 'password', None) and not user.password_hash:
                user.password_hash = self._hash_password(user.password)
                
            # Map domain model to ORM
            user_orm = UserOrm(
                username=user.username,
                password_hash=user.password_hash,
                email=getattr(user, 'email', None),
                is_active=user.is_active,
                is_admin=getattr(user, 'is_admin', False)
            )
            
            # Add to session
            self.session.add(user_orm)
            self.session.flush()
            self.session.refresh(user_orm)
            
            # Map back to domain model
            return _map_user_orm_to_model(user_orm)
        except Exception as e:
            logging.error(f"Error adding user: {e}")
            raise
            
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Retrieves a user by their ID."""
        user_orm = self.session.query(UserOrm).filter(UserOrm.id == user_id).first()
        return _map_user_orm_to_model(user_orm)
        
    def get_by_username(self, username: str) -> Optional[User]:
        """Retrieves a user by their username."""
        user_orm = self.session.query(UserOrm).filter(UserOrm.username == username).first()
        return _map_user_orm_to_model(user_orm)
        
    def update(self, user: User) -> Optional[User]:
        """Updates an existing user."""
        try:
            # Get existing user
            user_orm = self.session.query(UserOrm).filter(UserOrm.id == user.id).first()
            if not user_orm:
                return None
                
            # Check username uniqueness if changed
            if user.username != user_orm.username and self.get_by_username(user.username):
                raise ValueError(f"Username '{user.username}' already exists.")
                
            # Update fields
            user_orm.username = user.username
            user_orm.email = user.email
            user_orm.is_active = user.is_active
            user_orm.is_admin = user.is_admin
            
            # Only update password if provided
            if user.password_hash and user.password_hash != user_orm.password_hash:
                user_orm.password_hash = user.password_hash
                
            # Flush and refresh
            self.session.flush()
            self.session.refresh(user_orm)
            
            # Map back to domain
            return _map_user_orm_to_model(user_orm)
        except Exception as e:
            logging.error(f"Error updating user: {e}")
            raise
            
    def delete(self, user_id: int) -> bool:
        """Deletes a user by ID."""
        try:
            user_orm = self.session.query(UserOrm).filter(UserOrm.id == user_id).first()
            if not user_orm:
                return False
                
            self.session.delete(user_orm)
            self.session.flush()
            return True
        except Exception as e:
            logging.error(f"Error deleting user: {e}")
            raise
            
    def get_all(self) -> List[User]:
        """Retrieves all users."""
        users_orm = self.session.query(UserOrm).all()
        return [_map_user_orm_to_model(user) for user in users_orm]

class SqliteSupplierRepository(ISupplierRepository):
    """SQLite implementation of the supplier repository interface."""
    
    def __init__(self, session: Session):
        self.session = session
        
    def add(self, supplier: Supplier) -> Supplier:
        """Add a new supplier to the database."""
        try:
            # Check for name or CUIT duplicates
            if supplier.name and self.get_by_name(supplier.name):
                raise ValueError(f"Supplier with name '{supplier.name}' already exists.")
            
            if supplier.cuit and self.get_by_cuit(supplier.cuit):
                raise ValueError(f"Supplier with CUIT '{supplier.cuit}' already exists.")
                
            # Map domain model to ORM
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
            
            # Add to session
            self.session.add(supplier_orm)
            self.session.flush()
            self.session.refresh(supplier_orm)
            
            # Map back to domain model
            return _map_supplier_orm_to_model(supplier_orm)
        except Exception as e:
            logging.error(f"Error adding supplier: {e}")
            raise
    
    def get_by_id(self, supplier_id: int) -> Optional[Supplier]:
        """Get a supplier by ID."""
        supplier_orm = self.session.query(SupplierOrm).filter(SupplierOrm.id == supplier_id).first()
        return _map_supplier_orm_to_model(supplier_orm)
        
    def get_by_name(self, name: str) -> Optional[Supplier]:
        """Get a supplier by name."""
        if not name:
            return None
            
        supplier_orm = self.session.query(SupplierOrm).filter(SupplierOrm.name == name).first()
        return _map_supplier_orm_to_model(supplier_orm)
        
    def get_by_cuit(self, cuit: str) -> Optional[Supplier]:
        """Get a supplier by CUIT."""
        if not cuit:
            return None
            
        supplier_orm = self.session.query(SupplierOrm).filter(SupplierOrm.cuit == cuit).first()
        return _map_supplier_orm_to_model(supplier_orm)
    
    def get_all(self) -> List[Supplier]:
        """Get all suppliers."""
        suppliers_orm = self.session.query(SupplierOrm).order_by(SupplierOrm.name).all()
        return [_map_supplier_orm_to_model(orm) for orm in suppliers_orm]
        
    def update(self, supplier: Supplier) -> Optional[Supplier]:
        """Update an existing supplier."""
        try:
            # Get the existing supplier
            supplier_orm = self.session.query(SupplierOrm).filter(SupplierOrm.id == supplier.id).first()
            if not supplier_orm:
                return None
                
            # Check for name or CUIT duplicates with other suppliers
            if supplier.name and supplier.name != supplier_orm.name:
                existing = self.get_by_name(supplier.name)
                if existing and existing.id != supplier.id:
                    raise ValueError(f"Another supplier with name '{supplier.name}' already exists.")
            
            if supplier.cuit and supplier.cuit != supplier_orm.cuit:
                existing = self.get_by_cuit(supplier.cuit)
                if existing and existing.id != supplier.id:
                    raise ValueError(f"Another supplier with CUIT '{supplier.cuit}' already exists.")
            
            # Update properties
            supplier_orm.name = supplier.name
            supplier_orm.contact_person = supplier.contact_person
            supplier_orm.phone = supplier.phone
            supplier_orm.email = supplier.email
            supplier_orm.address = supplier.address
            supplier_orm.cuit = supplier.cuit
            supplier_orm.notes = supplier.notes
            supplier_orm.is_active = supplier.is_active
            
            # Flush changes
            self.session.flush()
            self.session.refresh(supplier_orm)
            
            # Return updated supplier
            return _map_supplier_orm_to_model(supplier_orm)
        except Exception as e:
            logging.error(f"Error updating supplier: {e}")
            raise
            
    def delete(self, supplier_id: int) -> bool:
        """Delete a supplier by ID."""
        try:
            # Check if supplier exists
            supplier_orm = self.session.query(SupplierOrm).filter(SupplierOrm.id == supplier_id).first()
            if not supplier_orm:
                return False
                
            # Check if supplier has associated purchase orders
            has_purchase_orders = self.session.query(PurchaseOrderOrm).filter(
                PurchaseOrderOrm.supplier_id == supplier_id
            ).first() is not None
            
            if has_purchase_orders:
                raise ValueError(f"Cannot delete supplier ID {supplier_id}. It has associated purchase orders.")
                
            # Delete the supplier
            self.session.delete(supplier_orm)
            self.session.flush()
            
            return True
        except Exception as e:
            logging.error(f"Error deleting supplier: {e}")
            raise
            
    def search(self, query: str) -> List[Supplier]:
        """Search for suppliers by name, contact, phone, email, or CUIT."""
        if not query:
            return []
            
        search_term = f"%{query}%"
        suppliers_orm = self.session.query(SupplierOrm).filter(
            or_(
                SupplierOrm.name.ilike(search_term),
                SupplierOrm.contact_person.ilike(search_term),
                SupplierOrm.phone.ilike(search_term),
                SupplierOrm.email.ilike(search_term),
                SupplierOrm.cuit.ilike(search_term)
            )
        ).order_by(SupplierOrm.name).all()
        
        return [_map_supplier_orm_to_model(orm) for orm in suppliers_orm]

class SqlitePurchaseOrderRepository(IPurchaseOrderRepository):
    """SQLite implementation of the purchase order repository interface."""
    
    def __init__(self, session: Session):
        self.session = session
        
    def add(self, purchase_order: PurchaseOrder) -> PurchaseOrder:
        """Add a new purchase order to the database."""
        try:
            # Verify the supplier exists
            supplier = self.session.query(SupplierOrm).filter(SupplierOrm.id == purchase_order.supplier_id).first()
            if not supplier:
                raise ValueError(f"Supplier with ID {purchase_order.supplier_id} not found.")
                
            # Map the domain model to ORM
            po_orm = PurchaseOrderOrm(
                supplier_id=purchase_order.supplier_id,
                supplier_name=supplier.name,  # Denormalized for quick access
                order_date=purchase_order.order_date,
                expected_delivery_date=purchase_order.expected_delivery_date,
                status=purchase_order.status,
                notes=purchase_order.notes
            )
            
            # Add purchase order items
            for item in purchase_order.items:
                product = self.session.query(ProductOrm).filter(ProductOrm.id == item.product_id).first()
                if not product:
                    raise ValueError(f"Product with ID {item.product_id} not found.")
                    
                item_orm = PurchaseOrderItemOrm(
                    product_id=item.product_id,
                    product_code=product.code,
                    product_description=product.description,
                    quantity_ordered=item.quantity_ordered,
                    cost_price=item.unit_price,
                    quantity_received=item.quantity_received
                )
                po_orm.items.append(item_orm)
            
            # Add to session
            self.session.add(po_orm)
            self.session.flush()
            self.session.refresh(po_orm)
            
            # Map back to domain model
            return _map_purchase_order_orm_to_model(po_orm)
        except Exception as e:
            logging.error(f"Error adding purchase order: {e}")
            raise
            
    def get_by_id(self, po_id: int) -> Optional[PurchaseOrder]:
        """Get a purchase order by ID."""
        po_orm = self.session.query(PurchaseOrderOrm).options(
            joinedload(PurchaseOrderOrm.items)
        ).filter(PurchaseOrderOrm.id == po_id).first()
        return _map_purchase_order_orm_to_model(po_orm)
        
    def get_all(self, status: str | None = None, supplier_id: int | None = None) -> List[PurchaseOrder]:
        """Get all purchase orders with optional filtering."""
        query = self.session.query(PurchaseOrderOrm).options(
            joinedload(PurchaseOrderOrm.items)
        )
        
        if status:
            query = query.filter(PurchaseOrderOrm.status == status)
        if supplier_id:
            query = query.filter(PurchaseOrderOrm.supplier_id == supplier_id)
            
        po_orms = query.order_by(PurchaseOrderOrm.order_date.desc()).all()
        return [_map_purchase_order_orm_to_model(po) for po in po_orms]
        
    def update_status(self, po_id: int, status: str) -> bool:
        """Update the status of a purchase order."""
        try:
            po_orm = self.session.query(PurchaseOrderOrm).filter(PurchaseOrderOrm.id == po_id).first()
            if not po_orm:
                return False
                
            po_orm.status = status
            po_orm.updated_at = datetime.now()
            self.session.flush()
            
            return True
        except Exception as e:
            logging.error(f"Error updating purchase order status: {e}")
            raise
            
    def get_items(self, po_id: int) -> List[PurchaseOrderItem]:
        """Get all items for a specific purchase order."""
        po_orm = self.session.query(PurchaseOrderOrm).options(
            joinedload(PurchaseOrderOrm.items)
        ).filter(PurchaseOrderOrm.id == po_id).first()
        
        if not po_orm:
            return []
            
        return [_map_purchase_order_item_orm_to_model(item) for item in po_orm.items]
        
    def update_item_received_quantity(self, item_id: int, quantity_received_increment: float) -> bool:
        """Update the received quantity for a purchase order item."""
        try:
            item_orm = self.session.query(PurchaseOrderItemOrm).filter(
                PurchaseOrderItemOrm.id == item_id
            ).first()
            
            if not item_orm:
                return False
                
            item_orm.quantity_received += Decimal(str(quantity_received_increment))
            self.session.flush()
            
            # If necessary, update the purchase order status based on item receipt
            self._check_and_update_po_status(item_orm.purchase_order_id)
            
            return True
        except Exception as e:
            logging.error(f"Error updating item received quantity: {e}")
            raise
            
    def _check_and_update_po_status(self, po_id: int) -> None:
        """Helper to check and update PO status based on item receipt status."""
        po_orm = self.session.query(PurchaseOrderOrm).options(
            joinedload(PurchaseOrderOrm.items)
        ).filter(PurchaseOrderOrm.id == po_id).first()
        
        if not po_orm or po_orm.status != "PENDING":
            return
            
        # Check if all items are fully received
        all_received = True
        for item in po_orm.items:
            if item.quantity_received < item.quantity_ordered:
                all_received = False
                break
                
        if all_received:
            po_orm.status = "RECEIVED"
            po_orm.updated_at = datetime.now()
            self.session.flush()

class SqliteCashDrawerRepository(SQLiteCashDrawerRepository):
    """Adapter class for SQLiteCashDrawerRepository to maintain API compatibility."""
    pass
