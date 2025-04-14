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
        self.customer_table.setModel(self.proxy_model)
        
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
        
    def accept(self):
        """Handle dialog acceptance."""
        # Get the selected customer
        selected_rows = self.customer_table.selectionModel().selectedRows()
        if selected_rows:
            # Get the model index from the proxy model
            proxy_index = selected_rows[0]
            # Map it to the source model
            source_index = self.proxy_model.mapToSource(proxy_index)
            # Get the item from the source model
            name_item = self.model.item(source_index.row(), 0)
            # Get the customer object from the item's data
            self.selected_customer = name_item.data(Qt.UserRole)
            
        super().accept()
        
    def get_selected_customer(self) -> Optional[Customer]:
        """Return the selected customer or None if none was selected."""
        return self.selected_customer 