"""Examples demonstrating how to use the Unit of Work pattern.

This module shows how to refactor existing services to use the Unit of Work pattern
for better transaction management and cleaner code when dealing with multiple
repository operations.
"""

from typing import List, Optional
from decimal import Decimal
import logging
from datetime import datetime

from core.models.product import Product
from core.models.sale import Sale, SaleItem
from core.models.inventory import InventoryMovement
from core.models.customer import Customer
from infrastructure.persistence.unit_of_work import UnitOfWork, unit_of_work
from core.services.service_base import ServiceBase


class ProductServiceWithUoW(ServiceBase):
    """Example of ProductService refactored to use Unit of Work pattern.
    
    This demonstrates how to simplify service methods by using the Unit of Work
    pattern instead of managing sessions manually.
    """
    
    def __init__(self):
        """Initialize the service."""
        super().__init__()
    
    def add_product(self, product_data: Product) -> Product:
        """Adds a new product using Unit of Work pattern."""
        with unit_of_work() as uow:
            # Validate product code uniqueness
            existing = uow.products.get_by_code(product_data.code)
            if existing:
                raise ValueError(f"Product code '{product_data.code}' already exists.")
            
            # Validate department exists if specified
            if product_data.department_id:
                department = uow.departments.get_by_id(product_data.department_id)
                if not department:
                    raise ValueError(f"Department with ID {product_data.department_id} not found.")
            
            self.logger.info(f"Adding product with code: {product_data.code}")
            return uow.products.add(product_data)
            # Transaction is automatically committed on successful exit
    
    def update_product_with_inventory_adjustment(self, product_id: int, 
                                                new_data: Product, 
                                                stock_adjustment: Optional[Decimal] = None) -> Product:
        """Complex operation: Update product and adjust inventory in a single transaction.
        
        This demonstrates the power of Unit of Work for operations that span multiple repositories.
        """
        with unit_of_work() as uow:
            # Get existing product
            existing_product = uow.products.get_by_id(product_id)
            if not existing_product:
                raise ValueError(f"Product with ID {product_id} not found")
            
            # Validate new data
            if new_data.code != existing_product.code:
                existing_by_code = uow.products.get_by_code(new_data.code)
                if existing_by_code and existing_by_code.id != product_id:
                    raise ValueError(f"Code '{new_data.code}' already exists for another product")
            
            # Update product
            updated_product = uow.products.update(new_data)
            
            # Create inventory movement if stock adjustment is needed
            if stock_adjustment and stock_adjustment != 0:
                movement = InventoryMovement(
                    product_id=product_id,
                    movement_type="adjustment",
                    quantity=stock_adjustment,
                    cost_price=updated_product.cost_price,
                    notes=f"Stock adjustment during product update",
                    movement_date=datetime.now()
                )
                uow.inventory.add(movement)
                
                # Update product stock
                new_stock = (existing_product.quantity_in_stock or Decimal('0')) + stock_adjustment
                updated_product.quantity_in_stock = new_stock
                updated_product = uow.products.update(updated_product)
            
            self.logger.info(f"Updated product {product_id} with inventory adjustment: {stock_adjustment}")
            return updated_product
            # All changes are committed together or rolled back if any operation fails
    
    def transfer_products_between_departments(self, product_ids: List[int], 
                                            new_department_id: int) -> List[Product]:
        """Transfer multiple products to a new department in a single transaction."""
        with unit_of_work() as uow:
            # Validate department exists
            department = uow.departments.get_by_id(new_department_id)
            if not department:
                raise ValueError(f"Department with ID {new_department_id} not found")
            
            updated_products = []
            for product_id in product_ids:
                product = uow.products.get_by_id(product_id)
                if not product:
                    raise ValueError(f"Product with ID {product_id} not found")
                
                product.department_id = new_department_id
                updated_product = uow.products.update(product)
                updated_products.append(updated_product)
            
            self.logger.info(f"Transferred {len(product_ids)} products to department {new_department_id}")
            return updated_products
            # All product updates are committed together


class SalesServiceWithUoW(ServiceBase):
    """Example of a sales service using Unit of Work for complex operations."""
    
    def __init__(self):
        super().__init__()
    
    def process_sale_with_inventory_update(self, sale_data: Sale, 
                                         sale_items: List[SaleItem]) -> Sale:
        """Process a sale and update inventory in a single transaction.
        
        This is a perfect example of why Unit of Work is beneficial - it ensures
        that either the entire sale is processed (including inventory updates)
        or nothing happens if any step fails.
        """
        with unit_of_work() as uow:
            # Validate customer exists if specified
            if sale_data.customer_id:
                customer = uow.customers.get_by_id(sale_data.customer_id)
                if not customer:
                    raise ValueError(f"Customer with ID {sale_data.customer_id} not found")
            
            # Validate products and check stock availability
            for item in sale_items:
                product = uow.products.get_by_id(item.product_id)
                if not product:
                    raise ValueError(f"Product with ID {item.product_id} not found")
                
                if product.uses_inventory:
                    available_stock = product.quantity_in_stock or Decimal('0')
                    if available_stock < item.quantity:
                        raise ValueError(
                            f"Insufficient stock for product {product.code}. "
                            f"Available: {available_stock}, Required: {item.quantity}"
                        )
            
            # Create the sale
            created_sale = uow.sales.add(sale_data)
            
            # Add sale items and update inventory
            for item in sale_items:
                item.sale_id = created_sale.id
                uow.sales.add_sale_item(item)
                
                # Update product inventory
                product = uow.products.get_by_id(item.product_id)
                if product.uses_inventory:
                    # Create inventory movement
                    movement = InventoryMovement(
                        product_id=item.product_id,
                        movement_type="sale",
                        quantity=-item.quantity,  # Negative for outgoing
                        cost_price=product.cost_price,
                        reference_id=str(created_sale.id),
                        notes=f"Sale #{created_sale.id}",
                        movement_date=created_sale.sale_date
                    )
                    uow.inventory.add(movement)
                    
                    # Update product stock
                    new_stock = (product.quantity_in_stock or Decimal('0')) - item.quantity
                    product.quantity_in_stock = new_stock
                    uow.products.update(product)
            
            self.logger.info(f"Processed sale {created_sale.id} with {len(sale_items)} items")
            return created_sale
            # All operations are committed together
    
    def refund_sale(self, sale_id: int, refund_items: List[dict]) -> Sale:
        """Process a partial or full refund, restoring inventory.
        
        Args:
            sale_id: ID of the original sale
            refund_items: List of dicts with 'product_id' and 'quantity' to refund
        """
        with unit_of_work() as uow:
            # Get original sale
            original_sale = uow.sales.get_by_id(sale_id)
            if not original_sale:
                raise ValueError(f"Sale with ID {sale_id} not found")
            
            # Validate refund items against original sale
            original_items = uow.sales.get_sale_items(sale_id)
            original_items_dict = {item.product_id: item.quantity for item in original_items}
            
            for refund_item in refund_items:
                product_id = refund_item['product_id']
                refund_qty = refund_item['quantity']
                
                if product_id not in original_items_dict:
                    raise ValueError(f"Product {product_id} was not in original sale")
                
                if refund_qty > original_items_dict[product_id]:
                    raise ValueError(
                        f"Cannot refund {refund_qty} of product {product_id}. "
                        f"Original quantity was {original_items_dict[product_id]}"
                    )
            
            # Create refund sale (negative amounts)
            refund_sale_data = Sale(
                customer_id=original_sale.customer_id,
                sale_date=datetime.now(),
                total_amount=-sum(item['quantity'] * original_items_dict[item['product_id']] 
                                for item in refund_items),  # Simplified calculation
                payment_method=original_sale.payment_method,
                notes=f"Refund for sale #{sale_id}"
            )
            
            refund_sale = uow.sales.add(refund_sale_data)
            
            # Process refund items and restore inventory
            for refund_item in refund_items:
                product_id = refund_item['product_id']
                refund_qty = refund_item['quantity']
                
                # Create refund sale item
                refund_sale_item = SaleItem(
                    sale_id=refund_sale.id,
                    product_id=product_id,
                    quantity=-refund_qty,  # Negative quantity for refund
                    unit_price=next(item.unit_price for item in original_items 
                                  if item.product_id == product_id)
                )
                uow.sales.add_sale_item(refund_sale_item)
                
                # Restore inventory
                product = uow.products.get_by_id(product_id)
                if product.uses_inventory:
                    # Create inventory movement
                    movement = InventoryMovement(
                        product_id=product_id,
                        movement_type="refund",
                        quantity=refund_qty,  # Positive for incoming
                        cost_price=product.cost_price,
                        reference_id=str(refund_sale.id),
                        notes=f"Refund from sale #{sale_id}",
                        movement_date=refund_sale.sale_date
                    )
                    uow.inventory.add(movement)
                    
                    # Update product stock
                    new_stock = (product.quantity_in_stock or Decimal('0')) + refund_qty
                    product.quantity_in_stock = new_stock
                    uow.products.update(product)
            
            self.logger.info(f"Processed refund {refund_sale.id} for original sale {sale_id}")
            return refund_sale
            # All refund operations are committed together


# Example of using Unit of Work directly (without service class)
def bulk_price_update(product_ids: List[int], price_increase_percentage: Decimal):
    """Example of a standalone function using Unit of Work.
    
    Updates prices for multiple products in a single transaction.
    """
    with UnitOfWork() as uow:
        updated_count = 0
        
        for product_id in product_ids:
            product = uow.products.get_by_id(product_id)
            if product:
                # Calculate new prices
                multiplier = 1 + (price_increase_percentage / 100)
                
                if product.sell_price:
                    product.sell_price = product.sell_price * multiplier
                if product.wholesale_price:
                    product.wholesale_price = product.wholesale_price * multiplier
                if product.special_price:
                    product.special_price = product.special_price * multiplier
                
                uow.products.update(product)
                updated_count += 1
        
        logging.info(f"Updated prices for {updated_count} products with {price_increase_percentage}% increase")
        return updated_count
        # All price updates are committed together


# Example of manual transaction control
def complex_operation_with_manual_control():
    """Example showing manual commit/rollback control within Unit of Work."""
    with UnitOfWork() as uow:
        try:
            # First phase: Create some products
            product1 = Product(code="TEST001", description="Test Product 1", sell_price=Decimal('10.00'))
            product2 = Product(code="TEST002", description="Test Product 2", sell_price=Decimal('20.00'))
            
            created_product1 = uow.products.add(product1)
            created_product2 = uow.products.add(product2)
            
            # Commit first phase
            uow.commit()
            
            # Second phase: Try to create a department
            # This might fail due to business rules
            department = uow.departments.add(Department(name="Test Department"))
            
            # Update products with new department
            created_product1.department_id = department.id
            created_product2.department_id = department.id
            
            uow.products.update(created_product1)
            uow.products.update(created_product2)
            
            # If we reach here, everything succeeded
            # Final commit happens automatically on context exit
            
        except Exception as e:
            # If anything in the second phase fails, we can rollback
            # but the first phase changes are already committed
            logging.error(f"Error in second phase: {e}")
            uow.rollback()
            raise