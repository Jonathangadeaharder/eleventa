import unittest
from datetime import datetime
from decimal import Decimal
from core.models.invoice import Invoice

class TestInvoiceModel(unittest.TestCase):
    """Tests for the Invoice model."""

    def test_invoice_creation(self):
        """Test that an Invoice object can be created with expected attributes."""
        # Create an invoice with required fields
        invoice = Invoice(
            sale_id=1
        )
        self.assertEqual(invoice.sale_id, 1)
        self.assertIsNone(invoice.id)
        self.assertIsNone(invoice.customer_id)
        self.assertIsNone(invoice.invoice_number)
        self.assertIsInstance(invoice.invoice_date, datetime)
        self.assertEqual(invoice.invoice_type, "B")
        self.assertEqual(invoice.customer_details, {})
        self.assertEqual(invoice.subtotal, Decimal("0.00"))
        self.assertEqual(invoice.iva_amount, Decimal("0.00"))
        self.assertEqual(invoice.total, Decimal("0.00"))
        self.assertEqual(invoice.iva_condition, "Consumidor Final")
        self.assertIsNone(invoice.cae)
        self.assertIsNone(invoice.cae_due_date)
        self.assertIsNone(invoice.notes)
        self.assertTrue(invoice.is_active)

    def test_invoice_creation_with_all_fields(self):
        """Test that an Invoice object can be created with all fields specified."""
        invoice_date = datetime.now()
        cae_due_date = datetime(2025, 12, 31)
        customer_details = {
            "name": "Test Customer",
            "cuit": "20-12345678-9",
            "address": "123 Test St",
            "iva_condition": "Responsable Inscripto"
        }
        
        invoice = Invoice(
            id=1,
            sale_id=2,
            customer_id=3,
            invoice_number="0001-00000001",
            invoice_date=invoice_date,
            invoice_type="A",
            customer_details=customer_details,
            subtotal=Decimal("100.00"),
            iva_amount=Decimal("21.00"),
            total=Decimal("121.00"),
            iva_condition="Responsable Inscripto",
            cae="12345678901234",
            cae_due_date=cae_due_date,
            notes="Test invoice",
            is_active=True
        )
        
        self.assertEqual(invoice.id, 1)
        self.assertEqual(invoice.sale_id, 2)
        self.assertEqual(invoice.customer_id, 3)
        self.assertEqual(invoice.invoice_number, "0001-00000001")
        self.assertEqual(invoice.invoice_date, invoice_date)
        self.assertEqual(invoice.invoice_type, "A")
        self.assertEqual(invoice.customer_details, customer_details)
        self.assertEqual(invoice.subtotal, Decimal("100.00"))
        self.assertEqual(invoice.iva_amount, Decimal("21.00"))
        self.assertEqual(invoice.total, Decimal("121.00"))
        self.assertEqual(invoice.iva_condition, "Responsable Inscripto")
        self.assertEqual(invoice.cae, "12345678901234")
        self.assertEqual(invoice.cae_due_date, cae_due_date)
        self.assertEqual(invoice.notes, "Test invoice")
        self.assertTrue(invoice.is_active)

if __name__ == '__main__':
    unittest.main()