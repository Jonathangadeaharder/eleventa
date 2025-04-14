from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableView, QSplitter,
    QMessageBox, QAbstractItemView, QGroupBox, QLabel
)
from PySide6.QtCore import Slot, Qt

# Assuming services and models exist
# from core.services.purchase_service import PurchaseService # Adjust import
from core.models.user import User # Added
from core.services.purchase_service import PurchaseService
from core.services.product_service import ProductService
from core.services.inventory_service import InventoryService
from ui.models.table_models import PurchaseOrderTableModel, PurchaseOrderItemTableModel
from ui.dialogs.purchase_dialogs import PurchaseOrderDialog, ReceiveStockDialog
from ui.utils import show_error_message

class PurchasesView(QWidget):
    """View for managing Purchase Orders."""

    def __init__(
        self,
        purchase_service: PurchaseService,
        product_service: ProductService,
        inventory_service: InventoryService,
        current_user: User, # Added
        parent=None
    ):
        super().__init__(parent)
        self.purchase_service = purchase_service
        self.product_service = product_service
        self.inventory_service = inventory_service
        self.current_user = current_user # Added

        # --- Models ---
        self.po_table_model = PurchaseOrderTableModel()
        self.po_item_table_model = PurchaseOrderItemTableModel()

        # --- Widgets ---
        self.new_po_button = QPushButton("Nueva Orden de Compra")
        self.receive_stock_button = QPushButton("Recibir Mercadería")
        self.view_po_button = QPushButton("Ver/Imprimir Orden") # Placeholder
        self.refresh_button = QPushButton("Refrescar Listado")

        self.view_po_button.setEnabled(False) # Disable unimplemented features initially

        # Purchase Orders Table
        self.po_table_view = QTableView()
        self.po_table_view.setModel(self.po_table_model)
        self.po_table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.po_table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.po_table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.po_table_view.horizontalHeader().setStretchLastSection(True)
        # self.po_table_view.resizeColumnsToContents()

        # Purchase Order Items Table
        self.po_item_table_view = QTableView()
        self.po_item_table_view.setModel(self.po_item_table_model)
        self.po_item_table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.po_item_table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.po_item_table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.po_item_table_view.horizontalHeader().setStretchLastSection(True)
        # self.po_item_table_view.resizeColumnsToContents()

        # --- Layout ---
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.new_po_button)
        button_layout.addWidget(self.receive_stock_button)
        button_layout.addWidget(self.view_po_button)
        button_layout.addStretch()
        button_layout.addWidget(self.refresh_button)

        # Use a splitter for tables
        splitter = QSplitter(Qt.Orientation.Vertical)
        po_group = QGroupBox("Órdenes de Compra")
        po_layout = QVBoxLayout(po_group)
        po_layout.addWidget(self.po_table_view)
        splitter.addWidget(po_group)

        item_group = QGroupBox("Detalle de Orden Seleccionada")
        item_layout = QVBoxLayout(item_group)
        item_layout.addWidget(self.po_item_table_view)
        splitter.addWidget(item_group)

        splitter.setSizes([300, 200]) # Initial size ratio

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(splitter)

        # --- Connections ---
        self.refresh_button.clicked.connect(self.refresh_purchase_orders)
        self.new_po_button.clicked.connect(self.create_new_purchase_order)
        self.receive_stock_button.clicked.connect(self.receive_selected_po_stock)
        # Connect selection change in PO table to update item table
        self.po_table_view.selectionModel().selectionChanged.connect(self.update_selected_po_items)

        # --- Initial Load ---
        self.refresh_purchase_orders()

    @Slot()
    def refresh_purchase_orders(self):
        """Fetches purchase orders and updates the PO table."""
        try:
            # TODO: Add filters for status (e.g., show only PENDING/PARTIALLY_RECEIVED)
            purchase_orders = self.purchase_service.find_purchase_orders()
            self.po_table_model.update_data(purchase_orders)
            # Clear item table as selection might change or become invalid
            self.po_item_table_model.update_data([])
            # self.po_table_view.resizeColumnsToContents()
        except Exception as e:
            show_error_message(self, "Error", f"Error al cargar órdenes de compra:\n{e}") # Added title
            print(f"Error refreshing purchase orders: {e}")

    @Slot()
    def update_selected_po_items(self):
        """Updates the item table based on the selected PO."""
        selected_po = self._get_selected_purchase_order()
        if selected_po and selected_po.items:
             # Fetch full PO details if items weren't loaded in get_all
             try:
                 full_po = self.purchase_service.get_purchase_order_by_id(selected_po.id)
                 if full_po:
                     self.po_item_table_model.update_data(full_po.items)
                 else: # Should not happen if selection is valid
                      self.po_item_table_model.update_data([])
             except Exception as e:
                 show_error_message(self, "Error", f"Error al cargar detalle de orden:\n{e}") # Added title
                 self.po_item_table_model.update_data([])
        else:
            self.po_item_table_model.update_data([]) # Clear items if no selection or PO has no items

    def _get_selected_purchase_order(self):
        """Helper to get the selected PurchaseOrder object from the table."""
        selected_indexes = self.po_table_view.selectionModel().selectedRows()
        if not selected_indexes:
            return None
        selected_row = selected_indexes[0].row()
        po = self.po_table_model.get_purchase_order(selected_row)
        return po

    @Slot()
    def create_new_purchase_order(self):
        """Opens the dialog to create a new purchase order."""
        # Pass necessary services and user to the dialog
        dialog = PurchaseOrderDialog(
            purchase_service=self.purchase_service,
            product_service=self.product_service,
            current_user=self.current_user, # Pass user
            parent=self
        )
        if dialog.exec():
            self.refresh_purchase_orders() # Refresh the list after creation

    @Slot()
    def receive_selected_po_stock(self):
        """Opens the dialog to receive stock for the selected PO."""
        selected_po = self._get_selected_purchase_order()
        if not selected_po:
            QMessageBox.information(self, "Información", "Seleccione una orden de compra de la lista.")
            return

        if selected_po.status in ["RECEIVED", "CANCELLED"]:
             QMessageBox.information(self, "Información", f"La orden de compra #{selected_po.id} ya está en estado '{selected_po.status}'.")
             return

        # Fetch full PO details including items before opening dialog
        try:
            full_po = self.purchase_service.get_purchase_order_by_id(selected_po.id)
            if not full_po:
                 show_error_message(self, "Error", "No se encontró la orden de compra seleccionada.")
                 return

            dialog = ReceiveStockDialog(
                purchase_service=self.purchase_service,
                inventory_service=self.inventory_service,
                purchase_order=full_po,
                current_user=self.current_user, # Pass user
                parent=self
            )
            if dialog.exec():
                self.refresh_purchase_orders() # Refresh list after receiving stock
        except Exception as e:
             show_error_message(self, "Error", f"Error al preparar recepción de mercadería:\n{e}") # Added title
             print(f"Error fetching PO {selected_po.id} for receiving: {e}")
