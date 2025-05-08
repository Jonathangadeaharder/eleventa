from typing import List, Optional, Dict, Tuple, Callable
from datetime import datetime
from decimal import Decimal
import logging
from sqlalchemy.orm import Session

# Adjust path if necessary
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from typing import List, Optional, Dict, Tuple, Callable # Added Callable
from datetime import datetime

# Adjust path if necessary
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlalchemy.orm import Session # Needed for type hint in factory

from core.interfaces.repository_interfaces import (
    IPurchaseOrderRepository, ISupplierRepository, IProductRepository
)
# Assuming an interface exists or using InventoryService directly
from core.services.inventory_service import InventoryService # Use concrete class if no interface
from core.models.purchase import PurchaseOrder, PurchaseOrderItem
from core.models.supplier import Supplier
from core.models.product import Product
from infrastructure.persistence.utils import session_scope # For transactions
from core.services.service_base import ServiceBase

class PurchaseService(ServiceBase):
    """Handles business logic related to purchase orders and suppliers."""

    # Type hints for repository factories: Callable[[Session], IRepositoryInterface]
    RepoFactory = Callable[[Session], any]

    def __init__(
        self,
        purchase_order_repo_factory: Callable[[Session], IPurchaseOrderRepository],
        supplier_repo_factory: Callable[[Session], ISupplierRepository],
        product_repo_factory: Callable[[Session], IProductRepository],
        inventory_service: InventoryService
    ):
        """
        Initialize with repository factories.
        
        Args:
            purchase_order_repo_factory: Factory function to create purchase order repository
            supplier_repo_factory: Factory function to create supplier repository
            product_repo_factory: Factory function to create product repository
            inventory_service: Service for inventory management
        """
        super().__init__()
        self.purchase_order_repo_factory = purchase_order_repo_factory
        self.supplier_repo_factory = supplier_repo_factory
        self.product_repo_factory = product_repo_factory
        self.inventory_service = inventory_service

    # --- Supplier Methods ---

    def add_supplier(self, supplier_data: Dict) -> Supplier:
        """Adds a new supplier after validation."""
        def _add_supplier(session, supplier_data):
            if not supplier_data.get('name'):
                raise ValueError("Supplier name is required.")

            supplier = Supplier(**supplier_data)
            
            # Get repository from factory
            supplier_repo = self._get_repository(self.supplier_repo_factory, session)
            
            # Check for duplicates
            if supplier_repo.get_by_name(supplier_data['name']):
                raise ValueError(f"Supplier with name '{supplier_data['name']}' already exists.")
            if supplier_data.get('cuit') and supplier_repo.get_by_cuit(supplier_data['cuit']):
                raise ValueError(f"Supplier with CUIT '{supplier_data['cuit']}' already exists.")

            added_supplier = supplier_repo.add(supplier)
            return added_supplier
            
        return self._with_session(_add_supplier, supplier_data)

    def update_supplier(self, supplier_id: int, supplier_data: Dict) -> Supplier:
        """Updates an existing supplier."""
        def _update_supplier(session, supplier_id, supplier_data):
            if not supplier_id:
                raise ValueError("Supplier ID is required for update.")

            # Get repository from factory
            supplier_repo = self._get_repository(self.supplier_repo_factory, session)
            
            supplier_to_update = supplier_repo.get_by_id(supplier_id)
            if not supplier_to_update:
                raise ValueError(f"Supplier with ID {supplier_id} not found.")

            # Check for potential duplicate name/CUIT conflicts (excluding self)
            if 'name' in supplier_data:
                existing_by_name = supplier_repo.get_by_name(supplier_data['name'])
                if existing_by_name and existing_by_name.id != supplier_id:
                    raise ValueError(f"Another supplier with name '{supplier_data['name']}' already exists.")
                supplier_to_update.name = supplier_data['name']

            if 'cuit' in supplier_data and supplier_data['cuit']:
                existing_by_cuit = supplier_repo.get_by_cuit(supplier_data['cuit'])
                if existing_by_cuit and existing_by_cuit.id != supplier_id:
                    raise ValueError(f"Another supplier with CUIT '{supplier_data['cuit']}' already exists.")
                supplier_to_update.cuit = supplier_data['cuit']

            # Update other fields
            supplier_to_update.contact_person = supplier_data.get('contact_person', supplier_to_update.contact_person)
            supplier_to_update.phone = supplier_data.get('phone', supplier_to_update.phone)
            supplier_to_update.email = supplier_data.get('email', supplier_to_update.email)
            supplier_to_update.address = supplier_data.get('address', supplier_to_update.address)
            supplier_to_update.notes = supplier_data.get('notes', supplier_to_update.notes)

            # Call update on the repository
            updated_supplier = supplier_repo.update(supplier_to_update)
            if not updated_supplier:
                raise RuntimeError(f"Failed to update supplier {supplier_id}")
            return updated_supplier
            
        return self._with_session(_update_supplier, supplier_id, supplier_data)

    def delete_supplier(self, supplier_id: int) -> bool:
        """Deletes a supplier."""
        def _delete_supplier(session, supplier_id):
            # Get repositories from factories
            supplier_repo = self._get_repository(self.supplier_repo_factory, session)
            po_repo = self._get_repository(self.purchase_order_repo_factory, session)

            # Check for related POs
            related_pos = po_repo.get_all(supplier_id=supplier_id)
            if any(po.status not in ["RECEIVED", "CANCELLED"] for po in related_pos):
                raise ValueError("Cannot delete supplier with active or pending purchase orders.")

            return supplier_repo.delete(supplier_id)
            
        return self._with_session(_delete_supplier, supplier_id)

    def find_suppliers(self, query: str = "") -> List[Supplier]:
        """Finds suppliers by name, contact, CUIT, etc."""
        def _find_suppliers(session, query):
            supplier_repo = self._get_repository(self.supplier_repo_factory, session)
            if not query:
                return supplier_repo.get_all()
            else:
                return supplier_repo.search(query)
                
        return self._with_session(_find_suppliers, query)

    def get_supplier_by_id(self, supplier_id: int) -> Optional[Supplier]:
        """Gets a supplier by ID."""
        def _get_supplier_by_id(session, supplier_id):
            supplier_repo = self._get_repository(self.supplier_repo_factory, session)
            return supplier_repo.get_by_id(supplier_id)
            
        return self._with_session(_get_supplier_by_id, supplier_id)

    # --- Purchase Order Methods ---

    def create_purchase_order(self, po_data: Dict) -> PurchaseOrder:
        """Creates a new purchase order."""
        def _create_purchase_order(session, po_data):
            supplier_id = po_data.get('supplier_id')
            items_data = po_data.get('items', [])

            if not supplier_id:
                raise ValueError("Supplier ID is required.")
            if not items_data:
                raise ValueError("Purchase order must contain at least one item.")

            # Get repositories from factories
            supplier_repo = self._get_repository(self.supplier_repo_factory, session)
            product_repo = self._get_repository(self.product_repo_factory, session)
            purchase_order_repo = self._get_repository(self.purchase_order_repo_factory, session)

            supplier = supplier_repo.get_by_id(supplier_id)
            if not supplier:
                raise ValueError(f"Supplier with ID {supplier_id} not found.")

            po_items = []
            for item_data in items_data:
                product_id = item_data.get('product_id')
                quantity = item_data.get('quantity', 0)
                cost = item_data.get('cost', 0)

                if not product_id or quantity <= 0 or cost < 0:
                    raise ValueError(f"Invalid item data: {item_data}. Quantity must be > 0, cost >= 0.")

                product = product_repo.get_by_id(product_id)
                if not product:
                    raise ValueError(f"Product with ID {product_id} not found.")

                po_item = PurchaseOrderItem(
                    product_id=product.id,
                    product_code=product.code,
                    product_description=product.description,
                    quantity_ordered=quantity,
                    unit_price=cost,
                    quantity_received=0
                )
                po_items.append(po_item)

            purchase_order = PurchaseOrder(
                supplier_id=supplier.id,
                order_date=po_data.get('order_date', datetime.now()),
                expected_delivery_date=po_data.get('expected_delivery_date'),
                status="PENDING",
                notes=po_data.get('notes'),
                items=po_items
            )

            created_po = purchase_order_repo.add(purchase_order)
            return created_po
            
        return self._with_session(_create_purchase_order, po_data)

    def get_purchase_order_by_id(self, po_id: int) -> Optional[PurchaseOrder]:
        """Retrieves a specific purchase order including its items."""
        def _get_purchase_order_by_id(session, po_id):
            purchase_order_repo = self._get_repository(self.purchase_order_repo_factory, session)
            return purchase_order_repo.get_by_id(po_id)
            
        return self._with_session(_get_purchase_order_by_id, po_id)

    def find_purchase_orders(self, status: Optional[str] = None, supplier_id: Optional[int] = None) -> List[PurchaseOrder]:
        """Finds purchase orders, optionally filtering by status or supplier."""
        def _find_purchase_orders(session, status, supplier_id):
            purchase_order_repo = self._get_repository(self.purchase_order_repo_factory, session)
            return purchase_order_repo.get_all(status=status, supplier_id=supplier_id)
            
        return self._with_session(_find_purchase_orders, status, supplier_id)

    def receive_purchase_order_items(self, po_id: int, received_data: Dict[int, Dict], notes: Optional[str] = None) -> PurchaseOrder:
        """
        Receives stock against a purchase order.
        
        Args:
            po_id: The ID of the purchase order
            received_data: Dict mapping PurchaseOrderItem ID to quantity received in this batch
            notes: Optional notes for the inventory movement
            
        Returns:
            The updated PurchaseOrder
        """
        def _receive_purchase_order_items(session, po_id, received_data, notes):
            if not received_data:
                raise ValueError("No received item quantities provided.")

            # Get repository from factory
            purchase_order_repo = self._get_repository(self.purchase_order_repo_factory, session)

            po = purchase_order_repo.get_by_id(po_id)
            if not po:
                raise ValueError(f"Purchase Order with ID {po_id} not found.")
            if po.status in ["RECEIVED", "CANCELLED"]:
                raise ValueError(f"Purchase Order {po_id} is already {po.status} and cannot receive more items.")

            po_items_dict = {item.id: item for item in po.items}
            total_items_ordered = sum(item.quantity_ordered for item in po.items)
            total_items_previously_received = sum(item.quantity_received for item in po.items)
            total_received_this_batch = 0
            updated_item_ids = set()

            # Iterate through the items to be received
            for item_id_str, received_info in received_data.items():
                item_id = int(item_id_str) if isinstance(item_id_str, str) else item_id_str
                qty_received_value = received_info.get('quantity_received')
                item_notes = received_info.get('notes')

                if qty_received_value is None:
                    self.logger.warning(f"Missing 'quantity_received' for item {item_id} in receive data. Skipping.")
                    continue

                # Basic validation for the quantity received in this batch
                if not isinstance(qty_received_value, (Decimal, float, int)) or qty_received_value <= 0:
                    raise ValueError(f"Invalid quantity received ({qty_received_value}) for item ID {item_id}. Must be a positive number.")
                qty_received_value = Decimal(str(qty_received_value))  # Ensure Decimal

                # Find the corresponding PurchaseOrderItem within the PO
                po_item = po_items_dict.get(item_id)
                if po_item is None:
                    raise ValueError(f"Purchase Order Item with ID {item_id} not found in PO {po_id}.")

                # Check if receiving more than ordered
                if Decimal(str(po_item.quantity_received)) + qty_received_value > po_item.quantity_ordered:
                    raise ValueError(f"Cannot receive {qty_received_value} for item {po_item.product_code}. "
                                    f"Ordered: {po_item.quantity_ordered}, Already Received: {po_item.quantity_received}.")

                # 1. Update Inventory Stock using InventoryService
                # Pass our session to inventory_service
                self.inventory_service.decrease_stock_for_sale(
                    product_id=po_item.product_id,
                    quantity=qty_received_value,
                    sale_id=po_id,  # Using PO ID as the related ID
                    user_id=None,  # No user ID for this operation
                    session=session  # Pass the session for transactionality
                )

                # 2. Update the quantity received on the PurchaseOrderItem
                purchase_order_repo.update_item_received_quantity(item_id, qty_received_value)
                po_item.quantity_received += qty_received_value  # Update local object state
                total_received_this_batch += qty_received_value
                updated_item_ids.add(item_id)

            # 3. Update PO Status
            new_total_received = total_items_previously_received + total_received_this_batch
            new_status = po.status
            # Ensure total_items_ordered is not zero before comparison
            if total_items_ordered > 0 and new_total_received >= total_items_ordered:
                new_status = "RECEIVED"
            elif new_total_received > 0:
                new_status = "PARTIALLY_RECEIVED"

            if new_status != po.status:
                purchase_order_repo.update_status(po_id, new_status)
                po.status = new_status  # Update local object status

            return po
            
        return self._with_session(_receive_purchase_order_items, po_id, received_data, notes)

    # Add other methods like cancel_purchase_order etc. later
