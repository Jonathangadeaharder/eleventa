# core/services/product_service.py

from typing import List, Optional, Callable, Any
from decimal import Decimal
import logging

from core.interfaces.repository_interfaces import IProductRepository, IDepartmentRepository
from core.models.product import Product, Department
from infrastructure.persistence.utils import session_scope
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
# Configure basic logging if not already done elsewhere
logging.basicConfig(level=logging.DEBUG)

RepositoryFactory = Callable[[Session], Any]

class ProductService:
    def __init__(
        self,
        product_repo_factory: RepositoryFactory,
        department_repo_factory: RepositoryFactory,
    ):
        self.product_repo_factory = product_repo_factory
        self.department_repo_factory = department_repo_factory
        # Add logging to check the type and content of factories
        logger.debug(f"ProductService initialized with:")
        logger.debug(f"  product_repo_factory type: {type(product_repo_factory)}, value: {product_repo_factory}")
        logger.debug(f"  department_repo_factory type: {type(department_repo_factory)}, value: {department_repo_factory}")

    def _validate_product(self, session: Session, product: Product, is_update: bool = False, existing_product_id: Optional[int] = None):
        """Common validation logic for adding/updating products."""
        if not product.code:
            raise ValueError("Código es requerido")
        if not product.description:
            raise ValueError("Descripción es requerida")
        if product.sell_price is not None and product.sell_price < 0:
            raise ValueError("Precio de venta debe ser positivo")
        if product.cost_price is not None and product.cost_price < 0:
            raise ValueError("Precio de costo debe ser positivo")

        # Instantiate repos with session
        dept_repo = self.department_repo_factory(session)
        prod_repo = self.product_repo_factory(session)

        # Check department existence
        if product.department_id is not None:
            department = dept_repo.get_by_id(product.department_id)
            if not department:
                raise ValueError(f"Departamento con ID {product.department_id} no existe")

        # Check code uniqueness
        existing_by_code = prod_repo.get_by_code(product.code)
        if existing_by_code:
            if is_update and existing_by_code.id == existing_product_id:
                pass # It's okay if the code belongs to the product being updated
            else:
                error_suffix = " para otro producto" if is_update else ""
                raise ValueError(f"Código '{product.code}' ya existe{error_suffix}")

    def add_product(self, product_data: Product) -> Product:
        """Adds a new product after validation."""
        with session_scope() as session:
            self._validate_product(session, product_data, is_update=False)
            prod_repo = self.product_repo_factory(session)
            logger.info(f"Adding product with code: {product_data.code}")
            added_product = prod_repo.add(product_data)
            return added_product

    def update_product(self, product_update_data: Product) -> None:
        """Updates an existing product after validation."""
        if product_update_data.id is None:
            raise ValueError("Product ID must be provided for update.")

        with session_scope() as session:
            prod_repo = self.product_repo_factory(session)
            existing_product = prod_repo.get_by_id(product_update_data.id)
            if not existing_product:
                raise ValueError(f"Producto con ID {product_update_data.id} no encontrado")

            # Validate the incoming data, considering it's an update
            self._validate_product(session, product_update_data, is_update=True, existing_product_id=product_update_data.id)

            logger.info(f"Updating product with ID: {product_update_data.id}")
            prod_repo.update(product_update_data)

    def delete_product(self, product_id: int) -> None:
        """Deletes a product if it doesn't have stock or doesn't use inventory."""
        with session_scope() as session:
            prod_repo = self.product_repo_factory(session)
            product = prod_repo.get_by_id(product_id)
            if product:
                has_inventory = product.uses_inventory if hasattr(product, 'uses_inventory') else False
                quantity_in_stock = 0
                if hasattr(product, 'quantity_in_stock') and isinstance(product.quantity_in_stock, (int, float)):
                    quantity_in_stock = product.quantity_in_stock
                    
                if has_inventory and quantity_in_stock > 0:
                    raise ValueError(f"Producto '{product.code}' no puede ser eliminado porque tiene stock ({quantity_in_stock})")
                logger.info(f"Deleting product with ID: {product_id}")
                prod_repo.delete(product_id)
            else:
                logger.warning(f"Attempted to delete non-existent product with ID: {product_id}")

    def find_product(self, search_term: Optional[str] = None) -> List[Product]:
        """Finds products based on a search term or returns all if no term is provided."""
        with session_scope() as session:
            prod_repo = self.product_repo_factory(session)
            if search_term:
                logger.debug(f"Searching products with term: '{search_term}'")
                return prod_repo.search(search_term)
            else:
                logger.debug("Getting all products")
                return prod_repo.get_all()

    def get_all_products(self, department_id=None) -> List[Product]:
         """Gets all products, optionally filtered by department_id."""
         logger.debug(f"Getting all products via get_all_products, department_id={department_id}")
         with session_scope() as session:
             prod_repo = self.product_repo_factory(session)
             products = prod_repo.get_all()
             
             # Filter by department_id if provided
             if department_id is not None:
                 products = [p for p in products if p.department_id == department_id]
                 
             return products

    def _validate_department(self, session: Session, department: Department, is_update: bool = False):
        """Common validation for department add/update."""
        if not department.name:
            raise ValueError("Nombre de departamento es requerido")
        dept_repo = self.department_repo_factory(session)
        existing = dept_repo.get_by_name(department.name)
        if existing:
            # Check if the found department is the same one being updated
            if not (is_update and existing.id == department.id):
                 raise ValueError(f"Departamento '{department.name}' ya existe")

    def add_department(self, department_data: Department) -> Department:
        """Adds a new department after validation."""
        with session_scope() as session:
            self._validate_department(session, department_data, is_update=False)
            dept_repo = self.department_repo_factory(session)
            logger.info(f"Adding department with name: {department_data.name}")
            added_department = dept_repo.add(department_data)
            return added_department

    def get_all_departments(self) -> List[Department]:
         """Gets all departments."""
         logger.debug("Entering get_all_departments")
         logger.debug(f"  Using department_repo_factory: {self.department_repo_factory}") # Log factory again before use
         with session_scope() as session:
             logger.debug("  Session scope created successfully.")
             try:
                 # Log just before instantiation
                 logger.debug("  Attempting to instantiate SqliteDepartmentRepository...")
                 dept_repo = self.department_repo_factory(session)
                 logger.debug(f"  SqliteDepartmentRepository instantiated: {type(dept_repo)}")
                 return dept_repo.get_all()
             except Exception as e:
                 logger.error(f"  Error instantiating or using dept_repo: {e}", exc_info=True)
                 raise # Re-raise the exception

    def delete_department(self, department_id: int) -> None:
        """Deletes a department if it's not in use by any products."""
        with session_scope() as session:
            dept_repo = self.department_repo_factory(session)
            prod_repo = self.product_repo_factory(session)

            department = dept_repo.get_by_id(department_id)
            if not department:
                 logger.warning(f"Attempted to delete non-existent department with ID: {department_id}")
                 return

            # Check if department is in use
            products_in_dept = prod_repo.search(f"department_id:{department_id}")
            if products_in_dept:
                 raise ValueError(f"Departamento '{department.name}' no puede ser eliminado, está en uso por productos.")

            logger.info(f"Deleting department with ID: {department_id}")
            dept_repo.delete(department_id)

    # Additional helper methods if needed 