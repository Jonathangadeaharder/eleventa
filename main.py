import os
import sys
from PySide6.QtWidgets import QApplication, QDialog
from PySide6.QtCore import Qt

# --- Config and Logging Setup (Step 0) ---
from config import config, DATABASE_URL # Import the dynamically generated URL
# load_config() # Load config early - This is now done within config.py on import
# setup_logging() # Setup logging based on config - This function is not defined in config.py

# --- Alembic Migration Imports ---
from alembic.config import Config
from alembic import command

# --- Core Service and Repository Imports (Step 1) ---
# Services (alphabetical)
from core.services.cash_drawer_service import CashDrawerService
from core.services.corte_service import CorteService
from core.services.customer_service import CustomerService
from core.services.inventory_service import InventoryService
from core.services.invoicing_service import InvoicingService
from core.services.product_service import ProductService
# from core.services.purchase_service import PurchaseService # Removed
from core.services.reporting_service import ReportingService
from core.services.sale_service import SaleService
from core.services.user_service import UserService

# ORM Models (alphabetical - these are used by repositories)
from infrastructure.persistence.sqlite.models_mapping import (
    CashDrawerEntryOrm, CreditPaymentOrm, CustomerOrm, DepartmentOrm,
    InventoryMovementOrm, InvoiceOrm, ProductOrm, # Removed PurchaseOrderItemOrm,
    # PurchaseOrderOrm, SaleItemOrm, SaleOrm, SupplierOrm, UserOrm
    SaleItemOrm, SaleOrm, UserOrm # Removed SupplierOrm, PurchaseOrderOrm, PurchaseOrderItemOrm
)

# Repository imports removed - services now use Unit of Work pattern

# --- Database Initialization (Step 2) ---
from infrastructure.persistence.sqlite.database import init_db

def run_migrations():
    """
    Programmatically runs Alembic migrations to ensure the database is up-to-date.
    """
    # Alembic needs to know where to find its configuration and scripts.
    # When frozen, the executable's path can be used to find bundled files.
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle, the PyInstaller bootloader
        # extends the sys module by a flag frozen=True and sets the app
        # path into sys._MEIPASS.
        bundle_dir = sys._MEIPASS
    else:
        # In a normal development environment
        bundle_dir = os.path.dirname(os.path.abspath(__file__))

    alembic_cfg_path = os.path.join(bundle_dir, 'alembic.ini')
    alembic_script_location = os.path.join(bundle_dir, 'alembic')

    try:
        print("Running database migrations...")
        alembic_cfg = Config(alembic_cfg_path)
        alembic_cfg.set_main_option("script_location", alembic_script_location)
        alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
        command.upgrade(alembic_cfg, "head")
        print("Migrations complete.")
    except Exception as e:
        print(f"Error running migrations: {e}")
        # In a real application, you might want to show an error dialog here
        # and exit gracefully.
        sys.exit(1)

def main(test_mode=False, test_user=None, mock_services=None):
    """
    Initializes and runs the Eleventa application.

    Order of operations:
    1. QApplication initialization.
    2. Platform-specific fixes (e.g., Qt for Windows).
    3. Database initialization (init_db).
    4. UI Imports (MainWindow, Dialogs) - AFTER QApplication and init_db.
    5. Service and Repository Instantiation (or use mocks).
    6. Login Dialog.
    7. Main Window display and application execution.

    Args:
        test_mode: If True, enables testing mode bypassing login dialog
        test_user: A pre-authenticated user object to use in test mode
        mock_services: A dictionary of mock services to use in test mode

    Returns:
        In test mode, returns a tuple of (app, main_window) for testing
        In normal mode, the function doesn't return (calls sys.exit)
    """
    # --- Application Setup (Early Step: QApplication) ---
    app_args = sys.argv if sys.argv else []
    app = QApplication.instance()
    if app is None:
        app = QApplication(app_args)

    # --- Platform Specific Fixes ---
    if sys.platform == 'win32':
        os.environ['QT_QPA_PLATFORM'] = 'windows:darkmode=0'

    # --- Database Initialization and Migration ---
    # The init_db() function from the original code, which creates tables
    # from SQLAlchemy's Base.metadata, is now superseded by Alembic's
    # migration system. It should be removed or commented out.
    # init_db() # REMOVE THIS LINE
    run_migrations() # ADD THIS LINE

    # --- UI Imports (AFTER QApplication and init_db) ---
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
        # purchase_service = mock_services.get('purchase_service') # Removed
        invoicing_service = mock_services.get('invoicing_service')
        corte_service = mock_services.get('corte_service')
        reporting_service = mock_services.get('reporting_service')
        user_service = mock_services.get('user_service')
        cash_drawer_service = mock_services.get('cash_drawer_service')
    else:
        # Repository factories are no longer needed as services use Unit of Work pattern

        # --- Service Instantiation (using Unit of Work pattern) ---
        user_service = UserService()

        try:
            print("Attempting to add admin user...")
            admin_user = user_service.add_user("admin", "12345")
            if admin_user:
                print(f"Admin user created/verified successfully with ID: {admin_user.id}")
            else:
                print("Admin user already exists or was not created.")
        except ValueError as e:
            if "already exists" in str(e).lower():
                print("Admin user already exists.")
            else:
                print(f"ValueError during admin user creation: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during admin user creation: {e}")

        product_service = ProductService()
        inventory_service = InventoryService()
        customer_service = CustomerService()
        
        sale_service = SaleService(
            inventory_service=inventory_service,
            customer_service=customer_service
        )

        corte_service = CorteService()
        invoicing_service = InvoicingService()
        reporting_service = ReportingService()
        cash_drawer_service = CashDrawerService()

    if not test_mode:
        try:
            with open("ui/style.qss", "r") as style_file:
                style = style_file.read()
            app.setStyleSheet(style)
            print("Loaded custom stylesheet")
        except Exception as e:
            print(f"Could not load stylesheet: {e}")

    # --- Login ---
    if test_mode and test_user:
        logged_in_user = test_user
    else:
        login_dialog = LoginDialog(user_service)
        if login_dialog.exec() == QDialog.Accepted:
            logged_in_user = login_dialog.get_logged_in_user()
            if not logged_in_user:
                print("Login accepted but no user returned. Exiting.")
                if not test_mode: sys.exit(1)
                else: raise ValueError("Login accepted but no user returned")
        else:
            print("Login cancelled or failed. Exiting.")
            if not test_mode: sys.exit(0)
            else: return None, None

    main_window = ui.main_window.MainWindow(
        logged_in_user=logged_in_user,
        product_service=product_service,
        inventory_service=inventory_service,
        sale_service=sale_service,
        customer_service=customer_service,
        # purchase_service=purchase_service, # Removed
        invoicing_service=invoicing_service,
        corte_service=corte_service,
        reporting_service=reporting_service,
        cash_drawer_service=cash_drawer_service
    )

    if not test_mode:
        try:
            main_window.show()
            sys.exit(app.exec())
        except Exception as e:
            print(f"Error showing main window: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        return app, main_window

if __name__ == "__main__":
    main()
