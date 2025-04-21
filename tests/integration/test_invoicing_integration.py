"""
Integration tests for the invoice system.

These tests verify that all components interact correctly together
including service classes and repositories with actual database sessions.

The test suite focuses on:
- Complete invoice lifecycle from sale to PDF generation
- Database persistence with actual repository implementations
- Service coordination between sale, customer, and invoice services

Test setup:
- Uses the clean_db fixture for database isolation
- Creates test customers, products and sales for each test
- Tests actual PDF generation with temporary files

Coverage goals:
- Test successful paths for all main invoicing workflows
- Verify data integrity across service boundaries
- Test file generation with real data
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
import os

from core.services.invoicing_service import InvoicingService
from core.services.sale_service import SaleService
from core.services.customer_service import CustomerService
from core.models.customer import Customer
from core.models.sale import Sale, SaleItem
from core.models.product import Product

from infrastructure.persistence.sqlite.repositories import (
    SqliteInvoiceRepository,
    SqliteSaleRepository,
    SqliteCustomerRepository,
    SqliteProductRepository,
)


class TestInvoicingIntegration:
    """Integration tests for the invoicing system with actual repositories."""

    @pytest.fixture
    def customer(self, clean_db):
        """
        Create or retrieve a test customer.

        This fixture:
        - Checks if a customer with the test CUIT already exists in the session.
        - If exists, returns the existing customer.
        - If not, creates a new customer with valid test data, persists it, and returns it.

        Dependencies:
        - Requires clean_db fixture for a database session
        """
        session = clean_db
        customer_repo = SqliteCustomerRepository(session)
        cuit_to_find = "20123456789"

        # Try to find existing customer first
        existing_customer = customer_repo.get_by_cuit(cuit_to_find) # Assuming get_by_cuit exists
        if existing_customer:
            return existing_customer

        # If not found, create a new one
        customer = Customer(
            name="Test Customer",
            address="123 Test St",
            cuit=cuit_to_find,
            iva_condition="Responsable Inscripto",
            email="test@example.com",
            phone="1234567890"
        )
        customer = customer_repo.add(customer)
        session.commit() # Commit here after adding
        return customer

    @pytest.fixture
    def product(self, clean_db):
        """
        Create or retrieve a test product.

        This fixture:
        - Checks if a product with the test code already exists.
        - If exists, returns the existing product.
        - If not, creates a new product, persists it, and returns it.

        Dependencies:
        - Requires clean_db fixture for a database session
        """
        session = clean_db
        product_repo = SqliteProductRepository(session)
        code_to_find = "TEST001"

        existing_product = product_repo.get_by_code(code_to_find)
        if existing_product:
            return existing_product

        product = Product(
            code=code_to_find,
            description="Test Product",  # Name is actually in the description field
            cost_price=80.00,
            sell_price=100.00,
            department_id=None,
            quantity_in_stock=10,
            min_stock=1
        )
        product = product_repo.add(product)
        session.commit() # Commit here after adding
        return product

    @pytest.fixture
    def sale(self, clean_db, customer, product):
        """
        Create a test sale. This assumes customer and product are unique per run
        due to the updated fixtures.

        Dependencies:
        - Requires clean_db fixture for a database session
        - Requires updated customer fixture
        - Requires updated product fixture
        """
        session = clean_db
        sale_repo = SqliteSaleRepository(session)

        sale_item = SaleItem(
            product_id=product.id,
            product_code=product.code,
            product_description=product.description, # Product name is in the description field
            quantity=2,
            unit_price=product.sell_price
        )

        sale = Sale(
            timestamp=datetime.now(),
            customer_id=customer.id,
            items=[sale_item]
        )

        # Add sale only if it doesn't exist (assuming no easy way to check by items/timestamp)
        # For simplicity, we'll create a new sale each time this fixture is called.
        # If duplicate sales become an issue, we'd need a more complex check.
        sale = sale_repo.add_sale(sale)
        session.commit() # Commit here after adding
        return sale

    @pytest.fixture
    def services(self, clean_db, customer, product, sale):
        """
        Set up service classes with proper sessions and repositories.
        
        This fixture:
        - Creates all necessary service instances with real repositories
        - Configures services with appropriate factory methods
        - Mocks services not directly related to invoicing
        
        Dependencies:
        - Requires clean_db fixture for a database session
        - Requires customer, product and sale fixtures to be pre-populated
        - Uses repository factory pattern for proper session handling
        
        Returns:
        - Dictionary with configured services and active session
        """
        session = clean_db
        
        # Create repositories with the same session
        invoice_repo = SqliteInvoiceRepository(session)
        sale_repo = SqliteSaleRepository(session)
        customer_repo = SqliteCustomerRepository(session)
        product_repo = SqliteProductRepository(session)
        
        # Create services with repository factory functions (not instances)
        def customer_repo_factory(session):
            return SqliteCustomerRepository(session)
        def credit_payment_repo_factory(session):
            return None  # Or mock if needed
        customer_service = CustomerService(
            customer_repo_factory=customer_repo_factory,
            credit_payment_repo_factory=credit_payment_repo_factory
        )
        
        # Initialize the inventory service with mocks as it's not needed for these tests
        class MockInventoryService:
            def update_stock_from_sale(self, *args, **kwargs):
                pass
        inventory_service = MockInventoryService()
        
        def sale_repo_factory(session):
            return SqliteSaleRepository(session)
        def product_repo_factory(session):
            return SqliteProductRepository(session)
        
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
        
        return {
            "invoicing_service": invoicing_service,
            "sale_service": sale_service,
            "customer_service": customer_service,
            "session": session
        }

    def test_create_invoice_from_sale(self, services, sale):
        """
        Test creating an invoice from a sale and then retrieving it.
        
        This test verifies:
        1. An invoice can be created from an existing sale
        2. The invoice is properly persisted in the database
        3. The invoice can be retrieved by ID and by sale ID
        4. All invoice fields are correctly populated
        """
        invoicing_service = services["invoicing_service"]
        session = services["session"]
        
        # Create invoice from sale
        invoice = invoicing_service.create_invoice_from_sale(sale.id)
        session.commit()
        
        # Verify invoice was created correctly
        assert invoice is not None
        assert invoice.id is not None
        assert invoice.sale_id == sale.id
        assert invoice.invoice_number is not None
        assert "0001-" in invoice.invoice_number
        
        # Test getting the invoice by ID
        retrieved_invoice = invoicing_service.get_invoice_by_id(invoice.id)
        assert retrieved_invoice is not None
        assert retrieved_invoice.id == invoice.id
        
        # Test getting the invoice by sale ID
        by_sale = invoicing_service.get_invoice_by_sale_id(sale.id)
        assert by_sale is not None
        assert by_sale.id == invoice.id

    def test_get_all_invoices(self, services, sale):
        """Test retrieving all invoices - this tests the functionality that failed in production."""
        invoicing_service = services["invoicing_service"]
        session = services["session"]
        
        # Create an invoice
        invoice = invoicing_service.create_invoice_from_sale(sale.id)
        session.commit()
        
        # Get all invoices
        invoices = invoicing_service.get_all_invoices()
        
        # Verify we get back the correct data
        assert invoices is not None
        assert len(invoices) == 1
        assert invoices[0].id == invoice.id
        assert invoices[0].sale_id == sale.id

    def test_generate_invoice_pdf(self, services, sale, tmp_path):
        """Test PDF generation functionality."""
        invoicing_service = services["invoicing_service"]
        session = services["session"]
        
        # Create invoice
        invoice = invoicing_service.create_invoice_from_sale(sale.id)
        session.commit()
        
        # Generate PDF to a temporary path
        pdf_path = os.path.join(tmp_path, f"invoice_{invoice.id}.pdf")
        
        # Use custom store info for testing
        store_info = {
            "name": "Test Store",
            "address": "123 Test Ave",
            "phone": "123-456-7890",
            "cuit": "30123456789",
            "iva_condition": "Responsable Inscripto"
        }
        
        result_path = invoicing_service.generate_invoice_pdf(
            invoice.id, 
            filename=pdf_path,
            store_info=store_info
        )
        
        # Check that PDF was created
        assert os.path.exists(result_path)
        assert os.path.getsize(result_path) > 0 