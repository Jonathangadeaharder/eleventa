import pytest
import os
from unittest.mock import MagicMock, patch
from core.models import Sale, Product, Customer
from core.services.sale_service import SaleService
from decimal import Decimal

@pytest.fixture
def mock_sale_service(product1):
    """Create a mocked sale service for testing."""
    sale_repo_factory = MagicMock()
    product_repo_factory = MagicMock()
    customer_repo_factory = MagicMock()
    inventory_service = MagicMock()
    customer_service = MagicMock()
    
    # Configure product_repo_factory to return product1 when get_by_id is called
    mock_product_repo = MagicMock()
    mock_product_repo.get_by_id.return_value = product1
    product_repo_factory.return_value = mock_product_repo
    
    # Configure the repository
    mock_repo = MagicMock()
    sale_repo_factory.return_value = mock_repo
    
    return SaleService(
        sale_repo_factory=sale_repo_factory,
        product_repo_factory=product_repo_factory,
        customer_repo_factory=customer_repo_factory,
        inventory_service=inventory_service,
        customer_service=customer_service
    )

@pytest.fixture
def product1():
    """Return a sample product for testing."""
    return Product(
        id=1,
        code="PROD1",
        description="Test Product 1",
        sell_price=Decimal("10.00"),
        cost_price=Decimal("5.00"),
        department_id=1
    )

@pytest.fixture
def sample_customer():
    """Return a sample customer for testing."""
    return Customer(
        id=5,
        name="Test Customer",
        cuit="12345"
    )

def test_create_sale_success(mock_sale_service, product1, sample_customer):
    """Test successful sale creation with valid data."""
    # Arrange
    items_data = [{'product_id': 1, 'quantity': '2'}]
    user_id = 1
    payment_type = 'cash'

    # Create a mock sale object with expected attributes
    mock_sale = MagicMock(spec=Sale)
    mock_sale.id = 1
    mock_sale.user_id = user_id
    mock_sale.is_credit_sale = False

    # Configure the repository to return the mock sale after add_sale is called
    mock_sale_service.sale_repo_factory().add_sale.return_value = mock_sale

    # Act
    sale = mock_sale_service.create_sale(
        items_data=items_data,
        user_id=user_id,
        payment_type=payment_type,
        session=MagicMock()
    )

    # Assert
    assert sale is not None
    assert sale.id == 1
    assert sale.user_id == user_id
    assert sale.is_credit_sale == False

    # Verify the repo factory was called
    mock_sale_service.sale_repo_factory().add_sale.assert_called_once()
    
    # Verify product repository was called to get product details
    mock_sale_service.product_repo_factory().get_by_id.assert_called_with(1)

def test_create_sale_with_credit(mock_sale_service, product1, sample_customer):
    """Test credit sale creation with valid customer."""
    # Arrange
    items_data = [{'product_id': 1, 'quantity': '1'}]
    user_id = 1
    customer_id = 5

    # Create a mock sale object with expected attributes
    mock_sale = MagicMock(spec=Sale)
    mock_sale.id = 1
    mock_sale.user_id = user_id
    mock_sale.is_credit_sale = True

    # Configure the repository to return the mock sale when add_sale is called
    mock_sale_service.sale_repo_factory().add_sale.return_value = mock_sale

    # Act
    sale = mock_sale_service.create_sale(
        items_data=items_data,
        user_id=user_id,
        payment_type=None,  # Payment type not needed for credit sales
        customer_id=customer_id,
        is_credit_sale=True,
        session=MagicMock()
    )

    # Assert
    assert sale is not None
    assert sale.id == 1
    assert sale.user_id == user_id
    assert sale.is_credit_sale is True

    # Verify the call was made
    mock_sale_service.sale_repo_factory().add_sale.assert_called_once()
    
    # Verify product repository was called to get product details
    mock_sale_service.product_repo_factory().get_by_id.assert_called_with(1)

def test_get_sale_by_id(mock_sale_service):
    """Test retrieving a sale by ID."""
    # Arrange
    sale_id = 1
    mock_sale = MagicMock(spec=Sale)
    mock_sale.id = sale_id
    
    mock_sale_service.sale_repo_factory().get_by_id.return_value = mock_sale

    # Act
    sale = mock_sale_service.get_sale_by_id(sale_id)

    # Assert
    assert sale is not None
    assert sale.id == sale_id

@patch('core.services.sale_service.create_receipt_pdf')
def test_generate_receipt_pdf(mock_create_receipt, mock_sale_service):
    """Test PDF receipt generation."""
    # Arrange
    sale_id = 1
    output_dir = "test_receipts"
    expected_path = os.path.join(output_dir, f"receipt_{sale_id}.pdf")
    
    # Configure the mock to return the expected path
    mock_create_receipt.return_value = expected_path

    # Act
    result = mock_sale_service.generate_receipt_pdf(sale_id, output_dir)

    # Assert
    assert result == expected_path
    mock_create_receipt.assert_called_once()
