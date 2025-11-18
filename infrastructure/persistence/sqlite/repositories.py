import sys
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
import logging

from sqlalchemy import (
    select,
    func,
    and_,
    or_,
    desc,
    asc,
    text,
)
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

# Note: sys.path manipulation is a workaround for import issues
# Consider fixing the project structure instead
project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ruff: noqa: E402 - imports below are after sys.path manipulation (intentional)
from core.interfaces.repository_interfaces import (
    IDepartmentRepository,
    IProductRepository,
    IInventoryRepository,
    ISaleRepository,
    ICustomerRepository,
    ICreditPaymentRepository,
    IUserRepository,
    IInvoiceRepository,
    IUnitRepository,
)
from core.models.product import Department, Product
from core.models.inventory import InventoryMovement
from core.models.sale import Sale
from core.models.customer import Customer
from core.models.credit_payment import CreditPayment
from core.models.user import User
from core.models.invoice import Invoice
from core.models.cash_drawer import CashDrawerEntry, CashDrawerEntryType
from core.models.unit import Unit

# Import specific ORM classes directly
from infrastructure.persistence.sqlite.models_mapping import (
    UserOrm,
    ProductOrm,
    DepartmentOrm,
    CustomerOrm,
    SaleOrm,
    SaleItemOrm,
    InventoryMovementOrm,
    InvoiceOrm,
    CashDrawerEntryOrm,
    CreditPaymentOrm,
    UnitOrm,
)


from infrastructure.persistence.sqlite.cash_drawer_repository import (
    SQLiteCashDrawerRepository,
)
from infrastructure.persistence.mappers import ModelMapper

import bcrypt

# All ORM-to-Domain mapping functions have been centralized in infrastructure.persistence.mappers.ModelMapper
# This provides better maintainability and consistency across the codebase.

# --- Repository Implementation ---


class SqliteDepartmentRepository(IDepartmentRepository):
    """SQLite implementation of the department repository interface."""

    def __init__(self, session: Session):
        """Initializes the repository with a database session."""
        if not isinstance(session, Session):
            raise TypeError("Session must be a SQLAlchemy Session object")
        self.session = session

    def add(self, department: Department) -> Department:
        """Adds a new department to the database."""
        # Check for existing name
        existing = self.get_by_name(department.name)
        if existing:
            raise ValueError(f"Department name '{department.name}' already exists.")

        try:
            # Map domain model to ORM model
            department_orm = DepartmentOrm(
                name=department.name,
                # description=department.description # Add if description is in ORM
            )
            # Add ORM model to session
            self.session.add(department_orm)
            self.session.flush()  # Flush to get the ID assigned by the database
            self.session.refresh(department_orm)
            # Map the ORM model (with ID) back to domain model and return
            return ModelMapper.department_orm_to_domain(department_orm)
        except IntegrityError as e:
            self.session.rollback()
            # Log error or handle specific constraint violations
            logging.error(f"Database integrity error adding department: {e}")
            raise ValueError(f"Could not add department: {e}")
        except Exception as e:
            self.session.rollback()
            logging.error(f"Unexpected error adding department: {e}")
            raise

    def get_by_id(
        self, department_id: int
    ) -> Optional[Department]:  # Changed type hint to int
        """Retrieves a department by its ID."""
        department_orm = self.session.get(DepartmentOrm, department_id)
        return ModelMapper.department_orm_to_domain(department_orm)

    def get_by_name(self, name: str) -> Optional[Department]:
        """Retrieves a department by its name."""
        stmt = select(DepartmentOrm).where(DepartmentOrm.name == name)
        department_orm = self.session.scalars(stmt).first()
        return ModelMapper.department_orm_to_domain(department_orm)

    def get_all(self) -> List[Department]:
        """Retrieves all departments, ordered by name."""
        stmt = select(DepartmentOrm).order_by(DepartmentOrm.name)
        results_orm = self.session.scalars(stmt).all()
        return [ModelMapper.department_orm_to_domain(dept) for dept in results_orm]

    def update(self, department: Department) -> Department:
        """Updates an existing department."""
        if department.id is None:
            raise ValueError("Department ID is required for update.")

        # Check for name collision if name is being changed
        existing_by_name = self.get_by_name(department.name)
        if existing_by_name and existing_by_name.id != department.id:
            raise ValueError(
                f"Another department with name '{department.name}' already exists."
            )

        department_orm = self.session.get(DepartmentOrm, department.id)
        if not department_orm:
            raise ValueError(f"Department with ID {department.id} not found.")

        try:
            # Update ORM attributes from domain model
            department_orm.name = department.name
            # department_orm.description = department.description # Add if description is in ORM

            self.session.flush()
            self.session.refresh(department_orm)
            return ModelMapper.department_orm_to_domain(department_orm)
        except IntegrityError as e:
            self.session.rollback()
            logging.error(
                f"Database integrity error updating department {department.id}: {e}"
            )
            raise ValueError(f"Could not update department: {e}")
        except Exception as e:
            self.session.rollback()
            logging.error(f"Unexpected error updating department {department.id}: {e}")
            raise

    def delete(self, department_id: int) -> bool:  # Changed type hint to int
        """Deletes a department by its ID."""
        department_orm = self.session.get(DepartmentOrm, department_id)
        if not department_orm:
            raise ValueError(f"Department with ID {department_id} not found")

        try:
            # Check if department is used by products (optional constraint)
            product_count = self.session.scalar(
                select(func.count(ProductOrm.id)).where(
                    ProductOrm.department_id == department_id
                )
            )
            if product_count > 0:
                raise ValueError(
                    f"Departamento {department_id} no puede ser eliminado, está en uso por {product_count} productos."
                )

            self.session.delete(department_orm)
            self.session.flush()
            return True
        except IntegrityError as e:
            self.session.rollback()
            # This might happen if there's a DB-level constraint not checked above
            logging.error(f"Integrity error deleting department {department_id}: {e}")
            raise ValueError("Cannot delete department. It might be in use.")
        except Exception as e:
            self.session.rollback()
            logging.error(f"Unexpected error deleting department {department_id}: {e}")
            raise


# Add other repository implementations (e.g., SqliteProductRepository) below

# --- Product Repository Implementation ---


class SqliteProductRepository(IProductRepository):
    """SQLite implementation of the product repository interface."""

    def __init__(self, session: Session):
        self.session = session

    def _create_product_orm(self, product: Product) -> ProductOrm:
        """Helper to map Product domain model to ProductOrm."""
        # Ensure department exists if ID is provided
        if product.department_id and not self.session.get(
            DepartmentOrm, product.department_id
        ):
            raise ValueError(f"Department with ID {product.department_id} not found.")

        # Get all data from the product model
        data = product.model_dump(
            exclude={"id", "department"}
        )  # Use model_dump for Pydantic v2+

        # Filter out fields that don't exist in the ProductOrm model
        # Only include fields that are in the ProductOrm model
        orm_fields = {
            "code",
            "description",
            "cost_price",
            "sell_price",
            "wholesale_price",
            "special_price",
            "department_id",
            "unit",
            "uses_inventory",
            "quantity_in_stock",
            "min_stock",
            "max_stock",
            "last_updated",
            "notes",
            "is_active",
        }

        # Filter the data to only include fields that exist in the ORM
        orm_data = {k: v for k, v in data.items() if k in orm_fields}

        return ProductOrm(**orm_data)

    def add(self, product: Product) -> Product:
        """Adds a new product to the database."""
        # Check for existing code
        existing = self.get_by_code(product.code)
        if existing:
            raise ValueError(f"Product code '{product.code}' already exists.")

        try:
            product_orm = self._create_product_orm(product)
            self.session.add(product_orm)
            self.session.flush()
            self.session.refresh(
                product_orm, attribute_names=["id", "department"]
            )  # Refresh to get ID and potentially loaded department
            return ModelMapper.product_orm_to_domain(product_orm)
        except IntegrityError as e:
            self.session.rollback()
            logging.error(f"Database integrity error adding product: {e}")
            raise ValueError(f"Could not add product: {e}")
        except Exception as e:
            self.session.rollback()
            logging.error(f"Unexpected error adding product: {e}")
            raise

    def get_by_id(self, product_id: int) -> Optional[Product]:  # ID is int
        """Retrieves a product by its ID, eagerly loading the department."""
        # Use joinedload to eager load department
        stmt = (
            select(ProductOrm)
            .options(joinedload(ProductOrm.department))
            .where(ProductOrm.id == product_id)
        )
        product_orm = self.session.scalars(stmt).first()
        return ModelMapper.product_orm_to_domain(product_orm)

    def get_by_code(self, code: str) -> Optional[Product]:
        """Retrieves a product by its code, eagerly loading the department."""
        stmt = (
            select(ProductOrm)
            .options(joinedload(ProductOrm.department))
            .where(ProductOrm.code == code)
        )
        product_orm = self.session.scalars(stmt).first()
        # Check if product is found
        if product_orm is None:
            return None

        # Map ORM to domain model
        return ModelMapper.product_orm_to_domain(product_orm)

    def get_all(
        self,
        filter_params: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        sort_params: Optional[Dict[str, Any]] = None,
        pagination_params: Optional[Dict[str, Any]] = None,
    ) -> List[Product]:
        """Retrieves all products with optional filtering, sorting, and pagination."""
        stmt = select(ProductOrm).options(joinedload(ProductOrm.department))

        # Filtering (example: filter by active status)
        if filter_params and "is_active" in filter_params:
            stmt = stmt.where(ProductOrm.is_active == filter_params["is_active"])
        # Add more filters as needed based on filter_params

        # Sorting
        if sort_params:
            sort_by = sort_params.get("sort_by", "description")
            sort_column = getattr(ProductOrm, sort_by, None)
            if sort_column:
                if sort_params.get("sort_order", "asc") == "desc":
                    stmt = stmt.order_by(desc(sort_column))
                else:
                    stmt = stmt.order_by(asc(sort_column))
        elif sort_by:
            sort_column = getattr(ProductOrm, sort_by, None)
            if sort_column:
                if sort_params and sort_params.get("order", "asc") == "desc":
                    stmt = stmt.order_by(desc(sort_column))
                else:
                    stmt = stmt.order_by(asc(sort_column))
        else:
            # Default sort
            stmt = stmt.order_by(ProductOrm.description)

        # Pagination
        if pagination_params:
            page = pagination_params.get("page", 1)
            page_size = pagination_params.get("page_size", 10)  # Default page size
            offset = (page - 1) * page_size
            limit = page_size

        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        results_orm = self.session.scalars(stmt).all()
        return [ModelMapper.product_orm_to_domain(prod) for prod in results_orm]

    def get_by_department_id(self, department_id: int) -> List[Product]:
        """Retrieves all products for a specific department."""
        stmt = (
            select(ProductOrm)
            .where(ProductOrm.department_id == department_id)
            .order_by(ProductOrm.description)
        )
        results_orm = self.session.scalars(stmt).all()
        # Map ORM objects to domain models
        return [ModelMapper.product_orm_to_domain(prod) for prod in results_orm]

    def update(self, product: Product) -> Product:
        """Updates an existing product."""
        if product.id is None:
            raise ValueError("Product ID is required for update.")

        # Check for code collision if code is being changed
        if product.code:
            existing_by_code = self.get_by_code(product.code)
            if existing_by_code and existing_by_code.id != product.id:
                raise ValueError(
                    f"Another product with code '{product.code}' already exists."
                )

        product_orm = self.session.get(ProductOrm, product.id)
        if not product_orm:
            raise ValueError(f"Product with ID {product.id} not found.")

        # Ensure department exists if ID is provided and changing
        if (
            product.department_id is not None
            and product.department_id != product_orm.department_id
        ):
            if not self.session.get(DepartmentOrm, product.department_id):
                raise ValueError(
                    f"Department with ID {product.department_id} not found."
                )

        try:
            # Get all data from the product model
            data = product.model_dump(exclude={"id", "department"})

            # Filter out fields that don't exist in the ProductOrm model
            # Only include fields that are in the ProductOrm model
            orm_fields = {
                "code",
                "description",
                "cost_price",
                "sell_price",
                "wholesale_price",
                "special_price",
                "department_id",
                "unit",
                "uses_inventory",
                "quantity_in_stock",
                "min_stock",
                "max_stock",
                "last_updated",
                "notes",
                "is_active",
            }

            # Filter the data to only include fields that exist in the ORM
            filtered_data = {k: v for k, v in data.items() if k in orm_fields}

            # Update ORM attributes from domain model
            for key, value in filtered_data.items():
                setattr(product_orm, key, value)

            product_orm.last_updated = datetime.now()  # Explicitly set last_updated

            self.session.flush()
            self.session.refresh(
                product_orm, attribute_names=["department"]
            )  # Refresh to get loaded department
            return ModelMapper.product_orm_to_domain(product_orm)
        except IntegrityError as e:
            self.session.rollback()
            logging.error(
                f"Database integrity error updating product {product.id}: {e}"
            )
            raise ValueError(f"Could not update product: {e}")
        except Exception as e:
            self.session.rollback()
            logging.error(f"Unexpected error updating product {product.id}: {e}")
            raise

    def delete(self, product_id: int) -> bool:
        """Deletes a product by its ID."""
        # Consider adding checks for related entities (sales, inventory) if needed
        product_orm = self.session.get(ProductOrm, product_id)
        if product_orm:
            try:
                self.session.delete(product_orm)
                self.session.flush()
                return True
            except Exception as e:
                self.session.rollback()
                logging.error(f"Error deleting product {product_id}: {e}")
                raise
        return False

    def search(self, term: str) -> List[Product]:
        """Searches products by code or description, prioritizing exact matches."""
        search_term = f"%{term}%"

        # First try exact matches for code
        exact_code_stmt = (
            select(ProductOrm)
            .options(joinedload(ProductOrm.department))
            .where(ProductOrm.code.ilike(term))
        )
        exact_code_results = self.session.scalars(exact_code_stmt).all()

        # If we found exact code matches, return them first
        if exact_code_results:
            exact_products = [
                ModelMapper.product_orm_to_domain(prod) for prod in exact_code_results
            ]

            # Also get partial matches but exclude the exact ones
            partial_stmt = (
                select(ProductOrm)
                .options(joinedload(ProductOrm.department))
                .where(
                    and_(
                        or_(
                            ProductOrm.code.ilike(search_term),
                            ProductOrm.description.ilike(search_term),
                        ),
                        ~ProductOrm.code.ilike(term),  # Exclude exact code matches
                    )
                )
                .order_by(ProductOrm.description)
            )
            partial_results = self.session.scalars(partial_stmt).all()
            partial_products = [
                ModelMapper.product_orm_to_domain(prod) for prod in partial_results
            ]

            # Return exact matches first, then partial matches
            return exact_products + partial_products
        else:
            # No exact code matches, return all partial matches
            stmt = (
                select(ProductOrm)
                .options(joinedload(ProductOrm.department))
                .where(
                    or_(
                        ProductOrm.code.ilike(search_term),
                        ProductOrm.description.ilike(search_term),
                    )
                )
                .order_by(ProductOrm.description)
            )
            results_orm = self.session.scalars(stmt).all()
            return [ModelMapper.product_orm_to_domain(prod) for prod in results_orm]

    def get_low_stock(
        self, threshold: Optional[Decimal] = None
    ) -> List[Product]:  # Changed threshold to Decimal
        """Retrieves products where stock <= min_stock or below optional threshold."""
        stmt = select(ProductOrm).options(joinedload(ProductOrm.department))

        # Only include products that use inventory
        stmt = stmt.where(ProductOrm.uses_inventory == True)

        if threshold is not None:
            stmt = stmt.where(ProductOrm.quantity_in_stock <= threshold)
        else:
            # Default: stock <= min_stock (only for products that have min_stock set)
            stmt = stmt.where(
                and_(
                    ProductOrm.min_stock
                    != None,  # Only products with min_stock configured
                    ProductOrm.quantity_in_stock <= ProductOrm.min_stock,
                )
            )

        stmt = stmt.order_by(ProductOrm.description)
        results_orm = self.session.scalars(stmt).all()
        return [ModelMapper.product_orm_to_domain(prod) for prod in results_orm]

    def get_low_stock_products(
        self, threshold: Optional[Decimal] = None
    ) -> List[Product]:
        """Alias for get_low_stock method to match interface."""
        return self.get_low_stock(threshold)

    def get_inventory_report(self) -> List[Product]:
        """Returns all products with inventory information."""
        stmt = select(ProductOrm).options(joinedload(ProductOrm.department))
        stmt = stmt.where(ProductOrm.uses_inventory == True)
        stmt = stmt.order_by(ProductOrm.description)
        results_orm = self.session.scalars(stmt).all()
        return [ModelMapper.product_orm_to_domain(prod) for prod in results_orm]

    def update_stock(
        self,
        product_id: int,
        quantity_change: Decimal,
        cost_price: Optional[Decimal] = None,
    ) -> Optional[Product]:  # Changed types to Decimal
        """Updates the stock quantity and optionally the cost price of a specific product."""
        product_orm = self.session.get(ProductOrm, product_id)
        if product_orm:
            try:
                # Ensure quantity_in_stock is treated as Decimal if it comes from DB as Numeric
                current_stock = (
                    product_orm.quantity_in_stock
                    if isinstance(product_orm.quantity_in_stock, Decimal)
                    else Decimal(str(product_orm.quantity_in_stock))
                )
                # Set the new quantity directly (assume quantity_change is the new total)
                product_orm.quantity_in_stock = quantity_change

                if cost_price is not None:
                    # Ensure cost_price is Decimal for assignment to Numeric column
                    product_orm.cost_price = (
                        cost_price
                        if isinstance(cost_price, Decimal)
                        else Decimal(str(cost_price))
                    )

                product_orm.last_updated = datetime.now()
                self.session.flush()
                self.session.refresh(product_orm, attribute_names=["department"])
                return ModelMapper.product_orm_to_domain(product_orm)
            except Exception as e:
                self.session.rollback()
                logging.error(f"Error updating stock for product {product_id}: {e}")
                raise
        return None


# --- Inventory Movement Repository Implementation ---


class SqliteInventoryRepository(IInventoryRepository):
    """SQLite implementation of the inventory repository interface."""

    def __init__(self, session: Session):
        """Initialize with a database session."""
        self.session = session

    def add_movement(self, movement: InventoryMovement) -> InventoryMovement:
        """Adds a new inventory movement record."""
        try:
            # Map domain model to ORM
            movement_orm = InventoryMovementOrm(
                product_id=movement.product_id,
                user_id=movement.user_id,
                timestamp=movement.timestamp,
                movement_type=movement.movement_type,
                quantity=movement.quantity,  # Assign Decimal directly to Numeric
                description=movement.description,
                related_id=movement.related_id,
            )
            self.session.add(movement_orm)
            self.session.flush()
            self.session.refresh(movement_orm)
            return ModelMapper.inventory_movement_orm_to_domain(movement_orm)
        except Exception as e:
            self.session.rollback()
            logging.error(f"Error adding inventory movement: {e}")
            raise

    def get_movements_for_product(
        self,
        product_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[InventoryMovement]:
        """Retrieves all inventory movements for a specific product, ordered by timestamp."""
        stmt = select(InventoryMovementOrm).where(
            InventoryMovementOrm.product_id == product_id
        )
        if start_date:
            stmt = stmt.where(InventoryMovementOrm.timestamp >= start_date)
        if end_date:
            stmt = stmt.where(InventoryMovementOrm.timestamp <= end_date)
        stmt = stmt.order_by(InventoryMovementOrm.timestamp.desc())
        results_orm = self.session.scalars(stmt).all()
        return [
            ModelMapper.inventory_movement_orm_to_domain(move) for move in results_orm
        ]

    def get_all_movements(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[InventoryMovement]:
        """Retrieves all inventory movements within an optional date range."""
        stmt = select(InventoryMovementOrm)
        if start_date:
            stmt = stmt.where(InventoryMovementOrm.timestamp >= start_date)
        if end_date:
            stmt = stmt.where(InventoryMovementOrm.timestamp <= end_date)
        stmt = stmt.order_by(InventoryMovementOrm.timestamp.desc())
        results_orm = self.session.scalars(stmt).all()
        return [
            ModelMapper.inventory_movement_orm_to_domain(move) for move in results_orm
        ]

    def get_movements(
        self,
        product_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        movement_type: Optional[str] = None,
    ) -> List[InventoryMovement]:
        """Retrieves inventory movements with optional filters."""
        stmt = select(InventoryMovementOrm)

        if product_id is not None:
            stmt = stmt.where(InventoryMovementOrm.product_id == product_id)
        if start_date:
            stmt = stmt.where(InventoryMovementOrm.timestamp >= start_date)
        if end_date:
            stmt = stmt.where(InventoryMovementOrm.timestamp <= end_date)
        if movement_type:
            stmt = stmt.where(InventoryMovementOrm.movement_type == movement_type)

        stmt = stmt.order_by(InventoryMovementOrm.timestamp.desc())
        results_orm = self.session.scalars(stmt).all()
        return [
            ModelMapper.inventory_movement_orm_to_domain(move) for move in results_orm
        ]


# --- Sale Repository Implementation ---


class SqliteSaleRepository(ISaleRepository):
    """SQLite implementation of the sale repository interface."""

    def __init__(self, session: Session):  # Changed from __init__(self, session)
        self.session = session

    def add_sale(self, sale: Sale) -> Sale:
        """Adds a new sale and its items to the database."""
        try:
            # Map Sale domain model to SaleOrm
            sale_orm = SaleOrm(
                date_time=sale.timestamp,
                customer_id=sale.customer_id,
                is_credit_sale=sale.is_credit_sale,
                user_id=sale.user_id,
                payment_type=sale.payment_type,
                total_amount=sale.total,  # Assuming total is calculated and passed in Sale model?
            )

            # Map SaleItem domain models to SaleItemOrm and associate with SaleOrm
            for item_model in sale.items:
                item_orm = SaleItemOrm(
                    product_id=item_model.product_id,
                    quantity=item_model.quantity,  # Decimal -> Numeric
                    unit_price=item_model.unit_price,  # Decimal -> Numeric
                    product_code=item_model.product_code,
                    product_description=item_model.product_description,
                    product_unit=getattr(item_model, "product_unit", "Unidad"),
                )
                sale_orm.items.append(item_orm)

            self.session.add(sale_orm)
            self.session.flush()
            self.session.refresh(sale_orm)
            # Need to eager load items when refreshing/mapping back if required by caller
            # Or map back manually here including items
            return ModelMapper.sale_orm_to_domain(sale_orm)
        except Exception as e:
            self.session.rollback()
            logging.error(f"Error adding sale: {e}")
            raise

    def get_by_id(self, sale_id: int) -> Optional[Sale]:
        """Retrieves a single sale by its ID, including its items."""
        stmt = (
            select(SaleOrm)
            .options(joinedload(SaleOrm.items))
            .where(SaleOrm.id == sale_id)
        )
        sale_orm = self.session.scalars(stmt).first()
        return ModelMapper.sale_orm_to_domain(sale_orm)

    # Keeping the duplicate method name as it was in the original file
    def get_sale_by_id(self, sale_id: int) -> Optional[Sale]:
        """Retrieves a single sale by its ID (alternative method name)."""
        return self.get_by_id(sale_id)

    def get_sales_by_period(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> List[Sale]:
        """Retrieves all sales within the specified time period."""
        stmt = select(SaleOrm).options(joinedload(SaleOrm.items))
        if start_time:
            stmt = stmt.where(SaleOrm.date_time >= start_time)
        if end_time:
            # Add a small delta for inclusive end_time check if needed
            # end_time_inclusive = end_time + timedelta(seconds=1)
            stmt = stmt.where(SaleOrm.date_time <= end_time)
        stmt = stmt.order_by(SaleOrm.date_time.desc())

        # Use unique() to handle eager loading with collections
        results_orm = self.session.scalars(stmt).unique().all()
        return [ModelMapper.sale_orm_to_domain(sale) for sale in results_orm]

    # Aggregation methods remain largely the same, as they return Dicts, not domain models directly
    # (Ensure they query the ORM models correctly)
    def get_sales_summary_by_period(
        self, start_date=None, end_date=None, group_by: str = "day"
    ) -> List[Dict[str, Any]]:
        """Retrieves aggregated sales data grouped by a time period."""
        # Convert date objects to datetime if needed
        if start_date and not isinstance(start_date, datetime):
            start_date = datetime.combine(start_date, datetime.min.time())
        if end_date and not isinstance(end_date, datetime):
            end_date = datetime.combine(end_date, datetime.max.time())

        # Date formatting depends on the database engine (SQLite specific functions)
        if group_by == "day":
            date_format_str = "%Y-%m-%d"
            date_func = func.strftime(date_format_str, SaleOrm.date_time)
        elif group_by == "month":
            date_format_str = "%Y-%m"
            date_func = func.strftime(date_format_str, SaleOrm.date_time)
        elif group_by == "year":
            date_format_str = "%Y"
            date_func = func.strftime(date_format_str, SaleOrm.date_time)
        else:
            raise ValueError("Invalid group_by value. Use 'day', 'month', or 'year'.")

        # Use SQLAlchemy for aggregation
        query = self.session.query(
            date_func.label("date"),
            func.sum(SaleOrm.total_amount).label("total_sales"),
            func.count(SaleOrm.id).label("num_sales"),
        )

        if start_date:
            query = query.filter(SaleOrm.date_time >= start_date)
        if end_date:
            query = query.filter(SaleOrm.date_time <= end_date)

        query = query.group_by(date_func).order_by(date_func)

        results = query.all()

        # Convert results to the expected dictionary format
        result_list = [
            {
                "date": row.date,
                "total_sales": (
                    float(row.total_sales) if row.total_sales is not None else 0.0
                ),
                "num_sales": row.num_sales,
            }
            for row in results
        ]

        # Debug print the raw results
        # print(f"Raw query results: {result_list}") # Keep this commented out or remove for production

        return result_list

    def get_sales_by_payment_type(
        self, start_date=None, end_date=None
    ) -> List[Dict[str, Any]]:
        """Retrieves sales data aggregated by payment type for a period."""
        stmt = (
            select(
                SaleOrm.payment_type.label("payment_type"),
                func.sum(SaleOrm.total_amount).label("total_amount"),
                func.count(SaleOrm.id).label("num_sales"),
            )
            .group_by(SaleOrm.payment_type)
            .order_by(desc("total_amount"))
        )

        if start_date:
            stmt = stmt.where(SaleOrm.date_time >= start_date)
        if end_date:
            stmt = stmt.where(SaleOrm.date_time <= end_date)

        results = self.session.execute(stmt).mappings().all()
        return [
            {
                "payment_type": (
                    row["payment_type"] if row["payment_type"] else "Desconocido"
                ),
                "total_sales": (
                    float(row["total_amount"]) if row["total_amount"] else 0.0
                ),  # Convert to float and use total_sales key
                "num_sales": row["num_sales"],
            }
            for row in results
        ]

    def get_sales_by_department(
        self, start_date=None, end_date=None
    ) -> List[Dict[str, Any]]:
        """Retrieves sales data aggregated by product department for a period."""
        stmt = select(
            DepartmentOrm.id.label("department_id"),
            DepartmentOrm.name.label("department_name"),
            func.sum(SaleItemOrm.quantity * SaleItemOrm.unit_price).label(
                "total_amount"
            ),
            func.sum(SaleItemOrm.quantity).label("quantity_sold"),
            func.count(SaleOrm.id).label("num_sales"),  # Count distinct sales
        )
        stmt = stmt.select_from(SaleOrm)
        stmt = stmt.join(SaleItemOrm, SaleOrm.id == SaleItemOrm.sale_id)
        stmt = stmt.join(ProductOrm, SaleItemOrm.product_id == ProductOrm.id)
        stmt = stmt.join(DepartmentOrm, ProductOrm.department_id == DepartmentOrm.id)

        if start_date:
            stmt = stmt.where(SaleOrm.date_time >= start_date)
        if end_date:
            stmt = stmt.where(SaleOrm.date_time <= end_date)

        stmt = stmt.group_by(DepartmentOrm.id, DepartmentOrm.name).order_by(
            desc("total_amount")
        )

        results = self.session.execute(stmt).mappings().all()
        return [
            {
                "department_id": row["department_id"],
                "department_name": row["department_name"],
                "total_sales": (
                    float(row["total_amount"]) if row["total_amount"] else 0.0
                ),  # Convert to float and use total_sales key
                "quantity_sold": (
                    float(row["quantity_sold"]) if row["quantity_sold"] else 0.0
                ),  # Convert to float for consistency
                "num_sales": row["num_sales"],
            }
            for row in results
        ]

    def get_sales_by_customer(
        self, start_date=None, end_date=None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieves sales data aggregated by customer for a period."""
        stmt = select(
            CustomerOrm.id.label("customer_id"),
            CustomerOrm.name.label("customer_name"),
            func.sum(SaleOrm.total_amount).label("total_amount"),
            func.count(SaleOrm.id).label("num_sales"),
        )
        stmt = stmt.select_from(SaleOrm)
        stmt = stmt.join(CustomerOrm, SaleOrm.customer_id == CustomerOrm.id)

        if start_date:
            stmt = stmt.where(SaleOrm.date_time >= start_date)
        if end_date:
            stmt = stmt.where(SaleOrm.date_time <= end_date)

        stmt = (
            stmt.group_by(CustomerOrm.id, CustomerOrm.name)
            .order_by(desc("total_amount"))
            .limit(limit)
        )

        results = self.session.execute(stmt).mappings().all()
        return [
            {
                "customer_id": row["customer_id"],
                "customer_name": row["customer_name"],
                "total_sales": (
                    float(row["total_amount"]) if row["total_amount"] else 0.0
                ),  # Convert to float and use total_sales key
                "num_sales": row["num_sales"],
            }
            for row in results
        ]

    def get_top_selling_products(
        self, start_date=None, end_date=None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieves the top selling products for a period by quantity."""
        stmt = (
            select(
                ProductOrm.id.label("product_id"),
                ProductOrm.code.label("product_code"),
                ProductOrm.description.label("product_description"),
                func.sum(SaleItemOrm.quantity).label("quantity_sold"),
            )
            .select_from(SaleOrm)
            .join(SaleItemOrm, SaleOrm.id == SaleItemOrm.sale_id)
            .join(ProductOrm, SaleItemOrm.product_id == ProductOrm.id)
        )

        if start_date:
            stmt = stmt.where(SaleOrm.date_time >= start_date)
        if end_date:
            stmt = stmt.where(SaleOrm.date_time <= end_date)

        stmt = (
            stmt.group_by(ProductOrm.id, ProductOrm.code, ProductOrm.description)
            .order_by(desc("quantity_sold"))
            .limit(limit)
        )

        results = self.session.execute(stmt).mappings().all()
        return [
            {
                "product_id": row["product_id"],
                "product_code": row["product_code"],
                "product_description": row["product_description"],
                "quantity_sold": row["quantity_sold"],  # Keep as Decimal
            }
            for row in results
        ]

    def calculate_profit_for_period(
        self, start_time: datetime, end_time: datetime
    ) -> Dict[str, Any]:
        """
        Calculates the total profit for a period (revenue - cost).

        Args:
            start_time: The start of the period
            end_time: The end of the period

        Returns:
            Dictionary with profit data
            Example: {'revenue': 5000.0, 'cost': 3000.0, 'profit': 2000.0, 'margin': 0.4}
        """
        # Convert date objects to datetime if needed
        if not isinstance(start_time, datetime):
            start_time = datetime.combine(start_time, datetime.min.time())
        if not isinstance(end_time, datetime):
            end_time = datetime.combine(end_time, datetime.max.time())

        # Initialize result values
        total_revenue = Decimal("0.00")
        total_cost = Decimal("0.00")

        # Use join load to get all sales with their items in a single query
        sales_with_items = (
            self.session.query(SaleOrm)
            .options(joinedload(SaleOrm.items))
            .filter(SaleOrm.date_time >= start_time)
            .filter(SaleOrm.date_time <= end_time)
            .all()
        )

        # Calculate revenue from all sale items
        for sale in sales_with_items:
            for item in sale.items:
                total_revenue += item.quantity * item.unit_price

                # Get the product cost price and calculate cost
                product = (
                    self.session.query(ProductOrm)
                    .filter(ProductOrm.id == item.product_id)
                    .first()
                )
                if product and product.cost_price:
                    item_cost = product.cost_price * item.quantity
                    total_cost += item_cost

        # Calculate profit
        total_profit = total_revenue - total_cost

        # Calculate profit margin (as a decimal)
        profit_margin = Decimal("0.00")
        if total_revenue > Decimal("0.00"):
            profit_margin = total_profit / total_revenue

        # Convert all Decimal values to float to avoid type comparison issues
        return {
            "revenue": float(total_revenue),
            "cost": float(total_cost),
            "profit": float(total_profit),
            "margin": float(profit_margin),
        }

    def get_cash_drawer_entries(
        self, start_date=None, end_date=None, drawer_id=None
    ) -> List[CashDrawerEntry]:
        """Get all cash drawer entries for a time period and optionally a specific drawer."""
        # Build base query
        query = self.session.query(CashDrawerEntryOrm)

        # Apply filters if provided
        if start_date:
            query = query.filter(CashDrawerEntryOrm.timestamp >= start_date)
        if end_date:
            query = query.filter(CashDrawerEntryOrm.timestamp <= end_date)
        if drawer_id is not None:
            query = query.filter(CashDrawerEntryOrm.drawer_id == drawer_id)

        # Execute query and convert results
        orm_entries = query.order_by(CashDrawerEntryOrm.timestamp).all()
        return [self._orm_to_model(orm_entry) for orm_entry in orm_entries]

    def get_last_start_entry(
        self, drawer_id: Optional[int] = None
    ) -> Optional[CashDrawerEntry]:
        """Get the most recent START entry for a drawer."""
        # Build query for START entries
        query = self.session.query(CashDrawerEntryOrm).filter(
            CashDrawerEntryOrm.entry_type == CashDrawerEntryType.START.value
        )  # Use .value here

        # Add drawer filter if provided
        if drawer_id is not None:
            query = query.filter(CashDrawerEntryOrm.drawer_id == drawer_id)

        # Get the most recent entry
        orm_entry = query.order_by(desc(CashDrawerEntryOrm.timestamp)).first()

        # Convert to domain model if found
        return self._orm_to_model(orm_entry) if orm_entry else None

    def get_entry_by_id(self, entry_id: int) -> Optional[CashDrawerEntry]:
        """Get a cash drawer entry by ID."""
        orm_entry = (
            self.session.query(CashDrawerEntryOrm)
            .filter(CashDrawerEntryOrm.id == entry_id)
            .first()
        )
        return self._orm_to_model(orm_entry) if orm_entry else None

    def update(self, sale_id: int, data: Dict[str, Any]) -> Optional[Sale]:
        """Updates specific fields of a sale identified by its ID."""
        try:
            # Retrieve the SaleOrm object using the primary key
            sale_orm = self.session.get(SaleOrm, sale_id)
            if not sale_orm:
                logging.warning(f"Sale with ID {sale_id} not found for update.")
                return None

            # Update attributes from the data dictionary
            for key, value in data.items():
                if hasattr(sale_orm, key):
                    setattr(sale_orm, key, value)
                else:
                    logging.warning(
                        f"Attempted to update non-existent attribute '{key}' on SaleOrm for sale ID {sale_id}"
                    )

            self.session.commit()
            self.session.refresh(
                sale_orm
            )  # Refresh to get any DB-generated values or updated state
            return ModelMapper.sale_orm_to_domain(sale_orm)
        except Exception as e:
            self.session.rollback()
            logging.error(f"Error updating sale ID {sale_id} with data {data}: {e}")
            raise


class SqliteCustomerRepository(ICustomerRepository):
    """SQLite implementation of the customer repository interface."""

    def __init__(self, session: Session):
        self.session = session

    def add(self, customer: Customer) -> Customer:
        """Add a new customer to the repository."""
        try:
            # Check for duplicate CUIT
            if customer.cuit:  # Only check if CUIT is provided
                existing_cuit = self.session.execute(
                    text("SELECT id FROM customers WHERE cuit = :cuit"),
                    {"cuit": customer.cuit},
                ).scalar_one_or_none()

                if existing_cuit:
                    raise ValueError(
                        f"Customer with CUIT {customer.cuit} already exists"
                    )

            # Check for duplicate email
            if customer.email:  # Only check if email is provided
                existing_email = self.session.execute(
                    text("SELECT id FROM customers WHERE email = :email"),
                    {"email": customer.email},
                ).scalar_one_or_none()

                if existing_email:
                    raise ValueError(
                        f"Customer with email {customer.email} already exists"
                    )

            # Create a new CustomerOrm object and set attributes individually
            if customer.id is None:
                # New customer to be created with auto-ID
                customer_orm = CustomerOrm(
                    name=customer.name,
                    phone=customer.phone,
                    email=customer.email,
                    address=customer.address,
                    cuit=customer.cuit,
                    iva_condition=customer.iva_condition,
                    credit_limit=customer.credit_limit,
                    credit_balance=customer.credit_balance,
                    is_active=customer.is_active,
                )
            else:
                # Customer with pre-defined ID (e.g., migration)
                customer_orm = CustomerOrm(
                    id=customer.id,
                    name=customer.name,
                    phone=customer.phone,
                    email=customer.email,
                    address=customer.address,
                    cuit=customer.cuit,
                    iva_condition=customer.iva_condition,
                    credit_limit=customer.credit_limit,
                    credit_balance=customer.credit_balance,
                    is_active=customer.is_active,
                )

            # Add to session
            self.session.add(customer_orm)
            self.session.flush()
            self.session.refresh(customer_orm)

            # Map back to domain model
            return ModelMapper.customer_orm_to_domain(customer_orm)
        except Exception as e:
            # Log the error
            logging.error(f"Error adding customer: {e}")
            raise

    def get_by_id(self, customer_id) -> Optional[Customer]:
        """Get a customer by ID."""
        customer_orm = (
            self.session.query(CustomerOrm)
            .filter(CustomerOrm.id == customer_id)
            .first()
        )
        return ModelMapper.customer_orm_to_domain(customer_orm)

    def get_by_cuit(self, cuit: str) -> Optional[Customer]:
        """Get a customer by CUIT."""
        if not cuit:
            return None
        customer_orm = (
            self.session.query(CustomerOrm).filter(CustomerOrm.cuit == cuit).first()
        )
        return ModelMapper.customer_orm_to_domain(customer_orm)

    def search(
        self, term: str, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[Customer]:
        """Search for customers by name, phone, email, or CUIT, with optional pagination."""
        if not term:
            return []

        # Case-insensitive search on all text fields
        query = (
            self.session.query(CustomerOrm)
            .filter(
                or_(
                    CustomerOrm.name.ilike(f"%{term}%"),
                    CustomerOrm.phone.ilike(f"%{term}%"),
                    CustomerOrm.email.ilike(f"%{term}%"),
                    CustomerOrm.cuit.ilike(f"%{term}%"),
                )
            )
            .order_by(CustomerOrm.name)
        )

        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)

        results = query.all()
        return [ModelMapper.customer_orm_to_domain(orm) for orm in results]

    def get_all(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[Customer]:
        """Get all customers, with optional pagination."""
        query = self.session.query(CustomerOrm).order_by(CustomerOrm.name)
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
        customers_orm = query.all()
        return [ModelMapper.customer_orm_to_domain(orm) for orm in customers_orm]

    def update(self, customer: Customer) -> Customer:
        """Update an existing customer."""
        try:
            # Get the existing customer
            customer_orm = (
                self.session.query(CustomerOrm)
                .filter(CustomerOrm.id == customer.id)
                .first()
            )
            if not customer_orm:
                raise ValueError(f"Customer with ID {customer.id} not found")

            # Update properties
            customer_orm.name = customer.name
            customer_orm.phone = customer.phone
            customer_orm.email = customer.email
            customer_orm.address = customer.address
            customer_orm.cuit = customer.cuit
            customer_orm.iva_condition = customer.iva_condition
            customer_orm.credit_limit = customer.credit_limit
            customer_orm.credit_balance = customer.credit_balance  # Added this line
            # We typically don't update credit_balance directly through update()
            # It should be managed through dedicated operations that log the changes
            customer_orm.is_active = customer.is_active
            customer_orm.updated_at = datetime.now()

            # Flush changes
            self.session.flush()
            self.session.refresh(customer_orm)

            # Return updated customer
            return ModelMapper.customer_orm_to_domain(customer_orm)
        except Exception as e:
            # Log the error
            logging.error(f"Error updating customer: {e}")
            raise

    def update_balance(self, customer_id, new_balance: Decimal) -> bool:
        """Update a customer's credit balance."""
        try:
            # Get the customer
            customer_orm = (
                self.session.query(CustomerOrm)
                .filter(CustomerOrm.id == customer_id)
                .first()
            )
            if not customer_orm:
                return False

            # Update the balance
            customer_orm.credit_balance = new_balance
            customer_orm.updated_at = datetime.now()

            # Flush changes
            self.session.flush()

            return True
        except Exception as e:
            # Log the error
            logging.error(f"Error updating customer balance: {e}")
            raise

    def delete(self, customer_id) -> bool:
        """Delete a customer by ID."""
        try:
            # Get the customer
            customer_orm = (
                self.session.query(CustomerOrm)
                .filter(CustomerOrm.id == customer_id)
                .first()
            )
            if not customer_orm:
                return False

            # Delete the customer
            self.session.delete(customer_orm)
            self.session.flush()

            return True
        except Exception as e:
            # Log the error
            logging.error(f"Error deleting customer: {e}")
            raise


class SqliteInvoiceRepository(IInvoiceRepository):
    """SQLite implementation of the invoice repository interface."""

    def __init__(self, session: Session):
        self.session = session

    def add(self, invoice: Invoice) -> Invoice:
        """Add a new invoice to the database."""
        try:
            # Check if the sale already has an invoice
            if self.get_by_sale_id(invoice.sale_id):
                raise ValueError(
                    f"Invoice for sale ID {invoice.sale_id} already exists"
                )

            # Map to ORM
            invoice_orm = ModelMapper.invoice_domain_to_orm(invoice)

            # Add to session
            self.session.add(invoice_orm)
            self.session.flush()
            self.session.refresh(invoice_orm)

            # Map back to domain model and return
            return ModelMapper.invoice_orm_to_domain(invoice_orm)
        except Exception as e:
            # Log error and re-raise
            logging.error(f"Error adding invoice: {e}")
            raise

    def get_by_id(self, invoice_id: int) -> Optional[Invoice]:
        """Get an invoice by its ID."""
        invoice_orm = (
            self.session.query(InvoiceOrm).filter(InvoiceOrm.id == invoice_id).first()
        )
        return ModelMapper.invoice_orm_to_domain(invoice_orm)

    def get_by_sale_id(self, sale_id: int) -> Optional[Invoice]:
        """Get an invoice for a specific sale."""
        invoice_orm = (
            self.session.query(InvoiceOrm).filter(InvoiceOrm.sale_id == sale_id).first()
        )
        return ModelMapper.invoice_orm_to_domain(invoice_orm)

    def get_by_invoice_number(self, invoice_number: str) -> Optional[Invoice]:
        """Get an invoice by its number."""
        invoice_orm = (
            self.session.query(InvoiceOrm)
            .filter(InvoiceOrm.invoice_number == invoice_number)
            .first()
        )
        return ModelMapper.invoice_orm_to_domain(invoice_orm)

    def get_all(self) -> List[Invoice]:
        """Get all invoices."""
        invoice_orms = self.session.query(InvoiceOrm).all()
        return [
            ModelMapper.invoice_orm_to_domain(orm)
            for orm in invoice_orms
            if orm is not None
        ]

    def update(self, invoice: Invoice) -> Invoice:
        """Update an existing invoice."""
        try:
            # Find the existing invoice
            existing_orm = (
                self.session.query(InvoiceOrm)
                .filter(InvoiceOrm.id == invoice.id)
                .first()
            )
            if not existing_orm:
                raise ValueError(f"Invoice with ID {invoice.id} not found")

            # Update the ORM object with new values
            updated_orm = ModelMapper.invoice_domain_to_orm(invoice, existing_orm)

            # Flush to ensure changes are reflected
            self.session.flush()
            self.session.refresh(updated_orm)

            # Return mapped domain model
            return ModelMapper.invoice_orm_to_domain(updated_orm)
        except Exception as e:
            # Log error and re-raise
            logging.error(f"Error updating invoice: {e}")
            raise

    def delete(self, invoice_id: int) -> bool:
        """Delete an invoice by its ID."""
        try:
            invoice_orm = (
                self.session.query(InvoiceOrm)
                .filter(InvoiceOrm.id == invoice_id)
                .first()
            )
            if not invoice_orm:
                return False

            self.session.delete(invoice_orm)
            self.session.flush()
            return True
        except Exception as e:
            # Log error and re-raise
            logging.error(f"Error deleting invoice: {e}")
            raise


class SqliteCreditPaymentRepository(ICreditPaymentRepository):
    """SQLite implementation of the credit payment repository interface."""

    def __init__(self, session: Session):
        self.session = session

    def add(self, payment: CreditPayment) -> CreditPayment:
        """Adds a new credit payment to the database."""
        try:
            # Verify customer exists
            customer_exists = (
                self.session.query(CustomerOrm)
                .filter(CustomerOrm.id == payment.customer_id)
                .first()
            )
            if not customer_exists:
                raise ValueError(f"Customer with ID {payment.customer_id} not found.")

            # Map the domain model to ORM
            payment_orm = CreditPaymentOrm(
                customer_id=payment.customer_id,
                amount=payment.amount,
                timestamp=payment.timestamp,  # Use timestamp directly
                notes=payment.notes,  # Use notes directly
                user_id=payment.user_id,
            )

            # Add to session
            self.session.add(payment_orm)
            self.session.flush()
            self.session.refresh(payment_orm)

            # Map back to domain model
            return ModelMapper.credit_payment_orm_to_domain(payment_orm)
        except Exception as e:
            logging.error(f"Error adding credit payment: {e}")
            raise

    def get_by_id(self, payment_id: int) -> Optional[CreditPayment]:
        """Gets a credit payment by its ID."""
        payment_orm = (
            self.session.query(CreditPaymentOrm)
            .filter(CreditPaymentOrm.id == payment_id)
            .first()
        )
        return ModelMapper.credit_payment_orm_to_domain(payment_orm)

    def get_for_customer(self, customer_id: int) -> List[CreditPayment]:
        """Get all credit payments for a customer."""
        payments = (
            self.session.query(CreditPaymentOrm)
            .filter_by(customer_id=customer_id)
            .order_by(CreditPaymentOrm.timestamp.desc())
            .all()
        )
        return [ModelMapper.credit_payment_orm_to_domain(p) for p in payments]

    def delete(self, payment_id: int) -> bool:
        """Delete a credit payment by ID."""
        try:
            payment = (
                self.session.query(CreditPaymentOrm).filter_by(id=payment_id).first()
            )
            if not payment:
                return False

            self.session.delete(payment)
            self.session.flush()
            return True
        except Exception as e:
            logging.error(f"Error deleting credit payment: {e}")
            raise


class SqliteUserRepository(IUserRepository):
    """SQLite implementation of the user repository interface."""

    def __init__(self, session: Session):
        self.session = session

    def _hash_password(self, password: str) -> str:
        """Hash the password using bcrypt."""
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt()
        hashed_bytes = bcrypt.hashpw(password_bytes, salt)
        return hashed_bytes.decode("utf-8")

    def add(self, user: User) -> User:
        """Adds a new user to the database."""
        try:
            # Check if username already exists
            if self.get_by_username(user.username):
                raise ValueError(f"Username '{user.username}' already exists.")

            # If password is provided but no password_hash, hash the password
            if getattr(user, "password", None) and not user.password_hash:
                user.password_hash = self._hash_password(user.password)

            # Map domain model to ORM
            user_orm = UserOrm(
                username=user.username,
                password_hash=user.password_hash,
                email=getattr(user, "email", None),
                is_active=user.is_active,
                is_admin=getattr(user, "is_admin", False),
            )

            # Add to session
            self.session.add(user_orm)
            self.session.flush()
            self.session.refresh(user_orm)

            # Map back to domain model
            return ModelMapper.user_orm_to_domain(user_orm)
        except Exception as e:
            logging.error(f"Error adding user: {e}")
            raise

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Retrieves a user by their ID."""
        user_orm = self.session.query(UserOrm).filter(UserOrm.id == user_id).first()
        return ModelMapper.user_orm_to_domain(user_orm)

    def get_by_username(self, username: str) -> Optional[User]:
        """Retrieves a user by their username."""
        user_orm = (
            self.session.query(UserOrm).filter(UserOrm.username == username).first()
        )
        return ModelMapper.user_orm_to_domain(user_orm)

    def update(self, user: User) -> Optional[User]:
        """Updates an existing user."""
        try:
            # Get existing user
            user_orm = self.session.query(UserOrm).filter(UserOrm.id == user.id).first()
            if not user_orm:
                return None

            # Check username uniqueness if changed
            if user.username != user_orm.username and self.get_by_username(
                user.username
            ):
                raise ValueError(f"Username '{user.username}' already exists.")

            # Update fields
            user_orm.username = user.username
            user_orm.email = user.email
            user_orm.is_active = user.is_active
            user_orm.is_admin = user.is_admin

            # Only update password if provided
            if user.password_hash and user.password_hash != user_orm.password_hash:
                user_orm.password_hash = user.password_hash

            # Flush and refresh
            self.session.flush()
            self.session.refresh(user_orm)

            # Map back to domain
            return ModelMapper.user_orm_to_domain(user_orm)
        except Exception as e:
            logging.error(f"Error updating user: {e}")
            raise

    def delete(self, user_id: int) -> bool:
        """Deletes a user by ID."""
        try:
            user_orm = self.session.query(UserOrm).filter(UserOrm.id == user_id).first()
            if not user_orm:
                return False

            self.session.delete(user_orm)
            self.session.flush()
            return True
        except Exception as e:
            logging.error(f"Error deleting user: {e}")
            raise

    def get_all(self) -> List[User]:
        """Retrieves all users."""
        users_orm = self.session.query(UserOrm).all()
        return [ModelMapper.user_orm_to_domain(user) for user in users_orm]


class SqliteCashDrawerRepository(SQLiteCashDrawerRepository):
    """Adapter class for SQLiteCashDrawerRepository to maintain API compatibility."""

    pass


class SqliteUnitRepository(IUnitRepository):
    """SQLite implementation of the unit repository interface."""

    def __init__(self, session: Session):
        self.session = session

    def add(self, unit: Unit) -> Unit:
        """Adds a new unit to the database."""
        try:
            # Check if unit name already exists
            existing = self.get_by_name(unit.name)
            if existing:
                raise ValueError(f"Unit name '{unit.name}' already exists.")

            # Create ORM object
            unit_orm = UnitOrm(
                name=unit.name,
                abbreviation=unit.abbreviation,
                description=unit.description,
                is_active=unit.is_active,
            )

            # Add to session
            self.session.add(unit_orm)
            self.session.flush()
            self.session.refresh(unit_orm)

            # Map back to domain model
            return ModelMapper.unit_orm_to_domain(unit_orm)
        except Exception as e:
            logging.error(f"Error adding unit: {e}")
            raise

    def get_by_id(self, unit_id: int) -> Optional[Unit]:
        """Retrieves a unit by its ID."""
        unit_orm = self.session.get(UnitOrm, unit_id)
        return ModelMapper.unit_orm_to_domain(unit_orm)

    def get_by_name(self, name: str) -> Optional[Unit]:
        """Retrieves a unit by its name."""
        stmt = select(UnitOrm).where(UnitOrm.name == name)
        unit_orm = self.session.scalars(stmt).first()
        return ModelMapper.unit_orm_to_domain(unit_orm)

    def get_all(self, active_only: bool = True) -> List[Unit]:
        """Retrieves all units, optionally filtered by active status."""
        stmt = select(UnitOrm).order_by(UnitOrm.name)
        if active_only:
            stmt = stmt.where(UnitOrm.is_active == True)
        units_orm = self.session.scalars(stmt).all()
        return [ModelMapper.unit_orm_to_domain(unit) for unit in units_orm]

    def update(self, unit: Unit) -> Optional[Unit]:
        """Updates an existing unit."""
        try:
            if unit.id is None:
                raise ValueError("Unit ID is required for update.")

            # Check for name collision if name is being changed
            existing_by_name = self.get_by_name(unit.name)
            if existing_by_name and existing_by_name.id != unit.id:
                raise ValueError(
                    f"Another unit with name '{unit.name}' already exists."
                )

            unit_orm = self.session.get(UnitOrm, unit.id)
            if not unit_orm:
                raise ValueError(f"Unit with ID {unit.id} not found.")

            # Update ORM attributes
            unit_orm.name = unit.name
            unit_orm.abbreviation = unit.abbreviation
            unit_orm.description = unit.description
            unit_orm.is_active = unit.is_active

            self.session.flush()
            self.session.refresh(unit_orm)
            return ModelMapper.unit_orm_to_domain(unit_orm)
        except Exception as e:
            logging.error(f"Error updating unit: {e}")
            raise

    def delete(self, unit_id: int) -> bool:
        """Deletes a unit by its ID."""
        try:
            unit_orm = self.session.get(UnitOrm, unit_id)
            if not unit_orm:
                raise ValueError(f"Unit with ID {unit_id} not found")

            # Check if unit is used by products
            product_count = self.session.scalar(
                select(func.count(ProductOrm.id)).where(
                    ProductOrm.unit == unit_orm.name
                )
            )
            if product_count > 0:
                raise ValueError(
                    f"Unit {unit_id} cannot be deleted, it is used by {product_count} products."
                )

            self.session.delete(unit_orm)
            self.session.flush()
            return True
        except Exception as e:
            logging.error(f"Error deleting unit: {e}")
            raise

    def search(self, query: str) -> List[Unit]:
        """Searches for units based on name or abbreviation."""
        stmt = (
            select(UnitOrm)
            .where(
                or_(
                    UnitOrm.name.ilike(f"%{query}%"),
                    UnitOrm.abbreviation.ilike(f"%{query}%"),
                )
            )
            .order_by(UnitOrm.name)
        )
        units_orm = self.session.scalars(stmt).all()
        return [ModelMapper.unit_orm_to_domain(unit) for unit in units_orm]
