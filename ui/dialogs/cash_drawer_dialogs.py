from PySide6.QtWidgets import (
    QApplication, QDialog, QWidget,
    QVBoxLayout, QHBoxLayout, QGridLayout, QStackedLayout, QFormLayout,
    QDialogButtonBox,
    QLabel, QLineEdit, QPushButton,
    QComboBox, QCheckBox, QRadioButton,
    QSlider, QSpinBox, QDoubleSpinBox,
    QTextEdit, QPlainTextEdit,
    QProgressBar, QTableView, QTableWidget,
    QTreeView, QTreeWidget,
    QListView, QListWidget,
    QScrollArea, QDockWidget, QToolBar, QStatusBar,
    QCalendarWidget, QGraphicsView, QMainWindow,
    QDateEdit, QTimeEdit, QDateTimeEdit, QTabWidget,
    QGroupBox, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt, QDate, Slot as pyqtSlot
from PySide6.QtGui import QFont

from decimal import Decimal
import locale
from datetime import date, timedelta

from core.models.cash_drawer import CashDrawerEntry
from core.services.cash_drawer_service import CashDrawerService
from ui.models.cash_drawer_model import CashDrawerTableModel

# Configure locale for currency formatting
locale.setlocale(locale.LC_ALL, '')


class OpenCashDrawerDialog(QDialog):
    """Dialog for opening a cash drawer with an initial amount."""
    
    def __init__(self, cash_drawer_service: CashDrawerService, user_id: int, parent=None):
        try:
            super().__init__(parent)
            self.cash_drawer_service = cash_drawer_service
            self.user_id = user_id
            self.entry = None  # Will store the created entry
            
            self.initial_amount_field = None
            self.description_field = None
            
            self.init_ui()
        except Exception as e:
            print(f"Error initializing OpenCashDrawerDialog: {str(e)}")
        
    def init_ui(self):
        """Initialize the UI."""
        try:
            self.setWindowTitle("Abrir Caja")
            self.setMinimumWidth(350)
            
            # Create layouts
            main_layout = QVBoxLayout(self)
            form_layout = QFormLayout()
            
            # Create widgets
            self.initial_amount_field = QDoubleSpinBox()
            self.initial_amount_field.setRange(0, 1000000)
            self.initial_amount_field.setDecimals(2)
            self.initial_amount_field.setSingleStep(100)
            self.initial_amount_field.setPrefix("$ ")
            
            self.description_field = QPlainTextEdit()
            self.description_field.setPlaceholderText("Descripción (opcional)")
            self.description_field.setMaximumHeight(80)
            
            # Add widgets to form layout
            form_layout.addRow("Monto Inicial:", self.initial_amount_field)
            form_layout.addRow("Descripción:", self.description_field)
            
            # Create buttons
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(self.accept)
            button_box.rejected.connect(self.reject)
            
            # Add layouts to main layout
            main_layout.addLayout(form_layout)
            main_layout.addWidget(button_box)
        except Exception as e:
            print(f"Error in OpenCashDrawerDialog.init_ui: {str(e)}")
        
    def accept(self):
        """Handle dialog acceptance."""
        try:
            print("OpenDrawerDialog accept called")
            # Get values from form
            initial_amount = Decimal(str(self.initial_amount_field.value()))
            description = self.description_field.toPlainText() or "Apertura inicial de caja"
            
            # Call service to open drawer
            self.entry = self.cash_drawer_service.open_drawer(
                initial_amount=initial_amount,
                description=description,
                user_id=self.user_id
            )
            
            QMessageBox.information(
                self, 
                "Éxito", 
                f"Caja abierta exitosamente con un monto inicial de {locale.currency(float(initial_amount), grouping=True)}"
            )
            
            super().accept()
            
        except ValueError as e:
            print(f"ValueError in OpenDrawerDialog accept: {str(e)}")
            QMessageBox.warning(self, "Error", str(e))
            
        except Exception as e:
            print(f"Exception in OpenDrawerDialog accept: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error al abrir caja: {str(e)}")


class AddRemoveCashDialog(QDialog):
    """Dialog for adding or removing cash from the drawer."""
    
    def __init__(self, cash_drawer_service: CashDrawerService, user_id: int, is_adding: bool = True, parent=None):
        try:
            super().__init__(parent)
            self.cash_drawer_service = cash_drawer_service
            self.user_id = user_id
            self.is_adding = is_adding
            self.entry = None  # Will store the created entry
            
            self.amount_field = None
            self.description_field = None
            
            self.init_ui()
        except Exception as e:
            print(f"Error initializing AddRemoveCashDialog: {str(e)}")
        
    def init_ui(self):
        """Initialize the UI."""
        try:
            operation = "Agregar" if self.is_adding else "Retirar"
            self.setWindowTitle(f"{operation} Efectivo")
            self.setMinimumWidth(350)
            
            # Create layouts
            main_layout = QVBoxLayout(self)
            form_layout = QFormLayout()
            
            # Create widgets
            self.amount_field = QDoubleSpinBox()
            self.amount_field.setRange(0.01, 1000000)
            self.amount_field.setDecimals(2)
            self.amount_field.setSingleStep(100)
            self.amount_field.setPrefix("$ ")
            
            self.description_field = QPlainTextEdit()
            self.description_field.setPlaceholderText("Motivo del movimiento")
            self.description_field.setMaximumHeight(80)
            
            # Add widgets to form layout
            form_layout.addRow(f"{operation} Monto:", self.amount_field)
            form_layout.addRow("Descripción:", self.description_field)
            
            # Current balance info (optional, will be shown if available)
            try:
                current_balance = self.cash_drawer_service.repository.get_current_balance()
                balance_label = QLabel(f"Balance actual: {locale.currency(float(current_balance), grouping=True)}")
                form_layout.addRow("", balance_label)
            except:
                pass
            
            # Create buttons
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(self.accept)
            button_box.rejected.connect(self.reject)
            
            # Add layouts to main layout
            main_layout.addLayout(form_layout)
            main_layout.addWidget(button_box)
        except Exception as e:
            print(f"Error in AddRemoveCashDialog.init_ui: {str(e)}")
        
    def accept(self):
        """Handle dialog acceptance."""
        try:
            # Get values from form
            amount = Decimal(str(self.amount_field.value()))
            description = self.description_field.toPlainText()
            
            if not description:
                QMessageBox.warning(self, "Error", "Por favor ingrese una descripción del movimiento.")
                return
                
            # Call service to add/remove cash
            if self.is_adding:
                self.entry = self.cash_drawer_service.add_cash(
                    amount=amount,
                    description=description,
                    user_id=self.user_id
                )
                operation = "agregado"
            else:
                self.entry = self.cash_drawer_service.remove_cash(
                    amount=amount,
                    description=description,
                    user_id=self.user_id
                )
                operation = "retirado"
                
            QMessageBox.information(
                self, 
                "Éxito", 
                f"Se ha {operation} {locale.currency(float(amount), grouping=True)} de la caja."
            )
            
            super().accept()
            
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al procesar la operación: {str(e)}")


class CashDrawerHistoryDialog(QDialog):
    """Dialog for viewing cash drawer history."""
    
    def __init__(self, cash_drawer_service: CashDrawerService, parent=None, test_mode=False):
        try:
            super().__init__(parent)
            self.cash_drawer_service = cash_drawer_service
            self.test_mode = test_mode
            self.table_model = None
            
            # Initialize UI components
            self.table_view = None
            self.date_from = None
            self.date_to = None
            self.initial_label = None
            self.in_label = None
            self.out_label = None
            self.balance_label = None
            self.summary_group = None
            
            self.init_ui()
            if not test_mode:
                # Only load data in non-test mode
                self.load_today_data()
        except Exception as e:
            print(f"Error initializing CashDrawerHistoryDialog: {str(e)}")
        
    def init_ui(self):
        """Initialize the UI."""
        try:
            self.setWindowTitle("Historial de Caja")
            self.resize(800, 500)
            
            # Create layouts
            main_layout = QVBoxLayout(self)
            filter_layout = QHBoxLayout()
            
            # Create filter widgets
            self.date_from = QDateEdit(QDate.currentDate())
            self.date_to = QDateEdit(QDate.currentDate())
            filter_button = QPushButton("Filtrar")
            filter_button.clicked.connect(self.apply_filter)
            
            # Add widgets to filter layout
            filter_layout.addWidget(QLabel("Desde:"))
            filter_layout.addWidget(self.date_from)
            filter_layout.addWidget(QLabel("Hasta:"))
            filter_layout.addWidget(self.date_to)
            filter_layout.addWidget(filter_button)
            filter_layout.addStretch(1)
            
            # Create table view
            self.table_view = QTableView()
            self.table_view.setAlternatingRowColors(True)
            self.table_view.setSelectionBehavior(QTableView.SelectRows)
            self.table_view.setEditTriggers(QTableView.NoEditTriggers)
            
            # Only create and set up the model in non-test mode
            if not self.test_mode:
                try:
                    # Create model
                    self.table_model = CashDrawerTableModel()
                    self.table_view.setModel(self.table_model)
                    
                    # Adjust table columns
                    header = self.table_view.horizontalHeader()
                    if header:
                        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
                        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Timestamp
                        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Type
                        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Amount
                        header.setSectionResizeMode(4, QHeaderView.Stretch)           # Description
                        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # User
                except Exception as e:
                    print(f"Error setting up table model: {e}")
            
            # Create summary widgets
            self.summary_group = QGroupBox("Resumen")
            summary_form = QFormLayout(self.summary_group)
            
            self.initial_label = QLabel("0.00")
            self.in_label = QLabel("0.00")
            self.out_label = QLabel("0.00")
            self.balance_label = QLabel("0.00")
            
            # Set object names for testing
            self.initial_label.setObjectName("summary_initial")
            self.in_label.setObjectName("summary_cash_in")
            self.out_label.setObjectName("summary_cash_out")
            self.balance_label.setObjectName("summary_balance")
            
            font = QFont()
            font.setBold(True)
            self.balance_label.setFont(font)
            
            summary_form.addRow("Monto Inicial:", self.initial_label)
            summary_form.addRow("Entradas:", self.in_label)
            summary_form.addRow("Salidas:", self.out_label)
            summary_form.addRow("Balance Actual:", self.balance_label)
            
            # Add close button
            close_button = QPushButton("Cerrar")
            close_button.clicked.connect(self.accept)
            
            # Add widgets to main layout
            main_layout.addLayout(filter_layout)
            main_layout.addWidget(self.table_view)
            main_layout.addWidget(self.summary_group)
            main_layout.addWidget(close_button)
        except Exception as e:
            print(f"Error in CashDrawerHistoryDialog.init_ui: {str(e)}")
        
    def load_today_data(self):
        """Load data for today."""
        if self.test_mode:
            return  # Skip in test mode
            
        try:
            summary = self.cash_drawer_service.get_drawer_summary()
            
            # Update table - ensure model exists
            if self.table_model:
                self.table_model.setEntries(summary['entries_today'])
            
            # Update summary
            self.update_summary_display(summary)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar datos: {str(e)}")
            
    def apply_filter(self):
        """Apply date filter to load data for a specific range."""
        try:
            start_date = self.date_from.date().toPyDate()
            end_date = self.date_to.date().toPyDate()
            
            # Load entries for date range
            entries = self.cash_drawer_service.repository.get_entries_by_date_range(
                start_date=start_date,
                end_date=end_date
            )
            
            # Update table - check if model exists
            if hasattr(self, 'table_model') and self.table_model:
                self.table_model.setEntries(entries)
            
            # Update summary based on these entries
            self.update_summary_from_entries(entries)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al filtrar datos: {str(e)}")
            
    def update_summary_display(self, summary):
        """Update summary display with summary data."""
        self.initial_label.setText(locale.currency(float(summary.get('initial_amount', 0)), grouping=True))
        self.in_label.setText(locale.currency(float(summary.get('total_in', 0)), grouping=True))
        self.out_label.setText(locale.currency(float(summary.get('total_out', 0)), grouping=True))
        self.balance_label.setText(locale.currency(float(summary.get('current_balance', 0)), grouping=True))
        
    def update_summary_from_entries(self, entries):
        """Calculate and update summary from a list of entries."""
        from core.models.cash_drawer import CashDrawerEntryType
        from decimal import Decimal
        
        initial_amount = Decimal('0')
        total_in = Decimal('0')
        total_out = Decimal('0')
        balance = Decimal('0')
        
        for entry in entries:
            if entry.entry_type == CashDrawerEntryType.START:
                initial_amount += entry.amount
            elif entry.entry_type == CashDrawerEntryType.IN:
                total_in += entry.amount
            elif entry.entry_type == CashDrawerEntryType.OUT:
                total_out += abs(entry.amount)
            
            balance += entry.amount
        
        self.initial_label.setText(locale.currency(float(initial_amount), grouping=True))
        self.in_label.setText(locale.currency(float(total_in), grouping=True))
        self.out_label.setText(locale.currency(float(total_out), grouping=True))
        self.balance_label.setText(locale.currency(float(balance), grouping=True))

class CloseCashDrawerDialog(QDialog):
    """Dialog for closing the cash drawer."""

    def __init__(self, cash_drawer_service: CashDrawerService, user_id: int, parent=None):
        super().__init__(parent)
        self.cash_drawer_service = cash_drawer_service
        self.user_id = user_id
        self.entry = None  # Will store the created entry

        self.actual_amount_field = None
        self.description_field = None

        self.init_ui()

    def init_ui(self):
        """Initialize the UI."""
        self.setWindowTitle("Cerrar Caja")
        self.setMinimumWidth(350)

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.actual_amount_field = QDoubleSpinBox()
        self.actual_amount_field.setRange(0, 1000000)  # Allow 0 for cases where drawer might be empty
        self.actual_amount_field.setDecimals(2)
        self.actual_amount_field.setSingleStep(100)
        self.actual_amount_field.setPrefix("$ ")

        self.description_field = QPlainTextEdit()
        self.description_field.setPlaceholderText("Descripción del cierre (opcional)")
        self.description_field.setMaximumHeight(80)

        form_layout.addRow("Monto Real en Caja:", self.actual_amount_field)
        form_layout.addRow("Descripción:", self.description_field)

        # Display expected balance if possible (read-only)
        try:
            # This requires the service to have a method to get expected balance or similar
            # For now, we'll assume it's passed or calculated elsewhere if needed.
            # current_balance = self.cash_drawer_service.get_expected_balance_for_close() # Example
            # balance_label = QLabel(f"Balance esperado: {locale.currency(float(current_balance), grouping=True)}")
            # form_layout.addRow("", balance_label)
            pass # Placeholder for future enhancement
        except Exception as e:
            print(f"Could not fetch expected balance for close dialog: {e}")

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)

    def accept(self):
        """Handle dialog acceptance."""
        try:
            actual_amount = Decimal(str(self.actual_amount_field.value()))
            description = self.description_field.toPlainText() or f"Cierre de caja - {date.today().strftime('%Y-%m-%d')}"

            # Call the service to close the drawer
            self.entry = self.cash_drawer_service.close_drawer(
                actual_amount=actual_amount,
                description=description,
                user_id=self.user_id
                # drawer_id can be passed if multi-drawer support is active
            )

            QMessageBox.information(
                self,
                "Éxito",
                f"Caja cerrada exitosamente con un monto de {locale.currency(float(actual_amount), grouping=True)}."
            )
            super().accept()

        except ValueError as ve:
            QMessageBox.warning(self, "Error de Validación", str(ve))
        except Exception as e:
            # Log the error for debugging
            print(f"Error closing cash drawer: {e}") 
            QMessageBox.critical(self, "Error", f"Ocurrió un error al cerrar la caja: {str(e)}")
            # Do not call super().accept() on critical error, so dialog stays open


# Add aliases for backward compatibility with cash_drawer_view.py
OpenDrawerDialog = OpenCashDrawerDialog
CashMovementDialog = AddRemoveCashDialog
