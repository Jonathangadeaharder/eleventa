# Specification Pattern Guide

## Table of Contents
1. [Overview](#overview)
2. [Why Specifications?](#why-specifications)
3. [Basic Concepts](#basic-concepts)
4. [Creating Specifications](#creating-specifications)
5. [Composing Specifications](#composing-specifications)
6. [Repository Integration](#repository-integration)
7. [Examples](#examples)
8. [Best Practices](#best-practices)
9. [Testing](#testing)

## Overview

The **Specification Pattern** is a software design pattern that encapsulates business rules into reusable, composable objects. It allows you to define complex query logic in a type-safe, testable way.

### Key Benefits

- **Reusable**: Write once, use everywhere
- **Composable**: Combine specifications with AND, OR, NOT
- **Testable**: Easy to unit test business rules
- **Type-Safe**: Compile-time checking
- **Readable**: Business rules as named classes
- **Maintainable**: Change rules in one place

### When to Use

✅ **Use Specifications When:**
- You have complex querying logic that's reused
- Business rules need to be composed dynamically
- Query logic should be testable independently
- You want to keep repository methods focused

❌ **Don't Use Specifications When:**
- Query is simple and used once (e.g., `get_by_id`)
- Performance requires hand-optimized SQL
- Logic is purely UI-specific

## Why Specifications?

### Problem: Without Specifications

```python
# ❌ Problem: Query logic scattered everywhere

# In UI layer:
products = [p for p in all_products
            if p.quantity_in_stock > 0
            and p.department_id == dept_id
            and p.sell_price >= min_price
            and p.sell_price <= max_price]

# In report:
products = product_repo.get_all()
filtered = []
for p in products:
    if p.quantity_in_stock > 0 and p.department_id == dept_id:
        if p.sell_price >= min_price and p.sell_price <= max_price:
            filtered.append(p)

# In service:
def get_available_products(dept_id, min_price, max_price):
    # Same logic duplicated AGAIN
    pass
```

**Problems:**
- Logic duplicated across codebase
- Hard to test
- Easy to make mistakes
- Difficult to change rules
- No type safety

### Solution: With Specifications

```python
# ✅ Solution: Encapsulated, reusable, composable

# Define once:
spec = (products_in_stock()
        .and_(products_in_department(dept_id))
        .and_(products_in_price_range(min_price, max_price)))

# Use everywhere:
products = repo.find_by_specification(spec)

# Easy to test:
def test_specification():
    spec = products_in_stock()
    assert spec.is_satisfied_by(product_with_stock)
    assert not spec.is_satisfied_by(product_out_of_stock)
```

## Basic Concepts

### Specification Interface

Every specification implements two key methods:

```python
class Specification(ABC, Generic[T]):
    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool:
        """Check if candidate satisfies the specification (in-memory)."""
        pass

    @abstractmethod
    def to_sqlalchemy_filter(self):
        """Convert to SQLAlchemy filter (for database queries)."""
        pass
```

### Two Execution Modes

1. **In-Memory Filtering** (`is_satisfied_by`)
   - For testing
   - For filtering loaded objects
   - For validation

2. **Database Filtering** (`to_sqlalchemy_filter`)
   - For efficient database queries
   - Generates SQL WHERE clauses
   - Avoids loading unnecessary data

## Creating Specifications

### Simple Specification (No Parameters)

```python
from core.specifications.base import Specification
from core.models.product import Product

class ProductInStockSpecification(Specification[Product]):
    """Specification for products that are in stock."""

    def is_satisfied_by(self, product: Product) -> bool:
        """Check in-memory."""
        return product.quantity_in_stock > 0

    def to_sqlalchemy_filter(self):
        """Convert to SQL filter."""
        from infrastructure.persistence.sqlite.models_mapping import Product as ProductOrm
        return ProductOrm.quantity_in_stock > 0

    def __repr__(self) -> str:
        return "ProductInStock"


# Convenience factory function
def products_in_stock() -> ProductInStockSpecification:
    """Create specification for products in stock."""
    return ProductInStockSpecification()
```

### Parameterized Specification

```python
from core.specifications.base import ParameterizedSpecification
from uuid import UUID

class ProductInDepartmentSpecification(ParameterizedSpecification[Product]):
    """Specification for products in a specific department."""

    def __init__(self, department_id: UUID):
        self.department_id = department_id

    def is_satisfied_by(self, product: Product) -> bool:
        """Check in-memory."""
        return product.department_id == self.department_id

    def to_sqlalchemy_filter(self):
        """Convert to SQL filter."""
        from infrastructure.persistence.sqlite.models_mapping import Product as ProductOrm
        return ProductOrm.department_id == self.department_id

    def __repr__(self) -> str:
        return f"ProductInDepartment({self.department_id})"


# Convenience factory function
def products_in_department(department_id: UUID) -> ProductInDepartmentSpecification:
    """Create specification for products in department."""
    return ProductInDepartmentSpecification(department_id)
```

### Complex Specification

```python
from decimal import Decimal

class ProductPriceRangeSpecification(ParameterizedSpecification[Product]):
    """Specification for products within a price range."""

    def __init__(
        self,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None
    ):
        if min_price is None and max_price is None:
            raise ValueError("At least one price boundary must be specified")

        self.min_price = min_price
        self.max_price = max_price

    def is_satisfied_by(self, product: Product) -> bool:
        """Check in-memory."""
        if self.min_price is not None and product.sell_price < self.min_price:
            return False
        if self.max_price is not None and product.sell_price > self.max_price:
            return False
        return True

    def to_sqlalchemy_filter(self):
        """Convert to SQL filter."""
        from infrastructure.persistence.sqlite.models_mapping import Product as ProductOrm
        from sqlalchemy import and_

        filters = []
        if self.min_price is not None:
            filters.append(ProductOrm.sell_price >= self.min_price)
        if self.max_price is not None:
            filters.append(ProductOrm.sell_price <= self.max_price)

        return and_(*filters) if len(filters) > 1 else filters[0]

    def __repr__(self) -> str:
        return f"ProductPriceRange(min={self.min_price}, max={self.max_price})"


# Convenience factory
def products_in_price_range(
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None
) -> ProductPriceRangeSpecification:
    """Create specification for products in price range."""
    return ProductPriceRangeSpecification(min_price, max_price)
```

## Composing Specifications

### AND Composition

```python
# Combine multiple specifications with AND

spec = (products_in_stock()
        .and_(products_in_department(dept_id))
        .and_(products_in_price_range(min_price=Decimal('10'))))

# Generated SQL (approximately):
# WHERE quantity_in_stock > 0
#   AND department_id = :dept_id
#   AND sell_price >= 10

# Usage:
products = repo.find_by_specification(spec)
```

### OR Composition

```python
# Combine specifications with OR

spec = (products_low_stock()
        .or_(products_out_of_stock()))

# Generated SQL (approximately):
# WHERE (quantity_in_stock < min_stock)
#    OR (quantity_in_stock = 0)

# Usage:
products_needing_attention = repo.find_by_specification(spec)
```

### NOT Composition

```python
# Negate a specification

spec = products_in_stock().not_()

# Or equivalently:
spec = products_out_of_stock()

# Generated SQL (approximately):
# WHERE NOT (quantity_in_stock > 0)
```

### Complex Compositions

```python
# Combine AND, OR, NOT

# Find: (in_stock OR low_stock) AND in_electronics AND NOT expensive
spec = (products_in_stock().or_(products_low_stock())
        .and_(products_in_department(electronics_dept_id))
        .and_(products_in_price_range(max_price=Decimal('100'))))

# Find: in_stock AND (electronics OR home_goods)
in_electronics = products_in_department(electronics_id)
in_home = products_in_department(home_id)

spec = products_in_stock().and_(
    in_electronics.or_(in_home)
)
```

## Repository Integration

### Repository Interface

```python
from core.interfaces.specification_repository import ISpecificationRepository

class IProductRepository(ISpecificationRepository[Product]):
    """Product repository with specification support."""

    def find_by_specification(
        self,
        specification: Specification[Product]
    ) -> List[Product]:
        """Find all products matching specification."""
        pass
```

### Repository Implementation

```python
from infrastructure.persistence.repository_base import RepositoryBase
from core.interfaces.specification_repository import SpecificationRepositoryMixin

class ProductRepository(
    RepositoryBase[Product],
    IProductRepository,
    SpecificationRepositoryMixin[Product]
):
    """
    Product repository with specification support.

    Uses SpecificationRepositoryMixin to provide specification methods.
    """

    def __init__(self, session: Session):
        super().__init__(session)
        from infrastructure.persistence.sqlite.models_mapping import Product as ProductOrm
        self._entity_class = ProductOrm

    # Standard repository methods...

    def get_by_id(self, product_id: UUID) -> Optional[Product]:
        """Get product by ID."""
        # ... standard implementation ...
        pass

    # Specification methods inherited from mixin:
    # - find_by_specification(spec)
    # - find_one_by_specification(spec)
    # - count_by_specification(spec)
    # - exists_by_specification(spec)
    # - find_by_specification_paginated(spec, limit, offset)
```

### Using Specifications in Repository

```python
# In application code:

product_repo = ProductRepository(session)

# Find with specification
spec = products_in_stock().and_(products_in_department(dept_id))
products = product_repo.find_by_specification(spec)

# Count with specification
low_stock_spec = products_low_stock()
count = product_repo.count_by_specification(low_stock_spec)

# Check existence
out_of_stock_spec = products_out_of_stock()
has_out_of_stock = product_repo.exists_by_specification(out_of_stock_spec)

# Pagination
spec = products_in_department(dept_id)
page_1 = product_repo.find_by_specification_paginated(spec, limit=20, offset=0)
page_2 = product_repo.find_by_specification_paginated(spec, limit=20, offset=20)
```

## Examples

### Example 1: Product Search

```python
from decimal import Decimal
from core.specifications.product_specifications import *

def search_products(
    department_id: Optional[UUID] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    in_stock_only: bool = False,
    search_term: Optional[str] = None
) -> List[Product]:
    """Search products with flexible filters."""

    # Start with base specification
    spec = products_active()

    # Add filters dynamically
    if department_id:
        spec = spec.and_(products_in_department(department_id))

    if min_price or max_price:
        spec = spec.and_(products_in_price_range(min_price, max_price))

    if in_stock_only:
        spec = spec.and_(products_in_stock())

    if search_term:
        # Search in code OR description
        code_spec = products_code_like(search_term)
        desc_spec = products_description_like(search_term)
        spec = spec.and_(code_spec.or_(desc_spec))

    return product_repo.find_by_specification(spec)


# Usage:
electronics = search_products(
    department_id=electronics_dept_id,
    min_price=Decimal('50'),
    max_price=Decimal('500'),
    in_stock_only=True,
    search_term="laptop"
)
```

### Example 2: Sales Reports

```python
from datetime import datetime
from core.specifications.sale_specifications import *

def get_credit_sales_report(start_date: datetime, end_date: datetime):
    """Get credit sales within date range."""

    spec = (sales_by_date_range(start_date, end_date)
            .and_(credit_sales()))

    sales = sale_repo.find_by_specification(spec)

    total = sum(sale.total for sale in sales)
    count = len(sales)

    return {
        'sales': sales,
        'total': total,
        'count': count,
        'average': total / count if count > 0 else Decimal('0')
    }


# Usage:
from datetime import datetime, timedelta

today = datetime.now()
week_ago = today - timedelta(days=7)

report = get_credit_sales_report(week_ago, today)
print(f"Credit sales this week: {report['count']}")
print(f"Total: ${report['total']}")
```

### Example 3: Inventory Alerts

```python
def get_inventory_alerts(department_id: Optional[UUID] = None):
    """Get products needing attention."""

    # Products that are low stock OR out of stock
    needs_attention = products_low_stock().or_(products_out_of_stock())

    # Filter by department if specified
    if department_id:
        needs_attention = needs_attention.and_(
            products_in_department(department_id)
        )

    return product_repo.find_by_specification(needs_attention)


# Usage:
alerts = get_inventory_alerts(department_id=electronics_dept_id)
for product in alerts:
    if product.quantity_in_stock == 0:
        print(f"OUT OF STOCK: {product.code}")
    else:
        print(f"LOW STOCK: {product.code} ({product.quantity_in_stock})")
```

### Example 4: Customer Analysis

```python
def get_high_value_credit_sales(
    min_amount: Decimal,
    start_date: datetime,
    end_date: datetime
) -> List[Sale]:
    """Find high-value credit sales."""

    spec = (sales_by_date_range(start_date, end_date)
            .and_(credit_sales())
            .and_(sales_above_amount(min_amount)))

    return sale_repo.find_by_specification(spec)


# Usage:
high_value_credit = get_high_value_credit_sales(
    min_amount=Decimal('1000'),
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)

print(f"Found {len(high_value_credit)} high-value credit sales")
```

## Best Practices

### 1. Name Specifications Clearly

```python
# ✅ Good: Clear, descriptive names
class ProductInStockSpecification(Specification[Product]):
    pass

# ❌ Bad: Vague names
class ProductSpec1(Specification[Product]):
    pass
```

### 2. Provide Factory Functions

```python
# ✅ Good: Provide convenient factory functions
def products_in_stock() -> ProductInStockSpecification:
    return ProductInStockSpecification()

# Usage is clean:
spec = products_in_stock()

# ❌ Bad: Force users to instantiate classes
spec = ProductInStockSpecification()  # More verbose
```

### 3. Keep Specifications Focused

```python
# ✅ Good: Single responsibility
class ProductInStockSpecification(Specification[Product]):
    def is_satisfied_by(self, product: Product) -> bool:
        return product.quantity_in_stock > 0

class ProductLowStockSpecification(Specification[Product]):
    def is_satisfied_by(self, product: Product) -> bool:
        return (product.min_stock is not None and
                product.quantity_in_stock < product.min_stock)

# Combine them:
spec = products_in_stock().and_(products_low_stock())

# ❌ Bad: Multiple responsibilities
class ProductStockStatusSpecification(Specification[Product]):
    def __init__(self, check_in_stock, check_low_stock):
        # Too many responsibilities
        pass
```

### 4. Make Specifications Immutable

```python
# ✅ Good: Immutable specifications
class ProductInDepartmentSpecification(ParameterizedSpecification[Product]):
    def __init__(self, department_id: UUID):
        self.department_id = department_id  # Set once, never changed

    # No setters!

# ❌ Bad: Mutable specifications
class ProductInDepartmentSpecification(ParameterizedSpecification[Product]):
    def set_department(self, department_id: UUID):
        self.department_id = department_id  # Bad: mutable state
```

### 5. Use Type Hints

```python
# ✅ Good: Typed
class ProductInStockSpecification(Specification[Product]):
    def is_satisfied_by(self, product: Product) -> bool:
        return product.quantity_in_stock > 0

# ❌ Bad: Untyped
class ProductInStockSpecification(Specification):
    def is_satisfied_by(self, product):
        return product.quantity_in_stock > 0
```

### 6. Test Both Execution Modes

```python
def test_product_in_stock_specification():
    """Test specification in both modes."""
    spec = ProductInStockSpecification()

    # Test in-memory
    product_in_stock = Product(quantity_in_stock=Decimal('10'))
    product_out_of_stock = Product(quantity_in_stock=Decimal('0'))

    assert spec.is_satisfied_by(product_in_stock)
    assert not spec.is_satisfied_by(product_out_of_stock)

    # Test database query
    filter_expr = spec.to_sqlalchemy_filter()
    assert filter_expr is not None
    # Additional SQL query tests...
```

### 7. Document Business Rules

```python
class ProductLowStockSpecification(Specification[Product]):
    """
    Specification for products with low stock.

    Business Rule:
        A product is considered "low stock" when its current quantity
        is below its configured minimum stock level.

    Usage:
        spec = products_low_stock()
        low_stock_products = repo.find_by_specification(spec)

    Notes:
        - Products without a min_stock setting are not considered low stock
        - This is used for inventory alerts and reordering
    """
    pass
```

### 8. Avoid Over-Specification

```python
# ✅ Good: Specifications for reusable business rules
spec = products_low_stock()  # Reused everywhere

# ❌ Bad: Specifications for one-off queries
class ProductWithCodeP001Specification(Specification[Product]):
    # This is too specific! Just use get_by_code('P001')
    pass
```

## Testing

### Testing Specifications

```python
import pytest
from decimal import Decimal
from core.models.product import Product
from core.specifications.product_specifications import *

class TestProductSpecifications:
    """Test suite for product specifications."""

    def test_product_in_stock_satisfied(self):
        """Test product in stock specification."""
        # Arrange
        spec = products_in_stock()
        product = Product(
            code="P001",
            description="Test Product",
            quantity_in_stock=Decimal('10')
        )

        # Act & Assert
        assert spec.is_satisfied_by(product)

    def test_product_out_of_stock_not_satisfied(self):
        """Test product out of stock doesn't satisfy in_stock spec."""
        # Arrange
        spec = products_in_stock()
        product = Product(
            code="P001",
            description="Test Product",
            quantity_in_stock=Decimal('0')
        )

        # Act & Assert
        assert not spec.is_satisfied_by(product)

    def test_product_low_stock_satisfied(self):
        """Test low stock specification."""
        # Arrange
        spec = products_low_stock()
        product = Product(
            code="P001",
            description="Test Product",
            quantity_in_stock=Decimal('5'),
            min_stock=Decimal('10')
        )

        # Act & Assert
        assert spec.is_satisfied_by(product)

    def test_product_price_range_satisfied(self):
        """Test price range specification."""
        # Arrange
        spec = products_in_price_range(
            min_price=Decimal('10'),
            max_price=Decimal('100')
        )
        product = Product(
            code="P001",
            description="Test Product",
            sell_price=Decimal('50')
        )

        # Act & Assert
        assert spec.is_satisfied_by(product)

    def test_specification_composition_and(self):
        """Test AND composition."""
        # Arrange
        spec1 = products_in_stock()
        spec2 = products_in_price_range(max_price=Decimal('100'))
        composed = spec1.and_(spec2)

        product_match = Product(
            quantity_in_stock=Decimal('10'),
            sell_price=Decimal('50')
        )
        product_no_match = Product(
            quantity_in_stock=Decimal('10'),
            sell_price=Decimal('200')
        )

        # Act & Assert
        assert composed.is_satisfied_by(product_match)
        assert not composed.is_satisfied_by(product_no_match)

    def test_specification_composition_or(self):
        """Test OR composition."""
        # Arrange
        spec1 = products_low_stock()
        spec2 = products_out_of_stock()
        composed = spec1.or_(spec2)

        low_stock_product = Product(
            quantity_in_stock=Decimal('5'),
            min_stock=Decimal('10')
        )
        out_of_stock_product = Product(
            quantity_in_stock=Decimal('0')
        )
        ok_product = Product(
            quantity_in_stock=Decimal('20'),
            min_stock=Decimal('10')
        )

        # Act & Assert
        assert composed.is_satisfied_by(low_stock_product)
        assert composed.is_satisfied_by(out_of_stock_product)
        assert not composed.is_satisfied_by(ok_product)


class TestSaleSpecifications:
    """Test suite for sale specifications."""

    def test_sale_by_date_range(self):
        """Test date range specification."""
        from datetime import datetime
        from core.models.sale import Sale
        from core.specifications.sale_specifications import sales_by_date_range

        # Arrange
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)
        spec = sales_by_date_range(start, end)

        sale_in_range = Sale(created_at=datetime(2024, 1, 15))
        sale_out_of_range = Sale(created_at=datetime(2024, 2, 1))

        # Act & Assert
        assert spec.is_satisfied_by(sale_in_range)
        assert not spec.is_satisfied_by(sale_out_of_range)

    def test_sale_by_payment_type(self):
        """Test payment type specification."""
        from core.models.sale import Sale
        from core.specifications.sale_specifications import credit_sales

        # Arrange
        spec = credit_sales()

        credit_sale = Sale(payment_type='credit')
        cash_sale = Sale(payment_type='cash')

        # Act & Assert
        assert spec.is_satisfied_by(credit_sale)
        assert not spec.is_satisfied_by(cash_sale)
```

### Testing Repository Integration

```python
class TestProductRepositorySpecifications:
    """Test specification integration with repository."""

    @pytest.fixture
    def product_repo(self, session):
        """Create product repository."""
        return ProductRepository(session)

    @pytest.fixture
    def sample_products(self, product_repo):
        """Create sample products."""
        products = [
            Product(code="P001", quantity_in_stock=Decimal('10')),
            Product(code="P002", quantity_in_stock=Decimal('0')),
            Product(code="P003", quantity_in_stock=Decimal('5'),
                   min_stock=Decimal('10')),
        ]
        for p in products:
            product_repo.add(p)
        return products

    def test_find_by_specification(self, product_repo, sample_products):
        """Test finding products by specification."""
        # Arrange
        spec = products_in_stock()

        # Act
        results = product_repo.find_by_specification(spec)

        # Assert
        assert len(results) == 2  # P001 and P003
        assert all(p.quantity_in_stock > 0 for p in results)

    def test_count_by_specification(self, product_repo, sample_products):
        """Test counting products by specification."""
        # Arrange
        spec = products_out_of_stock()

        # Act
        count = product_repo.count_by_specification(spec)

        # Assert
        assert count == 1  # Only P002

    def test_exists_by_specification(self, product_repo, sample_products):
        """Test checking existence by specification."""
        # Arrange
        spec = products_low_stock()

        # Act
        exists = product_repo.exists_by_specification(spec)

        # Assert
        assert exists  # P003 is low stock
```

## Summary

The Specification Pattern is a powerful tool for:
- Encapsulating business rules
- Creating reusable query logic
- Building composable queries
- Improving testability
- Maintaining clean code

### Key Takeaways

1. **Specifications encapsulate business rules** into reusable objects
2. **Compose specifications** with AND, OR, NOT for complex queries
3. **Two execution modes**: in-memory (`is_satisfied_by`) and database (`to_sqlalchemy_filter`)
4. **Repository integration** provides clean query API
5. **Factory functions** make usage convenient
6. **Test both modes** to ensure correctness

### Next Steps

1. Review existing specifications in `core/specifications/`
2. Integrate specifications into your repositories
3. Replace duplicated query logic with specifications
4. Write tests for your specifications
5. Document business rules in specification classes

### Related Patterns

- **Repository Pattern**: Specifications work with repositories
- **Query Object Pattern**: Similar concept, specifications are more focused
- **Strategy Pattern**: Specifications are strategies for filtering
- **Composite Pattern**: Specifications can be composed

### Resources

- [Martin Fowler - Specification Pattern](https://www.martinfowler.com/apsupp/spec.pdf)
- [Domain-Driven Design](https://www.domainlanguage.com/ddd/)
- [Cosmic Python - Repository Pattern](https://www.cosmicpython.com/book/chapter_02_repository.html)
