"""
Use Cases / Application Layer

This package contains all use cases (application services) for the Eleventa POS system.
Use cases represent explicit business operations and orchestrate domain services.

Architecture:
    Presentation Layer (UI)
         ↓
    Application Layer (Use Cases) ← You are here
         ↓
    Domain Layer (Services, Models, Events)
         ↓
    Infrastructure Layer (Repositories, Database)

Benefits of Use Cases:
- Clear API for each business operation
- Decouple UI from domain logic
- Easy to test in isolation
- Self-documenting business capabilities
- Centralized validation and error handling

Usage:
    from core.use_cases import CreateProductUseCase, ProcessSaleUseCase
    from core.use_cases.dtos import CreateProductRequest

    # Initialize use case with dependencies
    use_case = CreateProductUseCase(product_service)

    # Execute
    request = CreateProductRequest(code="TEST", description="Test Product", ...)
    result = use_case.execute(request)

    # Handle result
    if result.is_success:
        product = result.data
        # Success path
    else:
        # Error handling
        print(f"Error: {result.error}")
        if result.errors:
            # Validation errors
            for field, error in result.errors.items():
                print(f"{field}: {error}")
"""

# Base classes
from core.use_cases.base import (
    UseCase,
    QueryUseCase,
    CommandUseCase,
    UseCaseResult,
    UseCaseStatus,
    log_use_case_execution,
    validate_request,
)

# DTOs
from core.use_cases.dtos import (
    # Product DTOs
    CreateProductRequest,
    UpdateProductRequest,
    ProductResponse,
    GetProductByCodeRequest,
    SearchProductsRequest,
    ProductListResponse,
    BulkPriceUpdateRequest,
    BulkPriceUpdateResponse,
    # Sale DTOs
    SaleItemRequest,
    ProcessSaleRequest,
    SaleResponse,
    # Customer DTOs
    CreateCustomerRequest,
    CustomerResponse,
    # Inventory DTOs
    AdjustInventoryRequest,
    InventoryResponse,
)

# Product Use Cases
from core.use_cases.product_use_cases import (
    CreateProductUseCase,
    UpdateProductUseCase,
    GetProductByCodeUseCase,
    SearchProductsUseCase,
    BulkUpdateProductPricesUseCase,
)

# Sale Use Cases
from core.use_cases.sale_use_cases import (
    ProcessSaleUseCase,
)

__all__ = [
    # Base
    'UseCase',
    'QueryUseCase',
    'CommandUseCase',
    'UseCaseResult',
    'UseCaseStatus',
    'log_use_case_execution',
    'validate_request',
    # DTOs
    'CreateProductRequest',
    'UpdateProductRequest',
    'ProductResponse',
    'GetProductByCodeRequest',
    'SearchProductsRequest',
    'ProductListResponse',
    'BulkPriceUpdateRequest',
    'BulkPriceUpdateResponse',
    'SaleItemRequest',
    'ProcessSaleRequest',
    'SaleResponse',
    'CreateCustomerRequest',
    'CustomerResponse',
    'AdjustInventoryRequest',
    'InventoryResponse',
    # Product Use Cases
    'CreateProductUseCase',
    'UpdateProductUseCase',
    'GetProductByCodeUseCase',
    'SearchProductsUseCase',
    'BulkUpdateProductPricesUseCase',
    # Sale Use Cases
    'ProcessSaleUseCase',
]
