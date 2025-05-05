import pytest
from decimal import Decimal
from datetime import datetime
from core.services.invoicing_service import InvoicingService
from core.models.sale import Sale, SaleItem
from core.models.customer import Customer
from core.models.invoice import Invoice


class DummyInvoiceRepo:
    def __init__(self, invoices=None):
        self.invoices = list(invoices) if invoices else []
        self.added = []
    def get_by_sale_id(self, sale_id):
        for inv in self.invoices:
            if inv.sale_id == sale_id:
                return inv
    def get_all(self):
        return self.invoices
    def add(self, invoice):
        invoice.id = invoice.id or len(self.invoices) + 1
        self.invoices.append(invoice)
        self.added.append(invoice)
        return invoice
    def get_by_id(self, invoice_id):
        for inv in self.invoices:
            if inv.id == invoice_id:
                return inv


class DummySaleRepo:
    def __init__(self, sales):
        self.sales = {s.id: s for s in sales}
    def get_by_id(self, sale_id):
        return self.sales.get(sale_id)


class DummyCustomerRepo:
    def __init__(self, customers):
        self.customers = {c.id: c for c in customers}
    def get_by_id(self, customer_id):
        return self.customers.get(customer_id)


def make_service(invoice_repo=None, sale_repo=None, customer_repo=None):
    # Create factory functions that return the provided repos
    invoice_repo_factory = lambda session=None: invoice_repo or DummyInvoiceRepo()
    sale_repo_factory = lambda session=None: sale_repo or DummySaleRepo([])
    customer_repo_factory = lambda session=None: customer_repo or DummyCustomerRepo([])
    
    return InvoicingService(
        invoice_repo_factory=invoice_repo_factory,
        sale_repo_factory=sale_repo_factory,
        customer_repo_factory=customer_repo_factory
    )


# _generate_next_invoice_number

def test_generate_next_invoice_number_first():
    repo = DummyInvoiceRepo([])
    svc = make_service(invoice_repo=repo)
    assert svc._generate_next_invoice_number(repo) == "0001-00000001"


def test_generate_next_invoice_number_increment():
    inv1 = Invoice(
        sale_id=1,
        invoice_number="0001-00000005",
        subtotal=Decimal('10'),
        iva_amount=Decimal('0'),
        total=Decimal('10'),
        customer_id=1
    )
    repo = DummyInvoiceRepo([inv1])
    svc = make_service(invoice_repo=repo)
    assert svc._generate_next_invoice_number(repo) == "0001-00000006"


def test_determine_invoice_type_various():
    svc = make_service()
    assert svc._determine_invoice_type(None) == "B"
    assert svc._determine_invoice_type("RESPONSABLE INSCRIPTO") == "A"
    for cond in ["MONOTRIBUTISTA", "EXENTO", "CONSUMIDOR FINAL"]:
        assert svc._determine_invoice_type(cond) == "B"
    assert svc._determine_invoice_type("UNKNOWN") == "B"


def test_get_iva_rate_various():
    svc = make_service()
    std = Decimal('0.21')
    assert svc._get_iva_rate("A", "RESPONSABLE INSCRIPTO") == std
    assert svc._get_iva_rate("B", "RESPONSABLE INSCRIPTO") == Decimal('0')
    assert svc._get_iva_rate("B", "ANY") == Decimal('0')
    assert svc._get_iva_rate("X", "EXENTO") == Decimal('0')
    assert svc._get_iva_rate("X", None) == std


# create_invoice_from_sale error conditions

def test_create_invoice_sale_not_found():
    svc = make_service(
        invoice_repo=DummyInvoiceRepo(),
        sale_repo=DummySaleRepo([]),
        customer_repo=DummyCustomerRepo([])
    )
    with pytest.raises(ValueError, match="Sale with ID 99 not found"):
        svc.create_invoice_from_sale(99)


def test_create_invoice_already_has_invoice():
    sale = Sale(id=10, items=[SaleItem(product_id=1, quantity=Decimal('1'), unit_price=Decimal('5'))], customer_id=1)
    inv = Invoice(sale_id=10, subtotal=Decimal('5'), iva_amount=Decimal('0'), total=Decimal('5'), customer_id=1)
    repo = DummyInvoiceRepo([inv])
    svc = make_service(
        invoice_repo=repo,
        sale_repo=DummySaleRepo([sale]),
        customer_repo=DummyCustomerRepo([])
    )
    with pytest.raises(ValueError, match="already has an invoice"):
        svc.create_invoice_from_sale(10)


def test_create_invoice_no_customer():
    sale = Sale(id=20, items=[SaleItem(product_id=1, quantity=Decimal('2'), unit_price=Decimal('3'))], customer_id=None)
    svc = make_service(
        invoice_repo=DummyInvoiceRepo(),
        sale_repo=DummySaleRepo([sale]),
        customer_repo=DummyCustomerRepo([])
    )
    with pytest.raises(ValueError, match="has no associated customer"):
        svc.create_invoice_from_sale(20)


def test_create_invoice_customer_not_found():
    sale = Sale(id=30, items=[SaleItem(product_id=1, quantity=Decimal('1'), unit_price=Decimal('4'))], customer_id=2)
    svc = make_service(
        invoice_repo=DummyInvoiceRepo(),
        sale_repo=DummySaleRepo([sale]),
        customer_repo=DummyCustomerRepo([])
    )
    with pytest.raises(ValueError, match="Customer with ID 2 not found"):
        svc.create_invoice_from_sale(30)


def test_create_invoice_success():
    sale = Sale(id=40, items=[SaleItem(product_id=1, quantity=Decimal('1'), unit_price=Decimal('10.00'))], customer_id=3)
    cust = Customer(
        name="Foo",
        id=3,
        phone="p",
        email="e",
        address="a",
        cuit="c",
        iva_condition="RESPONSABLE INSCRIPTO"
    )
    repo = DummyInvoiceRepo([])
    svc = make_service(
        invoice_repo=repo,
        sale_repo=DummySaleRepo([sale]),
        customer_repo=DummyCustomerRepo([cust])
    )
    inv = svc.create_invoice_from_sale(40)
    assert inv.sale_id == 40
    assert inv.customer_id == 3
    assert inv.invoice_type == "A"
    rate = svc._get_iva_rate(inv.invoice_type, cust.iva_condition)
    expected_subtotal = (sale.total / (Decimal('1') + rate)).quantize(Decimal('0.01'))
    # Subtotal should be quantized to 2 decimals
    assert inv.subtotal == expected_subtotal
    # Check total consistency
    assert abs(inv.subtotal + inv.iva_amount - inv.total) < Decimal('0.0000001')
    assert inv.total == sale.total


def test_create_invoice_duplicate_on_save():
    sale = Sale(id=60, items=[SaleItem(product_id=1, quantity=Decimal('1'), unit_price=Decimal('4'))], customer_id=5)
    cust = Customer(
        name="Bar",
        id=5,
        phone="p2",
        email="e2",
        address="a2",
        cuit="c2",
        iva_condition="RESPONSABLE INSCRIPTO"
    )
    # Existing invoice after concurrency error
    inv_existing = Invoice(sale_id=60, subtotal=Decimal('4'), iva_amount=Decimal('0'), total=Decimal('4'), customer_id=5)
    class ConcurrencyInvoiceRepo(DummyInvoiceRepo):
        def __init__(self, invoices):
            super().__init__(invoices)
            self.first_call = True
        def add(self, invoice):
            raise ValueError("Duplicate entry in DB")
        def get_by_sale_id(self, sale_id):
            # First check: no existing invoice, allow save to be attempted
            if self.first_call:
                self.first_call = False
                return None
            # After save failure: return existing invoice to trigger duplicate exception
            return inv_existing

    repo = ConcurrencyInvoiceRepo([])
    svc = make_service(
        invoice_repo=repo,
        sale_repo=DummySaleRepo([sale]),
        customer_repo=DummyCustomerRepo([cust])
    )
    with pytest.raises(ValueError, match=r"Sale with ID 60 already has an invoice \(duplicate\)"):
        svc.create_invoice_from_sale(60)


# get methods

def test_get_invoice_by_id_and_sale_id_and_all():
    inv1 = Invoice(sale_id=50, subtotal=Decimal('5'), iva_amount=Decimal('0'), total=Decimal('5'), customer_id=4)
    repo = DummyInvoiceRepo([inv1])
    svc = make_service(invoice_repo=repo)
    assert svc.get_invoice_by_id(inv1.id) == inv1
    assert svc.get_invoice_by_sale_id(inv1.sale_id) == inv1
    assert svc.get_all_invoices() == [inv1]
