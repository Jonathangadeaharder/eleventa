from typing import List, Optional, Any, Dict
from decimal import Decimal
from datetime import datetime

from core.models.inventory import InventoryMovement
from core.models.product import Product
from core.services.service_base import ServiceBase
from infrastructure.persistence.unit_of_work import UnitOfWork, unit_of_work

class InventoryService(ServiceBase):
    """Provides services related to inventory management."""

    def __init__(self):
        """
        Initialize the inventory service.
        """
        super().__init__()  # Initialize base class with default logger

    def add_inventory(
        self,
        product_id: int,
        quantity: Decimal,
        new_cost_price: Optional[Decimal] = None,
        notes: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Product:
        """Adds quantity to a product's stock, logs movement, and optionally updates cost price."""
        with unit_of_work() as uow:
            if quantity <= 0:
                raise ValueError("Quantity must be positive.")

            product = uow.products.get_by_id(product_id)
            if not product:
                raise ValueError(f"Product with ID {product_id} not found.")
            if not product.uses_inventory:
                raise ValueError(f"Product {product.code} does not use inventory control.")

            # Ensure quantity_in_stock is Decimal before adding
            current_stock = product.quantity_in_stock if isinstance(product.quantity_in_stock, Decimal) else Decimal(str(product.quantity_in_stock))
            new_quantity = current_stock + quantity

            # Update product stock (and cost if provided)
            uow.products.update_stock(product_id, quantity, new_cost_price)  # Pass quantity change, not new total

            # Log the movement
            movement = InventoryMovement(
                product_id=product_id,
                quantity=quantity,
                movement_type="PURCHASE",
                description=notes,
                user_id=user_id
            )
            uow.inventory.add_movement(movement)

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
        with unit_of_work() as uow:
            if quantity == 0:
                raise ValueError("Adjustment quantity cannot be zero.")

            product = uow.products.get_by_id(product_id)
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
            uow.products.update_stock(product_id, quantity)

            # Log the movement
            movement = InventoryMovement(
                product_id=product_id,
                quantity=quantity,
                movement_type="ADJUSTMENT",
                description=reason,
                user_id=user_id
            )
            uow.inventory.add_movement(movement)

            # Update local product object for return
            product.quantity_in_stock = new_quantity

            return product

    def decrease_stock_for_sale(
        self,
        product_id: int,
        quantity: Decimal,
        sale_id: int,
        user_id: Optional[int] = None
    ) -> None:
        """
        Decreases stock for a sold item.
        
        Args:
            product_id: The ID of the product
            quantity: The quantity to decrease (positive value)
            sale_id: The ID of the sale
            user_id: Optional user ID
        """
        with unit_of_work() as uow:
            if quantity <= 0:
                raise ValueError("Quantity for sale must be positive.")

            product = uow.products.get_by_id(product_id)
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
            uow.products.update_stock(product_id, -quantity)

            # Log movement
            movement = InventoryMovement(
                product_id=product_id,
                quantity=-quantity,
                movement_type="SALE",
                description=f"Venta #{sale_id}",
                related_id=sale_id,
                user_id=user_id
            )
            uow.inventory.add_movement(movement)

    # --- Reporting Methods ---

    def get_inventory_report(self) -> List[Dict[str, Any]]:
        """Returns a comprehensive inventory report."""
        with unit_of_work() as uow:
            return uow.products.get_inventory_report()

    def get_low_stock_products(self, threshold: Decimal = Decimal('10')) -> List[Product]:
        """Returns products with stock below the specified threshold."""
        with unit_of_work() as uow:
            return uow.products.get_low_stock_products(threshold)

    def get_inventory_movements(
        self,
        product_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        movement_type: Optional[str] = None
    ) -> List[InventoryMovement]:
        """Returns inventory movements with optional filters."""
        with unit_of_work() as uow:
            return uow.inventory.get_movements(
                product_id=product_id,
                start_date=start_date,
                end_date=end_date,
                movement_type=movement_type
            )