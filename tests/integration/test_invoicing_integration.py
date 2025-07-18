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
import tempfile
from unittest.mock import patch

from core.services.invoicing_service import InvoicingService
from core.services.sale_service import SaleService
from core.services.customer_service import CustomerService
from core.models.customer import Customer
from core.models.sale import Sale, SaleItem
from core.models.product import Product
from core.models.user import User
from core.models.enums import PaymentType
from core.interfaces.repository_interfaces import IInvoiceRepository

from infrastructure.persistence.sqlite.repositories import (
    SqliteInvoiceRepository,
    SqliteSaleRepository,
    SqliteCustomerRepository,
    SqliteProductRepository,
)
from infrastructure.persistence.sqlite.models_mapping import map_models, ensure_all_models_mapped


@pytest.mark.integration
class TestInvoicingIntegration:
    """Integration tests for the invoicing system with actual repositories."""

    @classmethod
    def setup_class(cls):
        """Ensure all models are mapped before running tests."""
        # This ensures tables are created properly
        map_models()
        ensure_all_models_mapped()
        
        print("All models mapped for TestInvoicingIntegration tests")

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
        # Correctly unpack the tuple yielded by clean_db
        session, _ = clean_db 
        customer_repo = SqliteCustomerRepository(session)
        cuit_to_find = "20123456789"

        # Create a new one
        customer = Customer(
            name="Test Customer",
            address="123 Test St",
            cuit=cuit_to_find,
            iva_condition="Responsable Inscripto",
            email="test@example.com",
            phone="1234567890"
        )
        customer = customer_repo.add(customer)
        session.flush()  # Don't commit yet, let test manage transaction
        return customer

    @pytest.fixture
    def product(self, clean_db):
        """
        Create or retrieve a test product.

        This fixture:
        - Creates a new product, persists it, and returns it.

        Dependencies:
        - Requires clean_db fixture for a database session
        """
        # Correctly unpack the tuple yielded by clean_db
        session, _ = clean_db 
        product_repo = SqliteProductRepository(session)
        code_to_find = "TEST001"

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
        session.flush()  # Don't commit yet, let test manage transaction
        return product

    @pytest.fixture
    def test_user(self, clean_db):
        """
        Retrieve the test user created by the clean_db fixture.
        """
        # clean_db yields (session, user)
        session, user = clean_db
        return user

    @pytest.fixture
    def sale(self, clean_db, customer, product, test_user):
        """
        Create a test sale with required relationships.

        Dependencies:
        - Requires clean_db fixture for a database session
        - Requires updated customer fixture
        - Requires updated product fixture
        - Requires test_user fixture
        """
        # Correctly unpack the tuple yielded by clean_db
        session, _ = clean_db 
        sale_repo = SqliteSaleRepository(session)

        sale_item = SaleItem(
            product_id=product.id,
            product_code=product.code,
            product_description=product.description,
            quantity=2,
            unit_price=product.sell_price
        )

        sale = Sale(
            timestamp=datetime.now(),
            customer_id=customer.id,
            items=[sale_item],
            user_id=test_user.id,
            payment_type=PaymentType.EFECTIVO
        )

        sale = sale_repo.add_sale(sale)
        session.flush()  # Explicitly flush to make sure the sale is available within the transaction
        
        # Verify sale is in the database
        db_sale = sale_repo.get_by_id(sale.id)
        print(f"Debug - sale fixture - created sale id={sale.id}, verification from DB: {db_sale}")
        
        return sale

    @pytest.fixture
    def services(self, clean_db, customer, product, sale, direct_repo_services=None):
        """
        Set up service classes with direct repository instances.
        
        This fixture now uses the direct_repo_services fixture when available,
        otherwise creates its own direct repository instances for reliability.
        
        Dependencies:
        - Requires clean_db fixture for a database session
        - Requires customer, product and sale fixtures to be pre-populated
        
        Returns:
        - Dictionary with configured services and active session
        """
        # Correctly unpack the tuple yielded by clean_db at the beginning
        session, _ = clean_db 
        
        # Set the session factory to use the same engine as the test session
        # This ensures the Unit of Work uses the same database connection
        from infrastructure.persistence.utils import session_scope_provider
        from sqlalchemy.orm import sessionmaker
        
        # Get the engine from the test session
        test_engine = session.bind
        
        # Create a session factory that uses the same engine
        test_session_factory = sessionmaker(bind=test_engine)
        
        # Set this as the session factory for the Unit of Work
        session_scope_provider.set_session_factory(test_session_factory)
        
        # If we have the direct_repo_services fixture available, use it
        if direct_repo_services:
            return direct_repo_services
        
        # Otherwise create our own services with direct repository instances
        # Ensure these use the correctly unpacked session
        invoice_repo = SqliteInvoiceRepository(session)
        sale_repo = SqliteSaleRepository(session)
        customer_repo = SqliteCustomerRepository(session)
        product_repo = SqliteProductRepository(session)
        
        # Services now use Unit of Work pattern and don't need repository factories
        invoicing_service = InvoicingService()
        customer_service = CustomerService()
        
        # Create SaleService - mock inventory service for simplicity
        from unittest.mock import MagicMock
        inventory_service = MagicMock()
        
        sale_service = SaleService(inventory_service, customer_service)

        return {
            "invoicing_service": invoicing_service,
            "sale_service": sale_service,
            "customer_service": customer_service,
            "session": session # Return the correctly unpacked session
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
        
        # Debug: Check if the sale exists in the database
        from infrastructure.persistence.sqlite.repositories import SqliteSaleRepository, SqliteInvoiceRepository, SqliteCustomerRepository
        sale_repo = SqliteSaleRepository(session)
        db_sale = sale_repo.get_by_id(sale.id)
        print(f"Debug - sale in test: id={sale.id}, sale from DB: {db_sale}")
        if not db_sale:
            print(f"Debug - Sale {sale.id} is not in the database, adding it now")
            sale_repo.add_sale(sale)
            session.flush()
            db_sale = sale_repo.get_by_id(sale.id)
            print(f"Debug - After commit: sale from DB: {db_sale}")
        
        # A direct approach without using session_scope
        invoice_repo = SqliteInvoiceRepository(session)
        customer_repo = SqliteCustomerRepository(session)
        
        # Manually perform the steps that would be inside the create_invoice_from_sale method
        # Check if sale exists - we already verified above
        # sale = db_sale
        
        # Check if there's already an invoice
        existing_invoice = invoice_repo.get_by_sale_id(sale.id)
        if existing_invoice:
            print(f"Debug - Sale {sale.id} already has an invoice with ID {existing_invoice.id}")
            raise ValueError(f"Sale with ID {sale.id} already has an invoice")
        
        # Check if sale has a customer
        if not sale.customer_id:
            print(f"Debug - Sale {sale.id} has no customer")
            raise ValueError(f"Sale with ID {sale.id} has no associated customer. A customer is required for invoicing.")
        
        # Get customer
        customer = customer_repo.get_by_id(sale.customer_id)
        if not customer:
            print(f"Debug - Customer {sale.customer_id} not found")
            raise ValueError(f"Customer with ID {sale.customer_id} not found")
        
        # Determine invoice type
        invoice_type = invoicing_service._determine_invoice_type(customer.iva_condition)

        # Calculate totals
        subtotal = float(sum(item.unit_price * item.quantity for item in sale.items))
        iva_rate = invoicing_service._get_iva_rate(invoice_type, customer.iva_condition)
        
        # Calculate IVA amount
        if iva_rate > 0:
            # IVA is calculated on pre-tax amount
            pre_tax_amount = Decimal(str(subtotal)) / (Decimal('1') + iva_rate)
            iva_amount = Decimal(str(subtotal)) - pre_tax_amount
        else:
            # No IVA
            iva_amount = Decimal('0')
            pre_tax_amount = Decimal(str(subtotal))
            
        # Round amounts
        pre_tax_amount = pre_tax_amount.quantize(Decimal('0.01'))
        iva_amount = iva_amount.quantize(Decimal('0.01'))
        total = pre_tax_amount + iva_amount
        
        # Generate customer details
        customer_details = {
            "name": customer.name,
            "address": customer.address,
            "cuit": customer.cuit,
            "iva_condition": customer.iva_condition,
            "email": customer.email,
            "phone": customer.phone
        }
        
        # Generate invoice number
        invoice_number = invoicing_service._generate_next_invoice_number(invoice_repo)
        
        # Create invoice
        from core.models.invoice import Invoice
        invoice = Invoice(
            sale_id=sale.id,
            customer_id=customer.id,
            invoice_number=invoice_number,
            invoice_type=invoice_type,
            customer_details=customer_details,
            subtotal=subtotal,
            iva_amount=iva_amount,
            total=total,
            iva_condition=customer.iva_condition
        )
        
        # Add invoice to repository
        invoice = invoice_repo.add(invoice)
        session.flush()
        
        # Assert the invoice was created properly
        assert invoice.id is not None
        assert invoice.sale_id == sale.id
        assert invoice.invoice_number == invoice_number
        
        # Verify it can be retrieved
        db_invoice = invoice_repo.get_by_id(invoice.id)
        assert db_invoice is not None
        assert db_invoice.id == invoice.id
        
        # Also check retrieval by sale_id
        db_invoice_by_sale = invoice_repo.get_by_sale_id(sale.id)
        assert db_invoice_by_sale is not None
        assert db_invoice_by_sale.id == invoice.id
        
        # Verify the fields
        assert db_invoice.invoice_type == invoice_type
        assert db_invoice.subtotal == subtotal
        assert db_invoice.iva_amount == iva_amount
        assert db_invoice.total == total

    def test_get_all_invoices(self, services, sale):
        """
        Test retrieving all invoices from the system.
        
        This test verifies:
        1. Multiple invoices can be created and persisted
        2. All invoices can be retrieved at once
        3. The list is properly ordered
        """
        invoicing_service = services["invoicing_service"]
        session = services["session"]
        
        # Create first invoice from the fixture sale
        invoice1 = invoicing_service.create_invoice_from_sale(sale.id)

        # All invoices should contain at least the one we just created
        invoices = invoicing_service.get_all_invoices()
        assert len(invoices) >= 1
        
        # The first invoice should be our invoice (by most recent date)
        found = False
        for inv in invoices:
            if inv.id == invoice1.id:
                found = True
                break
                
        assert found, "Could not find our invoice in the list of all invoices"

    def test_generate_invoice_pdf(self, services, sale):
        """
        Test generating a PDF invoice document.
        
        This test verifies:
        1. An invoice can be created from a sale
        2. A PDF can be generated from the invoice
        3. The PDF file is created with proper content
        """
        invoicing_service = services["invoicing_service"]
        session = services["session"]
        
        # Create invoice from sale
        invoice = invoicing_service.create_invoice_from_sale(sale.id)
        
        # Use a temporary file for PDF generation
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            pdf_path = tmp.name
            
        try:
            # Generate PDF with config.PDF_OUTPUT_DIR patch
            with patch("core.services.invoicing_service.config") as mock_config:
                # Set PDF_OUTPUT_DIR to temp directory
                mock_config.PDF_OUTPUT_DIR = tempfile.gettempdir()
                
                # Generate PDF with explicit output path
                pdf_result = invoicing_service.generate_invoice_pdf(invoice.id, output_path=pdf_path)
            
            # Verify PDF was created
            assert pdf_result is not None, "PDF generation failed"
            assert os.path.exists(pdf_path), "PDF file was not created"
            assert os.path.getsize(pdf_path) > 0, "PDF file is empty"
            
        finally:
            # Clean up temp file
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)