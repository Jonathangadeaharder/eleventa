"""
Product Specifications

Concrete specifications for product queries.
These encapsulate common product filtering logic.
"""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from core.specifications.base import Specification, ParameterizedSpecification
from core.models.product import Product


class ProductInStockSpecification(Specification[Product]):
    """
    Specification for products that are in stock.

    Satisfied when quantity_in_stock > 0.

    Usage:
        spec = ProductInStockSpecification()
        in_stock_products = repository.find_by_specification(spec)
    """

    def is_satisfied_by(self, product: Product) -> bool:
        """Check if product is in stock."""
        return product.quantity_in_stock > 0

    def to_sqlalchemy_filter(self):
        """Convert to SQLAlchemy filter."""
        from infrastructure.persistence.sqlite.models_mapping import (
            Product as ProductOrm,
        )

        return ProductOrm.quantity_in_stock > 0

    def __repr__(self) -> str:
        return "ProductInStock"


class ProductOutOfStockSpecification(Specification[Product]):
    """
    Specification for products that are out of stock.

    Satisfied when quantity_in_stock <= 0.

    Usage:
        spec = ProductOutOfStockSpecification()
        out_of_stock = repository.find_by_specification(spec)
    """

    def is_satisfied_by(self, product: Product) -> bool:
        """Check if product is out of stock."""
        return product.quantity_in_stock <= 0

    def to_sqlalchemy_filter(self):
        """Convert to SQLAlchemy filter."""
        from infrastructure.persistence.sqlite.models_mapping import (
            Product as ProductOrm,
        )

        return ProductOrm.quantity_in_stock <= 0

    def __repr__(self) -> str:
        return "ProductOutOfStock"


class ProductLowStockSpecification(Specification[Product]):
    """
    Specification for products with low stock.

    Satisfied when quantity_in_stock < min_stock.

    Usage:
        spec = ProductLowStockSpecification()
        low_stock_products = repository.find_by_specification(spec)
    """

    def is_satisfied_by(self, product: Product) -> bool:
        """Check if product has low stock."""
        if product.min_stock is None:
            return False
        return product.quantity_in_stock < product.min_stock

    def to_sqlalchemy_filter(self):
        """Convert to SQLAlchemy filter."""
        from infrastructure.persistence.sqlite.models_mapping import (
            Product as ProductOrm,
        )
        from sqlalchemy import and_

        return and_(
            ProductOrm.min_stock.isnot(None),
            ProductOrm.quantity_in_stock < ProductOrm.min_stock,
        )

    def __repr__(self) -> str:
        return "ProductLowStock"


class ProductInDepartmentSpecification(ParameterizedSpecification[Product]):
    """
    Specification for products in a specific department.

    Usage:
        spec = ProductInDepartmentSpecification(electronics_dept_id)
        electronics = repository.find_by_specification(spec)
    """

    def __init__(self, department_id: UUID):
        """
        Initialize specification.

        Args:
            department_id: The department ID to filter by
        """
        self.department_id = department_id

    def is_satisfied_by(self, product: Product) -> bool:
        """Check if product is in the specified department."""
        return product.department_id == self.department_id

    def to_sqlalchemy_filter(self):
        """Convert to SQLAlchemy filter."""
        from infrastructure.persistence.sqlite.models_mapping import (
            Product as ProductOrm,
        )

        return ProductOrm.department_id == self.department_id

    def __repr__(self) -> str:
        return f"ProductInDepartment({self.department_id})"


class ProductPriceRangeSpecification(ParameterizedSpecification[Product]):
    """
    Specification for products within a price range.

    Usage:
        spec = ProductPriceRangeSpecification(
            min_price=Decimal('100'),
            max_price=Decimal('500')
        )
        products_in_range = repository.find_by_specification(spec)
    """

    def __init__(
        self, min_price: Optional[Decimal] = None, max_price: Optional[Decimal] = None
    ):
        """
        Initialize specification.

        Args:
            min_price: Minimum price (inclusive), None for no minimum
            max_price: Maximum price (inclusive), None for no maximum
        """
        self.min_price = min_price
        self.max_price = max_price

    def is_satisfied_by(self, product: Product) -> bool:
        """Check if product price is within range."""
        if self.min_price is not None and product.sell_price < self.min_price:
            return False
        if self.max_price is not None and product.sell_price > self.max_price:
            return False
        return True

    def to_sqlalchemy_filter(self):
        """Convert to SQLAlchemy filter."""
        from infrastructure.persistence.sqlite.models_mapping import (
            Product as ProductOrm,
        )
        from sqlalchemy import and_

        conditions = []
        if self.min_price is not None:
            conditions.append(ProductOrm.sell_price >= self.min_price)
        if self.max_price is not None:
            conditions.append(ProductOrm.sell_price <= self.max_price)

        if not conditions:
            return True  # No filter
        elif len(conditions) == 1:
            return conditions[0]
        else:
            return and_(*conditions)

    def __repr__(self) -> str:
        return f"ProductPriceRange({self.min_price}, {self.max_price})"


class ProductCodeLikeSpecification(ParameterizedSpecification[Product]):
    """
    Specification for products with code matching a pattern.

    Usage:
        spec = ProductCodeLikeSpecification("LAPTOP%")
        laptops = repository.find_by_specification(spec)
    """

    def __init__(self, pattern: str):
        """
        Initialize specification.

        Args:
            pattern: Pattern to match (case-insensitive)
        """
        self.pattern = pattern.lower()

    def is_satisfied_by(self, product: Product) -> bool:
        """Check if product code matches pattern."""
        # Simple pattern matching (% = wildcard)
        pattern = self.pattern.replace("%", ".*")
        import re

        return bool(re.search(pattern, product.code.lower()))

    def to_sqlalchemy_filter(self):
        """Convert to SQLAlchemy filter."""
        from infrastructure.persistence.sqlite.models_mapping import (
            Product as ProductOrm,
        )
        from sqlalchemy import func

        return func.lower(ProductOrm.code).like(self.pattern)

    def __repr__(self) -> str:
        return f"ProductCodeLike('{self.pattern}')"


class ProductDescriptionLikeSpecification(ParameterizedSpecification[Product]):
    """
    Specification for products with description matching a pattern.

    Usage:
        spec = ProductDescriptionLikeSpecification("%laptop%")
        products = repository.find_by_specification(spec)
    """

    def __init__(self, pattern: str):
        """
        Initialize specification.

        Args:
            pattern: Pattern to match (case-insensitive)
        """
        self.pattern = pattern.lower()

    def is_satisfied_by(self, product: Product) -> bool:
        """Check if product description matches pattern."""
        pattern = self.pattern.replace("%", ".*")
        import re

        return bool(re.search(pattern, product.description.lower()))

    def to_sqlalchemy_filter(self):
        """Convert to SQLAlchemy filter."""
        from infrastructure.persistence.sqlite.models_mapping import (
            Product as ProductOrm,
        )
        from sqlalchemy import func

        return func.lower(ProductOrm.description).like(self.pattern)

    def __repr__(self) -> str:
        return f"ProductDescriptionLike('{self.pattern}')"


class ProductActiveSpecification(Specification[Product]):
    """
    Specification for active products.

    Satisfied when is_active = True.

    Usage:
        spec = ProductActiveSpecification()
        active_products = repository.find_by_specification(spec)
    """

    def is_satisfied_by(self, product: Product) -> bool:
        """Check if product is active."""
        return getattr(product, "is_active", True)  # Default to True if not present

    def to_sqlalchemy_filter(self):
        """Convert to SQLAlchemy filter."""
        from infrastructure.persistence.sqlite.models_mapping import (
            Product as ProductOrm,
        )

        # Assuming is_active field exists
        return ProductOrm.is_active == True

    def __repr__(self) -> str:
        return "ProductActive"


class ProductUsesInventorySpecification(Specification[Product]):
    """
    Specification for products that use inventory tracking.

    Usage:
        spec = ProductUsesInventorySpecification()
        tracked_products = repository.find_by_specification(spec)
    """

    def is_satisfied_by(self, product: Product) -> bool:
        """Check if product uses inventory."""
        return product.uses_inventory

    def to_sqlalchemy_filter(self):
        """Convert to SQLAlchemy filter."""
        from infrastructure.persistence.sqlite.models_mapping import (
            Product as ProductOrm,
        )

        return ProductOrm.uses_inventory == True

    def __repr__(self) -> str:
        return "ProductUsesInventory"


# Convenience factory functions


def products_in_stock() -> ProductInStockSpecification:
    """Create specification for in-stock products."""
    return ProductInStockSpecification()


def products_out_of_stock() -> ProductOutOfStockSpecification:
    """Create specification for out-of-stock products."""
    return ProductOutOfStockSpecification()


def products_with_low_stock() -> ProductLowStockSpecification:
    """Create specification for low-stock products."""
    return ProductLowStockSpecification()


def products_in_department(department_id: UUID) -> ProductInDepartmentSpecification:
    """Create specification for products in a department."""
    return ProductInDepartmentSpecification(department_id)


def products_in_price_range(
    min_price: Optional[Decimal] = None, max_price: Optional[Decimal] = None
) -> ProductPriceRangeSpecification:
    """Create specification for products in a price range."""
    return ProductPriceRangeSpecification(min_price, max_price)


def products_with_code_like(pattern: str) -> ProductCodeLikeSpecification:
    """Create specification for products with code matching pattern."""
    return ProductCodeLikeSpecification(pattern)


def products_with_description_like(pattern: str) -> ProductDescriptionLikeSpecification:
    """Create specification for products with description matching pattern."""
    return ProductDescriptionLikeSpecification(pattern)


def active_products() -> ProductActiveSpecification:
    """Create specification for active products."""
    return ProductActiveSpecification()
