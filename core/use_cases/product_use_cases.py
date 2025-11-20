"""
Product Use Cases

These use cases encapsulate all product-related business operations,
providing a clean API for the presentation layer.
"""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from core.use_cases.base import UseCase, UseCaseResult, QueryUseCase, log_use_case_execution
from core.use_cases.dtos import (
    CreateProductRequest,
    UpdateProductRequest,
    ProductResponse,
    GetProductByCodeRequest,
    SearchProductsRequest,
    ProductListResponse,
    BulkPriceUpdateRequest,
    BulkPriceUpdateResponse,
)
from core.services.product_service import ProductService


class CreateProductUseCase(UseCase[CreateProductRequest, ProductResponse]):
    """
    Use case for creating a new product.

    Orchestrates:
    - Product validation
    - Product creation via service
    - Event publishing (ProductCreated)

    Example:
        use_case = CreateProductUseCase(product_service)
        request = CreateProductRequest(
            code="LAPTOP001",
            description="Dell Laptop",
            sell_price=Decimal('999.99')
        )
        result = use_case.execute(request)

        if result.is_success:
            product = result.data
            print(f"Created product: {product.code}")
        else:
            print(f"Error: {result.error}")
    """

    def __init__(self, product_service: ProductService):
        """
        Initialize the use case.

        Args:
            product_service: The product service for business logic
        """
        super().__init__()
        self.product_service = product_service

    @log_use_case_execution
    def execute(self, request: CreateProductRequest) -> UseCaseResult[ProductResponse]:
        """
        Execute the create product use case.

        Args:
            request: The create product request

        Returns:
            UseCaseResult containing the created product or error
        """
        # Validation
        validation_errors = self._validate_request(request)
        if validation_errors:
            return UseCaseResult.validation_error(validation_errors)

        # Execute business logic
        try:
            domain_product = request.to_domain()
            created_product = self.product_service.add_product(
                domain_product,
                user_id=request.user_id
            )

            # Convert to response DTO
            response = ProductResponse.from_domain(created_product)
            return UseCaseResult.success(response)

        except ValueError as e:
            # Business rule violation
            if "already exists" in str(e).lower():
                return UseCaseResult.conflict(str(e))
            return UseCaseResult.failure(str(e))

        except Exception as e:
            # Unexpected error
            self.logger.error(f"Unexpected error creating product: {e}", exc_info=True)
            return UseCaseResult.failure(f"An unexpected error occurred: {str(e)}")

    def _validate_request(self, request: CreateProductRequest) -> Optional[dict]:
        """
        Validate the request.

        Returns:
            Dictionary of validation errors, or None if valid
        """
        errors = {}

        if not request.code or not request.code.strip():
            errors['code'] = 'Product code is required'

        if not request.description or not request.description.strip():
            errors['description'] = 'Description is required'

        if request.sell_price is None or request.sell_price <= 0:
            errors['sell_price'] = 'Sell price must be greater than zero'

        if request.cost_price is not None and request.cost_price < 0:
            errors['cost_price'] = 'Cost price cannot be negative'

        if request.quantity_in_stock < 0:
            errors['quantity_in_stock'] = 'Quantity cannot be negative'

        return errors if errors else None


class UpdateProductUseCase(UseCase[UpdateProductRequest, ProductResponse]):
    """
    Use case for updating an existing product.

    Handles partial updates and publishes appropriate events.
    """

    def __init__(self, product_service: ProductService):
        super().__init__()
        self.product_service = product_service

    @log_use_case_execution
    def execute(self, request: UpdateProductRequest) -> UseCaseResult[ProductResponse]:
        """Execute the update product use case."""
        # Validation
        validation_errors = self._validate_request(request)
        if validation_errors:
            return UseCaseResult.validation_error(validation_errors)

        try:
            # Get existing product
            existing_product = self.product_service.get_product_by_id(request.product_id)
            if not existing_product:
                return UseCaseResult.not_found("Product")

            # Apply updates (only non-None fields)
            if request.code is not None:
                existing_product.code = request.code
            if request.description is not None:
                existing_product.description = request.description
            if request.sell_price is not None:
                existing_product.sell_price = request.sell_price
            if request.cost_price is not None:
                existing_product.cost_price = request.cost_price
            if request.department_id is not None:
                existing_product.department_id = request.department_id

            # Update via service
            updated_product = self.product_service.update_product(
                existing_product,
                user_id=request.user_id
            )

            response = ProductResponse.from_domain(updated_product)
            return UseCaseResult.success(response)

        except ValueError as e:
            return UseCaseResult.failure(str(e))

        except Exception as e:
            self.logger.error(f"Unexpected error updating product: {e}", exc_info=True)
            return UseCaseResult.failure(f"An unexpected error occurred: {str(e)}")

    def _validate_request(self, request: UpdateProductRequest) -> Optional[dict]:
        """Validate the update request."""
        errors = {}

        if not request.product_id:
            errors['product_id'] = 'Product ID is required'

        if request.code is not None and not request.code.strip():
            errors['code'] = 'Product code cannot be empty'

        if request.description is not None and not request.description.strip():
            errors['description'] = 'Description cannot be empty'

        if request.sell_price is not None and request.sell_price <= 0:
            errors['sell_price'] = 'Sell price must be greater than zero'

        return errors if errors else None


class GetProductByCodeUseCase(QueryUseCase[GetProductByCodeRequest, ProductResponse]):
    """
    Query use case for getting a product by code.

    This is a read-only operation optimized for retrieval.
    """

    def __init__(self, product_service: ProductService):
        super().__init__()
        self.product_service = product_service

    def execute(self, request: GetProductByCodeRequest) -> UseCaseResult[ProductResponse]:
        """Execute the get product by code query."""
        if not request.code:
            return UseCaseResult.validation_error({'code': 'Product code is required'})

        product = self.product_service.get_product_by_code(request.code)

        if not product:
            return UseCaseResult.not_found("Product")

        response = ProductResponse.from_domain(product)
        return UseCaseResult.success(response)


class SearchProductsUseCase(QueryUseCase[SearchProductsRequest, ProductListResponse]):
    """
    Query use case for searching products.

    Supports filtering by search term, department, and stock status.
    """

    def __init__(self, product_service: ProductService):
        super().__init__()
        self.product_service = product_service

    def execute(self, request: SearchProductsRequest) -> UseCaseResult[ProductListResponse]:
        """Execute the search products query."""
        try:
            # Get products based on filters
            products = self.product_service.get_all_products(
                department_id=request.department_id
            )

            # Apply search term filter
            if request.search_term:
                search_lower = request.search_term.lower()
                products = [
                    p for p in products
                    if search_lower in p.code.lower()
                    or search_lower in p.description.lower()
                ]

            # Apply stock filter
            if request.in_stock_only:
                products = [
                    p for p in products
                    if p.quantity_in_stock > 0
                ]

            # Convert to response DTOs
            product_responses = [
                ProductResponse.from_domain(p) for p in products
            ]

            response = ProductListResponse(
                products=product_responses,
                total_count=len(product_responses)
            )

            return UseCaseResult.success(response)

        except Exception as e:
            self.logger.error(f"Error searching products: {e}", exc_info=True)
            return UseCaseResult.failure(f"Search failed: {str(e)}")


class BulkUpdateProductPricesUseCase(UseCase[BulkPriceUpdateRequest, BulkPriceUpdateResponse]):
    """
    Use case for bulk updating product prices.

    Updates prices by percentage and publishes events for each change.
    """

    def __init__(self, product_service: ProductService):
        super().__init__()
        self.product_service = product_service

    @log_use_case_execution
    def execute(self, request: BulkPriceUpdateRequest) -> UseCaseResult[BulkPriceUpdateResponse]:
        """Execute the bulk price update."""
        # Validation
        validation_errors = self._validate_request(request)
        if validation_errors:
            return UseCaseResult.validation_error(validation_errors)

        try:
            # Execute bulk update via service
            updated_count = self.product_service.update_prices_by_percentage(
                percentage=request.percentage,
                department_id=request.department_id,
                user_id=request.user_id
            )

            response = BulkPriceUpdateResponse(
                updated_count=updated_count,
                failed_products=[]
            )

            return UseCaseResult.success(response)

        except ValueError as e:
            return UseCaseResult.failure(str(e))

        except Exception as e:
            self.logger.error(f"Error in bulk price update: {e}", exc_info=True)
            return UseCaseResult.failure(f"Bulk update failed: {str(e)}")

    def _validate_request(self, request: BulkPriceUpdateRequest) -> Optional[dict]:
        """Validate the bulk update request."""
        errors = {}

        if request.percentage is None:
            errors['percentage'] = 'Percentage is required'
        elif request.percentage <= Decimal('-100'):
            errors['percentage'] = 'Percentage must be greater than -100'

        return errors if errors else None
