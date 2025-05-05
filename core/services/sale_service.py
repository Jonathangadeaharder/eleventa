import os
from sqlalchemy.orm import Session
from typing import Callable, Dict, Any, List, Optional, TypeVar, Type
from core.utils import session_scope  # Updated import path
from core.models.sale import Sale, SaleItem  # Import SaleItem as well
from core.interfaces.repository_interfaces import ISaleRepository, IProductRepository, ICustomerRepository
from decimal import Decimal
import uuid
from datetime import datetime

class SaleService:
    def __init__(self, sale_repo_factory: Callable[[], ISaleRepository], product_repo_factory: Callable[[], IProductRepository], customer_repo_factory: Callable[[], ICustomerRepository], inventory_service, customer_service):
        self.sale_repo_factory = sale_repo_factory
        self.product_repo_factory = product_repo_factory
        self.customer_repo_factory = customer_repo_factory
        self.inventory_service = inventory_service
        self.customer_service = customer_service

    def create_sale(self, items_data: List[Dict[str, Any]], user_id: int, payment_type: Optional[str] = None, customer_id: Optional[int] = None, is_credit_sale: bool = False, session: Optional[Session] = None) -> Sale:
        """Create a new sale with the given items and parameters."""
        # Convert item dictionaries to SaleItem objects
        sale_items = []
        for item_data in items_data:
            # Get product details if not provided
            product_id = item_data["product_id"]
            quantity = item_data["quantity"]
            
            # Handle case where only product_id and quantity are provided
            if "product_code" not in item_data or "product_description" not in item_data or "unit_price" not in item_data:
                # Fetch product from repository to get missing details
                product_repo = self.product_repo_factory(session) if session else self.product_repo_factory()
                product = product_repo.get_by_id(product_id)
                if product:
                    product_code = product.code
                    product_description = product.description
                    unit_price = product.sell_price
                else:
                    # Fallback values if product not found
                    product_code = f"PROD-{product_id}"
                    product_description = f"Product {product_id}"
                    unit_price = 0.0
            else:
                # Use provided values
                product_code = item_data["product_code"]
                product_description = item_data["product_description"]
                unit_price = item_data["unit_price"]
            
            sale_item = SaleItem(
                product_id=product_id,
                product_code=product_code,
                product_description=product_description,
                quantity=quantity,
                unit_price=unit_price
            )
            sale_items.append(sale_item)
        
        # Create the sale object with the SaleItem objects
        sale = Sale(
            items=sale_items,
            user_id=user_id,
            payment_type=payment_type,
            customer_id=customer_id,
            is_credit_sale=is_credit_sale
        )
        
        if session:
            sale_repo = self.sale_repo_factory(session)
            return sale_repo.add_sale(sale)
        else:
            with session_scope() as new_session:
                sale_repo = self.sale_repo_factory(new_session)
                return sale_repo.add_sale(sale)

    def get_sale(self, sale_id: int) -> Sale:
        with session_scope() as session:
            return self.sale_repo_factory().get_by_id(session, sale_id)

    def update_sale(self, sale_id: int, update_data: dict) -> Sale:
        with session_scope() as session:
            sale = self.sale_repo_factory().get_by_id(session, sale_id)
            if sale:
                return self.sale_repo_factory().update(session, sale, update_data)
            return None

    def delete_sale(self, sale_id: int) -> bool:
        with session_scope() as session:
            sale = self.sale_repo_factory().get_by_id(session, sale_id)
            if sale:
                return self.sale_repo_factory().delete(session, sale_id)
            return False

    def generate_receipt_pdf(self, sale_id: int, output_dir: str) -> str:
        """Generate a PDF receipt for a sale and return the file path."""
        with session_scope() as session:
            sale = self.sale_repo_factory().get_by_id(session, sale_id)
            if not sale:
                raise ValueError(f"Sale with ID {sale_id} not found")
            
            filename = f"receipt_{sale_id}.pdf"
            file_path = os.path.join(output_dir, filename)
            
            create_receipt_pdf(sale, file_path)
            return file_path

def create_receipt_pdf(sale: Sale, filename: str) -> None:
    """Generate a PDF receipt for the given sale and save it to the specified filename."""
    # Implementation would go here
    pass
