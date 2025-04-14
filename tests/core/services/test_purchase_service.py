import pytest

from core.services.purchase_service import PurchaseService
from core.services.inventory_service import InventoryService
from infrastructure.persistence.sqlite.repositories import (
    SqliteSupplierRepository, SqlitePurchaseOrderRepository, SqliteProductRepository
)
from core.models.supplier import Supplier
from core.models.purchase import PurchaseOrder
from core.models.product import Product

@pytest.fixture
def repo_factories(test_db_session):
    def supplier_repo_factory(session):
        return SqliteSupplierRepository(session)
    def purchase_order_repo_factory(session):
        return SqlitePurchaseOrderRepository(session)
    def product_repo_factory(session):
        return SqliteProductRepository(session)
    return {
        "supplier_repo_factory": supplier_repo_factory,
        "purchase_order_repo_factory": purchase_order_repo_factory,
        "product_repo_factory": product_repo_factory,
    }

@pytest.fixture
def inventory_service(test_db_session):
    # Use a real InventoryService if possible, or a simple mock if not available
    # For now, use a dummy with required interface
    class DummyInventoryService:
        def update_stock(self, *args, **kwargs):
            pass
    return DummyInventoryService()

@pytest.fixture
def purchase_service(repo_factories, inventory_service):
    return PurchaseService(
        purchase_order_repo=repo_factories["purchase_order_repo_factory"],
        supplier_repo=repo_factories["supplier_repo_factory"],
        product_repo=repo_factories["product_repo_factory"],
        inventory_service=inventory_service
    )

def test_add_supplier(purchase_service, test_db_session):
    supplier_data = {
        "name": "Test Supplier",
        "address": "123 Test St",
        "phone": "555-1234",
        "email": "test@supplier.com",
        "cuit": "123456789"
    }
    supplier = purchase_service.add_supplier(supplier_data, test_db_session)
    assert supplier.id is not None
    assert supplier.name == "Test Supplier"

def test_create_purchase_order(purchase_service, test_db_session):
    # First, add a supplier and a product
    supplier_data = {
        "name": "Supplier PO",
        "address": "456 PO St",
        "phone": "555-5678",
        "email": "po@supplier.com",
        "cuit": "987654321"
    }
    supplier = purchase_service.add_supplier(supplier_data, test_db_session)

    # Add a product directly using the product repo
    product_repo = purchase_service.product_repo_factory(test_db_session)
    product = Product(
        description="Test Product",
        code="TP001",
        cost_price=8.0,
        sell_price=10.0,
        department_id=None,
        quantity_in_stock=0
    )
    product = product_repo.add(product)
    print(f"Added product with ID: {product.id}")

    po_data = {
        "supplier_id": supplier.id,
        "items": [
            {
                "product_id": product.id,
                "quantity": 5,
                "cost": 8.0
            }
        ],
        "notes": "Test PO"
    }
    purchase_order = purchase_service.create_purchase_order(po_data, test_db_session)
    assert purchase_order.id is not None
    assert purchase_order.supplier_id == supplier.id
    assert len(purchase_order.items) == 1
    assert purchase_order.items[0].product_id == product.id
    assert purchase_order.items[0].quantity_ordered == 5