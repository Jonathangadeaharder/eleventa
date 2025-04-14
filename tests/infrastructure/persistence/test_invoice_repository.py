import pytest
import datetime
from decimal import Decimal
import time

import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.models.customer import Customer
from core.models.sale import Sale, SaleItem
from core.models.invoice import Invoice
from infrastructure.persistence.compat import (
    SqliteCustomerRepositoryCompat as SqliteCustomerRepository,
    SqliteSaleRepositoryCompat as SqliteSaleRepository,
    SqliteInvoiceRepositoryCompat as SqliteInvoiceRepository
)
from infrastructure.persistence.utils import session_scope
from infrastructure.persistence.sqlite.database import engine, Base
from sqlalchemy import delete
from infrastructure.persistence.sqlite.models_mapping import (
    InvoiceOrm, SaleOrm, CustomerOrm, SaleItemOrm
)

@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Set up the database for each test."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Clear existing data to avoid unique constraint violations
    with session_scope() as session:
        # Delete in correct order to avoid foreign key constraints
        session.execute(delete(InvoiceOrm))
        session.execute(delete(SaleItemOrm))  
        session.execute(delete(SaleOrm))
        session.execute(delete(CustomerOrm))
        session.commit()
    
    yield
    
    # Cleanup after each test
    with session_scope() as session:
        session.execute(delete(InvoiceOrm))
        session.execute(delete(SaleItemOrm))
        session.execute(delete(SaleOrm))
        session.execute(delete(CustomerOrm))
        session.commit()

@pytest.fixture
def customer_repo():
    return SqliteCustomerRepository()

@pytest.fixture
def sale_repo():
    return SqliteSaleRepository()

@pytest.fixture
def invoice_repo():
    return SqliteInvoiceRepository()

def create_sample_customer(customer_repo):
    unique_suffix = str(int(time.time()))
    customer = Customer(
        name="Test Customer",
        address="123 Test St",
        phone="555-1234",
        email="test@example.com",
        cuit=f"20{unique_suffix}",
        iva_condition="Responsable Inscripto"
    )
    return customer_repo.add(customer)

def create_sample_sale(sale_repo, customer_id):
    sale = Sale(
        customer_id=customer_id,
        timestamp=datetime.datetime.now(),
        payment_type="cash"
    )
    
    # Add a simple SaleItem to make the total match
    sale_item = SaleItem(
        product_id=1,
        quantity=Decimal("1"),
        unit_price=Decimal("100.00"),
        product_code="TEST001",
        product_description="Test Product"
    )
    # Set the total_price field by calculating it
    sale_item.total_price = sale_item.quantity * sale_item.unit_price
    sale.items = [sale_item]
    
    return sale_repo.add_sale(sale)

def get_unique_invoice_number():
    unique_suffix = str(int(time.time()))
    return f"A-0001-{unique_suffix}"

def test_add_and_get_invoice(customer_repo, sale_repo, invoice_repo):
    customer = create_sample_customer(customer_repo)
    sale = create_sample_sale(sale_repo, customer.id)
    invoice_number = get_unique_invoice_number()
    invoice = Invoice(
        sale_id=sale.id,
        customer_id=customer.id,
        invoice_number=invoice_number,
        invoice_date=datetime.datetime.now(),
        invoice_type="A",
        customer_details={
            "name": customer.name,
            "cuit": customer.cuit,
            "iva_condition": customer.iva_condition
        },
        subtotal=Decimal("82.64"),
        iva_amount=Decimal("17.36"),
        total=Decimal("100.00"),
        iva_condition=customer.iva_condition,
        cae="12345678901234",
        cae_due_date=datetime.datetime.now() + datetime.timedelta(days=10),
        notes="Test invoice",
        is_active=True
    )
    added_invoice = invoice_repo.add(invoice)
    assert added_invoice is not None
    assert added_invoice.sale_id == sale.id
    assert added_invoice.customer_id == customer.id
    assert added_invoice.invoice_number == invoice_number

    fetched_by_id = invoice_repo.get_by_id(added_invoice.id)
    assert fetched_by_id is not None
    assert fetched_by_id.invoice_number == invoice_number

    fetched_by_sale = invoice_repo.get_by_sale_id(sale.id)
    assert fetched_by_sale is not None
    assert fetched_by_sale.id == added_invoice.id

def test_get_all_invoices(customer_repo, sale_repo, invoice_repo):
    customer = create_sample_customer(customer_repo)
    sale = create_sample_sale(sale_repo, customer.id)
    invoice_number = get_unique_invoice_number()
    invoice = Invoice(
        sale_id=sale.id,
        customer_id=customer.id,
        invoice_number=invoice_number,
        invoice_date=datetime.datetime.now(),
        invoice_type="A",
        customer_details={
            "name": customer.name,
            "cuit": customer.cuit,
            "iva_condition": customer.iva_condition
        },
        subtotal=Decimal("50.00"),
        iva_amount=Decimal("10.50"),
        total=Decimal("60.50"),
        iva_condition=customer.iva_condition,
        cae="98765432109876",
        cae_due_date=datetime.datetime.now() + datetime.timedelta(days=10),
        notes="Another test invoice",
        is_active=True
    )
    invoice_repo.add(invoice)
    all_invoices = invoice_repo.get_all()
    assert any(inv.invoice_number == invoice_number for inv in all_invoices)

def test_duplicate_sale_id_raises_error(customer_repo, sale_repo, invoice_repo):
    customer = create_sample_customer(customer_repo)
    sale = create_sample_sale(sale_repo, customer.id)
    invoice_number1 = get_unique_invoice_number()
    # Wait a moment to ensure unique invoice numbers
    time.sleep(1)
    invoice_number2 = get_unique_invoice_number()
    
    invoice1 = Invoice(
        sale_id=sale.id,
        customer_id=customer.id,
        invoice_number=invoice_number1,
        invoice_date=datetime.datetime.now(),
        invoice_type="A",
        customer_details={
            "name": customer.name,
            "cuit": customer.cuit,
            "iva_condition": customer.iva_condition
        },
        subtotal=Decimal("30.00"),
        iva_amount=Decimal("6.30"),
        total=Decimal("36.30"),
        iva_condition=customer.iva_condition,
        cae="11111111111111",
        cae_due_date=datetime.datetime.now() + datetime.timedelta(days=10),
        notes="Duplicate sale test",
        is_active=True
    )
    invoice_repo.add(invoice1)
    invoice2 = Invoice(
        sale_id=sale.id,  # Same sale_id as invoice1
        customer_id=customer.id,
        invoice_number=invoice_number2,
        invoice_date=datetime.datetime.now(),
        invoice_type="A",
        customer_details={
            "name": customer.name,
            "cuit": customer.cuit,
            "iva_condition": customer.iva_condition
        },
        subtotal=Decimal("30.00"),
        iva_amount=Decimal("6.30"),
        total=Decimal("36.30"),
        iva_condition=customer.iva_condition,
        cae="22222222222222",
        cae_due_date=datetime.datetime.now() + datetime.timedelta(days=10),
        notes="Duplicate sale test 2",
        is_active=True
    )
    with pytest.raises(Exception):
        invoice_repo.add(invoice2)