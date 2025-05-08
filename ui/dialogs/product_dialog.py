import sys
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QDoubleSpinBox,
    QComboBox, QCheckBox, QPushButton, QLabel, QDialogButtonBox, QMessageBox,
    QApplication, QWidget, QFrame, QGroupBox, QSpacerItem, QSizePolicy # Added QGroupBox, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Slot, Signal
from PySide6.QtGui import QIcon
from typing import Optional, Dict, Any

# Assuming models and service are available (using mocks initially)
# Need Product and Department definitions
# Using definitions from other modules for consistency during development
from ui.models.table_models import Product
from ui.dialogs.department_dialog import Department

# Using the combined mock service from products_view for testing
# In real app, would import from core.services.product_service
# Ensure MockProductService has necessary methods (add_product, update_product, get_all_departments)
# We defined these in products_view.py earlier
from core.models.product import Product, Department
from core.services.product_service import ProductService # Keep this import

# Import common UI functions
from ui.utils import show_error_message, style_text_input, style_dropdown, style_primary_button, style_secondary_button, style_heading_label, apply_standard_form_style


class ProductDialog(QDialog):
    """Dialog for adding or modifying products."""
    validation_failed = Signal(str)

    def __init__(self, product_service, product_to_edit: Optional[Product] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.product_service = product_service
        self.product_to_edit = product_to_edit
        self.is_edit_mode = product_to_edit is not None

        self.setWindowTitle("Modificar Producto" if self.is_edit_mode else "Agregar Producto")
        self.setMinimumWidth(400)

        self._departments: list[Department] = [] # Cache departments

        self._init_ui()
        self._connect_signals()
        self._load_departments()

        # Make sure this is called after the UI is fully initialized
        QApplication.processEvents()

        if self.is_edit_mode:
            self._populate_form()
        else:
            # Set initial state for new product 
            # Make sure checkbox state is properly set first
            initial_inventory_enabled = True
            self.inventory_checkbox.setChecked(initial_inventory_enabled)
            self._toggle_inventory_fields(initial_inventory_enabled)
            self.adjustSize()  # Make sure dialog adjusts to content

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)
        
        # Add heading if in edit mode
        if self.is_edit_mode:
            heading = QLabel(f"Modificar Producto: {self.product_to_edit.code}")
        else:
            heading = QLabel("Nuevo Producto")
        style_heading_label(heading)
        main_layout.addWidget(heading)
        
        # Create main container frame
        container = QFrame()
        container.setFrameShape(QFrame.Shape.StyledPanel)
        container.setFrameShadow(QFrame.Shadow.Sunken)
        container.setStyleSheet("QFrame { background-color: #f9f9f9; border-radius: 4px; }")
        
        # Create layout for the container
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(15, 15, 15, 15)
        
        # Basic info group
        basic_info_group = QGroupBox("Información Básica")
        basic_info_layout = QFormLayout(basic_info_group)
        basic_info_layout.setSpacing(8)
        basic_info_layout.setContentsMargins(10, 15, 10, 10)

        # --- Form Fields ---
        self.code_input = QLineEdit()
        style_text_input(self.code_input)
        
        self.description_input = QLineEdit()
        style_text_input(self.description_input)
        
        self.sale_price_input = QDoubleSpinBox()
        self.sale_price_input.setDecimals(2)
        self.sale_price_input.setRange(0.0, 999999.99)
        self.sale_price_input.setPrefix("$ ")
        self.sale_price_input.setMinimumHeight(28)
        
        self.cost_price_input = QDoubleSpinBox()
        self.cost_price_input.setDecimals(2)
        self.cost_price_input.setRange(0.0, 999999.99)
        self.cost_price_input.setPrefix("$ ")
        self.cost_price_input.setMinimumHeight(28)
        
        self.department_combo = QComboBox()
        style_dropdown(self.department_combo)
        
        self.unit_input = QLineEdit("U") # Default unit
        style_text_input(self.unit_input)
        
        basic_info_layout.addRow("Código:", self.code_input)
        basic_info_layout.addRow("Descripción:", self.description_input)
        basic_info_layout.addRow("Precio Venta:", self.sale_price_input)
        basic_info_layout.addRow("Precio Costo:", self.cost_price_input)
        basic_info_layout.addRow("Departamento:", self.department_combo)
        basic_info_layout.addRow("Unidad Venta:", self.unit_input)
        
        # Add basic info group to container
        container_layout.addWidget(basic_info_group)
        
        # Inventory group
        inventory_group = QGroupBox("Información de Inventario")
        inventory_layout = QVBoxLayout(inventory_group)
        inventory_layout.setContentsMargins(10, 15, 10, 10)
        inventory_layout.setSpacing(8)
        
        self.inventory_checkbox = QCheckBox("Controlar Stock")
        self.inventory_checkbox.setChecked(True) # Default to tracking inventory
        inventory_layout.addWidget(self.inventory_checkbox)
        
        # Create a form for inventory fields
        inventory_form = QFormLayout()
        inventory_form.setContentsMargins(20, 5, 5, 5) # Indent the form
        
        self.stock_input = QDoubleSpinBox()
        self.stock_input.setDecimals(2)
        self.stock_input.setRange(-99999.99, 999999.99) # Allow negative temporarily if needed
        self.stock_input.setMinimumHeight(28)
        
        self.min_stock_input = QDoubleSpinBox()
        self.min_stock_input.setDecimals(2)
        self.min_stock_input.setRange(0.0, 999999.99)
        self.min_stock_input.setMinimumHeight(28)
        
        self.stock_label = QLabel("Stock Actual:")
        inventory_form.addRow(self.stock_label, self.stock_input)
        
        self.min_stock_label = QLabel("Stock Mínimo:")
        inventory_form.addRow(self.min_stock_label, self.min_stock_input)
        
        inventory_layout.addLayout(inventory_form)
        
        # Add inventory group to container
        container_layout.addWidget(inventory_group)
        
        # Add stretching space
        container_layout.addStretch(1)
        
        # Add container to main layout
        main_layout.addWidget(container)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Create custom buttons instead of standard button box
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setIcon(QIcon(":/icons/icons/cancel.png"))
        style_secondary_button(self.cancel_button)
        
        self.save_button = QPushButton("Guardar" if self.is_edit_mode else "Crear Producto")
        self.save_button.setIcon(QIcon(":/icons/icons/save.png"))
        style_primary_button(self.save_button)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        main_layout.addLayout(button_layout)
        
        # Connect the buttons
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def _connect_signals(self):
        self.inventory_checkbox.stateChanged.connect(self._toggle_inventory_fields)

    @Slot(int)
    def _toggle_inventory_fields(self, state):
        """Enable/disable inventory-related fields based on checkbox state."""
        # Convert to boolean - the checkbox can pass either a bool or Qt.CheckState
        show = bool(state)
        if isinstance(state, int):
            print(f"Toggle inventory fields - state type: {type(state)}, value: {state}")
            show = (state == 2)  # Qt.CheckState.Checked
        
        print(f"Visibility will be set to: {show}")
        
        # Set visibility on all related widgets
        self.stock_label.setVisible(show)
        self.stock_input.setVisible(show)
        self.min_stock_label.setVisible(show)
        self.min_stock_input.setVisible(show)
        
        # Ensure inventory_form's parent layout is notified of the visibility change
        for item in [self.stock_label, self.stock_input, self.min_stock_label, self.min_stock_input]:
            item.setVisible(show)
            # Force an explicit size policy update
            if show:
                item.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            else:
                item.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        
        # Force parent layouts to update
        self.layout().activate()
        inventory_form = self.stock_label.parentWidget().layout()
        if inventory_form:
            inventory_form.activate()
            
        # Update window to ensure changes are applied
        self.adjustSize()
        QApplication.processEvents()

    def _load_departments(self):
        """Loads departments into the combo box."""
        self.department_combo.clear()
        self.department_combo.addItem("- Sin Departamento -", None) # Add null option
        try:
            self._departments = self.product_service.get_all_departments()
            for dept in self._departments:
                self.department_combo.addItem(dept.name, dept.id) # Store ID as user data
        except AttributeError:
             QMessageBox.warning(self, "Error", "El servicio de productos no tiene el método 'get_all_departments'.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudieron cargar los departamentos:\n{e}")

    def _populate_form(self):
        """Fills the form with data from product_to_edit."""
        if not self.product_to_edit:
            return

        product = self.product_to_edit
        self.code_input.setText(product.code)
        self.description_input.setText(product.description)
        self.sale_price_input.setValue(product.sell_price)
        self.cost_price_input.setValue(product.cost_price)
        self.unit_input.setText(product.unit)
        self.inventory_checkbox.setChecked(product.uses_inventory)

        # Select department in combo box
        if product.department_id:
            index = self.department_combo.findData(product.department_id)
            if index >= 0:
                self.department_combo.setCurrentIndex(index)
            else:
                # Department might have been deleted, add it temporarily or show warning
                print(f"Warning: Department ID {product.department_id} not found for product {product.code}")
                # Optionally add a placeholder item
                # self.department_combo.addItem(f"ID {product.department_id} (No encontrado)", product.department_id)
                # self.department_combo.setCurrentIndex(self.department_combo.count() - 1)
                self.department_combo.setCurrentIndex(0) # Default to "None"
        else:
             self.department_combo.setCurrentIndex(0) # Select "None"

        # Toggle inventory fields and set values
        self._toggle_inventory_fields(product.uses_inventory)
        if product.uses_inventory:
            self.stock_input.setValue(product.quantity_in_stock)
            # Make stock read-only in edit mode, adjusted via Inventory module
            self.stock_input.setReadOnly(True)
            self.stock_input.setStyleSheet("background-color: #f0f0f0;") # Visual cue
            self.stock_label.setText("Stock Actual: (No editable aquí)")

            self.min_stock_input.setValue(product.min_stock)
        else:
             # Ensure stock fields are re-enabled if checkbox toggled back on
             self.stock_input.setReadOnly(False)
             self.stock_input.setStyleSheet("") # Reset style
             self.stock_label.setText("Stock Actual:")


    def accept(self):
        """Handles the OK button click: validates and saves the product."""
        code = self.code_input.text().strip()
        description = self.description_input.text().strip()
        sell_price = self.sale_price_input.value()
        cost_price = self.cost_price_input.value()
        unit = self.unit_input.text().strip() or "U"
        uses_inventory = self.inventory_checkbox.isChecked()
        stock = self.stock_input.value() if uses_inventory else 0.0
        min_stock = self.min_stock_input.value() if uses_inventory else 0.0
        dept_index = self.department_combo.currentIndex()
        department_id = self.department_combo.itemData(dept_index) if dept_index > 0 else None

        # --- Basic Validation ---
        if not code:
            QMessageBox.warning(self, "Entrada Inválida", "El código del producto es obligatorio.")
            self.code_input.setFocus()
            self.validation_failed.emit("El código del producto es obligatorio.")
            return
        if not description:
            QMessageBox.warning(self, "Entrada Inválida", "La descripción del producto es obligatoria.")
            self.description_input.setFocus()
            self.validation_failed.emit("La descripción del producto es obligatoria.")
            return
        if sell_price < 0:
             QMessageBox.warning(self, "Entrada Inválida", "El precio de venta no puede ser negativo.")
             self.sale_price_input.setFocus()
             self.validation_failed.emit("El precio de venta no puede ser negativo.")
             return
        if cost_price < 0:
             QMessageBox.warning(self, "Entrada Inválida", "El precio de costo no puede ser negativo.")
             self.cost_price_input.setFocus()
             self.validation_failed.emit("El precio de costo no puede ser negativo.")
             return
        # Add more validation as needed (e.g., code format)

        product_data = {
            "code": code,
            "description": description,
            "sell_price": sell_price,
            "cost_price": cost_price,
            "department_id": department_id,
            "unit": unit,
            "uses_inventory": uses_inventory,
            "min_stock": min_stock,
            # Stock is handled separately (only set on creation if inventory used, not editable here)
        }
        # Only include initial stock if adding a new product that uses inventory
        if not self.is_edit_mode and uses_inventory:
             product_data["quantity_in_stock"] = stock

        # Create a Product object from the dictionary
        try:
            # Ensure correct types (especially for Decimal if used, but service likely handles floats now)
            product_obj = Product(
                id=self.product_to_edit.id if self.is_edit_mode else None,
                code=product_data["code"],
                description=product_data["description"],
                sell_price=product_data["sell_price"],
                cost_price=product_data["cost_price"],
                department_id=product_data["department_id"],
                unit=product_data["unit"],
                uses_inventory=product_data["uses_inventory"],
                quantity_in_stock=product_data.get("quantity_in_stock", 0.0), # Use get with default
                min_stock=product_data["min_stock"]
            )
        except KeyError as e:
            QMessageBox.critical(self, "Error Interno", f"Falta clave al crear objeto Producto: {e}")
            return

        try:
            if self.is_edit_mode:
                print(f"[ProductDialog] Attempting to update product ID: {product_obj.id}")
                # Pass the Product object
                self.product_service.update_product(product_obj)
                QMessageBox.information(self, "Producto Modificado", f"Producto '{product_obj.description}' modificado correctamente.")
            else:
                print("[ProductDialog] Attempting to add new product")
                # Pass the Product object
                new_product = self.product_service.add_product(product_obj)
                QMessageBox.information(self, "Producto Agregado", f"Producto '{new_product.description}' agregado correctamente.")

            super().accept() # Close the dialog successfully

        except ValueError as e: # Catch validation errors from service (e.g., duplicate code)
             QMessageBox.warning(self, "Error al Guardar", str(e))
        except AttributeError as e:
            QMessageBox.critical(self, "Error de Servicio", f"Error llamando al servicio: {e}")
            print(f"Attribute error calling service: {e}")
        except Exception as e: # Catch unexpected errors
             QMessageBox.critical(self, "Error Inesperado", f"Ocurrió un error al guardar el producto:\n{e}")
             print(f"Error saving product: {e}") # Log error for debugging


# Example of running this dialog directly (for testing)
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Use the combined mock service
    mock_service = MockProductService()

    # Test 1: Add new product
    print("--- Testing ADD mode ---")
    dialog_add = ProductDialog(mock_service)
    result_add = dialog_add.exec()
    print(f"Add dialog result: {result_add} (1=Accepted, 0=Rejected)")
    print("Current products in mock service:", mock_service.find_product())
    print("-" * 20)


    # Test 2: Edit existing product (if one was added or mock exists)
    print("--- Testing EDIT mode ---")
    product_to_edit = mock_service.get_product_by_id(1) # Get first mock product
    if product_to_edit:
        dialog_edit = ProductDialog(mock_service, product_to_edit=product_to_edit)
        result_edit = dialog_edit.exec()
        print(f"Edit dialog result: {result_edit}")
        print("-" * 20)
        # Print updated product from mock service
        updated_product = mock_service.get_product_by_id(1)
        print("Updated product details:", updated_product)
    else:
        print("Could not find product with ID 1 to test edit mode.")


    sys.exit() # Exit after tests 