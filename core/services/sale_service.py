import os
from typing import Dict, Any, List, Optional
from decimal import Decimal
import uuid
from datetime import datetime

from core.services.service_base import ServiceBase
from infrastructure.persistence.unit_of_work import UnitOfWork, unit_of_work
from core.models.sale import Sale, SaleItem
from infrastructure.reporting.document_generator import DocumentPdfGenerator

class SaleService(ServiceBase):
    def __init__(self, inventory_service, customer_service):
        """
        Initialize with related services.
        
        Args:
            inventory_service: Service for inventory operations
            customer_service: Service for customer operations
        """
        super().__init__()  # Initialize base class with default logger
        self.inventory_service = inventory_service
        self.customer_service = customer_service
        self.document_generator = DocumentPdfGenerator()

    def create_sale(self, items_data: List[Dict[str, Any]], user_id: int, 
                   payment_type: Optional[str] = None, customer_id: Optional[int] = None, 
                   is_credit_sale: bool = False) -> Sale:
        """Create a new sale with the given items and parameters."""
        with unit_of_work() as uow:
            # Convert item dictionaries to SaleItem objects
            sale_items = []
            for item_data in items_data:
                # Get product details if not provided
                product_id = item_data["product_id"]
                quantity = item_data["quantity"]
                
                # Handle case where only product_id and quantity are provided
                if "product_code" not in item_data or "product_description" not in item_data or "unit_price" not in item_data:
                    # Fetch product from repository to get missing details
                    product = uow.products.get_by_id(product_id)
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
            
            return uow.sales.add_sale(sale)

    def get_sale_by_id(self, sale_id: int) -> Optional[Sale]:
        """Get a sale by its ID. Returns None if not found."""
        with unit_of_work() as uow:
            return uow.sales.get_by_id(sale_id)

    def assign_customer_to_sale(self, sale_id: int, customer_id: int) -> bool:
        """Assign a customer to an existing sale. Returns True if successful."""
        with unit_of_work() as uow:
            sale = uow.sales.get_by_id(sale_id)
            if sale:
                # Assume update method exists in repository
                update_data = {"customer_id": customer_id}
                uow.sales.update(sale_id, update_data)
                return True
            return False

    def update_sale(self, sale_id: int, update_data: dict) -> Sale:
        """Update a sale."""
        with unit_of_work() as uow:
            sale = uow.sales.get_by_id(sale_id)
            if sale:
                # Assume update method exists in repository
                return uow.sales.update(sale_id, update_data)
            return None

    def delete_sale(self, sale_id: int) -> bool:
        """Delete a sale by ID."""
        with unit_of_work() as uow:
            sale = uow.sales.get_by_id(sale_id)
            if sale:
                return uow.sales.delete(sale_id)
            return False

    def generate_receipt_pdf(self, sale_id: int, output_dir: str) -> str:
        """Generate a PDF receipt for a sale and return the file path."""
        with unit_of_work() as uow:
            sale = uow.sales.get_by_id(sale_id)
            if not sale:
                raise ValueError(f"Sale with ID {sale_id} not found")
                
            if not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir)
                    self.logger.info(f"Created output directory: {output_dir}")
                except OSError as e:
                    self.logger.error(f"Error creating output directory {output_dir}: {e}")
                    raise
                    
            filename = f"receipt_{sale_id}.pdf"
            file_path = os.path.join(output_dir, filename)
                
            success = self.document_generator.generate_receipt_from_sale(sale, file_path)
            if not success:
                raise RuntimeError(f"Failed to generate receipt PDF for sale {sale_id}")
            return file_path

    def generate_presupuesto_pdf(self, items_data: List[Any], total_amount: Decimal, 
                                 output_dir: str, customer_name: Optional[str] = None, 
                                 user_name: Optional[str] = None) -> str:
        """Generate a PDF for a 'Presupuesto' (Quote) and return the file path."""
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
                self.logger.info(f"Created output directory: {output_dir}")
            except OSError as e:
                self.logger.error(f"Error creating output directory {output_dir}: {e}")
                raise  # Re-raise the exception if directory creation fails

        presupuesto_uuid = str(uuid.uuid4())[:8] # Short UUID for ID
        filename = f"presupuesto_{presupuesto_uuid}.pdf"
        file_path = os.path.join(output_dir, filename)
        
        try:
            success = self.document_generator.generate_presupuesto_content(
                filename=file_path, 
                items=items_data, 
                total_amount=total_amount,
                customer_name=customer_name,
                user_name=user_name,
                presupuesto_id=presupuesto_uuid
            )
            if not success:
                raise RuntimeError(f"Failed to generate presupuesto PDF {file_path}")
            self.logger.info(f"Presupuesto PDF generated: {file_path}")
            return file_path
        except Exception as e:
            self.logger.error(f"Failed to generate presupuesto PDF {file_path}: {e}")
            # Depending on desired behavior, could re-raise or return None/error indicator
            raise # Re-raise to let the caller (UI) handle the error message
