# core/services/product_service.py

from typing import List, Optional, Any
from decimal import Decimal
from uuid import UUID

from core.models.product import Product, Department
from infrastructure.persistence.unit_of_work import UnitOfWork, unit_of_work
from core.services.service_base import ServiceBase
from core.utils.validation import (
    validate_required_field,
    validate_positive_number,
    validate_unique_field,
    validate_exists,
)
from core.events.product_events import (
    ProductCreated,
    ProductUpdated,
    ProductPriceChanged,
    ProductDeleted,
)


class ProductService(ServiceBase):
    """Service for product and department management using Unit of Work pattern."""

    def __init__(self):
        """
        Initialize the service.
        """
        super().__init__()  # Initialize base class with default logger

    def _validate_product(
        self,
        uow: UnitOfWork,
        product: Product,
        is_update: bool = False,
        existing_product_id: Optional[int] = None,
    ):
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

        # Validate department exists
        if product.department_id is not None:
            department = uow.departments.get_by_id(product.department_id)
            validate_exists(department is not None, "Department", product.department_id)

        # Validate product code uniqueness
        existing_by_code = uow.products.get_by_code(product.code)
        if is_update:
            # For updates, check uniqueness excluding current product
            if existing_by_code and existing_by_code.id != existing_product_id:
                raise ValueError(
                    f"Code '{product.code}' already exists for another record"
                )
        else:
            # For new products, check if code exists
            validate_unique_field(existing_by_code is not None, "Code", product.code)

    def add_product(self, product_data: Product, user_id: Optional[UUID] = None) -> Product:
        """
        Adds a new product after validation.

        Args:
            product_data: The product to add
            user_id: The ID of the user performing the action (for event tracking)

        Returns:
            The created product

        Raises:
            ValueError: If validation fails
        """
        with unit_of_work() as uow:
            self._validate_product(uow, product_data, is_update=False)

            self.logger.info(f"Adding product with code: {product_data.code}")
            added_product = uow.products.add(product_data)

            # Publish domain event
            if added_product and added_product.id:
                event = ProductCreated(
                    product_id=added_product.id,
                    code=added_product.code,
                    description=added_product.description,
                    sell_price=added_product.sell_price,
                    department_id=added_product.department_id,
                    user_id=user_id or UUID(int=0)  # Fallback if no user provided
                )
                uow.add_event(event)
                self.logger.debug(f"Published ProductCreated event for {added_product.code}")

            return added_product

    def update_product(self, product_update_data: Product, user_id: Optional[UUID] = None) -> None:
        """
        Updates an existing product after validation.

        Args:
            product_update_data: The updated product data
            user_id: The ID of the user performing the action (for event tracking)

        Raises:
            ValueError: If validation fails or product not found
        """
        with unit_of_work() as uow:
            if product_update_data.id is None:
                raise ValueError("Product ID must be provided for update.")

            existing_product = uow.products.get_by_id(product_update_data.id)
            if not existing_product:
                raise ValueError(f"Product with ID {product_update_data.id} not found")

            # Detect price change before update
            price_changed = (
                existing_product.sell_price != product_update_data.sell_price
            )
            old_price = existing_product.sell_price if price_changed else None

            # Validate the incoming data, considering it's an update
            self._validate_product(
                uow,
                product_update_data,
                is_update=True,
                existing_product_id=product_update_data.id,
            )

            self.logger.info(f"Updating product with ID: {product_update_data.id}")
            updated_product = uow.products.update(product_update_data)

            # Publish events
            if updated_product:
                # Specific event for price changes
                if price_changed and old_price is not None:
                    event = ProductPriceChanged(
                        product_id=updated_product.id,
                        code=updated_product.code,
                        old_price=old_price,
                        new_price=updated_product.sell_price,
                        price_change_percent=Decimal('0'),  # Calculated in __post_init__
                        user_id=user_id or UUID(int=0)
                    )
                    uow.add_event(event)
                    self.logger.debug(
                        f"Published ProductPriceChanged event: "
                        f"{updated_product.code} from {old_price} to {updated_product.sell_price}"
                    )

                # General update event
                event = ProductUpdated(
                    product_id=updated_product.id,
                    updated_fields={'code': updated_product.code},  # Could track more fields
                    user_id=user_id or UUID(int=0)
                )
                uow.add_event(event)
                self.logger.debug(f"Published ProductUpdated event for {updated_product.code}")

            return updated_product

    def delete_product(self, product_id: int, user_id: Optional[UUID] = None) -> None:
        """
        Deletes a product. Raises ValueError if it has stock.

        Args:
            product_id: The ID of the product to delete
            user_id: The ID of the user performing the action (for event tracking)

        Raises:
            ValueError: If product has stock and cannot be deleted
        """
        with unit_of_work() as uow:
            product = uow.products.get_by_id(product_id)
            if product:
                has_inventory = (
                    product.uses_inventory
                    if hasattr(product, "uses_inventory")
                    else False
                )
                quantity_in_stock = 0
                if (
                    hasattr(product, "quantity_in_stock")
                    and product.quantity_in_stock is not None
                ):
                    quantity_in_stock = float(product.quantity_in_stock)

                if has_inventory and quantity_in_stock > 0:
                    raise ValueError(
                        f"Product '{product.code}' cannot be deleted because it has stock"
                    )

                # Store info before deletion for event
                product_code = product.code
                product_description = product.description

                self.logger.info(f"Deleting product with ID: {product_id}")
                result = uow.products.delete(product_id)

                # Publish event
                if result:
                    event = ProductDeleted(
                        product_id=product.id,
                        code=product_code,
                        description=product_description,
                        user_id=user_id or UUID(int=0)
                    )
                    uow.add_event(event)
                    self.logger.debug(f"Published ProductDeleted event for {product_code}")

                return result
            else:
                self.logger.warning(
                    f"Attempted to delete non-existent product with ID: {product_id}"
                )
                return None

    def find_product(self, search_term: Optional[str] = None) -> List[Product]:
        """Finds products based on a search term or returns all if no term is provided."""
        with unit_of_work() as uow:
            if search_term:
                self.logger.debug(f"Searching products with term: '{search_term}'")
                return uow.products.search(search_term)
            else:
                self.logger.debug("Getting all products")
                return uow.products.get_all()

    def get_all_products(self, department_id=None) -> List[Product]:
        """Gets all products, optionally filtered by department_id."""
        with unit_of_work() as uow:
            self.logger.debug(
                f"Getting all products via get_all_products, department_id={department_id}"
            )

            products = uow.products.get_all()

            # Filter by department_id if provided
            if department_id is not None:
                products = [p for p in products if p.department_id == department_id]

            return products

    def get_product_by_code(self, code: str) -> Optional[Product]:
        """Gets a product by its code."""
        with unit_of_work() as uow:
            self.logger.debug(f"Getting product with code: {code}")
            return uow.products.get_by_code(code)

    def get_product_by_id(self, product_id: Any) -> Optional[Product]:
        """
        Gets a product by its ID.

        Args:
            product_id: The ID of the product (can be int or another type)

        Returns:
            Product object if found, None otherwise
        """
        with unit_of_work() as uow:
            self.logger.debug(
                f"Getting product with ID: {product_id}, type: {type(product_id)}"
            )

            product = uow.products.get_by_id(product_id)
            if not product:
                self.logger.debug(f"Product with ID {product_id} not found")
            return product

    def _validate_department(
        self, uow: UnitOfWork, department: Department, is_update: bool = False
    ):
        """Common validation for department add/update."""
        if not department.name:
            raise ValueError("Name cannot be empty")

        # Check name uniqueness
        existing = uow.departments.get_by_name(department.name)
        if existing:
            # Check if the found department is the same one being updated
            if not (is_update and existing.id == department.id):
                raise ValueError(f"Department name '{department.name}' already exists")

    def add_department(self, department_data: Department) -> Department:
        """Adds a new department after validation."""
        with unit_of_work() as uow:
            self._validate_department(uow, department_data, is_update=False)

            self.logger.info(f"Adding department with name: {department_data.name}")
            added_department = uow.departments.add(department_data)
            return added_department

    def get_all_departments(self) -> List[Department]:
        """Gets all departments."""
        with unit_of_work() as uow:
            self.logger.debug("Getting all departments")
            return uow.departments.get_all()

    def delete_department(self, department_id: int) -> None:
        """Deletes a department if it's not in use by any products."""
        with unit_of_work() as uow:
            department = uow.departments.get_by_id(department_id)
            if not department:
                self.logger.warning(
                    f"Attempted to delete non-existent department with ID: {department_id}"
                )
                return None

            # Check if department is in use
            products_in_dept = uow.products.get_by_department_id(department_id)
            if products_in_dept:
                raise ValueError(
                    f"Department '{department.name}' cannot be deleted, it is used by {len(products_in_dept)} product(s)."
                )

            self.logger.info(f"Deleting department with ID: {department_id}")
            return uow.departments.delete(department_id)

    def update_department(self, department_data: Department) -> Department:
        """Updates an existing department after validation."""
        with unit_of_work() as uow:
            if department_data.id is None:
                raise ValueError("Department ID must be provided for update.")

            existing_department = uow.departments.get_by_id(department_data.id)
            if not existing_department:
                raise ValueError(f"Department with ID {department_data.id} not found")

            # Validate the incoming data, considering it's an update
            self._validate_department(uow, department_data, is_update=True)

            self.logger.info(f"Updating department with ID: {department_data.id}")
            updated_department = uow.departments.update(department_data)
            return updated_department

    def update_prices_by_percentage(
        self,
        percentage: Decimal,
        department_id: Optional[int] = None,
        user_id: Optional[UUID] = None
    ) -> int:
        """
        Updates product prices by a given percentage.
        If department_id is provided, only updates products in that department.
        Returns the number of products updated.

        Args:
            percentage: Percentage to increase/decrease prices
            department_id: Optional department filter
            user_id: The ID of the user performing the action (for event tracking)

        Returns:
            Number of products updated

        Raises:
            ValueError: If percentage is invalid
        """
        if not isinstance(percentage, Decimal) or percentage <= Decimal("-100"):
            raise ValueError("Percentage must be a number greater than -100.")

        with unit_of_work() as uow:
            products_to_update: List[Product]
            if department_id is not None:
                self.logger.info(
                    f"Fetching products for department ID: {department_id} to update prices by {percentage}%."
                )
                products_to_update = uow.products.get_by_department_id(department_id)
            else:
                self.logger.info(
                    f"Fetching all products to update prices by {percentage}%."
                )
                products_to_update = uow.products.get_all()

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
                    product.sell_price = max(
                        Decimal("0.00"), new_price.quantize(Decimal("0.01"))
                    )

                    # Update cost price proportionally if it exists
                    if product.cost_price is not None:
                        original_cost_price = product.cost_price
                        cost_increase_amount = original_cost_price * (
                            percentage / Decimal("100")
                        )
                        new_cost_price = original_cost_price + cost_increase_amount
                        product.cost_price = max(
                            Decimal("0.00"), new_cost_price.quantize(Decimal("0.01"))
                        )

                    uow.products.update(
                        product
                    )  # Assuming update handles individual product persistence

                    # Publish price change event
                    event = ProductPriceChanged(
                        product_id=product.id,
                        code=product.code,
                        old_price=original_price,
                        new_price=product.sell_price,
                        price_change_percent=Decimal('0'),  # Calculated in __post_init__
                        user_id=user_id or UUID(int=0)
                    )
                    uow.add_event(event)

                    self.logger.debug(
                        f"Updated product ID {product.id} ('{product.code}'): sell_price from {original_price} to {product.sell_price}, cost_price updated proportionally."
                    )
                    updated_count += 1

            self.logger.info(
                f"Successfully updated prices for {updated_count} products by {percentage}%. Published {updated_count} events."
            )
            return updated_count

    def get_next_available_id(self) -> int:
        """Gets the next available ID for a new product."""
        with unit_of_work() as uow:
            products = uow.products.get_all()
            if not products:
                return 1

            # Get all existing IDs and find the next available one
            existing_ids = {p.id for p in products if p.id is not None}
            if not existing_ids:
                return 1

            # Find the first gap in the sequence, or return max + 1
            max_id = max(existing_ids)
            for i in range(1, max_id + 2):
                if i not in existing_ids:
                    return i

            return max_id + 1
