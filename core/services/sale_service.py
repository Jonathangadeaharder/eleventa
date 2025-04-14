from decimal import Decimal
from typing import List, Dict, Any, Optional
import os
from datetime import datetime

# Interfaces
from core.interfaces.repository_interfaces import (
    ISaleRepository, IProductRepository, ICustomerRepository
)
from core.services.inventory_service import InventoryService
from core.services.customer_service import CustomerService

# Models
from core.models.sale import Sale, SaleItem
from core.models.product import Product
from core.models.customer import Customer

# Persistence Utils
from infrastructure.persistence.utils import session_scope
from sqlalchemy.orm import Session

# Import config for store info
from config import Config

# Import receipt builder
from infrastructure.reporting.receipt_builder import generate_receipt_pdf as create_receipt_pdf

class SaleService:
    """Service layer for handling sales business logic."""

    def __init__(
        self,
        sale_repository: ISaleRepository,
        product_repository: IProductRepository,
        inventory_service: InventoryService,
        customer_service: CustomerService
    ):
        self.sale_repository = sale_repository
        self.product_repository = product_repository
        self.inventory_service = inventory_service
        self.customer_service = customer_service

    def create_sale(
        self,
        items_data: List[Dict[str, Any]],
        user_id: Optional[int], # Added user_id
        payment_type: Optional[str], # Added payment_type
        customer_id: Optional[int] = None,
        is_credit_sale: bool = False # Keep this for credit logic
    ) -> Sale:
        """
        Creates a new sale, saves it, updates inventory, and potentially customer balance.

        Args:
            items_data: List of item dictionaries ({'product_id', 'quantity'}).
            customer_id: Optional ID of the customer making the purchase.
            is_credit_sale: Flag indicating if the sale is on credit.

        Returns:
            The created Sale object.

        Raises:
            ValueError: If validation fails.
        """
        if not items_data:
            raise ValueError("Cannot create a sale with no items.")
        if is_credit_sale and not customer_id:
            raise ValueError("A customer ID must be provided for credit sales.")
        if not is_credit_sale and not payment_type:
            raise ValueError("Payment type must be provided for non-credit sales.")
        # Optional: Validate payment_type against a predefined list
        # allowed_payment_types = ['Efectivo', 'Tarjeta', 'Otro'] # Example
        # if not is_credit_sale and payment_type not in allowed_payment_types:
        #     raise ValueError(f"Invalid payment type: {payment_type}")
        if user_id is None: # Assuming user must be logged in to make a sale
             raise ValueError("User ID must be provided to create a sale.")

        sale_items_raw: List[Dict] = []
        product_ids_to_fetch = set()

        for item_data in items_data:
            product_id = item_data.get('product_id')
            quantity_str = item_data.get('quantity')
            if not product_id or quantity_str is None:
                raise ValueError(f"Missing 'product_id' or 'quantity' in item data: {item_data}")
            try:
                quantity = Decimal(str(quantity_str))
            except Exception:
                raise ValueError(f"Invalid quantity format '{quantity_str}' for product ID {product_id}.")
            if quantity <= 0:
                raise ValueError(f"Sale quantity must be positive for product ID {product_id}.")
            product_ids_to_fetch.add(product_id)
            sale_items_raw.append({
                'product_id': product_id,
                'quantity': quantity,
            })

        with session_scope() as session:
            product_repo_tx = self.product_repository
            sale_repo_tx = self.sale_repository

            customer: Optional[Customer] = None
            if customer_id:
                customer = self.customer_service.get_customer_by_id(customer_id)
                if not customer:
                    raise ValueError(f"Customer with ID {customer_id} not found.")

            fetched_products: Dict[int, Product] = {}
            for pid in product_ids_to_fetch:
                product = product_repo_tx.get_by_id(pid)
                if not product:
                    raise ValueError(f"Product with ID {pid} not found.")
                fetched_products[pid] = product

            final_sale_items: List[SaleItem] = []
            sale_total = Decimal(0)
            for item_raw in sale_items_raw:
                product = fetched_products[item_raw['product_id']]
                item = SaleItem(
                    product_id=product.id,
                    quantity=item_raw['quantity'],
                    unit_price=Decimal(str(product.sell_price)),
                    product_code=product.code,
                    product_description=product.description
                )
                final_sale_items.append(item)
                sale_total += item.subtotal

            sale_to_add = Sale(
                items=final_sale_items,
                customer_id=customer_id,
                is_credit_sale=is_credit_sale,
                user_id=user_id, # Pass user_id
                payment_type=payment_type if not is_credit_sale else 'Crédito' # Pass payment_type or set to 'Crédito'
            )
            # Ensure the repository handles saving these new fields
            created_sale = sale_repo_tx.add_sale(sale_to_add)

            for sold_item in created_sale.items:
                product = fetched_products[sold_item.product_id]
                if product.uses_inventory:
                    self.inventory_service.decrease_stock_for_sale(
                        session=session,
                        product_id=sold_item.product_id,
                        quantity=float(sold_item.quantity),
                        sale_id=created_sale.id,
                    )

            if created_sale.is_credit_sale and created_sale.customer_id:
                self.customer_service.increase_customer_debt(
                    session=session,
                    customer_id=created_sale.customer_id,
                    amount=sale_total
                )

            return created_sale

    def get_sale_by_id(self, sale_id: int) -> Optional[Sale]:
        """
        Retrieves a sale by its ID.
        
        Args:
            sale_id: The ID of the sale to retrieve
            
        Returns:
            The Sale object if found, None otherwise
        """
        with session_scope() as session:
            sale_repo = self.sale_repository
            return sale_repo.get_by_id(sale_id)
            
    def generate_receipt_pdf(self, sale_id: int, filename: Optional[str] = None) -> str:
        """
        Generates a PDF receipt for a sale.
        
        Args:
            sale_id: The ID of the sale to generate a receipt for
            filename: Optional filename to use for the PDF, if not provided a default name will be used
            
        Returns:
            The path to the generated PDF file
            
        Raises:
            ValueError: If the sale is not found
        """
        # Retrieve the sale
        sale = self.get_sale_by_id(sale_id)
        if not sale:
            raise ValueError(f"Sale with ID {sale_id} not found.")
            
        # Get user name if available
        user_name = None
        if sale.user_id:
            # In a real implementation, we would get the user name from a user service
            # For now, we'll use a placeholder
            user_name = f"Usuario {sale.user_id}"
            
        # Enhance sale with user name
        sale.user_name = user_name
        
        # Get customer name if available
        customer_name = None
        if sale.customer_id:
            customer = self.customer_service.get_customer_by_id(sale.customer_id)
            if customer:
                customer_name = customer.name
                
        # Enhance sale with customer name
        sale.customer_name = customer_name
        
        # Create a base directory for receipts if it doesn't exist
        receipts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "receipts")
        os.makedirs(receipts_dir, exist_ok=True)
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = os.path.join(receipts_dir, f"receipt_sale_{sale_id}_{timestamp}.pdf")
            
        # Get store information from config
        store_info = {
            'name': Config.STORE_NAME,
            'address': Config.STORE_ADDRESS,
            'tax_id': Config.STORE_CUIT,
            'iva_condition': Config.STORE_IVA_CONDITION,
            'phone': getattr(Config, 'STORE_PHONE', '')  # Optional phone field
        }
        
        # Call the receipt builder function
        return create_receipt_pdf(sale, store_info, filename)
