import sys
from decimal import Decimal, InvalidOperation
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QDialogButtonBox,
    QLabel,
    QDoubleSpinBox,
    QTextEdit,
)

# Assuming Customer model is available
from core.models.customer import Customer

# Import utility functions
from ..utils import show_error_message


class RegisterPaymentDialog(QDialog):
    """Dialog for registering a payment on a customer's account."""

    def __init__(self, customer: Customer, parent=None):
        super().__init__(parent)
        self._customer = customer
        self.payment_amount = Decimal(0)  # Store the validated payment amount
        self.payment_notes = ""  # Store the notes

        self.setWindowTitle(f"Registrar Pago para {customer.name}")

        # --- Widgets ---
        self.customer_label = QLabel(f"Cliente: {customer.name}")
        self.balance_label = QLabel(f"Saldo Actual: $ {customer.credit_balance:.2f}")

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 1_000_000)  # Min payment 0.01
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix("$ ")
        self.amount_spin.setValue(0.01)  # Start with minimum

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Notas sobre el pago (opcional)")

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        # --- Layout ---
        form_layout = QFormLayout()
        form_layout.addRow(self.customer_label)
        form_layout.addRow(self.balance_label)
        form_layout.addRow("Monto a Pagar (*):", self.amount_spin)
        form_layout.addRow("Notas:", self.notes_edit)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.button_box)

        # --- Connections ---
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.setMinimumWidth(350)

    def accept(self):
        """Validate amount and store data before accepting."""
        amount_value = self.amount_spin.value()
        notes_value = self.notes_edit.toPlainText().strip()

        try:
            amount_decimal = Decimal(str(amount_value)).quantize(Decimal("0.01"))
            if amount_decimal <= 0:
                show_error_message(
                    self, "Monto Inválido", "El monto del pago debe ser mayor a cero."
                )
                self.amount_spin.setFocus()
                return  # Keep dialog open

            self.payment_amount = amount_decimal
            self.payment_notes = notes_value or None  # Store None if empty
            super().accept()

        except InvalidOperation:
            show_error_message(
                self, "Monto Inválido", "El monto ingresado no es válido."
            )
            self.amount_spin.setFocus()
            return


# Example Usage
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    # Dummy customer for testing
    dummy = Customer(id=1, name="Test Customer", credit_balance=-150.75)

    app = QApplication(sys.argv)
    dialog = RegisterPaymentDialog(dummy)
    if dialog.exec():
        print("Payment Accepted:")
        print(f"  Amount: {dialog.payment_amount}")
        print(f"  Notes: {dialog.payment_notes}")
    else:
        print("Payment Cancelled")
    # sys.exit(app.exec()) # Avoid starting loop in test
