import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableView, QLineEdit,
    QLabel, QSpacerItem, QSizePolicy, QApplication, QMessageBox,
    QAbstractItemView, QHeaderView
)
from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QIcon  # Add QIcon import

# Import resources
from ui.resources import resources  # Import the compiled resources

# Models and Views/Dialogs
from ui.models.table_models import ProductTableModel, Product # Assuming Product mock is there too
from ui.dialogs.department_dialog import DepartmentDialog, MockProductService_Departments # Import the dialog
from ui.dialogs.product_dialog import ProductDialog # Import the Product dialog

# Placeholder for the actual service
# from core.services.product_service import ProductService


# Mock ProductService for standalone testing - Combine product and department mocks
class MockProductService(MockProductService_Departments): # Inherit department methods
    def __init__(self):
        MockProductService_Departments.__init__(self) # Initialize parent
        self._products = [
            Product(id=1, code="P001", description="Producto de Prueba 1", cost_price=10.0, sale_price=15.0, quantity_in_stock=100, min_stock=10, uses_inventory=True, department_id=1, department_name="Depto A"),
            Product(id=2, code="P002", description="Otro Artículo", cost_price=25.5, sale_price=35.0, quantity_in_stock=5, min_stock=8, uses_inventory=True, department_id=1, department_name="Depto A"),
            Product(id=3, code="SERV01", description="Servicio Sin Inventario", cost_price=0.0, sale_price=50.0, uses_inventory=False, department_id=2, department_name="Bebidas"), # Corrected dept name
            Product(id=4, code="P003", description="Producto B bajo stock", cost_price=5.0, sale_price=8.0, quantity_in_stock=2, min_stock=5, uses_inventory=True, department_id=1, department_name="Depto A"),
        ]
        self._next_product_id = 5 # Different counter for products

    def find_product(self, search_term: str = "") -> list[Product]:
        print(f"[MockService] Searching products with term: '{search_term}'")
        # Update department names before returning, in case they changed
        dept_map = {d.id: d.name for d in self.get_all_departments()}
        updated_products = []
        for p in self._products:
            # Ensure p has department_id attribute before accessing
            dept_id = getattr(p, 'department_id', None)
            p.department_name = dept_map.get(dept_id, "-")
            updated_products.append(p)

        if not search_term:
            return updated_products
        term = search_term.lower()
        return [p for p in updated_products if term in p.code.lower() or term in p.description.lower()]

    def get_product_by_id(self, product_id: int) -> Product | None:
        dept_map = {d.id: d.name for d in self.get_all_departments()}
        for p in self._products:
            if p.id == product_id:
                dept_id = getattr(p, 'department_id', None)
                p.department_name = dept_map.get(dept_id, "-")
                return p
        return None

    # Mock product CRUD needed later for ProductDialog
    def add_product(self, product_data): # Simplified
        print(f"[MockService] Adding product: {product_data['code']}")
        # Basic duplicate code check (case-insensitive)
        if any(p.code.lower() == product_data['code'].lower() for p in self._products):
            raise ValueError(f"El código de producto '{product_data['code']}' ya existe.")

        new_prod = Product(
            id=self._next_product_id,
            code=product_data['code'],
            description=product_data['description'],
            sale_price=product_data['sale_price'],
            cost_price=product_data['cost_price'],
            department_id=product_data.get('department_id'),
            quantity_in_stock=product_data.get('quantity_in_stock', 0.0),
            min_stock=product_data.get('min_stock', 0.0),
            uses_inventory=product_data.get('uses_inventory', True),
            unit=product_data.get('unit', "U")
        )
        self._products.append(new_prod)
        self._next_product_id += 1
        return new_prod

    def update_product(self, product_id, product_data):
        print(f"[MockService] Updating product ID {product_id}")
        # Basic duplicate code check (case-insensitive, excluding self)
        if any(p.code.lower() == product_data['code'].lower() and p.id != product_id for p in self._products):
             raise ValueError(f"Ya existe otro producto con el código '{product_data['code']}'.")

        for i, p in enumerate(self._products):
            if p.id == product_id:
                # Update fields selectively
                p.code = product_data['code']
                p.description = product_data['description']
                p.sale_price = product_data['sale_price']
                p.cost_price = product_data['cost_price']
                p.department_id = product_data.get('department_id')
                # Stock is not updated directly here in this mock
                # p.quantity_in_stock = product_data.get('quantity_in_stock', p.quantity_in_stock)
                p.min_stock = product_data.get('min_stock', p.min_stock)
                p.uses_inventory = product_data.get('uses_inventory', p.uses_inventory)
                p.unit = product_data.get('unit', p.unit)
                return p
        raise ValueError("Product not found for update")

    def delete_product(self, product_id):
        print(f"[MockService] Deleting product ID: {product_id}")
        product_to_delete = self.get_product_by_id(product_id)
        if not product_to_delete:
             raise ValueError("Product not found for deletion")

        # Basic check: prevent deletion if stock > 0 and uses inventory
        if product_to_delete.uses_inventory and product_to_delete.quantity_in_stock > 0:
            raise ValueError("No se puede eliminar un producto con stock existente.")

        original_length = len(self._products)
        self._products = [p for p in self._products if p.id != product_id]
        if len(self._products) == original_length:
            # This case should technically be caught by get_product_by_id check
            raise ValueError("Product not found for deletion during filtering")

    def get_all_products(self, department_id=None):
        """Devuelve todos los productos, opcionalmente filtrados por department_id."""
        dept_map = {d.id: d.name for d in self.get_all_departments()}
        updated_products = []
        for p in self._products:
            dept_id = getattr(p, 'department_id', None)
            p.department_name = dept_map.get(dept_id, "-")
            updated_products.append(p)
        if department_id is not None:
            return [p for p in updated_products if p.department_id == department_id]
        return updated_products


class ProductsView(QWidget):
    """View for managing products."""

    def __init__(self, product_service, parent=None, enable_auto_refresh=True):
        super().__init__(parent)
        # Ensure the passed service has both product and department methods
        self.product_service = product_service
        self.setObjectName("products_view")

        self._model = ProductTableModel()

        self._init_ui()
        self._connect_signals()

        # Use QTimer for delayed initial load to ensure the event loop is running
        # Allow disabling for testing to prevent timer-related hanging
        if enable_auto_refresh:
            QTimer.singleShot(0, self.refresh_products)


    def _init_ui(self):
        """Initialize the UI components."""
        main_layout = QVBoxLayout(self)

        # --- Toolbar ---
        toolbar_layout = QHBoxLayout()
        
        # Create buttons with icons
        self.new_button = QPushButton("Nuevo")
        self.new_button.setIcon(QIcon(":/icons/icons/new.png"))
        
        self.modify_button = QPushButton("Modificar")
        self.modify_button.setIcon(QIcon(":/icons/icons/edit.png"))
        
        self.delete_button = QPushButton("Eliminar")
        self.delete_button.setIcon(QIcon(":/icons/icons/delete.png"))
        
        self.departments_button = QPushButton("Departamentos")
        self.departments_button.setIcon(QIcon(":/icons/icons/departments.png"))
        
        toolbar_layout.addWidget(self.new_button)
        toolbar_layout.addWidget(self.modify_button)
        toolbar_layout.addWidget(self.delete_button)
        toolbar_layout.addWidget(self.departments_button)

        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        toolbar_layout.addSpacerItem(spacer)

        # Add search label and field with icon
        toolbar_layout.addWidget(QLabel("Buscar:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Código o descripción...")
        self.search_input.addAction(QIcon(":/icons/icons/search.png"), QLineEdit.ActionPosition.LeadingPosition)
        toolbar_layout.addWidget(self.search_input)

        main_layout.addLayout(toolbar_layout)

        # --- Table ---
        self.table_view = QTableView()
        self.table_view.setModel(self._model)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) # Read-only
        
        # Improve row selection visibility with stronger highlight color
        self.table_view.setStyleSheet("""
            QTableView::item:selected {
                background-color: #2979ff;
                color: white;
            }
            QTableView::item:hover {
                background-color: #e3f2fd;
            }
        """)
        
        # Set better column widths
        self.table_view.horizontalHeader().setStretchLastSection(False)  # Don't stretch last section automatically
        
        # Configure column widths with proportions
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        
        # Set specific widths for each column
        column_widths = {
            0: 100,    # Código
            1: 300,    # Descripción (give more space)
            2: 100,    # Precio Venta
            3: 80,     # Stock
            4: 80,     # Mínimo
            5: 100,    # Depto
            6: 100     # Costo
        }
        
        # Apply column widths
        for col, width in column_widths.items():
            self.table_view.setColumnWidth(col, width)
        
        # Make the description column stretch
        self.table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        # Ensure alternating row colors for better readability
        self.table_view.setAlternatingRowColors(True)
        
        # Set a minimum size for the table
        self.table_view.setMinimumSize(800, 400)
        
        main_layout.addWidget(self.table_view)

    def _connect_signals(self):
        """Connect signals to slots."""
        self.new_button.clicked.connect(self.add_new_product)
        self.modify_button.clicked.connect(self.modify_selected_product)
        self.delete_button.clicked.connect(self.delete_selected_product)
        self.departments_button.clicked.connect(self.manage_departments)
        self.search_input.textChanged.connect(self.filter_products)
        self.table_view.doubleClicked.connect(self.modify_selected_product) # Double-click to modify

    def _get_selected_product(self) -> Product | None:
        """Gets the Product object from the currently selected row."""
        selected_indexes = self.table_view.selectedIndexes()
        if not selected_indexes:
            return None
            
        # Get the unique row(s) from selected indices
        selected_rows = set(index.row() for index in selected_indexes)
        if not selected_rows:
            return None
            
        # Use the first selected row
        row = next(iter(selected_rows))
        
        # Get the product directly from the model
        return self._model.get_product_at_row(row)

    @Slot()
    def refresh_products(self):
        """Fetches all products from the service and updates the table."""
        print("[ProductsView] Refreshing products...")
        search_term = self.search_input.text()
        try:
            # Now calls the combined mock service's find method
            products = self.product_service.find_product(search_term)
            self._model.update_data(products)
            print(f"[ProductsView] Found {len(products)} products.")
            
            # Ensure the first row is selected if there are products
            if products and len(products) > 0:
                self.table_view.selectRow(0)
                
        except Exception as e:
             QMessageBox.critical(self, "Error", f"No se pudieron cargar los productos: {e}")

    @Slot()
    def add_new_product(self):
        """Handles the 'New' button click."""
        print("[ProductsView] 'Add New Product' clicked.")
        # Instantiate and exec ProductDialog in 'add' mode
        product_dialog = ProductDialog(self.product_service, parent=self)
        if product_dialog.exec(): # exec() returns 1 (Accepted) if OK was clicked and accept() succeeded
            print("[ProductsView] ProductDialog accepted. Refreshing product list.")
            self.refresh_products()
        else:
             print("[ProductsView] ProductDialog cancelled.")

    @Slot()
    def modify_selected_product(self):
        """Handles the 'Modify' button click or double-click."""
        selected_product = self._get_selected_product()
        if selected_product:
            print(f"[ProductsView] 'Modify Product' clicked for: {selected_product.code}")
            # Instantiate and exec ProductDialog in 'edit' mode
            product_dialog = ProductDialog(self.product_service, product_to_edit=selected_product, parent=self)
            if product_dialog.exec():
                print("[ProductsView] ProductDialog accepted. Refreshing product list.")
                self.refresh_products()
            else:
                 print("[ProductsView] ProductDialog cancelled.")
        else:
            QMessageBox.information(self, "Modificar Producto", "Por favor, seleccione un producto de la lista.")
            print("[ProductsView] 'Modify Product' clicked, but no product selected.")

    @Slot()
    def delete_selected_product(self):
        """Handles the 'Delete' button click."""
        selected_product = self._get_selected_product()
        if not selected_product:
            QMessageBox.information(self, "Eliminar Producto", "Por favor, seleccione un producto de la lista.")
            print("[ProductsView] 'Delete Product' clicked, but no product selected.")
            return
            
        print(f"[ProductsView] 'Delete Product' clicked for: {selected_product.code}. Asking confirmation...")
        reply = QMessageBox.question(self, "Eliminar Producto",
                                     f"¿Está seguro que desea eliminar el producto '{selected_product.description}' ({selected_product.code})?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.product_service.delete_product(selected_product.id)
                print(f"[ProductsView] Product ID {selected_product.id} deleted (mock call).")
                self.refresh_products()
                QMessageBox.information(self, "Eliminar Producto", "Producto eliminado correctamente.")
            except ValueError as e: # Catch potential service errors (e.g., product has stock)
                QMessageBox.warning(self, "Eliminar Producto", f"No se pudo eliminar el producto: {e}")
            except Exception as e: # Catch other unexpected errors
                QMessageBox.critical(self, "Error", f"Ocurrió un error inesperado: {e}")

    @Slot()
    def manage_departments(self):
        """Handles the 'Departments' button click."""
        print("[ProductsView] 'Manage Departments' clicked.")
        # Instantiate and exec DepartmentDialog
        # Pass the same service instance which should handle departments
        dept_dialog = DepartmentDialog(self.product_service, parent=self)
        dept_dialog.exec()
        # Refresh product list afterwards in case department names changed
        # which might affect the display in the product table.
        print("[ProductsView] Department dialog closed. Refreshing product list.")
        self.refresh_products()


    @Slot(str)
    def filter_products(self, text: str):
        """Filters the product list based on the search input."""
        print(f"[ProductsView] Filtering products with text: '{text}'")
        self.refresh_products()


# Example of running this view directly (for testing)
if __name__ == '__main__':

    app = QApplication(sys.argv)
    # Use the combined mock service for testing
    mock_service = MockProductService()
    products_view = ProductsView(mock_service)
    products_view.setWindowTitle("Products View Test")
    products_view.setGeometry(150, 150, 800, 500)
    products_view.show()
    sys.exit(app.exec()) 