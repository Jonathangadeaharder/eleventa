"""
Specification-Aware Repository Interface

Extension to standard repositories that support the Specification Pattern.
This allows repositories to accept specifications for flexible querying.

Usage:
    spec = products_in_stock().and_(products_in_department(dept_id))
    products = product_repo.find_by_specification(spec)

Benefits:
- Encapsulates business rules in reusable specifications
- Composable queries (AND, OR, NOT)
- Type-safe
- Works with both in-memory and database queries
- Testable
"""

from abc import ABC, abstractmethod
from typing import List, TypeVar, Generic, Optional
from core.specifications.base import Specification

T = TypeVar('T')


class ISpecificationRepository(ABC, Generic[T]):
    """
    Repository interface that supports specification-based queries.

    This extends the standard repository interface with specification support.
    Repositories implementing this interface can accept Specification objects
    for filtering.

    Usage:
        class IProductSpecificationRepository(IProductRepository, ISpecificationRepository[Product]):
            pass

        # Then use it:
        spec = ProductInStockSpecification()
        products = repo.find_by_specification(spec)
    """

    @abstractmethod
    def find_by_specification(self, specification: Specification[T]) -> List[T]:
        """
        Find all entities matching the specification.

        Args:
            specification: The specification to match against

        Returns:
            List of entities matching the specification

        Example:
            spec = ProductInStockSpecification()
            in_stock_products = repo.find_by_specification(spec)

            # With composition:
            spec = products_in_stock().and_(products_in_department(dept_id))
            filtered = repo.find_by_specification(spec)
        """
        pass  # pragma: no cover

    @abstractmethod
    def find_one_by_specification(
        self,
        specification: Specification[T]
    ) -> Optional[T]:
        """
        Find first entity matching the specification.

        Args:
            specification: The specification to match against

        Returns:
            First entity matching specification or None

        Example:
            spec = ProductByCodeSpecification('P001')
            product = repo.find_one_by_specification(spec)
        """
        pass  # pragma: no cover

    @abstractmethod
    def count_by_specification(self, specification: Specification[T]) -> int:
        """
        Count entities matching the specification.

        Args:
            specification: The specification to match against

        Returns:
            Count of entities matching specification

        Example:
            spec = ProductLowStockSpecification()
            low_stock_count = repo.count_by_specification(spec)
        """
        pass  # pragma: no cover

    @abstractmethod
    def exists_by_specification(self, specification: Specification[T]) -> bool:
        """
        Check if any entity matches the specification.

        Args:
            specification: The specification to match against

        Returns:
            True if at least one entity matches, False otherwise

        Example:
            spec = ProductOutOfStockSpecification()
            has_out_of_stock = repo.exists_by_specification(spec)
        """
        pass  # pragma: no cover


class IPageableSpecificationRepository(ISpecificationRepository[T], Generic[T]):
    """
    Specification repository with pagination support.

    Extends ISpecificationRepository with pagination capabilities.
    """

    @abstractmethod
    def find_by_specification_paginated(
        self,
        specification: Specification[T],
        limit: int = 100,
        offset: int = 0
    ) -> List[T]:
        """
        Find entities matching specification with pagination.

        Args:
            specification: The specification to match against
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of entities matching specification (paginated)

        Example:
            spec = ProductInDepartmentSpecification(dept_id)
            page_1 = repo.find_by_specification_paginated(spec, limit=20, offset=0)
            page_2 = repo.find_by_specification_paginated(spec, limit=20, offset=20)
        """
        pass  # pragma: no cover


# Concrete Repository Interfaces with Specification Support

from core.models.product import Product
from core.models.sale import Sale


class IProductSpecificationRepository(IPageableSpecificationRepository[Product]):
    """
    Product repository with specification support.

    Combines standard product repository methods with specification queries.

    Usage:
        # Standard methods still work:
        product = repo.get_by_id(product_id)

        # Plus specification methods:
        spec = products_in_stock().and_(products_low_stock())
        low_stock_in_stock = repo.find_by_specification(spec)
    """

    # Standard product repository methods would be inherited here
    # (from IProductRepository in repository_interfaces.py)

    def find_low_stock_in_department(self, department_id) -> List[Product]:
        """
        Example convenience method using specifications internally.

        This demonstrates how repository methods can use specifications
        internally while providing a simple API.
        """
        from core.specifications.product_specifications import (
            products_low_stock,
            products_in_department
        )
        spec = products_low_stock().and_(products_in_department(department_id))
        return self.find_by_specification(spec)


class ISaleSpecificationRepository(IPageableSpecificationRepository[Sale]):
    """
    Sale repository with specification support.

    Usage:
        from datetime import datetime
        spec = sales_by_date_range(start_date, end_date).and_(credit_sales())
        credit_sales_today = repo.find_by_specification(spec)
    """
    pass


# Base Implementation Helper

class SpecificationRepositoryMixin(Generic[T]):
    """
    Mixin class providing default specification repository implementation.

    This can be mixed into concrete repository implementations to provide
    specification support.

    Requirements:
    - Must have self.session (SQLAlchemy session)
    - Must define self._entity_class (ORM model class)
    - Must implement _entity_to_domain(entity) -> T

    Usage:
        class ProductRepository(
            RepositoryBase[Product],
            IProductSpecificationRepository,
            SpecificationRepositoryMixin[Product]
        ):
            def __init__(self, session: Session):
                super().__init__(session)
                self._entity_class = ProductOrm
    """

    def find_by_specification(self, specification: Specification[T]) -> List[T]:
        """
        Find all entities matching the specification.

        Uses the specification's to_sqlalchemy_filter() method to
        build a database query.
        """
        if not hasattr(self, 'session') or not hasattr(self, '_entity_class'):
            raise NotImplementedError(
                "SpecificationRepositoryMixin requires session and _entity_class"
            )

        # Get SQLAlchemy filter from specification
        filter_expr = specification.to_sqlalchemy_filter()

        # Query database
        query = self.session.query(self._entity_class)
        if filter_expr is not None:
            query = query.filter(filter_expr)

        entities = query.all()

        # Convert to domain models
        return [self._entity_to_domain(e) for e in entities]

    def find_one_by_specification(
        self,
        specification: Specification[T]
    ) -> Optional[T]:
        """Find first entity matching specification."""
        if not hasattr(self, 'session') or not hasattr(self, '_entity_class'):
            raise NotImplementedError(
                "SpecificationRepositoryMixin requires session and _entity_class"
            )

        filter_expr = specification.to_sqlalchemy_filter()

        query = self.session.query(self._entity_class)
        if filter_expr is not None:
            query = query.filter(filter_expr)

        entity = query.first()

        return self._entity_to_domain(entity) if entity else None

    def count_by_specification(self, specification: Specification[T]) -> int:
        """Count entities matching specification."""
        if not hasattr(self, 'session') or not hasattr(self, '_entity_class'):
            raise NotImplementedError(
                "SpecificationRepositoryMixin requires session and _entity_class"
            )

        filter_expr = specification.to_sqlalchemy_filter()

        query = self.session.query(self._entity_class)
        if filter_expr is not None:
            query = query.filter(filter_expr)

        return query.count()

    def exists_by_specification(self, specification: Specification[T]) -> bool:
        """Check if any entity matches specification."""
        return self.count_by_specification(specification) > 0

    def find_by_specification_paginated(
        self,
        specification: Specification[T],
        limit: int = 100,
        offset: int = 0
    ) -> List[T]:
        """Find entities matching specification with pagination."""
        if not hasattr(self, 'session') or not hasattr(self, '_entity_class'):
            raise NotImplementedError(
                "SpecificationRepositoryMixin requires session and _entity_class"
            )

        filter_expr = specification.to_sqlalchemy_filter()

        query = self.session.query(self._entity_class)
        if filter_expr is not None:
            query = query.filter(filter_expr)

        entities = query.limit(limit).offset(offset).all()

        return [self._entity_to_domain(e) for e in entities]


# In-Memory Repository Implementation

class InMemorySpecificationRepository(ISpecificationRepository[T], Generic[T]):
    """
    In-memory implementation of specification repository.

    Useful for testing and prototyping.

    Usage:
        repo = InMemorySpecificationRepository[Product]()
        repo.add(product1)
        repo.add(product2)

        spec = ProductInStockSpecification()
        in_stock = repo.find_by_specification(spec)
    """

    def __init__(self):
        self._items: List[T] = []

    def add(self, item: T) -> T:
        """Add an item to the repository."""
        self._items.append(item)
        return item

    def get_all(self) -> List[T]:
        """Get all items."""
        return self._items.copy()

    def clear(self) -> None:
        """Clear all items."""
        self._items.clear()

    def find_by_specification(self, specification: Specification[T]) -> List[T]:
        """Find items matching specification using in-memory filtering."""
        return [
            item for item in self._items
            if specification.is_satisfied_by(item)
        ]

    def find_one_by_specification(
        self,
        specification: Specification[T]
    ) -> Optional[T]:
        """Find first item matching specification."""
        for item in self._items:
            if specification.is_satisfied_by(item):
                return item
        return None

    def count_by_specification(self, specification: Specification[T]) -> int:
        """Count items matching specification."""
        return len(self.find_by_specification(specification))

    def exists_by_specification(self, specification: Specification[T]) -> bool:
        """Check if any item matches specification."""
        return self.find_one_by_specification(specification) is not None
