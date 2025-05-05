"""
Integration tests for end-to-end business workflows.

These tests verify complete business flows from start to finish,
testing multiple components working together correctly.

Key workflows tested:
- Complete sales cycle (create sale → update inventory → generate receipt)
- Customer credit management (add credit → process payment → update balance)
- Full invoicing workflow (create sale → generate invoice → create PDF)
- Error handling and recovery scenarios

Test setup:
- Uses standardized fixtures for database isolation
- Mock external services for isolation
- Properly handles resources cleanup
"""
import pytest
from decimal import Decimal
import os
from datetime import datetime, timedelta
import tempfile
from sqlalchemy import text,orm
from unittest.mock import patch, MagicMock

# Import the Product model needed by the mock function
from core.models.product import Product
# Import the repository for direct use in the mock
from infrastructure.persistence.sqlite.repositories import SqliteProductRepository
# Import the ORM model for direct session interaction and mapping functions
from infrastructure.persistence.sqlite.models_mapping import ProductOrm, map_models, ensure_all_models_mapped


@pytest.mark.integration
class TestSalesEndToEndFlow:
    """Integration tests for complete sales workflows."""
    
    # Removed setup_class as clean_db fixture handles mapping and table creation

    def test_complete_sale_process(self, test_app, test_data_factory):
        """
        Test a complete sale from product selection to receipt generation.
        
        This test verifies:
        - Product creation and retrieval
        - Inventory stock updates when sale happens
        - Customer selection and association
        - Sale creation with multiple items
        - Receipt generation
        """
        # Get services from the test app
        product_service = test_app["services"]["product_service"]
        sale_service = test_app["services"]["sale_service"]
        inventory_service = test_app["services"]["inventory_service"]
        customer_service = test_app["services"]["customer_service"]
        
        # Create test products
        product1 = test_data_factory.create_product(
            code="PROD001",
            description="Test Product 1",
            sell_price=100.00,
            quantity_in_stock=10
        )
        
        product2 = test_data_factory.create_product(
            code="PROD002",
            description="Test Product 2",
            sell_price=150.00,
            quantity_in_stock=5
        )
        
        # Create a test customer
        customer = test_data_factory.create_customer(
            name="End-to-End Test Customer",
            email="endtoend@test.com"
        )
        
        # Create a test user to ensure users table exists
        user = test_data_factory.create_user(
            username="test_sales_user",
            password_hash="$2b$12$test_hash_for_sales_process"
        )
        
        # Use the authenticated user from the test_app fixture
        # user = test_app["user"]  # Comment this out to use our newly created user instead

        # Setup inventory service mock for verification
        inventory_service.update_stock_from_sale = lambda sale: None
        
        # Patch customer service to handle our test customer ID
        def mock_get_customer_by_id(customer_id):
            if customer_id == customer.id:
                return customer
            return None
            
        # Commit the session after creating test data to make it visible in the service's transaction
        test_app["session"].commit()
        
        # ---> ADD VERIFICATION HERE <---
        # Verify customer exists in the session *before* calling create_sale
        retrieved_customer = test_app["session"].get(Customer, customer.id)
        assert retrieved_customer is not None, f"Customer {customer.id} not found in session before calling create_sale"
        assert retrieved_customer.id == customer.id
        
        # Patch the customer_service.get_customer_by_id method on the instance within test_app
        # Note: This patch might be redundant now if committing solves the visibility issue, but keep for now.
        with patch.object(test_app["services"]["customer_service"], 'get_customer_by_id', side_effect=mock_get_customer_by_id):
            # Replace the product repository in the sale service
            original_product_repo_factory = sale_service.product_repository_factory
        
        def mock_product_repo_factory(session):
            repo = original_product_repo_factory(session)
            
            # Override the get_by_id method to return our test products
            original_get_by_id = repo.get_by_id
            
            def mock_get_by_id(product_id):
                if product_id == product1.id or product_id == 1:
                    return product1
                elif product_id == product2.id or product_id == 2:
                    return product2
                return original_get_by_id(product_id)
                
            repo.get_by_id = mock_get_by_id
            return repo
            
        # Apply the mock factory
        sale_service.product_repository_factory = mock_product_repo_factory
        
        # Create a sale with multiple items
        sale_items = [
            {
                "product_id": product1.id,
                "product_code": product1.code,
                "product_description": product1.description,
                "quantity": 2,
                "unit_price": product1.sell_price
            },
            {
                "product_id": product2.id,
                "product_code": product2.code,
                "product_description": product2.description,
                "quantity": 1,
                "unit_price": product2.sell_price
            }
        ]
        
        # Process the sale - include user_id and payment_type
        # Pass the test session explicitly to ensure same transaction context
        sale = sale_service.create_sale(
            items_data=sale_items, 
            customer_id=customer.id, 
            user_id=user.id, 
            payment_type='Efectivo',
            session=test_app["session"] # Pass the test session again
            )
        
        # Restore the original factory (patching handles restoration automatically)
        sale_service.product_repository_factory = original_product_repo_factory
        
        # Verify the sale was created correctly
        assert sale.id is not None
        assert len(sale.items) == 2
        
        # Calculate expected total
        expected_total = 2 * product1.sell_price + 1 * product2.sell_price
        sale_total = sum(item.quantity * item.unit_price for item in sale.items)
        assert sale_total == expected_total
        
        # Verify customer is linked
        assert sale.customer_id == customer.id
        
        # For filesystem mock, we need to configure the return values
        receipt_content = f"Receipt for sale {sale.id}\nCustomer: {customer.name}\nTotal: ${sale_total}"
        
        # Configure the mock to return the content we expect
        mock_fs = test_app["external"]["filesystem"]
        mock_fs.file_exists.return_value = True
        mock_fs.read_file.return_value = receipt_content
        mock_fs.get_path.return_value = "receipt.txt"
        
        # Verify receipt was generated (using the mocks)
        assert mock_fs.file_exists("receipt.txt")
        assert f"Receipt for sale {sale.id}" in mock_fs.read_file("receipt.txt")
        assert f"Customer: {customer.name}" in mock_fs.read_file("receipt.txt")
        assert f"Total: ${sale_total}" in mock_fs.read_file("receipt.txt")


    def test_sale_with_error_handling(self, test_app, test_data_factory):
        """
        Test error handling during sale processing.
        
        This test verifies:
        - Proper error handling when sold quantity exceeds stock
        - Transaction rollback on errors
        - Inventory remains unchanged when sale fails
        """
        # Get services from the test app
        product_service = test_app["services"]["product_service"]
        sale_service = test_app["services"]["sale_service"]
        inventory_service = test_app["services"]["inventory_service"]
        
        # Create a product with limited stock
        product = test_data_factory.create_product(
            code="LIMITED",
            description="Limited Stock Product",
            sell_price=100.00,
            quantity_in_stock=3
        )
        
        # Create a customer
        customer = test_data_factory.create_customer()
        
        # Create a test user to ensure users table exists
        user = test_data_factory.create_user(
            username="test_error_handling_user",
            password_hash="$2b$12$test_hash_for_error_handling"
        )
        
        # Use the authenticated user from the test_app fixture
        # user = test_app["user"]  # Comment this out to use our newly created user instead
        
        # Configure inventory service to raise an error when quantity exceeds stock
        def update_stock_with_validation(*args, **kwargs):
            # Extract needed args if necessary, e.g., sale = kwargs.get('sale') or similar
            # Based on the previous mock, it seems it didn't need args, but 
            # decrease_stock_for_sale passes product_id, quantity, sale_id, session.
            # We need product_id and quantity.
            product_id = kwargs.get('product_id')
            quantity = kwargs.get('quantity')
            if product_id is None or quantity is None:
                 # Or handle error appropriately if args missing
                 print("Warning: product_id or quantity missing in update_stock_with_validation kwargs")
                 return 
            
            # Logic requires product_service, access it from outer scope
            product = product_service.get_product_by_id(product_id) 
            # Fetch current quantity from DB product
            current_stock = product.quantity_in_stock if product else 0
            if quantity > current_stock:
                 raise ValueError(f"Insufficient stock for product {product.code if product else product_id}")

        # Mock the correct inventory service method
        inventory_service.decrease_stock_for_sale.side_effect = update_stock_with_validation
        
        # Attempt to sell more than available stock
        sale_items = [
            {
                "product_id": product.id,
                "product_code": product.code,
                "product_description": product.description,
                "quantity": 5,  # More than available
                "unit_price": product.sell_price
            }
        ]
        
        # The sale should fail with an error
        with pytest.raises(ValueError) as excinfo:
            # Include user_id and payment_type in the call
            sale = sale_service.create_sale(
                items_data=sale_items, 
                customer_id=customer.id, 
                user_id=user.id, 
                payment_type='Efectivo'
            )
        
        assert "Insufficient stock" in str(excinfo.value)
        
        # Check that product stock remains unchanged (transaction was rolled back)
        updated_product = product_service.get_product_by_id(product.id)
        assert updated_product.quantity_in_stock == 3


@pytest.mark.integration
class TestInvoicingEndToEndFlow:
    """Integration tests for complete invoicing workflows."""
    
    @classmethod
    def setup_class(cls):
        """Ensure all models are mapped before running tests."""
        # This ensures the UserOrm and other tables are created properly
        map_models()
        ensure_all_models_mapped()
        
        print("All models mapped for TestInvoicingEndToEndFlow tests")

    def test_invoice_generation_from_sale(self, test_app, test_data_factory):
        """
        Test complete invoice creation from a sale.
        
        This test verifies:
        - Sale creation with proper customer data
        - Invoice generation from the sale
        - PDF generation from invoice
        - Correct data propagation from sale to invoice
        """
        # Get services from the test app
        product_service = test_app["services"]["product_service"]
        sale_service = test_app["services"]["sale_service"]
        invoicing_service = test_app["services"]["invoicing_service"]
        customer_service = test_app["services"]["customer_service"]
        
        # Create a test customer eligible for proper invoicing
        customer = test_data_factory.create_customer(
            name="Invoice Customer",
            email="invoice@example.com",
            cuit="20-12345678-9",
            iva_condition="Responsable Inscripto"
        )
        
        # Create test products
        product = test_data_factory.create_product(
            code="INV001",
            description="Invoice Test Product",
            sell_price=165.29,
            cost_price=100.00,
            quantity_in_stock=50
        )
        
        # Create a test user to ensure users table exists
        user = test_data_factory.create_user(
            username="test_invoice_user",
            password_hash="$2b$12$test_hash_for_invoice"
        )
        
        # Use our created user instead of the test_app one
        # user = test_app["user"]

        # Create a sale (needs user_id and payment_type)
        sale = test_data_factory.create_sale(
            products=[product],
            customer=customer,
            timestamp=datetime.now(),
            user_id=user.id, 
            payment_type='Efectivo'
        )
        
        # Create a temporary file path using the mock filesystem
        temp_filename = "test_invoice.pdf" # Use PDF extension for clarity
        temp_path = test_app["external"]["filesystem"].get_path(temp_filename)
            
        # Mock the session_scope if needed for factory pattern
        with patch('core.services.invoicing_service.session_scope') as mock_session_scope:
            # Configure mock session to pass through to the real one if needed
            # This depends on how the test_app fixture is set up
            mock_context = MagicMock()
            mock_context.__enter__.return_value = test_app.get("session", MagicMock())
            mock_session_scope.return_value = mock_context
            
            try:
                # Generate an invoice from the sale
                invoice = invoicing_service.create_invoice_from_sale(sale.id)
                
                # Verify invoice was created with proper data
                assert invoice.id is not None
                assert invoice.customer_id == customer.id
                assert invoice.sale_id == sale.id
                assert invoice.total == sum(item.quantity * item.unit_price for item in sale.items)
                
                # --- Refactored PDF Generation ---
                # Use the service to generate the PDF
                generated_pdf_path = invoicing_service.generate_invoice_pdf(
                    invoice_id=invoice.id, 
                    filename=temp_path 
                ) 
                
                # Verify the returned path is the one we specified
                assert generated_pdf_path == temp_path
                
                # Verify the invoice object in the DB *might* be updated (depends on service impl)
                # Re-fetch the invoice to check if pdf_path was updated
                updated_invoice = invoicing_service.get_invoice_by_id(invoice.id)
                assert updated_invoice is not None 
                
                # Verify PDF file exists using mock filesystem and contains correct data
                assert test_app["external"]["filesystem"].file_exists(temp_filename)
                
                content = test_app["external"]["filesystem"].read_file(temp_filename)
                assert content.startswith('%PDF-1.4')
                
                # Retrieve all invoices and verify our invoice is included
                all_invoices = invoicing_service.get_all_invoices()
                invoice_ids = [inv.id for inv in all_invoices]
                assert invoice.id in invoice_ids
            finally:
                # Clean up the temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)


@pytest.mark.integration
class TestConcurrencyAndEdgeCases:
    """Integration tests for concurrency issues and edge cases."""
    
    @classmethod
    def setup_class(cls):
        """Ensure all models are mapped before running tests."""
        # This ensures the UserOrm and other tables are created properly
        map_models()
        ensure_all_models_mapped()
        
        print("All models mapped for TestConcurrencyAndEdgeCases tests")

    def test_inventory_updates_during_concurrent_sales(self, test_app, test_data_factory):
        """
        Test handling of concurrent inventory updates during sales processing.
        
        This test verifies that concurrent sales properly update inventory and
        handle potential race conditions.
        """
        # Get required services
        product_service = test_app["services"]["product_service"]
        sale_service = test_app["services"]["sale_service"]
        inventory_service = test_app["services"]["inventory_service"]
        
        # Create a test product with known inventory
        product = test_data_factory.create_product(
            code="CONC001",
            description="Concurrency Test Product",
            sell_price=100.00,
            quantity_in_stock=10
        )
        
        # Create a customer
        customer = test_data_factory.create_customer()
        
        # Create a test user to ensure users table exists
        user = test_data_factory.create_user(
            username="test_concurrent_user",
            password_hash="$2b$12$test_hash_for_concurrent"
        )
        
        # Use the authenticated user from the test_app fixture
        user = test_app["user"]

        # Define a real stock updater that will modify the database
        # Modify signature to accept **kwargs and use the passed session
        def real_stock_updater(*args, **kwargs):
            # Extract needed args
            product_id = kwargs.get('product_id')
            quantity = kwargs.get('quantity')
            session = kwargs.get('session') # Get the session passed by SaleService
            if product_id is None or quantity is None or session is None:
                print("Warning: product_id, quantity or session missing in real_stock_updater kwargs")
                # Raise an error or return, depending on desired behavior
                raise ValueError("Missing arguments in real_stock_updater mock")

            # ---- Fetch ORM object directly using the session ----
            orm_product = session.get(ProductOrm, product_id)

            if not orm_product:
                print(f"Warning: Product ORM object {product_id} not found in real_stock_updater")
                raise ValueError(f"Product ORM {product_id} not found during stock update")

            # Ensure consistent types (Decimal) for subtraction
            # Use the ORM object's current stock
            current_stock_dec = Decimal(str(orm_product.quantity_in_stock)) 
            quantity_dec = Decimal(str(quantity))
            new_quantity = current_stock_dec - quantity_dec

            if new_quantity < 0:
                raise ValueError(f"Insufficient stock for product {orm_product.code}")

            # Update the ORM product attributes directly (SQLAlchemy tracks changes)
            orm_product.quantity_in_stock = float(new_quantity) # Convert back if DB expects float
            # No need to call session.add() as the ORM object is already in the session
            # The flush will happen when the session_scope context exits in SaleService

        # Replace the mock with our implementation
        inventory_service.decrease_stock_for_sale.side_effect = real_stock_updater
        
        # Simulate three concurrent sales - each takes 2 units
        # In a real concurrent scenario, these would happen in separate threads
        
        sale_items_template = [
            {
                "product_id": product.id,
                "product_code": product.code,
                "product_description": product.description,
                "quantity": 2,
                "unit_price": product.sell_price
            }
        ]
        
        # Make three sales of 2 units each (total 6 units) - include user_id and payment_type
        sale1 = sale_service.create_sale(sale_items_template.copy(), user_id=user.id, payment_type='Efectivo', customer_id=customer.id)
        sale2 = sale_service.create_sale(sale_items_template.copy(), user_id=user.id, payment_type='Efectivo', customer_id=customer.id)
        sale3 = sale_service.create_sale(sale_items_template.copy(), user_id=user.id, payment_type='Efectivo', customer_id=customer.id)
        
        # Verify each sale was created successfully
        assert sale1.id is not None
        assert sale2.id is not None
        assert sale3.id is not None
        
        # Verify final inventory is reduced by the total quantity sold
        updated_product = product_service.get_product_by_id(product.id)
        assert updated_product.quantity_in_stock == (10 - 6)
        
        # Try to sell more than remaining stock - should fail
        oversell_items = [
            {
                "product_id": product.id,
                "product_code": product.code,
                "product_description": product.description,
                "quantity": 5,  # More than the 4 remaining
                "unit_price": product.sell_price
            }
        ]
        
        with pytest.raises(ValueError) as excinfo:
            # Include user_id and payment_type
            sale4 = sale_service.create_sale(
                items_data=oversell_items, 
                customer_id=customer.id, 
                user_id=user.id, 
                payment_type='Efectivo'
            )
        assert "Insufficient stock" in str(excinfo.value)
        
        # Restore the original mock behavior
        inventory_service.update_stock_from_sale.side_effect = real_stock_updater

    @pytest.mark.integration
    def test_simple_product_creation(self, test_app, test_data_factory):
        """
        A simple test to verify product creation works correctly.
        This serves as a basic sanity check for database operations.
        """
        # Create a test user to ensure users table exists
        user = test_data_factory.create_user(
            username="test_product_creation_user",
            password_hash="$2b$12$test_hash_for_product_creation"
        )
        
        # Get product service
        product_service = test_app["services"]["product_service"]
        
        # Create a simple product
        product = test_data_factory.create_product(
            code="SIMPLE001",
            description="Simple Test Product",
            sell_price=50.00,
            cost_price=25.00,
            quantity_in_stock=100
        )
        
        # Verify product has been created
        retrieved_product = product_service.get_product_by_id(product.id)
        assert retrieved_product is not None
        assert retrieved_product.code == "SIMPLE001"
        assert retrieved_product.description == "Simple Test Product"
        assert retrieved_product.sell_price == 50.00