from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QDoubleSpinBox,
    QTextEdit,
    QDialogButtonBox,
    QWidget,
    QFormLayout,
    QMessageBox,
)
from typing import Optional

# Adjust imports
from core.models.product import Product
from core.models.user import User
from core.services.inventory_service import InventoryService
from ui.utils import show_error_message  # Assuming utility function


class AddInventoryDialog(QDialog):
    """Dialog for adding stock quantity to a product."""

    def __init__(
        self,
        inventory_service: InventoryService,
        product: Product,
        current_user: Optional[User] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.inventory_service = inventory_service
        self.product = product
        self.current_user = current_user

        self.setWindowTitle(f"Agregar Cantidad - {product.description}")
        self.setMinimumWidth(400)

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # --- Product Info (Read-only) ---
        self.code_label = QLabel(self.product.code)
        self.desc_label = QLabel(self.product.description)
        self.current_stock_label = QLabel(
            f"{self.product.quantity_in_stock:.2f} {self.product.unit}"
        )

        form_layout.addRow("Código:", self.code_label)
        form_layout.addRow("Descripción:", self.desc_label)
        form_layout.addRow("Stock Actual:", self.current_stock_label)

        # --- Input Fields ---
        self.quantity_spinbox = QDoubleSpinBox()
        self.quantity_spinbox.setDecimals(2)
        self.quantity_spinbox.setRange(
            0.0, 999999.99
        )  # Permitir 0.0 para validación y tests
        self.quantity_spinbox.setValue(1.0)  # Default quantity

        self.cost_spinbox = QDoubleSpinBox()
        self.cost_spinbox.setDecimals(2)
        self.cost_spinbox.setRange(0.00, 9999999.99)
        self.cost_spinbox.setValue(self.product.cost_price)  # Default to current cost
        self.cost_spinbox.setPrefix("$ ")

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText(
            "Opcional: Motivo, Nro. Factura Compra, etc."
        )
        self.notes_edit.setFixedHeight(60)

        form_layout.addRow("Cantidad a Agregar:", self.quantity_spinbox)
        form_layout.addRow("Nuevo Costo (Opcional):", self.cost_spinbox)
        form_layout.addRow("Notas:", self.notes_edit)

        main_layout.addLayout(form_layout)

        # --- Buttons ---
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

    def accept(self):
        """Validate input and call the inventory service."""
        quantity = self.quantity_spinbox.value()
        new_cost = self.cost_spinbox.value()
        notes = self.notes_edit.toPlainText().strip()

        if quantity <= 0:
            show_error_message(
                self,
                "Cantidad Inválida",
                "La cantidad a agregar debe ser mayor que cero.",
            )
            self.quantity_spinbox.setFocus()
            return

        # Check if cost actually changed to avoid unnecessary updates
        cost_to_update = new_cost if new_cost != self.product.cost_price else None

        try:
            # Use current user ID if available
            user_id = self.current_user.id if self.current_user else None
            self.inventory_service.add_inventory(
                product_id=self.product.id,
                quantity=quantity,
                new_cost_price=cost_to_update,
                notes=notes,
                user_id=user_id,
            )
            # If successful, close the dialog
            super().accept()

        except ValueError as e:
            QMessageBox.warning(self, "Error de Validación", str(e))
        except Exception as e:
            QMessageBox.critical(
                self, "Error Inesperado", f"Ocurrió un error al agregar inventario: {e}"
            )
            print(f"Error adding inventory: {e}")

    def reject(self):
        """Reject the dialog."""
        super().reject()
