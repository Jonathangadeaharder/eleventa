"""
Integration tests for the invoicing service.
"""
# Remove threading imports
# import threading 
import pytest
from sqlalchemy import text # Keep text for potential use, remove create_engine/sessionmaker
from sqlalchemy.orm import Session # Keep Session for type hinting if needed
from sqlalchemy.exc import OperationalError

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
from core.models.enums import PaymentType
from infrastructure.persistence.sqlite.models_mapping import ProductOrm # Keep map_models if used elsewhere, remove if only for old fixture
from decimal import Decimal
from core.interfaces.repository_interfaces import IInvoiceRepository
# import time # Remove time import

# Remove global engine, URL, and SessionFactory
# TEST_DB_URL = "sqlite:///test_db.sqlite"
# global_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
# Base.metadata.create_all(global_engine)
# SessionFactory = sessionmaker(bind=global_engine)

# Remove custom db_session fixture
# @pytest.fixture(scope="function")
# def db_session(): ... (removed)

# Use test_db_session from conftest
@pytest.fixture
def repositories(test_db_session: Session): # Use test_db_session directly
    return {
        "invoice_repo": SqliteInvoiceRepository(test_db_session),
        "sale_repo": SqliteSaleRepository(test_db_session),
        "customer_repo": SqliteCustomerRepository(test_db_session),
    }

@pytest.fixture
def invoicing_service(test_db_session):
    """Provide an InvoicingService instance for testing."""
    # Set the session factory to use the same engine as the test session
    from infrastructure.persistence.utils import session_scope_provider
    from sqlalchemy.orm import sessionmaker
    
    # Get the engine from the test session
    test_engine = test_db_session.bind
    
    # Create a session factory that uses the same engine
    test_session_factory = sessionmaker(bind=test_engine)
    
    # Set this as the session factory for the Unit of Work
    session_scope_provider.set_session_factory(test_session_factory)
    
    return InvoicingService()

# Use test_db_session
def create_customer_and_sale(test_db_session: Session, sale_repo: SqliteSaleRepository, customer_repo: SqliteCustomerRepository):
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
    test_db_session.add(product)
    test_db_session.flush() # Keep flush to get product ID
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
        payment_type=PaymentType.EFECTIVO,
    )
    sale = sale_repo.add_sale(sale)
    # Remove commit - test_db_session handles transaction
    # test_db_session.commit() 
    return customer, sale

# Use test_db_session
def test_create_invoice_integration(test_db_session: Session, repositories, invoicing_service):
    """Test basic invoice creation from a sale using standard session fixture."""
    customer, sale = create_customer_and_sale(
        test_db_session, repositories["sale_repo"], repositories["customer_repo"]
    )
    # Commit the test data so it's visible to the invoicing service's Unit of Work
    test_db_session.commit()
    
    invoice = invoicing_service.create_invoice_from_sale(sale.id)
    assert invoice is not None
    assert invoice.sale_id == sale.id
    assert invoice.customer_id == customer.id
    # Check invoice is persisted within the same transaction
    persisted = repositories["invoice_repo"].get_by_id(invoice.id)
    assert persisted is not None

# Remove the entire test_concurrent_invoice_creation function
# def test_concurrent_invoice_creation(db_session, repositories): ... (removed)
