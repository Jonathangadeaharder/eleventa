"""
Base classes for the Use Case / Application Layer

This module implements the Application Layer pattern, which sits between
the UI (Presentation layer) and the Domain/Service layer. Use cases represent
explicit business operations that the system can perform.

Based on Clean Architecture and Hexagonal Architecture patterns.

Benefits:
- Clear entry points for each business operation
- Decouple UI from domain services
- Easy to add cross-cutting concerns (logging, metrics, auth)
- Testable in isolation
- Self-documenting API

References:
- Clean Architecture by Robert C. Martin
- Architecture Patterns with Python (Cosmic Python)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar, Optional, Any
from enum import Enum
import logging


# Type variables for request and response
TRequest = TypeVar("TRequest")
TResponse = TypeVar("TResponse")


class UseCaseStatus(Enum):
    """Status of use case execution."""

    SUCCESS = "success"
    FAILURE = "failure"
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    UNAUTHORIZED = "unauthorized"
    CONFLICT = "conflict"


@dataclass
class UseCaseResult(Generic[TResponse]):
    """
    Result of a use case execution.

    Provides a consistent way to return results, errors, and status
    from use cases to the presentation layer.

    Usage:
        # Success
        return UseCaseResult.success(data=product)

        # Failure
        return UseCaseResult.failure(
            error="Product not found",
            status=UseCaseStatus.NOT_FOUND
        )
    """

    status: UseCaseStatus
    data: Optional[TResponse] = None
    error: Optional[str] = None
    errors: Optional[dict] = None  # For validation errors

    @property
    def is_success(self) -> bool:
        """Check if the use case succeeded."""
        return self.status == UseCaseStatus.SUCCESS

    @property
    def is_failure(self) -> bool:
        """Check if the use case failed."""
        return not self.is_success

    @classmethod
    def success(cls, data: TResponse) -> "UseCaseResult[TResponse]":
        """Create a success result."""
        return cls(status=UseCaseStatus.SUCCESS, data=data)

    @classmethod
    def failure(
        cls,
        error: str,
        status: UseCaseStatus = UseCaseStatus.FAILURE,
        errors: Optional[dict] = None,
    ) -> "UseCaseResult":
        """Create a failure result."""
        return cls(status=status, error=error, errors=errors)

    @classmethod
    def validation_error(cls, errors: dict) -> "UseCaseResult":
        """Create a validation error result."""
        return cls(
            status=UseCaseStatus.VALIDATION_ERROR,
            error="Validation failed",
            errors=errors,
        )

    @classmethod
    def not_found(cls, resource: str) -> "UseCaseResult":
        """Create a not found result."""
        return cls(status=UseCaseStatus.NOT_FOUND, error=f"{resource} not found")

    @classmethod
    def conflict(cls, message: str) -> "UseCaseResult":
        """Create a conflict result (e.g., duplicate key)."""
        return cls(status=UseCaseStatus.CONFLICT, error=message)


class UseCase(ABC, Generic[TRequest, TResponse]):
    """
    Base class for all use cases.

    Use cases represent a single business operation that the system can perform.
    They orchestrate domain services, repositories, and publish events.

    Each use case should:
    1. Validate the request
    2. Perform business logic via services
    3. Return a structured result

    Usage:
        class CreateProductUseCase(UseCase[CreateProductRequest, Product]):
            def execute(self, request: CreateProductRequest) -> UseCaseResult[Product]:
                # Validation
                if not request.code:
                    return UseCaseResult.validation_error({'code': 'Required'})

                # Business logic
                try:
                    product = self.product_service.add_product(request.to_domain())
                    return UseCaseResult.success(product)
                except ValueError as e:
                    return UseCaseResult.failure(str(e))
    """

    def __init__(self):
        """Initialize the use case with logging."""
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def execute(self, request: TRequest) -> UseCaseResult[TResponse]:
        """
        Execute the use case.

        Args:
            request: The use case request object

        Returns:
            UseCaseResult containing either data or error
        """
        pass

    def _log_execution(self, request: TRequest) -> None:
        """Log use case execution."""
        self.logger.info(f"Executing {self.__class__.__name__} with request: {request}")

    def _log_success(self, result: Any) -> None:
        """Log successful execution."""
        self.logger.debug(f"{self.__class__.__name__} completed successfully")

    def _log_failure(self, error: str) -> None:
        """Log failed execution."""
        self.logger.warning(f"{self.__class__.__name__} failed: {error}")


class QueryUseCase(ABC, Generic[TRequest, TResponse]):
    """
    Base class for query use cases (CQRS pattern).

    Query use cases are read-only operations that don't modify state.
    They can be optimized differently from command use cases.

    Usage:
        class GetProductByCodeQuery(QueryUseCase[str, Product]):
            def execute(self, code: str) -> UseCaseResult[Product]:
                product = self.product_repository.get_by_code(code)
                if not product:
                    return UseCaseResult.not_found("Product")
                return UseCaseResult.success(product)
    """

    def __init__(self):
        """Initialize the query use case."""
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def execute(self, request: TRequest) -> UseCaseResult[TResponse]:
        """
        Execute the query.

        Args:
            request: The query request

        Returns:
            UseCaseResult containing the query result
        """
        pass


class CommandUseCase(UseCase[TRequest, TResponse]):
    """
    Base class for command use cases (CQRS pattern).

    Command use cases modify state and may publish domain events.
    They represent write operations.

    Commands should be:
    - Validated before execution
    - Transactional (all-or-nothing)
    - Event-sourced (publish events on success)
    """

    pass


# Decorator for use case middleware


def log_use_case_execution(func):
    """
    Decorator to log use case execution.

    Usage:
        class MyUseCase(UseCase):
            @log_use_case_execution
            def execute(self, request):
                # ...
    """

    def wrapper(self, request):
        self.logger.info(f"Executing {self.__class__.__name__}")
        try:
            result = func(self, request)
            if result.is_success:
                self.logger.debug(f"{self.__class__.__name__} succeeded")
            else:
                self.logger.warning(f"{self.__class__.__name__} failed: {result.error}")
            return result
        except Exception as e:
            self.logger.error(
                f"{self.__class__.__name__} raised exception: {e}", exc_info=True
            )
            raise

    return wrapper


def validate_request(validator_func):
    """
    Decorator to validate request before execution.

    Usage:
        def validate_create_product(request):
            errors = {}
            if not request.code:
                errors['code'] = 'Required'
            return errors

        class CreateProductUseCase(UseCase):
            @validate_request(validate_create_product)
            def execute(self, request):
                # Validation already done
                # ...
    """

    def decorator(func):
        def wrapper(self, request):
            errors = validator_func(request)
            if errors:
                return UseCaseResult.validation_error(errors)
            return func(self, request)

        return wrapper

    return decorator
