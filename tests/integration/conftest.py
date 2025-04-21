"""
Pytest configuration file for integration tests.

This file contains fixtures specifically for integration tests,
including authenticated users, mock services, and standardized
test database setup and teardown.
"""
import pytest
from unittest.mock import MagicMock
import sys
import os
from contextlib import contextmanager

# Add project root to path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from infrastructure.persistence.sqlite.repositories import SqliteUserRepository
from core.services.user_service import UserService
from core.models.user import User

# Import fixtures from the fixtures directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../fixtures")))
try:
    from external_service_mocks import mock_http_client, mock_file_system, mock_external_services
except ImportError:
    # Create mock functions if they don't exist
    @pytest.fixture
    def mock_http_client():
        return MagicMock()
        
    @pytest.fixture
    def mock_file_system():
        return MagicMock()
        
    @pytest.fixture
    def mock_external_services():
        return {"http": MagicMock(), "filesystem": MagicMock()}


@pytest.fixture(scope="function")
def clean_db():
    """
    Provide a clean database session for each test.
    
    This fixture:
    1. Drops all existing tables defined in Base.metadata
    2. Creates all tables defined in Base.metadata for an in-memory SQLite database
    3. Initializes the schema
    4. Yields the session for test use
    5. Rolls back any uncommitted changes after the test
    
    All integration tests should use this fixture to ensure proper
    database isolation between tests.
    """
    from infrastructure.persistence.sqlite.database import SessionLocal, engine, Base, create_all_tables
    
    # Drop all tables first to ensure a clean state for each test function
    Base.metadata.drop_all(bind=engine)
    
    # Create tables anew
    create_all_tables(engine)
    
    # Create a session
    session = SessionLocal()
    
    try:
        yield session
    finally:
        # Roll back any changes made within the session during the test
        session.rollback()
        session.close()
        # Optional: Clean up tables after test if needed, though dropping at the start is usually sufficient
        # Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user():
    """
    Create a simple test user without hitting the database.
    
    This is useful for tests that just need a user object but don't need
    to verify database authentication logic.
    """
    return User(
        id=999,
        username="testuser",
        password_hash="$2b$12$test_hash_for_testing_only"
    )


@pytest.fixture
def authenticated_user(clean_db):
    """
    Provide a real authenticated user from the test database.
    
    Creates a test user if it doesn't exist, or retrieves an existing one.
    """
    session = clean_db
    user_repo = SqliteUserRepository(session)
    user_service = UserService(user_repo)
    
    # Try to get the test user
    test_user = user_service.get_user_by_username("testuser")
    if not test_user:
        # Create a new test user if one doesn't exist
        test_user = user_service.add_user("testuser", "password123")
    
    # Make sure the user is committed to the database
    session.commit()
    return test_user


@pytest.fixture
def mock_services():
    """
    Provide mock services for testing.
    
    This avoids hitting the database completely for pure unit tests.
    """
    services = {
        'product_service': MagicMock(),
        'inventory_service': MagicMock(),
        'sale_service': MagicMock(),
        'customer_service': MagicMock(),
        'purchase_service': MagicMock(),
        'invoicing_service': MagicMock(),
        'corte_service': MagicMock(),
        'reporting_service': MagicMock(),
        'user_service': MagicMock()
    }
    
    # Setup the user service mock to return a test user
    test_user = User(id=1, username="mockuser", password_hash="mock_hash")
    services['user_service'].authenticate.return_value = test_user
    services['user_service'].get_user_by_username.return_value = test_user
    
    return services


@pytest.fixture
def test_app(clean_db, authenticated_user, mock_external_services):
    """
    Set up a complete application environment for integration tests.
    
    This fixture:
    1. Initializes the database
    2. Creates a test user
    3. Sets up external services mocks
    4. Creates required repositories and services
    
    This is useful for end-to-end tests that need to verify
    the complete application flow.
    
    Returns:
        dict: Dictionary containing app components, services, and session
    """
    from core.services.product_service import ProductService
    from core.services.customer_service import CustomerService
    from core.services.sale_service import SaleService
    from core.services.invoicing_service import InvoicingService
    from infrastructure.persistence.sqlite.repositories import (
        SqliteProductRepository,
        SqliteCustomerRepository,
        SqliteSaleRepository,
        SqliteInvoiceRepository
    )
    
    session = clean_db
    
    # Create repositories with the session
    product_repo = SqliteProductRepository(session)
    customer_repo = SqliteCustomerRepository(session)
    sale_repo = SqliteSaleRepository(session)
    invoice_repo = SqliteInvoiceRepository(session)
    
    # Create repository factories for services that need them
    @contextmanager
    def get_session_context():
        try:
            yield session
        finally:
            # Don't actually commit in tests
            pass
            
    def product_repo_factory(session):
        return SqliteProductRepository(session)
        
    def customer_repo_factory(session):
        return SqliteCustomerRepository(session)
        
    def sale_repo_factory(session):
        return SqliteSaleRepository(session)
        
    def credit_payment_repo_factory(session):
        # Mock for now since it's not central to most tests
        return MagicMock()

    def department_repo_factory(session):
        from infrastructure.persistence.sqlite.repositories import SqliteDepartmentRepository
        return SqliteDepartmentRepository(session)
    
    # Create services
    product_service = ProductService(
        product_repo_factory=product_repo_factory, 
        department_repo_factory=department_repo_factory
    )
    
    customer_service = CustomerService(
        customer_repo_factory=customer_repo_factory,
        credit_payment_repo_factory=credit_payment_repo_factory
    )
    
    # Mock inventory service for simplicity
    inventory_service = MagicMock()
    
    sale_service = SaleService(
        sale_repository_factory=sale_repo_factory,
        product_repository_factory=product_repo_factory,
        inventory_service=inventory_service,
        customer_service=customer_service
    )
    
    invoicing_service = InvoicingService(
        invoice_repo=invoice_repo,
        sale_repo=sale_repo,
        customer_repo=customer_repo
    )
    
    # Return all components needed for integration tests
    return {
        "session": session,
        "user": authenticated_user,
        "repositories": {
            "product_repo": product_repo,
            "customer_repo": customer_repo,
            "sale_repo": sale_repo,
            "invoice_repo": invoice_repo
        },
        "services": {
            "product_service": product_service,
            "customer_service": customer_service,
            "sale_service": sale_service,
            "invoicing_service": invoicing_service,
            "inventory_service": inventory_service
        },
        "external": mock_external_services,
        "get_session": get_session_context
    }


# Standardized fixture for creating test data factories
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
    from infrastructure.persistence.sqlite.repositories import (
        SqliteProductRepository,
        SqliteCustomerRepository,
        SqliteSaleRepository
    )
    
    session = clean_db
    product_repo = SqliteProductRepository(session)
    customer_repo = SqliteCustomerRepository(session)
    sale_repo = SqliteSaleRepository(session)
    
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