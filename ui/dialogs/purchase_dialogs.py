from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QMessageBox, QDialogButtonBox, QTableView, QComboBox, QDateEdit, QTextEdit,
    QAbstractItemView, QDoubleSpinBox, QLabel
)
from PySide6.QtCore import Slot, QDate, Qt, QAbstractTableModel, QModelIndex # Added QAbstractTableModel, QModelIndex
from PySide6.QtGui import QColor # Added QColor
from typing import Optional, List, Dict, Any

# Assuming core models and services exist
from core.models.supplier import Supplier
from core.models.product import Product
from core.models.purchase import PurchaseOrder, PurchaseOrderItem
# from core.services.purchase_service import PurchaseService # Adjust import
# from core.services.product_service import ProductService # Adjust import
from ui.models.table_models import PurchaseOrderItemTableModel
from ui.utils import show_error_message, ask_confirmation # Assuming utils exist

# --- Custom Table Model for Receiving Stock ---

class ReceiveStockItemTableModel(QAbstractTableModel):
    """Model specifically for the Receive Stock dialog table."""
    HEADERS = ["Código", "Descripción", "Pedido", "Recibido", "Pendiente", "Recibir Ahora"]
    # Column indices
    COL_CODE = 0
    COL_DESC = 1
    COL_ORDERED = 2
    COL_RECEIVED_PREV = 3
    COL_PENDING = 4
    COL_RECEIVE_NOW = 5 # Editable column

    def __init__(self, items: List[PurchaseOrderItem] = [], parent=None):
        super().__init__(parent)
        # Store original items and track quantities to receive now
        self._items = items
        # Initialize quantities to receive now, default to pending amount
        self._receive_now_quantities = {
            item.id: max(0, item.quantity_ordered - item.quantity_received)
            for item in items
        }

    def rowCount(self, parent=QModelIndex()) -> int: return len(self._items)
    def columnCount(self, parent=QModelIndex()) -> int: return len(self.HEADERS)
    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.HEADERS[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid(): return None
        item = self._items[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            if col == self.COL_CODE: return item.product_code
            if col == self.COL_DESC: return item.product_description
            if col == self.COL_ORDERED: return f"{item.quantity_ordered:.2f}"
            if col == self.COL_RECEIVED_PREV: return f"{item.quantity_received:.2f}"
            if col == self.COL_PENDING:
                pending = max(0, item.quantity_ordered - item.quantity_received)
                return f"{pending:.2f}"
            if col == self.COL_RECEIVE_NOW:
                return self._receive_now_quantities.get(item.id, 0.0)

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col >= self.COL_ORDERED: # Numeric columns
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        elif role == Qt.ItemDataRole.BackgroundRole:
             if col == self.COL_RECEIVE_NOW: # Highlight editable cell
                 return QColor(Qt.GlobalColor.yellow).lighter(160)

        return None

    def setData(self, index: QModelIndex, value: Any, role=Qt.ItemDataRole.EditRole) -> bool:
        """Handles editing the 'Receive Now' column."""
        if not index.isValid() or role != Qt.ItemDataRole.EditRole or index.column() != self.COL_RECEIVE_NOW:
            return False

        item = self._items[index.row()]
        try:
            receive_qty = float(value)
            if receive_qty < 0:
                raise ValueError("Quantity cannot be negative.")
            # Validate against pending quantity
            pending = max(0, item.quantity_ordered - item.quantity_received)
            if receive_qty > pending:
                 # Optionally clamp or show error, here we clamp
                 receive_qty = pending
                 # Consider showing a warning to the user

            self._receive_now_quantities[item.id] = receive_qty
            self.dataChanged.emit(index, index, [role])
            return True
        except (ValueError, TypeError):
            return False # Invalid input

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        """Sets flags for items, making 'Receive Now' editable."""
        default_flags = super().flags(index)
        if index.isValid() and index.column() == self.COL_RECEIVE_NOW:
            # Allow editing only if there are pending items
            item = self._items[index.row()]
            pending = max(0, item.quantity_ordered - item.quantity_received)
            if pending > 0:
                return default_flags | Qt.ItemFlag.ItemIsEditable
            else:
                return default_flags & ~Qt.ItemFlag.ItemIsEditable # Make non-editable if nothing pending
        return default_flags

    def get_receive_quantities(self) -> Dict[int, float]:
        """Returns the dictionary of {item_id: quantity_to_receive_now}."""
        # Filter out zero quantities
        return {item_id: qty for item_id, qty in self._receive_now_quantities.items() if qty > 0}


class PurchaseOrderDialog(QDialog):
    """Dialog for creating a new Purchase Order."""

    def __init__(self, purchase_service, product_service, current_user=None, parent=None):
        super().__init__(parent)
        self.purchase_service = purchase_service
        self.product_service = product_service
        self.current_user = current_user
        self.current_po_items: List[PurchaseOrderItem] = [] # Store items being added

        self.setWindowTitle("Nueva Orden de Compra")
        self.setMinimumSize(700, 500) # Set a reasonable minimum size

        # --- Models ---
        self.items_table_model = PurchaseOrderItemTableModel([]) # Start empty

        # --- Widgets ---
        # Supplier Selection
        self.supplier_combo = QComboBox()
        self.supplier_combo.setPlaceholderText("Seleccione un proveedor...")
        self._load_suppliers()

        # Dates
        self.order_date_edit = QDateEdit(QDate.currentDate())
        self.order_date_edit.setCalendarPopup(True)
        self.expected_date_edit = QDateEdit()
        self.expected_date_edit.setCalendarPopup(True)
        self.expected_date_edit.setSpecialValueText("Opcional") # Indicate optional
        self.expected_date_edit.setDate(QDate.currentDate().addDays(7)) # Default +7 days

        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Notas adicionales sobre la orden...")

        # Item Entry
        self.product_search_edit = QLineEdit()
        self.product_search_edit.setPlaceholderText("Buscar producto por código o descripción...")
        self.product_combo = QComboBox() # To show search results
        self.product_combo.setPlaceholderText("Seleccione producto a agregar...")
        self.quantity_spinbox = QDoubleSpinBox()
        self.quantity_spinbox.setRange(0.01, 99999.99)
        self.quantity_spinbox.setValue(1.0)
        self.cost_spinbox = QDoubleSpinBox()
        self.cost_spinbox.setRange(0.00, 999999.99)
        self.cost_spinbox.setDecimals(2)
        self.cost_spinbox.setPrefix("$ ")
        self.add_item_button = QPushButton("Agregar Ítem")

        # Items Table
        self.items_table_view = QTableView()
        self.items_table_view.setModel(self.items_table_model)
        self.items_table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.items_table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.items_table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.items_table_view.horizontalHeader().setStretchLastSection(True)
        # self.items_table_view.resizeColumnsToContents()

        self.remove_item_button = QPushButton("Quitar Ítem Seleccionado")
        self.total_label = QLabel("Total Orden: $ 0.00")
        font = self.total_label.font()
        font.setBold(True)
        self.total_label.setFont(font)

        # Dialog Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Crear Orden")

        # --- Layout ---
        form_layout = QFormLayout()
        form_layout.addRow("Proveedor (*):", self.supplier_combo)
        form_layout.addRow("Fecha Orden:", self.order_date_edit)
        form_layout.addRow("Fecha Estimada Entrega:", self.expected_date_edit)
        form_layout.addRow("Notas:", self.notes_edit)

        item_entry_layout = QHBoxLayout()
        item_entry_layout.addWidget(QLabel("Producto:"))
        item_entry_layout.addWidget(self.product_search_edit, 2)
        item_entry_layout.addWidget(self.product_combo, 3)
        item_entry_layout.addWidget(QLabel("Cantidad:"))
        item_entry_layout.addWidget(self.quantity_spinbox)
        item_entry_layout.addWidget(QLabel("Costo Unit.:"))
        item_entry_layout.addWidget(self.cost_spinbox)
        item_entry_layout.addWidget(self.add_item_button)

        items_layout = QVBoxLayout()
        items_layout.addLayout(item_entry_layout)
        items_layout.addWidget(self.items_table_view)
        items_button_layout = QHBoxLayout()
        items_button_layout.addWidget(self.remove_item_button)
        items_button_layout.addStretch()
        items_button_layout.addWidget(self.total_label)
        items_layout.addLayout(items_button_layout)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addLayout(items_layout)
        main_layout.addWidget(self.button_box)

        # --- Connections ---
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.product_search_edit.textChanged.connect(self._search_products)
        self.product_combo.currentIndexChanged.connect(self._product_selected)
        self.add_item_button.clicked.connect(self._add_item_to_order)
        self.remove_item_button.clicked.connect(self._remove_selected_item)
        self.items_table_model.rowsInserted.connect(self._update_total)
        self.items_table_model.rowsRemoved.connect(self._update_total)
        self.items_table_model.modelReset.connect(self._update_total)


    def _load_suppliers(self):
        """Loads suppliers into the combo box."""
        self.supplier_combo.clear()
        self.supplier_combo.addItem("", None) # Add empty default item
        try:
            suppliers = self.purchase_service.find_suppliers()
            for supplier in suppliers:
                self.supplier_combo.addItem(f"{supplier.name} (ID: {supplier.id})", supplier)
        except Exception as e:
            show_error_message(self, f"Error al cargar proveedores:\n{e}")

    @Slot(str)
    def _search_products(self, text: str):
        """Searches products based on input and updates the product combo box."""
        self.product_combo.clear()
        self.product_combo.addItem("", None) # Default empty
        if len(text) < 2: # Don't search for very short strings
            return
        try:
            products = self.product_service.find_product(text) # Assuming service exists
            for product in products:
                display_text = f"{product.code} - {product.description} (Stock: {product.quantity_in_stock:.2f})"
                self.product_combo.addItem(display_text, product)
        except Exception as e:
            print(f"Error searching products: {e}") # Log error, maybe show subtle indicator

    @Slot(int)
    def _product_selected(self, index: int):
        """Updates cost price when a product is selected from the combo."""
        product = self.product_combo.currentData()
        if product and isinstance(product, Product):
            self.cost_spinbox.setValue(product.cost_price or 0.0)
        else:
            self.cost_spinbox.setValue(0.0)

    @Slot()
    def _add_item_to_order(self):
        """Adds the selected product as an item to the current PO."""
        product = self.product_combo.currentData()
        quantity = self.quantity_spinbox.value()
        cost = self.cost_spinbox.value()

        if not isinstance(product, Product):
            QMessageBox.warning(self, "Error", "Seleccione un producto válido.")
            return
        if quantity <= 0:
            QMessageBox.warning(self, "Error", "La cantidad debe ser mayor a cero.")
            return
        if cost < 0:
             QMessageBox.warning(self, "Error", "El costo no puede ser negativo.")
             return

        # Check if item already exists, if so, maybe ask to update? For now, allow duplicates.
        po_item = PurchaseOrderItem(
            product_id=product.id,
            product_code=product.code,
            product_description=product.description,
            quantity_ordered=quantity,
            cost_price=cost,
            quantity_received=0 # Always 0 initially
        )
        self.current_po_items.append(po_item)
        self.items_table_model.update_data(self.current_po_items) # Refresh table

        # Clear entry fields
        self.product_search_edit.clear()
        self.product_combo.clear()
        self.quantity_spinbox.setValue(1.0)
        self.cost_spinbox.setValue(0.0)
        self.product_search_edit.setFocus()

    @Slot()
    def _remove_selected_item(self):
        """Removes the selected item from the current PO list."""
        selected_indexes = self.items_table_view.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.information(self, "Información", "Seleccione un ítem de la lista para quitar.")
            return

        selected_row = selected_indexes[0].row()
        if 0 <= selected_row < len(self.current_po_items):
            del self.current_po_items[selected_row]
            self.items_table_model.update_data(self.current_po_items) # Refresh table

    @Slot()
    def _update_total(self):
        """Calculates and updates the total amount label."""
        total = sum(item.subtotal for item in self.current_po_items)
        self.total_label.setText(f"Total Orden: $ {total:.2f}")

    @Slot()
    def accept(self):
        """Handles the OK button click: validates and creates the PO."""
        selected_supplier = self.supplier_combo.currentData()
        order_date = self.order_date_edit.dateTime().toPython() # Get datetime
        expected_date_str = self.expected_date_edit.text()
        expected_date = self.expected_date_edit.dateTime().toPython() if expected_date_str != "Opcional" else None
        notes = self.notes_edit.toPlainText().strip() or None

        if not isinstance(selected_supplier, Supplier):
            QMessageBox.warning(self, "Error de Validación", "Seleccione un proveedor válido.")
            return
        if not self.current_po_items:
            QMessageBox.warning(self, "Error de Validación", "La orden de compra debe tener al menos un ítem.")
            return

        po_data = {
            "supplier_id": selected_supplier.id,
            "order_date": order_date,
            "expected_delivery_date": expected_date,
            "notes": notes,
            "items": [
                {
                    "product_id": item.product_id,
                    "quantity_ordered": item.quantity_ordered,
                    "cost_price": item.cost_price
                } for item in self.current_po_items
            ]
        }

        try:
            created_po = self.purchase_service.create_purchase_order(po_data)
            QMessageBox.information(self, "Éxito", f"Orden de Compra #{created_po.id} creada correctamente.")
            super().accept() # Close dialog on success
        except ValueError as ve:
            QMessageBox.critical(self, "Error", f"Error al crear orden de compra:\n{ve}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error inesperado:\n{e}")
            print(f"Unexpected error creating purchase order: {e}") # Log full error

# --- Receive Stock Dialog ---
class ReceiveStockDialog(QDialog):
    """Dialog for receiving items from a purchase order."""
    
    def __init__(self, purchase_service, inventory_service, purchase_order, current_user=None, parent=None):
        super().__init__(parent)
        self.purchase_service = purchase_service
        self.inventory_service = inventory_service
        self.purchase_order = purchase_order
        self.current_user = current_user

        self.setWindowTitle(f"Recibir Mercadería - Orden #{purchase_order.id}")
        self.setMinimumSize(800, 400) # Adjust size

        # --- Model ---
        self.receive_table_model = ReceiveStockItemTableModel(purchase_order.items)

        # --- Widgets ---
        self.info_label = QLabel(f"<b>Proveedor:</b> {purchase_order.supplier_name}<br>"
                                 f"<b>Fecha Orden:</b> {purchase_order.order_date.strftime('%Y-%m-%d')}<br>"
                                 f"<b>Estado Actual:</b> {purchase_order.status}")
        self.info_label.setTextFormat(Qt.TextFormat.RichText)

        self.receive_table_view = QTableView()
        self.receive_table_view.setModel(self.receive_table_model)
        self.receive_table_view.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.receive_table_view.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers) # Allow editing 'Receive Now'
        self.receive_table_view.horizontalHeader().setStretchLastSection(False)
        self.receive_table_view.resizeColumnsToContents()

        self.notes_label = QLabel("Notas de Recepción (Opcional):")
        self.notes_edit = QLineEdit()

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Confirmar Recepción")

        # --- Layout ---
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.info_label)
        main_layout.addWidget(self.receive_table_view)
        notes_layout = QHBoxLayout()
        notes_layout.addWidget(self.notes_label)
        notes_layout.addWidget(self.notes_edit)
        main_layout.addLayout(notes_layout)
        main_layout.addWidget(self.button_box)

        # --- Connections ---
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    @Slot()
    def accept(self):
        """Handles confirmation: validates quantities and calls the service."""
        receive_quantities = self.receive_table_model.get_receive_quantities()
        notes = self.notes_edit.text().strip() or None

        if not receive_quantities:
            QMessageBox.information(self, "Información", "No se especificaron cantidades para recibir.")
            return # Don't proceed if nothing is being received

        # Confirmation dialog
        items_summary = []
        for item_id, qty in receive_quantities.items():
             # Find item details for summary (could be more efficient)
             item = next((i for i in self.purchase_order.items if i.id == item_id), None)
             if item:
                 items_summary.append(f"- {item.product_code}: {qty:.2f}")
        summary_text = "\n".join(items_summary)

        if not ask_confirmation(self, f"Confirmar recepción de los siguientes ítems?\n\n{summary_text}"):
            return

        try:
            # Call the service method to receive items
            updated_po = self.purchase_service.receive_purchase_order_items(
                po_id=self.purchase_order.id,
                received_items_data=receive_quantities,
                notes=notes
            )
            QMessageBox.information(self, "Éxito", f"Mercadería recibida correctamente. Nuevo estado: {updated_po.status}")
            super().accept() # Close dialog on success
        except ValueError as ve:
            QMessageBox.critical(self, "Error", f"Error al recibir mercadería:\n{ve}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error inesperado:\n{e}")
            print(f"Unexpected error receiving stock for PO {self.purchase_order.id}: {e}") # Log full error
