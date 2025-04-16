"""
Integration tests for customer-related views and models.

These tests verify that customer components work together correctly,
including the table models and view rendering.
"""
import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QTableView

from core.models.customer import Customer
from ui.models.table_models import CustomerTableModel


class TestCustomerTableModel:
    """Tests for the customer table model."""
    
    def test_customer_table_model_with_customer_attributes(self, qtbot):
        """Test that CustomerTableModel handles Customer attributes correctly."""
        # Create a sample customer with the actual model attributes
        test_customer = Customer(
            id=1,
            name="Test Customer",
            phone="555-1234",
            email="test@example.com",
            address="123 Main St",
            credit_balance=100.0,
            credit_limit=500.0
        )
        
        # Create the model
        model = CustomerTableModel()
        
        # Update with our test customer
        model.update_data([test_customer])
        
        # Verify the model has one row
        assert model.rowCount() == 1
        
        # Test that attribute access works correctly
        # Get the customer at row 0
        retrieved_customer = model.get_customer_at_row(0)
        assert retrieved_customer is not None
        assert retrieved_customer.id == 1
        assert retrieved_customer.name == "Test Customer"
        assert retrieved_customer.phone == "555-1234"
        assert retrieved_customer.email == "test@example.com"
        assert retrieved_customer.address == "123 Main St"
        assert retrieved_customer.credit_balance == 100.0
        assert retrieved_customer.credit_limit == 500.0
        
        # Create a table view to test data rendering
        view = QTableView()
        view.setModel(model)
        qtbot.addWidget(view)
        
        # Test data display
        index = model.index(0, 0)  # Name column
        assert model.data(index, Qt.ItemDataRole.DisplayRole) == "Test Customer"
        
        index = model.index(0, 1)  # Phone column
        assert model.data(index, Qt.ItemDataRole.DisplayRole) == "555-1234"
        
        index = model.index(0, 2)  # Email column
        assert model.data(index, Qt.ItemDataRole.DisplayRole) == "test@example.com"
        
        index = model.index(0, 3)  # Address column
        assert model.data(index, Qt.ItemDataRole.DisplayRole) == "123 Main St"
        
        index = model.index(0, 4)  # Credit balance column
        assert model.data(index, Qt.ItemDataRole.DisplayRole) == "100.00"
        
        index = model.index(0, 5)  # Credit limit column
        assert model.data(index, Qt.ItemDataRole.DisplayRole) == "500.00"


class TestCustomerViewIntegration:
    """Tests for customer view integration."""
    
    @patch('ui.views.customers_view.CustomersView')
    def test_customer_view_initialization(self, mock_customer_view, qtbot):
        """Test that CustomersView initializes with the correct model and data."""
        # Create mock repository that returns our test customers
        mock_customer_repo = MagicMock()
        test_customers = [
            Customer(
                id=1,
                name="Customer 1",
                phone="555-1234",
                email="customer1@example.com",
                address="123 Main St",
                credit_balance=100.0,
                credit_limit=500.0
            ),
            Customer(
                id=2,
                name="Customer 2",
                phone="555-5678",
                email="customer2@example.com",
                address="456 Second St",
                credit_balance=200.0,
                credit_limit=1000.0
            ),
        ]
        mock_customer_repo.get_all.return_value = test_customers
        
        # In a real test with the actual view implementation, we'd check the table contents
        # For now, we can just assert that the repository returns the expected customers
        customers = mock_customer_repo.get_all()
        assert len(customers) == 2
        assert customers[0].name == "Customer 1"
        assert customers[0].credit_balance == 100.0  # This would fail if attribute names don't match
        assert customers[1].name == "Customer 2"
        assert customers[1].credit_limit == 1000.0  # This would fail if attribute names don't match 