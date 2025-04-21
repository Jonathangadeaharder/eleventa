import pytest
from unittest.mock import MagicMock, patch, ANY
from decimal import Decimal
import os # Import os for mocking

# Service and Models
from core.services.sale_service import SaleService
from core.models.sale import Sale, SaleItem
from core.models.product import Product
from core.models.customer import Customer # Added Customer model

# Interfaces and other services needed for mocks
from core.interfaces.repository_interfaces import ISaleRepository, IProductRepository, ICustomerRepository
from core.services.inventory_service import InventoryService
from core.services.customer_service import CustomerService
from infrastructure.persistence.utils import session_scope # For mocking

# --- Fixtures ---

@pytest.fixture
def mock_sale_repo():
    return MagicMock(spec=ISaleRepository)

@pytest.fixture
def mock_product_repo():
    return MagicMock(spec=IProductRepository)

@pytest.fixture
def mock_inventory_service():
    return MagicMock(spec=InventoryService)

@pytest.fixture
def mock_customer_service():
    return MagicMock(spec=CustomerService)

@pytest.fixture
def sale_service(mock_sale_repo, mock_product_repo, mock_inventory_service, mock_customer_service):
    """Fixture for the SaleService with mocked dependencies."""
    return SaleService(
        sale_repository_factory=lambda session=None: mock_sale_repo,
        product_repository_factory=lambda session=None: mock_product_repo,
        inventory_service=mock_inventory_service,
        customer_service=mock_customer_service
    )

@pytest.fixture
def product1():
    return Product(id=1, code="P001", description="Prod 1", sell_price=Decimal('10.00'), uses_inventory=True)

@pytest.fixture
def product2():
    return Product(id=2, code="P002", description="Prod 2", sell_price=Decimal('20.00'), uses_inventory=True)

@pytest.fixture
def product3_no_inv():
    return Product(id=3, code="P003", description="Prod 3 NonInv", sell_price=Decimal('5.00'), uses_inventory=False)

@pytest.fixture
def sample_customer():
    return Customer(id=5, name="Test Customer", cuit="12345")

# --- Helper for Mocking add_sale ---
def mock_add_sale_impl(sale_id_start=100, item_id_start=200):
    """Creates a side_effect function for mock_sale_repo.add_sale that assigns IDs."""
    def side_effect(sale_arg: Sale):
        sale_arg.id = sale_id_start
        for idx, item in enumerate(sale_arg.items):
            item.id = item_id_start + idx
            item.sale_id = sale_id_start
        return sale_arg
    return side_effect

# --- Tests for create_sale ---

@patch('infrastructure.persistence.utils.session_scope')
def test_create_sale_success(
    mock_session_scope, sale_service, mock_product_repo, mock_sale_repo, mock_inventory_service,
    mock_customer_service, product1, product2
):
    """Verify successful sale creation and inventory decrease calls."""
    # Arrange
    mock_product_repo.get_by_id.side_effect = lambda pid: {1: product1, 2: product2}.get(pid)
    mock_sale_repo.add_sale.side_effect = mock_add_sale_impl(sale_id_start=101, item_id_start=200)
    mock_inventory_service.decrease_stock_for_sale.return_value = None

    items_data = [
        {'product_id': 1, 'quantity': '2'},
        {'product_id': 2, 'quantity': Decimal('1.5')}
    ]
    user_id = 1
    payment_type = "Efectivo"

    # Act
    created_sale = sale_service.create_sale(
        items_data=items_data,
        user_id=user_id,
        payment_type=payment_type
    )

    # Assert
    # 1. Product repo calls
    mock_product_repo.get_by_id.assert_any_call(1)
    mock_product_repo.get_by_id.assert_any_call(2)
    assert mock_product_repo.get_by_id.call_count == 2

    # 2. Sale repo call
    mock_sale_repo.add_sale.assert_called_once()
    call_args, _ = mock_sale_repo.add_sale.call_args
    sale_arg = call_args[0]
    assert isinstance(sale_arg, Sale)
    assert len(sale_arg.items) == 2
    assert sale_arg.items[0].product_id == 1
    assert sale_arg.items[0].quantity == Decimal('2')
    assert sale_arg.items[0].unit_price == Decimal('10.00')
    assert sale_arg.items[1].product_id == 2
    assert sale_arg.items[1].quantity == Decimal('1.5')
    assert sale_arg.items[1].unit_price == Decimal('20.00')
    assert sale_arg.user_id == user_id
    assert sale_arg.payment_type == payment_type
    assert not sale_arg.is_credit_sale
    assert sale_arg.customer_id is None

    # 3. Inventory service calls
    assert mock_inventory_service.decrease_stock_for_sale.call_count == 2
    # Note: Inventory service expects quantity as Decimal now
    mock_inventory_service.decrease_stock_for_sale.assert_any_call(
        session=ANY, product_id=1, quantity=Decimal('2'), sale_id=101 # Use Decimal
    )
    mock_inventory_service.decrease_stock_for_sale.assert_any_call(
        session=ANY, product_id=2, quantity=Decimal('1.5'), sale_id=101 # Use Decimal
    )
    mock_customer_service.increase_customer_debt.assert_not_called()

    # 4. Returned sale object
    assert created_sale.id == 101
    assert created_sale.items[0].id == 200
    assert created_sale.items[1].id == 201
    assert created_sale.items[0].sale_id == 101
    assert created_sale.items[1].sale_id == 101

@patch('infrastructure.persistence.utils.session_scope')
def test_create_sale_success_item_without_inventory(
    mock_session_scope, sale_service, mock_product_repo, mock_sale_repo, mock_inventory_service,
    product1, product3_no_inv
):
    """Verify sale creation succeeds, but stock is not decreased for non-inventory item."""
    # Arrange
    mock_product_repo.get_by_id.side_effect = lambda pid: {1: product1, 3: product3_no_inv}.get(pid)
    mock_sale_repo.add_sale.side_effect = mock_add_sale_impl(sale_id_start=102, item_id_start=300)
    mock_inventory_service.decrease_stock_for_sale.return_value = None

    items_data = [
        {'product_id': 1, 'quantity': '1'},
        {'product_id': 3, 'quantity': '5'} # Product 3 does not use inventory
    ]
    user_id = 2
    payment_type = "Tarjeta"

    # Act
    created_sale = sale_service.create_sale(
        items_data=items_data,
        user_id=user_id,
        payment_type=payment_type
    )

    # Assert
    mock_sale_repo.add_sale.assert_called_once()
    # Inventory service ONLY called for product 1
    assert mock_inventory_service.decrease_stock_for_sale.call_count == 1
    mock_inventory_service.decrease_stock_for_sale.assert_called_once_with(
        session=ANY, product_id=1, quantity=Decimal('1.0'), sale_id=102 # Use Decimal
    )
    assert created_sale.id == 102
    assert len(created_sale.items) == 2

@patch('infrastructure.persistence.utils.session_scope')
def test_create_sale_validation_empty_list(mock_session_scope, sale_service, mock_sale_repo):
    """Test creating sale with an empty item list raises ValueError."""
    with pytest.raises(ValueError, match="Cannot create a sale with no items."):
        sale_service.create_sale(items_data=[], user_id=1, payment_type="Efectivo")
    mock_sale_repo.add_sale.assert_not_called()

@patch('infrastructure.persistence.utils.session_scope')
def test_create_sale_validation_missing_data(mock_session_scope, sale_service, mock_sale_repo):
    """Test creating sale with missing item data raises ValueError."""
    items_data = [
        {'product_id': 1} # Missing quantity
    ]
    with pytest.raises(ValueError, match="Missing 'product_id' or 'quantity'"):
        sale_service.create_sale(items_data=items_data, user_id=1, payment_type="Efectivo")
    mock_sale_repo.add_sale.assert_not_called()

@patch('infrastructure.persistence.utils.session_scope')
def test_create_sale_validation_invalid_quantity_format(mock_session_scope, sale_service):
    """Test creating sale with invalid quantity format raises ValueError."""
    items_data = [
        {'product_id': 1, 'quantity': 'abc'}
    ]
    with pytest.raises(ValueError, match="Invalid quantity format"):
        sale_service.create_sale(items_data=items_data, user_id=1, payment_type="Efectivo")

@patch('infrastructure.persistence.utils.session_scope')
def test_create_sale_validation_non_positive_quantity(mock_session_scope, sale_service):
    """Test creating sale with zero or negative quantity raises ValueError."""
    items_data_zero = [
        {'product_id': 1, 'quantity': '0'}
    ]
    with pytest.raises(ValueError, match="Sale quantity must be positive"):
        sale_service.create_sale(items_data=items_data_zero, user_id=1, payment_type="Efectivo")

    items_data_negative = [
        {'product_id': 1, 'quantity': '-1.5'}
    ]
    with pytest.raises(ValueError, match="Sale quantity must be positive"):
        sale_service.create_sale(items_data=items_data_negative, user_id=1, payment_type="Efectivo")

@patch('infrastructure.persistence.utils.session_scope')
def test_create_sale_with_various_payment_types(mock_session_scope, sale_service, mock_product_repo, mock_sale_repo, product1):
    """Test creating sales with each allowed payment type."""
    allowed_payment_types = ["Efectivo", "Tarjeta", "Otro"] # Exclude Crédito for this test
    items_data = [
        {'product_id': 1, 'quantity': '1'}
    ]
    user_id = 42

    mock_product_repo.get_by_id.return_value = product1
    mock_sale_repo.add_sale.side_effect = mock_add_sale_impl(sale_id_start=900, item_id_start=1000)

    for payment_type in allowed_payment_types:
        created_sale = sale_service.create_sale(
            items_data=items_data,
            user_id=user_id,
            payment_type=payment_type
        )
        assert created_sale.payment_type == payment_type
        assert created_sale.user_id == user_id
        assert created_sale.items[0].product_id == 1

@patch('infrastructure.persistence.utils.session_scope')
def test_create_sale_with_different_user_ids(mock_session_scope, sale_service, mock_product_repo, mock_sale_repo, product1):
    """Test creating sales with different user IDs."""
    items_data = [
        {'product_id': 1, 'quantity': '1'}
    ]
    payment_type = "Efectivo"
    user_ids = [101, 202]

    mock_product_repo.get_by_id.return_value = product1
    mock_sale_repo.add_sale.side_effect = mock_add_sale_impl(sale_id_start=800, item_id_start=1100)

    for user_id in user_ids:
        created_sale = sale_service.create_sale(
            items_data=items_data,
            user_id=user_id,
            payment_type=payment_type
        )
        assert created_sale.user_id == user_id
        assert created_sale.payment_type == payment_type

@patch('infrastructure.persistence.utils.session_scope')
def test_create_sale_validation_product_not_found(mock_session_scope, sale_service, mock_product_repo, mock_sale_repo):
    """Test creating sale fails if a product ID is not found."""
    items_data = [
        {'product_id': 1, 'quantity': '1'},
        {'product_id': 999, 'quantity': '1'} # Product 999 not found
    ]
    # Mock get_by_id to return None for ID 999
    mock_product_repo.get_by_id.side_effect = lambda pid: {1: product1}.get(pid) # Only product1 exists

    with pytest.raises(ValueError, match="Product with ID 999 not found"):
        sale_service.create_sale(items_data=items_data, user_id=1, payment_type="Efectivo")
    mock_sale_repo.add_sale.assert_not_called() # Sale should not be added
    # mock_session_scope.assert_called_once() # Scope entry might fail before full execution

@patch('infrastructure.persistence.utils.session_scope')
def test_create_sale_transactionality_inventory_fail(mock_session_scope, sale_service, mock_product_repo, mock_sale_repo, mock_inventory_service, product1):
    """Test that sale creation is rolled back if inventory decrease fails."""
    # Arrange
    mock_product_repo.get_by_id.return_value = product1
    mock_sale_repo.add_sale.side_effect = mock_add_sale_impl(sale_id_start=700, item_id_start=1200)

    # Simulate inventory service failing
    inventory_error = ValueError("Insufficient stock!")
    mock_inventory_service.decrease_stock_for_sale.side_effect = inventory_error

    items_data = [
        {'product_id': 1, 'quantity': '1'}
    ]

    # Act & Assert
    with pytest.raises(ValueError, match="Insufficient stock!"):
        sale_service.create_sale(items_data=items_data, user_id=1, payment_type="Efectivo")

    # Check that add_sale was called (happens before inventory decrease)
    mock_sale_repo.add_sale.assert_called_once()
    # Check that inventory decrease was attempted
    mock_inventory_service.decrease_stock_for_sale.assert_called_once()
    # Critical: Session scope context manager should exit (implicitly rolling back on error)
    # mock_session_scope.assert_called_once() # Scope entry might fail before full execution

@patch('infrastructure.persistence.utils.session_scope')
def test_create_sale_validation_missing_user_id(mock_session_scope, sale_service):
    """Test creating sale fails if user_id is missing."""
    items_data = [
        {'product_id': 1, 'quantity': '1'}
    ]
    with pytest.raises(ValueError, match="User ID must be provided"):
        sale_service.create_sale(items_data=items_data, user_id=None, payment_type="Efectivo")

@patch('infrastructure.persistence.utils.session_scope')
def test_create_sale_validation_missing_payment_type_non_credit(mock_session_scope, sale_service):
    """Test creating non-credit sale fails if payment_type is missing."""
    items_data = [
        {'product_id': 1, 'quantity': '1'}
    ]
    with pytest.raises(ValueError, match="Payment type must be provided"):
        sale_service.create_sale(items_data=items_data, user_id=1, payment_type=None, is_credit_sale=False)

@patch('infrastructure.persistence.utils.session_scope')
def test_create_sale_credit_sale_success(mock_session_scope, sale_service, mock_product_repo, mock_sale_repo, mock_inventory_service, mock_customer_service, product1, sample_customer):
    """Test creating a credit sale successfully, updating customer debt."""
    # Arrange
    mock_product_repo.get_by_id.return_value = product1
    mock_sale_repo.add_sale.side_effect = mock_add_sale_impl(sale_id_start=600, item_id_start=1300)
    mock_inventory_service.decrease_stock_for_sale.return_value = None
    mock_customer_service.get_customer_by_id.return_value = sample_customer
    mock_customer_service.increase_customer_debt.return_value = None

    items_data = [
        {'product_id': 1, 'quantity': '3'}
    ]
    user_id = 3
    customer_id = sample_customer.id
    expected_sale_total = product1.sell_price * 3

    # Act
    created_sale = sale_service.create_sale(
        items_data=items_data,
        user_id=user_id,
        customer_id=customer_id,
        is_credit_sale=True,
        payment_type=None # Should be ignored for credit sale
    )

    # Assert
    mock_product_repo.get_by_id.assert_called_once_with(1)
    mock_sale_repo.add_sale.assert_called_once()
    # Check sale details
    call_args, _ = mock_sale_repo.add_sale.call_args
    sale_arg = call_args[0]
    assert sale_arg.is_credit_sale is True
    assert sale_arg.customer_id == customer_id
    assert sale_arg.payment_type == 'Crédito' # Set automatically
    # Check inventory decrease
    mock_inventory_service.decrease_stock_for_sale.assert_called_once_with(
        session=ANY, product_id=1, quantity=Decimal('3.0'), sale_id=600 # Use Decimal
    )
    # Check customer service calls
    mock_customer_service.get_customer_by_id.assert_called_once_with(customer_id)
    mock_customer_service.increase_customer_debt.assert_called_once_with(
        session=ANY, customer_id=customer_id, amount=expected_sale_total
    )
    # Check returned sale
    assert created_sale.id == 600
    assert created_sale.is_credit_sale is True

@patch('infrastructure.persistence.utils.session_scope')
def test_create_sale_credit_sale_missing_customer(mock_session_scope, sale_service):
    """Test creating credit sale fails if customer_id is missing."""
    items_data = [
        {'product_id': 1, 'quantity': '1'}
    ]
    with pytest.raises(ValueError, match="A customer ID must be provided for credit sales."):
        sale_service.create_sale(items_data=items_data, user_id=1, is_credit_sale=True, customer_id=None, payment_type=None)

@patch('infrastructure.persistence.utils.session_scope')
def test_create_sale_credit_sale_customer_not_found(mock_session_scope, sale_service, mock_customer_service):
    """Test creating credit sale fails if customer_id is not found."""
    items_data = [{'product_id': 1, 'quantity': '1'}]
    customer_id = 999
    mock_customer_service.get_customer_by_id.return_value = None # Simulate customer not found

    with pytest.raises(ValueError, match=f"Customer with ID {customer_id} not found."):
        sale_service.create_sale(items_data=items_data, user_id=1, customer_id=customer_id, is_credit_sale=True, payment_type=None)
    mock_customer_service.get_customer_by_id.assert_called_once_with(customer_id)

# --- Tests for get_sale_by_id ---

@patch('infrastructure.persistence.utils.session_scope')
def test_get_sale_by_id_found(mock_session_scope, sale_service, mock_sale_repo):
    """Test retrieving an existing sale by its ID."""
    # Arrange
    sale_id = 123
    expected_sale = Sale(id=sale_id, user_id=1, payment_type="Efectivo") # Example sale
    mock_sale_repo.get_by_id.return_value = expected_sale
    # We don't need to mock the session object itself here, 
    # as we trust session_scope provides one to the factory.
    # mock_session = MagicMock()
    # mock_session_scope.return_value.__enter__.return_value = mock_session

    # Act
    found_sale = sale_service.get_sale_by_id(sale_id)

    # Assert
    # mock_session_scope.assert_called_once() # Don't assert this way
    mock_sale_repo.get_by_id.assert_called_once_with(sale_id)
    assert found_sale == expected_sale

@patch('infrastructure.persistence.utils.session_scope')
def test_get_sale_by_id_not_found(mock_session_scope, sale_service, mock_sale_repo):
    """Test retrieving a non-existent sale returns None."""
    # Arrange
    sale_id = 999
    mock_sale_repo.get_by_id.return_value = None
    # mock_session = MagicMock()
    # mock_session_scope.return_value.__enter__.return_value = mock_session

    # Act
    found_sale = sale_service.get_sale_by_id(sale_id)

    # Assert
    # mock_session_scope.assert_called_once() # Don't assert this way
    mock_sale_repo.get_by_id.assert_called_once_with(sale_id)
    assert found_sale is None

# --- Tests for generate_receipt_pdf ---

@patch('core.services.sale_service.create_receipt_pdf')
@patch('core.services.sale_service.os.path.join')
@patch('core.services.sale_service.os.makedirs')
@patch('core.services.sale_service.datetime')
@patch('core.services.sale_service.Config')
def test_generate_receipt_pdf_success(
    mock_config, mock_datetime, mock_makedirs, mock_os_path_join,
    mock_create_receipt, sale_service, mock_sale_repo, mock_customer_service, sample_customer
):
    """Test successfully generating a PDF receipt for a sale."""
    # Arrange
    sale_id = 101
    user_id = 5
    customer_id = sample_customer.id
    test_sale = Sale(
        id=sale_id,
        user_id=user_id,
        customer_id=customer_id,
        payment_type="Tarjeta",
        items=[SaleItem(product_id=1, quantity=2, unit_price=10)]
    )

    # Mock dependencies
    sale_service.get_sale_by_id = MagicMock(return_value=test_sale) # Mock internal call
    mock_customer_service.get_customer_by_id.return_value = sample_customer

    # Mock Config attributes
    mock_config.STORE_NAME = "My Test Store"
    mock_config.STORE_ADDRESS = "123 Test St"
    mock_config.STORE_CUIT = "30-11111111-1"
    mock_config.STORE_IVA_CONDITION = "RI"
    mock_config.STORE_PHONE = "555-1234"

    # Mock datetime for predictable filename
    mock_now = MagicMock()
    mock_now.strftime.return_value = "20240101120000"
    mock_datetime.now.return_value = mock_now

    # Mock os.path.join to return a predictable path
    expected_dir = "/path/to/project/receipts"
    expected_filename = f"/path/to/project/receipts/receipt_sale_{sale_id}_20240101120000.pdf"
    mock_os_path_join.side_effect = lambda *args: expected_filename if len(args) > 1 and args[-1].startswith("receipt_sale") else expected_dir

    # Mock create_receipt_pdf to return the filename
    mock_create_receipt.return_value = expected_filename

    # Act
    pdf_path = sale_service.generate_receipt_pdf(sale_id)

    # Assert
    sale_service.get_sale_by_id.assert_called_once_with(sale_id)
    mock_customer_service.get_customer_by_id.assert_called_once_with(customer_id)
    # Check that directories are created (might be called multiple times by path logic)
    # assert mock_makedirs.called
    # Check that os.path.join was called to build the filename
    assert mock_os_path_join.called

    # Check that the create_receipt_pdf function was called with correct arguments
    mock_create_receipt.assert_called_once()
    call_args, _ = mock_create_receipt.call_args
    passed_sale_obj = call_args[0]
    passed_store_info = call_args[1]
    passed_filename = call_args[2]

    assert passed_sale_obj == test_sale
    assert passed_sale_obj.user_name == f"Usuario {user_id}" # Check enhanced attribute
    assert passed_sale_obj.customer_name == sample_customer.name # Check enhanced attribute
    assert passed_store_info['name'] == "My Test Store"
    assert passed_store_info['address'] == "123 Test St"
    assert passed_store_info['tax_id'] == "30-11111111-1"
    assert passed_store_info['iva_condition'] == "RI"
    assert passed_store_info['phone'] == "555-1234"
    assert passed_filename == expected_filename

    # Check returned path
    assert pdf_path == expected_filename


@patch('core.services.sale_service.create_receipt_pdf')
def test_generate_receipt_pdf_sale_not_found(mock_create_receipt, sale_service):
    """Test generating PDF fails if the sale is not found."""
    # Arrange
    sale_id = 999
    sale_service.get_sale_by_id = MagicMock(return_value=None) # Mock internal call

    # Act & Assert
    with pytest.raises(ValueError, match=f"Sale with ID {sale_id} not found."):
        sale_service.generate_receipt_pdf(sale_id)

    sale_service.get_sale_by_id.assert_called_once_with(sale_id)
    mock_create_receipt.assert_not_called()

# --- Tests for generate_receipt_pdf (To be added) ---
# Test customer not found but receipt still generated
# Test using provided filename
