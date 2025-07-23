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
from core.services.unit_service import UnitService

# Import common UI functions
from ui.utils import show_error_message, show_info_message, style_text_input, style_dropdown, style_primary_button, style_secondary_button, style_heading_label, apply_standard_form_style


class ProductDialog(QDialog):
    """Dialog for adding or modifying products."""
    validation_failed = Signal(str)

    def __init__(self, product_service, product_to_edit: Optional[Product] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.product_service = product_service
        self.unit_service = UnitService()
        self.product_to_edit = product_to_edit
        self.is_edit_mode = product_to_edit is not None

        self.setWindowTitle("Modificar Producto" if self.is_edit_mode else "Agregar Producto")
        self.setMinimumWidth(400)

        self._departments: list[Department] = [] # Cache departments
        self._units: list = [] # Cache units

        self._init_ui()
        self._connect_signals()
        self._load_departments()
        self._load_units()

        # Make sure this is called after the UI is fully initialized
        QApplication.processEvents()

        if self.is_edit_mode:
            self._populate_form()
        else:
            # Set initial state for new product 
            # Suggest next available ID
            try:
                next_id = self.product_service.get_next_available_id()
                self.id_input.setText(str(next_id))
            except Exception as e:
                print(f"Warning: Could not get next available ID: {e}")
                self.id_input.setText("1")
            
            # Make sure checkbox state is properly set first
            initial_inventory_enabled = True
            self.inventory_checkbox.setChecked(initial_inventory_enabled)
            
        # Set initial inventory fields visibility based on checkbox state
        # This must be called after checkbox state is set
        # Use the proper Qt state value (2 for checked, 0 for unchecked)
        initial_state = 2 if self.inventory_checkbox.isChecked() else 0
        self._toggle_inventory_fields(initial_state)
        
        if not self.is_edit_mode:
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
        # ID field
        self.id_input = QLineEdit()
        style_text_input(self.id_input)
        self.id_input.setPlaceholderText("Se sugerirá automáticamente")
        
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
        
        self.unit_combo = QComboBox()
        style_dropdown(self.unit_combo)
        
        basic_info_layout.addRow("ID:", self.id_input)
        basic_info_layout.addRow("Código:", self.code_input)
        basic_info_layout.addRow("Descripción:", self.description_input)
        basic_info_layout.addRow("Precio Venta:", self.sale_price_input)
        basic_info_layout.addRow("Precio Costo:", self.cost_price_input)
        basic_info_layout.addRow("Departamento:", self.department_combo)
        basic_info_layout.addRow("Unidad Venta:", self.unit_combo)
        
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
        if isinstance(state, int):
            show = (state == 2)  # Qt.CheckState.Checked
        elif isinstance(state, bool):
            show = state
        else:
            show = bool(state)
        
        # Set visibility on all related widgets
        self.stock_label.setVisible(show)
        self.stock_input.setVisible(show)
        self.min_stock_label.setVisible(show)
        self.min_stock_input.setVisible(show)
        
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

    def _load_units(self):
        """Loads units into the combo box."""
        self.unit_combo.clear()
        self.unit_combo.addItem("U", "U") # Add default unit option
        try:
            self._units = self.unit_service.get_all_units(active_only=True)
            for unit in self._units:
                display_text = f"{unit.name}"
                if unit.abbreviation:
                    display_text += f" ({unit.abbreviation})"
                self.unit_combo.addItem(display_text, unit.name)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudieron cargar las unidades:\n{e}")

    def _populate_form(self):
        """Fills the form with data from product_to_edit."""
        if not self.product_to_edit:
            return

        product = self.product_to_edit
        # Set ID field (read-only for existing products)
        if product.id is not None:
            self.id_input.setText(str(product.id))
            self.id_input.setReadOnly(True)
        
        self.code_input.setText(product.code)
        self.description_input.setText(product.description)
        self.sale_price_input.setValue(product.sell_price)
        self.cost_price_input.setValue(product.cost_price)
        # Select unit in combo box
        unit_index = self.unit_combo.findData(product.unit)
        if unit_index >= 0:
            self.unit_combo.setCurrentIndex(unit_index)
        else:
            # Unit might not exist in the list, set to default
            self.unit_combo.setCurrentIndex(0)
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
        """Handles the OK button click: collects data and delegates validation to service layer."""
        try:
            # Collect data from UI without validation
            # Get ID from input field
            id_text = self.id_input.text().strip()
            product_id = None
            if id_text:  # Only validate if ID is provided
                try:
                    product_id = int(id_text)
                except ValueError:
                    raise ValueError("El ID debe ser un número entero válido")
            
            code = self.code_input.text().strip()
            description = self.description_input.text().strip()
            sell_price = self.sale_price_input.value()
            cost_price = self.cost_price_input.value()
            unit_index = self.unit_combo.currentIndex()
            unit = self.unit_combo.itemData(unit_index) if unit_index >= 0 else "U"
            uses_inventory = self.inventory_checkbox.isChecked()
            stock = self.stock_input.value() if uses_inventory else 0.0
            min_stock = self.min_stock_input.value() if uses_inventory else 0.0
            dept_index = self.department_combo.currentIndex()
            department_id = self.department_combo.itemData(dept_index) if dept_index > 0 else None

            # Create Product object
            product_obj = Product(
                id=self.product_to_edit.id if self.is_edit_mode else product_id,
                code=code,
                description=description,
                sell_price=sell_price,
                cost_price=cost_price,
                department_id=department_id,
                unit=unit,
                uses_inventory=uses_inventory,
                quantity_in_stock=stock if not self.is_edit_mode and uses_inventory else (self.product_to_edit.quantity_in_stock if self.is_edit_mode else 0.0),
                min_stock=min_stock
            )

            # Call service - validation happens here
            if self.is_edit_mode:
                self.product_service.update_product(product_obj)
                show_info_message(self, "Éxito", "Producto modificado correctamente")
            else:
                new_product = self.product_service.add_product(product_obj)
                show_info_message(self, "Éxito", "Producto agregado correctamente")

            super().accept()  # Close dialog successfully

        except ValueError as e:
            # Handle validation errors from service
            error_message = str(e)
            show_error_message(self, "Error de validación", error_message)
            self._focus_field_for_error(error_message)
            self.validation_failed.emit(error_message)

        except Exception as e:
            # Handle unexpected errors
            show_error_message(self, "Error", f"Ocurrió un error inesperado: {str(e)}")
            print(f"Error saving product: {e}")  # Log for debugging

    def _focus_field_for_error(self, error_message):
        """Focus the appropriate field based on the error message for better UX."""
        error_lower = error_message.lower()
        
        if 'id' in error_lower:
            self.id_input.setFocus()
            self.id_input.selectAll()
        elif 'code' in error_lower:
            self.code_input.setFocus()
            self.code_input.selectAll()
        elif 'description' in error_lower:
            self.description_input.setFocus()
            self.description_input.selectAll()
        elif 'sell price' in error_lower:
            self.sale_price_input.setFocus()
            self.sale_price_input.selectAll()
        elif 'cost price' in error_lower:
            self.cost_price_input.setFocus()
            self.cost_price_input.selectAll()
        elif 'department' in error_lower:
            self.department_combo.setFocus()


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