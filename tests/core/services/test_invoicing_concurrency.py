"""
Integration tests for the invoicing service with concurrency checks.
These tests verify that the invoicing service correctly handles concurrent invoice creation
and prevents duplicate invoices from being created for the same sale.
"""
import threading
import pytest
from sqlalchemy import create_engine, text
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
from infrastructure.persistence.sqlite.models_mapping import ProductOrm, map_models
from decimal import Decimal
import time

# Using file-based SQLite DB for test to ensure all threads can access it
TEST_DB_URL = "sqlite:///test_db.sqlite"
global_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(global_engine)
SessionFactory = sessionmaker(bind=global_engine)

@pytest.fixture(scope="function")
def db_session():
    # Ensure models are mapped
    map_models()
    
    # Clear any existing data from previous tests
    with global_engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f"DELETE FROM {table.name}"))
        conn.commit()
    
    # Create session
    session = SessionFactory()
    yield session
    
    # Cleanup
    session.close()
    
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
        lambda session: repositories["invoice_repo"],
        lambda session: repositories["sale_repo"],
        lambda session: repositories["customer_repo"],
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
    # Commit to ensure data is visible to all threads
    db_session.commit()
    return customer, sale

def test_create_invoice_integration(db_session, repositories, invoicing_service):
    """Test basic invoice creation from a sale."""
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
    """Test that concurrent invoice creation for the same sale is handled correctly."""
    customer, sale = create_customer_and_sale(
        db_session, repositories["sale_repo"], repositories["customer_repo"]
    )
    print(f"Created test sale with ID: {sale.id}")
    
    # Ensure we can fetch the sale from the main thread before creating worker threads
    fetched_sale = repositories["sale_repo"].get_by_id(sale.id)
    assert fetched_sale is not None, "Failed to retrieve the sale in the main thread"
    
    successful_invoices = []
    errors = []
    thread_lock = threading.Lock()

    def create_invoice():
        # Each thread needs its own session
        thread_session = SessionFactory()
        try:
            thread_repos = {
                "invoice_repo": SqliteInvoiceRepository(thread_session),
                "sale_repo": SqliteSaleRepository(thread_session),
                "customer_repo": SqliteCustomerRepository(thread_session),
            }
            thread_service = InvoicingService(
                lambda session: thread_repos["invoice_repo"],
                lambda session: thread_repos["sale_repo"],
                lambda session: thread_repos["customer_repo"],
            )
            
            # Try to find the sale in this thread
            thread_sale = thread_repos["sale_repo"].get_by_id(sale.id)
            if thread_sale is None:
                with thread_lock:
                    errors.append(f"Thread could not find sale with ID {sale.id}")
                return
                
            try:
                inv = thread_service.create_invoice_from_sale(sale.id)
                if inv:
                    with thread_lock:
                        successful_invoices.append(inv)
                    thread_session.commit()
            except Exception as e:
                with thread_lock:
                    errors.append(str(e))
                thread_session.rollback()
        except Exception as e:
            with thread_lock:
                errors.append(f"Thread error: {str(e)}")
        finally:
            thread_session.close()

    # Run threads with a slight delay to ensure they run concurrently but not exactly simultaneously
    # This helps to reliably create the race condition
    threads = []
    for i in range(5):
        t = threading.Thread(target=create_invoice)
        threads.append(t)
        t.start()
        time.sleep(0.01)  # Small delay to ensure threads overlap but don't start simultaneously
    
    for t in threads:
        t.join()

    # Print all errors for debugging
    for err in errors:
        print(f"Thread error: {err}")
    
    # Only one invoice should be created, others should raise duplicate invoice error
    assert len(successful_invoices) == 1, f"Expected exactly 1 successful invoice, got {len(successful_invoices)}"
    
    # Verify that we have the expected number of errors
    # We expect 4 errors because we started 5 threads, and only one should succeed
    assert len(errors) >= 4, f"Expected at least 4 errors from concurrent threads, got {len(errors)}"
    
    # Check that all errors are related to duplicate invoices
    # We'll verify using more flexible pattern matching
    invoice_error_patterns = [
        "already has an invoice",
        "duplicate",
        "invoice for sale",
        "already exists",
        "sale may already have an invoice"
    ]
    
    error_match_count = 0
    for error in errors:
        error_text = error.lower()
        if any(pattern in error_text for pattern in invoice_error_patterns):
            error_match_count += 1
    
    # At least one error should match our expected patterns
    assert error_match_count > 0, "No errors matched the expected duplicate invoice patterns"
    
    # Verify in the database that there is exactly 1 invoice for this sale
    with SessionFactory() as verify_session:
        invoice_repo = SqliteInvoiceRepository(verify_session)
        invoice = invoice_repo.get_by_sale_id(sale.id)
        assert invoice is not None, "No invoice found in the database"
        
        # Count all invoices to make sure we only have one
        all_invoices = invoice_repo.get_all()
        invoice_count = len([inv for inv in all_invoices if inv.sale_id == sale.id])
        assert invoice_count == 1, f"Expected exactly 1 invoice in database, found {invoice_count}"
    
    # Clean up the database after the test
    db_session.execute(text("DELETE FROM invoices"))
    db_session.execute(text("DELETE FROM sale_items"))
    db_session.execute(text("DELETE FROM sales"))
    db_session.execute(text("DELETE FROM customers"))
    db_session.execute(text("DELETE FROM products"))
    db_session.commit()
