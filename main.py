import sys
from PySide6.QtWidgets import QApplication, QDialog # Added QDialog for result check
from typing import Callable

# Core Components
from core.services.product_service import ProductService
from core.services.inventory_service import InventoryService
from core.services.sale_service import SaleService
from core.services.customer_service import CustomerService
from core.services.purchase_service import PurchaseService
from core.services.user_service import UserService
from core.services.corte_service import CorteService
from core.services.invoicing_service import InvoicingService
from core.services.reporting_service import ReportingService # Add ReportingService
from core.interfaces.repository_interfaces import (
    IProductRepository, IDepartmentRepository, IInventoryRepository, ISaleRepository,
    ICustomerRepository, ICreditPaymentRepository, IUserRepository,
    IPurchaseOrderRepository, ISupplierRepository, ICashDrawerRepository,
    IInvoiceRepository
)
from infrastructure.persistence.sqlite.repositories import (
    SqliteProductRepository, SqliteDepartmentRepository, SqliteInventoryRepository, SqliteSaleRepository,
    SqliteCustomerRepository, SqliteCreditPaymentRepository, SqliteSupplierRepository, SqlitePurchaseOrderRepository,
    SqliteUserRepository, SqliteCashDrawerRepository, SqliteInvoiceRepository
)
from infrastructure.persistence.sqlite.database import init_db, SessionLocal
from infrastructure.persistence.utils import session_scope

# UI
from ui.main_window import MainWindow
from ui.dialogs.login_dialog import LoginDialog
# from config import Config # To be uncommented later

def main():
    # Initialize database and session provider
    init_db() # Make sure tables are created

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
        sys.exit(1) # Exit if user service cannot be initialized

    if not user_service:
        print("User service could not be created. Exiting.")
        sys.exit(1)

    # --- Other Service Instantiation (using factories) ---
    product_service = ProductService(get_product_repo, get_dept_repo)
    inventory_service = InventoryService(get_inventory_repo, get_product_repo)
    customer_service = CustomerService(get_customer_repo, get_credit_payment_repo) # Uses factories

    # Adjust services to use factory functions directly
    sale_service = SaleService(get_sale_repo, get_product_repo, inventory_service, customer_service) # Uses factories + instance
    purchase_service = PurchaseService(
        purchase_order_repo=get_po_repo, # Pass factory
        supplier_repo=get_supplier_repo,   # Pass factory
        product_repo=get_product_repo,     # Pass factory
        inventory_service=inventory_service # Pass instance
    )
    
    # Instantiate Corte Service
    corte_service = CorteService(get_sale_repo, get_cash_drawer_repo)
    
    # Instantiate Invoicing Service with factory functions
    invoicing_service = InvoicingService(
        invoice_repo=get_invoice_repo, 
        sale_repo=get_sale_repo, 
        customer_repo=get_customer_repo
    )
    
    # Instantiate Reporting Service for advanced reports
    reporting_service = ReportingService(get_sale_repo)

    # --- Application Setup ---
    app = QApplication(sys.argv)

    # --- Login ---
    # Pass the already created user_service instance
    login_dialog = LoginDialog(user_service)
    if login_dialog.exec() == QDialog.Accepted:
        logged_in_user = login_dialog.get_logged_in_user()
        if not logged_in_user:
            # Should not happen if dialog logic is correct, but safety check
            print("Login accepted but no user returned. Exiting.")
            sys.exit(1)
    else:
        print("Login cancelled or failed. Exiting.")
        sys.exit(0) # User cancelled

    # Pass services and logged in user to the main window
    main_window = MainWindow(
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
    main_window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
