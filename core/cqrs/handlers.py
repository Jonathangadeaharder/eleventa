"""
Command and Query Handlers

Handlers process commands and queries:
- CommandHandlers modify state and publish events
- QueryHandlers fetch data from read models

This module provides base classes and example implementations.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional
import logging

from core.cqrs.commands import Command
from core.cqrs.queries import Query
from core.use_cases.base import UseCaseResult


TCommand = TypeVar("TCommand", bound=Command)
TQuery = TypeVar("TQuery", bound=Query)
TResult = TypeVar("TResult")


class CommandHandler(ABC, Generic[TCommand, TResult]):
    """
    Base class for command handlers.

    Command handlers:
    - Validate the command
    - Execute business logic via services
    - Publish domain events
    - Return success/failure result

    Usage:
        class CreateProductCommandHandler(CommandHandler[CreateProductCommand, UUID]):
            def __init__(self, product_service):
                self.product_service = product_service

            def handle(self, command: CreateProductCommand) -> UseCaseResult[UUID]:
                # Validate
                if not command.code:
                    return UseCaseResult.validation_error({'code': 'Required'})

                # Execute
                try:
                    product = self.product_service.add_product(...)
                    return UseCaseResult.success(product.id)
                except ValueError as e:
                    return UseCaseResult.failure(str(e))
    """

    def __init__(self):
        """Initialize the command handler."""
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def handle(self, command: TCommand) -> UseCaseResult[TResult]:
        """
        Handle the command.

        Args:
            command: The command to handle

        Returns:
            UseCaseResult containing the result or error
        """
        pass

    def _log_command(self, command: TCommand) -> None:
        """Log command execution."""
        self.logger.info(f"Handling {type(command).__name__}")

    def _log_success(self, result: TResult) -> None:
        """Log successful command execution."""
        self.logger.debug("Command completed successfully")

    def _log_failure(self, error: str) -> None:
        """Log failed command execution."""
        self.logger.warning(f"Command failed: {error}")


class QueryHandler(ABC, Generic[TQuery, TResult]):
    """
    Base class for query handlers.

    Query handlers:
    - Fetch data from read models
    - Never modify state
    - Return data or None (never fail)
    - Can be cached

    Usage:
        class GetProductByIdQueryHandler(QueryHandler[GetProductByIdQuery, ProductReadModel]):
            def __init__(self, query_repository):
                self.query_repository = query_repository

            def handle(self, query: GetProductByIdQuery) -> Optional[ProductReadModel]:
                return self.query_repository.get_product_by_id(query.product_id)
    """

    def __init__(self):
        """Initialize the query handler."""
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def handle(self, query: TQuery) -> Optional[TResult]:
        """
        Handle the query.

        Args:
            query: The query to handle

        Returns:
            Query result or None if not found
        """
        pass

    def _log_query(self, query: TQuery) -> None:
        """Log query execution."""
        self.logger.debug(f"Handling {type(query).__name__}")


# Example Command Handlers (Concrete Implementations)

from uuid import UUID
from core.cqrs.commands import CreateProductCommand, UpdateProductCommand
from core.cqrs.read_models import ProductReadModel
from core.services.product_service import ProductService
from core.models.product import Product
from decimal import Decimal


class CreateProductCommandHandler(CommandHandler[CreateProductCommand, UUID]):
    """
    Handler for CreateProductCommand.

    Creates a new product and returns its ID.
    """

    def __init__(self, product_service: ProductService):
        super().__init__()
        self.product_service = product_service

    def handle(self, command: CreateProductCommand) -> UseCaseResult[UUID]:
        """Handle the create product command."""
        self._log_command(command)

        # Validation
        errors = self._validate_command(command)
        if errors:
            return UseCaseResult.validation_error(errors)

        # Execute
        try:
            # Convert command to domain model
            product = Product(
                code=command.code,
                description=command.description,
                sell_price=command.sell_price,
                cost_price=command.cost_price,
                department_id=command.department_id,
                uses_inventory=command.uses_inventory,
                quantity_in_stock=command.quantity_in_stock,
                min_stock=command.min_stock,
                max_stock=command.max_stock,
                unit_id=command.unit_id,
            )

            created_product = self.product_service.add_product(
                product, user_id=command.user_id
            )

            self._log_success(created_product.id)
            return UseCaseResult.success(created_product.id)

        except ValueError as e:
            self._log_failure(str(e))
            if "already exists" in str(e).lower():
                return UseCaseResult.conflict(str(e))
            return UseCaseResult.failure(str(e))

        except Exception as e:
            self._log_failure(str(e))
            return UseCaseResult.failure(f"Unexpected error: {str(e)}")

    def _validate_command(self, command: CreateProductCommand) -> Optional[dict]:
        """Validate the create product command."""
        errors = {}

        if not command.code or not command.code.strip():
            errors["code"] = "Product code is required"

        if not command.description or not command.description.strip():
            errors["description"] = "Description is required"

        if command.sell_price <= 0:
            errors["sell_price"] = "Sell price must be greater than zero"

        if command.cost_price is not None and command.cost_price < 0:
            errors["cost_price"] = "Cost price cannot be negative"

        return errors if errors else None


class UpdateProductCommandHandler(CommandHandler[UpdateProductCommand, UUID]):
    """
    Handler for UpdateProductCommand.

    Updates an existing product and returns its ID.
    """

    def __init__(self, product_service: ProductService):
        super().__init__()
        self.product_service = product_service

    def handle(self, command: UpdateProductCommand) -> UseCaseResult[UUID]:
        """Handle the update product command."""
        self._log_command(command)

        # Validation
        errors = self._validate_command(command)
        if errors:
            return UseCaseResult.validation_error(errors)

        try:
            # Get existing product
            existing_product = self.product_service.get_product_by_id(
                command.product_id
            )
            if not existing_product:
                return UseCaseResult.not_found("Product")

            # Apply updates
            if command.code is not None:
                existing_product.code = command.code
            if command.description is not None:
                existing_product.description = command.description
            if command.sell_price is not None:
                existing_product.sell_price = command.sell_price
            if command.cost_price is not None:
                existing_product.cost_price = command.cost_price
            if command.department_id is not None:
                existing_product.department_id = command.department_id
            if command.uses_inventory is not None:
                existing_product.uses_inventory = command.uses_inventory
            if command.quantity_in_stock is not None:
                existing_product.quantity_in_stock = command.quantity_in_stock

            # Update via service
            updated_product = self.product_service.update_product(
                existing_product, user_id=command.user_id
            )

            self._log_success(updated_product.id)
            return UseCaseResult.success(updated_product.id)

        except ValueError as e:
            self._log_failure(str(e))
            return UseCaseResult.failure(str(e))

        except Exception as e:
            self._log_failure(str(e))
            return UseCaseResult.failure(f"Unexpected error: {str(e)}")

    def _validate_command(self, command: UpdateProductCommand) -> Optional[dict]:
        """Validate the update product command."""
        errors = {}

        if command.code is not None and not command.code.strip():
            errors["code"] = "Product code cannot be empty"

        if command.description is not None and not command.description.strip():
            errors["description"] = "Description cannot be empty"

        if command.sell_price is not None and command.sell_price <= 0:
            errors["sell_price"] = "Sell price must be greater than zero"

        return errors if errors else None


# Example Query Handlers (Concrete Implementations)

from typing import List
from core.cqrs.queries import (
    GetProductByIdQuery,
    GetProductByCodeQuery,
    SearchProductsQuery,
)
from core.cqrs.read_models import ProductListItemReadModel


class GetProductByIdQueryHandler(QueryHandler[GetProductByIdQuery, ProductReadModel]):
    """
    Handler for GetProductByIdQuery.

    Fetches a product by ID from the read model.
    """

    def __init__(self, product_service: ProductService):
        super().__init__()
        self.product_service = product_service

    def handle(self, query: GetProductByIdQuery) -> Optional[ProductReadModel]:
        """Handle the get product by ID query."""
        self._log_query(query)

        product = self.product_service.get_product_by_id(query.product_id)

        if not product:
            return None

        # Convert domain model to read model
        return self._to_read_model(product)

    def _to_read_model(self, product) -> ProductReadModel:
        """Convert domain product to read model."""
        # In a real implementation, this would fetch denormalized data
        # from a read-optimized view
        return ProductReadModel(
            id=product.id,
            code=product.code,
            description=product.description,
            sell_price=product.sell_price,
            cost_price=product.cost_price,
            quantity_in_stock=product.quantity_in_stock,
            min_stock=product.min_stock,
            max_stock=product.max_stock,
            uses_inventory=product.uses_inventory,
            department_id=product.department_id,
            department_name=None,  # Would be denormalized in real impl
            unit_id=product.unit_id,
            unit_name=None,  # Would be denormalized in real impl
            in_stock=product.quantity_in_stock > 0,
            is_low_stock=(
                product.min_stock is not None
                and product.quantity_in_stock < product.min_stock
            ),
            stock_value=(
                product.quantity_in_stock * (product.cost_price or Decimal("0"))
            ),
        )


class GetProductByCodeQueryHandler(
    QueryHandler[GetProductByCodeQuery, ProductReadModel]
):
    """Handler for GetProductByCodeQuery."""

    def __init__(self, product_service: ProductService):
        super().__init__()
        self.product_service = product_service

    def handle(self, query: GetProductByCodeQuery) -> Optional[ProductReadModel]:
        """Handle the get product by code query."""
        self._log_query(query)

        product = self.product_service.get_product_by_code(query.code)

        if not product:
            return None

        # Reuse the conversion logic
        handler = GetProductByIdQueryHandler(self.product_service)
        return handler._to_read_model(product)


class SearchProductsQueryHandler(
    QueryHandler[SearchProductsQuery, List[ProductListItemReadModel]]
):
    """
    Handler for SearchProductsQuery.

    Returns a list of products matching the search criteria.
    """

    def __init__(self, product_service: ProductService):
        super().__init__()
        self.product_service = product_service

    def handle(self, query: SearchProductsQuery) -> List[ProductListItemReadModel]:
        """Handle the search products query."""
        self._log_query(query)

        # Get products
        products = self.product_service.get_all_products(
            department_id=query.department_id
        )

        # Apply filters
        if query.search_term:
            search_lower = query.search_term.lower()
            products = [
                p
                for p in products
                if search_lower in p.code.lower()
                or search_lower in p.description.lower()
            ]

        if query.in_stock_only:
            products = [p for p in products if p.quantity_in_stock > 0]

        if query.min_price is not None:
            products = [p for p in products if p.sell_price >= query.min_price]

        if query.max_price is not None:
            products = [p for p in products if p.sell_price <= query.max_price]

        # Convert to read models
        read_models = [self._to_list_item(p) for p in products]

        # Apply pagination
        start = query.offset
        end = start + query.limit
        return read_models[start:end]

    def _to_list_item(self, product) -> ProductListItemReadModel:
        """Convert domain product to list item read model."""
        return ProductListItemReadModel(
            id=product.id,
            code=product.code,
            description=product.description,
            sell_price=product.sell_price,
            quantity_in_stock=product.quantity_in_stock,
            department_name=None,  # Would be denormalized
            in_stock=product.quantity_in_stock > 0,
            is_low_stock=(
                product.min_stock is not None
                and product.quantity_in_stock < product.min_stock
            ),
        )
