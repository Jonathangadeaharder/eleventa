import unittest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Assuming Base is defined in your ORM setup and CustomerOrm in models_mapping
from infrastructure.persistence.sqlite.database import Base
from infrastructure.persistence.sqlite.models_mapping import CustomerOrm
from infrastructure.persistence.sqlite.repositories import SqliteCustomerRepository
from core.models.customer import Customer

# Use an in-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"

class TestSqliteCustomerRepository(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up the in-memory database and tables once for the test class."""
        cls.engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(cls.engine) # Create tables based on ORM models
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        """Clean up the database after all tests in the class."""
        Base.metadata.drop_all(cls.engine)

    def setUp(self):
        """Create a new session and repository for each test."""
        self.session = self.SessionLocal()
        self.repository = SqliteCustomerRepository(self.session)
        # Start a transaction for each test
        self.transaction = self.session.begin_nested()

    def tearDown(self):
        """Rollback the transaction and close the session after each test."""
        self.transaction.rollback() # Rollback changes made during the test
        self.session.close()

    def _add_sample_customer(self, name="Test Customer", cuit="12345678") -> Customer:
        customer = Customer(name=name, cuit=cuit, email=f"{name.lower().replace(' ', '.')}@test.com")
        return self.repository.add(customer)

    def test_add_customer(self):
        """Test adding a new customer."""
        customer_data = Customer(name="New Customer", cuit="11223344", phone="555-1234")
        added_customer = self.repository.add(customer_data)

        self.assertIsNotNone(added_customer.id)
        self.assertEqual(added_customer.name, "New Customer")
        self.assertEqual(added_customer.cuit, "11223344")
        self.assertEqual(added_customer.phone, "555-1234")

        # Verify it's in the database directly
        db_customer = self.session.query(CustomerOrm).filter_by(id=added_customer.id).first()
        self.assertIsNotNone(db_customer)
        self.assertEqual(db_customer.name, "New Customer")

    def test_add_customer_duplicate_cuit(self):
        """Test adding a customer with a duplicate CUIT raises an error (or handles it)."""
        # First add a customer with a specific CUIT
        self._add_sample_customer(cuit="99887766")
        
        # Create another customer with the same CUIT
        duplicate_customer = Customer(name="Another Customer", cuit="99887766")
        
        # Try to add the duplicate customer - this should raise an exception
        # We don't need to rollback here as the repository will handle that
        with self.assertRaises(ValueError):
            self.repository.add(duplicate_customer)
        
        # Since the repository already rolled back, our transaction is now closed
        # We need to start a new one for the test to continue
        self.transaction = self.session.begin_nested()

    def test_get_customer_by_id(self):
        """Test retrieving a customer by ID."""
        added_customer = self._add_sample_customer()
        retrieved_customer = self.repository.get_by_id(added_customer.id)

        self.assertIsNotNone(retrieved_customer)
        self.assertEqual(retrieved_customer.id, added_customer.id)
        self.assertEqual(retrieved_customer.name, added_customer.name)

    def test_get_customer_by_id_not_found(self):
        """Test retrieving a non-existent customer ID returns None."""
        non_existent_id = uuid.uuid4()
        retrieved_customer = self.repository.get_by_id(non_existent_id)
        self.assertIsNone(retrieved_customer)

    def test_get_customer_by_cuit(self):
        """Test retrieving a customer by CUIT."""
        cuit = "55667788"
        added_customer = self._add_sample_customer(cuit=cuit)
        retrieved_customer = self.repository.get_by_cuit(cuit)

        self.assertIsNotNone(retrieved_customer)
        self.assertEqual(retrieved_customer.id, added_customer.id)
        self.assertEqual(retrieved_customer.cuit, cuit)

    def test_get_customer_by_cuit_not_found(self):
        """Test retrieving a non-existent CUIT returns None."""
        retrieved_customer = self.repository.get_by_cuit("00000000")
        self.assertIsNone(retrieved_customer)

    def test_get_all_customers(self):
        """Test retrieving all customers."""
        self._add_sample_customer(name="Customer Alpha", cuit="1")
        self._add_sample_customer(name="Customer Beta", cuit="2")
        self._add_sample_customer(name="Customer Gamma", cuit="3")

        all_customers = self.repository.get_all()
        self.assertEqual(len(all_customers), 3)
        # Check if names are present (order might vary)
        names = {c.name for c in all_customers}
        self.assertIn("Customer Alpha", names)
        self.assertIn("Customer Beta", names)
        self.assertIn("Customer Gamma", names)

    def test_update_customer(self):
        """Test updating an existing customer."""
        added_customer = self._add_sample_customer()
        updated_data = Customer(
            id=added_customer.id,
            name="Updated Name",
            phone="555-9999",
            email="updated@example.com",
            address="456 Updated Ave",
            cuit=added_customer.cuit, # CUIT might not be updatable easily due to unique constraint
            iva_condition="Monotributista",
            credit_limit=5000.0,
            credit_balance=100.0,
            is_active=False
        )
        updated_customer = self.repository.update(updated_data)

        self.assertIsNotNone(updated_customer)
        self.assertEqual(updated_customer.name, "Updated Name")
        self.assertEqual(updated_customer.phone, "555-9999")
        self.assertEqual(updated_customer.email, "updated@example.com")
        self.assertEqual(updated_customer.address, "456 Updated Ave")
        self.assertEqual(updated_customer.iva_condition, "Monotributista")
        self.assertEqual(updated_customer.credit_limit, 5000.0)
        self.assertEqual(updated_customer.credit_balance, 100.0)
        self.assertFalse(updated_customer.is_active)

        # Verify changes in DB
        db_customer = self.session.query(CustomerOrm).filter_by(id=added_customer.id).first()
        self.assertEqual(db_customer.name, "Updated Name")
        self.assertFalse(db_customer.is_active)

    def test_update_customer_not_found(self):
        """Test updating a non-existent customer returns None."""
        non_existent_customer = Customer(id=uuid.uuid4(), name="Ghost")
        updated_customer = self.repository.update(non_existent_customer)
        self.assertIsNone(updated_customer)

    def test_delete_customer(self):
        """Test deleting an existing customer."""
        added_customer = self._add_sample_customer()
        result = self.repository.delete(added_customer.id)
        self.assertTrue(result)

        # Verify deleted from DB
        db_customer = self.session.query(CustomerOrm).filter_by(id=added_customer.id).first()
        self.assertIsNone(db_customer)

    def test_delete_customer_not_found(self):
        """Test deleting a non-existent customer returns False."""
        non_existent_id = uuid.uuid4()
        result = self.repository.delete(non_existent_id)
        self.assertFalse(result)

    def test_search_customer_by_name(self):
        """Test searching customers by name (case-insensitive, partial)."""
        self._add_sample_customer(name="John Doe", cuit="1")
        self._add_sample_customer(name="Jane Doe", cuit="2")
        self._add_sample_customer(name="Peter Jones", cuit="3")

        results_doe = self.repository.search_by_name("doe")
        self.assertEqual(len(results_doe), 2)
        names_doe = {c.name for c in results_doe}
        self.assertIn("John Doe", names_doe)
        self.assertIn("Jane Doe", names_doe)

        results_peter = self.repository.search_by_name("Peter")
        self.assertEqual(len(results_peter), 1)
        self.assertEqual(results_peter[0].name, "Peter Jones")

        results_no_match = self.repository.search_by_name("xyz")
        self.assertEqual(len(results_no_match), 0)


if __name__ == '__main__':
    unittest.main() 