import os
from sqlalchemy.orm import Session
from typing import Callable, Dict, Any, List, Optional, TypeVar, Type
from core.utils import session_scope  # Updated import path
from core.models.sale import Sale
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
        sale_data = {
            'items': items_data,
            'user_id': user_id,
            'payment_type': payment_type,
            'customer_id': customer_id,
            'is_credit_sale': is_credit_sale
        }
        if session:
            return self.sale_repo_factory().create(session, sale_data)
        with session_scope() as session:
            return self.sale_repo_factory().create(session, sale_data)

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
