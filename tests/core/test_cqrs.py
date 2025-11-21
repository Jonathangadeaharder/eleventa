"""
Tests for CQRS (Command Query Responsibility Segregation)

Tests commands, queries, handlers, and read models.
"""

import pytest
from unittest.mock import Mock, MagicMock
from decimal import Decimal
from uuid import UUID, uuid4

from core.cqrs.commands import (
    CreateProductCommand,
    UpdateProductCommand,
    DeleteProductCommand,
    ProcessSaleCommand,
    SaleItemCommand,
)

from core.cqrs.queries import (
    GetProductByIdQuery,
    GetProductByCodeQuery,
    SearchProductsQuery,
    GetLowStockProductsQuery,
)

from core.cqrs.read_models import (
    ProductReadModel,
    ProductListItemReadModel,
    SaleReadModel,
    DashboardSummaryReadModel,
)

from core.cqrs.handlers import (
    CreateProductCommandHandler,
    UpdateProductCommandHandler,
    GetProductByIdQueryHandler,
    SearchProductsQueryHandler,
)

from core.use_cases.base import UseCaseStatus
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
        quantity_in_stock=Decimal('10'),
        min_stock=Decimal('5')
    )


# Test Commands

class TestCommands:
    """Test command objects."""

    def test_create_product_command_is_immutable(self):
        """Test that commands are immutable (frozen)."""
        command = CreateProductCommand(
            code="TEST",
            description="Test",
            sell_price=Decimal('99.99')
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            command.code = "MODIFIED"

    def test_create_product_command_has_required_fields(self):
        """Test command creation with required fields."""
        command = CreateProductCommand(
            code="TEST001",
            description="Test Product",
            sell_price=Decimal('99.99')
        )

        assert command.code == "TEST001"
        assert command.description == "Test Product"
        assert command.sell_price == Decimal('99.99')

    def test_process_sale_command_with_items(self):
        """Test sale command with multiple items."""
        command = ProcessSaleCommand(
            items=[
                SaleItemCommand(product_code="PROD001", quantity=Decimal('1')),
                SaleItemCommand(product_code="PROD002", quantity=Decimal('2')),
            ],
            payment_type="cash",
            paid_amount=Decimal('100')
        )

        assert len(command.items) == 2
        assert command.items[0].product_code == "PROD001"
        assert command.payment_type == "cash"


# Test Queries

class TestQueries:
    """Test query objects."""

    def test_get_product_by_id_query(self):
        """Test product query by ID."""
        product_id = uuid4()
        query = GetProductByIdQuery(product_id=product_id)

        assert query.product_id == product_id

    def test_search_products_query_with_filters(self):
        """Test search query with multiple filters."""
        query = SearchProductsQuery(
            search_term="laptop",
            department_id=uuid4(),
            in_stock_only=True,
            min_price=Decimal('100'),
            max_price=Decimal('1000'),
            limit=50,
            offset=10
        )

        assert query.search_term == "laptop"
        assert query.in_stock_only is True
        assert query.limit == 50
        assert query.offset == 10

    def test_search_products_query_defaults(self):
        """Test query with default values."""
        query = SearchProductsQuery()

        assert query.search_term is None
        assert query.in_stock_only is False
        assert query.limit == 100
        assert query.offset == 0


# Test Read Models

class TestReadModels:
    """Test read model objects."""

    def test_product_read_model_is_immutable(self):
        """Test that read models are immutable."""
        read_model = ProductReadModel(
            id=uuid4(),
            code="TEST",
            description="Test",
            sell_price=Decimal('99.99'),
            cost_price=Decimal('75.00'),
            quantity_in_stock=Decimal('10'),
            min_stock=Decimal('5'),
            max_stock=None,
            uses_inventory=True,
            department_id=None,
            department_name=None,
            unit_id=None,
            unit_name=None,
            in_stock=True,
            is_low_stock=False,
            stock_value=Decimal('750.00')
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            read_model.sell_price = Decimal('149.99')

    def test_product_read_model_has_denormalized_fields(self):
        """Test that read model includes denormalized data."""
        read_model = ProductReadModel(
            id=uuid4(),
            code="TEST",
            description="Test",
            sell_price=Decimal('99.99'),
            cost_price=Decimal('75.00'),
            quantity_in_stock=Decimal('10'),
            min_stock=Decimal('5'),
            max_stock=None,
            uses_inventory=True,
            department_id=uuid4(),
            department_name="Electronics",  # Denormalized!
            unit_id=uuid4(),
            unit_name="pieces",  # Denormalized!
            in_stock=True,
            is_low_stock=False,
            stock_value=Decimal('750.00')
        )

        # These fields come from other tables but are denormalized
        assert read_model.department_name == "Electronics"
        assert read_model.unit_name == "pieces"

    def test_product_read_model_has_computed_fields(self):
        """Test that read model includes computed fields."""
        read_model = ProductReadModel(
            id=uuid4(),
            code="TEST",
            description="Test",
            sell_price=Decimal('99.99'),
            cost_price=Decimal('75.00'),
            quantity_in_stock=Decimal('10'),
            min_stock=Decimal('15'),  # quantity < min
            max_stock=None,
            uses_inventory=True,
            department_id=None,
            department_name=None,
            unit_id=None,
            unit_name=None,
            in_stock=True,  # Computed
            is_low_stock=True,  # Computed
            stock_value=Decimal('750.00')  # Computed
        )

        assert read_model.in_stock is True
        assert read_model.is_low_stock is True  # quantity < min_stock
        assert read_model.stock_value == Decimal('750.00')  # 10 * 75

    def test_product_list_item_read_model_is_lightweight(self):
        """Test that list item model only has essential fields."""
        list_item = ProductListItemReadModel(
            id=uuid4(),
            code="TEST",
            description="Test",
            sell_price=Decimal('99.99'),
            quantity_in_stock=Decimal('10'),
            department_name="Electronics",
            in_stock=True,
            is_low_stock=False
        )

        # Has essential fields
        assert list_item.code == "TEST"
        assert list_item.sell_price == Decimal('99.99')

        # Doesn't have cost_price, min_stock, etc. (lighter weight)
        assert not hasattr(list_item, 'cost_price')
        assert not hasattr(list_item, 'min_stock')


# Test Command Handlers

class TestCommandHandlers:
    """Test command handler execution."""

    def test_create_product_command_handler_success(self, mock_product_service, test_product):
        """Test successful command execution."""
        # Setup
        mock_product_service.add_product.return_value = test_product
        handler = CreateProductCommandHandler(mock_product_service)

        command = CreateProductCommand(
            code="TEST001",
            description="Test Product",
            sell_price=Decimal('99.99')
        )

        # Execute
        result = handler.handle(command)

        # Verify
        assert result.is_success
        assert result.data == test_product.id
        mock_product_service.add_product.assert_called_once()

    def test_create_product_command_handler_validation_error(self, mock_product_service):
        """Test command validation."""
        handler = CreateProductCommandHandler(mock_product_service)

        command = CreateProductCommand(
            code="",  # Invalid
            description="",  # Invalid
            sell_price=Decimal('-10')  # Invalid
        )

        result = handler.handle(command)

        assert result.is_failure
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert 'code' in result.errors
        assert 'description' in result.errors
        assert 'sell_price' in result.errors

    def test_create_product_command_handler_conflict(self, mock_product_service):
        """Test duplicate code conflict."""
        mock_product_service.add_product.side_effect = ValueError("Code already exists")
        handler = CreateProductCommandHandler(mock_product_service)

        command = CreateProductCommand(
            code="EXISTING",
            description="Test",
            sell_price=Decimal('99.99')
        )

        result = handler.handle(command)

        assert result.is_failure
        assert result.status == UseCaseStatus.CONFLICT

    def test_update_product_command_handler_success(self, mock_product_service, test_product):
        """Test successful product update."""
        # Setup
        updated_product = Product(**{**test_product.__dict__, 'sell_price': Decimal('149.99')})
        mock_product_service.get_product_by_id.return_value = test_product
        mock_product_service.update_product.return_value = updated_product

        handler = UpdateProductCommandHandler(mock_product_service)

        command = UpdateProductCommand(
            product_id=test_product.id,
            sell_price=Decimal('149.99')
        )

        # Execute
        result = handler.handle(command)

        # Verify
        assert result.is_success
        assert result.data == test_product.id
        mock_product_service.update_product.assert_called_once()

    def test_update_product_command_handler_not_found(self, mock_product_service):
        """Test updating non-existent product."""
        mock_product_service.get_product_by_id.return_value = None
        handler = UpdateProductCommandHandler(mock_product_service)

        command = UpdateProductCommand(
            product_id=uuid4(),
            sell_price=Decimal('149.99')
        )

        result = handler.handle(command)

        assert result.is_failure
        assert result.status == UseCaseStatus.NOT_FOUND


# Test Query Handlers

class TestQueryHandlers:
    """Test query handler execution."""

    def test_get_product_by_id_query_handler_success(self, mock_product_service, test_product):
        """Test successful product query."""
        # Setup
        mock_product_service.get_product_by_id.return_value = test_product
        handler = GetProductByIdQueryHandler(mock_product_service)

        query = GetProductByIdQuery(product_id=test_product.id)

        # Execute
        result = handler.handle(query)

        # Verify
        assert result is not None
        assert isinstance(result, ProductReadModel)
        assert result.code == test_product.code
        assert result.sell_price == test_product.sell_price

    def test_get_product_by_id_query_handler_not_found(self, mock_product_service):
        """Test query for non-existent product."""
        # Setup
        mock_product_service.get_product_by_id.return_value = None
        handler = GetProductByIdQueryHandler(mock_product_service)

        query = GetProductByIdQuery(product_id=uuid4())

        # Execute
        result = handler.handle(query)

        # Verify - queries return None, not errors!
        assert result is None

    def test_query_handler_converts_to_read_model(self, mock_product_service, test_product):
        """Test that query handler converts domain model to read model."""
        # Setup
        mock_product_service.get_product_by_id.return_value = test_product
        handler = GetProductByIdQueryHandler(mock_product_service)

        # Execute
        result = handler.handle(GetProductByIdQuery(product_id=test_product.id))

        # Verify it's a read model, not domain model
        assert isinstance(result, ProductReadModel)
        assert hasattr(result, 'in_stock')  # Computed field
        assert hasattr(result, 'is_low_stock')  # Computed field
        assert hasattr(result, 'stock_value')  # Computed field
        assert hasattr(result, 'department_name')  # Denormalized field

    def test_search_products_query_handler(self, mock_product_service):
        """Test product search."""
        # Setup products
        products = [
            Product(
                id=uuid4(), code="LAPTOP001", description="Dell Laptop",
                sell_price=Decimal('999'), quantity_in_stock=Decimal('5')
            ),
            Product(
                id=uuid4(), code="LAPTOP002", description="HP Laptop",
                sell_price=Decimal('899'), quantity_in_stock=Decimal('3')
            ),
            Product(
                id=uuid4(), code="MOUSE001", description="Wireless Mouse",
                sell_price=Decimal('25'), quantity_in_stock=Decimal('50')
            ),
        ]
        mock_product_service.get_all_products.return_value = products

        handler = SearchProductsQueryHandler(mock_product_service)

        # Execute search
        query = SearchProductsQuery(search_term="laptop")
        results = handler.handle(query)

        # Verify
        assert len(results) == 2  # Only laptops
        assert all('laptop' in r.code.lower() or 'laptop' in r.description.lower()
                   for r in results)

    def test_search_products_with_filters(self, mock_product_service):
        """Test search with multiple filters."""
        products = [
            Product(
                id=uuid4(), code="PROD001", description="Product 1",
                sell_price=Decimal('100'), quantity_in_stock=Decimal('5')
            ),
            Product(
                id=uuid4(), code="PROD002", description="Product 2",
                sell_price=Decimal('200'), quantity_in_stock=Decimal('0')  # Out of stock
            ),
        ]
        mock_product_service.get_all_products.return_value = products

        handler = SearchProductsQueryHandler(mock_product_service)

        # Execute with in_stock_only filter
        query = SearchProductsQuery(in_stock_only=True)
        results = handler.handle(query)

        # Verify
        assert len(results) == 1  # Only in-stock product
        assert results[0].code == "PROD001"

    def test_search_products_pagination(self, mock_product_service):
        """Test search pagination."""
        products = [
            Product(id=uuid4(), code=f"PROD{i:03d}", description=f"Product {i}",
                   sell_price=Decimal('100'), quantity_in_stock=Decimal('10'))
            for i in range(1, 101)  # 100 products
        ]
        mock_product_service.get_all_products.return_value = products

        handler = SearchProductsQueryHandler(mock_product_service)

        # Execute with pagination
        query = SearchProductsQuery(limit=10, offset=20)
        results = handler.handle(query)

        # Verify
        assert len(results) == 10  # Limited to 10
        assert results[0].code == "PROD021"  # Offset by 20


# Test CQRS Separation

class TestCQRSSeparation:
    """Test that CQRS properly separates reads and writes."""

    def test_commands_modify_state(self, mock_product_service):
        """Test that commands modify state."""
        handler = CreateProductCommandHandler(mock_product_service)
        command = CreateProductCommand(
            code="TEST",
            description="Test",
            sell_price=Decimal('99.99')
        )

        handler.handle(command)

        # Verify service method was called (state modified)
        mock_product_service.add_product.assert_called_once()

    def test_queries_never_modify_state(self, mock_product_service):
        """Test that queries never modify state."""
        handler = GetProductByIdQueryHandler(mock_product_service)
        query = GetProductByIdQuery(product_id=uuid4())

        handler.handle(query)

        # Verify only read method was called (no modifications)
        mock_product_service.get_product_by_id.assert_called_once()
        # No add_product, update_product, or delete_product calls
        assert not mock_product_service.add_product.called
        assert not mock_product_service.update_product.called

    def test_commands_can_fail(self, mock_product_service):
        """Test that commands can fail with errors."""
        handler = CreateProductCommandHandler(mock_product_service)
        command = CreateProductCommand(
            code="",  # Invalid
            description="Test",
            sell_price=Decimal('99.99')
        )

        result = handler.handle(command)

        assert result.is_failure
        assert result.error is not None

    def test_queries_never_fail(self, mock_product_service):
        """Test that queries return None/empty, never fail."""
        handler = GetProductByIdQueryHandler(mock_product_service)
        mock_product_service.get_product_by_id.return_value = None

        # Query for non-existent product
        result = handler.handle(GetProductByIdQuery(product_id=uuid4()))

        # Returns None, doesn't raise or return error
        assert result is None

        # Search query
        search_handler = SearchProductsQueryHandler(mock_product_service)
        mock_product_service.get_all_products.return_value = []

        results = search_handler.handle(SearchProductsQuery())

        # Returns empty list, doesn't raise or return error
        assert results == []
