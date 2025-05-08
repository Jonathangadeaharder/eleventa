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
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sqlalchemy.pool
import uuid
import importlib

# Set TEST_MODE environment variable for all test runs
os.environ["TEST_MODE"] = "true"

# Add project root to path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from infrastructure.persistence.sqlite.repositories import SqliteUserRepository
from core.services.user_service import UserService
from core.models.user import User

# <<< Explicitly import models_mapping here to ensure models are registered with Base >>>
import infrastructure.persistence.sqlite.models_mapping 

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
    Provides a clean in-memory SQLite database with tables created FOR EACH TEST.
    Avoids module reloading by creating engine and session locally.
    """
    import os
    import uuid
    import sqlalchemy.pool
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    # Import necessary ORM models
    # We will get Base via the models_mapping module after it's imported
    # from infrastructure.persistence.sqlite.database import Base 
    from infrastructure.persistence.sqlite.models_mapping import UserOrm
    from core.models.user import User

    # Generate a unique identifier for this test's database
    test_id = f"memdb_{uuid.uuid4().hex}"
    test_db_url = f"sqlite:///file:{test_id}?mode=memory&cache=shared"
    print(f"Creating in-memory DB for test: {test_db_url}")

    # Create a test-specific engine
    test_engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False},
        poolclass=sqlalchemy.pool.StaticPool # Essential for SQLite in-memory
    )
    
    # Create tables using the test engine
    try:
        # Get the Base object that models were registered with via the mapping module
        Base = infrastructure.persistence.sqlite.models_mapping.Base
        
        # Directly create tables using the correct Base's metadata and the test engine
        print(f"Creating tables directly using models_mapping.Base.metadata ({len(Base.metadata.tables)} tables)...")
        Base.metadata.create_all(bind=test_engine)
        print("Tables created successfully.")
    except Exception as e:
        print(f"Error creating tables: {e}")
        raise

    # Create a test-specific session factory bound to the test engine
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # Create a session
    session = TestingSessionLocal()
    
    # --- Create Test User ---
    test_user = User(
        id=999,
        username="testuser",
        password_hash="$2b$12$test_hash_for_testing_only"
    )
    user_orm = UserOrm(
        id=test_user.id,
        username=test_user.username,
        password_hash=test_user.password_hash,
        is_active=True,
        is_admin=False # Ensure is_admin is set if required by schema
    )
    
    try:
        print("Adding test user...")
        session.add(user_orm)
        session.commit()
        print("Test user added and committed.")
    except Exception as e:
        print(f"Error adding test user: {e}")
        session.rollback()
        # It might be useful to inspect the DB state here if errors persist
        raise
    # --- End Test User ---
    
    try:
        # Yield the session and the domain model user
        yield session, test_user 
    finally:
        print("Closing session and dropping tables...")
        session.close()
        # Drop tables using the same test engine and the correct Base metadata
        try:
            # Ensure we use the same Base instance from models_mapping
            Base = infrastructure.persistence.sqlite.models_mapping.Base
            print(f"Dropping tables using models_mapping.Base metadata ({len(Base.metadata.tables)} tables)...")
            Base.metadata.drop_all(bind=test_engine)
            print("Tables dropped.")
        except Exception as e:
            print(f"Error dropping tables: {e}")


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
    
    Retrieves the user created by the clean_db fixture.
    """
    session, user = clean_db # Unpack session and user from clean_db
    # session = clean_db # Old code
    # user_repo = SqliteUserRepository(session)
    # user_service = UserService(user_repo)
    # 
    # # Try to get the test user
    # test_user = user_service.get_user_by_username("testuser")
    # if not test_user:
    #     # Create a new test user if one doesn't exist
    #     test_user = user_service.add_user("testuser", "password123")
    # 
    # # Make sure the user is committed to the database
    # session.commit()
    # return test_user
    return user # Return the user yielded by clean_db


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
    from core.services.service_base import ServiceBase
    from infrastructure.persistence.sqlite.repositories import (
        SqliteProductRepository,
        SqliteCustomerRepository,
        SqliteSaleRepository,
        SqliteInvoiceRepository,
        SqliteDepartmentRepository
    )
    
    # Unpack the clean_db tuple to get the session
    session, _ = clean_db
    
    # Create repository factories for services that may need them
    @contextmanager
    def get_session_context():
        try:
            yield session
        finally:
            # Don't actually commit in tests
            pass
            
    def product_repo_factory(session_arg):
        # ALWAYS use the provided session_arg to ensure we work with the correct transaction
        return SqliteProductRepository(session_arg)
        
    def customer_repo_factory(session_arg):
        # ALWAYS use the provided session_arg to ensure we work with the correct transaction
        return SqliteCustomerRepository(session_arg)
        
    def sale_repo_factory(session_arg):
        # ALWAYS use the provided session_arg to ensure we work with the correct transaction
        return SqliteSaleRepository(session_arg)
        
    def invoice_repo_factory(session_arg):
        # ALWAYS use the provided session_arg to ensure we work with the correct transaction
        return SqliteInvoiceRepository(session_arg)
        
    def credit_payment_repo_factory(session_arg):
        # Mock for now since it's not central to most tests
        return MagicMock()

    def department_repo_factory(session_arg):
        # ALWAYS use the provided session_arg to ensure we work with the correct transaction
        return SqliteDepartmentRepository(session_arg)
    
    # Create a subclass of ServiceBase that overrides _with_session to always use our test session
    class TestServiceBase(ServiceBase):
        def _with_session(self, func, *args, **kwargs):
            """Override _with_session to always use our test session instead of creating a new one."""
            return func(session, *args, **kwargs)
    
    # Create services with our custom ServiceBase implementation
    class TestProductService(ProductService, TestServiceBase):
        pass
        
    class TestCustomerService(CustomerService, TestServiceBase):
        pass
        
    class TestSaleService(SaleService, TestServiceBase):
        pass
        
    class TestInvoicingService(InvoicingService, TestServiceBase):
        pass
    
    # Initialize services with our factories
    product_service = TestProductService(
        product_repo_factory=product_repo_factory, 
        department_repo_factory=department_repo_factory
    )
    
    customer_service = TestCustomerService(
        customer_repo_factory=customer_repo_factory,
        credit_payment_repo_factory=credit_payment_repo_factory
    )
    
    # Mock inventory service for simplicity
    inventory_service = MagicMock()
    
    sale_service = TestSaleService(
        sale_repo_factory=sale_repo_factory,
        product_repo_factory=product_repo_factory,
        customer_repo_factory=customer_repo_factory,
        inventory_service=inventory_service,
        customer_service=customer_service
    )
    
    invoicing_service = TestInvoicingService(
        invoice_repo_factory=invoice_repo_factory,
        sale_repo_factory=sale_repo_factory,
        customer_repo_factory=customer_repo_factory
    )
    
    # Return all components needed for integration tests
    return {
        "session": session,
        "user": authenticated_user,
        "repositories": {
            "product_repo": product_repo_factory(session),
            "customer_repo": customer_repo_factory(session),
            "sale_repo": sale_repo_factory(session),
            "invoice_repo": invoice_repo_factory(session)
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
    from core.models.user import User
    from infrastructure.persistence.sqlite.repositories import (
        SqliteProductRepository,
        SqliteCustomerRepository,
        SqliteSaleRepository,
        SqliteUserRepository
    )
    
    # Unpack the clean_db tuple to get just the session
    session, _ = clean_db
    
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
            session.flush() # Flush to assign ID but don't commit yet
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
            session.flush() # Flush to assign ID but don't commit yet
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
            session.flush() # Flush to assign ID but don't commit yet
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
            session.flush() # Flush to assign ID but don't commit yet
            return sale
    
    return TestDataFactory()


@pytest.fixture
def transactional_tests(clean_db):
    """
    Wrap all tests in a transaction that's rolled back after the test.
    
    This ensures changes made during the test don't persist
    beyond the test, providing better isolation.
    """
    session, _ = clean_db  # Unpack to get the session
    
    # Start a nested transaction (savepoint)
    connection = session.connection()
    transaction = connection.begin_nested()
    
    yield
    
    # Roll back the transaction after the test
    if transaction.is_active:
        transaction.rollback()
    
    # Close the connection
    connection.close()


@pytest.fixture
def direct_repo_services(clean_db):
    """
    Creates services with repository factory functions to match the updated service constructors.
    """
    from core.services.product_service import ProductService
    from core.services.customer_service import CustomerService
    from core.services.sale_service import SaleService
    from core.services.invoicing_service import InvoicingService
    from infrastructure.persistence.sqlite.repositories import (
        SqliteProductRepository,
        SqliteCustomerRepository,
        SqliteSaleRepository,
        SqliteInvoiceRepository,
        SqliteDepartmentRepository,
        SqliteCreditPaymentRepository
    )
    
    # Unpack the clean_db tuple to get the session
    session, _ = clean_db
    
    # Create factory functions that return repositories with the provided session
    def product_repo_factory(session_arg=None):
        return SqliteProductRepository(session_arg or session)
        
    def department_repo_factory(session_arg=None):
        return SqliteDepartmentRepository(session_arg or session)
        
    def customer_repo_factory(session_arg=None):
        return SqliteCustomerRepository(session_arg or session)
        
    def credit_payment_repo_factory(session_arg=None):
        return SqliteCreditPaymentRepository(session_arg or session)
        
    def sale_repo_factory(session_arg=None):
        return SqliteSaleRepository(session_arg or session)
        
    def invoice_repo_factory(session_arg=None):
        return SqliteInvoiceRepository(session_arg or session)
    
    # Create services using factory patterns
    product_service = ProductService(
        product_repo_factory=product_repo_factory,
        department_repo_factory=department_repo_factory
    )
    
    customer_service = CustomerService(
        customer_repo_factory=customer_repo_factory,
        credit_payment_repo_factory=credit_payment_repo_factory
    )
    
    # Mock inventory service
    inventory_service = MagicMock()
    
    sale_service = SaleService(
        sale_repo_factory=sale_repo_factory,
        product_repo_factory=product_repo_factory,
        customer_repo_factory=customer_repo_factory,
        inventory_service=inventory_service,
        customer_service=customer_service
    )
    
    invoicing_service = InvoicingService(
        invoice_repo_factory=invoice_repo_factory,
        sale_repo_factory=sale_repo_factory,
        customer_repo_factory=customer_repo_factory
    )
    
    return {
        "product_service": product_service,
        "customer_service": customer_service,
        "sale_service": sale_service,
        "invoicing_service": invoicing_service,
        "inventory_service": inventory_service,
        "session": session,
        "repositories": {
            "product_repo": product_repo_factory(),
            "department_repo": department_repo_factory(),
            "customer_repo": customer_repo_factory(),
            "sale_repo": sale_repo_factory(),
            "invoice_repo": invoice_repo_factory(),
            "credit_payment_repo": credit_payment_repo_factory()
        }
    }