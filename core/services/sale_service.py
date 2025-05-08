import os
from sqlalchemy.orm import Session
from typing import Callable, Dict, Any, List, Optional, TypeVar, Type
from decimal import Decimal
import uuid
from datetime import datetime

from core.services.service_base import ServiceBase
from infrastructure.persistence.utils import session_scope
from core.models.sale import Sale, SaleItem
from core.interfaces.repository_interfaces import ISaleRepository, IProductRepository, ICustomerRepository

class SaleService(ServiceBase):
    def __init__(self, 
                 sale_repo_factory: Callable[[Session], ISaleRepository], 
                 product_repo_factory: Callable[[Session], IProductRepository], 
                 customer_repo_factory: Callable[[Session], ICustomerRepository], 
                 inventory_service, 
                 customer_service):
        """
        Initialize with repository factories and related services.
        
        Args:
            sale_repo_factory: Factory function to create sale repository
            product_repo_factory: Factory function to create product repository
            customer_repo_factory: Factory function to create customer repository
            inventory_service: Service for inventory operations
            customer_service: Service for customer operations
        """
        super().__init__()  # Initialize base class with default logger
        self.sale_repo_factory = sale_repo_factory
        self.product_repo_factory = product_repo_factory
        self.customer_repo_factory = customer_repo_factory
        self.inventory_service = inventory_service
        self.customer_service = customer_service

    def create_sale(self, items_data: List[Dict[str, Any]], user_id: int, 
                   payment_type: Optional[str] = None, customer_id: Optional[int] = None, 
                   is_credit_sale: bool = False, session: Optional[Session] = None) -> Sale:
        """Create a new sale with the given items and parameters."""
        def _create_sale(session, items_data, user_id, payment_type, customer_id, is_credit_sale):
            # Get repositories from factories
            product_repo = self._get_repository(self.product_repo_factory, session)
            sale_repo = self._get_repository(self.sale_repo_factory, session)
            
            # Convert item dictionaries to SaleItem objects
            sale_items = []
            for item_data in items_data:
                # Get product details if not provided
                product_id = item_data["product_id"]
                quantity = item_data["quantity"]
                
                # Handle case where only product_id and quantity are provided
                if "product_code" not in item_data or "product_description" not in item_data or "unit_price" not in item_data:
                    # Fetch product from repository to get missing details
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
            
            return sale_repo.add_sale(sale)
            
        # If session is provided, use it directly; otherwise use _with_session
        if session:
            return _create_sale(session, items_data, user_id, payment_type, customer_id, is_credit_sale)
        else:
            return self._with_session(_create_sale, items_data, user_id, payment_type, customer_id, is_credit_sale)

    def get_sale(self, sale_id: int) -> Sale:
        """Get a sale by ID."""
        def _get_sale(session, sale_id):
            sale_repo = self._get_repository(self.sale_repo_factory, session)
            return sale_repo.get_by_id(sale_id)
            
        return self._with_session(_get_sale, sale_id)

    def update_sale(self, sale_id: int, update_data: dict) -> Sale:
        """Update a sale."""
        def _update_sale(session, sale_id, update_data):
            sale_repo = self._get_repository(self.sale_repo_factory, session)
            sale = sale_repo.get_by_id(sale_id)
            if sale:
                # Assume update method exists in repository
                return sale_repo.update(sale_id, update_data)
            return None
            
        return self._with_session(_update_sale, sale_id, update_data)

    def delete_sale(self, sale_id: int) -> bool:
        """Delete a sale by ID."""
        def _delete_sale(session, sale_id):
            sale_repo = self._get_repository(self.sale_repo_factory, session)
            sale = sale_repo.get_by_id(sale_id)
            if sale:
                return sale_repo.delete(sale_id)
            return False
            
        return self._with_session(_delete_sale, sale_id)

    def generate_receipt_pdf(self, sale_id: int, output_dir: str) -> str:
        """Generate a PDF receipt for a sale and return the file path."""
        def _generate_receipt_pdf(session, sale_id, output_dir):
            sale_repo = self._get_repository(self.sale_repo_factory, session)
            sale = sale_repo.get_by_id(sale_id)
            if not sale:
                raise ValueError(f"Sale with ID {sale_id} not found")
                
            filename = f"receipt_{sale_id}.pdf"
            file_path = os.path.join(output_dir, filename)
                
            create_receipt_pdf(sale, file_path)
            return file_path
            
        return self._with_session(_generate_receipt_pdf, sale_id, output_dir)

def create_receipt_pdf(sale: Sale, filename: str) -> None:
    """Generate a PDF receipt for the given sale and save it to the specified filename."""
    # Implementation would go here
    pass
