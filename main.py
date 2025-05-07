from contextlib import contextmanager
from typing import Callable
import sys
import os

from PySide6.QtWidgets import QApplication, QDialog

# Core application non-UI imports
from core.services.customer_service import CustomerService
from core.services.corte_service import CorteService
from core.services.inventory_service import InventoryService
from core.services.invoicing_service import InvoicingService
from core.services.purchase_service import PurchaseService
from core.services.product_service import ProductService
from core.services.reporting_service import ReportingService
from core.services.sale_service import SaleService
from core.services.user_service import UserService

from core.interfaces.repository_interfaces import (
    IProductRepository, IDepartmentRepository, IInventoryRepository, ISaleRepository,
    ICustomerRepository, ICreditPaymentRepository, IUserRepository,
    IPurchaseOrderRepository, ISupplierRepository, ICashDrawerRepository,
    IInvoiceRepository
)
from infrastructure.persistence.sqlite.database import init_db, SessionLocal
from infrastructure.persistence.sqlite.repositories import (
    SqliteProductRepository, SqliteDepartmentRepository, SqliteInventoryRepository,
    SqliteSaleRepository, SqliteCustomerRepository, SqliteCreditPaymentRepository,
    SqliteSupplierRepository, SqlitePurchaseOrderRepository, SqliteUserRepository,
    SqliteCashDrawerRepository, SqliteInvoiceRepository
)
from infrastructure.persistence.utils import session_scope

# Note: ui.resources.resources, ui.main_window, and LoginDialog will be imported inside main()

def main(test_mode=False, test_user=None, mock_services=None):
    """
    Main application entry point.
    
    Args:
        test_mode: If True, enables testing mode bypassing login dialog
        test_user: A pre-authenticated user object to use in test mode
        mock_services: A dictionary of mock services to use in test mode
    
    Returns:
        In test mode, returns a tuple of (app, main_window) for testing
        In normal mode, the function doesn't return (calls sys.exit)
    """
    # --- Application Setup (Step 1: QApplication) ---
    app_args = sys.argv if sys.argv else []
    app = QApplication.instance() 
    if app is None:
        app = QApplication(app_args) 

    # --- Platform Specific Fixes (Step 2) ---
    if sys.platform == 'win32':
        os.environ['QT_QPA_PLATFORM'] = 'windows:darkmode=0'
    
    # --- Database Initialization (Step 3) ---
    init_db() 

    # --- UI Imports (Step 4: AFTER QApplication and init_db) ---
    import ui.resources.resources 
    import ui.main_window
    from ui.dialogs.login_dialog import LoginDialog

    # Use provided mock services in test mode or create real services
    if test_mode and mock_services:
        # Use mock services provided for testing
        product_service = mock_services.get('product_service')
        inventory_service = mock_services.get('inventory_service')
        sale_service = mock_services.get('sale_service')
        customer_service = mock_services.get('customer_service')
        purchase_service = mock_services.get('purchase_service')
        invoicing_service = mock_services.get('invoicing_service')
        corte_service = mock_services.get('corte_service')
        reporting_service = mock_services.get('reporting_service')
        user_service = mock_services.get('user_service')
    else:
        # --- Repository Factories --- #
        # Define functions that take a session and return a repository instance
        def get_inventory_repo(session): return SqliteInventoryRepository(session)
        def get_product_repo(session): return SqliteProductRepository(session)
        def get_dept_repo(session): return SqliteDepartmentRepository(session)
        def get_sale_repo(session): return SqliteSaleRepository(session)
        def get_customer_repo(session): return SqliteCustomerRepository(session)
        def get_credit_payment_repo(session): return SqliteCreditPaymentRepository(session)
        def get_supplier_repo(session): return SqliteSupplierRepository(session)
        def get_po_repo(session): return SqlitePurchaseOrderRepository(session)
        def get_cash_drawer_repo(session): return SqliteCashDrawerRepository(session)
        def get_invoice_repo(session): return SqliteInvoiceRepository(session)
        def get_user_repo(session): return SqliteUserRepository(session)

        # --- Service Instantiation (Requires specific handling for initial User Setup/Login) ---
        # Create UserService instance needed *before* main window loop for login
        user_service = None
        try:
            with session_scope() as session:
                user_repo_instance = get_user_repo(session)
                user_service = UserService(user_repo_instance) # Pass the INSTANCE

                # --- Add default admin user if not exists ---
                try:
                    print("Attempting to add admin user...")
                    admin_user = user_service.add_user("admin", "12345")
                    print(f"Admin user created successfully with ID: {admin_user.id}")
                except ValueError as e:
                    if "already exists" in str(e):
                        print("Admin user already exists.")
                    else:
                        # Re-raise other validation errors
                        raise e
                except Exception as e:
                    print(f"An unexpected error occurred during admin user creation: {e}")
                    # Decide if you want to exit or continue
                    # sys.exit(1)

        except Exception as e:
            print(f"Failed to initialize user service or add admin user: {e}")
            if not test_mode:
                sys.exit(1) # Exit if user service cannot be initialized
            else:
                raise # Re-raise for tests to catch

        if not user_service:
            print("User service could not be created. Exiting.")
            if not test_mode:
                sys.exit(1)
            else:
                raise ValueError("User service could not be created")

        # --- Other Service Instantiation (using factories) ---
        # Use both factories and instances for improved reliability
        with session_scope() as session:
            # Create repository instances for direct use
            product_repo_instance = get_product_repo(session)
            dept_repo_instance = get_dept_repo(session)
            inventory_repo_instance = get_inventory_repo(session)
            sale_repo_instance = get_sale_repo(session)
            customer_repo_instance = get_customer_repo(session)
            credit_payment_repo_instance = get_credit_payment_repo(session)
            po_repo_instance = get_po_repo(session)
            supplier_repo_instance = get_supplier_repo(session)
            cash_drawer_repo_instance = get_cash_drawer_repo(session)
            invoice_repo_instance = get_invoice_repo(session)
            
            # Initialize services with both repository instances and factories for flexibility
            product_service = ProductService(
                product_repo=product_repo_instance,
                department_repo=dept_repo_instance,
                product_repo_factory=get_product_repo,
                department_repo_factory=get_dept_repo
            )
            
            inventory_service = InventoryService(
                inventory_repo_factory=get_inventory_repo,
                product_repo_factory=get_product_repo
            )
            
            customer_service = CustomerService(
                customer_repo_factory=get_customer_repo,
                credit_payment_repo_factory=get_credit_payment_repo
            )
    
            sale_service = SaleService(
                sale_repo_factory=get_sale_repo,
                product_repo_factory=get_product_repo,
                customer_repo_factory=get_customer_repo,
                inventory_service=inventory_service,
                customer_service=customer_service
            )
            
            purchase_service = PurchaseService(
                purchase_order_repo=get_po_repo,
                supplier_repo=get_supplier_repo,
                product_repo=get_product_repo,
                inventory_service=inventory_service
            )
            
            # Instantiate Corte Service
            corte_service = CorteService(
                sale_repository=sale_repo_instance,
                cash_drawer_repository=cash_drawer_repo_instance
            )
            
            # Use both repository instances and factories for InvoicingService
            invoicing_service = InvoicingService(
                invoice_repo_factory=get_invoice_repo,
                sale_repo_factory=get_sale_repo,
                customer_repo_factory=get_customer_repo
            )
            
            # Instantiate Reporting Service for advanced reports
            @contextmanager
            def sale_repo_factory():
                try:
                    yield sale_repo_instance
                finally:
                    pass  # No need to close since we're using the existing session
                    
            reporting_service = ReportingService(sale_repo_factory)

    if not test_mode:
        # Load custom style sheet only in normal mode.
        # If app is a MagicMock (in tests), setStyleSheet will be a mock call,
        # but we explicitly skip loading and applying it here for test_mode.
        try:
            style_file = open("ui/style.qss", "r")
            style = style_file.read()
            app.setStyleSheet(style)
            style_file.close()
            print("Loaded custom stylesheet")
        except Exception as e:
            print(f"Could not load stylesheet: {e}")

    # --- Login ---
    # In test mode with a test user, skip the login dialog
    if test_mode and test_user:
        logged_in_user = test_user
    else:
        # Pass the already created user_service instance
        login_dialog = LoginDialog(user_service)
        if login_dialog.exec() == QDialog.Accepted:
            logged_in_user = login_dialog.get_logged_in_user()
            if not logged_in_user:
                # Should not happen if dialog logic is correct, but safety check
                print("Login accepted but no user returned. Exiting.")
                if not test_mode:
                    sys.exit(1)
                else:
                    raise ValueError("Login accepted but no user returned")
        else:
            print("Login cancelled or failed. Exiting.")
            if not test_mode:
                sys.exit(0) # User cancelled
            else:
                return None, None # For tests to handle user cancellation

    # Pass services and logged in user to the main window
    main_window = ui.main_window.MainWindow(
        logged_in_user=logged_in_user, # Added
        product_service=product_service,
        inventory_service=inventory_service,
        sale_service=sale_service,
        customer_service=customer_service,
        purchase_service=purchase_service,
        invoicing_service=invoicing_service,
        corte_service=corte_service,
        reporting_service=reporting_service  # Add ReportingService to MainWindow
    )
    
    # In normal mode, show the window and run the app
    if not test_mode:
        main_window.show()
        sys.exit(app.exec())
    else:
        # In test mode, return app and main_window for testing
        return app, main_window

if __name__ == "__main__":
    main()
