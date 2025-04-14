from typing import List, Optional, Dict, Tuple
from datetime import datetime

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

class PurchaseService:
    """Handles business logic related to purchase orders and suppliers."""

    # Type hints for repository factories: Callable[[Session], IRepositoryInterface]
    RepoFactory = Callable[[Session], any]

    def __init__(
        self,
        purchase_order_repo: RepoFactory, # Changed: Expect factory
        supplier_repo: RepoFactory,       # Changed: Expect factory
        product_repo: RepoFactory,         # Changed: Expect factory
        inventory_service: InventoryService # Keep instance for now, could also be factory
    ):
        # Store factories
        self.purchase_order_repo_factory = purchase_order_repo
        self.supplier_repo_factory = supplier_repo
        self.product_repo_factory = product_repo
        # Keep inventory service instance as passed
        self.inventory_service = inventory_service

    # --- Supplier Methods ---

    def add_supplier(self, supplier_data: Dict, session=None) -> Supplier:
        """Adds a new supplier after validation."""
        if not supplier_data.get('name'):
            raise ValueError("Supplier name is required.")

        # Remove duplicate checks here as they should be inside the session_scope
        # using the supplier_repo_factory

        supplier = Supplier(**supplier_data)
        with session_scope(session) as session:
            # Instantiate repo with session from factory
            supplier_repo = self.supplier_repo_factory(session)
            # Check for duplicates using the session-specific repo
            if supplier_repo.get_by_name(supplier_data['name']):
                 raise ValueError(f"Supplier with name '{supplier_data['name']}' already exists.")
            if supplier_data.get('cuit') and supplier_repo.get_by_cuit(supplier_data['cuit']):
                 raise ValueError(f"Supplier with CUIT '{supplier_data['cuit']}' already exists.")

            added_supplier = supplier_repo.add(supplier)
            return added_supplier

    def update_supplier(self, supplier_id: int, supplier_data: Dict) -> Supplier:
        """Updates an existing supplier."""
        if not supplier_id:
            raise ValueError("Supplier ID is required for update.")

        with session_scope() as session:
            supplier_repo = self.supplier_repo_factory(session) # Instantiate repo
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

            # Call update on the session-specific repo instance
            updated_supplier = supplier_repo.update(supplier_to_update)
            if not updated_supplier: # Should not happen if get_by_id worked, but check anyway
                 raise RuntimeError(f"Failed to update supplier {supplier_id}")
            return updated_supplier

    def delete_supplier(self, supplier_id: int) -> bool:
        """Deletes a supplier."""
        with session_scope() as session:
            supplier_repo = self.supplier_repo_factory(session) # Instantiate repo
            po_repo = self.purchase_order_repo_factory(session) # Instantiate repo

            # Check for related POs using session-specific repo
            related_pos = po_repo.get_all(supplier_id=supplier_id)
            if any(po.status not in ["RECEIVED", "CANCELLED"] for po in related_pos):
                 raise ValueError("Cannot delete supplier with active or pending purchase orders.")

            return supplier_repo.delete(supplier_id)

    def find_suppliers(self, query: str = "") -> List[Supplier]:
        """Finds suppliers by name, contact, CUIT, etc."""
        with session_scope() as session:
            supplier_repo = self.supplier_repo_factory(session) # Instantiate repo
            if not query:
                return supplier_repo.get_all()
            else:
                return supplier_repo.search(query)

    def get_supplier_by_id(self, supplier_id: int) -> Optional[Supplier]:
        with session_scope() as session:
            supplier_repo = self.supplier_repo_factory(session) # Instantiate repo
            return supplier_repo.get_by_id(supplier_id)

    # --- Purchase Order Methods ---

    def create_purchase_order(self, po_data: Dict, session=None) -> PurchaseOrder:
        """Creates a new purchase order."""
        supplier_id = po_data.get('supplier_id')
        items_data = po_data.get('items', [])

        if not supplier_id:
            raise ValueError("Supplier ID is required.")
        if not items_data:
            raise ValueError("Purchase order must contain at least one item.")

        with session_scope(session) as session:
            # Instantiate repos with session from factories
            supplier_repo = self.supplier_repo_factory(session)
            product_repo = self.product_repo_factory(session)
            purchase_order_repo = self.purchase_order_repo_factory(session)

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

                product = product_repo.get_by_id(product_id) # Use session-specific repo
                if not product:
                    raise ValueError(f"Product with ID {product_id} not found.")

                po_item = PurchaseOrderItem(
                    product_id=product.id,
                    product_code=product.code, # Denormalize
                    product_description=product.description, # Denormalize
                    quantity_ordered=quantity,
                    cost_price=cost,
                    quantity_received=0 # Initially zero
                )
                po_items.append(po_item)

            purchase_order = PurchaseOrder(
                supplier_id=supplier.id,
                supplier_name=supplier.name, # Denormalize
                order_date=po_data.get('order_date', datetime.now()),
                expected_delivery_date=po_data.get('expected_delivery_date'),
                status="PENDING", # Initial status
                notes=po_data.get('notes'),
                items=po_items
            )

            created_po = purchase_order_repo.add(purchase_order) # Use session-specific repo
            return created_po

    def get_purchase_order_by_id(self, po_id: int) -> Optional[PurchaseOrder]:
        """Retrieves a specific purchase order including its items."""
        with session_scope() as session:
            purchase_order_repo = self.purchase_order_repo_factory(session) # Instantiate repo
            return purchase_order_repo.get_by_id(po_id)

    def find_purchase_orders(self, status: Optional[str] = None, supplier_id: Optional[int] = None) -> List[PurchaseOrder]:
        """Finds purchase orders, optionally filtering by status or supplier."""
        with session_scope() as session:
            purchase_order_repo = self.purchase_order_repo_factory(session) # Instantiate repo
            return purchase_order_repo.get_all(status=status, supplier_id=supplier_id)

    def receive_purchase_order_items(self, po_id: int, received_items_data: Dict[int, float], notes: Optional[str] = None) -> PurchaseOrder:
        """
        Receives stock against a purchase order.
        :param po_id: The ID of the purchase order.
        :param received_items_data: Dict mapping PurchaseOrderItem ID to quantity received in this batch.
        :param notes: Optional notes for the inventory movement.
        :return: The updated PurchaseOrder.
        """
        if not received_items_data:
            raise ValueError("No received item quantities provided.")

        with session_scope() as session:
            # Instantiate repos with session from factories
            purchase_order_repo = self.purchase_order_repo_factory(session)
            # product_repo = self.product_repo_factory(session) # Not directly needed here
            # inventory_service instance is already available via self.inventory_service

            po = purchase_order_repo.get_by_id(po_id) # Use session-specific repo
            if not po:
                raise ValueError(f"Purchase Order with ID {po_id} not found.")
            if po.status in ["RECEIVED", "CANCELLED"]:
                raise ValueError(f"Purchase Order {po_id} is already {po.status} and cannot receive more items.")

            po_items_dict = {item.id: item for item in po.items}
            total_items_ordered = sum(item.quantity_ordered for item in po.items)
            total_items_previously_received = sum(item.quantity_received for item in po.items)
            total_received_this_batch = 0
            updated_item_ids = set()

            for item_id, qty_received_batch in received_items_data.items():
                if qty_received_batch <= 0:
                    continue # Ignore zero or negative receipts

                po_item = po_items_dict.get(item_id)
                if not po_item:
                    raise ValueError(f"Purchase Order Item with ID {item_id} not found in PO {po_id}.")

                if po_item.quantity_received + qty_received_batch > po_item.quantity_ordered:
                    raise ValueError(f"Cannot receive {qty_received_batch} for item {po_item.product_code}. "
                                     f"Ordered: {po_item.quantity_ordered}, Already Received: {po_item.quantity_received}.")

                # 1. Update Inventory Stock using InventoryService
                #    The service should handle logging the movement.
                self.inventory_service.add_inventory(
                    product_id=po_item.product_id,
                    quantity=qty_received_batch,
                    cost_price=po_item.cost_price, # Use cost from PO item
                    movement_description=f"Receiving PO-{po_id}. {notes or ''}".strip(),
                    related_id=po_id,
                    session=session # Pass the session for transactionality
                )

                # 2. Update the quantity_received using the repository method
                success = purchase_order_repo.update_item_received_quantity(item_id, qty_received_batch)
                if not success:
                    # Should not happen if PO item was found earlier, but handle the case
                    raise RuntimeError(f"Failed to update quantity_received for item {item_id}")
                
                # Update local tracking
                updated_item_ids.add(item_id)
                total_received_this_batch += qty_received_batch

            # 3. Update PO Status
            new_total_received = total_items_previously_received + total_received_this_batch
            new_status = po.status
            # Ensure total_items_ordered is not zero before comparison
            if total_items_ordered > 0 and new_total_received >= total_items_ordered:
                new_status = "RECEIVED"
            elif new_total_received > 0:
                new_status = "PARTIALLY_RECEIVED"

            if new_status != po.status:
                purchase_order_repo.update_status(po_id, new_status) # Use session-specific repo
                po.status = new_status # Update local object status

            # Update local item objects for the return value (already done by modifying item_orm)
            for item_id in updated_item_ids:
                 po_items_dict[item_id].quantity_received += received_items_data[item_id]

            # Commit happens automatically via session_scope exit
            # Re-fetch the PO to ensure all updates are reflected? Optional.
            # updated_po = self.purchase_order_repo.get_by_id(po_id)
            # return updated_po or po # Return the potentially updated local object

            return po # Return the modified local PO object

    # Add other methods like cancel_purchase_order etc. later
