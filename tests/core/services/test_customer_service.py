import unittest
from unittest.mock import MagicMock, patch
from core.models.customer import Customer
from core.interfaces.repository_interfaces import ICustomerRepository, ICreditPaymentRepository
from core.services.customer_service import CustomerService
from infrastructure.persistence.utils import session_scope # Assuming we might need this structure later, though not strictly required for mock tests


class TestCustomerService(unittest.TestCase):

    def setUp(self):
        self.mock_customer_repo = MagicMock(spec=ICustomerRepository)
        self.mock_credit_payment_repo = MagicMock(spec=ICreditPaymentRepository)
        
        # Create factory functions that return the mocked repositories
        def customer_repo_factory(session):
            return self.mock_customer_repo
            
        def credit_payment_repo_factory(session):
            return self.mock_credit_payment_repo
            
        self.customer_service = CustomerService(
            customer_repo_factory=customer_repo_factory,
            credit_payment_repo_factory=credit_payment_repo_factory
        )

        # Sample Customer data
        self.customer_data_1 = {
            "name": "John Doe",
            "phone": "1234567890",
            "email": "john.doe@example.com",
            "address": "123 Main St",
            "credit_limit": 1000.0,
            "credit_balance": 0.0
        }
        self.customer_1 = Customer(id=1, **self.customer_data_1)

        self.customer_data_2 = {
            "name": "Jane Smith",
            "phone": "0987654321",
            "email": "jane.smith@example.com",
            "address": "456 Oak Ave",
            "credit_limit": 500.0,
            "credit_balance": 50.0
        }
        self.customer_2 = Customer(id=2, **self.customer_data_2)

    def test_add_customer_success(self):
        self.mock_customer_repo.add.return_value = self.customer_1
        result = self.customer_service.add_customer(**self.customer_data_1)
        self.mock_customer_repo.add.assert_called_once()
        # Check if the data passed to add is correct (excluding id)
        call_args, call_kwargs = self.mock_customer_repo.add.call_args
        added_customer = call_args[0]
        self.assertEqual(added_customer.name, self.customer_data_1["name"])
        self.assertEqual(added_customer.email, self.customer_data_1["email"])
        self.assertEqual(result, self.customer_1)

    def test_add_customer_validation_missing_name(self):
        invalid_data = self.customer_data_1.copy()
        invalid_data["name"] = ""
        with self.assertRaisesRegex(ValueError, "Customer name cannot be empty"):
            self.customer_service.add_customer(**invalid_data)
        self.mock_customer_repo.add.assert_not_called()

    def test_add_customer_validation_invalid_email(self):
        # Basic check - more complex regex could be used
        invalid_data = self.customer_data_1.copy()
        invalid_data["email"] = "invalid-email"
        with self.assertRaisesRegex(ValueError, "Invalid email format"):
            self.customer_service.add_customer(**invalid_data)
        self.mock_customer_repo.add.assert_not_called()

    # Add test for duplicate name/email if required by business logic (repo might handle unique constraints)

    def test_update_customer_success(self):
        updated_data = self.customer_data_1.copy()
        updated_data["phone"] = "1112223333"
        # Remove credit_balance as it's not accepted by update_customer
        if "credit_balance" in updated_data:
            del updated_data["credit_balance"]
            
        updated_customer = Customer(id=1, **updated_data)

        self.mock_customer_repo.get_by_id.return_value = self.customer_1
        self.mock_customer_repo.update.return_value = updated_customer

        result = self.customer_service.update_customer(1, **updated_data)

        self.mock_customer_repo.get_by_id.assert_called_once_with(1)
        self.mock_customer_repo.update.assert_called_once()
        # Check if the correct updated customer object was passed
        call_args, call_kwargs = self.mock_customer_repo.update.call_args
        customer_to_update = call_args[0]
        self.assertEqual(customer_to_update.id, 1)
        self.assertEqual(customer_to_update.phone, "1112223333")
        self.assertEqual(result, updated_customer)

    def test_update_customer_not_found(self):
        self.mock_customer_repo.get_by_id.return_value = None
        updated_data = self.customer_data_1.copy()
        updated_data["phone"] = "1112223333"
        # Remove credit_balance as it's not accepted by update_customer
        if "credit_balance" in updated_data:
            del updated_data["credit_balance"]

        with self.assertRaisesRegex(ValueError, "Customer with ID 99 not found"):
            self.customer_service.update_customer(99, **updated_data)

        self.mock_customer_repo.get_by_id.assert_called_once_with(99)
        self.mock_customer_repo.update.assert_not_called()

    def test_update_customer_validation_empty_name(self):
        updated_data = self.customer_data_1.copy()
        updated_data["name"] = ""
        # Remove credit_balance as it's not accepted by update_customer
        if "credit_balance" in updated_data:
            del updated_data["credit_balance"]

        self.mock_customer_repo.get_by_id.return_value = self.customer_1 # Assume customer exists

        with self.assertRaisesRegex(ValueError, "Customer name cannot be empty"):
            self.customer_service.update_customer(1, **updated_data)

        self.mock_customer_repo.update.assert_not_called()

    def test_get_customer_by_id_success(self):
        self.mock_customer_repo.get_by_id.return_value = self.customer_1
        result = self.customer_service.get_customer_by_id(1)
        self.mock_customer_repo.get_by_id.assert_called_once_with(1)
        self.assertEqual(result, self.customer_1)

    def test_get_customer_by_id_not_found(self):
        self.mock_customer_repo.get_by_id.return_value = None
        result = self.customer_service.get_customer_by_id(99)
        self.mock_customer_repo.get_by_id.assert_called_once_with(99)
        self.assertIsNone(result)

    def test_get_all_customers(self):
        self.mock_customer_repo.get_all.return_value = [self.customer_1, self.customer_2]
        result = self.customer_service.get_all_customers()
        self.mock_customer_repo.get_all.assert_called_once()
        self.assertEqual(result, [self.customer_1, self.customer_2])

    def test_find_customer(self):
        search_term = "John"
        self.mock_customer_repo.search.return_value = [self.customer_1]
        result = self.customer_service.find_customer(search_term)
        self.mock_customer_repo.search.assert_called_once_with(search_term)
        self.assertEqual(result, [self.customer_1])

    def test_delete_customer_success_no_balance(self):
        # Assuming customer_1 has 0 balance for this test
        customer_with_no_balance = Customer(id=1, **self.customer_data_1)
        customer_with_no_balance.credit_balance = 0.0
        self.mock_customer_repo.get_by_id.return_value = customer_with_no_balance
        self.mock_customer_repo.delete.return_value = True # Assume delete returns success bool

        result = self.customer_service.delete_customer(1)

        self.mock_customer_repo.get_by_id.assert_called_once_with(1)
        self.mock_customer_repo.delete.assert_called_once_with(1)
        self.assertTrue(result)

    def test_delete_customer_not_found(self):
        self.mock_customer_repo.get_by_id.return_value = None
        self.mock_customer_repo.delete.return_value = False # Or doesn't matter

        # Customer service just returns False when customer not found, doesn't raise error
        result = self.customer_service.delete_customer(99)
        
        self.assertFalse(result)
        self.mock_customer_repo.get_by_id.assert_called_once_with(99)
        self.mock_customer_repo.delete.assert_not_called()


    def test_delete_customer_with_balance(self):
        # Use customer_2 which has a balance
        self.mock_customer_repo.get_by_id.return_value = self.customer_2

        with self.assertRaisesRegex(ValueError, "Cannot delete customer Jane Smith with an outstanding balance"):
             self.customer_service.delete_customer(2)

        self.mock_customer_repo.get_by_id.assert_called_once_with(2)
        self.mock_customer_repo.delete.assert_not_called()


    def test_apply_payment_success(self):
        from decimal import Decimal
        from core.models.credit import CreditPayment

        self.mock_customer_repo.get_by_id.return_value = self.customer_1
        self.mock_customer_repo.update_balance.return_value = True

        payment = CreditPayment(customer_id=1, amount=Decimal("100.00"), id=10, notes="Test payment", user_id=5)
        self.mock_credit_payment_repo.add.return_value = payment

        result = self.customer_service.apply_payment(
            customer_id=1,
            amount=Decimal("100.00"),
            notes="Test payment",
            user_id=5
        )

        self.mock_customer_repo.get_by_id.assert_called_once_with(1)
        self.mock_customer_repo.update_balance.assert_called_once_with(1, self.customer_1.credit_balance + 100.00)
        self.mock_credit_payment_repo.add.assert_called_once()
        self.assertEqual(result, payment)

    def test_apply_payment_customer_not_found(self):
        from decimal import Decimal
        self.mock_customer_repo.get_by_id.return_value = None
        with self.assertRaisesRegex(ValueError, "Customer with ID 1 not found."):
            self.customer_service.apply_payment(1, Decimal("50.00"))

    def test_apply_payment_negative_amount(self):
        from decimal import Decimal
        self.mock_customer_repo.get_by_id.return_value = self.customer_1
        with self.assertRaisesRegex(ValueError, "Payment amount must be positive."):
            self.customer_service.apply_payment(1, Decimal("-10.00"))

    def test_increase_customer_debt_success(self):
        from decimal import Decimal
        mock_session = MagicMock()
        self.mock_customer_repo.get_by_id.return_value = self.customer_1
        self.mock_customer_repo.update_balance.return_value = True

        # Call method
        self.customer_service.increase_customer_debt(
            customer_id=1,
            amount=Decimal("25.00"),
            session=mock_session
        )

        self.mock_customer_repo.get_by_id.assert_called_once_with(1)
        self.mock_customer_repo.update_balance.assert_called_once_with(1, self.customer_1.credit_balance - 25.00)

    def test_increase_customer_debt_customer_not_found(self):
        from decimal import Decimal
        mock_session = MagicMock()
        self.mock_customer_repo.get_by_id.return_value = None
        with self.assertRaisesRegex(ValueError, "Customer with ID 1 not found within transaction."):
            self.customer_service.increase_customer_debt(1, Decimal("10.00"), session=mock_session)

    def test_increase_customer_debt_negative_amount(self):
        from decimal import Decimal
        mock_session = MagicMock()
        self.mock_customer_repo.get_by_id.return_value = self.customer_1
        with self.assertRaisesRegex(ValueError, "Amount to increase debt must be positive."):
            self.customer_service.increase_customer_debt(1, Decimal("-5.00"), session=mock_session)

    def test_get_customer_payments_returns_payments(self):
        from decimal import Decimal
        from core.models.credit import CreditPayment

        payments = [
            CreditPayment(customer_id=1, amount=Decimal("50.00"), id=1, notes="First", user_id=2),
            CreditPayment(customer_id=1, amount=Decimal("25.00"), id=2, notes="Second", user_id=2)
        ]
        self.mock_credit_payment_repo.get_for_customer.return_value = payments

        result = self.customer_service.get_customer_payments(1)
        self.mock_credit_payment_repo.get_for_customer.assert_called_once_with(1)
        self.assertEqual(result, payments)

if __name__ == '__main__':
    unittest.main()