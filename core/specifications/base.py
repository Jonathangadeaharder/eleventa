"""
Base Specification Classes

Provides the foundation for the Specification pattern, including
base classes and composite specifications.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Union


T = TypeVar('T')  # The entity type (Product, Sale, etc.)


class Specification(ABC, Generic[T]):
    """
    Base class for all specifications.

    A specification encapsulates a business rule that can be used to
    test whether an object satisfies certain criteria.

    Usage:
        class ProductInStockSpecification(Specification[Product]):
            def is_satisfied_by(self, product: Product) -> bool:
                return product.quantity_in_stock > 0

            def to_sqlalchemy_filter(self):
                return Product.quantity_in_stock > 0

        # Test in memory
        spec = ProductInStockSpecification()
        if spec.is_satisfied_by(product):
            print("Product is in stock")

        # Use in database query
        query = session.query(Product).filter(spec.to_sqlalchemy_filter())
    """

    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool:
        """
        Check if the candidate satisfies this specification.

        This method is used for in-memory filtering.

        Args:
            candidate: The object to test

        Returns:
            True if the candidate satisfies the specification
        """
        pass

    @abstractmethod
    def to_sqlalchemy_filter(self):
        """
        Convert this specification to a SQLAlchemy filter expression.

        This method is used for database queries.

        Returns:
            SQLAlchemy filter expression
        """
        pass

    def and_(self, other: 'Specification[T]') -> 'AndSpecification[T]':
        """
        Create an AND specification.

        Args:
            other: Another specification

        Returns:
            AndSpecification combining self and other

        Example:
            spec = in_stock.and_(in_electronics)
            # Products that are in stock AND in electronics
        """
        return AndSpecification(self, other)

    def or_(self, other: 'Specification[T]') -> 'OrSpecification[T]':
        """
        Create an OR specification.

        Args:
            other: Another specification

        Returns:
            OrSpecification combining self and other

        Example:
            spec = low_stock.or_(out_of_stock)
            # Products that are low stock OR out of stock
        """
        return OrSpecification(self, other)

    def not_(self) -> 'NotSpecification[T]':
        """
        Create a NOT specification.

        Returns:
            NotSpecification negating self

        Example:
            spec = in_stock.not_()
            # Products that are NOT in stock
        """
        return NotSpecification(self)

    def __and__(self, other: 'Specification[T]') -> 'AndSpecification[T]':
        """
        Python & operator support.

        Example:
            spec = in_stock & in_electronics
        """
        return self.and_(other)

    def __or__(self, other: 'Specification[T]') -> 'OrSpecification[T]':
        """
        Python | operator support.

        Example:
            spec = low_stock | out_of_stock
        """
        return self.or_(other)

    def __invert__(self) -> 'NotSpecification[T]':
        """
        Python ~ operator support.

        Example:
            spec = ~in_stock  # Not in stock
        """
        return self.not_()


class CompositeSpecification(Specification[T], ABC):
    """
    Base class for composite specifications.

    Composite specifications combine multiple specifications
    using logical operators (AND, OR, NOT).
    """
    pass


class AndSpecification(CompositeSpecification[T]):
    """
    Specification that combines two specifications with AND logic.

    Satisfied when BOTH specifications are satisfied.

    Usage:
        spec = AndSpecification(in_stock, in_electronics)
        # Or using helper:
        spec = in_stock.and_(in_electronics)
        # Or using operator:
        spec = in_stock & in_electronics
    """

    def __init__(self, left: Specification[T], right: Specification[T]):
        """
        Initialize AND specification.

        Args:
            left: First specification
            right: Second specification
        """
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        """
        Check if candidate satisfies both specifications.

        Args:
            candidate: The object to test

        Returns:
            True if BOTH specifications are satisfied
        """
        return (
            self.left.is_satisfied_by(candidate) and
            self.right.is_satisfied_by(candidate)
        )

    def to_sqlalchemy_filter(self):
        """
        Convert to SQLAlchemy AND expression.

        Returns:
            SQLAlchemy AND expression
        """
        from sqlalchemy import and_
        return and_(
            self.left.to_sqlalchemy_filter(),
            self.right.to_sqlalchemy_filter()
        )

    def __repr__(self) -> str:
        return f"({self.left} AND {self.right})"


class OrSpecification(CompositeSpecification[T]):
    """
    Specification that combines two specifications with OR logic.

    Satisfied when EITHER specification is satisfied.

    Usage:
        spec = OrSpecification(low_stock, out_of_stock)
        # Or using helper:
        spec = low_stock.or_(out_of_stock)
        # Or using operator:
        spec = low_stock | out_of_stock
    """

    def __init__(self, left: Specification[T], right: Specification[T]):
        """
        Initialize OR specification.

        Args:
            left: First specification
            right: Second specification
        """
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        """
        Check if candidate satisfies either specification.

        Args:
            candidate: The object to test

        Returns:
            True if EITHER specification is satisfied
        """
        return (
            self.left.is_satisfied_by(candidate) or
            self.right.is_satisfied_by(candidate)
        )

    def to_sqlalchemy_filter(self):
        """
        Convert to SQLAlchemy OR expression.

        Returns:
            SQLAlchemy OR expression
        """
        from sqlalchemy import or_
        return or_(
            self.left.to_sqlalchemy_filter(),
            self.right.to_sqlalchemy_filter()
        )

    def __repr__(self) -> str:
        return f"({self.left} OR {self.right})"


class NotSpecification(CompositeSpecification[T]):
    """
    Specification that negates another specification.

    Satisfied when the wrapped specification is NOT satisfied.

    Usage:
        spec = NotSpecification(in_stock)
        # Or using helper:
        spec = in_stock.not_()
        # Or using operator:
        spec = ~in_stock
    """

    def __init__(self, spec: Specification[T]):
        """
        Initialize NOT specification.

        Args:
            spec: Specification to negate
        """
        self.spec = spec

    def is_satisfied_by(self, candidate: T) -> bool:
        """
        Check if candidate does NOT satisfy the specification.

        Args:
            candidate: The object to test

        Returns:
            True if specification is NOT satisfied
        """
        return not self.spec.is_satisfied_by(candidate)

    def to_sqlalchemy_filter(self):
        """
        Convert to SQLAlchemy NOT expression.

        Returns:
            SQLAlchemy NOT expression
        """
        from sqlalchemy import not_
        return not_(self.spec.to_sqlalchemy_filter())

    def __repr__(self) -> str:
        return f"NOT({self.spec})"


class ParameterizedSpecification(Specification[T], ABC):
    """
    Base class for specifications that take parameters.

    Example:
        class ProductInDepartmentSpecification(ParameterizedSpecification[Product]):
            def __init__(self, department_id):
                self.department_id = department_id

            def is_satisfied_by(self, product):
                return product.department_id == self.department_id

            def to_sqlalchemy_filter(self):
                return Product.department_id == self.department_id
    """
    pass
