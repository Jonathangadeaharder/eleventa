import threading
import pytest
import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
    # Create a temporary file for the test database
    temp_db_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db_file.close()
    
    # Create file-based SQLite DB for integration test with check_same_thread=False
    db_url = f"sqlite:///{temp_db_file.name}?check_same_thread=False"
    engine = create_engine(db_url)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create a session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    # Cleanup
    session.close()
    engine.dispose()  # Properly close all connections
    
    # Give the system a moment to release file handles
    import time
    time.sleep(0.1)
    
    # Delete the temporary file
    try:
        if os.path.exists(temp_db_file.name):
            os.unlink(temp_db_file.name)
    except (PermissionError, OSError) as e:
        print(f"Warning: Could not delete temporary database file: {e}")
        # This is not critical for test success

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
        invoice_repo_factory=lambda session=None: repositories["invoice_repo"],
        sale_repo_factory=lambda session=None: repositories["sale_repo"],
        customer_repo_factory=lambda session=None: repositories["customer_repo"],
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
    # Create a customer and sale
    customer, sale = create_customer_and_sale(
        db_session, repositories["sale_repo"], repositories["customer_repo"]
    )
    
    # Commit the session to ensure data is visible to all threads
    db_session.commit()
    
    # The shared connection will work across threads with check_same_thread=False
    results = []
    errors = []
    
    def create_invoice():
        # Use a new session per thread but with same engine
        thread_session = sessionmaker(bind=db_session.get_bind())()
        try:
            # Create repositories with the thread-specific session
            thread_repos = {
                "invoice_repo": SqliteInvoiceRepository(thread_session),
                "sale_repo": SqliteSaleRepository(thread_session),
                "customer_repo": SqliteCustomerRepository(thread_session)
            }
            
            # Create a service with thread-safe repositories
            thread_service = InvoicingService(
                invoice_repo_factory=lambda session=None: thread_repos["invoice_repo"],
                sale_repo_factory=lambda session=None: thread_repos["sale_repo"],
                customer_repo_factory=lambda session=None: thread_repos["customer_repo"]
            )
            
            # Try to create an invoice
            inv = thread_service.create_invoice_from_sale(sale.id)
            if inv:
                thread_session.commit()  # Important: commit the successful creation
                results.append(inv)
        except Exception as e:
            thread_session.rollback()  # Important: rollback on error
            errors.append(str(e))
        finally:
            thread_session.close()

    # Create and start threads
    threads = [threading.Thread(target=create_invoice) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Only one invoice should be created, others should raise duplicate invoice error
    assert len([r for r in results if r is not None]) == 1
    print("Errors:", errors)
    assert any(
        "already has an invoice" in e.lower() or
        "already exists" in e.lower() or
        "duplicate" in e.lower()
        for e in errors
    ), f"Expected an error message containing 'already has an invoice', 'already exists', or 'duplicate', but got: {errors}"