from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableView, QPushButton, QHeaderView, QMessageBox,
    QComboBox, QFrame, QDialog, QDialogButtonBox, QRadioButton,
    QAbstractItemView, QFormLayout, QDoubleSpinBox, QSizePolicy, QSpacerItem,
    QGroupBox
)
from PySide6.QtCore import Qt, Slot, QTimer, QStringListModel, QPoint
from PySide6.QtWidgets import QCompleter
from PySide6.QtGui import QIcon, QFont, QPixmap, QKeySequence
from decimal import Decimal
from typing import List, Optional
import os
import subprocess
import sys

# Import models and services
from ui.models.table_models import SaleItemTableModel
from core.models.sale import SaleItem
from core.models.customer import Customer
from core.models.user import User
from core.models.product import Product
from core.services.product_service import ProductService
from core.services.sale_service import SaleService
from core.services.customer_service import CustomerService

# Import common UI functions
from ui.utils import (
    show_error_message, show_info_message, ask_confirmation,
    style_text_input, style_primary_button, style_secondary_button,
    style_dropdown, style_heading_label, style_total_label
)

# Import resources
from ui.resources import resources  # Import the compiled resources

# --- Payment Dialog (Optional, alternative to radio buttons) ---
class PaymentDialog(QDialog):
    """Dialog to select payment method and optionally confirm amount."""
    def __init__(self, total_amount: Decimal, allow_credit: bool, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar Pago")
        self.selected_payment_method = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Total a Pagar: $ {total_amount:.2f}"))

        self.cash_radio = QRadioButton("&Efectivo")
        self.card_radio = QRadioButton("&Tarjeta")
        self.credit_radio = QRadioButton("A &Crédito")
        self.other_radio = QRadioButton("&Otro")

        # Disable credit if not allowed (e.g., no customer selected)
        self.credit_radio.setEnabled(allow_credit)

        self.cash_radio.setChecked(True) # Default to cash

        layout.addWidget(self.cash_radio)
        layout.addWidget(self.card_radio)
        layout.addWidget(self.credit_radio)
        layout.addWidget(self.other_radio)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        if self.cash_radio.isChecked():
            self.selected_payment_method = "Efectivo"
        elif self.card_radio.isChecked():
            self.selected_payment_method = "Tarjeta"
        elif self.credit_radio.isChecked():
            self.selected_payment_method = "Crédito"
        elif self.other_radio.isChecked():
            self.selected_payment_method = "Otro"
        else:
             show_error_message(self, "Error", "Debe seleccionar un método de pago.")
             return # Keep dialog open

        super().accept()


# --- Sales View --- #
class SalesView(QWidget):
    """View for processing sales."""

    def __init__(
        self,
        product_service: ProductService,
        sale_service: SaleService,
        customer_service: CustomerService,
        current_user: User,
        parent=None
    ):
        super().__init__(parent)

        # --- Test: Create a blank QPixmap ---
        print("Attempting to create blank QPixmap in SalesView init...")
        try:
            blank_pixmap = QPixmap(16, 16)
            print(f"Blank QPixmap created: {blank_pixmap}, isNull: {blank_pixmap.isNull()}")
            if blank_pixmap.isNull():
                print("Warning: Blank QPixmap is null after creation.")
        except Exception as e:
            print(f"Error creating blank QPixmap: {e}")
        # --- End Test ---

        self.product_service = product_service
        self.sale_service = sale_service
        self.customer_service = customer_service
        self.current_user = current_user # Store current user
        self._customers: List[Customer] = [] # Cache for customer list
        self.selected_customer = None
        self._current_total = Decimal("0.00")  # Initialize total amount
        self.setObjectName("sales_view")

        self.setWindowTitle("Ventas")
        self.sale_item_model = SaleItemTableModel()

        self._init_ui()
        self._connect_signals()
        self.update_total()  # Initialize the total amount

    def _init_ui(self):
        """Initialize the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # --- Header Section with product entry and customer selection ---
        header_container = QFrame()
        header_container.setFrameShape(QFrame.Shape.StyledPanel)
        header_container.setFrameShadow(QFrame.Shadow.Raised)
        header_container.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border-radius: 6px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        # Product entry part
        entry_layout = QHBoxLayout()
        entry_layout.setSpacing(8)
        
        self.code_label = QLabel("Código/Nombre:")
        self.code_label.setStyleSheet("font-weight: bold;")
        
        self.product_combo = QComboBox()
        self.product_combo.setEditable(True)
        self.product_combo.setPlaceholderText("Buscar por código o nombre...")
        self.product_combo.setMinimumWidth(300)
        style_text_input(self.product_combo.lineEdit())
        self.product_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus) # Explicit focus policy
        self.product_combo.lineEdit().setFocusPolicy(Qt.FocusPolicy.StrongFocus) # Explicit focus policy for lineEdit
        self.product_combo.view().setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # Add a top margin to the QComboBox view to prevent overlap
        self.product_combo.setStyleSheet("""
            QComboBox QAbstractItemView {
                margin-top: 5px; /* Increased margin */
            }
        """)
        # --- QCompleter integration for non-blocking product suggestions ---
        self._suggestion_model = QStringListModel(self)
        self._completer = QCompleter(self._suggestion_model, self)
        self._completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._completer.setFilterMode(Qt.MatchContains)
        le = self.product_combo.lineEdit()
        le.setCompleter(self._completer)
        self._display_map = {}
        self._selected_suggested_product = None
        self._completer.activated[str].connect(self._on_completer_activated)
        
        self.add_button = QPushButton("Agregar")
        self.add_button.setIcon(QIcon(":/icons/icons/new.png")) # Reverted to original resource path
        style_secondary_button(self.add_button)
        
        entry_layout.addWidget(self.code_label)
        entry_layout.addWidget(self.product_combo)
        entry_layout.addWidget(self.add_button)
        header_layout.addLayout(entry_layout)
        
        # Spacer
        header_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, 
                                              QSizePolicy.Policy.Minimum))
        
        # Customer selection part
        customer_layout = QHBoxLayout()
        customer_layout.setSpacing(8)
        
        self.customer_label = QLabel("Cliente: Ninguno")
        self.customer_label.setStyleSheet("""
            padding: 5px 10px;
            background-color: #e6e6e6;
            border-radius: 3px;
            font-weight: bold;
        """)
        
        self.select_customer_button = QPushButton("Seleccionar Cliente")
        self.select_customer_button.setIcon(QIcon(":/icons/icons/customers.png")) # Reverted to original
        style_secondary_button(self.select_customer_button)
        
        customer_layout.addWidget(self.customer_label)
        customer_layout.addWidget(self.select_customer_button)
        header_layout.addLayout(customer_layout)
        
        main_layout.addWidget(header_container)

        # --- Table ---
        table_container = QGroupBox("Detalle de la Venta")
        table_container.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
            }
        """)
        
        table_layout = QVBoxLayout(table_container)
        
        self.table_view = QTableView()
        self.table_view.setModel(self.sale_item_model)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setStyleSheet("""
            QTableView {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 2px;
                gridline-color: #e0e0e0;
                selection-background-color: #2c6ba5;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 5px;
                border: none;
                border-right: 1px solid #d0d0d0;
                border-bottom: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """)
        
        # Configure column widths
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_view.horizontalHeader().setHighlightSections(False)
        table_layout.addWidget(self.table_view)
        
        main_layout.addWidget(table_container, 1)  # Give table stretch factor of 1

        # --- Bottom Layout (Total + Actions) ---
        bottom_container = QFrame()
        bottom_container.setFrameShape(QFrame.Shape.StyledPanel)
        bottom_container.setFrameShadow(QFrame.Shadow.Raised)
        bottom_container.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border-radius: 6px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        bottom_layout = QHBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(15, 10, 15, 10)

        # Total amount display
        total_layout = QVBoxLayout()
        total_layout.setSpacing(2)
        
        total_label = QLabel("Total:")
        total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.total_amount_label = QLabel("$0.00")
        style_total_label(self.total_amount_label)
        self.total_amount_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.total_amount_label.setMinimumWidth(150)
        
        total_layout.addWidget(total_label)
        total_layout.addWidget(self.total_amount_label)
        bottom_layout.addLayout(total_layout)

        bottom_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, 
                                                QSizePolicy.Policy.Minimum))

        # Action buttons
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(8)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        
        self.remove_item_button = QPushButton("Quitar Artículo")
        self.remove_item_button.setIcon(QIcon(":/icons/icons/delete.png")) # Reverted to original
        style_secondary_button(self.remove_item_button)
        
        self.cancel_button = QPushButton("Cancelar Venta")
        self.cancel_button.setIcon(QIcon(":/icons/icons/cancel.png")) # Reverted to original
        style_secondary_button(self.cancel_button)
        
        buttons_layout.addWidget(self.remove_item_button)
        buttons_layout.addWidget(self.cancel_button)
        
        actions_layout.addLayout(buttons_layout)
        
        # Add finalizing and invoice buttons
        finalizing_layout = QHBoxLayout()
        finalizing_layout.setSpacing(8)
        
        self.finalize_button = QPushButton("Finalizar Venta (F12)")
        style_primary_button(self.finalize_button)
        self.finalize_button.setIcon(QIcon(":/icons/icons/save.png")) # Reverted to original
        finalizing_layout.addWidget(self.finalize_button)
        
        self.invoice_button = QPushButton("Facturar")
        style_secondary_button(self.invoice_button)
        self.invoice_button.setIcon(QIcon(":/icons/icons/invoice.png")) # Reverted to original
        self.invoice_button.setEnabled(False)  # Disabled by default until a sale is completed
        finalizing_layout.addWidget(self.invoice_button)
        
        actions_layout.addLayout(finalizing_layout)
        
        bottom_layout.addLayout(actions_layout)
        
        main_layout.addWidget(bottom_container)
        
        # Set focus to code entry
        self.product_combo.setFocus()

    def _connect_signals(self):
        """Connect UI signals to slots."""
        self.add_button.clicked.connect(self.add_item_from_entry)
        self.table_view.doubleClicked.connect(self._edit_selected_item_quantity) # Placeholder
        self.remove_item_button.clicked.connect(self.remove_selected_item)
        self.cancel_button.clicked.connect(self.cancel_current_sale)
        self.finalize_button.clicked.connect(self.finalize_current_sale)
        self.select_customer_button.clicked.connect(self._select_customer)
        self.sale_item_model.dataChanged.connect(self.update_total) # Connect dataChanged
        self.sale_item_model.modelReset.connect(self.update_total)  # Connect modelReset
        self.invoice_button.clicked.connect(self.generate_invoice_from_sale)

        # Connect search signal for product combo
        self.product_combo.lineEdit().textEdited.connect(self._search_and_suggest_products)
        self.product_combo.activated.connect(self._product_selected_from_combo) # Handle selection

    def _product_selected_from_combo(self, index: int):
        # This can be used if we want to immediately add when selected, or pre-fill something.
        # For now, we'll let the user press "Add" or Enter.
        # If user selects an item, then presses enter on the lineedit, it should add.
        # The QComboBox's lineEdit() QLineEdit emits returnPressed when Enter is pressed.
        # pass
        # When a product is selected from the dropdown, add it to the sale immediately.
        # The 'index' argument is provided by the 'activated' signal but not directly used by add_item_from_entry,
        # as it fetches the current selection from the combobox itself.
        if index >= 0: # Ensure a valid item was selected (index -1 means no selection or text edited)
            # Check if the item at index has valid product data before proceeding
            product_data = self.product_combo.itemData(index)
            if product_data and isinstance(product_data, Product):
                self.add_item_from_entry()
            # else: item might be a placeholder or an error, do nothing or log

    def keyPressEvent(self, event: QKeySequence):
        """Handle global key presses for shortcuts."""
        super().keyPressEvent(event)
        if event.key() == Qt.Key.Key_F10:
            self.finalize_current_sale()
        elif event.key() == Qt.Key.Key_F5:
            # Potentially refresh products or other data, if applicable
            pass
        elif event.matches(QKeySequence.StandardKey.Delete):
            if self.table_view.hasFocus():
                self.remove_selected_item()
        elif event.key() == Qt.Key.Key_Enter or event.key() == Qt.Key.Key_Return:
            if self.product_combo.lineEdit().hasFocus():
                self.add_item_from_entry()
            elif self.finalize_button.hasFocus(): # Check if finalize button has focus
                self.finalize_current_sale()

    # --- Customer Handling --- #
    @Slot()
    def _load_customers(self):
        """Load customers from the service."""
        try:
            self._customers = self.customer_service.get_all_customers()
        except Exception as e:
            show_error_message(self, "Error", f"No se pudieron cargar los clientes: {e}")
            self._customers = []

    @Slot()
    def _select_customer(self):
        """Open a dialog to select a customer for the sale."""
        from ui.dialogs.select_customer_dialog import SelectCustomerDialog
        
        # Load customers if we haven't already
        if not self._customers:
            self._load_customers()
            
        dialog = SelectCustomerDialog(self._customers, self)
        if dialog.exec():
            selected_customer = dialog.get_selected_customer()
            if selected_customer:
                self.selected_customer = selected_customer
                self.customer_label.setText(f"Cliente: {selected_customer.name}")
            else:
                self.selected_customer = None
                self.customer_label.setText("Cliente: Ninguno")

    def _get_selected_customer_id(self) -> Optional[int]:
        """Gets the ID of the selected customer."""
        # Handle both the proper attribute and the mock case for testing
        if hasattr(self, 'selected_customer') and self.selected_customer:
            return self.selected_customer.id
        elif hasattr(self, 'customer_combo') and hasattr(self.customer_combo, 'currentData'):
            # This branch is used in tests where customer_combo is a MagicMock
            return self.customer_combo.currentData()

    # --- Existing Slots / Methods (add_item, update_total, remove_item, cancel_current_sale) --- #
    @Slot(str)
    def _search_and_suggest_products(self, text: str):
        """Searches products based on input and updates the completer for product suggestions."""
        line_edit = self.product_combo.lineEdit()
        combo_box = self.product_combo

        # If text is too short or empty, clear suggestions and hide popup
        if not text or len(text) < 2: # Min 2 chars to search
            self._suggestion_model.setStringList([])
            self._display_map = {}
            self._selected_suggested_product = None
            if self._completer.popup() and self._completer.popup().isVisible():
                self._completer.popup().hide()
            return

        # Text is valid, attempt to find products
        products = self.product_service.find_product(text) # Service call

        if products:
            displays = [
                f"{p.code} – {p.description} (Stock: {p.quantity_in_stock:.2f})"
                for p in products
            ]
            self._display_map = dict(zip(displays, products))
            self._suggestion_model.setStringList(displays)
            line_edit.setFocus() # Keep focus on the line edit
        else:
            # No products found for the search term
            self._suggestion_model.setStringList([])
            self._display_map = {}
            self._selected_suggested_product = None

        # Popup positioning logic: only show and position if there are suggestions
        if self._suggestion_model.stringList(): # Check if model has strings
            self._completer.complete() # Trigger completer (it uses the model)
            popup = self._completer.popup()
            if popup:
                popup.setFixedWidth(line_edit.width())
                def move_popup_action():
                    global_x = line_edit.mapToGlobal(QPoint(0, 0)).x()
                    global_y = combo_box.mapToGlobal(QPoint(0, combo_box.height() + 4)).y()
                    popup.move(global_x, global_y)
                QTimer.singleShot(0, move_popup_action)
        else:
            # If, after all checks, there are no suggestions, ensure popup is hidden
            if self._completer.popup() and self._completer.popup().isVisible():
                self._completer.popup().hide()

    @Slot(str)
    def _on_completer_activated(self, display: str):
        product = self._display_map.get(display)
        if not product:
            self._selected_suggested_product = None
            return
        le = self.product_combo.lineEdit()
        le.setText(display)
        le.setCursorPosition(len(display))
        self._selected_suggested_product = product

    @Slot()
    def add_item_from_entry(self):
        product_to_add: Optional[Product] = None

        # Prefer product selected from completer
        if self._selected_suggested_product:
            product_to_add = self._selected_suggested_product
            self._selected_suggested_product = None
            print(f"Product selected from completer: {product_to_add.code}")
        else:
            # Try to get product from combobox selection first
            selected_data = self.product_combo.currentData()
            if selected_data and isinstance(selected_data, Product):
                product_to_add = selected_data
                print(f"Product selected from combo: {product_to_add.code}")
            else:
                # If no selection or data is not Product, use the text (code or name fragment)
                code_or_name = self.product_combo.currentText().strip()
                if not code_or_name:
                    self.product_combo.setFocus()
                    return

                print(f"Attempting to find product by text: {code_or_name}")
                try:
                    # Attempt to get by code first for exact match
                    product_by_code = self.product_service.get_product_by_code(code_or_name)
                    if product_by_code:
                        product_to_add = product_by_code
                    else:
                        # If not found by exact code, try find_product and take the best match if unambiguous
                        # This part might need more sophisticated logic if find_product returns multiple items
                        # For now, we assume if user typed something not exactly a code, and didn't pick
                        # from dropdown, they might expect an error or a chance to refine.
                        # Or, if find_product returns one exact match for the text, use that.
                        possible_products = self.product_service.find_product(code_or_name)
                        if len(possible_products) == 1:
                            product_to_add = possible_products[0]
                        elif len(possible_products) > 1:
                            # Ambiguous: multiple products match. User should select from dropdown.
                            # Or, if the current text is an exact code of one of them:
                            for p in possible_products:
                                if p.code == code_or_name:
                                    product_to_add = p
                                    break
                            if not product_to_add:
                                show_error_message(self, "Producto ambiguo", 
                                                   f"Múltiples productos coinciden con '{code_or_name}'. Por favor, seleccione uno de la lista.")
                                self.product_combo.setFocus()
                                self.product_combo.showPopup() # Encourage selection
                                return
                except Exception as e: # Catch errors during product fetch
                    show_error_message(self, "Error de Búsqueda", f"Error al buscar producto: {e}")
                    self.product_combo.setFocus()
                    return

        if not product_to_add:
            show_error_message(self, "Producto No Encontrado", f"No se encontró un producto con el texto: {self.product_combo.currentText().strip()}")
            self.product_combo.lineEdit().selectAll()
            self.product_combo.setFocus()
            return

        # At this point, product_to_add should be a valid Product object
        try:
            quantity = Decimal("1") # Default quantity
            if product_to_add.sell_price is None:
                show_error_message(self, "Error de Precio", f"El producto '{product_to_add.code}' no tiene un precio de venta definido.")
                self.product_combo.lineEdit().selectAll()
                self.product_combo.setFocus()
                return
            
            unit_price = Decimal(str(product_to_add.sell_price))
            
            sale_item = SaleItem(
                product_id=product_to_add.id,
                quantity=quantity,
                unit_price=unit_price,
                product_code=product_to_add.code,
                product_description=product_to_add.description
            )
            
            print(f"Adding product: {product_to_add.code}, price: {product_to_add.sell_price}, as Decimal: {unit_price}")
            
            self.sale_item_model.add_item(sale_item)
            self.product_combo.clearEditText() # Clear the text input
            self.product_combo.clear() # Clear the combo box items
            self.product_combo.setFocus()
            
            self.update_total()
            
        except Exception as e:
            show_error_message(self, "Error", f"Ocurrió un error al agregar el producto: {e}")
            self.product_combo.setFocus()

    @Slot()
    def update_total(self):
        total = Decimal("0.00")
        for item in self.sale_item_model.get_all_items():
            total += item.subtotal
        self.total_amount_label.setText(f"Total: $ {total:.2f}")
        self._current_total = total # Store current total for payment dialog

    @Slot()
    def remove_selected_item(self):
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_indexes: return
        model_index = selected_indexes[0]
        self.sale_item_model.remove_item(model_index.row())

    @Slot()
    def cancel_current_sale(self):
        if not self.sale_item_model.get_all_items():
            self._clear_sale()
            return
        if ask_confirmation(self, "Cancelar Venta", "¿Está seguro?"):
            self._clear_sale()

    def open_pdf_file(self, file_path):
        """Open a PDF file with the default system viewer."""
        try:
            if sys.platform == 'win32':  # Windows
                os.startfile(file_path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', file_path], check=True)
            else:  # Linux and other Unix-like
                subprocess.run(['xdg-open', file_path], check=True)
            return True
        except Exception as e:
            show_error_message(self, "Error al Abrir PDF", 
                              f"No se pudo abrir el archivo PDF: {e}")
            return False

    @Slot()
    def print_receipt(self, sale_id):
        """Generate and display a PDF receipt for the given sale ID."""
        try:
            # Create a receipts directory if it doesn't exist
            receipts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "receipts")
            os.makedirs(receipts_dir, exist_ok=True)
            
            # Generate receipt PDF using SaleService
            pdf_path = self.sale_service.generate_receipt_pdf(sale_id, receipts_dir)
            
            # Inform user that receipt has been generated
            show_info_message(self, "Recibo Generado", 
                            f"El recibo ha sido generado correctamente.\nUbicación: {pdf_path}")
            
            # Open the PDF with default viewer
            self.open_pdf_file(pdf_path)
            
        except Exception as e:
            show_error_message(self, "Error al Generar Recibo", 
                              f"No se pudo generar el recibo: {e}")

    @Slot()
    def finalize_current_sale(self):
        items = self.sale_item_model.get_all_items()
        if not items:
            show_error_message(self, "Finalizar Venta", "No hay artículos.")
            return

        customer_id = self._get_selected_customer_id()
        allow_credit = customer_id is not None # Allow credit only if a customer is selected

        # --- Payment Selection --- #
        payment_dialog = PaymentDialog(self._current_total, allow_credit, self)
        if not payment_dialog.exec():
            return # User cancelled payment selection

        payment_method = payment_dialog.selected_payment_method
        if not payment_method: # Should not happen if validation in dialog is correct, but check anyway
             show_error_message(self, "Error", "No se seleccionó un método de pago válido.")
             return

        is_credit = (payment_method == "Crédito")

        # Final confirmation message, including payment type
        confirmation_message = f"¿Finalizar venta por $ {self._current_total:.2f} con pago '{payment_method}'?"
        if customer_id and self.selected_customer:
            customer_name = self.selected_customer.name
            confirmation_message += f"\nCliente: {customer_name}"

        if not ask_confirmation(self, "Finalizar Venta", confirmation_message):
            return

        try:
            items_data = [
                {
                    'product_id': item.product_id,
                    'quantity': item.quantity,
                    # 'unit_price': item.unit_price # Service fetches price from DB
                } for item in items
            ]

            # Ensure user_id is passed
            if not self.current_user or self.current_user.id is None:
                 show_error_message(self, "Error de Usuario", "No se pudo identificar al usuario actual.")
                 return

            # Call SaleService with all required arguments
            created_sale = self.sale_service.create_sale(
                items_data=items_data,
                user_id=self.current_user.id,
                payment_type=payment_method, # Pass the selected method
                customer_id=customer_id,
                is_credit_sale=is_credit # Pass the flag derived from payment method
            )

            show_info_message(self, "Venta Finalizada", f"Venta #{created_sale.id} registrada exitosamente.")
            
            # Store sale ID before clearing
            sale_id = created_sale.id
            
            # Enable invoice button with the sale ID
            self.invoice_button.setEnabled(True)
            self.current_sale_id = sale_id
            
            # Clear the sale
            self._clear_sale()

            # Ask to print receipt
            if ask_confirmation(self, "Imprimir Recibo", "¿Desea imprimir el recibo?"):
                self.print_receipt(sale_id)

        except ValueError as ve: # Catch validation errors from service
            show_error_message(self, "Error de Validación", str(ve))
        except Exception as e:
            show_error_message(self, "Error al Finalizar", f"No se pudo registrar la venta: {e}")

    @Slot()
    def generate_invoice_from_sale(self):
        """Generate an invoice from the most recently completed sale."""
        if not hasattr(self, 'current_sale_id'):
            show_error_message(self, "No hay una venta reciente para facturar.")
            return
            
        try:
            # We need to check if the parent window has an invoicing_service
            main_window = self.window()
            if not hasattr(main_window, 'invoicing_service'):
                show_error_message(self, "No se puede acceder al servicio de facturación.")
                return
                
            # Check if the sale already has an invoice
            invoice = main_window.invoicing_service.get_invoice_by_sale_id(self.current_sale_id)
            if invoice:
                response = ask_confirmation(
                    self, 
                    f"Esta venta ya tiene una factura (Nro. {invoice.invoice_number}).\n"
                    f"¿Desea ver la factura existente?",
                    "Factura Existente"
                )
                if response:
                    # Generate and display the PDF
                    filename = main_window.invoicing_service.generate_invoice_pdf(invoice.id)
                    self.open_pdf_file(filename)
                return
                
            # Generate a new invoice for the sale
            invoice = main_window.invoicing_service.create_invoice_from_sale(self.current_sale_id)
            
            # Show success message
            show_info_message(self, "Factura Generada", f"Factura generada correctamente. Número: {invoice.invoice_number}")
            
            # Ask if user wants to view the invoice
            response = ask_confirmation(
                self, 
                "¿Desea ver la factura generada?",
                "Ver Factura"
            )
            if response:
                # Generate and display the PDF
                filename = main_window.invoicing_service.generate_invoice_pdf(invoice.id)
                self.open_pdf_file(filename)
                
        except Exception as e:
            show_error_message(self, "Error al Generar Factura", f"Error al generar la factura: {str(e)}")

    def _clear_sale(self):
        """Clears the sale items, total, and customer selection."""
        self.sale_item_model.clear()
        self.product_combo.clearEditText() # Clear the text part of QComboBox
        self.product_combo.clear()       # Clear the items in QComboBox
        self.selected_customer = None
        self.customer_label.setText("Cliente: Ninguno")
        self.product_combo.setFocus()
        self.invoice_button.setEnabled(False)  # Disable invoice button
        if hasattr(self, 'current_sale_id'):
            delattr(self, 'current_sale_id')
        # update_total is called automatically by modelReset signal
        
    def _edit_selected_item_quantity(self, index):
        """Edit the quantity of the selected sale item."""
        # This is a placeholder method that could be implemented in the future
        # For now, we'll just print a message to show it was called
        row = index.row()
        if row >= 0:
            item = self.sale_item_model.get_item_at_row(row)
            if item:
                print(f"Edit quantity for item {item.description} would be handled here")
