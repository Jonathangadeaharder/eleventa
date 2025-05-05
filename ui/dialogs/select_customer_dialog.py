from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QLineEdit, QLabel, QAbstractItemView, QHeaderView
)
from PySide6.QtCore import Qt, QModelIndex, QSortFilterProxyModel
from PySide6.QtGui import QStandardItemModel, QStandardItem

from typing import List, Optional
from core.models.customer import Customer

class SelectCustomerDialog(QDialog):
    """Dialog for selecting a customer from a list."""
    
    def __init__(self, customers: List[Customer], parent=None):
        super().__init__(parent)
        self.customers = customers
        self.selected_customer = None
        
        self.setWindowTitle("Seleccionar Cliente")
        self.setMinimumSize(600, 400)
        
        self.setup_ui()
        self.populate_customers()
        
    def setup_ui(self):
        """Set up the user interface."""
        main_layout = QVBoxLayout(self)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Buscar:"))
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Nombre, teléfono, email...")
        self.search_edit.textChanged.connect(self.filter_customers)
        search_layout.addWidget(self.search_edit)
        
        main_layout.addLayout(search_layout)
        
        # Customers table
        self.customer_table = QTableView()
        self.customer_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.customer_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.customer_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.customer_table.setAlternatingRowColors(True)
        self.customer_table.horizontalHeader().setStretchLastSection(True)
        self.customer_table.doubleClicked.connect(self.accept)
        
        # Set up model
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Nombre", "Teléfono", "Email", "Dirección", "Saldo"])
        
        # Set up proxy model for filtering
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        
        # Set model to table and ensure selection model is created
        self.customer_table.setModel(self.proxy_model)
        
        # Force selection model creation if needed
        if self.customer_table.selectionModel() is None:
            current_model = self.customer_table.model()
            self.customer_table.setModel(None)
            self.customer_table.setModel(current_model)
        
        main_layout.addWidget(self.customer_table)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        buttons_layout.addStretch()
        
        self.select_button = QPushButton("Seleccionar")
        self.select_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.select_button)
        
        main_layout.addLayout(buttons_layout)
        
        # Set focus on search
        self.search_edit.setFocus()
        
    def populate_customers(self):
        """Populate the table with customers."""
        self.model.setRowCount(0)  # Clear existing rows
        
        for customer in self.customers:
            name_item = QStandardItem(customer.name or "")
            phone_item = QStandardItem(customer.phone or "")
            email_item = QStandardItem(customer.email or "")
            address_item = QStandardItem(customer.address or "")
            balance_item = QStandardItem(f"${customer.credit_balance:.2f}" if customer.credit_balance else "$0.00")
            
            # Store the customer object in the name item's data
            name_item.setData(customer, Qt.UserRole)
            
            # Add row to model
            self.model.appendRow([name_item, phone_item, email_item, address_item, balance_item])
            
        # Adjust column widths
        self.customer_table.resizeColumnsToContents()
        
    def filter_customers(self):
        """Filter the customers based on search text."""
        search_text = self.search_edit.text()
        self.proxy_model.setFilterRegularExpression(search_text)
        
    def accept(self, index=None):
        """
        Handles dialog acceptance. If an index is provided (e.g., from double-click),
        selects the corresponding customer. Otherwise, uses the current selection.
        """
        selected_index = None
        # Get selection model safely
        selection_model = self.customer_table.selectionModel()

        # Proceed only if selection model exists
        if selection_model:
            if index and index.isValid():
                # Map proxy index to source index if needed (important!)
                source_index = self.proxy_model.mapToSource(index)
                selected_index = source_index
                # We don't strictly need to visually select here for the logic,
                # but if desired, ensure selection_model is valid first.
                # selection_model.select(index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
            else:
                # Check selectedRows only if selection_model is valid
                rows = selection_model.selectedRows()
                if rows:
                    # Map proxy index to source index
                    proxy_index = rows[0]
                    source_index = self.proxy_model.mapToSource(proxy_index)
                    selected_index = source_index

        # Check if a valid source index was determined
        if selected_index and selected_index.isValid():
            item = self.model.itemFromIndex(selected_index)
            if item:
                self.selected_customer = item.data(Qt.UserRole)
                # Call base accept ONLY if a customer is successfully selected
                super().accept()
            else:
                # Handle case where index is valid but no item found (shouldn't happen ideally)
                self.selected_customer = None
                # Consider logging this unexpected state
        else:
            # No valid selection (or selection model was None), do not accept the dialog
            self.selected_customer = None
            # Optionally provide user feedback here if desired (e.g., QMessageBox)
        
    def get_selected_customer(self) -> Optional[Customer]:
        """Return the selected customer or None if none was selected."""
        return self.selected_customer
