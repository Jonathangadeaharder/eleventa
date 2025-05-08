from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, QTextEdit, 
    QPushButton, QDialogButtonBox, QWidget, QFormLayout, QMessageBox,
    QRadioButton, QButtonGroup, QGroupBox
)
from PySide6.QtCore import Qt
from typing import Optional
from decimal import Decimal

# Adjust imports
from core.models.product import Product
from core.services.inventory_service import InventoryService
from ui.utils import show_error_message

class AdjustInventoryDialog(QDialog):
    """Dialog for adjusting stock quantity of a product (increase or decrease)."""

    def __init__(self, inventory_service: InventoryService, product: Product, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.inventory_service = inventory_service
        self.product = product

        self.setWindowTitle(f"Ajustar Stock - {product.description}")
        self.setMinimumWidth(450)

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # --- Product Info (Read-only) ---
        self.code_label = QLabel(self.product.code)
        self.desc_label = QLabel(self.product.description)
        self.current_stock_label = QLabel(f"{self.product.quantity_in_stock:.2f} {self.product.unit}")
        
        form_layout.addRow("Código:", self.code_label)
        form_layout.addRow("Descripción:", self.desc_label)
        form_layout.addRow("Stock Actual:", self.current_stock_label)

        # --- Adjustment Type Selection ---
        adjustment_group = QGroupBox("Tipo de Ajuste")
        adjustment_layout = QVBoxLayout(adjustment_group)
        
        self.increase_radio = QRadioButton("Incrementar Stock")
        self.decrease_radio = QRadioButton("Disminuir Stock")
        self.increase_radio.setChecked(True)  # Default to increase
        
        self.adjustment_group = QButtonGroup()
        self.adjustment_group.addButton(self.increase_radio)
        self.adjustment_group.addButton(self.decrease_radio)
        
        adjustment_layout.addWidget(self.increase_radio)
        adjustment_layout.addWidget(self.decrease_radio)
        
        # --- Input Fields ---
        self.quantity_spinbox = QDoubleSpinBox()
        self.quantity_spinbox.setDecimals(2)
        self.quantity_spinbox.setRange(0.0, 999999.99)
        self.quantity_spinbox.setValue(1.0)  # Default quantity
        
        self.reason_edit = QTextEdit()
        self.reason_edit.setPlaceholderText("Motivo del ajuste (requerido)")
        self.reason_edit.setFixedHeight(60)

        form_layout.addRow("Cantidad a Ajustar:", self.quantity_spinbox)
        
        # Add all elements to main layout
        main_layout.addLayout(form_layout)
        main_layout.addWidget(adjustment_group)
        main_layout.addWidget(QLabel("Motivo:"))
        main_layout.addWidget(self.reason_edit)

        # Add result preview
        self.result_label = QLabel()
        self.result_label.setStyleSheet("font-weight: bold;")
        self._update_result_label()
        
        main_layout.addWidget(QLabel("Resultado del Ajuste:"))
        main_layout.addWidget(self.result_label)

        # --- Buttons ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)
        
        # Connect signals
        self.quantity_spinbox.valueChanged.connect(self._update_result_label)
        self.increase_radio.toggled.connect(self._update_result_label)
        
    def _update_result_label(self):
        """Update the result preview label based on current inputs."""
        current_stock = Decimal(str(self.product.quantity_in_stock))
        adjustment = Decimal(str(self.quantity_spinbox.value()))
        
        if self.increase_radio.isChecked():
            new_stock = current_stock + adjustment
            sign = "+"
        else:
            new_stock = current_stock - adjustment
            sign = "-"
            
        # Check if adjustment would result in negative stock
        if new_stock < 0:
            self.result_label.setText(f"ERROR: ¡El ajuste resultaría en stock negativo! ({new_stock:.2f})")
            self.result_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.result_label.setText(f"{current_stock:.2f} {sign} {adjustment:.2f} = {new_stock:.2f}")
            self.result_label.setStyleSheet("color: green; font-weight: bold;")

    def accept(self):
        """Validate input and call the inventory service."""
        quantity = Decimal(str(self.quantity_spinbox.value()))
        reason = self.reason_edit.toPlainText().strip()

        if quantity <= 0:
            show_error_message(self, "Cantidad Inválida", "La cantidad a ajustar debe ser mayor que cero.")
            self.quantity_spinbox.setFocus()
            return
            
        if not reason:
            show_error_message(self, "Motivo Requerido", "Por favor, ingrese el motivo del ajuste.")
            self.reason_edit.setFocus()
            return
        
        # If decreasing stock, make quantity negative
        if self.decrease_radio.isChecked():
            quantity = -quantity
            
        # Calculate new stock to check if it would be negative
        current_stock = Decimal(str(self.product.quantity_in_stock))
        new_stock = current_stock + quantity
        if new_stock < 0:
            show_error_message(self, "Stock Insuficiente", 
                              f"El ajuste resultaría en stock negativo ({new_stock:.2f}).")
            return
            
        try:
            # TODO: Get user_id if available
            user_id = None 
            updated_product = self.inventory_service.adjust_inventory(
                product_id=self.product.id,
                quantity=quantity,
                reason=reason,
                user_id=user_id
            )
            # If successful, close the dialog
            super().accept()

        except ValueError as e:
            QMessageBox.warning(self, "Error de Validación", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error Inesperado", f"Ocurrió un error al ajustar el inventario: {e}")
            print(f"Error adjusting inventory: {e}")

    def reject(self):
        """Reject the dialog."""
        super().reject() 