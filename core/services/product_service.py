# core/services/product_service.py

from typing import List, Optional, Callable, Any
from decimal import Decimal
import logging
from sqlalchemy.orm import Session

from core.interfaces.repository_interfaces import IProductRepository, IDepartmentRepository
from core.models.product import Product, Department
from infrastructure.persistence.utils import session_scope
from core.services.service_base import ServiceBase
from core.utils.validation import (
    validate_required_field,
    validate_positive_number,
    validate_unique_field,
    validate_exists
)

class ProductService(ServiceBase):
    """Service for product and department management."""
    
    def __init__(
        self,
        product_repo_factory: Callable[[Session], IProductRepository],
        department_repo_factory: Callable[[Session], IDepartmentRepository]
    ):
        """
        Initialize with repository factories.
        
        Args:
            product_repo_factory: Factory function to create product repository
            department_repo_factory: Factory function to create department repository
        """
        super().__init__()  # Initialize base class with default logger
        self.product_repo_factory = product_repo_factory
        self.department_repo_factory = department_repo_factory

    def _validate_product(self, session: Session, product: Product, is_update: bool = False, existing_product_id: Optional[int] = None):
        """Common validation logic for adding/updating products using centralized validation utilities."""
        # Validate required fields
        validate_required_field(product.code, "Code")
        validate_required_field(product.description, "Description")
        
        # Validate prices - must be positive and non-zero
        if product.sell_price is not None:
            validate_positive_number(product.sell_price, "Sell price")
            if product.sell_price == 0:
                raise ValueError("Sell price cannot be zero")
        
        if product.cost_price is not None:
            validate_positive_number(product.cost_price, "Cost price")
            if product.cost_price == 0:
                raise ValueError("Cost price cannot be zero")

        # Get repositories from factories
        dept_repo = self._get_repository(self.department_repo_factory, session)
        prod_repo = self._get_repository(self.product_repo_factory, session)

        # Validate department exists
        if product.department_id is not None:
            department = dept_repo.get_by_id(product.department_id)
            validate_exists(department is not None, "Department", product.department_id)

        # Validate product code uniqueness
        existing_by_code = prod_repo.get_by_code(product.code)
        if is_update:
            # For updates, check uniqueness excluding current product
            if existing_by_code and existing_by_code.id != existing_product_id:
                raise ValueError(f"Code '{product.code}' already exists for another record")
        else:
            # For new products, check if code exists
            validate_unique_field(
                existing_by_code is not None,
                "Code",
                product.code
            )

    def add_product(self, product_data: Product) -> Product:
        """Adds a new product after validation."""
        def _add_product(session, product_data):
            self._validate_product(session, product_data, is_update=False)
            
            # Get repository from factory
            prod_repo = self._get_repository(self.product_repo_factory, session)
            
            self.logger.info(f"Adding product with code: {product_data.code}")
            added_product = prod_repo.add(product_data)
            return added_product
            
        return self._with_session(_add_product, product_data)

    def update_product(self, product_update_data: Product) -> None:
        """Updates an existing product after validation."""
        def _update_product(session, product_update_data):
            if product_update_data.id is None:
                raise ValueError("Product ID must be provided for update.")

            # Get repository from factory
            prod_repo = self._get_repository(self.product_repo_factory, session)
            
            existing_product = prod_repo.get_by_id(product_update_data.id)
            if not existing_product:
                raise ValueError(f"Product with ID {product_update_data.id} not found")

            # Validate the incoming data, considering it's an update
            self._validate_product(session, product_update_data, is_update=True, existing_product_id=product_update_data.id)

            self.logger.info(f"Updating product with ID: {product_update_data.id}")
            return prod_repo.update(product_update_data)
            
        return self._with_session(_update_product, product_update_data)

    def delete_product(self, product_id: int) -> None:
        """Deletes a product if it doesn't have stock or doesn't use inventory."""
        def _delete_product(session, product_id):
            # Get repository from factory
            prod_repo = self._get_repository(self.product_repo_factory, session)
            
            product = prod_repo.get_by_id(product_id)
            if product:
                has_inventory = product.uses_inventory if hasattr(product, 'uses_inventory') else False
                quantity_in_stock = 0
                if hasattr(product, 'quantity_in_stock') and product.quantity_in_stock is not None:
                    quantity_in_stock = float(product.quantity_in_stock)
                    
                if has_inventory and quantity_in_stock > 0:
                    raise ValueError(f"Product '{product.code}' cannot be deleted because it has stock ({quantity_in_stock})")
                self.logger.info(f"Deleting product with ID: {product_id}")
                return prod_repo.delete(product_id)
            else:
                self.logger.warning(f"Attempted to delete non-existent product with ID: {product_id}")
                return None
                
        return self._with_session(_delete_product, product_id)

    def find_product(self, search_term: Optional[str] = None) -> List[Product]:
        """Finds products based on a search term or returns all if no term is provided."""
        def _find_product(session, search_term):
            # Get repository from factory
            prod_repo = self._get_repository(self.product_repo_factory, session)
            
            if search_term:
                self.logger.debug(f"Searching products with term: '{search_term}'")
                return prod_repo.search(search_term)
            else:
                self.logger.debug("Getting all products")
                return prod_repo.get_all()
                
        return self._with_session(_find_product, search_term)

    def get_all_products(self, department_id=None) -> List[Product]:
        """Gets all products, optionally filtered by department_id."""
        def _get_all_products(session, department_id):
            self.logger.debug(f"Getting all products via get_all_products, department_id={department_id}")
            
            # Get repository from factory
            prod_repo = self._get_repository(self.product_repo_factory, session)
            
            products = prod_repo.get_all()
            
            # Filter by department_id if provided
            if department_id is not None:
                products = [p for p in products if p.department_id == department_id]
                
            return products
            
        return self._with_session(_get_all_products, department_id)

    def get_product_by_code(self, code: str) -> Optional[Product]:
        """Gets a product by its code."""
        def _get_product_by_code(session, code):
            self.logger.debug(f"Getting product with code: {code}")
            
            # Get repository from factory
            prod_repo = self._get_repository(self.product_repo_factory, session)
            
            return prod_repo.get_by_code(code)
            
        return self._with_session(_get_product_by_code, code)

    def get_product_by_id(self, product_id: Any) -> Optional[Product]:
        """
        Gets a product by its ID.
        
        Args:
            product_id: The ID of the product (can be int or another type)
            
        Returns:
            Product object if found, None otherwise
        """
        def _get_product_by_id(session, product_id):
            self.logger.debug(f"Getting product with ID: {product_id}, type: {type(product_id)}")
            
            # Get repository from factory
            prod_repo = self._get_repository(self.product_repo_factory, session)
            
            product = prod_repo.get_by_id(product_id)
            if not product:
                self.logger.debug(f"Product with ID {product_id} not found")
            return product
            
        return self._with_session(_get_product_by_id, product_id)

    def _validate_department(self, session: Session, department: Department, is_update: bool = False):
        """Common validation for department add/update."""
        if not department.name:
            raise ValueError("Name cannot be empty")
        
        # Get repository from factory
        dept_repo = self._get_repository(self.department_repo_factory, session)
        
        # Check name uniqueness
        existing = dept_repo.get_by_name(department.name)
        if existing:
            # Check if the found department is the same one being updated
            if not (is_update and existing.id == department.id):
                 raise ValueError(f"Department name '{department.name}' already exists")

    def add_department(self, department_data: Department) -> Department:
        """Adds a new department after validation."""
        def _add_department(session, department_data):
            self._validate_department(session, department_data, is_update=False)
            
            # Get repository from factory
            dept_repo = self._get_repository(self.department_repo_factory, session)
            
            self.logger.info(f"Adding department with name: {department_data.name}")
            added_department = dept_repo.add(department_data)
            return added_department
            
        return self._with_session(_add_department, department_data)

    def get_all_departments(self) -> List[Department]:
        """Gets all departments."""
        def _get_all_departments(session):
            self.logger.debug("Getting all departments")
            
            # Get repository from factory
            dept_repo = self._get_repository(self.department_repo_factory, session)
            
            return dept_repo.get_all()
            
        return self._with_session(_get_all_departments)

    def delete_department(self, department_id: int) -> None:
        """Deletes a department if it's not in use by any products."""
        def _delete_department(session, department_id):
            # Get repositories from factories
            dept_repo = self._get_repository(self.department_repo_factory, session)
            prod_repo = self._get_repository(self.product_repo_factory, session)

            department = dept_repo.get_by_id(department_id)
            if not department:
                self.logger.warning(f"Attempted to delete non-existent department with ID: {department_id}")
                return None

            # Check if department is in use
            products_in_dept = prod_repo.get_by_department_id(department_id)
            if products_in_dept:
                raise ValueError(f"Department '{department.name}' cannot be deleted, it is used by {len(products_in_dept)} product(s).")

            self.logger.info(f"Deleting department with ID: {department_id}")
            return dept_repo.delete(department_id)
            
        return self._with_session(_delete_department, department_id)

    def update_department(self, department_data: Department) -> Department:
        """Updates an existing department after validation."""
        def _update_department(session, department_data):
            if department_data.id is None:
                raise ValueError("Department ID must be provided for update.")
                
            # Get repository from factory
            dept_repo = self._get_repository(self.department_repo_factory, session)
            
            existing_department = dept_repo.get_by_id(department_data.id)
            if not existing_department:
                raise ValueError(f"Department with ID {department_data.id} not found")
                
            # Validate the incoming data, considering it's an update
            self._validate_department(session, department_data, is_update=True)
            
            self.logger.info(f"Updating department with ID: {department_data.id}")
            updated_department = dept_repo.update(department_data)
            return updated_department
            
        return self._with_session(_update_department, department_data)

    def update_prices_by_percentage(self, percentage: Decimal, department_id: Optional[int] = None) -> int:
        """
        Updates product prices by a given percentage.
        If department_id is provided, only updates products in that department.
        Returns the number of products updated.
        """
        if not isinstance(percentage, Decimal) or percentage <= Decimal("-100") :
            raise ValueError("Percentage must be a number greater than -100.")

        def _update_prices(session: Session, percentage: Decimal, department_id: Optional[int]) -> int:
            prod_repo = self._get_repository(self.product_repo_factory, session)
            
            products_to_update: List[Product]
            if department_id is not None:
                self.logger.info(f"Fetching products for department ID: {department_id} to update prices by {percentage}%.")
                products_to_update = prod_repo.get_by_department_id(department_id)
            else:
                self.logger.info(f"Fetching all products to update prices by {percentage}%.")
                products_to_update = prod_repo.get_all()

            if not products_to_update:
                self.logger.info("No products found to update.")
                return 0

            updated_count = 0
            for product in products_to_update:
                if product.sell_price is not None:
                    original_price = product.sell_price
                    increase_amount = original_price * (percentage / Decimal("100"))
                    new_price = original_price + increase_amount
                    # Ensure price is not negative, though percentage validation should prevent this for positive prices
                    product.sell_price = max(Decimal("0.00"), new_price.quantize(Decimal("0.01"))) 
                    
                    # Update cost price proportionally if it exists
                    if product.cost_price is not None:
                        original_cost_price = product.cost_price
                        cost_increase_amount = original_cost_price * (percentage / Decimal("100"))
                        new_cost_price = original_cost_price + cost_increase_amount
                        product.cost_price = max(Decimal("0.00"), new_cost_price.quantize(Decimal("0.01")))

                    prod_repo.update(product) # Assuming update handles individual product persistence
                    self.logger.debug(f"Updated product ID {product.id} ('{product.code}'): sell_price from {original_price} to {product.sell_price}, cost_price updated proportionally.")
                    updated_count += 1
            
            self.logger.info(f"Successfully updated prices for {updated_count} products by {percentage}%.")
            return updated_count

        return self._with_session(_update_prices, percentage, department_id)
