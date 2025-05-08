from typing import List, Optional, Callable, Any
from sqlalchemy.orm import Session
from decimal import Decimal

from core.interfaces.repository_interfaces import IInventoryRepository, IProductRepository
from core.models.inventory import InventoryMovement
from core.models.product import Product
from core.services.service_base import ServiceBase
from infrastructure.persistence.utils import session_scope

class InventoryService(ServiceBase):
    """Provides services related to inventory management."""

    def __init__(self, inventory_repo_factory: Callable[[Session], IInventoryRepository], 
                 product_repo_factory: Callable[[Session], IProductRepository]):
        """
        Initialize with repository factories.
        
        Args:
            inventory_repo_factory: Factory function to create inventory repository
            product_repo_factory: Factory function to create product repository
        """
        super().__init__()  # Initialize base class with default logger
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
        def _add_inventory(session, product_id, quantity, new_cost_price, notes, user_id):
            if quantity <= 0:
                raise ValueError("Quantity must be positive.")
                
            # Get repositories from factories
            prod_repo = self._get_repository(self.product_repo_factory, session)
            inv_repo = self._get_repository(self.inventory_repo_factory, session)

            product = prod_repo.get_by_id(product_id)
            if not product:
                raise ValueError(f"Product with ID {product_id} not found.")
            if not product.uses_inventory:
                raise ValueError(f"Product {product.code} does not use inventory control.")

            # Ensure quantity_in_stock is Decimal before adding
            current_stock = product.quantity_in_stock if isinstance(product.quantity_in_stock, Decimal) else Decimal(str(product.quantity_in_stock))
            new_quantity = current_stock + quantity

            # Update product stock (and cost if provided)
            prod_repo.update_stock(product_id, quantity, new_cost_price)  # Pass quantity change, not new total

            # Log the movement
            movement = InventoryMovement(
                product_id=product_id,
                quantity=quantity,
                movement_type="PURCHASE",
                description=notes,
                user_id=user_id
            )
            inv_repo.add_movement(movement)

            # Update local product object for return
            product.quantity_in_stock = new_quantity
            if new_cost_price is not None:
                product.cost_price = new_cost_price

            return product
            
        return self._with_session(_add_inventory, product_id, quantity, new_cost_price, notes, user_id)

    def adjust_inventory(
        self,
        product_id: int,
        quantity: Decimal,
        reason: str,
        user_id: Optional[int] = None
    ) -> Product:
        """Adjusts a product's stock quantity (positive or negative) and logs movement."""
        def _adjust_inventory(session, product_id, quantity, reason, user_id):
            if quantity == 0:
                raise ValueError("Adjustment quantity cannot be zero.")

            # Get repositories from factories
            prod_repo = self._get_repository(self.product_repo_factory, session)
            inv_repo = self._get_repository(self.inventory_repo_factory, session)

            product = prod_repo.get_by_id(product_id)
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

            # Update product stock - pass the change in quantity, not the new total
            prod_repo.update_stock(product_id, quantity)

            # Log the movement
            movement = InventoryMovement(
                product_id=product_id,
                quantity=quantity,
                movement_type="ADJUSTMENT",
                description=reason,
                user_id=user_id
            )
            inv_repo.add_movement(movement)

            # Update local product object for return
            product.quantity_in_stock = new_quantity

            return product
            
        return self._with_session(_adjust_inventory, product_id, quantity, reason, user_id)

    def decrease_stock_for_sale(
        self,
        product_id: int,
        quantity: Decimal,
        sale_id: int,
        user_id: Optional[int] = None,
        session: Optional[Session] = None
    ) -> None:
        """
        Decreases stock for a sold item.
        
        Args:
            product_id: The ID of the product
            quantity: The quantity to decrease (positive value)
            sale_id: The ID of the sale
            user_id: Optional user ID
            session: Optional session to use (for transaction sharing)
        """
        def _decrease_stock_for_sale(session, product_id, quantity, sale_id, user_id):
            if quantity <= 0:
                raise ValueError("Quantity for sale must be positive.")

            # Get repositories from factories
            prod_repo = self._get_repository(self.product_repo_factory, session)
            inv_repo = self._get_repository(self.inventory_repo_factory, session)

            product = prod_repo.get_by_id(product_id)
            if not product:
                raise ValueError(f"Product with ID {product_id} not found for sale item.")
            if not product.uses_inventory:
                raise ValueError(f"Product {product.code} does not use inventory control but was included in sale {sale_id}.")

            # Ensure quantity_in_stock is Decimal before comparison/subtraction
            current_stock = Decimal('0.0')  # Initialize as Decimal
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

            # Update stock - pass the negative quantity as change
            prod_repo.update_stock(product_id, -quantity)

            # Log movement
            movement = InventoryMovement(
                product_id=product_id,
                quantity=-quantity,
                movement_type="SALE",
                description=f"Venta #{sale_id}",
                related_id=sale_id,
                user_id=user_id
            )
            inv_repo.add_movement(movement)
        
        # If session is provided, use it directly; otherwise use _with_session
        if session:
            return _decrease_stock_for_sale(session, product_id, quantity, sale_id, user_id)
        else:
            return self._with_session(_decrease_stock_for_sale, product_id, quantity, sale_id, user_id)

    # --- Reporting Methods ---

    def get_inventory_report(self) -> List[Product]:
        """Retrieves a general inventory report (all products with stock)."""
        def _get_inventory_report(session):
            prod_repo = self._get_repository(self.product_repo_factory, session)
            return prod_repo.get_all()
            
        return self._with_session(_get_inventory_report)

    def get_low_stock_products(self) -> List[Product]:
        """Retrieves products below their minimum stock level."""
        def _get_low_stock_products(session):
            prod_repo = self._get_repository(self.product_repo_factory, session)
            return prod_repo.get_low_stock()
            
        return self._with_session(_get_low_stock_products)

    def get_inventory_movements(self, product_id: Optional[int] = None) -> List[InventoryMovement]:
        """Retrieves inventory movements, optionally filtered by product."""
        def _get_inventory_movements(session, product_id):
            inv_repo = self._get_repository(self.inventory_repo_factory, session)
            if product_id:
                return inv_repo.get_movements_for_product(product_id)
            else:
                return inv_repo.get_all_movements()
                
        return self._with_session(_get_inventory_movements, product_id) 