import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import datetime
from core.services.invoicing_service import InvoicingService
from core.models.sale import Sale, SaleItem
from core.models.customer import Customer
from core.models.invoice import Invoice
from core.interfaces.repository_interfaces import IInvoiceRepository


def make_service():
    # Create service with Unit of Work pattern
    return InvoicingService()


# _generate_next_invoice_number

@patch('core.services.invoicing_service.unit_of_work')
def test_generate_next_invoice_number_first(mock_uow):
    mock_context = MagicMock()
    mock_uow.return_value.__enter__.return_value = mock_context
    mock_context.invoices.get_all.return_value = []
    
    svc = make_service()
    assert svc._generate_next_invoice_number(mock_context.invoices) == "0001-00000001"


@patch('core.services.invoicing_service.unit_of_work')
def test_generate_next_invoice_number_increment(mock_uow):
    inv1 = Invoice(
        sale_id=1,
        invoice_number="0001-00000005",
        subtotal=Decimal('10'),
        iva_amount=Decimal('0'),
        total=Decimal('10'),
        customer_id=1
    )
    mock_context = MagicMock()
    mock_uow.return_value.__enter__.return_value = mock_context
    mock_context.invoices.get_all.return_value = [inv1]
    
    svc = make_service()
    assert svc._generate_next_invoice_number(mock_context.invoices) == "0001-00000006"


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

@patch('core.services.invoicing_service.unit_of_work')
def test_create_invoice_sale_not_found(mock_uow):
    mock_context = MagicMock()
    mock_uow.return_value.__enter__.return_value = mock_context
    mock_context.sales.get_by_id.return_value = None
    
    svc = make_service()
    with pytest.raises(ValueError, match="Sale with ID 99 not found"):
        svc.create_invoice_from_sale(99)


@patch('core.services.invoicing_service.unit_of_work')
def test_create_invoice_already_has_invoice(mock_uow):
    sale = Sale(id=10, items=[SaleItem(product_id=1, quantity=Decimal('1'), unit_price=Decimal('5'))], customer_id=1)
    inv = Invoice(sale_id=10, subtotal=Decimal('5'), iva_amount=Decimal('0'), total=Decimal('5'), customer_id=1)
    
    mock_context = MagicMock()
    mock_uow.return_value.__enter__.return_value = mock_context
    mock_context.sales.get_by_id.return_value = sale
    mock_context.invoices.get_by_sale_id.return_value = inv
    
    svc = make_service()
    with pytest.raises(ValueError, match="already has an invoice"):
        svc.create_invoice_from_sale(10)


@patch('core.services.invoicing_service.unit_of_work')
def test_create_invoice_no_customer(mock_uow):
    sale = Sale(id=20, items=[SaleItem(product_id=1, quantity=Decimal('2'), unit_price=Decimal('3'))], customer_id=None)
    
    mock_context = MagicMock()
    mock_uow.return_value.__enter__.return_value = mock_context
    mock_context.sales.get_by_id.return_value = sale
    mock_context.invoices.get_by_sale_id.return_value = None
    
    svc = make_service()
    with pytest.raises(ValueError, match="has no associated customer"):
        svc.create_invoice_from_sale(20)


@patch('core.services.invoicing_service.unit_of_work')
def test_create_invoice_customer_not_found(mock_uow):
    sale = Sale(id=30, items=[SaleItem(product_id=1, quantity=Decimal('1'), unit_price=Decimal('4'))], customer_id=2)
    
    mock_context = MagicMock()
    mock_uow.return_value.__enter__.return_value = mock_context
    mock_context.sales.get_by_id.return_value = sale
    mock_context.invoices.get_by_sale_id.return_value = None
    mock_context.customers.get_by_id.return_value = None
    
    svc = make_service()
    with pytest.raises(ValueError, match="Customer with ID 2 not found"):
        svc.create_invoice_from_sale(30)


@patch('core.services.invoicing_service.unit_of_work')
def test_create_invoice_success(mock_uow):
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
    
    mock_context = MagicMock()
    mock_uow.return_value.__enter__.return_value = mock_context
    mock_context.sales.get_by_id.return_value = sale
    mock_context.invoices.get_by_sale_id.return_value = None
    mock_context.customers.get_by_id.return_value = cust
    mock_context.invoices.get_all.return_value = []
    
    # Mock the add method to return the invoice with an ID
    def mock_add(invoice):
        invoice.id = 1
        return invoice
    mock_context.invoices.add.side_effect = mock_add
    
    svc = make_service()
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


@patch('core.services.invoicing_service.unit_of_work')
def test_create_invoice_duplicate_on_save(mock_uow):
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
    
    mock_context = MagicMock()
    mock_uow.return_value.__enter__.return_value = mock_context
    mock_context.sales.get_by_id.return_value = sale
    mock_context.invoices.get_by_sale_id.return_value = None
    mock_context.customers.get_by_id.return_value = cust
    mock_context.invoices.get_all.return_value = []
    
    # Mock the add method to raise a duplicate entry error
    mock_context.invoices.add.side_effect = ValueError("Duplicate entry in DB")
    
    svc = make_service()
    with pytest.raises(ValueError, match=r"Sale with ID 60 already has an invoice \(duplicate\)"):
        svc.create_invoice_from_sale(60)


# get methods

@patch('core.services.invoicing_service.unit_of_work')
def test_get_invoice_by_id_and_sale_id_and_all(mock_uow):
    inv1 = Invoice(sale_id=50, subtotal=Decimal('5'), iva_amount=Decimal('0'), total=Decimal('5'), customer_id=4)
    inv1.id = 1  # Set an ID for the invoice
    
    mock_context = MagicMock()
    mock_uow.return_value.__enter__.return_value = mock_context
    mock_context.invoices.get_by_id.return_value = inv1
    mock_context.invoices.get_by_sale_id.return_value = inv1
    mock_context.invoices.get_all.return_value = [inv1]
    
    svc = make_service()
    assert svc.get_invoice_by_id(inv1.id) == inv1
    assert svc.get_invoice_by_sale_id(inv1.sale_id) == inv1
    assert svc.get_all_invoices() == [inv1]
