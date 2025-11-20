"""
Tests for Use Cases / Application Layer

Tests the use case execution, validation, and result handling.
"""

import pytest
from unittest.mock import Mock, MagicMock
from decimal import Decimal
from uuid import UUID, uuid4

from core.use_cases.base import UseCase, UseCaseResult, UseCaseStatus
from core.use_cases.dtos import (
    CreateProductRequest,
    UpdateProductRequest,
    ProductResponse,
    ProcessSaleRequest,
    SaleItemRequest,
)
from core.use_cases.product_use_cases import (
    CreateProductUseCase,
    UpdateProductUseCase,
    SearchProductsUseCase,
)
from core.models.product import Product


# Fixtures

@pytest.fixture
def mock_product_service():
    """Create a mock product service."""
    return Mock()


@pytest.fixture
def test_product():
    """Create a test product."""
    return Product(
        id=uuid4(),
        code="TEST001",
        description="Test Product",
        sell_price=Decimal('99.99'),
        cost_price=Decimal('75.00'),
        quantity_in_stock=Decimal('10')
    )


# Test UseCaseResult

class TestUseCaseResult:
    """Test UseCaseResult functionality."""

    def test_success_result(self):
        """Test creating a success result."""
        data = {"key": "value"}
        result = UseCaseResult.success(data)

        assert result.is_success
        assert not result.is_failure
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data == data
        assert result.error is None

    def test_failure_result(self):
        """Test creating a failure result."""
        error_msg = "Something went wrong"
        result = UseCaseResult.failure(error_msg)

        assert result.is_failure
        assert not result.is_success
        assert result.status == UseCaseStatus.FAILURE
        assert result.error == error_msg
        assert result.data is None

    def test_validation_error_result(self):
        """Test creating a validation error result."""
        errors = {
            'code': 'Required',
            'price': 'Must be positive'
        }
        result = UseCaseResult.validation_error(errors)

        assert result.is_failure
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert result.errors == errors
        assert result.error == "Validation failed"

    def test_not_found_result(self):
        """Test creating a not found result."""
        result = UseCaseResult.not_found("Product")

        assert result.is_failure
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "Product not found" in result.error

    def test_conflict_result(self):
        """Test creating a conflict result."""
        message = "Code already exists"
        result = UseCaseResult.conflict(message)

        assert result.is_failure
        assert result.status == UseCaseStatus.CONFLICT
        assert result.error == message


# Test CreateProductUseCase

class TestCreateProductUseCase:
    """Test creating products via use case."""

    def test_create_product_success(self, mock_product_service, test_product):
        """Test successful product creation."""
        # Setup
        mock_product_service.add_product.return_value = test_product
        use_case = CreateProductUseCase(mock_product_service)

        request = CreateProductRequest(
            code="TEST001",
            description="Test Product",
            sell_price=Decimal('99.99'),
            cost_price=Decimal('75.00')
        )

        # Execute
        result = use_case.execute(request)

        # Verify
        assert result.is_success
        assert result.data.code == "TEST001"
        assert result.data.sell_price == Decimal('99.99')
        mock_product_service.add_product.assert_called_once()

    def test_create_product_missing_code(self, mock_product_service):
        """Test validation error for missing code."""
        use_case = CreateProductUseCase(mock_product_service)

        request = CreateProductRequest(
            code="",  # Empty code
            description="Test Product",
            sell_price=Decimal('99.99')
        )

        result = use_case.execute(request)

        assert result.is_failure
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert 'code' in result.errors

    def test_create_product_invalid_price(self, mock_product_service):
        """Test validation error for invalid price."""
        use_case = CreateProductUseCase(mock_product_service)

        request = CreateProductRequest(
            code="TEST001",
            description="Test Product",
            sell_price=Decimal('-10')  # Negative price
        )

        result = use_case.execute(request)

        assert result.is_failure
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert 'sell_price' in result.errors

    def test_create_product_duplicate_code(self, mock_product_service):
        """Test conflict when code already exists."""
        mock_product_service.add_product.side_effect = ValueError(
            "Code already exists"
        )
        use_case = CreateProductUseCase(mock_product_service)

        request = CreateProductRequest(
            code="EXISTING",
            description="Test Product",
            sell_price=Decimal('99.99')
        )

        result = use_case.execute(request)

        assert result.is_failure
        assert result.status == UseCaseStatus.CONFLICT

    def test_create_product_multiple_validation_errors(self, mock_product_service):
        """Test multiple validation errors at once."""
        use_case = CreateProductUseCase(mock_product_service)

        request = CreateProductRequest(
            code="",  # Missing
            description="",  # Missing
            sell_price=Decimal('0')  # Invalid
        )

        result = use_case.execute(request)

        assert result.is_failure
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert 'code' in result.errors
        assert 'description' in result.errors
        assert 'sell_price' in result.errors


# Test UpdateProductUseCase

class TestUpdateProductUseCase:
    """Test updating products via use case."""

    def test_update_product_success(self, mock_product_service, test_product):
        """Test successful product update."""
        # Setup
        mock_product_service.get_product_by_id.return_value = test_product
        updated_product = Product(**{**test_product.__dict__, 'sell_price': Decimal('149.99')})
        mock_product_service.update_product.return_value = updated_product

        use_case = UpdateProductUseCase(mock_product_service)

        request = UpdateProductRequest(
            product_id=test_product.id,
            sell_price=Decimal('149.99')
        )

        # Execute
        result = use_case.execute(request)

        # Verify
        assert result.is_success
        assert result.data.sell_price == Decimal('149.99')
        mock_product_service.update_product.assert_called_once()

    def test_update_product_not_found(self, mock_product_service):
        """Test updating non-existent product."""
        mock_product_service.get_product_by_id.return_value = None
        use_case = UpdateProductUseCase(mock_product_service)

        request = UpdateProductRequest(
            product_id=uuid4(),
            sell_price=Decimal('149.99')
        )

        result = use_case.execute(request)

        assert result.is_failure
        assert result.status == UseCaseStatus.NOT_FOUND

    def test_update_product_partial_update(self, mock_product_service, test_product):
        """Test partial update (only some fields)."""
        mock_product_service.get_product_by_id.return_value = test_product
        mock_product_service.update_product.return_value = test_product

        use_case = UpdateProductUseCase(mock_product_service)

        # Only update description, leave price unchanged
        request = UpdateProductRequest(
            product_id=test_product.id,
            description="Updated Description"
        )

        result = use_case.execute(request)

        assert result.is_success
        # Verify only description was changed
        called_product = mock_product_service.update_product.call_args[0][0]
        assert called_product.description == "Updated Description"


# Test SearchProductsUseCase

class TestSearchProductsUseCase:
    """Test searching products."""

    def test_search_all_products(self, mock_product_service):
        """Test searching all products."""
        products = [
            Product(id=uuid4(), code="PROD001", description="Product 1", sell_price=Decimal('10')),
            Product(id=uuid4(), code="PROD002", description="Product 2", sell_price=Decimal('20')),
        ]
        mock_product_service.get_all_products.return_value = products

        use_case = SearchProductsUseCase(mock_product_service)

        from core.use_cases.dtos import SearchProductsRequest
        request = SearchProductsRequest()

        result = use_case.execute(request)

        assert result.is_success
        assert result.data.total_count == 2
        assert len(result.data.products) == 2

    def test_search_with_term(self, mock_product_service):
        """Test searching with search term."""
        products = [
            Product(id=uuid4(), code="LAPTOP001", description="Dell Laptop", sell_price=Decimal('999')),
            Product(id=uuid4(), code="LAPTOP002", description="HP Laptop", sell_price=Decimal('899')),
            Product(id=uuid4(), code="MOUSE001", description="Wireless Mouse", sell_price=Decimal('25')),
        ]
        mock_product_service.get_all_products.return_value = products

        use_case = SearchProductsUseCase(mock_product_service)

        from core.use_cases.dtos import SearchProductsRequest
        request = SearchProductsRequest(search_term="laptop")

        result = use_case.execute(request)

        assert result.is_success
        assert result.data.total_count == 2  # Only laptops
        assert all('laptop' in p.code.lower() or 'laptop' in p.description.lower()
                   for p in result.data.products)

    def test_search_in_stock_only(self, mock_product_service):
        """Test filtering by in-stock status."""
        products = [
            Product(id=uuid4(), code="PROD001", description="In Stock",
                   sell_price=Decimal('10'), quantity_in_stock=Decimal('5')),
            Product(id=uuid4(), code="PROD002", description="Out of Stock",
                   sell_price=Decimal('20'), quantity_in_stock=Decimal('0')),
        ]
        mock_product_service.get_all_products.return_value = products

        use_case = SearchProductsUseCase(mock_product_service)

        from core.use_cases.dtos import SearchProductsRequest
        request = SearchProductsRequest(in_stock_only=True)

        result = use_case.execute(request)

        assert result.is_success
        assert result.data.total_count == 1  # Only in-stock product
        assert result.data.products[0].quantity_in_stock > 0


# Test ProcessSaleUseCase (Complex orchestration)

class TestProcessSaleUseCase:
    """Test processing sales (complex use case)."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services for sale processing."""
        return {
            'sale_service': Mock(),
            'product_service': Mock(),
            'customer_service': Mock(),
            'inventory_service': Mock(),
        }

    def test_process_simple_cash_sale(self, mock_services):
        """Test processing a simple cash sale."""
        from core.use_cases.sale_use_cases import ProcessSaleUseCase

        # Setup products
        product1 = Product(
            id=uuid4(), code="PROD001", description="Product 1",
            sell_price=Decimal('100'), quantity_in_stock=Decimal('10')
        )
        mock_services['product_service'].get_product_by_code.return_value = product1
        mock_services['product_service'].get_product_by_id.return_value = product1

        # Setup sale service
        from core.models.sale import Sale
        sale = Sale(
            id=uuid4(),
            total=Decimal('100'),
            payment_type='cash',
            paid_amount=Decimal('150'),
            change_amount=Decimal('50'),
            items=[]
        )
        mock_services['sale_service'].add_sale = Mock(return_value=sale)

        use_case = ProcessSaleUseCase(**mock_services)

        request = ProcessSaleRequest(
            items=[SaleItemRequest(product_code="PROD001", quantity=Decimal('1'))],
            payment_type="cash",
            paid_amount=Decimal('150')
        )

        # Note: This test is simplified - actual use case uses UoW
        # For full integration test, see integration tests
        # Here we're testing the validation logic

        # Validate request
        errors = use_case._validate_request(request)
        assert errors is None  # Should pass validation

    def test_process_sale_validation_missing_items(self, mock_services):
        """Test validation error for missing items."""
        from core.use_cases.sale_use_cases import ProcessSaleUseCase

        use_case = ProcessSaleUseCase(**mock_services)

        request = ProcessSaleRequest(
            items=[],  # No items
            payment_type="cash",
            paid_amount=Decimal('100')
        )

        errors = use_case._validate_request(request)
        assert errors is not None
        assert 'items' in errors

    def test_process_sale_validation_invalid_payment_type(self, mock_services):
        """Test validation error for invalid payment type."""
        from core.use_cases.sale_use_cases import ProcessSaleUseCase

        use_case = ProcessSaleUseCase(**mock_services)

        request = ProcessSaleRequest(
            items=[SaleItemRequest(product_code="PROD001", quantity=Decimal('1'))],
            payment_type="bitcoin",  # Invalid
            paid_amount=Decimal('100')
        )

        errors = use_case._validate_request(request)
        assert errors is not None
        assert 'payment_type' in errors

    def test_process_sale_credit_requires_customer(self, mock_services):
        """Test validation error for credit sale without customer."""
        from core.use_cases.sale_use_cases import ProcessSaleUseCase

        use_case = ProcessSaleUseCase(**mock_services)

        request = ProcessSaleRequest(
            items=[SaleItemRequest(product_code="PROD001", quantity=Decimal('1'))],
            payment_type="credit",
            customer_id=None,  # Missing customer
            paid_amount=Decimal('0')
        )

        errors = use_case._validate_request(request)
        assert errors is not None
        assert 'customer_id' in errors


# Test DTOs

class TestDTOs:
    """Test Data Transfer Objects."""

    def test_create_product_request_to_domain(self):
        """Test converting request DTO to domain model."""
        request = CreateProductRequest(
            code="TEST001",
            description="Test Product",
            sell_price=Decimal('99.99'),
            cost_price=Decimal('75.00')
        )

        domain_product = request.to_domain()

        assert isinstance(domain_product, Product)
        assert domain_product.code == "TEST001"
        assert domain_product.sell_price == Decimal('99.99')

    def test_product_response_from_domain(self):
        """Test converting domain model to response DTO."""
        product = Product(
            id=uuid4(),
            code="TEST001",
            description="Test Product",
            sell_price=Decimal('99.99'),
            quantity_in_stock=Decimal('10')
        )

        response = ProductResponse.from_domain(product)

        assert response.code == "TEST001"
        assert response.sell_price == Decimal('99.99')
        assert response.quantity_in_stock == Decimal('10')
