import unittest
from decimal import Decimal
from datetime import datetime

from core.models.sale import Sale, SaleItem

class TestSaleModels(unittest.TestCase):

    def test_sale_item_creation(self):
        """Assert SaleItem creation and subtotal calculation."""
        item = SaleItem(
            product_id=1,
            quantity=Decimal("2.5"),
            unit_price=Decimal("10.50"),
            product_code="P001",
            product_description="Test Product"
        )
        self.assertIsNone(item.id)
        self.assertEqual(item.product_id, 1)
        self.assertEqual(item.quantity, Decimal("2.5"))
        self.assertEqual(item.unit_price, Decimal("10.50"))
        self.assertEqual(item.product_code, "P001")
        self.assertEqual(item.product_description, "Test Product")

        # Test subtotal calculation
        expected_subtotal = (Decimal("2.5") * Decimal("10.50")).quantize(Decimal("0.01")) # 26.25
        self.assertEqual(item.subtotal, expected_subtotal)

    def test_sale_creation(self):
        """Assert Sale creation with list of items and total calculation."""
        item1 = SaleItem(product_id=1, quantity=Decimal("2"), unit_price=Decimal("5.00")) # Subtotal 10.00
        item2 = SaleItem(product_id=2, quantity=Decimal("1.5"), unit_price=Decimal("20.00")) # Subtotal 30.00

        sale = Sale(items=[item1, item2])

        self.assertIsNone(sale.id)
        self.assertIsInstance(sale.timestamp, datetime)
        self.assertEqual(len(sale.items), 2)
        self.assertIs(sale.items[0], item1)
        self.assertIs(sale.items[1], item2)

        # Test total calculation
        expected_total = (Decimal("10.00") + Decimal("30.00")).quantize(Decimal("0.01")) # 40.00
        self.assertEqual(sale.total, expected_total)

    def test_sale_creation_empty(self):
        """Test Sale creation with no items."""
        sale = Sale()
        self.assertEqual(len(sale.items), 0)
        self.assertEqual(sale.total, Decimal("0.00"))

if __name__ == '__main__':
    unittest.main() 