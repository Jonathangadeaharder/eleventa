from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableView, QLineEdit,
    QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Slot, Qt
from PySide6.QtGui import QKeySequence, QShortcut

# Assuming PurchaseService and SupplierTableModel exist
# from core.services.purchase_service import PurchaseService # Adjust import
from ui.models.table_models import SupplierTableModel
from ui.dialogs.supplier_dialog import SupplierDialog # Adjust import
from ui.utils import show_error_message, ask_confirmation # Assuming utils exist

class SuppliersView(QWidget):
    """View for managing suppliers."""

    def __init__(self, purchase_service, parent=None):
        super().__init__(parent)
        self.purchase_service = purchase_service

        # --- Models ---
        self.supplier_table_model = SupplierTableModel()

        # --- Widgets ---
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Buscar por nombre, contacto, CUIT...")

        self.add_button = QPushButton("Nuevo Proveedor")
        self.modify_button = QPushButton("Modificar")
        self.delete_button = QPushButton("Eliminar")
        self.refresh_button = QPushButton("Refrescar") # Optional

        self.supplier_table_view = QTableView()
        self.supplier_table_view.setModel(self.supplier_table_model)
        self.supplier_table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.supplier_table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.supplier_table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) # Read-only
        self.supplier_table_view.horizontalHeader().setStretchLastSection(True)
        # self.supplier_table_view.resizeColumnsToContents() # Adjust column widths

        # --- Layout ---
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.modify_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        button_layout.addWidget(self.refresh_button)

        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_edit)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(button_layout)
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.supplier_table_view)

        # --- Connections ---
        self.add_button.clicked.connect(self.add_new_supplier)
        self.modify_button.clicked.connect(self.modify_selected_supplier)
        self.delete_button.clicked.connect(self.delete_selected_supplier)
        self.refresh_button.clicked.connect(self.refresh_suppliers)
        self.search_edit.textChanged.connect(self.filter_suppliers)
        self.supplier_table_view.doubleClicked.connect(self.modify_selected_supplier)

        # --- Initial Load ---
        self.refresh_suppliers()

    @Slot()
    def refresh_suppliers(self):
        """Fetches all suppliers and updates the table."""
        try:
            # Pass the search term if filtering is active
            search_term = self.search_edit.text().strip()
            suppliers = self.purchase_service.find_suppliers(search_term)
            self.supplier_table_model.update_data(suppliers)
            # self.supplier_table_view.resizeColumnsToContents() # Optional resize after data load
        except Exception as e:
            show_error_message(self, "Error al cargar proveedores", str(e))
            print(f"Error refreshing suppliers: {e}") # Log full error

    @Slot()
    def filter_suppliers(self):
        """Filters suppliers based on the search term."""
        self.refresh_suppliers() # Re-use refresh logic which now includes search

    @Slot()
    def add_new_supplier(self):
        """Opens the dialog to add a new supplier."""
        dialog = SupplierDialog(self.purchase_service, parent=self)
        if dialog.exec():
            self.refresh_suppliers() # Refresh list if dialog was accepted

    def _get_selected_supplier(self):
        """Helper to get the selected supplier from the table."""
        selected_indexes = self.supplier_table_view.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.information(self, "Información", "Seleccione un proveedor de la lista.")
            return None
        selected_row = selected_indexes[0].row()
        supplier = self.supplier_table_model.get_supplier(selected_row)
        return supplier

    @Slot()
    def modify_selected_supplier(self):
        """Opens the dialog to modify the selected supplier."""
        supplier = self._get_selected_supplier()
        if not supplier:
            return

        dialog = SupplierDialog(self.purchase_service, supplier=supplier, parent=self)
        if dialog.exec():
            self.refresh_suppliers() # Refresh list if dialog was accepted

    @Slot()
    def delete_selected_supplier(self):
        """Deletes the selected supplier after confirmation."""
        supplier = self._get_selected_supplier()
        if not supplier:
            return

        if ask_confirmation(self, "Confirmar Eliminación", f"¿Está seguro que desea eliminar al proveedor '{supplier.name}'?"):
            try:
                success = self.purchase_service.delete_supplier(supplier.id)
                if success:
                    QMessageBox.information(self, "Éxito", "Proveedor eliminado correctamente.")
                    self.refresh_suppliers()
                else:
                    # Should ideally not happen if get_by_id worked, but handle anyway
                    show_error_message(self, "No se pudo eliminar el proveedor (posiblemente ya fue eliminado).")
            except ValueError as ve: # Catch specific errors from service (e.g., has POs)
                 show_error_message(self, f"Error al eliminar:\n{ve}")
            except Exception as e:
                show_error_message(self, f"Error inesperado al eliminar proveedor:\n{e}")
                print(f"Error deleting supplier {supplier.id}: {e}") # Log full error
