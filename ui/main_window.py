import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QStatusBar, QStackedWidget, QToolBar, QWidget, QLabel,
    QVBoxLayout
)
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtCore import Qt, Slot, QSize

# Import resources
from ui.resources import resources  # Import the compiled resources

# Import actual views and services
from ui.views.products_view import ProductsView
from ui.views.inventory_view import InventoryView
from ui.views.sales_view import SalesView
from ui.views.customers_view import CustomersView
from ui.views.invoices_view import InvoicesView
from ui.views.corte_view import CorteView
from ui.views.reports_view import ReportsView
from ui.views.configuration_view import ConfigurationView
from ui.views.cash_drawer_view import CashDrawerView
from core.services.product_service import ProductService
from core.services.inventory_service import InventoryService
from core.services.sale_service import SaleService
from core.services.customer_service import CustomerService
from core.services.purchase_service import PurchaseService
from core.services.invoicing_service import InvoicingService
from core.services.corte_service import CorteService
from core.services.reporting_service import ReportingService
from core.services.cash_drawer_service import CashDrawerService
from core.models.user import User
from ui.views.suppliers_view import SuppliersView
from ui.views.purchases_view import PurchasesView

# Placeholder for future views (keep for other views)
class PlaceholderWidget(QWidget):
    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel(f"Placeholder for {name} View", self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setObjectName(f"{name.lower().replace(' ', '_')}_view_placeholder")

class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(
        self,
        logged_in_user: User,
        product_service: ProductService,
        inventory_service: InventoryService,
        sale_service: SaleService,
        customer_service: CustomerService,
        purchase_service: PurchaseService,
        invoicing_service: InvoicingService,
        corte_service: CorteService,
        reporting_service: ReportingService,  # Add ReportingService parameter
        cash_drawer_service: CashDrawerService,  # Add CashDrawerService parameter
        parent=None
    ):
        super().__init__(parent)
        self.setWindowTitle("Eleventa Clone")
        self.setGeometry(100, 100, 1000, 700)

        # Store logged in user and injected services
        self.current_user = logged_in_user
        self.product_service = product_service
        self.inventory_service = inventory_service
        self.sale_service = sale_service
        self.customer_service = customer_service
        self.purchase_service = purchase_service
        self.invoicing_service = invoicing_service
        self.corte_service = corte_service
        self.reporting_service = reporting_service  # Store the ReportingService
        self.cash_drawer_service = cash_drawer_service  # Store the CashDrawerService

        self.stacked_widget = QStackedWidget(self)
        self.setCentralWidget(self.stacked_widget)

        # --- Create Views ---
        sales_view = SalesView(
            product_service=self.product_service,
            sale_service=self.sale_service,
            customer_service=self.customer_service,
            current_user=self.current_user
        )
        products_view = ProductsView(self.product_service)
        inventory_view = InventoryView(self.inventory_service, self.product_service)
        customers_view = CustomersView(self.customer_service)
        invoices_view = InvoicesView(self.invoicing_service)
        corte_view = CorteView(
            corte_service=self.corte_service, 
            user_id=self.current_user.id if self.current_user else None
        )
        # Update ReportsView to use ReportingService instead of placeholder
        reports_view = ReportsView(self.reporting_service)  # Pass ReportingService
        config_view = ConfigurationView()  # Use the new ConfigurationView
        suppliers_view = SuppliersView(self.purchase_service)
        purchases_view = PurchasesView(
            purchase_service=self.purchase_service,
            product_service=self.product_service,
            inventory_service=self.inventory_service,
            current_user=self.current_user
        )
        cash_drawer_view = CashDrawerView(
            cash_drawer_service=self.cash_drawer_service,
            user_id=self.current_user.id if self.current_user else None
        )

        self.views = {
            "Sales": sales_view,
            "Products": products_view,
            "Inventory": inventory_view,
            "Customers": customers_view,
            "Purchases": purchases_view,
            "Invoices": invoices_view,
            "Corte": corte_view,
            "Reports": reports_view,
            "Configuration": config_view,
            "Suppliers": suppliers_view,
            "CashDrawer": cash_drawer_view,
        }

        self.view_indices = {}
        index = 0
        for name, widget in self.views.items():
            self.stacked_widget.addWidget(widget)
            self.view_indices[name] = index
            index += 1

        self._create_toolbar()
        self._create_status_bar()

        # Start at the Sales view by default
        self.switch_view(self.view_indices["Sales"])

    def _create_toolbar(self):
        """Creates the main toolbar and actions."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(32, 32))  # Larger icons
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #2c6ba5;
                spacing: 5px;
                padding: 5px;
            }
            QToolButton {
                background-color: transparent;
                border-radius: 4px;
                padding: 5px;
                color: white;
            }
            QToolButton:hover {
                background-color: #3880c4;
            }
            QToolButton:pressed {
                background-color: #1c5080;
            }
        """)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        # Define action details: (Text, View name, Icon name, Shortcut)
        actions = [
            ("F1 Ventas", "Sales", "sales", "F1"),
            ("F2 Clientes", "Customers", "customers", "F2"),
            ("F3 Productos", "Products", "products", "F3"),
            ("F4 Inventario", "Inventory", "inventory", "F4"),
            ("F5 Compras", "Purchases", "purchases", "F5"),
            ("F6 Facturas", "Invoices", "invoices", "F6"),
            ("F7 Corte", "Corte", "corte", "F7"),
            ("F8 Reportes", "Reports", "reports", "F8"),
            ("F9 Caja", "CashDrawer", "cash_drawer", "F9"),
            ("Configuración", "Configuration", "config", None),
            ("Provee&dores", "Suppliers", "suppliers", None),
        ]

        for text, view_name, icon_name, shortcut in actions:
            if view_name in self.view_indices:
                action = QAction(QIcon(f":/icons/icons/{icon_name}.png"), text, self)
                action.setStatusTip(f"Switch to {view_name} view")
                action.setIconText(text.split(" ")[0])  # Set the text that appears below the icon
                
                # Set font for action text
                font = action.font()
                font.setBold(True)
                action.setFont(font)
                
                action.triggered.connect(
                    lambda checked=False, index=self.view_indices[view_name]: self.switch_view(index)
                )
                if shortcut:
                    action.setShortcut(QKeySequence(shortcut))
                toolbar.addAction(action)
            else:
                print(f"Warning: View '{view_name}' not found for action '{text}'")

    def _create_status_bar(self):
        """Creates the status bar and adds user display."""
        self.status_bar = QStatusBar(self)
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #f5f5f5;
                border-top: 1px solid #dddddd;
            }
        """)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        if self.current_user:
            self.user_label = QLabel(f" Usuario: {self.current_user.username} ")
            self.user_label.setStyleSheet("""
                background-color: #e6e6e6;
                color: #2c6ba5;
                padding: 3px 10px;
                border-radius: 3px;
                margin: 2px;
                font-weight: bold;
            """)
            self.status_bar.addPermanentWidget(self.user_label)

    @Slot(int)
    def switch_view(self, index: int):
        """Switches the central widget to the view at the given index."""
        if 0 <= index < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(index)
            current_widget = self.stacked_widget.widget(index)
            view_name = "Unknown"
            for name, idx in self.view_indices.items():
                if idx == index:
                    view_name = name
                    break
            self.status_bar.showMessage(f"{view_name} View Active")
        else:
            print(f"Error: Invalid view index {index}")

if __name__ == '__main__':
    class MockProductService:
        def get_all_products(self, department_id=None):
            return []
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

    class MockCashDrawerService:
        def get_cash_drawer_data(self, user_id): return {}

    mock_user = User(id=0, username="testuser", password_hash="")

    app = QApplication(sys.argv)
    main_win = MainWindow(
        logged_in_user=mock_user,
        product_service=MockProductService(),
        inventory_service=MockInventoryService(),
        sale_service=MockSaleService(),
        customer_service=MockCustomerService(),
        purchase_service=MockPurchaseService(),
        invoicing_service=MockInvoicingService(),
        corte_service=MockCorteService(),
        reporting_service=MockReportingService(),
        cash_drawer_service=MockCashDrawerService()
    )

    main_win.show()
    sys.exit(app.exec())
