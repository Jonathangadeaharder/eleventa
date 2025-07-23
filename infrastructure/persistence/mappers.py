"""Centralized mapping utilities for ORM to Domain model conversions.

This module provides a unified approach to mapping between SQLAlchemy ORM models
and domain models, reducing boilerplate code in repositories.
"""

from typing import Optional, List, Dict, Any, TypeVar, Type, Union
from decimal import Decimal
import json
import logging
from datetime import datetime

# Domain models
from core.models.product import Product
from core.models.department import Department
from core.models.sale import Sale, SaleItem
from core.models.customer import Customer
from core.models.inventory import InventoryMovement
from core.models.invoice import Invoice
from core.models.credit_payment import CreditPayment
from core.models.user import User
from core.models.unit import Unit

# ORM models (imported at runtime to avoid circular imports)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from infrastructure.persistence.sqlite.models_mapping import (
        ProductOrm, DepartmentOrm, SaleOrm, SaleItemOrm, CustomerOrm,
        InventoryMovementOrm, InvoiceOrm, CreditPaymentOrm, UserOrm, UnitOrm
    )

# Type variables for generic mapping
DomainModel = TypeVar('DomainModel')
OrmModel = TypeVar('OrmModel')

class ModelMapper:
    """Centralized mapper for ORM to Domain model conversions."""
    
    @staticmethod
    def department_orm_to_domain(dept_orm: "DepartmentOrm") -> Optional[Department]:
        """Maps DepartmentOrm to Department domain model."""
        if not dept_orm:
            return None
        return Department(
            id=dept_orm.id,
            name=dept_orm.name,
            description=getattr(dept_orm, 'description', None)
        )
    
    @staticmethod
    def product_orm_to_domain(prod_orm: "ProductOrm") -> Optional[Product]:
        """Maps ProductOrm to Product domain model."""
        if not prod_orm:
            return None
        
        # Map related department if exists
        department_model = ModelMapper.department_orm_to_domain(prod_orm.department) if prod_orm.department else None
        
        return Product(
            id=prod_orm.id,
            code=prod_orm.code,
            description=prod_orm.description,
            cost_price=prod_orm.cost_price,
            sell_price=prod_orm.sell_price,
            wholesale_price=prod_orm.wholesale_price,
            special_price=prod_orm.special_price,
            department_id=prod_orm.department_id,
            department=department_model,
            unit=prod_orm.unit,
            uses_inventory=prod_orm.uses_inventory,
            quantity_in_stock=prod_orm.quantity_in_stock,
            min_stock=prod_orm.min_stock,
            max_stock=prod_orm.max_stock,
            last_updated=prod_orm.last_updated,
            notes=prod_orm.notes,
            is_active=prod_orm.is_active
        )
    
    @staticmethod
    def sale_item_orm_to_domain(item_orm: "SaleItemOrm") -> Optional[SaleItem]:
        """Maps SaleItemOrm to SaleItem domain model."""
        if not item_orm:
            return None
        return SaleItem(
            id=item_orm.id,
            sale_id=item_orm.sale_id,
            product_id=item_orm.product_id,
            quantity=item_orm.quantity,
            unit_price=item_orm.unit_price,
            product_code=item_orm.product_code,
            product_description=item_orm.product_description,
            product_unit=getattr(item_orm, 'product_unit', 'Unidad')
        )
    
    @staticmethod
    def sale_orm_to_domain(sale_orm: "SaleOrm") -> Optional[Sale]:
        """Maps SaleOrm to Sale domain model."""
        if not sale_orm:
            return None
        
        # Map related items
        items_model = [
            ModelMapper.sale_item_orm_to_domain(item) 
            for item in sale_orm.items
        ] if sale_orm.items else []
        
        return Sale(
            id=sale_orm.id,
            timestamp=sale_orm.date_time,
            items=items_model,
            customer_id=sale_orm.customer_id,
            is_credit_sale=sale_orm.is_credit_sale,
            user_id=sale_orm.user_id,
            payment_type=sale_orm.payment_type
        )
    
    @staticmethod
    def customer_orm_to_domain(cust_orm: "CustomerOrm") -> Optional[Customer]:
        """Maps CustomerOrm to Customer domain model."""
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
            credit_limit=Decimal(str(cust_orm.credit_limit)) if cust_orm.credit_limit is not None else Decimal('0.0'),
            credit_balance=Decimal(str(cust_orm.credit_balance)) if cust_orm.credit_balance is not None else Decimal('0.0'),
            is_active=cust_orm.is_active
        )
    
    @staticmethod
    def inventory_movement_orm_to_domain(move_orm: "InventoryMovementOrm") -> Optional[InventoryMovement]:
        """Maps InventoryMovementOrm to InventoryMovement domain model."""
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
    
    @staticmethod
    def credit_payment_orm_to_domain(payment_orm: "CreditPaymentOrm") -> Optional[CreditPayment]:
        """Maps CreditPaymentOrm to CreditPayment domain model."""
        if not payment_orm:
            return None
        return CreditPayment(
            id=payment_orm.id,
            customer_id=payment_orm.customer_id,
            amount=payment_orm.amount,
            timestamp=payment_orm.timestamp,
            notes=payment_orm.notes,
            user_id=payment_orm.user_id
        )
    
    @staticmethod
    def user_orm_to_domain(user_orm: "UserOrm") -> Optional[User]:
        """Maps UserOrm to User domain model."""
        if not user_orm:
            return None
        return User(
            id=user_orm.id,
            username=user_orm.username,
            password_hash=user_orm.password_hash,
            email=user_orm.email,
            is_active=user_orm.is_active,
            is_admin=user_orm.is_admin
        )
    
    @staticmethod
    def invoice_orm_to_domain(invoice_orm: "InvoiceOrm") -> Optional[Invoice]:
        """Maps InvoiceOrm to Invoice domain model."""
        if not invoice_orm:
            return None
        
        # Deserialize customer_details if it's stored as JSON string
        customer_details_dict = {}
        if invoice_orm.customer_details:
            try:
                customer_details_dict = json.loads(invoice_orm.customer_details)
            except json.JSONDecodeError:
                logging.warning(f"Could not decode customer_details JSON for invoice {invoice_orm.id}")
                customer_details_dict = {}
        
        return Invoice(
            id=invoice_orm.id,
            sale_id=invoice_orm.sale_id,
            customer_id=invoice_orm.customer_id,
            invoice_number=invoice_orm.invoice_number,
            invoice_date=invoice_orm.invoice_date,
            invoice_type=invoice_orm.invoice_type,
            customer_details=customer_details_dict,
            subtotal=invoice_orm.subtotal,
            iva_amount=invoice_orm.iva_amount,
            total=invoice_orm.total,
            iva_condition=invoice_orm.iva_condition,
            cae=invoice_orm.cae,
            cae_due_date=invoice_orm.cae_due_date,
            notes=invoice_orm.notes,
            is_active=invoice_orm.is_active
        )
    
    @staticmethod
    def invoice_domain_to_orm(invoice: Invoice, invoice_orm: Optional["InvoiceOrm"] = None) -> "InvoiceOrm":
        """Maps Invoice domain model to InvoiceOrm."""
        # Import here to avoid circular imports
        from infrastructure.persistence.sqlite.models_mapping import InvoiceOrm
        
        if not invoice_orm:
            invoice_orm = InvoiceOrm()
        
        # Map attributes from domain model to ORM model
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
            invoice_orm.customer_details = "{}"
        
        invoice_orm.subtotal = invoice.subtotal
        invoice_orm.iva_amount = invoice.iva_amount
        invoice_orm.total = invoice.total
        invoice_orm.iva_condition = invoice.iva_condition
        invoice_orm.cae = invoice.cae
        invoice_orm.cae_due_date = invoice.cae_due_date
        invoice_orm.notes = invoice.notes
        invoice_orm.is_active = invoice.is_active
        
        return invoice_orm
    
    @staticmethod
    def unit_orm_to_domain(unit_orm: "UnitOrm") -> Optional[Unit]:
        """Maps UnitOrm to Unit domain model."""
        if not unit_orm:
            return None
        return Unit(
            id=unit_orm.id,
            name=unit_orm.name,
            abbreviation=unit_orm.abbreviation,
            description=unit_orm.description,
            is_active=unit_orm.is_active,
            created_at=unit_orm.created_at,
            updated_at=unit_orm.updated_at
        )


class AutoMapper:
    """Generic auto-mapper using Pydantic's model_validate for compatible models."""
    
    @staticmethod
    def orm_to_domain(orm_instance: OrmModel, domain_class: Type[DomainModel], 
                     field_mappings: Optional[Dict[str, str]] = None,
                     exclude_fields: Optional[List[str]] = None) -> Optional[DomainModel]:
        """Generic ORM to domain mapping using Pydantic's model_validate.
        
        Args:
            orm_instance: The ORM instance to convert
            domain_class: The target domain model class
            field_mappings: Optional dict mapping ORM field names to domain field names
            exclude_fields: Optional list of ORM fields to exclude from mapping
        
        Returns:
            Domain model instance or None if orm_instance is None
        """
        if not orm_instance:
            return None
        
        # Extract data from ORM columns
        data = {}
        
        # Get all column attributes
        if hasattr(orm_instance, '__table__'):
            for column in orm_instance.__table__.columns:
                field_name = column.name
                if exclude_fields and field_name in exclude_fields:
                    continue
                
                # Apply field mapping if provided
                target_field = field_mappings.get(field_name, field_name) if field_mappings else field_name
                data[target_field] = getattr(orm_instance, field_name)
        
        # Try to use Pydantic's model_validate if available
        if hasattr(domain_class, 'model_validate'):
            try:
                return domain_class.model_validate(data)
            except Exception as e:
                logging.warning(f"Auto-mapping failed for {domain_class.__name__}: {e}")
                return None
        
        # Fallback for dataclasses or other types
        try:
            return domain_class(**data)
        except Exception as e:
            logging.warning(f"Auto-mapping failed for {domain_class.__name__}: {e}")
            return None


# Convenience functions for backward compatibility
def map_department_orm_to_model(dept_orm) -> Optional[Department]:
    """Backward compatibility wrapper."""
    return ModelMapper.department_orm_to_domain(dept_orm)

def map_product_orm_to_model(prod_orm) -> Optional[Product]:
    """Backward compatibility wrapper."""
    return ModelMapper.product_orm_to_domain(prod_orm)

def map_sale_orm_to_model(sale_orm) -> Optional[Sale]:
    """Backward compatibility wrapper."""
    return ModelMapper.sale_orm_to_domain(sale_orm)

def map_sale_item_orm_to_model(item_orm) -> Optional[SaleItem]:
    """Backward compatibility wrapper."""
    return ModelMapper.sale_item_orm_to_domain(item_orm)

def map_customer_orm_to_model(cust_orm) -> Optional[Customer]:
    """Backward compatibility wrapper."""
    return ModelMapper.customer_orm_to_domain(cust_orm)

def map_inventory_movement_orm_to_model(move_orm) -> Optional[InventoryMovement]:
    """Backward compatibility wrapper."""
    return ModelMapper.inventory_movement_orm_to_domain(move_orm)

def map_credit_payment_orm_to_model(payment_orm) -> Optional[CreditPayment]:
    """Backward compatibility wrapper."""
    return ModelMapper.credit_payment_orm_to_domain(payment_orm)

def map_user_orm_to_model(user_orm) -> Optional[User]:
    """Backward compatibility wrapper."""
    return ModelMapper.user_orm_to_domain(user_orm)

def map_invoice_orm_to_model(invoice_orm) -> Optional[Invoice]:
    """Backward compatibility wrapper."""
    return ModelMapper.invoice_orm_to_domain(invoice_orm)

def map_invoice_model_to_orm(invoice: Invoice, invoice_orm=None):
    """Backward compatibility wrapper."""
    return ModelMapper.invoice_domain_to_orm(invoice, invoice_orm)