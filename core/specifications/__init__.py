"""
Specification Pattern

The Specification pattern encapsulates business rules and query logic
into reusable, composable objects that can be combined to create
complex queries.

Key Concepts:

1. **Specification** - Encapsulates a single business rule
   Example: ProductInStockSpecification, PriceRangeSpecification

2. **Composite Specifications** - Combine specifications
   - AndSpecification: Both specs must be satisfied
   - OrSpecification: Either spec must be satisfied
   - NotSpecification: Spec must not be satisfied

3. **Benefits**:
   - Reusable query logic
   - Composable (combine with AND, OR, NOT)
   - Testable in isolation
   - Type-safe
   - Self-documenting
   - DRY principle

Usage:
    # Define specifications
    in_stock = ProductInStockSpecification()
    in_electronics = ProductInDepartmentSpecification(electronics_dept_id)
    low_stock = ProductLowStockSpecification()

    # Compose specifications
    spec = in_stock.and_(in_electronics).and_(low_stock)

    # Use in repository
    products = repository.find_by_specification(spec)

    # Equivalent to:
    # SELECT * FROM products
    # WHERE quantity_in_stock > 0
    #   AND department_id = :dept_id
    #   AND quantity_in_stock < min_stock

References:
- Domain-Driven Design by Eric Evans
- Specifications Pattern by Martin Fowler
- Enterprise Patterns and MDA by Jim Arlow & Ila Neustadt
"""

from core.specifications.base import (
    Specification,
    CompositeSpecification,
    AndSpecification,
    OrSpecification,
    NotSpecification,
)

from core.specifications.product_specifications import (
    ProductInStockSpecification,
    ProductOutOfStockSpecification,
    ProductLowStockSpecification,
    ProductInDepartmentSpecification,
    ProductPriceRangeSpecification,
    ProductCodeLikeSpecification,
    ProductDescriptionLikeSpecification,
    ProductActiveSpecification,
)

from core.specifications.sale_specifications import (
    SaleByDateRangeSpecification,
    SaleByCustomerSpecification,
    SaleByPaymentTypeSpecification,
    SaleAboveAmountSpecification,
    SaleBelowAmountSpecification,
    SaleCreditSaleSpecification,
)

__all__ = [
    # Base
    "Specification",
    "CompositeSpecification",
    "AndSpecification",
    "OrSpecification",
    "NotSpecification",
    # Product Specifications
    "ProductInStockSpecification",
    "ProductOutOfStockSpecification",
    "ProductLowStockSpecification",
    "ProductInDepartmentSpecification",
    "ProductPriceRangeSpecification",
    "ProductCodeLikeSpecification",
    "ProductDescriptionLikeSpecification",
    "ProductActiveSpecification",
    # Sale Specifications
    "SaleByDateRangeSpecification",
    "SaleByCustomerSpecification",
    "SaleByPaymentTypeSpecification",
    "SaleAboveAmountSpecification",
    "SaleBelowAmountSpecification",
    "SaleCreditSaleSpecification",
]
