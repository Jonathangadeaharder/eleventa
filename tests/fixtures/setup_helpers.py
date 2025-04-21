"""
Test setup helper functions.

This module provides helper functions to extract complex test data setup
into reusable components.
"""
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
import uuid
from sqlalchemy.orm import Session

# Import core models
from core.models.product import Product, Department
from core.models.customer import Customer
from core.models.sale import Sale, SaleItem
from core.models.invoice import Invoice
from core.models.user import User
from core.models.supplier import Supplier
from core.models.purchase import PurchaseOrder, PurchaseOrderItem
from core.models.inventory import InventoryMovement

# Import repositories
from infrastructure.persistence.sqlite.repositories import (
    SqliteProductRepository, SqliteDepartmentRepository,
    SqliteCustomerRepository, SqliteSaleRepository,
    SqliteInventoryRepository, SqliteInvoiceRepository,
    SqliteUserRepository, SqliteSupplierRepository,
    SqlitePurchaseOrderRepository
)

# Import test data factory functions 
from tests.fixtures.test_data import (
    create_department, create_product, create_customer,
    create_sale, create_sale_item, create_invoice,
    create_user, create_supplier, create_purchase_order
)

def setup_basic_product_data(session: Session) -> Tuple[Department, List[Product]]:
    """
    Set up a department and some basic products for testing.
    
    Args:
        session: SQLAlchemy session
        
    Returns:
        Tuple containing the department and a list of created products
    """
    # Create repositories
    dept_repo = SqliteDepartmentRepository(session)
    product_repo = SqliteProductRepository(session)
    
    # Create a department
    department = dept_repo.add(create_department(name="Test Department"))
    
    # Create some products in that department
    products = []
    products.append(product_repo.add(create_product(
        code="P001",
        description="Test Product 1",
        sell_price=Decimal("10.00"),
        cost_price=Decimal("5.00"),
        department_id=department.id
    )))
    
    products.append(product_repo.add(create_product(
        code="P002",
        description="Test Product 2",
        sell_price=Decimal("20.00"),
        cost_price=Decimal("10.00"),
        department_id=department.id
    )))
    
    products.append(product_repo.add(create_product(
        code="P003",
        description="Test Product 3",
        sell_price=Decimal("15.00"),
        cost_price=Decimal("7.50"),
        department_id=department.id
    )))
    
    return department, products

def setup_customer_data(session: Session, num_customers: int = 2) -> List[Customer]:
    """
    Set up multiple customers for testing.
    
    Args:
        session: SQLAlchemy session
        num_customers: Number of customers to create
        
    Returns:
        List of created customers
    """
    customer_repo = SqliteCustomerRepository(session)
    customers = []
    
    # Create customers
    for i in range(1, num_customers + 1):
        customer = customer_repo.add(create_customer(
            name=f"Test Customer {i}",
            phone=f"555-{1000+i}",
            email=f"customer{i}@example.com",
            cuit=f"2012345678{i}",
            address=f"{i}23 Test St"
        ))
        customers.append(customer)
    
    return customers

def setup_sale_data(
    session: Session, 
    products: List[Product], 
    customer: Optional[Customer] = None,
    num_sales: int = 1
) -> List[Sale]:
    """
    Set up sales data for testing.
    
    Args:
        session: SQLAlchemy session
        products: List of products to use in sales
        customer: Optional customer for the sales
        num_sales: Number of sales to create
        
    Returns:
        List of created sales
    """
    sale_repo = SqliteSaleRepository(session)
    sales = []
    
    # Create sales with items
    for i in range(num_sales):
        # Create sale items from products
        items = []
        for j, product in enumerate(products[:2]):  # Use first 2 products
            items.append(create_sale_item(
                product_id=product.id,
                product_code=product.code,
                product_description=product.description,
                quantity=Decimal(str(j + 1)),  # Quantity 1 for first item, 2 for second
                unit_price=product.sell_price
            ))
        
        # Create a sale with those items
        sale = create_sale(
            timestamp=datetime.now() - timedelta(days=i),
            items=items,
            customer_id=customer.id if customer else None,
            payment_type="Efectivo"
        )
        
        # Add the sale to the repository
        sale = sale_repo.add(sale)
        sales.append(sale)
    
    return sales

def setup_invoice_data(session: Session, sales: List[Sale], customer: Optional[Customer] = None) -> List[Invoice]:
    """
    Set up invoice data for sales.
    
    Args:
        session: SQLAlchemy session
        sales: List of sales to create invoices for
        customer: Optional customer for the invoices
        
    Returns:
        List of created invoices
    """
    invoice_repo = SqliteInvoiceRepository(session)
    invoices = []
    
    # Create an invoice for each sale
    for i, sale in enumerate(sales):
        # Create customer details dict
        customer_details = {}
        if customer:
            customer_details = {
                "name": customer.name,
                "cuit": customer.cuit,
                "address": customer.address,
                "iva_condition": customer.iva_condition or "Consumidor Final"
            }
        
        # Calculate invoice amounts based on sale
        subtotal = sum(item.quantity * item.unit_price for item in sale.items)
        iva_amount = subtotal * Decimal("0.21")  # Example tax rate
        total = subtotal + iva_amount
        
        # Create invoice
        invoice = create_invoice(
            sale_id=sale.id,
            customer_id=customer.id if customer else None,
            invoice_number=f"B-0001-{1000+i:08d}",
            invoice_date=sale.timestamp,
            customer_details=customer_details,
            subtotal=subtotal,
            iva_amount=iva_amount,
            total=total
        )
        
        # Add invoice to repository
        invoice = invoice_repo.add(invoice)
        invoices.append(invoice)
    
    return invoices

def setup_purchase_order_data(
    session: Session, 
    products: List[Product], 
    supplier: Optional[Supplier] = None
) -> PurchaseOrder:
    """
    Set up purchase order data for testing.
    
    Args:
        session: SQLAlchemy session
        products: List of products to include in the order
        supplier: Optional supplier for the order
        
    Returns:
        Created purchase order
    """
    # Create repositories
    supplier_repo = SqliteSupplierRepository(session)
    po_repo = SqlitePurchaseOrderRepository(session)
    
    # Create a supplier if not provided
    if not supplier:
        supplier = supplier_repo.add(create_supplier())
    
    # Create purchase order items
    items = []
    for product in products:
        items.append(PurchaseOrderItem(
            product_id=product.id,
            product_code=product.code,
            product_description=product.description,
            quantity_ordered=10.0,
            cost_price=float(product.cost_price),
            quantity_received=0.0
        ))
    
    # Create purchase order
    purchase_order = create_purchase_order(
        supplier_id=supplier.id,
        order_date=datetime.now(),
        items=items,
        status="PENDING"
    )
    
    # Add to repository
    purchase_order = po_repo.add(purchase_order)
    return purchase_order

def setup_complete_test_environment(session: Session) -> Dict[str, Any]:
    """
    Set up a complete test environment with all related entities.
    
    This function creates a comprehensive set of test data including:
    - Departments and products
    - Customers
    - Sales with items
    - Invoices
    - Supplier and purchase orders
    
    Args:
        session: SQLAlchemy session
        
    Returns:
        Dictionary containing all created entities for easy access
    """
    # Set up departments and products
    department, products = setup_basic_product_data(session)
    
    # Set up customers
    customers = setup_customer_data(session, num_customers=2)
    
    # Set up supplier
    supplier_repo = SqliteSupplierRepository(session)
    supplier = supplier_repo.add(create_supplier())
    
    # Set up sales for first customer
    sales = setup_sale_data(session, products, customers[0], num_sales=2)
    
    # Set up invoices for those sales
    invoices = setup_invoice_data(session, sales, customers[0])
    
    # Set up purchase order
    purchase_order = setup_purchase_order_data(session, products, supplier)
    
    # Return all created entities
    return {
        "department": department,
        "products": products,
        "customers": customers,
        "supplier": supplier,
        "sales": sales,
        "invoices": invoices,
        "purchase_order": purchase_order
    } 