from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableView, QFormLayout, QLineEdit, QMessageBox, QHeaderView,
    QGroupBox, QFrame, QSplitter, QTextEdit
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont, QColor
from decimal import Decimal
import locale
from datetime import datetime
from infrastructure.reporting.receipt_builder import format_currency

# Import the print manager
from infrastructure.reporting.print_utility import print_manager as default_print_manager, PrintType, PrintDestination

from core.services.cash_drawer_service import CashDrawerService
from core.models.cash_drawer import CashDrawerEntry, CashDrawerEntryType
from ui.models.table_models import CashDrawerTableModel
from ui.dialogs.cash_drawer_dialogs import OpenDrawerDialog, CashMovementDialog

# Utility function to parse currency input

def parse_currency_input(value: str) -> Decimal:
    """Parse a currency string (with optional commas) to Decimal."""
    value = value.replace(",", "").strip()
    if not value:
        raise ValueError("Empty input")
    try:
        return Decimal(value).quantize(Decimal('0.01'))
    except Exception:
        raise ValueError(f"Invalid currency input: {value}")

# Utility function to calculate cash difference

def calculate_difference(expected: Decimal, actual: Decimal) -> Decimal:
    """Calculate the difference between expected and actual cash amounts."""
    return (expected - actual).quantize(Decimal('0.01'))

class CashDrawerView(QWidget):
    """View for managing cash drawer operations."""
    
    def __init__(self, cash_drawer_service: CashDrawerService, user_id: int, parent=None, print_manager=None):
        super().__init__(parent)
        self.service = cash_drawer_service
        self.user_id = user_id
        self.current_drawer_id = None
        self.print_manager = print_manager or default_print_manager
        self._init_ui()
        self._connect_signals()
        self._refresh_data()
        
    def _init_ui(self):
        """Initialize the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Status section
        status_group = QGroupBox("Estado de Caja")
        status_layout = QFormLayout()
        
        self.status_label = QLabel("Cerrada")
        status_font = QFont()
        status_font.setBold(True)
        status_font.setPointSize(12)
        self.status_label.setFont(status_font)
        
        self.balance_label = QLabel("$ 0.00")
        balance_font = QFont()
        balance_font.setBold(True)
        balance_font.setPointSize(14)
        self.balance_label.setFont(balance_font)
        
        self.open_time_label = QLabel("-")
        self.open_user_label = QLabel("-")
        
        # Add fields to status layout
        status_layout.addRow("Estado:", self.status_label)
        status_layout.addRow("Saldo Actual:", self.balance_label)
        status_layout.addRow("Hora Apertura:", self.open_time_label)
        status_layout.addRow("Abierta por:", self.open_user_label)
        
        status_group.setLayout(status_layout)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        
        self.open_button = QPushButton("Abrir Caja")
        self.add_cash_button = QPushButton("Agregar Efectivo")
        self.remove_cash_button = QPushButton("Retirar Efectivo")
        self.print_report_button = QPushButton("Imprimir Reporte")
        
        # Initially disable buttons that require an open drawer
        self.add_cash_button.setEnabled(False)
        self.remove_cash_button.setEnabled(False)
        self.print_report_button.setEnabled(False)
        
        actions_layout.addWidget(self.open_button)
        actions_layout.addWidget(self.add_cash_button)
        actions_layout.addWidget(self.remove_cash_button)
        actions_layout.addWidget(self.print_report_button)
        
        # Table for cash drawer entries
        table_label = QLabel("Movimientos de Caja:")
        self.entries_table = QTableView()
        self.entries_table.setSelectionBehavior(QTableView.SelectRows)
        self.entries_table.setSelectionMode(QTableView.SingleSelection)
        self.entries_table.setAlternatingRowColors(True)
        
        self.table_model = CashDrawerTableModel()
        self.entries_table.setModel(self.table_model)
        
        # Adjust table column widths
        self.entries_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        self.entries_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Timestamp
        self.entries_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Type
        self.entries_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Amount
        self.entries_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)  # Description
        self.entries_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)  # User
        
        # Summary section
        summary_group = QGroupBox("Resumen del Día")
        summary_layout = QFormLayout()
        
        self.total_in_label = QLabel("$ 0.00")
        self.total_out_label = QLabel("$ 0.00")
        self.initial_amount_label = QLabel("$ 0.00")
        self.expected_balance_label = QLabel("$ 0.00")
        self.actual_balance_label = QLabel("$ 0.00")
        self.difference_label = QLabel("$ 0.00")
        
        summary_layout.addRow("Monto Inicial:", self.initial_amount_label)
        summary_layout.addRow("Total Ingresos:", self.total_in_label)
        summary_layout.addRow("Total Retiros:", self.total_out_label)
        summary_layout.addRow("Saldo Esperado:", self.expected_balance_label)
        summary_layout.addRow("Saldo Actual:", self.actual_balance_label)
        summary_layout.addRow("Diferencia:", self.difference_label)
        
        summary_group.setLayout(summary_layout)
        
        # Add all components to main layout
        main_layout.addWidget(status_group)
        main_layout.addLayout(actions_layout)
        main_layout.addWidget(table_label)
        main_layout.addWidget(self.entries_table)
        main_layout.addWidget(summary_group)
        
    def _connect_signals(self):
        """Connect signals to slots."""
        self.open_button.clicked.connect(self._handle_open_drawer)
        self.add_cash_button.clicked.connect(self._handle_add_cash)
        self.remove_cash_button.clicked.connect(self._handle_remove_cash)
        self.print_report_button.clicked.connect(self._print_report)
        
    def _refresh_data(self):
        """Refresh all data displayed in the view."""
        # Get drawer summary
        summary = self.service.get_drawer_summary(self.current_drawer_id)
        
        # Update status section
        is_open = summary.get('is_open', False)
        self.status_label.setText("Abierta" if is_open else "Cerrada")
        self.status_label.setStyleSheet("color: green" if is_open else "color: red")
        
        # Update balance
        current_balance = summary.get('current_balance', Decimal('0.00'))
        # Use f-string formatting for currency, ensure 2 decimal places
        self.balance_label.setText(f"${current_balance:,.2f}")
        
        # Update open info if available
        if is_open:
            opened_at = summary.get('opened_at')
            opened_by = summary.get('opened_by')
            
            if opened_at:
                self.open_time_label.setText(opened_at.strftime("%d/%m/%Y %H:%M"))
            
            if opened_by:
                # In a real app, you might want to fetch the user name from a user service
                self.open_user_label.setText(str(opened_by))
                
            # Enable buttons that require an open drawer
            self.add_cash_button.setEnabled(True)
            self.remove_cash_button.setEnabled(True)
            self.print_report_button.setEnabled(True)
            
            # Change open button text to "Close Drawer" functionality
            self.open_button.setText("Cerrar Caja")
        else:
            self.open_time_label.setText("-")
            self.open_user_label.setText("-")
            
            # Disable buttons that require an open drawer
            self.add_cash_button.setEnabled(False)
            self.remove_cash_button.setEnabled(False)
            self.print_report_button.setEnabled(False)
            
            # Change button text back to "Open Drawer"
            self.open_button.setText("Abrir Caja")
            
        # Update table with entries
        raw_entries = summary.get('entries_today', [])
        # Pre-format amounts to strings before passing to the model
        formatted_entries = []
        for entry in raw_entries:
            # Create a copy or convert Pydantic model to dict if needed
            if hasattr(entry, 'dict'):
                # For Pydantic models (v1)
                formatted_entry = entry.dict()
            elif hasattr(entry, 'model_dump'):
                # For Pydantic models (v2)
                formatted_entry = entry.model_dump()
            else:
                # For dictionary entries
                formatted_entry = entry.copy()
                
            # Handle amount differently based on type
            if isinstance(entry, dict):
                amount = entry.get('amount', Decimal('0.00'))
            else:
                # For Pydantic model
                amount = getattr(entry, 'amount', Decimal('0.00'))
                
            # Store the formatted string directly
            formatted_entry['amount'] = f"${amount:,.2f}" 
            formatted_entries.append(formatted_entry)
            
        self.table_model.update_entries(formatted_entries)
        
        # Update summary section
        initial_amount = summary.get('initial_amount', Decimal('0.00'))
        total_in = summary.get('total_in', Decimal('0.00'))
        total_out = summary.get('total_out', Decimal('0.00'))
        
        # Use f-string formatting for currency
        self.initial_amount_label.setText(f"${initial_amount:,.2f}")
        self.total_in_label.setText(f"${total_in:,.2f}")
        self.total_out_label.setText(f"${total_out:,.2f}")
        
        # Calculate expected balance and difference (would normally be done in the service)
        expected_balance = initial_amount + total_in - total_out
        difference = current_balance - expected_balance
        
        # Use f-string formatting for currency
        self.expected_balance_label.setText(f"${expected_balance:,.2f}")
        self.actual_balance_label.setText(f"${current_balance:,.2f}") # Reuse formatted current_balance
        self.difference_label.setText(f"${difference:,.2f}")
        
        # Style the difference label based on value
        if difference == 0:
            self.difference_label.setStyleSheet("color: black")
        elif difference < 0:
            self.difference_label.setStyleSheet("color: red")
        else:
            self.difference_label.setStyleSheet("color: blue")
            
    def _handle_open_drawer(self):
        """Handle opening or closing the cash drawer."""
        print("_handle_open_drawer called")
        summary = self.service.get_drawer_summary(self.current_drawer_id)
        is_open = summary.get('is_open', False)
        
        if is_open:
            # Drawer is open, ask if user wants to close it
            # For now, just show message - in real app would implement proper closing flow
            print("Drawer is open, showing information message")
            QMessageBox.information(
                self, 
                "Cierre de Caja", 
                "El cierre de caja no está implementado en esta versión.\n"
                "Por favor, implemente la lógica de cierre de caja según sus requisitos."
            )
        else:
            # Drawer is closed, open it
            # Use the correct dialog class name (alias) and parent
            print("Drawer is closed, opening dialog")
            dialog = OpenDrawerDialog(self.service, self.user_id, self)
            if dialog.exec():
                print("Dialog executed successfully")
                # The dialog now handles the service call and message boxes internally
                # We just need to refresh the view if it succeeded
                if dialog.entry: # Check if the dialog successfully created an entry
                    print("Dialog entry created, refreshing data")
                    self._refresh_data()
                # No need for try/except here as the dialog handles its own errors
            else:
                print("Dialog execution failed")
                    
    def _handle_add_cash(self):
        """Handle adding cash to the drawer."""
        # Check if drawer is open first
        summary = self.service.get_drawer_summary(self.current_drawer_id)
        if not summary.get('is_open', False):
            QMessageBox.warning(self, "Error", "La caja debe estar abierta para agregar efectivo.")
            return

        # Use the correct dialog class name (alias), pass service/user_id, and parent
        dialog = CashMovementDialog(self.service, self.user_id, is_adding=True, parent=self)
        if dialog.exec():
            # The dialog now handles the service call and message boxes internally
            # We just need to refresh the view if it succeeded
            if dialog.entry: # Check if the dialog successfully created an entry
                self._refresh_data()
                
    def _handle_remove_cash(self):
        """Handle removing cash from the drawer."""
        # Check if drawer is open first
        summary = self.service.get_drawer_summary(self.current_drawer_id)
        if not summary.get('is_open', False):
            QMessageBox.warning(self, "Error", "La caja debe estar abierta para retirar efectivo.")
            return

        # Use the correct dialog class name (alias), pass service/user_id, and parent
        dialog = CashMovementDialog(self.service, self.user_id, is_adding=False, parent=self)
        if dialog.exec():
             # The dialog now handles the service call and message boxes internally
             # We just need to refresh the view if it succeeded
            if dialog.entry: # Check if the dialog successfully created an entry
                self._refresh_data()
                
    def _print_report(self):
        """Print a cash drawer report."""
        # Get the current drawer data
        drawer_summary = self.service.get_drawer_summary(self.current_drawer_id)
        
        # Check if drawer is open
        if not drawer_summary.get('is_open', False):
            QMessageBox.warning(self, "Error", "La caja debe estar abierta para imprimir el reporte.")
            return
            
        try:
            # Prepare the data for printing
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            
            print_data = {
                'title': 'Reporte de Caja',
                'drawer_id': self.current_drawer_id,
                'drawer_data': drawer_summary,
                'timestamp': timestamp
            }
            
            # Use the print manager to generate and open the PDF
            result = self.print_manager.print(
                print_type=PrintType.CASH_DRAWER,
                data=print_data,
                destination=PrintDestination.PREVIEW  # Open in PDF viewer
            )
            
            if not result:
                QMessageBox.warning(self, "Error", "Ocurrió un error al generar el reporte.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al imprimir el reporte: {str(e)}")

# Re-export utility functions
__all__ = [
    'parse_currency_input',
    'calculate_difference',
    'CashDrawerView'
]
