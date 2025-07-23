"""
Test data management module.

This module provides standardized fixtures and factory methods for test data creation.
It centralizes common test data patterns for reuse across the test suite.
"""
import uuid
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Callable

# Import core models
from core.models.product import Product, Department
from core.models.customer import Customer
from core.models.sale import Sale, SaleItem
from core.models.invoice import Invoice
from core.models.user import User
from core.models.enums import PaymentType
# from core.models.supplier import Supplier
# from core.models.purchase import PurchaseOrder, PurchaseOrderItem

# Factory methods for creating test entities
def create_department(
    id: Optional[int] = None,
    name: str = "Test Department"
) -> Department:
    """Create a department with default test values."""
    return Department(
        id=id,
        name=name
    )

def create_product(
    id: Optional[int] = None,
    code: str = "TST001",
    description: str = "Test Product",
    sell_price: Decimal = Decimal("10.00"),
    cost_price: Decimal = Decimal("5.00"),
    department_id: Optional[int] = None,
    tax_rate: Decimal = Decimal("0.21"),
    is_active: bool = True
) -> Product:
    """Create a product with default test values."""
    return Product(
        id=id,
        code=code,
        description=description,
        sell_price=sell_price,
        cost_price=cost_price,
        department_id=department_id,
        tax_rate=tax_rate,
        is_active=is_active
    )

def create_customer(
    id: Optional[uuid.UUID] = None,
    name: str = "Test Customer",
    phone: Optional[str] = "555-1234",
    email: Optional[str] = "test@example.com",
    address: Optional[str] = "123 Test St",
    cuit: Optional[str] = "20123456789",
    iva_condition: Optional[str] = "Consumidor Final",
    credit_limit: Decimal = Decimal('1000.0'),
    credit_balance: Decimal = Decimal('0.0'),
    is_active: bool = True
) -> Customer:
    """Create a customer with default test values."""
    return Customer(
        id=id or uuid.uuid4(),
        name=name,
        phone=phone,
        email=email,
        address=address,
        cuit=cuit,
        iva_condition=iva_condition,
        credit_limit=credit_limit,
        credit_balance=credit_balance,
        is_active=is_active
    )

def create_sale_item(
    id: Optional[int] = None,
    sale_id: Optional[int] = None,
    product_id: int = 1,
    product_code: str = "TST001",
    product_description: str = "Test Product",
    quantity: Decimal = Decimal("1"),
    unit_price: Decimal = Decimal("10.00")
) -> SaleItem:
    """Create a sale item with default test values."""
    return SaleItem(
        id=id,
        sale_id=sale_id,
        product_id=product_id,
        product_code=product_code,
        product_description=product_description,
        quantity=quantity,
        unit_price=unit_price
    )

def create_sale(
    id: Optional[int] = None,
    timestamp: datetime = None,
    items: List[SaleItem] = None,
    customer_id: Optional[int] = None,
    is_credit_sale: bool = False,
    user_id: Optional[int] = None,
    payment_type: Optional[PaymentType] = PaymentType.EFECTIVO
) -> Sale:
    """Create a sale with default test values."""
    if timestamp is None:
        timestamp = datetime.now()
    
    if items is None:
        # Create a default sale item
        items = [create_sale_item()]
        
    return Sale(
        id=id,
        timestamp=timestamp,
        items=items,
        customer_id=customer_id,
        is_credit_sale=is_credit_sale,
        user_id=user_id,
        payment_type=payment_type
    )

def create_invoice(
    id: Optional[int] = None,
    sale_id: int = 1,
    customer_id: Optional[int] = None,
    invoice_number: Optional[str] = "B-0001-00000001",
    invoice_date: datetime = None,
    invoice_type: str = "B",
    customer_details: Dict[str, Any] = None,
    subtotal: Decimal = Decimal("10.00"),
    iva_amount: Decimal = Decimal("2.10"),
    total: Decimal = Decimal("12.10"),
    iva_condition: str = "Consumidor Final"
) -> Invoice:
    """Create an invoice with default test values."""
    if invoice_date is None:
        invoice_date = datetime.now()
        
    if customer_details is None:
        customer_details = {
            "name": "Test Customer",
            "cuit": "20123456789",
            "address": "123 Test St",
            "iva_condition": "Consumidor Final"
        }
        
    return Invoice(
        id=id,
        sale_id=sale_id,
        customer_id=customer_id,
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        invoice_type=invoice_type,
        customer_details=customer_details,
        subtotal=subtotal,
        iva_amount=iva_amount,
        total=total,
        iva_condition=iva_condition
    )

def create_user(
    id: Optional[int] = None,
    username: str = "testuser",
    password_hash: str = "$2b$12$test_hash_for_testing_only",
    email: Optional[str] = "testuser@example.com",
    is_active: bool = True,
    is_admin: bool = False
) -> User:
    """Create a user with default test values."""
    return User(
        id=id,
        username=username,
        password_hash=password_hash,
        email=email,
        is_active=is_active,
        is_admin=is_admin
    )

# Test Data Builder classes for complex object creation
class ProductBuilder:
    """
    Builder for creating Product test instances with flexible configuration.
    Useful for complex test scenarios requiring specific product setups.
    """
    def __init__(self):
        self.id = None
        self.code = "TST001"
        self.description = "Test Product"
        self.sell_price = Decimal("10.00")
        self.cost_price = Decimal("5.00")
        self.department_id = None
        self.tax_rate = Decimal("0.21")
        self.is_active = True
        
    def with_id(self, id: int):
        self.id = id
        return self
        
    def with_code(self, code: str):
        self.code = code
        return self
        
    def with_description(self, description: str):
        self.description = description
        return self
        
    def with_prices(self, sell_price: Decimal, cost_price: Decimal):
        self.sell_price = sell_price
        self.cost_price = cost_price
        return self
        
    def with_department(self, department_id: int):
        self.department_id = department_id
        return self
        
    def inactive(self):
        self.is_active = False
        return self
        
    def build(self) -> Product:
        return Product(
            id=self.id,
            code=self.code,
            description=self.description,
            sell_price=self.sell_price,
            cost_price=self.cost_price,
            department_id=self.department_id,
            tax_rate=self.tax_rate,
            is_active=self.is_active
        )

class SaleBuilder:
    """
    Builder for creating Sale test instances with flexible configuration.
    Useful for complex test scenarios requiring specific sale setups.
    """
    def __init__(self):
        self.id = None
        self.timestamp = datetime.now()
        self.items = []
        self.customer_id = None
        self.is_credit_sale = False
        self.user_id = None
        self.payment_type = PaymentType.EFECTIVO
        
    def with_id(self, id: int):
        self.id = id
        return self
        
    def with_timestamp(self, timestamp: datetime):
        self.timestamp = timestamp
        return self
        
    def with_item(self, item: SaleItem):
        self.items.append(item)
        return self
        
    def with_product(self, product_id: int, quantity: Decimal, unit_price: Decimal, 
                    product_code: str = "TEST", product_description: str = "Test Product"):
        item = SaleItem(
            product_id=product_id, 
            quantity=quantity,
            unit_price=unit_price,
            product_code=product_code,
            product_description=product_description
        )
        self.items.append(item)
        return self
        
    def with_customer(self, customer_id: int):
        self.customer_id = customer_id
        return self
        
    def as_credit_sale(self):
        self.is_credit_sale = True
        self.payment_type = PaymentType.CREDITO
        return self
        
    def with_payment_type(self, payment_type: PaymentType):
        self.payment_type = payment_type
        return self
        
    def with_user(self, user_id: int):
        self.user_id = user_id
        return self
        
    def build(self) -> Sale:
        # If no items were added, create a default one
        if not self.items:
            self.with_product(1, Decimal("1"), Decimal("10.00"))
            
        return Sale(
            id=self.id,
            timestamp=self.timestamp,
            items=self.items,
            customer_id=self.customer_id,
            is_credit_sale=self.is_credit_sale,
            user_id=self.user_id,
            payment_type=self.payment_type
        )

# Pytest fixtures for test classes
@pytest.fixture
def test_department():
    """Fixture that returns a test department."""
    return create_department()

@pytest.fixture
def test_product(test_department):
    """Fixture that returns a test product linked to the test department."""
    return create_product(department_id=test_department.id if test_department.id else 1)

@pytest.fixture
def test_customer():
    """Fixture that returns a test customer."""
    return create_customer()

@pytest.fixture
def test_sale():
    """Fixture that returns a test sale with one item."""
    return create_sale()

@pytest.fixture
def test_invoice(test_sale, test_customer):
    """Fixture that returns a test invoice linked to the test sale and customer."""
    return create_invoice(
        sale_id=test_sale.id if test_sale.id else 1,
        customer_id=test_customer.id.int if test_customer.id else None
    )

@pytest.fixture
def test_user():
    """Fixture that returns a test user."""
    return create_user()

@pytest.fixture
def test_data_factory(clean_db):
    """
    Fixture for creating standardized test data.
    
    Returns a factory object with methods to create standard test entities
    like products, customers, sales, etc. with customizable properties.
    
    Example usage:
    ```
    def test_something(test_data_factory):
        # Create a standard product
        product = test_data_factory.create_product()
        
        # Create a product with custom properties
        custom_product = test_data_factory.create_product(
            code="CUSTOM1",
            description="Custom Product",
            sell_price=150.00
        )
    ```
    """
    from core.models.product import Product
    from core.models.customer import Customer
    from core.models.sale import Sale, SaleItem
    from core.models.user import User
    from infrastructure.persistence.sqlite.repositories import (
        SqliteProductRepository,
        SqliteCustomerRepository,
        SqliteSaleRepository,
        SqliteUserRepository
    )
    
    session = clean_db
    product_repo = SqliteProductRepository(session)
    customer_repo = SqliteCustomerRepository(session)
    sale_repo = SqliteSaleRepository(session)
    user_repo = SqliteUserRepository(session)
    
    class TestDataFactory:
        def create_product(self, **kwargs):
            """Create a test product with default or custom properties."""
            defaults = {
                "code": "TEST001",
                "description": "Test Product",
                "cost_price": 80.00,
                "sell_price": 100.00,
                "department_id": None,
                "quantity_in_stock": 10,
                "min_stock": 1
            }
            # Override defaults with any provided kwargs
            defaults.update(kwargs)
            product = Product(**defaults)
            product = product_repo.add(product)
            session.commit()
            return product
            
        def create_customer(self, **kwargs):
            """Create a test customer with default or custom properties."""
            defaults = {
                "name": "Test Customer",
                "address": "123 Test St",
                "cuit": "20123456789",
                "iva_condition": "Responsable Inscripto",
                "email": "test@example.com",
                "phone": "1234567890"
            }
            # Override defaults with any provided kwargs
            defaults.update(kwargs)
            customer = Customer(**defaults)
            customer = customer_repo.add(customer)
            session.commit()
            return customer
        
        def create_user(self, **kwargs):
            """Create a test user with default or custom properties."""
            defaults = {
                "username": "testuser",
                "password_hash": "$2b$12$test_hash_for_testing_only",
                "is_active": True
            }
            # Override defaults with any provided kwargs
            defaults.update(kwargs)
            user = User(**defaults)
            user = user_repo.add(user)
            session.commit()
            return user
            
        def create_sale(self, products=None, customer=None, **kwargs):
            """
            Create a test sale with provided products and customer.
            
            If products or customer are not provided, they will be created.
            """
            from datetime import datetime
            
            # Create customer if not provided
            if customer is None:
                customer = self.create_customer()
                
            # Create a default product if not provided
            if products is None:
                products = [self.create_product()]
                
            # Create sale items from products
            sale_items = []
            for product in products:
                sale_items.append(SaleItem(
                    product_id=product.id,
                    product_code=product.code,
                    product_description=product.description,
                    quantity=1,
                    unit_price=product.sell_price
                ))
                
            # Create the sale
            defaults = {
                "timestamp": datetime.now(),
                "customer_id": customer.id,
                "items": sale_items
            }
            # Override defaults with any provided kwargs
            defaults.update(kwargs)
            sale = Sale(**defaults)
            sale = sale_repo.add_sale(sale)
            session.commit()
            return sale
    
    return TestDataFactory()