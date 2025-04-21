import pytest
from decimal import Decimal
from core.models.sale import Sale, SaleItem


def test_saleitem_subtotal():
    item = SaleItem(product_id=1, quantity=Decimal('3'), unit_price=Decimal('2.50'))
    assert item.subtotal == Decimal('7.50')


def test_sale_total_empty():
    sale = Sale(items=[])
    assert sale.total == Decimal('0.00')


def test_sale_total_with_items():
    items = [
        SaleItem(product_id=1, quantity=Decimal('1'), unit_price=Decimal('5.00')),
        SaleItem(product_id=2, quantity=Decimal('2'), unit_price=Decimal('3.25'))
    ]
    sale = Sale(items=items)
    expected = Decimal('5.00') + Decimal('6.50')
    assert sale.total == expected.quantize(Decimal('0.01'))
