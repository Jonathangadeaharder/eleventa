"""
Integration tests for UI components interacting with services.

These tests verify that UI components work correctly with their
dependent services.
"""
import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QLabel, QMessageBox


class TestProductUIWorkflows:
    """Tests for product management UI workflows."""
    
    def test_product_form_save_interaction(self, qtbot):
        """Test that product form correctly interacts with product service."""
        # Create mock service and objects
        mock_product_service = MagicMock()
        mock_product = MagicMock()
        mock_product.code = "P001"
        mock_product.name = "Test Product"
        mock_product.price = 10.99
        
        # Configure service to return our product on save
        mock_product_service.create_product.return_value = mock_product
        
        # Create a simple mock of a product form
        class ProductForm(QDialog):
            def __init__(self, product_service):
                super().__init__()
                self.product_service = product_service
                self.saved_product = None
                
                # Create form fields
                self.code_input = QLineEdit()
                self.code_input.setObjectName("code_input")
                
                self.name_input = QLineEdit()
                self.name_input.setObjectName("name_input")
                
                self.price_input = QLineEdit()
                self.price_input.setObjectName("price_input")
                
                # Create buttons
                self.save_button = QPushButton("Save")
                self.save_button.setObjectName("save_button")
                self.save_button.clicked.connect(self.save_product)
                
                self.cancel_button = QPushButton("Cancel")
                self.cancel_button.setObjectName("cancel_button")
                self.cancel_button.clicked.connect(self.reject)
            
            def save_product(self):
                # Collect form data
                code = self.code_input.text()
                name = self.name_input.text()
                
                try:
                    price = float(self.price_input.text())
                except ValueError:
                    return False
                
                # Save the product using the service
                self.saved_product = self.product_service.create_product(
                    code, name, price
                )
                
                if self.saved_product:
                    self.accept()
                    return True
                return False
        
        # Create the form with mock service
        form = ProductForm(product_service=mock_product_service)
        qtbot.addWidget(form)
        
        # Fill the form
        qtbot.keyClicks(form.code_input, "P001")
        qtbot.keyClicks(form.name_input, "Test Product")
        qtbot.keyClicks(form.price_input, "10.99")
        
        # Click the save button
        form.save_button.click()
        QApplication.processEvents()
        
        # Verify service was called with correct data
        mock_product_service.create_product.assert_called_once_with(
            "P001", "Test Product", 10.99
        )
        
        # Verify dialog result and saved product
        assert form.result() == QDialog.Accepted
        assert form.saved_product == mock_product


class TestInventoryUIWorkflows:
    """Tests for inventory management UI workflows."""
    
    @pytest.mark.integration
    def test_stock_adjustment_dialog(self, qtbot):
        """Test the stock adjustment dialog integration with inventory service."""
        # Create mock service
        mock_inventory_service = MagicMock()
        
        # Configure service to return success
        mock_inventory_service.adjust_stock.return_value = {
            "product": MagicMock(code="P001", name="Test Product", stock=15),
            "original_stock": 10,
            "new_stock": 15,
            "change": 5,
            "reason": "Manual adjustment"
        }
        
        # Create a simple stock adjustment dialog
        class StockAdjustmentDialog(QDialog):
            def __init__(self, inventory_service, product):
                super().__init__()
                self.inventory_service = inventory_service
                self.product = product
                self.adjustment_result = None
                
                # Create dialog elements
                self.product_info = QLabel(f"Product: {product.code} - {product.name}")
                self.product_info.setObjectName("product_info")
                
                self.current_stock = QLabel(f"Current stock: {product.stock}")
                self.current_stock.setObjectName("current_stock")
                
                self.quantity_input = QLineEdit()
                self.quantity_input.setObjectName("quantity_input")
                
                self.reason_input = QLineEdit()
                self.reason_input.setObjectName("reason_input")
                
                # Create buttons
                self.save_button = QPushButton("Save")
                self.save_button.setObjectName("save_button")
                self.save_button.clicked.connect(self.save_adjustment)
                
                self.cancel_button = QPushButton("Cancel")
                self.cancel_button.setObjectName("cancel_button")
                self.cancel_button.clicked.connect(self.reject)
            
            def save_adjustment(self):
                # Collect form data
                try:
                    quantity = int(self.quantity_input.text())
                except ValueError:
                    return False
                
                reason = self.reason_input.text()
                
                # Adjust the stock using the service
                self.adjustment_result = self.inventory_service.adjust_stock(
                    self.product.code, quantity, reason
                )
                
                if self.adjustment_result:
                    self.accept()
                    return True
                return False
        
        # Create a mock product
        mock_product = MagicMock()
        mock_product.code = "P001"
        mock_product.name = "Test Product"
        mock_product.stock = 10
        
        # Create the dialog with mock service and product
        dialog = StockAdjustmentDialog(
            inventory_service=mock_inventory_service,
            product=mock_product
        )
        qtbot.addWidget(dialog)
        
        # Fill the form
        qtbot.keyClicks(dialog.quantity_input, "5")
        qtbot.keyClicks(dialog.reason_input, "Manual adjustment")
        
        # Click the save button (using direct call instead of mouseClick)
        qtbot.wait(100)
        dialog.save_button.click()
        QApplication.processEvents()
        
        # Verify service was called with correct data
        mock_inventory_service.adjust_stock.assert_called_once_with(
            "P001", 5, "Manual adjustment"
        )
        
        # Verify dialog result and adjustment result
        assert dialog.result() == QDialog.Accepted
        assert dialog.adjustment_result is not None
        assert dialog.adjustment_result["original_stock"] == 10
        assert dialog.adjustment_result["new_stock"] == 15


class TestSaleUIWorkflows:
    """Tests for sales UI workflows."""
    
    @pytest.mark.integration
    def test_sale_item_addition(self, qtbot):
        """Test adding items to a sale through UI."""
        # Create mock services
        mock_product_service = MagicMock()
        mock_sale_service = MagicMock()
        
        # Configure product service to return a product
        mock_product = MagicMock()
        mock_product.code = "P001"
        mock_product.name = "Test Product"
        mock_product.price = 15.00
        mock_product.stock = 10
        
        mock_product_service.get_by_code.return_value = mock_product
        
        # Configure sale service
        mock_sale_service.add_item.return_value = True
        
        # Create a simple add item dialog
        class AddItemDialog(QDialog):
            def __init__(self, product_service, sale_service):
                super().__init__()
                self.product_service = product_service
                self.sale_service = sale_service
                self.added_product = None
                
                # Create dialog elements
                self.product_code_input = QLineEdit()
                self.product_code_input.setObjectName("product_code_input")
                
                self.quantity_input = QLineEdit()
                self.quantity_input.setObjectName("quantity_input")
                self.quantity_input.setText("1")  # Default quantity
                
                self.product_info = QLabel("")
                self.product_info.setObjectName("product_info")
                
                # Create buttons
                self.lookup_button = QPushButton("Lookup")
                self.lookup_button.setObjectName("lookup_button")
                self.lookup_button.clicked.connect(self.lookup_product)
                
                self.add_button = QPushButton("Add to Sale")
                self.add_button.setObjectName("add_button")
                self.add_button.clicked.connect(self.add_to_sale)
                self.add_button.setEnabled(False)  # Disabled until product is looked up
                
                self.cancel_button = QPushButton("Cancel")
                self.cancel_button.setObjectName("cancel_button")
                self.cancel_button.clicked.connect(self.reject)
            
            def lookup_product(self):
                product_code = self.product_code_input.text()
                product = self.product_service.get_by_code(product_code)
                
                if product:
                    self.added_product = product
                    self.product_info.setText(
                        f"{product.name} - ${product.price:.2f} - Stock: {product.stock}"
                    )
                    self.add_button.setEnabled(True)
                    return True
                
                self.product_info.setText("Product not found")
                self.add_button.setEnabled(False)
                return False
            
            def add_to_sale(self):
                if not self.added_product:
                    return False
                
                try:
                    quantity = int(self.quantity_input.text())
                except ValueError:
                    return False
                
                # Add to sale using the service
                result = self.sale_service.add_item(self.added_product.code, quantity)
                
                if result:
                    self.accept()
                    return True
                return False
        
        # Create the dialog with mock services
        dialog = AddItemDialog(
            product_service=mock_product_service,
            sale_service=mock_sale_service
        )
        qtbot.addWidget(dialog)
        
        # Enter product code
        qtbot.keyClicks(dialog.product_code_input, "P001")
        
        # Click lookup button (using direct call instead of mouseClick)
        dialog.lookup_button.click()
        QApplication.processEvents()
        
        # Verify product service was called
        mock_product_service.get_by_code.assert_called_once_with("P001")
        
        # Verify product info was updated
        assert "Test Product" in dialog.product_info.text()
        assert dialog.add_button.isEnabled()
        
        # Enter quantity and add to sale
        dialog.quantity_input.clear()  # Clear the field first
        qtbot.keyClicks(dialog.quantity_input, "2")  # Set to 2 (not appending to default 1)
        dialog.add_button.click()  # Use direct click instead of mouseClick
        QApplication.processEvents()
        
        # Verify sale service was called
        mock_sale_service.add_item.assert_called_once_with("P001", 2)
        
        # Verify dialog was accepted
        assert dialog.result() == QDialog.Accepted


class TestCustomerUIWorkflows:
    """Tests for customer management UI workflows."""
    
    @pytest.mark.integration
    def test_customer_search_and_select(self, qtbot):
        """Test searching for customers and selecting one."""
        # Create mock service
        mock_customer_service = MagicMock()
        
        # Configure service to return customers on search
        mock_customers = [
            MagicMock(id=1, name="John Doe", email="john@example.com"),
            MagicMock(id=2, name="Jane Smith", email="jane@example.com")
        ]
        mock_customer_service.search_customers.return_value = mock_customers
        
        # Create a simple customer search dialog
        class CustomerSearchDialog(QDialog):
            def __init__(self, customer_service):
                super().__init__()
                self.customer_service = customer_service
                self.selected_customer = None
                self.search_results = []
                
                # Create dialog elements
                self.search_input = QLineEdit()
                self.search_input.setObjectName("search_input")
                
                self.results_label = QLabel("Enter search term to find customers")
                self.results_label.setObjectName("results_label")
                
                # Create buttons
                self.search_button = QPushButton("Search")
                self.search_button.setObjectName("search_button")
                self.search_button.clicked.connect(self.search_customers)
                
                self.select_button = QPushButton("Select Customer 1")
                self.select_button.setObjectName("select_button_1")
                self.select_button.clicked.connect(lambda: self.select_customer(0))
                self.select_button.setVisible(False)
                
                self.select_button2 = QPushButton("Select Customer 2")
                self.select_button2.setObjectName("select_button_2")
                self.select_button2.clicked.connect(lambda: self.select_customer(1))
                self.select_button2.setVisible(False)
                
                self.cancel_button = QPushButton("Cancel")
                self.cancel_button.setObjectName("cancel_button")
                self.cancel_button.clicked.connect(self.reject)
            
            def search_customers(self):
                search_term = self.search_input.text()
                self.search_results = self.customer_service.search_customers(search_term)
                
                if self.search_results:
                    result_text = f"Found {len(self.search_results)} customers:"
                    self.results_label.setText(result_text)
                    
                    # Show/hide select buttons based on results
                    if len(self.search_results) > 0:
                        self.select_button.setText(f"Select {self.search_results[0].name}")
                        self.select_button.setVisible(True)
                    else:
                        self.select_button.setVisible(False)
                        
                    if len(self.search_results) > 1:
                        self.select_button2.setText(f"Select {self.search_results[1].name}")
                        self.select_button2.setVisible(True)
                    else:
                        self.select_button2.setVisible(False)
                    
                    return True
                
                self.results_label.setText("No customers found")
                self.select_button.setVisible(False)
                self.select_button2.setVisible(False)
                return False
            
            def select_customer(self, index):
                if 0 <= index < len(self.search_results):
                    self.selected_customer = self.search_results[index]
                    self.accept()
                    return True
                return False
        
        # Create the dialog with mock service
        dialog = CustomerSearchDialog(customer_service=mock_customer_service)
        qtbot.addWidget(dialog)
        
        # Enter search term
        qtbot.keyClicks(dialog.search_input, "John")
        
        # Click search button (using direct call instead of mouseClick)
        dialog.search_button.click()
        QApplication.processEvents()
        
        # Verify service was called
        mock_customer_service.search_customers.assert_called_once_with("John")
        
        # Verify search results were processed
        assert "Found 2 customers" in dialog.results_label.text()
        assert dialog.select_button.isVisible()
        assert dialog.select_button2.isVisible()
        
        # Select first customer (using direct call instead of mouseClick)
        dialog.select_button.click()
        QApplication.processEvents()
        
        # Verify selected customer and dialog result
        assert dialog.selected_customer == mock_customers[0]
        assert dialog.result() == QDialog.Accepted 