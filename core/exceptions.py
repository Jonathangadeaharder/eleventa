"""
Core exceptions module for eleventa.

This module defines all application-specific exceptions used across
the application for consistent error handling.
"""


class ApplicationError(Exception):
    """Base class for all application-specific exceptions."""

    def __init__(self, message="An application error occurred"):
        self.message = message
        super().__init__(self.message)


class ValidationError(ApplicationError):
    """
    Exception raised when validation fails.

    Typically used when creating or updating resources with invalid data.
    """

    def __init__(self, message="Validation error"):
        super().__init__(message)


class ResourceNotFoundError(ApplicationError):
    """
    Exception raised when a requested resource is not found.

    Used when attempting to retrieve, update, or delete a non-existent resource.
    """

    def __init__(self, message="Resource not found"):
        super().__init__(message)


class DatabaseError(ApplicationError):
    """
    Exception raised when database operations fail.

    Used for persistence layer errors like connection issues or constraint violations.
    """

    def __init__(self, message="Database operation failed", original_exception=None):
        self.original_exception = original_exception
        super().__init__(message)


class AuthenticationError(ApplicationError):
    """
    Exception raised when authentication fails.

    Used for invalid credentials or unauthorized access attempts.
    """

    def __init__(self, message="Authentication failed"):
        super().__init__(message)


class BusinessRuleError(ApplicationError):
    """
    Exception raised when a business rule is violated.

    Used for domain-specific rule violations that are not validation errors.
    """

    def __init__(self, message="Business rule violation"):
        super().__init__(message)


class ExternalServiceError(ApplicationError):
    """
    Exception raised when an external service call fails.

    Used for integration errors with external APIs or services.
    """

    def __init__(self, message="External service error", service_name=None):
        self.service_name = service_name
        message_with_service = (
            f"{message} (Service: {service_name})" if service_name else message
        )
        super().__init__(message_with_service)


class SaleCreationError(ValidationError):
    """
    Exception raised when sale creation fails due to invalid data.

    Used specifically for errors during sale creation process.
    """

    def __init__(self, message="Failed to create sale"):
        super().__init__(message)


class SaleNotFoundError(ResourceNotFoundError):
    """
    Exception raised when a requested sale is not found.

    Used specifically for sale-related resource not found errors.
    """

    def __init__(self, sale_id=None):
        message = (
            f"Sale with ID {sale_id} not found"
            if sale_id is not None
            else "Sale not found"
        )
        super().__init__(message)
