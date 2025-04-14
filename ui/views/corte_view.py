from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QComboBox, QDateEdit, QDoubleSpinBox, QGridLayout,
    QSplitter, QTableView, QHeaderView, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt, QDate, Slot
from PySide6.QtGui import QFont, QColor
from datetime import datetime, time, timedelta
from decimal import Decimal

from core.services.corte_service import CorteService
from core.models.cash_drawer import CashDrawerEntry, CashDrawerEntryType
from ui.models.table_models import CashDrawerEntryTableModel
from ui.widgets.filter_dropdowns import PeriodFilterWidget, FilterBoxWidget, FilterDropdown


class CorteView(QWidget):
    """
    View for displaying the end-of-day/shift cash drawer reconciliation (Corte) report.
    Shows sales totals by payment type, cash movements, and calculates expected cash in drawer.
    """
    
    def __init__(self, corte_service: CorteService, user_id: int = None):
        super().__init__()
        self.corte_service = corte_service
        self.user_id = user_id
        self.current_data = None
        
        # Create table models for cash entries
        self.cash_in_model = CashDrawerEntryTableModel()
        self.cash_out_model = CashDrawerEntryTableModel()
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Corte de Caja")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Filter section using our new widget
        filter_box = FilterBoxWidget(self)
        
        # Period filter using our custom widget
        self.period_filter = PeriodFilterWidget("Mostrar ventas de:")
        filter_box.add_widget(self.period_filter)
        
        # Cash register filter (future enhancement, initially just showing one option)
        self.register_filter = FilterDropdown("De la Caja:", [
            ("Caja Principal", 1)
        ])
        filter_box.add_widget(self.register_filter)
        
        # Add filter box to main layout
        main_layout.addWidget(filter_box)
        
        # Report content - Split into left and right sections
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left section - Financial summary
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Sales Summary Section
        sales_frame = self._create_section_frame("Resumen de Ventas")
        sales_layout = QGridLayout()
        
        # Row 1: Total Sales
        sales_layout.addWidget(QLabel("Total de ventas:"), 0, 0)
        self.total_sales_label = QLabel("$0.00")
        self.total_sales_label.setFont(self._create_bold_font())
        sales_layout.addWidget(self.total_sales_label, 0, 1)
        
        # Row 2: Number of Sales
        sales_layout.addWidget(QLabel("Número de ventas:"), 1, 0)
        self.sale_count_label = QLabel("0")
        sales_layout.addWidget(self.sale_count_label, 1, 1)
        
        # Add sales summary layout to frame
        sales_frame.setLayout(sales_layout)
        left_layout.addWidget(sales_frame)
        
        # Sales by Payment Type Section
        payment_frame = self._create_section_frame("Ventas por Forma de Pago")
        payment_layout = QGridLayout()
        
        # Will be populated dynamically based on data
        self.payment_type_labels = {}
        
        # Placeholder rows - will be replaced with actual data
        payment_layout.addWidget(QLabel("Efectivo:"), 0, 0)
        self.payment_type_labels["Efectivo"] = QLabel("$0.00")
        payment_layout.addWidget(self.payment_type_labels["Efectivo"], 0, 1)
        
        payment_layout.addWidget(QLabel("Tarjeta:"), 1, 0)
        self.payment_type_labels["Tarjeta"] = QLabel("$0.00")
        payment_layout.addWidget(self.payment_type_labels["Tarjeta"], 1, 1)
        
        payment_layout.addWidget(QLabel("Crédito:"), 2, 0)
        self.payment_type_labels["Crédito"] = QLabel("$0.00")
        payment_layout.addWidget(self.payment_type_labels["Crédito"], 2, 1)
        
        # Add payment types layout to frame
        payment_frame.setLayout(payment_layout)
        left_layout.addWidget(payment_frame)
        
        # Cash Drawer Section
        cash_frame = self._create_section_frame("Caja")
        cash_layout = QGridLayout()
        
        # Row 1: Starting Balance
        cash_layout.addWidget(QLabel("Saldo inicial:"), 0, 0)
        self.starting_balance_label = QLabel("$0.00")
        cash_layout.addWidget(self.starting_balance_label, 0, 1)
        
        # Row 2: Cash Sales
        cash_layout.addWidget(QLabel("Ventas en efectivo:"), 1, 0)
        self.cash_sales_label = QLabel("$0.00")
        cash_layout.addWidget(self.cash_sales_label, 1, 1)
        
        # Row 3: Cash In
        cash_layout.addWidget(QLabel("Entradas de efectivo:"), 2, 0)
        self.cash_in_label = QLabel("$0.00")
        cash_layout.addWidget(self.cash_in_label, 2, 1)
        
        # Row 4: Cash Out
        cash_layout.addWidget(QLabel("Salidas de efectivo:"), 3, 0)
        self.cash_out_label = QLabel("$0.00")
        cash_layout.addWidget(self.cash_out_label, 3, 1)
        
        # Row 5: Expected Cash (calculated)
        cash_layout.addWidget(QLabel("Efectivo esperado en caja:"), 4, 0)
        self.expected_cash_label = QLabel("$0.00")
        self.expected_cash_label.setFont(self._create_bold_font())
        cash_layout.addWidget(self.expected_cash_label, 4, 1)
        
        # Row 6: Actual Cash (user input)
        cash_layout.addWidget(QLabel("Efectivo real en caja:"), 5, 0)
        self.actual_cash_input = QDoubleSpinBox()
        self.actual_cash_input.setRange(0, 1000000)
        self.actual_cash_input.setDecimals(2)
        self.actual_cash_input.setSingleStep(10)
        self.actual_cash_input.valueChanged.connect(self._calculate_cash_difference)
        cash_layout.addWidget(self.actual_cash_input, 5, 1)
        
        # Row 7: Difference (calculated)
        cash_layout.addWidget(QLabel("Diferencia:"), 6, 0)
        self.cash_difference_label = QLabel("$0.00")
        cash_layout.addWidget(self.cash_difference_label, 6, 1)
        
        # Add cash layout to frame
        cash_frame.setLayout(cash_layout)
        left_layout.addWidget(cash_frame)
        
        # "Do Corte" Button
        self.do_corte_btn = QPushButton("Hacer Corte del Día")
        self.do_corte_btn.setMinimumHeight(40)
        self.do_corte_btn.clicked.connect(self._on_do_corte)
        left_layout.addWidget(self.do_corte_btn)
        
        left_layout.addStretch()
        
        # Right section - Cash drawer movements
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Cash In Entries
        cash_in_frame = self._create_section_frame("Entradas de Efectivo")
        cash_in_layout = QVBoxLayout()
        
        self.cash_in_table = QTableView()
        self.cash_in_table.setModel(self.cash_in_model)
        self.cash_in_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.cash_in_table.verticalHeader().setVisible(False)
        self.cash_in_table.setAlternatingRowColors(True)
        
        cash_in_layout.addWidget(self.cash_in_table)
        cash_in_frame.setLayout(cash_in_layout)
        right_layout.addWidget(cash_in_frame)
        
        # Cash Out Entries
        cash_out_frame = self._create_section_frame("Salidas de Efectivo")
        cash_out_layout = QVBoxLayout()
        
        self.cash_out_table = QTableView()
        self.cash_out_table.setModel(self.cash_out_model)
        self.cash_out_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.cash_out_table.verticalHeader().setVisible(False)
        self.cash_out_table.setAlternatingRowColors(True)
        
        cash_out_layout.addWidget(self.cash_out_table)
        cash_out_frame.setLayout(cash_out_layout)
        right_layout.addWidget(cash_out_frame)
        
        # Add widgets to splitter and set sizes
        content_splitter.addWidget(left_widget)
        content_splitter.addWidget(right_widget)
        content_splitter.setSizes([1, 1])  # Equal initial sizes
        
        # Add splitter to main layout
        main_layout.addWidget(content_splitter)
        
        # Set layout margins and spacing
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Connect signals
        self.period_filter.periodChanged.connect(self._on_period_changed)
        
        # Initialize with default period (Today)
    
    def _create_section_frame(self, title):
        """Create a framed section with title"""
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setFrameShadow(QFrame.Shadow.Raised)
        frame.setLineWidth(1)
        frame.setMidLineWidth(0)
        
        # Apply stylesheet for a cleaner look
        frame.setStyleSheet("QFrame { background-color: #f8f8f8; border: 1px solid #ddd; border-radius: 4px; }")
        
        # Create and add title label to the frame's layout later
        layout = QVBoxLayout(frame)
        title_label = QLabel(title)
        title_label.setFont(self._create_bold_font())
        layout.addWidget(title_label)
        
        return frame
    
    def _create_bold_font(self):
        """Create a bold font for headings"""
        font = QFont()
        font.setBold(True)
        return font
    
    @Slot(datetime, datetime)
    def _on_period_changed(self, start_datetime, end_datetime):
        """Handle period filter selection changes and refresh report."""
        self._refresh_corte_report(start_datetime, end_datetime)
    
    def _refresh_corte_report(self, start_time, end_time):
        """Fetch data and update the corte report for the given time period."""
        try:
            # Get the corte data from the service
            corte_data = self.corte_service.calculate_corte_data(start_time, end_time)
            self.current_data = corte_data
            
            # Update sales summary
            self.total_sales_label.setText(f"${corte_data['total_sales']:.2f}")
            self.sale_count_label.setText(str(corte_data['num_sales']))
            
            # Update payment type breakdown
            for payment_type, amount in corte_data['sales_by_payment_type'].items():
                # Create label if it doesn't exist
                if payment_type not in self.payment_type_labels:
                    payment_layout = self.payment_type_labels["Efectivo"].parent().layout()
                    row = payment_layout.rowCount()
                    payment_layout.addWidget(QLabel(f"{payment_type}:"), row, 0)
                    self.payment_type_labels[payment_type] = QLabel("$0.00")
                    payment_layout.addWidget(self.payment_type_labels[payment_type], row, 1)
                
                # Update label
                self.payment_type_labels[payment_type].setText(f"${amount:.2f}")
            
            # Update cash drawer summary
            self.starting_balance_label.setText(f"${corte_data['starting_balance']:.2f}")
            self.cash_sales_label.setText(f"${corte_data['cash_sales']:.2f}")
            self.cash_in_label.setText(f"${corte_data['cash_in_total']:.2f}")
            self.cash_out_label.setText(f"${corte_data['cash_out_total']:.2f}")
            
            # Calculate and update expected cash
            expected_cash = (
                corte_data['starting_balance'] + 
                corte_data['cash_sales'] + 
                corte_data['cash_in_total'] - 
                corte_data['cash_out_total']
            )
            self.expected_cash_label.setText(f"${expected_cash:.2f}")
            
            # Reset actual cash input and difference
            self.actual_cash_input.setValue(expected_cash)
            self._calculate_cash_difference()
            
            # Update cash in/out tables
            self.cash_in_model.update_entries(corte_data['cash_in_entries'])
            self.cash_out_model.update_entries(corte_data['cash_out_entries'])
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar el reporte: {str(e)}")
    
    def _calculate_cash_difference(self):
        """Calculate and display the difference between expected and actual cash."""
        if self.current_data is None:
            return
        
        expected_cash = (
            self.current_data['starting_balance'] + 
            self.current_data['cash_sales'] + 
            self.current_data['cash_in_total'] - 
            self.current_data['cash_out_total']
        )
        
        actual_cash = self.actual_cash_input.value()
        difference = actual_cash - expected_cash
        
        # Display difference with color coding
        self.cash_difference_label.setText(f"${difference:.2f}")
        
        # Use color to indicate positive (green) or negative (red) difference
        if difference < 0:
            self.cash_difference_label.setStyleSheet("color: red;")
        elif difference > 0:
            self.cash_difference_label.setStyleSheet("color: green;")
        else:
            self.cash_difference_label.setStyleSheet("")
    
    def _on_do_corte(self):
        """Execute the 'Corte' operation - finalize current period and save results."""
        if self.current_data is None:
            QMessageBox.warning(self, "Advertencia", "No hay datos para realizar el corte.")
            return
        
        # Ask for confirmation
        response = QMessageBox.question(
            self, 
            "Confirmar Corte", 
            "¿Está seguro que desea realizar el corte? Esta operación no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if response == QMessageBox.StandardButton.Yes:
            try:
                # Get the current actual cash value
                actual_cash = self.actual_cash_input.value()
                
                # Call service to finalize the corte
                self.corte_service.finalize_corte(
                    self.period_filter.get_period_range()[0],  # start_time
                    self.period_filter.get_period_range()[1],  # end_time
                    actual_cash,
                    self.user_id
                )
                
                QMessageBox.information(
                    self, 
                    "Corte Realizado", 
                    "El corte de caja se ha realizado exitosamente."
                )
                
                # Refresh the report
                self._on_period_changed(*self.period_filter.get_period_range())
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al realizar el corte: {str(e)}")