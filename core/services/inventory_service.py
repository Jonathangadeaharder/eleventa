from typing import List, Optional, Callable, Any # Added Callable, Any
from sqlalchemy.orm import Session # Needed for type hinting session passed in decrease_stock
from decimal import Decimal # Added Decimal

# Adjust imports based on project structure
from core.interfaces.repository_interfaces import IInventoryRepository, IProductRepository
from core.models.inventory import InventoryMovement
from core.models.product import Product
from infrastructure.persistence.utils import session_scope # For managing transactions

# Define RepositoryFactory type alias
RepositoryFactory = Callable[[Session], Any]

class InventoryService:
    """Provides services related to inventory management."""

    def __init__(self, inventory_repo_factory: RepositoryFactory, product_repo_factory: RepositoryFactory):
        self.inventory_repo_factory = inventory_repo_factory
        self.product_repo_factory = product_repo_factory

    def add_inventory(
        self,
        product_id: int,
        quantity: Decimal,
        new_cost_price: Optional[Decimal] = None,
        notes: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Product:
        """Adds quantity to a product's stock, logs movement, and optionally updates cost price."""
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")

        with session_scope() as session:
            # Instantiate repositories within session scope
            prod_repo = self.product_repo_factory(session)
            inv_repo = self.inventory_repo_factory(session)

            product = prod_repo.get_by_id(product_id) # Use instantiated repo
            if not product:
                raise ValueError(f"Product with ID {product_id} not found.")
            if not product.uses_inventory:
                raise ValueError(f"Product {product.code} does not use inventory control.")

            # Ensure quantity_in_stock is Decimal before adding
            current_stock = product.quantity_in_stock if isinstance(product.quantity_in_stock, Decimal) else Decimal(str(product.quantity_in_stock))
            new_quantity = current_stock + quantity

            # Update product stock (and cost if provided)
            prod_repo.update_stock(product_id, new_quantity, new_cost_price) # Use instantiated repo

            # Log the movement
            movement = InventoryMovement(
                product_id=product_id,
                quantity=quantity,
                movement_type="PURCHASE",
                description=notes,
                user_id=user_id
            )
            inv_repo.add_movement(movement) # Use instantiated repo

            # Update local product object for return
            product.quantity_in_stock = new_quantity
            if new_cost_price is not None:
                product.cost_price = new_cost_price

            return product

    def adjust_inventory(
        self,
        product_id: int,
        quantity: Decimal,
        reason: str,
        user_id: Optional[int] = None
    ) -> Product:
        """Adjusts a product's stock quantity (positive or negative) and logs movement."""
        if quantity == 0:
            raise ValueError("Adjustment quantity cannot be zero.")

        with session_scope() as session:
            # Instantiate repositories within session scope
            prod_repo = self.product_repo_factory(session)
            inv_repo = self.inventory_repo_factory(session)

            product = prod_repo.get_by_id(product_id) # Use instantiated repo
            if not product:
                raise ValueError(f"Product with ID {product_id} not found.")
            if not product.uses_inventory:
                raise ValueError(f"Product {product.code} does not use inventory control.")

            # Ensure quantity_in_stock is Decimal before adding
            current_stock = product.quantity_in_stock if isinstance(product.quantity_in_stock, Decimal) else Decimal(str(product.quantity_in_stock))
            new_quantity = current_stock + quantity

            allow_negative_stock = False
            if new_quantity < 0 and not allow_negative_stock:
                raise ValueError(
                    f"Adjustment results in negative stock ({new_quantity}) for product {product.code}, which is not allowed."
                )

            # Update product stock
            prod_repo.update_stock(product_id, new_quantity) # Use instantiated repo

            # Log the movement
            movement = InventoryMovement(
                product_id=product_id,
                quantity=quantity,
                movement_type="ADJUSTMENT",
                description=reason,
                user_id=user_id
            )
            inv_repo.add_movement(movement) # Use instantiated repo

            # Update local product object for return
            product.quantity_in_stock = new_quantity

            return product

    def decrease_stock_for_sale(
        self,
        session: Session, # Expects an active session
        product_id: int,
        quantity: Decimal,
        sale_id: int,
        user_id: Optional[int] = None
    ) -> None:
        """Decreases stock for a sold item within an existing transaction."""
        if quantity <= 0:
            raise ValueError("Quantity for sale must be positive.")

        # Instantiate repositories using the provided session
        prod_repo = self.product_repo_factory(session)
        inv_repo = self.inventory_repo_factory(session)

        product = prod_repo.get_by_id(product_id) # Use instantiated repo
        if not product:
            raise ValueError(f"Product with ID {product_id} not found for sale item.")
        if not product.uses_inventory:
            raise ValueError(f"Product {product.code} does not use inventory control but was included in sale {sale_id}.")

        # Ensure quantity_in_stock is Decimal before comparison/subtraction
        current_stock = Decimal('0.0') # Initialize as Decimal
        if hasattr(product, 'quantity_in_stock') and product.quantity_in_stock is not None:
            try:
                current_stock = Decimal(str(product.quantity_in_stock))
            except Exception:
                 # Handle case where conversion fails, though should ideally be Decimal already
                 raise ValueError(f"Invalid stock quantity format for product {product.code}")

        new_quantity = current_stock - quantity

        allow_negative_stock_sales = False
        if new_quantity < 0 and not allow_negative_stock_sales:
            raise ValueError(
                f"Insufficient stock for product {product.code} (requires {quantity}, has {current_stock}). Sale {sale_id}"
            )

        # Update stock
        prod_repo.update_stock(product_id, new_quantity) # Use instantiated repo

        # Log movement
        movement = InventoryMovement(
            product_id=product_id,
            quantity=-quantity,
            movement_type="SALE",
            description=f"Venta #{sale_id}",
            related_id=sale_id,
            user_id=user_id
        )
        inv_repo.add_movement(movement) # Use instantiated repo

    # --- Reporting Methods ---

    def get_inventory_report(self) -> List[Product]:
        """Retrieves a general inventory report (all products with stock)."""
        with session_scope() as session:
            prod_repo = self.product_repo_factory(session)
            return prod_repo.get_all()

    def get_low_stock_products(self) -> List[Product]:
        """Retrieves products below their minimum stock level."""
        with session_scope() as session:
            prod_repo = self.product_repo_factory(session)
            return prod_repo.get_low_stock()

    def get_inventory_movements(self, product_id: Optional[int] = None) -> List[InventoryMovement]:
        """Retrieves inventory movements, optionally filtered by product."""
        with session_scope() as session:
            inv_repo = self.inventory_repo_factory(session)
            if product_id:
                return inv_repo.get_movements_for_product(product_id)
            else:
                return inv_repo.get_all_movements() 