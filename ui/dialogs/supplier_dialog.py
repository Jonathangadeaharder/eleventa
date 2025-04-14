from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QMessageBox,
    QDialogButtonBox, QTextEdit
)
from PySide6.QtCore import Slot
from typing import Optional, Dict

from core.models.supplier import Supplier
# Assuming PurchaseService interface/class exists and is passed
# from core.services.purchase_service import PurchaseService # Adjust import path as needed

class SupplierDialog(QDialog):
    """Dialog for adding or editing a Supplier."""

    def __init__(self, purchase_service, supplier: Optional[Supplier] = None, parent=None):
        super().__init__(parent)
        self.purchase_service = purchase_service
        self.supplier = supplier # None if adding, existing Supplier object if editing

        self.setWindowTitle("Proveedor" if not supplier else "Editar Proveedor")

        # Widgets
        self.name_edit = QLineEdit()
        self.cuit_edit = QLineEdit()
        self.contact_person_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.address_edit = QTextEdit()
        self.notes_edit = QTextEdit()

        # Layout
        form_layout = QFormLayout()
        form_layout.addRow("Nombre (*):", self.name_edit)
        form_layout.addRow("CUIT:", self.cuit_edit)
        form_layout.addRow("Contacto:", self.contact_person_edit)
        form_layout.addRow("Teléfono:", self.phone_edit)
        form_layout.addRow("Email:", self.email_edit)
        form_layout.addRow("Dirección:", self.address_edit)
        form_layout.addRow("Notas:", self.notes_edit)

        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.button_box)

        # Populate form if editing
        if self.supplier:
            self._populate_form()

    def _populate_form(self):
        """Fills the form fields with the existing supplier's data."""
        if not self.supplier:
            return
        self.name_edit.setText(self.supplier.name or "")
        self.cuit_edit.setText(self.supplier.cuit or "")
        self.contact_person_edit.setText(self.supplier.contact_person or "")
        self.phone_edit.setText(self.supplier.phone or "")
        self.email_edit.setText(self.supplier.email or "")
        self.address_edit.setPlainText(self.supplier.address or "")
        self.notes_edit.setPlainText(self.supplier.notes or "")

    def _get_form_data(self) -> Dict:
        """Retrieves data from the form fields."""
        return {
            "name": self.name_edit.text().strip(),
            "cuit": self.cuit_edit.text().strip() or None, # Treat empty as None
            "contact_person": self.contact_person_edit.text().strip() or None,
            "phone": self.phone_edit.text().strip() or None,
            "email": self.email_edit.text().strip() or None,
            "address": self.address_edit.toPlainText().strip() or None,
            "notes": self.notes_edit.toPlainText().strip() or None,
        }

    @Slot()
    def accept(self):
        """Handles the OK button click: validates and saves the supplier."""
        supplier_data = self._get_form_data()

        if not supplier_data["name"]:
            QMessageBox.warning(self, "Error de Validación", "El nombre del proveedor es obligatorio.")
            self.name_edit.setFocus()
            return

        try:
            if self.supplier: # Editing existing supplier
                self.purchase_service.update_supplier(self.supplier.id, supplier_data)
                QMessageBox.information(self, "Éxito", "Proveedor actualizado correctamente.")
            else: # Adding new supplier
                self.purchase_service.add_supplier(supplier_data)
                QMessageBox.information(self, "Éxito", "Proveedor agregado correctamente.")
            super().accept() # Close dialog on success
        except ValueError as ve:
            QMessageBox.critical(self, "Error", f"Error al guardar proveedor:\n{ve}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error inesperado:\n{e}")
            # Log the full error for debugging
            print(f"Unexpected error saving supplier: {e}")
