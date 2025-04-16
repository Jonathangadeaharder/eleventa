"""
Direct script to run product dialog tests outside of pytest framework.
This avoids issues with pytest and dialog testing.
"""
import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog

# Patch Qt classes
def patch_qt_classes():
    """Patch Qt dialog classes to prevent them from blocking."""
    print("Patching Qt dialog classes...")
    QDialog.exec = lambda *args, **kwargs: 1  # Return Accepted (1)
    QMessageBox.exec = lambda *args, **kwargs: QMessageBox.Ok
    QMessageBox.information = lambda *args, **kwargs: QMessageBox.Ok
    QMessageBox.warning = lambda *args, **kwargs: QMessageBox.Ok
    QMessageBox.critical = lambda *args, **kwargs: QMessageBox.Ok
    print("Patching completed")
    
def run_product_dialog_test():
    """Run the product dialog test directly."""
    from PySide6 import QtWidgets
    from ui.dialogs.product_dialog import ProductDialog
    from core.models.product import Product
    
    # Create a mock product service
    class MockProductService:
        def __init__(self):
            self.added_product = None
            self.updated_product = None
        
        def add_product(self, product):
            print(f"MockProductService.add_product called with {product.code}")
            self.added_product = product
            return product
            
        def update_product(self, product):
            print(f"MockProductService.update_product called with {product.code}")
            self.updated_product = product
            return product
            
        def get_all_departments(self):
            print("MockProductService.get_all_departments called")
            return [
                type("Department", (), {"id": 1, "name": "Beverages"})(),
                type("Department", (), {"id": 2, "name": "Snacks"})(),
            ]
    
    # Create the dialog
    service = MockProductService()
    dialog = ProductDialog(product_service=service)
    
    # Set form fields
    dialog.code_input.setText("P003")
    dialog.description_input.setText("New Product")
    dialog.sale_price_input.setValue(12.5)
    dialog.department_combo.setCurrentIndex(1)
    dialog.inventory_checkbox.setChecked(True)
    dialog.stock_input.setValue(20)
    dialog.min_stock_input.setValue(2)
    
    # Accept the dialog (trigger validation and saving)
    print("Accepting dialog...")
    result = dialog.accept()
    print(f"Dialog accepted with result: {result}")
    
    # Verify the product was added correctly
    if service.added_product is not None:
        print("Test PASSED: Product was added to service")
        print(f"  Code: {service.added_product.code}")
        print(f"  Description: {service.added_product.description}")
        print(f"  Price: {service.added_product.sell_price}")
        print(f"  Inventory: {service.added_product.uses_inventory}")
        print(f"  Stock: {service.added_product.quantity_in_stock}")
    else:
        print("Test FAILED: No product was added to service")
        
    return service.added_product is not None

def main():
    """Main function to set up environment and run tests."""
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Apply patches to prevent dialogs from blocking
    patch_qt_classes()
    
    # Run the test
    print("\n=== Running product dialog test ===")
    success = run_product_dialog_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 