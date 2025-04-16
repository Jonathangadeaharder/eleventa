import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QTableView, QMessageBox, QAbstractItemView, QHeaderView
)
from PySide6.QtCore import Qt, Slot # Import Slot
from PySide6.QtGui import QKeySequence, QShortcut # For shortcuts

# Assuming Table Model, Dialog, and Service are available
from ..models.table_models import CustomerTableModel
from ..dialogs.customer_dialog import CustomerDialog
from ..dialogs.register_payment_dialog import RegisterPaymentDialog # Added payment dialog
from core.services.customer_service import CustomerService
# Import utility functions
from ..utils import show_error_message, ask_confirmation, show_info_message # Added show_info_message

class CustomersView(QWidget):
    """View for managing customers."""

    def __init__(self, customer_service: CustomerService, parent=None):
        super().__init__(parent)
        self._customer_service = customer_service

        self.setWindowTitle("Clientes")

        # --- Widgets ---
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Buscar por nombre...")
        self.refresh_button = QPushButton("Refrescar") # Added Refresh
        self.add_button = QPushButton("&Nuevo Cliente (F5)") # Added shortcut hint
        self.modify_button = QPushButton("&Modificar Cliente (F6)") # Added shortcut hint
        self.delete_button = QPushButton("&Eliminar Cliente (Supr)") # Added shortcut hint
        self.register_payment_button = QPushButton("Registrar &Pago") # Renombrado para coincidir con el test
        self.edit_button = QPushButton("Editar")

        self.table_view = QTableView()
        self.table_model = CustomerTableModel(self)
        self.table_view.setModel(self.table_model)

        # Table View Setup
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_view.setSortingEnabled(True) # Enable sorting by clicking headers
        # Resize columns to contents initially
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        # Allow Description to stretch
        # self.table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)


        # --- Layout ---
        toolbar_layout = QHBoxLayout()
        toolbar_layout.addWidget(self.search_edit)
        toolbar_layout.addWidget(self.refresh_button)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.add_button)
        toolbar_layout.addWidget(self.modify_button)
        toolbar_layout.addWidget(self.delete_button)
        toolbar_layout.addWidget(self.register_payment_button)
        toolbar_layout.addWidget(self.edit_button)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(toolbar_layout)
        main_layout.addWidget(self.table_view)

        # --- Connections ---
        self.refresh_button.clicked.connect(self.refresh_customers)
        self.search_edit.textChanged.connect(self.filter_customers)
        self.add_button.clicked.connect(self.add_new_customer)
        self.modify_button.clicked.connect(self.modify_selected_customer)
        self.delete_button.clicked.connect(self.delete_selected_customer)
        self.register_payment_button.clicked.connect(self.register_payment) # Conectar el botón renombrado
        self.table_view.doubleClicked.connect(self.modify_selected_customer)

        # --- Shortcuts ---
        QShortcut(QKeySequence(Qt.Key.Key_F5), self, self.add_new_customer)
        QShortcut(QKeySequence(Qt.Key.Key_F6), self, self.modify_selected_customer)
        QShortcut(QKeySequence(Qt.Key.Key_Delete), self, self.delete_selected_customer)
        QShortcut(QKeySequence(Qt.Key.Key_F12), self, self.refresh_customers) # Example: F12 to refresh
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self.search_edit, self.search_edit.clear) # Esc clears search
        QShortcut(QKeySequence(Qt.Key.Key_F7), self, self.register_payment) # Consider adding a shortcut for payment, e.g., F7

        # --- Initial Data Load ---
        self.refresh_customers()

    @Slot()
    def refresh_customers(self):
        """Fetches all customers and updates the table."""
        try:
            search_term = self.search_edit.text().strip()
            if search_term:
                customers = self._customer_service.find_customer(search_term)
            else:
                customers = self._customer_service.get_all_customers()
            self.table_model.update_data(customers)
            # Resize columns after data load
            self.table_view.resizeColumnsToContents()
            # self.table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        except Exception as e:
            show_error_message(self, "Error al Cargar Clientes", f"No se pudieron cargar los clientes: {e}")

    @Slot()
    def filter_customers(self):
        """Filters customers based on the search term (triggers refresh)."""
        self.refresh_customers() # Re-uses refresh logic which now includes search

    @Slot()
    def add_new_customer(self):
        """Opens the dialog to add a new customer."""
        dialog = CustomerDialog(self._customer_service, parent=self)
        if dialog.exec():
            self.refresh_customers() # Refresh list after adding

    def _get_selected_customer(self):
        """Helper to get the selected customer object from the table."""
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            return None
        # Use the model's method to get the underlying data object
        model_index = selected_indexes[0] # We use SingleSelection
        customer = self.table_model.get_customer_at_row(model_index.row())
        return customer

    @Slot()
    def modify_selected_customer(self):
        """Opens the dialog to modify the selected customer."""
        selected_customer = self._get_selected_customer()
        if not selected_customer:
            show_error_message(self, "Selección Requerida", "Por favor, seleccione un cliente para modificar.")
            return

        dialog = CustomerDialog(self._customer_service, customer=selected_customer, parent=self)
        if dialog.exec():
            self.refresh_customers() # Refresh list after modification

    @Slot()
    def delete_selected_customer(self):
        """Deletes the selected customer after confirmation."""
        selected_customer = self._get_selected_customer()
        if not selected_customer:
            show_error_message(self, "Selección Requerida", "Por favor, seleccione un cliente para eliminar.")
            return

        if ask_confirmation(self, "Confirmar Eliminación", f"¿Está seguro de que desea eliminar al cliente '{selected_customer.name}'?"):
            try:
                deleted = self._customer_service.delete_customer(selected_customer.id)
                if deleted:
                    self.refresh_customers() # Refresh list after deleting
                else:
                    # This case might not happen if service raises error on failure
                    show_error_message(self, "Error al Eliminar", "No se pudo eliminar el cliente.")
            except ValueError as e: # Catch specific service validation errors
                 show_error_message(self, "Error al Eliminar", str(e))
            except Exception as e:
                show_error_message(self, "Error al Eliminar", f"Ocurrió un error inesperado: {e}")

    # --- New Slot for Payment --- #
    @Slot()
    def register_payment(self):
        """Opens a dialog to register a payment for the selected customer."""
        selected_customer = self._get_selected_customer()
        if not selected_customer:
            show_error_message(self, "Selección Requerida", "Por favor, seleccione un cliente para registrar un pago.")
            return

        # Open the payment dialog
        dialog = RegisterPaymentDialog(selected_customer, parent=self)
        if dialog.exec():
            # Dialog was accepted, get amount and notes
            amount = dialog.payment_amount
            notes = dialog.payment_notes
            # user_id = ... # Get current user ID if implementing users

            try:
                # Call the customer service to apply the payment
                payment_log = self._customer_service.apply_payment(
                    customer_id=selected_customer.id,
                    amount=amount,
                    notes=notes
                    # user_id=user_id
                )
                show_info_message(self, "Pago Registrado", f"Pago de $ {amount:.2f} registrado para {selected_customer.name}.")
                self.refresh_customers() # Refresh the view to show updated balance
            except ValueError as ve:
                show_error_message(self, "Error al Registrar Pago", str(ve))
            except Exception as e:
                show_error_message(self, "Error Inesperado", f"Ocurrió un error al registrar el pago: {e}")
                print(f"Unexpected error during payment registration: {e}")

# Example Usage (for testing if run directly)
if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    from core.models.customer import Customer # Need Customer for mock
    from decimal import Decimal # Added Decimal for mock

    # Mock CustomerService for standalone testing
    class MockCustomerService:
        _customers = [
            Customer(id=1, name="Alice Wonderland", phone="111", email="alice@wonder.land", address="Tea Party Lane", credit_limit=100, credit_balance=10),
            Customer(id=2, name="Bob The Builder", phone="222", email="bob@build.it", address="Fixit Ave", credit_limit=500, credit_balance=-50),
            Customer(id=3, name="Charlie Chaplin", phone="333", email=None, address="Silent Street", credit_limit=0, credit_balance=0),
        ]
        def get_all_customers(self): print("Mock: get_all"); return self._customers
        def find_customer(self, term): print(f"Mock: find '{term}'"); return [c for c in self._customers if term.lower() in (c.name or "").lower()]
        def add_customer(self, **kwargs): print(f"Mock: add {kwargs}"); new_id = max(c.id for c in self._customers) + 1; new_c = Customer(id=new_id, **kwargs); self._customers.append(new_c); return new_c
        def update_customer(self, customer_id, **kwargs): print(f"Mock: update {customer_id} with {kwargs}"); cust = self.get_customer_by_id(customer_id); cust.name=kwargs['name']; cust.phone=kwargs['phone']; cust.email=kwargs['email']; cust.address=kwargs['address']; cust.credit_limit=kwargs['credit_limit']; return cust
        def delete_customer(self, customer_id):
            print(f"Mock: delete {customer_id}")
            cust = self.get_customer_by_id(customer_id)
            if cust and cust.credit_balance is not None and Decimal(str(cust.credit_balance)) > Decimal('0.01'):
                # Compare as Decimal to avoid potential float issues
                raise ValueError(f"Cannot delete customer {cust.name} with balance {cust.credit_balance:.2f}")
            # Filter out the customer to be deleted
            self._customers = [c for c in self._customers if c.id != customer_id]
            return True # Indicate success
        def get_customer_by_id(self, id): return next((c for c in self._customers if c.id == id), None)
        def apply_payment(self, customer_id, amount, notes=None, user_id=None):
            print(f"Mock: apply payment for {customer_id}, Amount: {amount}, Notes: {notes}")
            cust = self.get_customer_by_id(customer_id)
            if cust:
                cust.credit_balance += float(amount) # Simulate payment decreasing debt
            # Return a dummy CreditPayment object if needed
            from core.models.credit import CreditPayment
            return CreditPayment(id=999, customer_id=customer_id, amount=amount)

    app = QApplication(sys.argv)
    service = MockCustomerService()
    view = CustomersView(service)
    view.show()
    app.exec() # Start the event loop directly 