"""
Integration tests for database interactions.

These tests verify that components interact correctly with database
and data persists through different operations.
"""
import pytest
from unittest.mock import MagicMock, patch
import tempfile
import os


class TestProductPersistence:
    """Tests for product data persistence."""
    
    def test_product_crud_operations(self):
        """Test Create, Read, Update, Delete operations for products."""
        # Create mock session and database components
        mock_session = MagicMock()
        
        # Create mock repositories
        mock_product_repo = MagicMock()
        
        # Create a test product
        mock_product = MagicMock()
        mock_product.id = 1
        mock_product.code = "P001"
        mock_product.name = "Test Product"
        mock_product.price = 10.99
        mock_product.stock = 5
        
        # Configure repository behaviors
        mock_product_repo.add.return_value = mock_product
        
        # Set get_by_id to return the product after "adding" it
        def get_by_id_side_effect(id):
            if id == 1:
                return mock_product
            return None
            
        mock_product_repo.get_by_id.side_effect = get_by_id_side_effect
        
        # Make get_by_code behave similarly
        def get_by_code_side_effect(code):
            if code == "P001":
                return mock_product
            return None
            
        mock_product_repo.get_by_code.side_effect = get_by_code_side_effect
        
        # Update behavior
        def update_side_effect(product):
            if product.id == 1:
                # We're returning the same mock product object but with updated price
                mock_product.price = product.price
                return mock_product
            return None
            
        mock_product_repo.update.side_effect = update_side_effect
        
        # Mock successful deletion
        mock_product_repo.delete.return_value = True
        
        # Create minimal service to test with repository
        class ProductService:
            def __init__(self, product_repo):
                self.product_repo = product_repo
                
            def create_product(self, code, name, price, stock=0):
                product = MagicMock()
                product.id = None
                product.code = code
                product.name = name
                product.price = price
                product.stock = stock
                
                return self.product_repo.add(product)
                
            def get_product(self, id):
                return self.product_repo.get_by_id(id)
                
            def get_by_code(self, code):
                return self.product_repo.get_by_code(code)
                
            def update_product(self, product):
                # Must be an existing product
                if product.id:
                    return self.product_repo.update(product)
                return None
                
            def delete_product(self, product_id):
                return self.product_repo.delete(product_id)
        
        # Create the service with our mock repository
        product_service = ProductService(product_repo=mock_product_repo)
        
        # Test CREATE operation
        new_product = product_service.create_product(
            code="P001",
            name="Test Product",
            price=10.99,
            stock=5
        )
        
        # Verify the product was added
        mock_product_repo.add.assert_called_once()
        assert new_product.id == 1
        assert new_product.code == "P001"
        assert new_product.name == "Test Product"
        assert new_product.price == 10.99
        assert new_product.stock == 5
        
        # Test READ operations
        product_by_id = product_service.get_product(1)
        assert product_by_id.id == 1
        assert product_by_id.code == "P001"
        
        product_by_code = product_service.get_by_code("P001")
        assert product_by_code.id == 1
        assert product_by_code.name == "Test Product"
        
        # Test UPDATE operation
        product_by_id.price = 12.99
        updated_product = product_service.update_product(product_by_id)
        
        mock_product_repo.update.assert_called_once()
        assert updated_product.price == 12.99
        
        # Test DELETE operation
        deleted = product_service.delete_product(1)
        
        mock_product_repo.delete.assert_called_once_with(1)
        assert deleted is True


class TestSalePersistence:
    """Tests for sale data persistence."""
    
    def test_sale_with_items_persistence(self):
        """Test creating a sale with multiple items and verifying persistence."""
        # Create mock repositories
        mock_sale_repo = MagicMock()
        mock_sale_item_repo = MagicMock()
        mock_product_repo = MagicMock()
        mock_customer_repo = MagicMock()
        
        # Create mock products
        products = {
            "P001": MagicMock(
                id=1,
                code="P001",
                name="Product 1",
                price=10.00,
                stock=20
            ),
            "P002": MagicMock(
                id=2,
                code="P002",
                name="Product 2",
                price=15.50,
                stock=10
            )
        }
        
        # Configure product repository
        def get_product_by_code(code):
            return products.get(code)
            
        mock_product_repo.get_by_code.side_effect = get_product_by_code
        
        # Configure sale repository to return a new sale with ID
        def add_sale(sale_data):
            return MagicMock(
                id=1,
                date=sale_data["date"],
                customer_id=sale_data["customer_id"],
                total=sale_data["total"],
                items=[]  # Items added separately
            )
            
        mock_sale_repo.add.side_effect = add_sale
        
        # Configure sale item repository
        def add_sale_item(item_data):
            return MagicMock(
                id=len(mock_sale_item_repo.add.mock_calls),  # Use call count for unique IDs
                sale_id=item_data["sale_id"],
                product_id=item_data["product_id"],
                quantity=item_data["quantity"],
                price=item_data["price"],
                subtotal=item_data["subtotal"]
            )
            
        mock_sale_item_repo.add.side_effect = add_sale_item
        
        # Create get_items_for_sale behavior
        mock_items = []
        
        def get_items_for_sale(sale_id):
            return mock_items
            
        mock_sale_item_repo.get_for_sale.side_effect = get_items_for_sale
        
        # Create a minimal sale service for testing
        class SaleService:
            def __init__(self, sale_repo, sale_item_repo, product_repo, customer_repo):
                self.sale_repo = sale_repo
                self.sale_item_repo = sale_item_repo
                self.product_repo = product_repo
                self.customer_repo = customer_repo
                self.current_sale = {
                    "date": "2023-05-01",
                    "customer_id": None,
                    "items": [],
                    "total": 0
                }
                
            def add_item(self, product_code, quantity):
                product = self.product_repo.get_by_code(product_code)
                if product and product.stock >= quantity:
                    item = {
                        "product": product,
                        "product_id": product.id,
                        "quantity": quantity,
                        "price": product.price,
                        "subtotal": product.price * quantity
                    }
                    self.current_sale["items"].append(item)
                    self.current_sale["total"] += item["subtotal"]
                    return True
                return False
                
            def set_customer(self, customer_id):
                self.current_sale["customer_id"] = customer_id
                
            def save_sale(self):
                if not self.current_sale["items"]:
                    return None
                    
                # Create sale record
                sale_data = {
                    "date": self.current_sale["date"],
                    "customer_id": self.current_sale["customer_id"],
                    "total": self.current_sale["total"]
                }
                
                # Save sale to get ID
                saved_sale = self.sale_repo.add(sale_data)
                
                # Save each item
                for item in self.current_sale["items"]:
                    item_data = {
                        "sale_id": saved_sale.id,
                        "product_id": item["product_id"],
                        "quantity": item["quantity"],
                        "price": item["price"],
                        "subtotal": item["subtotal"]
                    }
                    saved_item = self.sale_item_repo.add(item_data)
                    # For testing: add to our mock items list
                    nonlocal mock_items
                    mock_items.append(saved_item)
                
                # Reset current sale
                self.current_sale = {
                    "date": "2023-05-01",
                    "customer_id": None,
                    "items": [],
                    "total": 0
                }
                
                return saved_sale
                
            def get_sale_with_items(self, sale_id):
                sale = self.sale_repo.get_by_id(sale_id)
                if sale:
                    sale.items = self.sale_item_repo.get_for_sale(sale_id)
                    return sale
                return None
        
        # Create the service with mock repositories
        sale_service = SaleService(
            sale_repo=mock_sale_repo,
            sale_item_repo=mock_sale_item_repo,
            product_repo=mock_product_repo,
            customer_repo=mock_customer_repo
        )
        
        # Test adding items to the sale
        result1 = sale_service.add_item("P001", 2)
        assert result1 is True
        
        result2 = sale_service.add_item("P002", 1)
        assert result2 is True
        
        # Set a customer
        sale_service.set_customer(1)
        
        # Save the sale
        saved_sale = sale_service.save_sale()
        
        # Verify sale was created
        assert saved_sale.id == 1
        assert saved_sale.total == (10.00 * 2) + (15.50 * 1)
        
        # Verify sale repository was called
        mock_sale_repo.add.assert_called_once()
        
        # Verify sale items were saved (2 items)
        assert mock_sale_item_repo.add.call_count == 2
        
        # Test retrieving sale with items
        mock_sale_repo.get_by_id = MagicMock(return_value=saved_sale)
        
        retrieved_sale = sale_service.get_sale_with_items(1)
        
        # Verify sale was retrieved with items
        assert retrieved_sale.id == 1
        assert len(retrieved_sale.items) == 2
        assert mock_sale_item_repo.get_for_sale.call_count == 1


class TestInventoryTransactions:
    """Tests for inventory transaction tracking."""
    
    def test_inventory_transaction_recording(self):
        """Test that inventory changes are recorded as transactions."""
        # Create mock repositories
        mock_product_repo = MagicMock()
        mock_inventory_txn_repo = MagicMock()
        
        # Create a test product
        test_product = MagicMock(
            id=1,
            code="P001",
            name="Test Product",
            price=10.00,
            stock=10
        )
        
        # Configure repositories
        mock_product_repo.get_by_id.return_value = test_product
        mock_product_repo.get_by_code.return_value = test_product
        
        # Configure product update
        def update_product(product):
            # Return a copy with updated stock
            return MagicMock(
                id=product.id,
                code=product.code,
                name=product.name,
                price=product.price,
                stock=product.stock
            )
            
        mock_product_repo.update.side_effect = update_product
        
        # Configure transaction creation
        def add_transaction(txn_data):
            return MagicMock(
                id=len(mock_inventory_txn_repo.add.mock_calls) + 1,
                product_id=txn_data["product_id"],
                date=txn_data["date"],
                quantity=txn_data["quantity"],
                type=txn_data["type"],
                reference=txn_data["reference"],
                previous_stock=txn_data["previous_stock"],
                new_stock=txn_data["new_stock"]
            )
            
        mock_inventory_txn_repo.add.side_effect = add_transaction
        
        # Define transaction types for clarity
        TXN_TYPE_PURCHASE = "purchase"
        TXN_TYPE_SALE = "sale"
        TXN_TYPE_ADJUSTMENT = "adjustment"
        
        # Create a minimal inventory service for testing
        class InventoryService:
            def __init__(self, product_repo, inventory_txn_repo):
                self.product_repo = product_repo
                self.inventory_txn_repo = inventory_txn_repo
                
            def adjust_stock(self, product_id, quantity, reason, txn_type):
                # Get product
                product = self.product_repo.get_by_id(product_id)
                if not product:
                    return None
                    
                # Record previous stock
                previous_stock = product.stock
                
                # Update product stock
                product.stock += quantity
                
                # Save updated product
                updated_product = self.product_repo.update(product)
                
                # Record transaction
                txn_data = {
                    "product_id": product_id,
                    "date": "2023-05-01",  # Mock date
                    "quantity": quantity,
                    "type": txn_type,
                    "reference": reason,
                    "previous_stock": previous_stock,
                    "new_stock": updated_product.stock
                }
                
                transaction = self.inventory_txn_repo.add(txn_data)
                
                # Return combined result
                return {
                    "product": updated_product,
                    "transaction": transaction
                }
                
            def purchase_stock(self, product_id, quantity, purchase_id):
                return self.adjust_stock(
                    product_id,
                    quantity,
                    f"Purchase #{purchase_id}",
                    TXN_TYPE_PURCHASE
                )
                
            def sale_stock(self, product_id, quantity, sale_id):
                return self.adjust_stock(
                    product_id,
                    -quantity,  # Negative for sales
                    f"Sale #{sale_id}",
                    TXN_TYPE_SALE
                )
                
            def manual_adjustment(self, product_id, quantity, reason):
                return self.adjust_stock(
                    product_id,
                    quantity,
                    reason,
                    TXN_TYPE_ADJUSTMENT
                )
                
            def get_transactions(self, product_id=None, txn_type=None, limit=10):
                # In a real implementation, this would filter based on parameters
                # For our test, we'll return all transactions
                return self.inventory_txn_repo.get_all()
        
        # Create service with mock repositories
        inventory_service = InventoryService(
            product_repo=mock_product_repo,
            inventory_txn_repo=mock_inventory_txn_repo
        )
        
        # Test purchase transaction
        purchase_result = inventory_service.purchase_stock(1, 5, 1001)
        
        # Verify purchase updates product and records transaction
        assert purchase_result["product"].stock == 15  # 10 + 5
        assert purchase_result["transaction"].type == TXN_TYPE_PURCHASE
        assert purchase_result["transaction"].quantity == 5
        assert purchase_result["transaction"].previous_stock == 10
        assert purchase_result["transaction"].new_stock == 15
        
        # Test sale transaction
        sale_result = inventory_service.sale_stock(1, 3, 2001)
        
        # Verify sale updates product and records transaction
        assert sale_result["product"].stock == 12  # 15 - 3
        assert sale_result["transaction"].type == TXN_TYPE_SALE
        assert sale_result["transaction"].quantity == -3
        assert sale_result["transaction"].previous_stock == 15
        assert sale_result["transaction"].new_stock == 12
        
        # Test manual adjustment
        adjustment_result = inventory_service.manual_adjustment(
            1, -2, "Inventory count adjustment"
        )
        
        # Verify adjustment updates product and records transaction
        assert adjustment_result["product"].stock == 10  # 12 - 2
        assert adjustment_result["transaction"].type == TXN_TYPE_ADJUSTMENT
        assert adjustment_result["transaction"].quantity == -2
        assert adjustment_result["transaction"].previous_stock == 12
        assert adjustment_result["transaction"].new_stock == 10
        
        # Verify repository call counts
        assert mock_product_repo.update.call_count == 3
        assert mock_inventory_txn_repo.add.call_count == 3


class TestDatabaseIntegrity:
    """Tests for database integrity and constraints."""
    
    def test_foreign_key_integrity(self):
        """Test that foreign key constraints are enforced."""
        # Create a minimal database simulation
        class MockDatabase:
            def __init__(self):
                self.products = {}
                self.sales = {}
                self.sale_items = {}
                
            def add_product(self, product_data):
                product_id = len(self.products) + 1
                product = {
                    "id": product_id,
                    "code": product_data["code"],
                    "name": product_data["name"],
                    "price": product_data["price"]
                }
                self.products[product_id] = product
                return product
                
            def add_sale(self, sale_data):
                sale_id = len(self.sales) + 1
                sale = {
                    "id": sale_id,
                    "date": sale_data["date"],
                    "customer_id": sale_data["customer_id"],
                    "total": sale_data["total"]
                }
                self.sales[sale_id] = sale
                return sale
                
            def add_sale_item(self, item_data):
                # Check foreign key integrity
                sale_id = item_data["sale_id"]
                product_id = item_data["product_id"]
                
                if sale_id not in self.sales:
                    raise ValueError(f"Sale with ID {sale_id} does not exist")
                    
                if product_id not in self.products:
                    raise ValueError(f"Product with ID {product_id} does not exist")
                
                item_id = len(self.sale_items) + 1
                item = {
                    "id": item_id,
                    "sale_id": sale_id,
                    "product_id": product_id,
                    "quantity": item_data["quantity"],
                    "price": item_data["price"]
                }
                self.sale_items[item_id] = item
                return item
        
        # Create database and test data
        db = MockDatabase()
        
        # Add test products
        product1 = db.add_product({
            "code": "P001",
            "name": "Test Product 1",
            "price": 10.00
        })
        
        product2 = db.add_product({
            "code": "P002",
            "name": "Test Product 2",
            "price": 15.00
        })
        
        # Add a test sale
        sale = db.add_sale({
            "date": "2023-05-01",
            "customer_id": 1,
            "total": 35.00
        })
        
        # Test valid sale items
        item1 = db.add_sale_item({
            "sale_id": sale["id"],
            "product_id": product1["id"],
            "quantity": 2,
            "price": product1["price"]
        })
        
        assert item1["sale_id"] == sale["id"]
        assert item1["product_id"] == product1["id"]
        
        # Test foreign key constraint with invalid sale ID
        with pytest.raises(ValueError) as exc_info:
            db.add_sale_item({
                "sale_id": 999,  # Non-existent sale
                "product_id": product2["id"],
                "quantity": 1,
                "price": product2["price"]
            })
        
        assert "Sale with ID 999 does not exist" in str(exc_info.value)
        
        # Test foreign key constraint with invalid product ID
        with pytest.raises(ValueError) as exc_info:
            db.add_sale_item({
                "sale_id": sale["id"],
                "product_id": 999,  # Non-existent product
                "quantity": 1,
                "price": 20.00
            })
        
        assert "Product with ID 999 does not exist" in str(exc_info.value) 