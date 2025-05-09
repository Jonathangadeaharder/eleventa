from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton,
    QLineEdit, QLabel, QMessageBox, QFileDialog, QMenu, QComboBox
)
from PySide6.QtCore import Qt, QModelIndex, QPoint
from PySide6.QtGui import QAction
import os
import subprocess
import platform

from ui.models.table_models import InvoiceTableModel
from ui.utils import show_error_message, show_info_message, ask_confirmation
from core.services.invoicing_service import InvoicingService

class InvoicesView(QWidget):
    """View for displaying and managing invoices."""
    
    def __init__(self, invoicing_service: InvoicingService, parent=None):
        super().__init__(parent)
        self.invoicing_service = invoicing_service
        self.setup_ui()
        self.refresh_invoices()

    def setup_ui(self):
        """Set up the user interface."""
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Header section with title and search
        header_layout = QHBoxLayout()
        title_label = QLabel("Facturas")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Add search field
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Buscar:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Nro. de factura, cliente...")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self.filter_invoices)
        search_layout.addWidget(self.search_edit)
        header_layout.addLayout(search_layout)
        
        main_layout.addLayout(header_layout)
        
        # Filter options
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Tipo:"))
        self.type_filter = QComboBox()
        self.type_filter.addItems(["Todas", "Tipo A", "Tipo B", "Tipo C"])
        self.type_filter.currentIndexChanged.connect(self.refresh_invoices)
        filter_layout.addWidget(self.type_filter)
        
        filter_layout.addSpacing(20)
        
        filter_layout.addWidget(QLabel("Estado:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Todas", "Activas", "Anuladas"])
        self.status_filter.currentIndexChanged.connect(self.refresh_invoices)
        filter_layout.addWidget(self.status_filter)
        
        filter_layout.addStretch()
        
        # Refresh button
        self.refresh_button = QPushButton("Actualizar")
        self.refresh_button.clicked.connect(self.refresh_invoices)
        filter_layout.addWidget(self.refresh_button)
        
        main_layout.addLayout(filter_layout)
        
        # Invoice table
        self.invoice_table = QTableView()
        self.invoice_table.setSelectionBehavior(QTableView.SelectRows)
        self.invoice_table.setSelectionMode(QTableView.SingleSelection)
        self.invoice_table.horizontalHeader().setStretchLastSection(True)
        self.invoice_table.setAlternatingRowColors(True)
        self.invoice_table.setSortingEnabled(True)
        
        # Create and set model
        self.invoice_model = InvoiceTableModel()
        self.invoice_table.setModel(self.invoice_model)
        
        # Enable context menu
        self.invoice_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.invoice_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Connect double click to view invoice
        self.invoice_table.doubleClicked.connect(self.view_invoice)
        
        main_layout.addWidget(self.invoice_table)
        
        # Buttons section
        buttons_layout = QHBoxLayout()
        
        self.view_button = QPushButton("Ver Factura")
        self.view_button.clicked.connect(self.view_invoice)
        buttons_layout.addWidget(self.view_button)
        
        self.print_button = QPushButton("Imprimir")
        self.print_button.clicked.connect(self.print_invoice)
        buttons_layout.addWidget(self.print_button)
        
        buttons_layout.addStretch()
        
        self.generate_button = QPushButton("Generar Factura")
        self.generate_button.clicked.connect(self.generate_invoice)
        buttons_layout.addWidget(self.generate_button)
        
        main_layout.addLayout(buttons_layout)

    def refresh_invoices(self):
        """Refresh the invoice list from the service."""
        try:
            # Get all invoices
            invoices = self.invoicing_service.get_all_invoices()
            
            # Apply filters
            if self.type_filter.currentIndex() > 0:
                invoice_type = self.type_filter.currentText().replace("Tipo ", "")
                invoices = [inv for inv in invoices if inv.invoice_type == invoice_type]
                
            if self.status_filter.currentIndex() == 1:  # Active
                invoices = [inv for inv in invoices if inv.is_active]
            elif self.status_filter.currentIndex() == 2:  # Canceled
                invoices = [inv for inv in invoices if not inv.is_active]
            
            # Update the model
            self.invoice_model.update_data(invoices)
            
            # Resize columns for better visibility
            self.invoice_table.resizeColumnsToContents()
            
        except Exception as e:
            show_error_message(self, "Error", f"Error al cargar facturas: {str(e)}")

    def filter_invoices(self):
        """Filter invoices based on search text."""
        # This is a simple client-side filter
        # In a real app with many invoices, this would be done server-side
        search_text = self.search_edit.text().lower()
        if not search_text:
            self.refresh_invoices()  # Reset to full list
            return
            
        try:
            # Get all invoices that match the search text
            invoices = self.invoicing_service.get_all_invoices()
            filtered_invoices = []
            
            for invoice in invoices:
                # Check invoice number
                if invoice.invoice_number and search_text in invoice.invoice_number.lower():
                    filtered_invoices.append(invoice)
                    continue
                    
                # Check customer name
                if (invoice.customer_details and 'name' in invoice.customer_details and 
                    search_text in invoice.customer_details['name'].lower()):
                    filtered_invoices.append(invoice)
                    continue
                    
                # Could add more fields to search here
                
            # Update the model with filtered results
            self.invoice_model.update_data(filtered_invoices)
            
        except Exception as e:
            show_error_message(self, "Error", f"Error al filtrar facturas: {str(e)}")

    def get_selected_invoice_id(self):
        """Get the ID of the currently selected invoice."""
        selected_rows = self.invoice_table.selectionModel().selectedRows()
        if not selected_rows:
            return None
            
        row_index = selected_rows[0].row()
        return self.invoice_model.invoices[row_index].id

    def view_invoice(self):
        """View the selected invoice as PDF."""
        invoice_id = self.get_selected_invoice_id()
        if invoice_id is None:
            show_error_message(self, "Selección Requerida", "Por favor seleccione una factura para ver.")
            return
            
        try:
            # Generate the PDF and get the filename
            filename = self.invoicing_service.generate_invoice_pdf(invoice_id)
            
            # Open the PDF with default viewer
            if os.path.exists(filename):
                self.open_file_with_default_app(filename)
            else:
                show_error_message(self, "Error", f"El archivo de factura no existe: {filename}")
                
        except Exception as e:
            show_error_message(self, "Error", f"Error al generar el PDF de la factura: {str(e)}")

    def print_invoice(self):
        """Print the selected invoice."""
        invoice_id = self.get_selected_invoice_id()
        if invoice_id is None:
            show_error_message(self, "Selección Requerida", "Por favor seleccione una factura para imprimir.")
            return
            
        try:
            # Generate the PDF
            filename = self.invoicing_service.generate_invoice_pdf(invoice_id)
            
            # Inform the user to print from the opened application
            show_info_message(self, "Factura Generada", 
                f"El archivo de factura se ha generado correctamente.\n\n"
                f"Se abrirá ahora para que pueda imprimirlo desde su visor de PDF."
            )
            
            # Open the PDF with default viewer
            if os.path.exists(filename):
                self.open_file_with_default_app(filename)
            else:
                show_error_message(self, "Error", f"El archivo de factura no existe: {filename}")
                
        except Exception as e:
            show_error_message(self, "Error", f"Error al generar el PDF para impresión: {str(e)}")

    def generate_invoice(self):
        """Show dialog to generate a new invoice from a sale."""
        from ui.dialogs.generate_invoice_dialog import GenerateInvoiceDialog
        dialog = GenerateInvoiceDialog(self.invoicing_service, self)
        if dialog.exec():
            # Refresh the invoice list if an invoice was generated
            self.refresh_invoices()
            show_info_message(self, "Éxito", "Factura generada correctamente.")

    def show_context_menu(self, position: QPoint):
        """Show context menu for invoice table."""
        menu = QMenu()
        
        view_action = menu.addAction("Ver Factura")
        print_action = menu.addAction("Imprimir")
        menu.addSeparator()
        save_pdf_action = menu.addAction("Guardar PDF...")
        
        # Add cancel invoice option if we have an active invoice selected
        cancel_action = None
        row = self.invoice_table.rowAt(position.y())
        if row >= 0 and row < len(self.invoice_model.invoices):
            invoice = self.invoice_model.invoices[row]
            if invoice.is_active:
                menu.addSeparator()
                cancel_action = menu.addAction("Anular Factura")
        
        # Show menu and handle action
        action = menu.exec(self.invoice_table.viewport().mapToGlobal(position))
        
        if action == view_action:
            self.view_invoice()
        elif action == print_action:
            self.print_invoice()
        elif action == save_pdf_action:
            self.save_invoice_pdf()
        elif cancel_action is not None and action == cancel_action:
            self.cancel_invoice(row)

    def save_invoice_pdf(self):
        """Save the selected invoice as PDF to a user-specified location."""
        invoice_id = self.get_selected_invoice_id()
        if invoice_id is None:
            show_error_message(self, "Selección Requerida", "Por favor seleccione una factura para guardar como PDF.")
            return
            
        try:
            # Get invoice details to suggest a filename
            invoice = self.invoicing_service.get_invoice_by_id(invoice_id)
            if not invoice:
                show_error_message(self, "Error", "No se pudo encontrar la factura seleccionada.")
                return
                
            # Show file save dialog
            suggested_name = f"Factura_{invoice.invoice_number.replace('-', '_')}.pdf"
            filename, _ = QFileDialog.getSaveFileName(
                self, 
                "Guardar Factura como PDF",
                suggested_name,
                "Archivos PDF (*.pdf)"
            )
            
            if not filename:  # User canceled
                return
                
            # Generate the PDF at the specified location
            self.invoicing_service.generate_invoice_pdf(invoice_id, filename=filename)
            
            show_info_message(self, "Éxito", f"La factura se ha guardado como {filename}")
                
        except Exception as e:
            show_error_message(self, "Error", f"Error al guardar el PDF de la factura: {str(e)}")

    def cancel_invoice(self, row):
        """Cancel the selected invoice."""
        # This would require implementation in the service layer
        # For now just show a message
        show_info_message(self, "No Implementado", "La funcionalidad para anular facturas no está implementada aún.")

    def open_file_with_default_app(self, filename):
        """Open a file with the default application."""
        try:
            system = platform.system()
            if system == 'Windows':
                os.startfile(os.path.abspath(filename))
            elif system == 'Darwin':  # macOS
                subprocess.call(['open', filename])
            else:  # Linux and others
                subprocess.call(['xdg-open', filename])
        except Exception as e:
            show_error_message(self, "Error", f"Error al abrir el archivo: {str(e)}")