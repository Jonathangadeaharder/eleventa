# Use Cases / Application Layer Guide

## Table of Contents

1. [Overview](#overview)
2. [What Are Use Cases?](#what-are-use-cases)
3. [Architecture](#architecture)
4. [Benefits](#benefits)
5. [Usage Examples](#usage-examples)
6. [Creating Custom Use Cases](#creating-custom-use-cases)
7. [Testing](#testing)
8. [Best Practices](#best-practices)

---

## Overview

The Use Case layer (also called Application Layer) represents the **business operations** your system can perform. Each use case is a single, well-defined operation with clear inputs and outputs.

This is **Phase 2** of the architectural improvements, building on the Domain Events infrastructure from Phase 1.

### What Was Added

- **Base Use Case Classes**: `UseCase`, `QueryUseCase`, `CommandUseCase`
- **Result Pattern**: `UseCaseResult` for consistent error handling
- **DTOs (Data Transfer Objects)**: Request/Response objects that decouple UI from domain
- **Concrete Use Cases**: Product, Sale, and Customer operations
- **Validation**: Centralized request validation

---

## What Are Use Cases?

A use case represents **one thing the system does**. Each use case:

1. **Receives a Request** - A DTO containing all necessary data
2. **Validates the Request** - Checks business rules and constraints
3. **Orchestrates Services** - Coordinates multiple domain services
4. **Returns a Result** - Success with data, or failure with error

### Example

```python
# Traditional approach (UI directly calls service)
def on_create_product_clicked(self):
    try:
        product = Product(code=self.code_input.text(), ...)
        self.product_service.add_product(product)
        self.show_success("Product created")
    except ValueError as e:
        self.show_error(str(e))

# Use Case approach (cleaner, testable, reusable)
def on_create_product_clicked(self):
    request = CreateProductRequest(
        code=self.code_input.text(),
        description=self.desc_input.text(),
        sell_price=Decimal(self.price_input.text())
    )

    result = self.create_product_use_case.execute(request)

    if result.is_success:
        self.show_success(f"Product created: {result.data.code}")
    else:
        self.show_error(result.error)
```

---

## Architecture

### Layer Diagram

```
┌─────────────────────────────────────────┐
│   Presentation Layer (UI)               │
│   - Dialogs, Views, Widgets             │
│   - Handles user input/output           │
└────────────────┬────────────────────────┘
                 │ DTOs (Request/Response)
                 ↓
┌─────────────────────────────────────────┐
│   Application Layer (Use Cases) ← HERE  │
│   - CreateProductUseCase                │
│   - ProcessSaleUseCase                  │
│   - Orchestrates services               │
│   - Validates requests                  │
│   - Publishes events                    │
└────────────────┬────────────────────────┘
                 │ Domain Models
                 ↓
┌─────────────────────────────────────────┐
│   Domain Layer (Services & Events)      │
│   - ProductService, SaleService         │
│   - Domain Events                       │
│   - Business Rules                      │
└────────────────┬────────────────────────┘
                 │ Repositories
                 ↓
┌─────────────────────────────────────────┐
│   Infrastructure Layer                  │
│   - Repositories, Database              │
│   - Unit of Work                        │
└─────────────────────────────────────────┘
```

### File Structure

```
core/
└── use_cases/
    ├── __init__.py                  # Exports
    ├── base.py                      # Base classes
    ├── dtos.py                      # Request/Response DTOs
    ├── product_use_cases.py         # Product operations
    ├── sale_use_cases.py            # Sale operations
    └── customer_use_cases.py        # Customer operations
```

---

## Benefits

### 1. **Decoupling**

UI doesn't know about services or repositories:

```python
# Bad: UI knows about services, repositories, UoW
class ProductDialog:
    def save(self):
        with unit_of_work() as uow:
            product = Product(...)
            uow.products.add(product)
            # What if we need to update inventory?
            # What about events?
            # Validation?

# Good: UI only knows about use cases
class ProductDialog:
    def save(self):
        request = CreateProductRequest(...)
        result = self.use_case.execute(request)
        # All complexity hidden
```

### 2. **Testability**

Use cases can be tested without UI or database:

```python
def test_create_product_use_case():
    # Mock services
    mock_service = Mock(spec=ProductService)
    use_case = CreateProductUseCase(mock_service)

    # Execute
    request = CreateProductRequest(code="TEST", ...)
    result = use_case.execute(request)

    # Verify
    assert result.is_success
    mock_service.add_product.assert_called_once()
```

### 3. **Reusability**

Same use case from different UIs (Desktop, Web, API, CLI):

```python
# Desktop app
result = create_product_use_case.execute(request)

# Web API
@app.post("/products")
def create_product(request: CreateProductRequest):
    result = create_product_use_case.execute(request)
    if result.is_success:
        return {"product": result.data}
    raise HTTPException(400, result.error)

# CLI
def create_product_command(code, description, price):
    request = CreateProductRequest(code=code, ...)
    result = create_product_use_case.execute(request)
    print(f"Created: {result.data.code}" if result.is_success else result.error)
```

### 4. **Self-Documenting**

Use cases document what the system can do:

```python
# List of use cases = List of features
CreateProductUseCase          # "System can create products"
UpdateProductUseCase          # "System can update products"
ProcessSaleUseCase            # "System can process sales"
BulkUpdateProductPricesUseCase  # "System can bulk update prices"
```

### 5. **Validation Centralization**

One place for validation rules:

```python
class CreateProductUseCase:
    def _validate_request(self, request):
        errors = {}
        if not request.code:
            errors['code'] = 'Required'
        if request.sell_price <= 0:
            errors['sell_price'] = 'Must be positive'
        return errors if errors else None
```

---

## Usage Examples

### Example 1: Creating a Product

```python
from core.use_cases import CreateProductUseCase, CreateProductRequest
from core.services.product_service import ProductService
from decimal import Decimal

# Initialize use case
product_service = ProductService()
use_case = CreateProductUseCase(product_service)

# Create request
request = CreateProductRequest(
    code="LAPTOP001",
    description="Dell Laptop 15 inch",
    sell_price=Decimal('999.99'),
    cost_price=Decimal('750.00'),
    department_id=electronics_dept_id,
    user_id=current_user_id
)

# Execute
result = use_case.execute(request)

# Handle result
if result.is_success:
    product = result.data
    print(f"✓ Product created: {product.code}")
    print(f"  ID: {product.id}")
    print(f"  Price: ${product.sell_price}")
else:
    print(f"✗ Error: {result.error}")

    # Handle validation errors
    if result.status == UseCaseStatus.VALIDATION_ERROR:
        for field, error in result.errors.items():
            print(f"  {field}: {error}")

    # Handle conflicts (duplicate code)
    elif result.status == UseCaseStatus.CONFLICT:
        print("  Product code already exists")
```

### Example 2: Processing a Sale (Complex Workflow)

```python
from core.use_cases import ProcessSaleUseCase, ProcessSaleRequest, SaleItemRequest
from decimal import Decimal

# Initialize use case with dependencies
use_case = ProcessSaleUseCase(
    sale_service=sale_service,
    product_service=product_service,
    customer_service=customer_service,
    inventory_service=inventory_service
)

# Create request with multiple items
request = ProcessSaleRequest(
    items=[
        SaleItemRequest(product_code="LAPTOP001", quantity=Decimal('1')),
        SaleItemRequest(product_code="MOUSE001", quantity=Decimal('2')),
        SaleItemRequest(product_code="CABLE001", quantity=Decimal('3'))
    ],
    customer_id=customer_id,  # Optional
    payment_type="cash",
    paid_amount=Decimal('1500.00'),
    user_id=current_user_id
)

# Execute - orchestrates entire workflow
result = use_case.execute(request)

if result.is_success:
    sale = result.data
    print(f"✓ Sale completed!")
    print(f"  Sale ID: {sale.sale_id}")
    print(f"  Total: ${sale.total_amount}")
    print(f"  Paid: ${sale.paid_amount}")
    print(f"  Change: ${sale.change_amount}")

    # Events automatically published:
    # - SaleStarted
    # - SaleItemAdded (x3)
    # - SaleCompleted
    #
    # Event handlers automatically execute:
    # - Generate receipt
    # - Update inventory
    # - Award loyalty points
    # - Update analytics
else:
    print(f"✗ Sale failed: {result.error}")

    # Specific error handling
    if "Insufficient stock" in result.error:
        print("  Please check inventory")
    elif "Insufficient credit" in result.error:
        print("  Customer needs to make a payment")
```

### Example 3: Searching Products (Query Use Case)

```python
from core.use_cases import SearchProductsUseCase, SearchProductsRequest

use_case = SearchProductsUseCase(product_service)

request = SearchProductsRequest(
    search_term="laptop",
    department_id=electronics_dept_id,
    in_stock_only=True
)

result = use_case.execute(request)

if result.is_success:
    products = result.data.products
    print(f"Found {result.data.total_count} products:")
    for product in products:
        print(f"  {product.code}: {product.description} - ${product.sell_price}")
```

### Example 4: Bulk Price Update

```python
from core.use_cases import BulkUpdateProductPricesUseCase, BulkPriceUpdateRequest
from decimal import Decimal

use_case = BulkUpdateProductPricesUseCase(product_service)

request = BulkPriceUpdateRequest(
    percentage=Decimal('10'),  # 10% increase
    department_id=electronics_dept_id,  # Only electronics
    user_id=current_user_id
)

result = use_case.execute(request)

if result.is_success:
    print(f"✓ Updated {result.data.updated_count} products")
    # ProductPriceChanged event published for each product!
```

---

## Creating Custom Use Cases

### Step 1: Define DTOs

```python
# In core/use_cases/dtos.py

@dataclass
class PerformInventoryCountRequest:
    """Request to perform physical inventory count."""
    department_id: Optional[UUID] = None
    user_id: Optional[UUID] = None

@dataclass
class InventoryCountResponse:
    """Response with inventory count results."""
    counted_products: int
    discrepancies: List[dict]
    total_variance: Decimal
```

### Step 2: Create Use Case

```python
# In core/use_cases/inventory_use_cases.py

from core.use_cases.base import UseCase, UseCaseResult
from core.use_cases.dtos import PerformInventoryCountRequest, InventoryCountResponse

class PerformInventoryCountUseCase(UseCase[PerformInventoryCountRequest, InventoryCountResponse]):
    """
    Use case for performing physical inventory count.

    Orchestrates:
    1. Fetch all products in department
    2. Compare system vs physical counts
    3. Generate discrepancy report
    4. Optionally adjust inventory
    5. Publish InventoryCounted event
    """

    def __init__(self, product_service, inventory_service):
        super().__init__()
        self.product_service = product_service
        self.inventory_service = inventory_service

    def execute(self, request: PerformInventoryCountRequest) -> UseCaseResult[InventoryCountResponse]:
        """Execute the inventory count."""
        # Validation
        # ...

        # Business logic
        try:
            products = self.product_service.get_all_products(
                department_id=request.department_id
            )

            # Perform count logic
            discrepancies = []
            for product in products:
                # Compare system vs physical
                # Record discrepancies
                pass

            response = InventoryCountResponse(
                counted_products=len(products),
                discrepancies=discrepancies,
                total_variance=calculate_variance(discrepancies)
            )

            return UseCaseResult.success(response)

        except Exception as e:
            return UseCaseResult.failure(str(e))
```

### Step 3: Register in __init__.py

```python
# In core/use_cases/__init__.py

from core.use_cases.inventory_use_cases import PerformInventoryCountUseCase

__all__ = [
    # ... existing exports
    'PerformInventoryCountUseCase',
]
```

### Step 4: Use in UI

```python
class InventoryCountDialog:
    def __init__(self, use_case: PerformInventoryCountUseCase):
        self.use_case = use_case

    def perform_count(self):
        request = PerformInventoryCountRequest(
            department_id=self.selected_department_id,
            user_id=self.current_user_id
        )

        result = self.use_case.execute(request)

        if result.is_success:
            self.display_results(result.data)
        else:
            self.show_error(result.error)
```

---

## Testing

### Unit Testing Use Cases

```python
import pytest
from unittest.mock import Mock
from decimal import Decimal

from core.use_cases import CreateProductUseCase, CreateProductRequest
from core.services.product_service import ProductService
from core.models.product import Product

def test_create_product_success():
    """Test successful product creation."""
    # Arrange
    mock_service = Mock(spec=ProductService)
    expected_product = Product(
        id=UUID('12345678-1234-5678-1234-567812345678'),
        code="TEST001",
        description="Test Product",
        sell_price=Decimal('99.99')
    )
    mock_service.add_product.return_value = expected_product

    use_case = CreateProductUseCase(mock_service)
    request = CreateProductRequest(
        code="TEST001",
        description="Test Product",
        sell_price=Decimal('99.99')
    )

    # Act
    result = use_case.execute(request)

    # Assert
    assert result.is_success
    assert result.data.code == "TEST001"
    assert result.data.sell_price == Decimal('99.99')
    mock_service.add_product.assert_called_once()

def test_create_product_validation_error():
    """Test validation errors."""
    use_case = CreateProductUseCase(Mock())

    # Missing required fields
    request = CreateProductRequest(
        code="",  # Empty code
        description="Test",
        sell_price=Decimal('-10')  # Negative price
    )

    result = use_case.execute(request)

    assert result.is_failure
    assert result.status == UseCaseStatus.VALIDATION_ERROR
    assert 'code' in result.errors
    assert 'sell_price' in result.errors

def test_create_product_conflict():
    """Test duplicate product code."""
    mock_service = Mock(spec=ProductService)
    mock_service.add_product.side_effect = ValueError("Code already exists")

    use_case = CreateProductUseCase(mock_service)
    request = CreateProductRequest(
        code="EXISTING",
        description="Test",
        sell_price=Decimal('99.99')
    )

    result = use_case.execute(request)

    assert result.is_failure
    assert result.status == UseCaseStatus.CONFLICT
```

### Integration Testing

```python
@pytest.mark.integration
def test_process_sale_integration(clean_db, product_service, sale_service):
    """Test complete sale processing with real services."""
    # Setup - create test products
    product1 = create_test_product("PROD001", Decimal('100'))
    product2 = create_test_product("PROD002", Decimal('50'))

    # Create use case with real services
    use_case = ProcessSaleUseCase(
        sale_service=sale_service,
        product_service=product_service
    )

    # Execute sale
    request = ProcessSaleRequest(
        items=[
            SaleItemRequest(product_code="PROD001", quantity=Decimal('2')),
            SaleItemRequest(product_code="PROD002", quantity=Decimal('1'))
        ],
        payment_type="cash",
        paid_amount=Decimal('300')
    )

    result = use_case.execute(request)

    # Verify
    assert result.is_success
    assert result.data.total_amount == Decimal('250')  # 200 + 50
    assert result.data.change_amount == Decimal('50')  # 300 - 250
```

---

## Best Practices

### 1. **One Use Case = One Operation**

```python
# Good
class CreateProductUseCase: ...
class UpdateProductUseCase: ...
class DeleteProductUseCase: ...

# Bad
class ProductUseCase:
    def create(...): ...
    def update(...): ...
    def delete(...): ...
```

### 2. **Use DTOs, Not Domain Models**

```python
# Good - DTOs decouple UI from domain
def execute(self, request: CreateProductRequest) -> UseCaseResult[ProductResponse]:
    domain_product = request.to_domain()
    # ...
    return UseCaseResult.success(ProductResponse.from_domain(product))

# Bad - UI knows about domain models
def execute(self, product: Product) -> Product:
    # Tight coupling
```

### 3. **Validate in Use Cases, Not Services**

```python
# Use Case validates
class CreateProductUseCase:
    def execute(self, request):
        errors = self._validate_request(request)
        if errors:
            return UseCaseResult.validation_error(errors)
        # ...

# Service focuses on business logic
class ProductService:
    def add_product(self, product):
        # Assumes valid input
        # Focuses on domain rules
```

### 4. **Return Results, Don't Raise Exceptions**

```python
# Good
result = use_case.execute(request)
if result.is_failure:
    handle_error(result.error)

# Bad
try:
    use_case.execute(request)
except ValidationError as e:
    # Forces error handling via exceptions
```

### 5. **Keep Use Cases Stateless**

```python
# Good - stateless
class CreateProductUseCase:
    def __init__(self, product_service):
        self.product_service = product_service

    def execute(self, request):
        # Uses injected service, not instance state

# Bad - stateful
class CreateProductUseCase:
    def set_product_data(self, data):
        self.data = data

    def execute(self):
        # Uses instance state - not thread-safe
```

---

## Migration Guide

### Before (UI directly calls services)

```python
class ProductDialog(QDialog):
    def __init__(self, product_service):
        self.product_service = product_service

    def on_save_clicked(self):
        try:
            product = Product(
                code=self.code_input.text(),
                description=self.desc_input.text(),
                sell_price=Decimal(self.price_input.text())
            )
            self.product_service.add_product(product)
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
```

### After (UI uses use cases)

```python
class ProductDialog(QDialog):
    def __init__(self, create_product_use_case):
        self.use_case = create_product_use_case

    def on_save_clicked(self):
        request = CreateProductRequest(
            code=self.code_input.text(),
            description=self.desc_input.text(),
            sell_price=Decimal(self.price_input.text())
        )

        result = self.use_case.execute(request)

        if result.is_success:
            self.accept()
        elif result.status == UseCaseStatus.VALIDATION_ERROR:
            self.show_validation_errors(result.errors)
        else:
            QMessageBox.warning(self, "Error", result.error)
```

---

## Summary

The Use Case layer provides:

✅ **Clear separation** between UI and business logic
✅ **Consistent error handling** via Result pattern
✅ **Easy testing** - mock dependencies, test in isolation
✅ **Reusable operations** - same use case from different UIs
✅ **Self-documenting** - list of use cases = list of features
✅ **Centralized validation** - one place for rules
✅ **Event-driven** - integrates with domain events

Next steps:
- Phase 3: CQRS (separate read/write models)
- Phase 4: Specification Pattern (composable queries)
- Phase 5: Async event processing

See `docs/ARCHITECTURE_IMPROVEMENTS.md` for the complete roadmap.
