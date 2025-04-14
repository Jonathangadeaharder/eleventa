import unittest
import uuid
from core.models.customer import Customer

class TestCustomerModel(unittest.TestCase):

    def test_customer_creation(self):
        """Test that a Customer object can be created with expected attributes."""
        customer_id = uuid.uuid4()
        customer = Customer(
            id=customer_id,
            name="Test Customer",
            phone="123456789",
            email="test@example.com",
            address="123 Test St",
            cuit="20-12345678-9",
            iva_condition="Responsable Inscripto",
            credit_limit=1000.0,
            credit_balance=50.0,
            is_active=True
        )

        self.assertEqual(customer.id, customer_id)
        self.assertEqual(customer.name, "Test Customer")
        self.assertEqual(customer.phone, "123456789")
        self.assertEqual(customer.email, "test@example.com")
        self.assertEqual(customer.address, "123 Test St")
        self.assertEqual(customer.cuit, "20-12345678-9")
        self.assertEqual(customer.iva_condition, "Responsable Inscripto")
        self.assertEqual(customer.credit_limit, 1000.0)
        self.assertEqual(customer.credit_balance, 50.0)
        self.assertTrue(customer.is_active)

    def test_customer_creation_defaults(self):
        """Test that a Customer object can be created with default values."""
        customer = Customer(name="Default Customer")

        self.assertIsInstance(customer.id, uuid.UUID)
        self.assertEqual(customer.name, "Default Customer")
        self.assertIsNone(customer.phone)
        self.assertIsNone(customer.email)
        self.assertIsNone(customer.address)
        self.assertIsNone(customer.cuit)
        self.assertIsNone(customer.iva_condition)
        self.assertEqual(customer.credit_limit, 0.0)
        self.assertEqual(customer.credit_balance, 0.0)
        self.assertTrue(customer.is_active)

if __name__ == '__main__':
    unittest.main() 