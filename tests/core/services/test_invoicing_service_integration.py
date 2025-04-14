import threading
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers

from infrastructure.persistence.sqlite.database import Base
from infrastructure.persistence.sqlite.repositories import (
    SqliteInvoiceRepository,
    SqliteSaleRepository,
    SqliteCustomerRepository,
)
from core.services.invoicing_service import InvoicingService
from core.models.customer import Customer
from core.models.sale import Sale, SaleItem
from core.models.product import Product
from infrastructure.persistence.sqlite.models_mapping import ProductOrm
from decimal import Decimal

@pytest.fixture(scope="function")
def db_session():
    # In-memory SQLite DB for integration test
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    clear_mappers()

@pytest.fixture
def repositories(db_session):
    return {
        "invoice_repo": SqliteInvoiceRepository(db_session),
        "sale_repo": SqliteSaleRepository(db_session),
        "customer_repo": SqliteCustomerRepository(db_session),
    }

@pytest.fixture
def invoicing_service(repositories):
    return InvoicingService(
        repositories["invoice_repo"],
        repositories["sale_repo"],
        repositories["customer_repo"],
    )

def create_customer_and_sale(db_session, sale_repo, customer_repo):
    # Create a customer
    customer = Customer(
        name="Test Customer",
        address="123 Test St",
        phone="555-1234",
        email="test@example.com",
        iva_condition="Responsable Inscripto",
        cuit="20-12345678-9",
        credit_balance=0.0,
    )
    print(f"[TEST DEBUG] customer.id={customer.id} (type={type(customer.id)})")
    customer = customer_repo.add(customer)
    # Create and persist a product
    product = ProductOrm(
        code="P001",
        description="Test Product",
        cost_price=50.0,
        sell_price=100.0,
        department_id=None,
        quantity_in_stock=10.0,
        min_stock=1.0,
        is_active=True,
    )
    db_session.add(product)
    db_session.flush()
    sale_item = SaleItem(
        product_id=product.id,
        quantity=Decimal("2"),
        unit_price=Decimal("100.00"),
        product_code=product.code,
        product_description=product.description,
    )
    sale = Sale(
        id=None,
        customer_id=customer.id,
        items=[sale_item],
        payment_type="cash",
    )
    sale = sale_repo.add_sale(sale)
    return customer, sale

def test_create_invoice_integration(db_session, repositories, invoicing_service):
    customer, sale = create_customer_and_sale(
        db_session, repositories["sale_repo"], repositories["customer_repo"]
    )
    invoice = invoicing_service.create_invoice_from_sale(sale.id)
    assert invoice is not None
    assert invoice.sale_id == sale.id
    # Check invoice is persisted
    persisted = repositories["invoice_repo"].get_by_id(invoice.id)
    assert persisted is not None

def test_concurrent_invoice_creation(db_session, repositories):
    customer, sale = create_customer_and_sale(
        db_session, repositories["sale_repo"], repositories["customer_repo"]
    )
    service = InvoicingService(
        repositories["invoice_repo"],
        repositories["sale_repo"],
        repositories["customer_repo"],
    )
    results = []
    errors = []

    def create_invoice():
        try:
            inv = service.create_invoice_from_sale(sale.id)
            results.append(inv)
        except Exception as e:
            errors.append(str(e))

    threads = [threading.Thread(target=create_invoice) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Only one invoice should be created, others should raise duplicate invoice error
    assert len([r for r in results if r is not None]) == 1
    assert any("already exists" in e or "duplicate" in e.lower() for e in errors)