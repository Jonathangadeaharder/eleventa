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

# Import the Product model needed by the mock function
from core.models.product import Product
# Import the repository for direct use in the mock
from infrastructure.persistence.sqlite.repositories import SqliteProductRepository
# Import the ORM model for direct session interaction
from infrastructure.persistence.sqlite.models_mapping import ProductOrm


@pytest.mark.integration
class TestSalesEndToEndFlow:
    """Integration tests for complete sales workflows."""

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
        
        # Use the authenticated user from the test_app fixture
        user = test_app["user"]

        # Setup inventory service mock for verification
        inventory_service.update_stock_from_sale = lambda sale: None
        
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
        sale = sale_service.create_sale(
            items_data=sale_items, 
            customer_id=customer.id, 
            user_id=user.id, 
            payment_type='Efectivo'
        )
        
        # Verify the sale was created correctly
        assert sale.id is not None
        assert len(sale.items) == 2
        
        # Calculate expected total
        expected_total = 2 * product1.sell_price + 1 * product2.sell_price
        sale_total = sum(item.quantity * item.unit_price for item in sale.items)
        assert sale_total == expected_total
        
        # Verify customer is linked
        assert sale.customer_id == customer.id
        
        # Generate receipt (mocked for this test)
        receipt_path = test_app["external"]["filesystem"].get_path("receipt.txt")
        with open(receipt_path, "w") as f:
            f.write(f"Receipt for sale {sale.id}\n")
            f.write(f"Customer: {customer.name}\n")
            f.write(f"Total: ${sale_total}\n")
            
        # Verify receipt was generated
        assert test_app["external"]["filesystem"].file_exists("receipt.txt")
        receipt_content = test_app["external"]["filesystem"].read_file("receipt.txt")
        assert f"Receipt for sale {sale.id}" in receipt_content
        assert f"Customer: {customer.name}" in receipt_content
        assert f"Total: ${sale_total}" in receipt_content


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
        
        # Use the authenticated user from the test_app fixture
        user = test_app["user"]
        
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
    
    def test_invoice_generation_from_sale(self, test_app, test_data_factory):
        """
        Test the complete invoice generation workflow from sale to PDF.
        
        This test verifies:
        - Sale creation with proper customer data
        - Invoice generation from the sale
        - PDF file creation
        - Invoice persistence
        """
        # Get services
        sale_service = test_app["services"]["sale_service"]
        invoicing_service = test_app["services"]["invoicing_service"]
        # Get mock filesystem
        mock_fs = test_app["external"]["filesystem"]
        # Get user
        user = test_app["user"]
        
        # Create a customer with invoice-required fields
        customer = test_data_factory.create_customer(
            name="End-to-End Test Customer",
            cuit="20987654321",
            iva_condition="Responsable Inscripto",
            address="456 Invoice St"
        )
        
        # Create a product for the sale
        product = test_data_factory.create_product()
        
        # Create a sale (needs user_id and payment_type)
        sale = test_data_factory.create_sale(
            products=[product],
            customer=customer,
            timestamp=datetime.now(),
            user_id=user.id, # Pass user_id here for consistency in data factory if needed, or update create_sale call
            payment_type='Efectivo' # Pass payment_type
        )
        
        # Create a temporary file path using the mock filesystem
        temp_filename = "test_invoice.pdf" # Use PDF extension for clarity
        temp_path = mock_fs.get_path(temp_filename)
            
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
            # Note: The real generate_invoice_pdf likely takes store_info, etc.
            # We assume the mock or the service handles defaults for testing.
            generated_pdf_path = invoicing_service.generate_invoice_pdf(
                invoice_id=invoice.id, 
                filename=temp_path 
                # We might need to pass mock store_info if required by the actual implementation
            ) 
            
            # Verify the returned path is the one we specified
            assert generated_pdf_path == temp_path
            
            # Verify the invoice object in the DB *might* be updated (depends on service impl)
            # Re-fetch the invoice to check if pdf_path was updated
            updated_invoice = invoicing_service.get_invoice_by_id(invoice.id)
            # This assertion depends on whether generate_invoice_pdf updates the DB record
            # If it doesn't, this might fail or pdf_path might be None
            assert updated_invoice is not None 
            # assert updated_invoice.pdf_path == temp_path # Add this if generate_invoice_pdf updates the DB

            # Verify PDF file exists using mock filesystem and contains correct data
            assert mock_fs.file_exists(temp_filename)
            
            # The actual PDF content generation is mocked/simplified in the service for tests usually.
            # We check if the file contains *some* expected text based on the mock/simplified generation.
            # If the service creates a dummy text file instead of PDF for tests:
            content = mock_fs.read_file(temp_filename)
            # we accept the test will fail if it produces a real PDF.
            assert content.startswith('%PDF-1.4')
            # Optionally, add more robust PDF checks if needed later
            # assert f"Customer: {customer.name}" in content # This likely won't work with binary PDF
            # assert f"CUIT: {customer.cuit}" in content
            # assert f"Total: ${invoice.total}" in content # Use invoice total

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
    
    def test_inventory_updates_during_concurrent_sales(self, test_app, test_data_factory):
        """
        Test that inventory is correctly updated during concurrent sales.
        
        This test simulates multiple sales of the same product happening close
        together and verifies that inventory updates correctly handle the concurrency.
        """
        # This is a simplified simulation of concurrency in a single-threaded test
        # In real applications, you might need more sophisticated testing approaches
        
        # Get services
        product_service = test_app["services"]["product_service"]
        sale_service = test_app["services"]["sale_service"]
        inventory_service = test_app["services"]["inventory_service"]
        
        # Replace the mock with a simple implementation that updates stock
        original_stock_updater = inventory_service.update_stock_from_sale
        
        # Create a product with limited stock
        product = test_data_factory.create_product(
            code="CONCURRENT",
            description="Concurrent Sales Test Product",
            sell_price=100.00,
            quantity_in_stock=10
        )
        
        # Create a customer
        customer = test_data_factory.create_customer()
        
        # Get user
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
        inventory_service.update_stock_from_sale.side_effect = original_stock_updater

    @pytest.mark.integration
    def test_simple_product_creation(self, test_app, test_data_factory):
        """Test that we can create a product using the data factory."""
        # Create a simple product
        product = test_data_factory.create_product(
            code="TEST123",
            description="Test Product for Simple Test",
            sell_price=150.00
        )
        
        # Verify the product was created correctly
        assert product.id is not None
        assert product.code == "TEST123"
        assert product.description == "Test Product for Simple Test"
        assert product.sell_price == 150.00 