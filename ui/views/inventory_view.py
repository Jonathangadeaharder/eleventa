from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget, QTableView,
    QLabel, QSpacerItem, QSizePolicy, QFrame, QHeaderView, QLineEdit, QMessageBox,
    QDialog # Import QDialog
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QIcon, QStandardItemModel, QStandardItem, QFont
from typing import Optional
from datetime import datetime, timedelta

# Adjust imports based on actual project structure
from core.services.inventory_service import InventoryService
from core.services.product_service import ProductService
from core.models.user import User
from ui.models.table_models import ProductTableModel # Assuming reuse initially
from ui.utils import show_error_message, ask_confirmation # Assuming utility functions
from ui.dialogs.add_inventory_dialog import AddInventoryDialog # Import the dialog
from ui.dialogs.adjust_inventory_dialog import AdjustInventoryDialog # Import the new dialog
from ui.dialogs.import_export_dialog import ImportExportDialog # Import the import/export dialog
from core.models.product import Product # Import Product model
from ui.widgets.filter_dropdowns import FilterBoxWidget, FilterDropdown, PeriodFilterWidget

class InventoryView(QWidget):
    """View for managing inventory reports and actions."""

    def __init__(self, inventory_service: InventoryService, product_service: ProductService, current_user: Optional[User] = None, parent=None):
        super().__init__(parent)
        self.inventory_service = inventory_service
        self.product_service = product_service
        self.current_user = current_user

        # Models for the tables
        self.inventory_report_model = ProductTableModel(self)
        self.low_stock_model = ProductTableModel(self)

        self._setup_ui()
        self._connect_signals()
        self.refresh_inventory_report() # Load initial report

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Toolbar --- (Using buttons as a simple toolbar)
        toolbar_layout = QHBoxLayout()
        self.add_button = QPushButton(QIcon(":/icons/icons/new.png"), " Agregar Cantidad")
        self.adjust_button = QPushButton(QIcon(":/icons/icons/edit.png"), " Ajustar Stock")
        self.import_export_button = QPushButton(QIcon(":/icons/icons/import.png"), " Importar/Exportar")
        self.report_button = QPushButton(QIcon(":/icons/icons/reports.png"), " Reporte de Inventario")
        self.low_stock_button = QPushButton(QIcon(":/icons/icons/inventory.png"), " Productos Bajos")
        self.movements_button = QPushButton(QIcon(":/icons/icons/inventory.png"), " Movimientos")
        self.kardex_button = QPushButton(QIcon(":/icons/icons/inventory.png"), " Kardex")

        # Disable unimplemented features
        self.movements_button.setEnabled(False)
        self.kardex_button.setEnabled(False)
        # Add/Adjust might be triggered from selection later (TASK-018)
        # self.add_button.setEnabled(False) 
        # self.adjust_button.setEnabled(False)

        toolbar_layout.addWidget(self.add_button)
        toolbar_layout.addWidget(self.adjust_button)
        toolbar_layout.addWidget(self.import_export_button)
        toolbar_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        toolbar_layout.addWidget(self.report_button)
        toolbar_layout.addWidget(self.low_stock_button)
        toolbar_layout.addWidget(self.movements_button)
        toolbar_layout.addWidget(self.kardex_button)
        toolbar_layout.addStretch(1)
        main_layout.addLayout(toolbar_layout)

        # --- Filter section ---
        self.filter_box = FilterBoxWidget(self)
        
        # Department filter
        self.department_filter = FilterDropdown("Departamento:")
        self.filter_box.add_widget(self.department_filter)
        
        self.filter_box.add_separator()
        
        # Search field
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_label = QLabel("Buscar:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Código o descripción...")
        self.search_input.setEnabled(True)
        self.search_input.setReadOnly(False)
        self.search_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        
        search_widget = QWidget()
        search_widget.setLayout(search_layout)
        self.filter_box.add_widget(search_widget)
        
        # Add the filter box to the main layout
        main_layout.addWidget(self.filter_box)

        # --- Tab Widget ---
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # --- General Inventory Report Tab ---
        self.report_tab = QWidget()
        report_layout = QVBoxLayout(self.report_tab)

        self.report_table = QTableView()
        self.report_table.setModel(self.inventory_report_model)
        self.report_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.report_table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.report_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive) # Code
        self.report_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Description
        self.report_table.setSortingEnabled(True)
        report_layout.addWidget(self.report_table)

        # Summary labels
        summary_layout = QHBoxLayout()
        self.total_items_label = QLabel("Total Items: 0")
        self.total_cost_label = QLabel("Valor Costo: $0.00")
        self.total_sell_label = QLabel("Valor Venta: $0.00") # Added sell value
        summary_layout.addStretch(1)
        summary_layout.addWidget(self.total_items_label)
        summary_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        summary_layout.addWidget(self.total_cost_label)
        summary_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        summary_layout.addWidget(self.total_sell_label)
        summary_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        report_layout.addLayout(summary_layout)

        self.tab_widget.addTab(self.report_tab, "Reporte General")

        # --- Low Stock Report Tab ---
        self.low_stock_tab = QWidget()
        low_stock_layout = QVBoxLayout(self.low_stock_tab)

        self.low_stock_table = QTableView()
        self.low_stock_table.setModel(self.low_stock_model)
        self.low_stock_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.low_stock_table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.low_stock_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.low_stock_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive) # Code
        self.low_stock_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Description
        self.low_stock_table.setSortingEnabled(True)
        low_stock_layout.addWidget(self.low_stock_table)

        self.tab_widget.addTab(self.low_stock_tab, "Productos con Bajo Stock")

    def _connect_signals(self):
        self.report_button.clicked.connect(self._show_inventory_report_tab)
        self.low_stock_button.clicked.connect(self._show_low_stock_tab)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        # Connect add/adjust buttons (will be implemented in TASK-018)
        self.add_button.clicked.connect(self.add_inventory_item)
        self.adjust_button.clicked.connect(self.adjust_inventory_item)
        self.import_export_button.clicked.connect(self.open_import_export_dialog)
        
        # Connect filter signals
        self.department_filter.selectionChanged.connect(self._on_filter_changed)
        self.search_input.textChanged.connect(self._on_search_changed)

    def _on_tab_changed(self, index):
        """Refresh data when a tab becomes active."""
        if index == 0: # General Report
            self.refresh_inventory_report()
        elif index == 1: # Low Stock
            self.refresh_low_stock_report()

    def _show_inventory_report_tab(self):
        self.tab_widget.setCurrentIndex(0)
        # self.refresh_inventory_report() # Refresh triggered by currentChanged

    def _show_low_stock_tab(self):
        self.tab_widget.setCurrentIndex(1)
        # self.refresh_low_stock_report() # Refresh triggered by currentChanged
    
    def _on_filter_changed(self, department_id):
        """Handle when the department filter changes."""
        # Refresh the current tab with the new filter
        current_index = self.tab_widget.currentIndex()
        if current_index == 0:
            self.refresh_inventory_report()
        elif current_index == 1:
            self.refresh_low_stock_report()
    
    def _on_search_changed(self, search_text):
        """Handle when the search text changes."""
        # Apply filter after a short delay (could implement debounce here)
        current_index = self.tab_widget.currentIndex()
        if current_index == 0:
            self.refresh_inventory_report()
        elif current_index == 1:
            self.refresh_low_stock_report()

    def refresh_inventory_report(self):
        """Fetches all products and updates the general report table and totals."""
        try:
            # Get the selected department ID (if any)
            department_id = self.department_filter.get_selected_value()
            search_text = self.search_input.text().strip()
            
            # Use product service to get products with optional filtering
            if search_text:
                # Search by code or description
                products = self.product_service.search_products(search_text)
            else:
                # Get all products or by department
                products = self.product_service.get_all_products(department_id=department_id)
                
            # Filter for products that use inventory
            inventory_products = [p for p in products if p.uses_inventory]
            
            self.inventory_report_model.update_data(inventory_products)
            self._update_report_totals(inventory_products)
            print(f"Inventory report refreshed with {len(inventory_products)} items.") # Debug
        except Exception as e:
            # Pass parent, title, and message
            show_error_message(self, "Error al Cargar Reporte", f"No se pudo cargar el reporte de inventario: {e}")
            self.inventory_report_model.update_data([])
            self._update_report_totals([])

    def _update_report_totals(self, products):
        """Calculates and updates the summary labels for the general report."""
        total_items = len(products)
        total_cost = sum(p.quantity_in_stock * p.cost_price for p in products if p.quantity_in_stock is not None and p.cost_price is not None)
        total_sell = sum(p.quantity_in_stock * p.sell_price for p in products if p.quantity_in_stock is not None and p.sell_price is not None)

        self.total_items_label.setText(f"Total Items: {total_items}")
        self.total_cost_label.setText(f"Valor Costo: ${total_cost:,.2f}")
        self.total_sell_label.setText(f"Valor Venta: ${total_sell:,.2f}")

    def refresh_low_stock_report(self):
        """Fetches low stock products and updates the corresponding table."""
        try:
            # Get the selected department ID (if any)
            department_id = self.department_filter.get_selected_value()
            search_text = self.search_input.text().strip()
            
            # Get low stock products without department_id parameter
            low_stock_products = self.inventory_service.get_low_stock_products()
            
            self.low_stock_model.update_data(low_stock_products)
            print(f"Low stock report refreshed with {len(low_stock_products)} items.") # Debug
        except Exception as e:
            show_error_message(self, "Error al Cargar Productos Bajos", f"No se pudo cargar el reporte de bajo stock: {e}")
            self.low_stock_model.update_data([])

    # --- Slots for Button Actions ---

    def _get_active_table(self):
        """Gets the active table based on the current tab."""
        current_index = self.tab_widget.currentIndex()
        if current_index == 0:
            return self.report_table
        elif current_index == 1:
            return self.low_stock_table
        else:
            return None # Should not happen if tabs exist

    def _get_selected_product(self) -> Optional[Product]:
        """Gets the selected product from the currently visible table."""
        active_table = self._get_active_table()
        if not active_table:
            return None # Should not happen if tabs exist

        selected_indexes = active_table.selectionModel().selectedRows()
        if not selected_indexes:
            show_error_message(self, "Selección Requerida", "Por favor, seleccione un producto de la tabla.")
            return None

        selected_row = selected_indexes[0].row()
        model = active_table.model()
        selected_product = model.get_product_at_row(selected_row)
        return selected_product

    def add_inventory_item(self):
        """Opens the dialog to add inventory to the selected item."""
        selected_product = self._get_selected_product()
        if not selected_product:
            return

        dialog = AddInventoryDialog(self.inventory_service, selected_product, self.current_user, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Refresh the current view after adding stock
            current_index = self.tab_widget.currentIndex()
            if current_index == 0:
                self.refresh_inventory_report()
            elif current_index == 1:
                self.refresh_low_stock_report()
            # Optionally, re-select the item if needed
            print(f"Inventory added for {selected_product.code}") # Debug

    def adjust_inventory_item(self):
        """Opens the dialog to adjust stock of the selected item."""
        selected_product = self._get_selected_product()
        if not selected_product:
            return

        dialog = AdjustInventoryDialog(self.inventory_service, selected_product, self.current_user, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Refresh the current view after adjusting stock
            current_index = self.tab_widget.currentIndex()
            if current_index == 0:
                self.refresh_inventory_report()
            elif current_index == 1:
                self.refresh_low_stock_report()
            # Optionally, re-select the item if needed
            print(f"Inventory adjusted for {selected_product.code}") # Debug

    @Slot()
    def open_import_export_dialog(self):
        """Abre el diálogo de importación/exportación."""
        print("[InventoryView] 'Import/Export' clicked.")
        dialog = ImportExportDialog(self)
        if dialog.exec() == ImportExportDialog.DialogCode.Accepted:
            # Refrescar la vista actual después de una posible importación
            print("[InventoryView] Import/Export dialog accepted. Refreshing inventory view.")
            current_index = self.tab_widget.currentIndex()
            if current_index == 0:
                self.refresh_inventory_report()
            elif current_index == 1:
                self.refresh_low_stock_report()

    def showEvent(self, event):
        """Override showEvent to load filter data when the view becomes visible."""
        super().showEvent(event)
        self._load_filter_data()
    
    def _load_filter_data(self):
        """Load data for department filter dropdown."""
        try:
            departments = self.product_service.get_all_departments()
            # Add "All departments" as first item
            department_items = [("Todos los departamentos", None)] + list(departments)
            self.department_filter.set_items(department_items)
        except Exception as e:
            print(f"Error loading departments: {e}")

# Example Usage (for testing standalone)
if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QApplication
    # Mock services for standalone testing
    class MockInventoryService:
        def get_low_stock_products(self): return []
    class MockProductService:
        def get_all_products(self): return []
        def find_product(self, search_term=None):
            return self.get_all_products()
        def get_all_products(self, department_id=None):
            # Devuelve una lista vacía o puedes simular productos si lo deseas
            return []

    # Add dummy resource file for icons (replace with actual resource handling)
    # Create a dummy resources_rc.py if needed, or remove QIcon usage for test
    # try:
    #     import resources_rc
    # except ImportError:
    #     print("Warning: Resource file not found. Icons might not display.")
    #     pass

    app = QApplication(sys.argv)
    inventory_service = MockInventoryService()
    product_service = MockProductService()
    window = InventoryView(inventory_service, product_service)
    window.setWindowTitle("Inventory View Test")
    window.setGeometry(100, 100, 800, 600)
    window.show()
    sys.exit(app.exec())