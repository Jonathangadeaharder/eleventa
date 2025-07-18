import pytest
from unittest.mock import MagicMock, patch, ANY
from decimal import Decimal
from dataclasses import replace
import uuid

from core.models.customer import Customer
from core.models.credit_payment import CreditPayment
from core.interfaces.repository_interfaces import ICustomerRepository, ICreditPaymentRepository
from core.services.customer_service import CustomerService
from infrastructure.persistence.utils import session_scope # For mocking

# --- Fixtures ---

@pytest.fixture
def mock_customer_repo():
    return MagicMock(spec=ICustomerRepository)

@pytest.fixture
def mock_credit_payment_repo():
    return MagicMock(spec=ICreditPaymentRepository)

@pytest.fixture
def customer_service(mock_customer_repo, mock_credit_payment_repo):
    """Fixture for the CustomerService with mocked dependencies."""
    service = CustomerService()
    return service

@pytest.fixture
def customer_data_1():
    return {
        "name": "John Doe",
        "phone": "1234567890",
        "email": "john.doe@example.com",
        "address": "123 Main St",
        "credit_limit": Decimal('1000.00'),
        "credit_balance": Decimal('0.00')
    }

@pytest.fixture
def customer_1(customer_data_1):
    return Customer(id=1, **customer_data_1)

@pytest.fixture
def customer_data_2():
    return {
        "name": "Jane Smith",
        "phone": "0987654321",
        "email": "jane.smith@example.com",
        "address": "456 Oak Ave",
        "credit_limit": Decimal('500.00'),
        "credit_balance": Decimal('50.00') # Positive balance means customer owes money
    }

@pytest.fixture
def customer_2(customer_data_2):
    return Customer(id=2, **customer_data_2)

# --- Tests for add_customer ---

def test_add_customer_success(customer_service, mock_customer_repo, customer_data_1, customer_1):
    """Test adding a customer successfully."""
    # Arrange: Configure mock repo add to return the customer with an ID
    mock_customer_repo.add.return_value = customer_1
    # Extract data suitable for passing to add_customer (no ID)
    data_to_add = {k: v for k, v in customer_data_1.items() if k != 'id'}

    # Act with Unit of Work mocking
    with patch('core.services.customer_service.unit_of_work') as mock_uow:
        mock_context = MagicMock()
        mock_context.customers = mock_customer_repo
        mock_uow.return_value.__enter__.return_value = mock_context
        
        result = customer_service.add_customer(**data_to_add)

    # Assert
    mock_customer_repo.add.assert_called_once()
    call_args, _ = mock_customer_repo.add.call_args
    added_customer_obj = call_args[0]
    assert isinstance(added_customer_obj, Customer)
    assert added_customer_obj.id is None # ID should be None when passed to add
    assert added_customer_obj.name == data_to_add["name"]
    assert added_customer_obj.email == data_to_add["email"]
    assert result == customer_1 # Result should be the object returned by repo (with ID)

def test_add_customer_validation_missing_name(customer_service, mock_customer_repo, customer_data_1):
    """Test adding customer fails with empty name."""
    invalid_data = customer_data_1.copy()
    invalid_data["name"] = ""
    data_to_add = {k: v for k, v in invalid_data.items() if k != 'id'}

    with pytest.raises(ValueError, match="Customer name cannot be empty"):
        customer_service.add_customer(**data_to_add)
    mock_customer_repo.add.assert_not_called()

def test_add_customer_validation_invalid_email(customer_service, mock_customer_repo, customer_data_1):
    """Test adding customer fails with invalid email format."""
    invalid_data = customer_data_1.copy()
    invalid_data["email"] = "invalid-email"
    data_to_add = {k: v for k, v in invalid_data.items() if k != 'id'}

    with pytest.raises(ValueError, match="Invalid email format"):
        customer_service.add_customer(**data_to_add)
    mock_customer_repo.add.assert_not_called()

# --- Tests for update_customer ---

def test_update_customer_success(customer_service, mock_customer_repo, customer_1):
    """Test updating an existing customer successfully."""
    # Arrange
    customer_id = customer_1.id
    # Data for the update (excluding balance, as it shouldn't be updated here)
    update_payload = {
        "name": customer_1.name,
        "phone": "1112223333", # Changed phone
        "email": customer_1.email,
        "address": "999 New St", # Changed address
        "credit_limit": Decimal("1500.00") # Changed limit
    }
    # Expected state *after* update is fetched from repo (repo mock returns this)
    expected_updated_customer = replace(customer_1, **update_payload)

    mock_customer_repo.get_by_id.return_value = customer_1 # Find the original
    mock_customer_repo.update.return_value = expected_updated_customer # Repo returns updated

    # Act with Unit of Work mocking
    with patch('core.services.customer_service.unit_of_work') as mock_uow:
        mock_context = MagicMock()
        mock_context.customers = mock_customer_repo
        mock_uow.return_value.__enter__.return_value = mock_context
        
        result = customer_service.update_customer(customer_id, **update_payload)

    # Assert
    mock_customer_repo.get_by_id.assert_called_once_with(customer_id)
    mock_customer_repo.update.assert_called_once()
    # Check the object passed to repo.update
    call_args, _ = mock_customer_repo.update.call_args
    customer_to_update_obj = call_args[0]
    assert customer_to_update_obj.id == customer_id
    assert customer_to_update_obj.phone == update_payload["phone"]
    assert customer_to_update_obj.address == update_payload["address"]
    assert customer_to_update_obj.credit_limit == update_payload["credit_limit"]
    assert customer_to_update_obj.credit_balance == customer_1.credit_balance # Balance preserved

    # Check the returned object (should match what repo.update returned)
    assert result == expected_updated_customer
    assert result.credit_balance == customer_1.credit_balance # Ensure balance wasn't altered in return

def test_update_customer_not_found(customer_service, mock_customer_repo):
    """Test updating a non-existent customer fails."""
    customer_id = 99
    mock_customer_repo.get_by_id.return_value = None
    update_payload = {"name": "Test", "phone": "123"} # Dummy payload

    with patch('core.services.customer_service.unit_of_work') as mock_uow:
        mock_context = MagicMock()
        mock_context.customers = mock_customer_repo
        mock_uow.return_value.__enter__.return_value = mock_context
        
        with pytest.raises(ValueError, match=f"Customer with ID {customer_id} not found"):
            customer_service.update_customer(customer_id, **update_payload)

    mock_customer_repo.get_by_id.assert_called_once_with(customer_id)
    mock_customer_repo.update.assert_not_called()

def test_update_customer_validation_empty_name(customer_service, mock_customer_repo, customer_1):
    """Test updating customer fails with empty name."""
    update_payload = {"name": "", "phone": "123"}

    with pytest.raises(ValueError, match="Customer name cannot be empty"):
        # Validation happens before unit_of_work
        customer_service.update_customer(customer_1.id, **update_payload)

    mock_customer_repo.get_by_id.assert_not_called()
    mock_customer_repo.update.assert_not_called()

# --- Tests for get_customer_by_id ---

def test_get_customer_by_id_success(customer_service, mock_customer_repo, customer_1):
    """Test retrieving a customer by ID successfully."""
    customer_id = customer_1.id
    mock_customer_repo.get_by_id.return_value = customer_1
    
    with patch('core.services.customer_service.unit_of_work') as mock_uow:
        mock_context = MagicMock()
        mock_context.customers = mock_customer_repo
        mock_uow.return_value.__enter__.return_value = mock_context
        
        result = customer_service.get_customer_by_id(customer_id)
        
    mock_customer_repo.get_by_id.assert_called_once_with(customer_id)
    assert result == customer_1

def test_get_customer_by_id_not_found(customer_service, mock_customer_repo):
    """Test retrieving a non-existent customer returns None."""
    customer_id = 99
    mock_customer_repo.get_by_id.return_value = None
    
    with patch('core.services.customer_service.unit_of_work') as mock_uow:
        mock_context = MagicMock()
        mock_context.customers = mock_customer_repo
        mock_uow.return_value.__enter__.return_value = mock_context
        
        result = customer_service.get_customer_by_id(customer_id)
        
    mock_customer_repo.get_by_id.assert_called_once_with(customer_id)
    assert result is None

# --- Tests for get_all_customers ---

def test_get_all_customers(customer_service, mock_customer_repo, customer_1, customer_2):
    """Test retrieving all customers."""
    expected_customers = [customer_1, customer_2]
    mock_customer_repo.get_all.return_value = expected_customers
    
    with patch('core.services.customer_service.unit_of_work') as mock_uow:
        mock_context = MagicMock()
        mock_context.customers = mock_customer_repo
        mock_uow.return_value.__enter__.return_value = mock_context
        
        result = customer_service.get_all_customers()
        
    mock_customer_repo.get_all.assert_called_once_with(limit=None, offset=None)
    assert result == expected_customers

# --- Tests for find_customer ---

def test_find_customer(customer_service, mock_customer_repo, customer_1):
    """Test finding customers by a search term."""
    search_term = "John"
    expected_customers = [customer_1]
    mock_customer_repo.search.return_value = expected_customers
    
    with patch('core.services.customer_service.unit_of_work') as mock_uow:
        mock_context = MagicMock()
        mock_context.customers = mock_customer_repo
        mock_uow.return_value.__enter__.return_value = mock_context
        
        result = customer_service.find_customer(search_term)
        
    mock_customer_repo.search.assert_called_once_with(search_term, limit=None, offset=None)
    assert result == expected_customers

# --- Tests for delete_customer ---

def test_delete_customer_success_no_balance(customer_service, mock_customer_repo, customer_1):
    """Test deleting a customer with zero balance successfully."""
    customer_id = customer_1.id
    # Ensure balance is zero for this test case
    customer_1.credit_balance = Decimal('0.00')
    mock_customer_repo.get_by_id.return_value = customer_1
    mock_customer_repo.delete.return_value = True

    with patch('core.services.customer_service.unit_of_work') as mock_uow:
        mock_context = MagicMock()
        mock_context.customers = mock_customer_repo
        mock_uow.return_value.__enter__.return_value = mock_context
        
        result = customer_service.delete_customer(customer_id)

    mock_customer_repo.get_by_id.assert_called_once_with(customer_id)
    mock_customer_repo.delete.assert_called_once_with(customer_id)
    assert result is True

def test_delete_customer_not_found(customer_service, mock_customer_repo):
    """Test deleting a non-existent customer returns False."""
    customer_id = 99
    mock_customer_repo.get_by_id.return_value = None

    with patch('core.services.customer_service.unit_of_work') as mock_uow:
        mock_context = MagicMock()
        mock_context.customers = mock_customer_repo
        mock_uow.return_value.__enter__.return_value = mock_context
        
        result = customer_service.delete_customer(customer_id)

    assert result is False
    mock_customer_repo.get_by_id.assert_called_once_with(customer_id)
    mock_customer_repo.delete.assert_not_called()

def test_delete_customer_with_balance(customer_service, mock_customer_repo, customer_2):
    """Test deleting a customer with a non-zero balance fails."""
    customer_id = customer_2.id
    # customer_2 fixture already has a non-zero balance
    mock_customer_repo.get_by_id.return_value = customer_2

    with patch('core.services.customer_service.unit_of_work') as mock_uow:
        mock_context = MagicMock()
        mock_context.customers = mock_customer_repo
        mock_uow.return_value.__enter__.return_value = mock_context
        
        with pytest.raises(ValueError, match="Cannot delete customer Jane Smith with an outstanding balance"):
             customer_service.delete_customer(customer_id)

    mock_customer_repo.get_by_id.assert_called_once_with(customer_id)
    mock_customer_repo.delete.assert_not_called()

# --- Tests for apply_payment ---

def test_apply_payment_success(customer_service, mock_customer_repo, mock_credit_payment_repo, customer_1):
    """Test applying a payment successfully."""
    # Arrange
    customer_id_as_int = customer_1.id # This is an int from the current fixture (e.g., 1)
    customer_id_for_service_call = uuid.UUID(f'00000000-0000-0000-0000-{customer_id_as_int:012d}')

    payment_amount = Decimal("100.00")
    notes = "Test payment"
    user_id = 5
    
    # Ensure customer_1.credit_balance is Decimal for calculation
    original_balance = Decimal(str(customer_1.credit_balance))
    expected_new_balance = original_balance + payment_amount

    # Mock repo calls
    # The repo's get_by_id and update_balance can take Any, so UUID is fine.
    mock_customer_repo.get_by_id.return_value = customer_1 
    mock_customer_repo.update_balance.return_value = True
    
    expected_payment_log = CreditPayment(
        id=10, # Mocked return ID from repo.add
        customer_id=customer_id_for_service_call, # This must be the UUID
        amount=payment_amount,
        notes=notes,
        user_id=user_id
    )
    mock_credit_payment_repo.add.return_value = expected_payment_log

    # Act
    with patch('core.services.customer_service.unit_of_work') as mock_uow:
        mock_context = MagicMock()
        mock_context.customers = mock_customer_repo
        mock_context.credit_payments = mock_credit_payment_repo
        mock_uow.return_value.__enter__.return_value = mock_context
        
        result = customer_service.apply_payment(
            customer_id=customer_id_for_service_call, # Pass the UUID
            amount=payment_amount,
            notes=notes,
            user_id=user_id
        )

    # Assert
    mock_customer_repo.get_by_id.assert_called_once_with(customer_id_for_service_call)
    mock_customer_repo.update_balance.assert_called_once_with(customer_id_for_service_call, expected_new_balance)
    
    mock_credit_payment_repo.add.assert_called_once()
    call_args, _ = mock_credit_payment_repo.add.call_args
    payment_obj_passed_to_repo = call_args[0]
    
    assert isinstance(payment_obj_passed_to_repo, CreditPayment)
    assert payment_obj_passed_to_repo.customer_id == customer_id_for_service_call
    assert payment_obj_passed_to_repo.amount == payment_amount
    assert payment_obj_passed_to_repo.user_id == user_id
    assert payment_obj_passed_to_repo.notes == notes
    
    assert result == expected_payment_log

def test_apply_payment_customer_not_found(customer_service, mock_customer_repo):
    """Test applying payment fails if customer not found."""
    customer_id_uuid = uuid.uuid4() # Use a UUID for the call
    mock_customer_repo.get_by_id.return_value = None
    
    with patch('core.services.customer_service.unit_of_work') as mock_uow:
        mock_context = MagicMock()
        mock_context.customers = mock_customer_repo
        mock_uow.return_value.__enter__.return_value = mock_context
        
        with pytest.raises(ValueError, match=f"Customer with ID {str(customer_id_uuid)} not found."): # Match the UUID string
            customer_service.apply_payment(customer_id_uuid, Decimal("50.00"), user_id=1)

def test_apply_payment_non_positive_amount(customer_service):
    """Test applying zero or negative payment fails."""
    customer_id_uuid = uuid.UUID('00000000-0000-0000-0000-000000000001') # Use a consistent UUID
    with pytest.raises(ValueError, match="Payment amount must be positive."):
        customer_service.apply_payment(customer_id_uuid, Decimal("0.00"), user_id=1)
    with pytest.raises(ValueError, match="Payment amount must be positive."):
        customer_service.apply_payment(customer_id_uuid, Decimal("-10.00"), user_id=1)

# --- Tests for increase_customer_debt ---

def test_increase_customer_debt_success(customer_service, mock_customer_repo, customer_1):
    """Test increasing customer debt successfully."""
    # Arrange
    customer_id = customer_1.id
    increase_amount = Decimal("25.00")
    original_balance = customer_1.credit_balance # 0
    expected_new_balance = original_balance - increase_amount # Debt increases, balance decreases

    mock_customer_repo.get_by_id.return_value = customer_1
    mock_customer_repo.update_balance.return_value = True

    # Act
    with patch('core.services.customer_service.unit_of_work') as mock_uow:
        mock_context = MagicMock()
        mock_context.customers = mock_customer_repo
        mock_uow.return_value.__enter__.return_value = mock_context
        
        customer_service.increase_customer_debt(
            customer_id=customer_id,
            amount=increase_amount
        )

    # Assert
    mock_customer_repo.get_by_id.assert_called_once_with(customer_id)
    mock_customer_repo.update_balance.assert_called_once_with(customer_id, expected_new_balance) # Pass Decimal

def test_increase_customer_debt_customer_not_found(customer_service, mock_customer_repo):
    """Test increasing debt fails if customer not found within transaction."""
    customer_id = 99
    mock_customer_repo.get_by_id.return_value = None

    with patch('core.services.customer_service.unit_of_work') as mock_uow:
        mock_context = MagicMock()
        mock_context.customers = mock_customer_repo
        mock_uow.return_value.__enter__.return_value = mock_context
        
        with pytest.raises(ValueError, match=f"Customer with ID {customer_id} not found within transaction."):
            customer_service.increase_customer_debt(customer_id, Decimal("10.00"))
    mock_customer_repo.update_balance.assert_not_called()

def test_increase_customer_debt_non_positive_amount(customer_service):
    """Test increasing debt by zero or negative amount fails."""
    customer_id = 1
    with pytest.raises(ValueError, match="Amount to increase debt must be positive."):
        customer_service.increase_customer_debt(customer_id, Decimal("0.00"))
    with pytest.raises(ValueError, match="Amount to increase debt must be positive."):
        customer_service.increase_customer_debt(customer_id, Decimal("-5.00"))

# --- Tests for get_customer_payments ---

def test_get_customer_payments_success(customer_service, mock_credit_payment_repo):
    """Test retrieving payments for a customer successfully."""
    # Arrange
    customer_id = 1
    payment1 = CreditPayment(
        id=10, 
        customer_id=uuid.UUID('00000000-0000-0000-0000-000000000001'),  # Convert int to UUID
        amount=Decimal('50.00'),
        user_id=5  # Add required user_id field
    )
    payment2 = CreditPayment(
        id=11, 
        customer_id=uuid.UUID('00000000-0000-0000-0000-000000000001'),  # Convert int to UUID
        amount=Decimal('25.50'),
        user_id=5  # Add required user_id field
    )
    expected_payments = [payment1, payment2]

    mock_credit_payment_repo.get_for_customer.return_value = expected_payments

    # Act
    with patch('core.services.customer_service.unit_of_work') as mock_uow:
        mock_context = MagicMock()
        mock_context.credit_payments = mock_credit_payment_repo
        mock_uow.return_value.__enter__.return_value = mock_context
        
        result = customer_service.get_customer_payments(customer_id)

    # Assert
    mock_credit_payment_repo.get_for_customer.assert_called_once_with(customer_id)
    assert result == expected_payments

def test_get_customer_payments_no_payments(customer_service, mock_credit_payment_repo):
    """Test retrieving payments when a customer has none."""
    # Arrange
    customer_id = 2
    mock_credit_payment_repo.get_for_customer.return_value = [] # Repo returns empty list

    # Act
    with patch('core.services.customer_service.unit_of_work') as mock_uow:
        mock_context = MagicMock()
        mock_context.credit_payments = mock_credit_payment_repo
        mock_uow.return_value.__enter__.return_value = mock_context
        
        result = customer_service.get_customer_payments(customer_id)

    # Assert
    mock_credit_payment_repo.get_for_customer.assert_called_once_with(customer_id)
    assert result == []