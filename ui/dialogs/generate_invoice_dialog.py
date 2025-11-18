from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTableView,
)
from PySide6.QtCore import Qt

from core.services.invoicing_service import InvoicingService
from ui.models.table_models import SaleItemTableModel
from ui.utils import show_error_message, show_info_message


class GenerateInvoiceDialog(QDialog):
    """Dialog for selecting a sale to generate an invoice from."""

    def __init__(self, invoicing_service: InvoicingService, parent=None):
        super().__init__(parent)
        self.invoicing_service = invoicing_service
        self.setWindowTitle("Generar Factura")
        self.setMinimumSize(500, 400)
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Sale ID input section
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("ID de Venta:"))

        self.sale_id_edit = QLineEdit()
        self.sale_id_edit.setPlaceholderText("Ingrese el ID de la venta")
        input_layout.addWidget(self.sale_id_edit)

        self.search_button = QPushButton("Buscar")
        self.search_button.clicked.connect(self.search_sale)
        input_layout.addWidget(self.search_button)

        main_layout.addLayout(input_layout)

        # Sale details section
        self.sale_details_layout = QVBoxLayout()

        # Sale header info
        self.sale_info_layout = QHBoxLayout()
        self.sale_date_label = QLabel("Fecha: ")
        self.sale_info_layout.addWidget(self.sale_date_label)
        self.sale_info_layout.addStretch()
        self.sale_total_label = QLabel("Total: $0.00")
        self.sale_info_layout.addWidget(self.sale_total_label)

        self.sale_details_layout.addLayout(self.sale_info_layout)

        # Customer info
        self.customer_label = QLabel("Cliente: ")
        self.sale_details_layout.addWidget(self.customer_label)

        # Sale items table
        self.sale_items_table = QTableView()
        self.sale_items_table.setEditTriggers(QTableView.NoEditTriggers)
        self.sale_items_table.setSelectionBehavior(QTableView.SelectRows)
        self.sale_items_table.setAlternatingRowColors(True)

        self.sale_items_model = SaleItemTableModel()
        self.sale_items_table.setModel(self.sale_items_model)

        self.sale_details_layout.addWidget(self.sale_items_table)

        # Initially hide sale details
        self.sale_widget = QLabel("Ingrese el ID de una venta y presione 'Buscar'")
        self.sale_widget.setAlignment(Qt.AlignCenter)
        self.sale_details_layout.addWidget(self.sale_widget)
        self.sale_items_table.hide()

        main_layout.addLayout(self.sale_details_layout)

        # Buttons section
        buttons_layout = QHBoxLayout()

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        buttons_layout.addStretch()

        self.generate_button = QPushButton("Generar Factura")
        self.generate_button.clicked.connect(self.generate_invoice)
        self.generate_button.setEnabled(False)  # Disable until sale is selected
        buttons_layout.addWidget(self.generate_button)

        main_layout.addLayout(buttons_layout)

        # Focus on sale ID edit
        self.sale_id_edit.setFocus()

    def search_sale(self):
        """Search for a sale by ID and display its details."""
        sale_id_text = self.sale_id_edit.text().strip()
        if not sale_id_text:
            show_error_message("Por favor ingrese un ID de venta.")
            return

        try:
            # Parse sale ID
            sale_id = int(sale_id_text)

            # Get the sale service from the invoicing service
            # This assumes the invoicing service has a sale_repo attribute
            sale_repo = self.invoicing_service.sale_repo

            # Try to get the sale
            sale = sale_repo.get_by_id(sale_id)

            if not sale:
                show_error_message(f"No se encontró una venta con ID: {sale_id}")
                self.generate_button.setEnabled(False)
                return

            # Check if this sale already has an invoice
            existing_invoice = self.invoicing_service.get_invoice_by_sale_id(sale_id)
            if existing_invoice:
                show_error_message(
                    f"Esta venta ya tiene una factura asociada.\n"
                    f"Número de factura: {existing_invoice.invoice_number}"
                )
                self.generate_button.setEnabled(False)
                return

            # Check if the sale has a customer (required for invoicing)
            if not sale.customer_id:
                show_error_message(
                    "Esta venta no tiene un cliente asociado.\n"
                    "Se requiere un cliente para poder generar una factura."
                )
                self.generate_button.setEnabled(False)
                return

            # Update the UI with sale details
            self.update_sale_details(sale)

            # Enable the generate button
            self.generate_button.setEnabled(True)

        except ValueError:
            show_error_message(
                "Por favor ingrese un ID de venta válido (número entero)."
            )
        except Exception as e:
            show_error_message(f"Error al buscar la venta: {str(e)}")

    def update_sale_details(self, sale):
        """Update the UI with sale details."""
        # Hide the empty state label
        self.sale_widget.hide()

        # Show the items table
        self.sale_items_table.show()

        # Update date and total
        self.sale_date_label.setText(f"Fecha: {sale.date.strftime('%d/%m/%Y')}")
        self.sale_total_label.setText(f"Total: ${sale.total:.2f}")

        # Update customer info if available
        if sale.customer_id:
            customer_repo = self.invoicing_service.customer_repo
            customer = customer_repo.get_by_id(sale.customer_id)
            if customer:
                self.customer_label.setText(f"Cliente: {customer.name}")
            else:
                self.customer_label.setText(
                    f"Cliente ID: {sale.customer_id} (no encontrado)"
                )
        else:
            self.customer_label.setText("Cliente: No especificado")

        # Update items table
        self.sale_items_model.clear()
        if sale.items:
            for item in sale.items:
                self.sale_items_model.add_item(item)

        # Store the sale ID for later use
        self.current_sale_id = sale.id

    def generate_invoice(self):
        """Generate an invoice for the selected sale."""
        try:
            if not hasattr(self, "current_sale_id"):
                show_error_message(
                    self, "Error", "Por favor seleccione una venta primero."
                )
                return
            invoice = self.invoicing_service.create_invoice_from_sale(
                self.current_sale_id
            )
            show_info_message(
                self,
                "Factura generada",
                f"Factura generada correctamente.\nNúmero de factura: {invoice.invoice_number}",
            )
            self.accept()
        except Exception as e:
            show_error_message(self, "Error", f"Error al generar la factura: {str(e)}")
