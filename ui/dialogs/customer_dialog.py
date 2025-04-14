import sys
from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QDialogButtonBox, QMessageBox, QDoubleSpinBox
)

# Assuming Customer model and service are available
from core.models.customer import Customer
from core.services.customer_service import CustomerService
# Import utility functions if needed (e.g., for showing messages)
from ..utils import show_error_message, show_info_message

class CustomerDialog(QDialog):
    """Dialog for adding or editing customer information."""

    def __init__(self, customer_service: CustomerService, customer: Optional[Customer] = None, parent=None):
        super().__init__(parent)
        self._customer_service = customer_service
        self._customer = customer # None if adding, existing customer if editing

        self.setWindowTitle("Editar Cliente" if customer else "Nuevo Cliente")

        # --- Widgets ---
        self.name_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.address_edit = QLineEdit()
        self.credit_limit_spin = QDoubleSpinBox()
        self.credit_limit_spin.setRange(0, 1_000_000) # Set appropriate range
        self.credit_limit_spin.setDecimals(2)
        self.credit_limit_spin.setPrefix("$ ")

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        # --- Layout --- (Using QFormLayout for label-field pairs)
        form_layout = QFormLayout()
        form_layout.addRow("Nombre (*):", self.name_edit)
        form_layout.addRow("Teléfono:", self.phone_edit)
        form_layout.addRow("Email:", self.email_edit)
        form_layout.addRow("Dirección:", self.address_edit)
        form_layout.addRow("Límite de Crédito:", self.credit_limit_spin)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.button_box)

        # --- Connections ---
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # --- Populate Form if Editing ---
        if self._customer:
            self._populate_form()

        self.setMinimumWidth(400) # Adjust as needed

    def _populate_form(self):
        """Fills the form fields with data from the existing customer."""
        if not self._customer:
            return
        self.name_edit.setText(self._customer.name or "")
        self.phone_edit.setText(self._customer.phone or "")
        self.email_edit.setText(self._customer.email or "")
        self.address_edit.setText(self._customer.address or "")
        self.credit_limit_spin.setValue(self._customer.credit_limit or 0.0)

    def _get_customer_data_from_form(self) -> dict:
        """Extracts customer data from the form fields."""
        return {
            "name": self.name_edit.text().strip(),
            "phone": self.phone_edit.text().strip() or None,
            "email": self.email_edit.text().strip() or None,
            "address": self.address_edit.text().strip() or None,
            "credit_limit": self.credit_limit_spin.value(),
            # Credit balance is not typically edited here
            # "credit_balance": self._customer.credit_balance if self._customer else 0.0
        }

    def accept(self):
        """Handles the OK button click: validates and saves the customer."""
        customer_data = self._get_customer_data_from_form()

        try:
            if self._customer: # Editing existing customer
                # Include the existing balance when calling update
                # This assumes update_customer signature takes all fields or uses kwargs
                # We might need to adjust update_customer or how we pass data
                customer_data["credit_balance"] = self._customer.credit_balance # Keep existing balance
                self._customer_service.update_customer(self._customer.id, **customer_data)
                show_info_message(self, "Cliente Actualizado", "Cliente actualizado correctamente.")
            else: # Adding new customer
                self._customer_service.add_customer(**customer_data)
                show_info_message(self, "Cliente Agregado", "Nuevo cliente agregado correctamente.")

            super().accept() # Close the dialog successfully

        except ValueError as e:
            show_error_message(self, "Error de Validación", str(e))
        except Exception as e: # Catch other potential errors (DB, etc.)
            show_error_message(self, "Error", f"Ocurrió un error inesperado: {e}")
            # Keep dialog open on unexpected errors

# Example Usage (for testing if run directly)
if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    # Mock CustomerService for testing
    class MockCustomerService:
        def add_customer(self, **kwargs): print(f"Adding: {kwargs}"); return Customer(id=1, **kwargs)
        def update_customer(self, customer_id, **kwargs): print(f"Updating {customer_id}: {kwargs}"); return Customer(id=customer_id, **kwargs)
        def get_customer_by_id(self, id): return None # Needed by service update

    app = QApplication(sys.argv)
    service = MockCustomerService()

    # Test Add
    dialog_add = CustomerDialog(service)
    if dialog_add.exec():
        print("Add Dialog Accepted")

    # Test Edit (with dummy data)
    dummy_customer = Customer(id=5, name="Test Edit", phone="555", email="edit@test.com", address="Addr", credit_limit=150.0, credit_balance=20.0)
    dialog_edit = CustomerDialog(service, customer=dummy_customer)
    if dialog_edit.exec():
        print("Edit Dialog Accepted")

    sys.exit() # Exit without starting event loop if run directly 