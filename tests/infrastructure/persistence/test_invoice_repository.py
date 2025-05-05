import pytest
import datetime
from decimal import Decimal
import time
import uuid


from core.models.customer import Customer
from core.models.sale import Sale, SaleItem
from core.models.invoice import Invoice
from infrastructure.persistence.sqlite.repositories import (
    SqliteInvoiceRepository,
    SqliteCustomerRepository,
    SqliteDepartmentRepository,
    SqliteProductRepository,
    SqliteSaleRepository
)
from infrastructure.persistence.sqlite.models_mapping import (
    InvoiceOrm, SaleOrm, CustomerOrm, SaleItemOrm, ProductOrm, DepartmentOrm
)
from core.models.department import Department
from core.models.product import Product


@pytest.fixture
def invoice_repo(test_db_session):
    """Provides an instance of SqliteInvoiceRepository."""
    return SqliteInvoiceRepository(test_db_session)

@pytest.fixture
def create_customer(test_db_session):
    """Fixture to create a customer with transactional isolation."""
    def _create_customer(name="Test Customer"):
        customer_repo = SqliteCustomerRepository(test_db_session)
        # Use UUID for more robust uniqueness
        unique_suffix = str(uuid.uuid4())
        # Create a more reliably unique CUIT using more of the UUID
        # unique_cuit = f"20-12345678-{unique_suffix[:1]}" # Old, insufficient uniqueness
        cuit_middle = unique_suffix.replace('-', '')[:8] # Get 8 hex chars from UUID
        cuit_checksum = '9' # Placeholder checksum
        unique_cuit = f"20-{cuit_middle}-{cuit_checksum}" # Ensure format
        
        customer = Customer(
            name=f"{name} {unique_suffix[:8]}", # Use part of UUID for name too
            address="123 Test St",
            phone="555-1234",
            email=f"test_{unique_suffix[:8]}@example.com", # Use part of UUID for email
            cuit=unique_cuit,
            iva_condition="Responsable Inscripto"
        )
        added_customer = customer_repo.add(customer)
        return added_customer
    return _create_customer

@pytest.fixture
def create_department(test_db_session):
    """Fixture to create a department with transactional isolation."""
    def _create_department(name="Testing Dept"):
        dept_repo = SqliteDepartmentRepository(test_db_session)
        dept = Department(name=name)
        added_dept = dept_repo.add(dept)
        return added_dept
    return _create_department

@pytest.fixture
def create_product(test_db_session):
    """Fixture to create a product with transactional isolation."""
    def _create_product(dept_id, code_suffix=""):
        prod_repo = SqliteProductRepository(test_db_session)
        code = f"PFS_{code_suffix}{uuid.uuid4()}"
        prod = prod_repo.add(Product(code=code, description="ProdForSale", sell_price=100.0, department_id=dept_id))
        return prod
    return _create_product

@pytest.fixture
def create_sale(test_db_session):
    """Fixture to create a sale with transactional isolation."""
    def _create_sale(customer_id, product):
        sale_repo = SqliteSaleRepository(test_db_session)
        item = SaleItem(
            product_id=product.id,
            quantity=Decimal("1"),
            unit_price=Decimal("100.00"),
            product_code=product.code,
            product_description=product.description
        )
        sale = Sale(items=[item], customer_id=customer_id)
        added_sale = sale_repo.add_sale(sale)
        return added_sale
    return _create_sale

def get_unique_invoice_number():
    """Generates a unique invoice number for testing."""
    unique_suffix = str(int(time.time() * 1000))
    return f"A-0001-{unique_suffix}"

def create_customer_department_product_sale(test_db_session, create_customer, create_department, create_product, create_sale, suffix=""):
    """Helper to create customer, department, product, and sale with transactional isolation."""
    customer = create_customer(name=f"Test Customer {suffix}")
    dept = create_department(name=f"Test Department {suffix}")
    product = create_product(dept.id, code_suffix=suffix)
    sale = create_sale(customer.id, product)
    return customer, dept, product, sale

def test_add_and_get_invoice(invoice_repo, test_db_session, request, create_customer, create_department, create_product, create_sale):
    """Test adding a new invoice and retrieving it with transactional isolation."""
    # Start a transaction
    test_db_session.begin_nested()
    
    # --- Setup ---
    customer, dept, product, sale = create_customer_department_product_sale(test_db_session, create_customer, create_department, create_product, create_sale, "AddGet")
    # --- End Setup ---
    
    # Add finalizer to rollback the transaction after test completion
    def finalizer():
        test_db_session.rollback()
    request.addfinalizer(finalizer)
    
    invoice_number = get_unique_invoice_number()
    # Ensure customer ID is a string for JSON serialization
    cust_details = customer.to_dict() if hasattr(customer, 'to_dict') else {"name": customer.name, "id": str(customer.id)} 

    invoice = Invoice(
        sale_id=sale.id,
        customer_id=customer.id,
        invoice_number=invoice_number,
        invoice_date=datetime.datetime.now(),
        total=sale.total,
        invoice_type = "A",
        customer_details = cust_details,
        subtotal = sale.total / Decimal("1.21"), 
        iva_amount = sale.total - (sale.total / Decimal("1.21")),
        iva_condition = customer.iva_condition or "Responsable Inscripto",
        is_active=True
    )

    # Add invoice (no manual commit needed)
    added_invoice = invoice_repo.add(invoice)

    assert added_invoice is not None
    assert added_invoice.id is not None
    assert added_invoice.sale_id == sale.id
    assert added_invoice.customer_id == customer.id
    assert added_invoice.invoice_number == invoice_number

    # Retrieve and verify
    retrieved_invoice = invoice_repo.get_by_id(added_invoice.id)
    assert retrieved_invoice is not None
    assert retrieved_invoice.invoice_number == invoice_number
    assert retrieved_invoice.sale_id == sale.id

def test_get_all_invoices(invoice_repo, test_db_session, request, create_customer, create_department, create_product, create_sale):
    """Test retrieving all invoices with transactional isolation."""
    # Start a transaction
    test_db_session.begin_nested()
    
    invoice_numbers_added = set()

    # --- Create Invoice 1 ---
    customer1, dept1, product1, sale1 = create_customer_department_product_sale(test_db_session, create_customer, create_department, create_product, create_sale, "All1")
    
    inv_num1 = get_unique_invoice_number()
    # Ensure customer ID is string
    cust1_details = customer1.to_dict() if hasattr(customer1, 'to_dict') else {"name": customer1.name, "id": str(customer1.id)} 
    inv1 = Invoice(sale_id=sale1.id, customer_id=customer1.id, invoice_number=inv_num1, total=sale1.total, customer_details=cust1_details, invoice_type="A", iva_condition=customer1.iva_condition or "RI")
    invoice_repo.add(inv1)
    invoice_numbers_added.add(inv_num1)
    # --- End Invoice 1 --- 

    time.sleep(0.01) 

    # --- Create Invoice 2 ---
    customer2, dept2, product2, sale2 = create_customer_department_product_sale(test_db_session, create_customer, create_department, create_product, create_sale, "All2")
    
    inv_num2 = get_unique_invoice_number()
    # Ensure customer ID is string
    cust2_details = customer2.to_dict() if hasattr(customer2, 'to_dict') else {"name": customer2.name, "id": str(customer2.id)} 
    inv2 = Invoice(sale_id=sale2.id, customer_id=customer2.id, invoice_number=inv_num2, total=sale2.total, customer_details=cust2_details, invoice_type="A", iva_condition=customer2.iva_condition or "RI")
    invoice_repo.add(inv2)
    invoice_numbers_added.add(inv_num2)
    # --- End Invoice 2 --- 
    
    # Add finalizer to rollback the transaction after test completion
    def finalizer():
        test_db_session.rollback()
    request.addfinalizer(finalizer)

    # Retrieve all
    all_invoices = invoice_repo.get_all()
    assert len(all_invoices) == 2 
    retrieved_invoice_numbers = {inv.invoice_number for inv in all_invoices}
    assert retrieved_invoice_numbers == invoice_numbers_added

def test_duplicate_sale_id_raises_error(invoice_repo, test_db_session, request, create_customer, create_department, create_product, create_sale):
    """Test that adding an invoice for an already invoiced sale raises error with transactional isolation."""
    # Start a transaction
    test_db_session.begin_nested()
    
    # --- Setup ---
    customer, dept, product, sale = create_customer_department_product_sale(test_db_session, create_customer, create_department, create_product, create_sale, "Dup")
    
    invoice_number1 = get_unique_invoice_number()
    # Ensure customer ID is string for JSON serialization
    cust_details = customer.to_dict() if hasattr(customer, 'to_dict') else {"name": customer.name, "id": str(customer.id)} 

    invoice1 = Invoice(
        sale_id=sale.id, 
        customer_id=customer.id, 
        invoice_number=invoice_number1, 
        total=sale.total,
        customer_details=cust_details,
        invoice_type="A",
        iva_condition=customer.iva_condition or "RI"
    )
    invoice_repo.add(invoice1)

    # Attempt to add second invoice for the same sale
    time.sleep(0.01) 
    invoice_number2 = get_unique_invoice_number() 
    invoice2 = Invoice(
        sale_id=sale.id,  # Same sale_id as invoice1
        customer_id=customer.id, 
        invoice_number=invoice_number2, 
        total=sale.total,
        customer_details=cust_details,
        invoice_type="A",
        iva_condition=customer.iva_condition or "RI"
    )
    
    # Update the expected error message pattern
    expected_error_msg = f"Invoice for sale ID {sale.id} already exists"
    with pytest.raises(ValueError, match=expected_error_msg):
        invoice_repo.add(invoice2)
        # No commit needed as add should fail
        
    # Add finalizer to rollback the transaction after test completion
    def finalizer():
        test_db_session.rollback()
    request.addfinalizer(finalizer)
