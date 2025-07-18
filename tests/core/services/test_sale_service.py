import pytest
import os
from unittest.mock import MagicMock, patch
from core.models import Sale, Product, Customer
from core.models.enums import PaymentType
from core.services.sale_service import SaleService
from decimal import Decimal

@pytest.fixture
def mock_sale_service(product1):
    """Create a mocked sale service for testing."""
    inventory_service = MagicMock()
    customer_service = MagicMock()
    
    service = SaleService(
        inventory_service=inventory_service,
        customer_service=customer_service
    )
    
    return service

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

@patch('core.services.sale_service.unit_of_work')
def test_create_sale_success(mock_unit_of_work, mock_sale_service, product1, sample_customer):
    """Test successful sale creation with valid data."""
    # Arrange
    items_data = [{'product_id': 1, 'quantity': '2'}]
    user_id = 1
    payment_type = PaymentType.EFECTIVO

    # Create a mock sale object with expected attributes
    mock_sale = MagicMock(spec=Sale)
    mock_sale.id = 1
    mock_sale.user_id = user_id
    mock_sale.is_credit_sale = False

    # Setup Unit of Work mock
    mock_uow = MagicMock()
    mock_uow.sales.add_sale.return_value = mock_sale
    mock_uow.products.get_by_id.return_value = product1
    mock_unit_of_work.return_value.__enter__.return_value = mock_uow

    # Act
    sale = mock_sale_service.create_sale(
        items_data=items_data,
        user_id=user_id,
        payment_type=payment_type
    )

    # Assert
    assert sale is not None
    assert sale.id == 1
    assert sale.user_id == user_id
    assert sale.is_credit_sale == False

    # Verify the unit of work was used
    mock_unit_of_work.assert_called_once()
    mock_uow.sales.add_sale.assert_called_once()

@patch('core.services.sale_service.unit_of_work')
def test_create_sale_with_credit(mock_unit_of_work, mock_sale_service, product1, sample_customer):
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

    # Setup Unit of Work mock
    mock_uow = MagicMock()
    mock_uow.sales.add_sale.return_value = mock_sale
    mock_uow.products.get_by_id.return_value = product1
    mock_unit_of_work.return_value.__enter__.return_value = mock_uow

    # Act
    sale = mock_sale_service.create_sale(
        items_data=items_data,
        user_id=user_id,
        payment_type=None,  # Payment type not needed for credit sales
        customer_id=customer_id,
        is_credit_sale=True
    )

    # Assert
    assert sale is not None
    assert sale.id == 1
    assert sale.user_id == user_id
    assert sale.is_credit_sale is True

    # Verify the unit of work was used
    mock_unit_of_work.assert_called_once()
    mock_uow.sales.add_sale.assert_called_once()

@patch('core.services.sale_service.unit_of_work')
def test_get_sale_by_id(mock_unit_of_work, mock_sale_service):
    """Test retrieving a sale by ID."""
    # Arrange
    sale_id = 1
    mock_sale = MagicMock(spec=Sale)
    mock_sale.id = sale_id
    
    # Setup Unit of Work mock
    mock_uow = MagicMock()
    mock_uow.sales.get_by_id.return_value = mock_sale
    mock_unit_of_work.return_value.__enter__.return_value = mock_uow

    # Act
    sale = mock_sale_service.get_sale_by_id(sale_id)

    # Assert
    assert sale is not None
    assert sale.id == sale_id
    
    # Verify the unit of work was used
    mock_unit_of_work.assert_called_once()
    mock_uow.sales.get_by_id.assert_called_once_with(sale_id)

@patch('infrastructure.reporting.document_generator.DocumentPdfGenerator.generate_receipt_from_sale')
@patch('core.services.sale_service.unit_of_work')
def test_generate_receipt_pdf(mock_unit_of_work, mock_generate_receipt, mock_sale_service):
    """Test PDF receipt generation."""
    # Arrange
    sale_id = 1
    output_dir = "test_receipts"
    expected_path = os.path.join(output_dir, f"receipt_{sale_id}.pdf")
    
    # Create a mock sale object
    mock_sale = MagicMock(spec=Sale)
    mock_sale.id = sale_id
    
    # Setup Unit of Work mock
    mock_uow = MagicMock()
    mock_uow.sales.get_by_id.return_value = mock_sale
    mock_unit_of_work.return_value.__enter__.return_value = mock_uow
    
    # Configure the mock to return success
    mock_generate_receipt.return_value = True

    # Act
    result = mock_sale_service.generate_receipt_pdf(sale_id, output_dir)

    # Assert
    assert result == expected_path
    mock_generate_receipt.assert_called_once_with(mock_sale, expected_path)
    
    # Verify the unit of work was used
    mock_unit_of_work.assert_called_once()
    mock_uow.sales.get_by_id.assert_called_once_with(sale_id)
