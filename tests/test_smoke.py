import sys
import pytest
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from core.models.user import User
from tests.ui.qt_test_utils import process_events

# Define mock services as in ui/main_window.py
class MockProductService:
    def get_all_products(self, department_id=None): return []
    def get_product_by_code(self, code): return None
    def find_product(self, search_term=None):
        return self.get_all_products()

class MockInventoryService:
    def get_low_stock_products(self): return []
    def get_inventory_movements(self, product_id=None): return []

class MockCustomerService:
    def get_all_customers(self): return []
    def find_customer(self, term): return []

class MockPurchaseService:
    def get_all_suppliers(self): return []
    def find_supplier(self, term): return []
    def get_all_purchase_orders(self): return []
    def find_suppliers(self, term):
        return self.find_supplier(term)
    def find_purchase_orders(self, *args, **kwargs):
        return []

class MockSaleService:
    def get_all_sales(self): return []

class MockInvoicingService:
    def get_all_invoices(self): return []

class MockCorteService:
    def get_corte_data(self, user_id): return {}

class MockReportingService:
    def get_report_data(self): return {}

@pytest.mark.smoke
@pytest.mark.ui
def test_main_window_starts_and_shows(safe_qtbot):
    # Use the safe_qtbot which tracks widgets for cleanup
    main_win = None
    try:
        # Create a mock user
        mock_user = User(id=0, username="testuser", password_hash="")
        
        # Create the main window with mock services
        main_win = MainWindow(
            logged_in_user=mock_user,
            product_service=MockProductService(),
            inventory_service=MockInventoryService(),
            sale_service=MockSaleService(),
            customer_service=MockCustomerService(),
            purchase_service=MockPurchaseService(),
            invoicing_service=MockInvoicingService(),
            corte_service=MockCorteService(),
            reporting_service=MockReportingService()
        )
        
        # Add the widget to safe_qtbot for tracking
        safe_qtbot.addWidget(main_win)
        
        # Show the window and process events
        main_win.show()
        process_events()
        
        # Verify the window is visible
        assert main_win.isVisible()
    except Exception as e:
        pytest.fail(f"Test failed with exception: {str(e)}")
    finally:
        # Ensure cleanup happens even if an assertion fails
        if main_win is not None:
            main_win.close()
            process_events()
            # The deleteLater will be handled by the safe_qtbot fixture
