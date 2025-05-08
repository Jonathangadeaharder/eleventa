import sys
from decimal import Decimal, InvalidOperation
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QDialogButtonBox, QLabel, QDoubleSpinBox, QTextEdit
)

# Assuming Customer model is available
from core.models.customer import Customer
# Import utility functions
from ..utils import show_error_message

class AdjustBalanceDialog(QDialog):
    """Dialog for directly adjusting a customer's balance."""

    def __init__(self, customer: Customer, parent=None):
        super().__init__(parent)
        self._customer = customer
        self.adjustment_amount = Decimal(0) # Store the validated adjustment amount
        self.adjustment_notes = "" # Store the notes
        self.is_increase = False # True = increase debt, False = decrease debt

        self.setWindowTitle(f"Ajustar Saldo para {customer.name}")

        # --- Widgets ---
        self.customer_label = QLabel(f"Cliente: {customer.name}")
        self.balance_label = QLabel(f"Saldo Actual: $ {customer.credit_balance:.2f}")
        
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 1_000_000) # Min adjustment 0.01
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix("$ ")
        self.amount_spin.setValue(0.01) # Start with minimum

        # Add radio buttons or checkbox for increase/decrease selection
        from PySide6.QtWidgets import QRadioButton, QHBoxLayout
        self.decrease_radio = QRadioButton("Reducir Saldo (Pago)")
        self.increase_radio = QRadioButton("Aumentar Saldo (Deuda)")
        self.decrease_radio.setChecked(True) # Default to decrease
        
        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.decrease_radio)
        radio_layout.addWidget(self.increase_radio)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Notas sobre el ajuste (obligatorio)")
        self.notes_edit.setMaximumHeight(80)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        # --- Layout ---
        form_layout = QFormLayout()
        form_layout.addRow(self.customer_label)
        form_layout.addRow(self.balance_label)
        form_layout.addRow("Tipo de Ajuste:", radio_layout)
        form_layout.addRow("Monto (*):", self.amount_spin)
        form_layout.addRow("Notas (*):", self.notes_edit)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.button_box)

        # --- Connections ---
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.setMinimumWidth(400)

    def accept(self):
        """Validate input and store data before accepting."""
        amount_value = self.amount_spin.value()
        notes_value = self.notes_edit.toPlainText().strip()
        self.is_increase = self.increase_radio.isChecked()

        # Require notes for audit trail
        if not notes_value:
            show_error_message(self, "Notas Requeridas", 
                             "Por favor, ingrese una nota que explique este ajuste de saldo.")
            self.notes_edit.setFocus()
            return # Keep dialog open

        try:
            amount_decimal = Decimal(str(amount_value)).quantize(Decimal("0.01"))
            if amount_decimal <= 0:
                show_error_message(self, "Monto Inválido", "El monto del ajuste debe ser mayor a cero.")
                self.amount_spin.setFocus()
                return # Keep dialog open

            self.adjustment_amount = amount_decimal
            self.adjustment_notes = notes_value
            super().accept()

        except InvalidOperation:
            show_error_message(self, "Monto Inválido", "El monto ingresado no es válido.")
            self.amount_spin.setFocus()
            return 