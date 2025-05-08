from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QDateEdit, QPushButton, QTableView, QTabWidget, QFrame,
    QSplitter, QGroupBox, QFormLayout, QGridLayout, QSpacerItem,
    QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt, QDate, Slot, QDateTime
from PySide6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from PySide6.QtGui import QPainter
import os
import subprocess
import platform

from datetime import datetime, timedelta
from ui.models.table_models import ReportTableModel
from core.services.reporting_service import ReportingService


class ReportsView(QWidget):
    """View for displaying advanced sales reports and charts."""
    
    def __init__(self, reporting_service: ReportingService, parent=None):
        super().__init__(parent)
        self.reporting_service = reporting_service
        
        # Set up the layout
        main_layout = QVBoxLayout(self)
        
        # Create filter section
        filter_frame = QFrame(self)
        filter_frame.setFrameShape(QFrame.StyledPanel)
        filter_layout = QHBoxLayout(filter_frame)
        
        # Date range filter
        date_group = QGroupBox("Período")
        date_layout = QFormLayout(date_group)
        
        self.date_preset_combo = QComboBox()
        self.date_preset_combo.addItems([
            "Hoy", 
            "Ayer", 
            "Esta semana", 
            "Semana pasada",
            "Este mes", 
            "Mes pasado", 
            "Este año", 
            "Período personalizado"
        ])
        date_layout.addRow("Mostrar:", self.date_preset_combo)
        
        # Date range selectors (initially hidden, shown for custom period)
        date_range_layout = QHBoxLayout()
        
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addDays(-7))
        self.start_date_edit.setCalendarPopup(True)
        
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        
        date_range_layout.addWidget(QLabel("Desde:"))
        date_range_layout.addWidget(self.start_date_edit)
        date_range_layout.addWidget(QLabel("Hasta:"))
        date_range_layout.addWidget(self.end_date_edit)
        
        date_layout.addRow("", date_range_layout)
        
        # Department filter
        self.department_combo = QComboBox()
        self.department_combo.addItem("Todos los departamentos")
        # We'll populate departments later
        
        # Customer filter
        self.customer_combo = QComboBox()
        self.customer_combo.addItem("Todos los clientes")
        # We'll populate customers later
        
        # Report type selection
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems([
            "Ventas por período",
            "Ventas por departamento", 
            "Ventas por cliente", 
            "Productos más vendidos",
            "Análisis de ganancias"
        ])
        
        # Generate report button
        self.generate_btn = QPushButton("Generar reporte")
        
        # Print report button
        self.print_btn = QPushButton("Imprimir reporte")
        self.print_btn.setEnabled(False)  # Disable until a report is generated
        
        # Add all filters to layout
        filter_layout.addWidget(date_group)
        filter_layout.addWidget(QLabel("Departamento:"))
        filter_layout.addWidget(self.department_combo)
        filter_layout.addWidget(QLabel("Cliente:"))
        filter_layout.addWidget(self.customer_combo)
        filter_layout.addWidget(QLabel("Tipo de reporte:"))
        filter_layout.addWidget(self.report_type_combo)
        filter_layout.addWidget(self.generate_btn)
        filter_layout.addWidget(self.print_btn)
        
        main_layout.addWidget(filter_frame)
        
        # Create tab widget for different report views
        self.tab_widget = QTabWidget()
        self.table_tab = QWidget()
        self.chart_tab = QWidget()
        self.summary_tab = QWidget()
        
        # Set up table tab
        table_layout = QVBoxLayout(self.table_tab)
        self.result_table = QTableView()
        self.result_table.setAlternatingRowColors(True)
        table_layout.addWidget(self.result_table)
        
        # Set up chart tab
        chart_layout = QVBoxLayout(self.chart_tab)
        
        # Create chart
        self.chart = QChart()
        self.chart.setTitle("Ventas por período")
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        
        chart_layout.addWidget(self.chart_view)
        
        # Set up summary tab
        summary_layout = QGridLayout(self.summary_tab)
        
        # Summary widgets
        self.total_sales_value = QLabel("$0.00")
        self.total_sales_value.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.total_sales_count = QLabel("0")
        self.avg_sale_value = QLabel("$0.00")
        self.total_profit_value = QLabel("$0.00")
        self.profit_margin_value = QLabel("0%")
        
        # Add summary widgets to layout
        summary_layout.addWidget(QLabel("Total de Ventas:"), 0, 0)
        summary_layout.addWidget(self.total_sales_value, 0, 1)
        summary_layout.addWidget(QLabel("Número de Ventas:"), 1, 0)
        summary_layout.addWidget(self.total_sales_count, 1, 1)
        summary_layout.addWidget(QLabel("Venta Promedio:"), 2, 0)
        summary_layout.addWidget(self.avg_sale_value, 2, 1)
        summary_layout.addWidget(QLabel("Ganancia Total:"), 3, 0)
        summary_layout.addWidget(self.total_profit_value, 3, 1)
        summary_layout.addWidget(QLabel("Margen de Ganancia:"), 4, 0)
        summary_layout.addWidget(self.profit_margin_value, 4, 1)
        
        # Add spacer to push summary widgets to top
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        summary_layout.addItem(spacer, 5, 0, 1, 2)
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.table_tab, "Tabla")
        self.tab_widget.addTab(self.chart_tab, "Gráfico")
        self.tab_widget.addTab(self.summary_tab, "Resumen")
        
        main_layout.addWidget(self.tab_widget)
        
        # Connect signals
        self.date_preset_combo.currentIndexChanged.connect(self._handle_date_preset_changed)
        self.generate_btn.clicked.connect(self._generate_report)
        self.print_btn.clicked.connect(self._print_report)
        
        # Initialize with default data
        self._handle_date_preset_changed(0)  # Default to "Hoy"
        
        # Store the current report type and data for printing
        self.current_report_type = None
        self.current_start_date = None
        self.current_end_date = None
        self.pdf_path = None
    
    @Slot(int)
    def _handle_date_preset_changed(self, index):
        """Handle changes to the date preset combobox."""
        today = QDate.currentDate()
        
        # Hide/show date range controls based on selection
        custom_period = (index == 7)  # "Período personalizado" is the last option
        
        # Set date range based on selection
        if index == 0:  # Hoy
            self.start_date_edit.setDate(today)
            self.end_date_edit.setDate(today)
        elif index == 1:  # Ayer
            yesterday = today.addDays(-1)
            self.start_date_edit.setDate(yesterday)
            self.end_date_edit.setDate(yesterday)
        elif index == 2:  # Esta semana
            # Get the first day of the week (Monday)
            days_to_monday = today.dayOfWeek() - 1
            monday = today.addDays(-days_to_monday)
            self.start_date_edit.setDate(monday)
            self.end_date_edit.setDate(today)
        elif index == 3:  # Semana pasada
            days_to_monday = today.dayOfWeek() - 1
            last_monday = today.addDays(-days_to_monday - 7)
            last_sunday = today.addDays(-days_to_monday - 1)
            self.start_date_edit.setDate(last_monday)
            self.end_date_edit.setDate(last_sunday)
        elif index == 4:  # Este mes
            first_day = QDate(today.year(), today.month(), 1)
            self.start_date_edit.setDate(first_day)
            self.end_date_edit.setDate(today)
        elif index == 5:  # Mes pasado
            first_day_last_month = QDate(today.year(), today.month(), 1).addMonths(-1)
            last_day_last_month = QDate(today.year(), today.month(), 1).addDays(-1)
            self.start_date_edit.setDate(first_day_last_month)
            self.end_date_edit.setDate(last_day_last_month)
        elif index == 6:  # Este año
            first_day = QDate(today.year(), 1, 1)
            self.start_date_edit.setDate(first_day)
            self.end_date_edit.setDate(today)
    
    @Slot()
    def _generate_report(self):
        """Generate the selected report using the reporting service."""
        # Get date range
        start_date = self.start_date_edit.date().toPython()
        end_date = self.end_date_edit.date().toPython()
        
        # Convert to datetime with time
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Store current report parameters for printing
        self.current_report_type = self.report_type_combo.currentIndex()
        self.current_start_date = start_datetime
        self.current_end_date = end_datetime
        
        # Get report type
        report_type_index = self.report_type_combo.currentIndex()
        
        # Reset PDF path
        self.pdf_path = None
        
        # Generate appropriate report based on type
        try:
            if report_type_index == 0:  # Ventas por período
                self._generate_sales_by_period_report(start_datetime, end_datetime)
            elif report_type_index == 1:  # Ventas por departamento
                self._generate_sales_by_department_report(start_datetime, end_datetime)
            elif report_type_index == 2:  # Ventas por cliente
                self._generate_sales_by_customer_report(start_datetime, end_datetime)
            elif report_type_index == 3:  # Productos más vendidos
                self._generate_top_products_report(start_datetime, end_datetime)
            elif report_type_index == 4:  # Análisis de ganancias
                self._generate_profit_analysis_report(start_datetime, end_datetime)
            
            # Show table tab by default after generating report
            self.tab_widget.setCurrentIndex(0)
            
            # Enable print button since we have a report
            self.print_btn.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al generar el reporte: {str(e)}")
            self.print_btn.setEnabled(False)
    
    @Slot()
    def _print_report(self):
        """Generate a PDF report and open it with the default PDF viewer."""
        if self.current_report_type is None:
            # Skip showing message box in test environment
            if 'PYTEST_CURRENT_TEST' not in os.environ:
                QMessageBox.warning(self, "Advertencia", "Primero debe generar un reporte para imprimirlo.")
            return
        
        try:
            # Generate PDF based on current report type
            if self.current_report_type == 0:  # Ventas por período
                self.pdf_path = self.reporting_service.print_sales_by_period_report(
                    self.current_start_date, 
                    self.current_end_date
                )
            elif self.current_report_type == 1:  # Ventas por departamento
                self.pdf_path = self.reporting_service.print_sales_by_department_report(
                    self.current_start_date, 
                    self.current_end_date
                )
            elif self.current_report_type == 2:  # Ventas por cliente
                self.pdf_path = self.reporting_service.print_sales_by_customer_report(
                    self.current_start_date, 
                    self.current_end_date
                )
            elif self.current_report_type == 3:  # Productos más vendidos
                self.pdf_path = self.reporting_service.print_top_products_report(
                    self.current_start_date, 
                    self.current_end_date
                )
            elif self.current_report_type == 4:  # Análisis de ganancias
                self.pdf_path = self.reporting_service.print_profit_analysis_report(
                    self.current_start_date, 
                    self.current_end_date
                )
                
            # Always call _open_pdf even during tests, but _open_pdf itself will handle test mode
            if self.pdf_path:
                self._open_pdf(self.pdf_path)
                
                # Skip showing message box in test environment
                if 'PYTEST_CURRENT_TEST' not in os.environ:
                    QMessageBox.information(
                        self, 
                        "Reporte generado", 
                        f"El reporte ha sido generado correctamente y guardado en:\n{self.pdf_path}"
                    )
            else:
                # Skip showing message box in test environment
                if 'PYTEST_CURRENT_TEST' not in os.environ:
                    QMessageBox.warning(self, "Advertencia", "No se pudo generar o abrir el archivo PDF.")
                
        except Exception as e:
            # Skip showing message box in test environment
            if 'PYTEST_CURRENT_TEST' not in os.environ:
                QMessageBox.critical(self, "Error", f"Error al generar el reporte PDF: {str(e)}")
    
    def _open_pdf(self, pdf_path):
        """Open a PDF file with the system's default PDF viewer."""
        # During tests, just do nothing but don't skip the method call
        if 'PYTEST_CURRENT_TEST' in os.environ:
            return
            
        try:
            # Use the appropriate method based on the operating system
            if platform.system() == 'Windows':
                os.startfile(pdf_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', pdf_path], check=True)
            else:  # Linux and others
                subprocess.run(['xdg-open', pdf_path], check=True)
        except Exception as e:
            QMessageBox.warning(
                self, 
                "Error al abrir PDF", 
                f"No se pudo abrir el archivo PDF: {str(e)}\n\nPuede encontrar el archivo en: {pdf_path}"
            )
    
    def _generate_sales_by_period_report(self, start_datetime, end_datetime):
        """Generate sales by period report."""
        # Get data from reporting service
        data = self.reporting_service.get_sales_summary_by_period(
            start_datetime, end_datetime, 'day'
        )
        
        if not data:
            QMessageBox.information(self, "Sin datos", "No hay datos para el período seleccionado.")
            return
        
        # Update table with data
        headers = ["Fecha", "Ventas Totales", "Número de Ventas"]
        table_data = []
        
        # Create bar chart data
        bar_set = QBarSet("Ventas")
        categories = []
        
        total_sales_amount = 0.0
        total_sales_count = 0
        
        for row in data:
            date_str = row['date']
            total_amount = row['total_sales']
            num_sales = row['num_sales']
            
            table_data.append([date_str, f"${total_amount:.2f}", num_sales])
            
            # Add to chart data
            bar_set.append(total_amount)
            categories.append(date_str)
            
            # Update totals
            total_sales_amount += total_amount
            total_sales_count += num_sales
        
        # Create table model and set data
        model = ReportTableModel(table_data, headers)
        self.result_table.setModel(model)
        
        # Create chart
        self._update_chart("Ventas por día", categories, [bar_set])
        
        # Update summary
        avg_sale = total_sales_amount / total_sales_count if total_sales_count > 0 else 0
        
        # Get profit data for the same period
        profit_data = self.reporting_service.calculate_profit_for_period(
            start_datetime, end_datetime
        )
        
        self.total_sales_value.setText(f"${total_sales_amount:.2f}")
        self.total_sales_count.setText(str(total_sales_count))
        self.avg_sale_value.setText(f"${avg_sale:.2f}")
        self.total_profit_value.setText(f"${profit_data.get('total_profit', 0.0):.2f}")
        self.profit_margin_value.setText(f"{profit_data.get('profit_margin', 0.0) * 100:.1f}%")
    
    def _generate_sales_by_department_report(self, start_datetime, end_datetime):
        """Generate sales by department report."""
        # Get data from reporting service
        data = self.reporting_service.get_sales_by_department(
            start_datetime, end_datetime
        )
        
        if not data:
            QMessageBox.information(self, "Sin datos", "No hay datos para el período seleccionado.")
            return
        
        # Update table with data
        headers = ["Departamento", "Ventas Totales", "Cantidad de Artículos"]
        table_data = []
        
        # Create bar chart data
        bar_set = QBarSet("Ventas")
        categories = []
        
        total_sales_amount = 0.0
        
        for row in data:
            dept_name = row['department_name']
            total_amount = row['total_amount']
            num_items = row['num_items']
            
            table_data.append([dept_name, f"${total_amount:.2f}", num_items])
            
            # Add to chart data
            bar_set.append(total_amount)
            categories.append(dept_name)
            
            # Update totals
            total_sales_amount += total_amount
        
        # Create table model and set data
        model = ReportTableModel(table_data, headers)
        self.result_table.setModel(model)
        
        # Create chart
        self._update_chart("Ventas por departamento", categories, [bar_set])
        
        # Get additional data for summary
        period_data = self.reporting_service.calculate_profit_for_period(
            start_datetime, end_datetime
        )
        
        # Update summary
        self.total_sales_value.setText(f"${total_sales_amount:.2f}")
        self.total_sales_count.setText(str(sum(row['num_items'] for row in data)))
        self.total_profit_value.setText(f"${period_data.get('total_profit', 0.0):.2f}")
        self.profit_margin_value.setText(f"{period_data.get('profit_margin', 0.0) * 100:.1f}%")
    
    def _generate_sales_by_customer_report(self, start_datetime, end_datetime):
        """Generate sales by customer report."""
        # Get data from reporting service
        data = self.reporting_service.get_sales_by_customer(
            start_datetime, end_datetime, 20  # Get top 20 customers
        )
        
        if not data:
            QMessageBox.information(self, "Sin datos", "No hay datos para el período seleccionado.")
            return
        
        # Update table with data
        headers = ["Cliente", "Ventas Totales", "Número de Ventas"]
        table_data = []
        
        # Create bar chart data (limit to top 10 for better display)
        bar_set = QBarSet("Ventas")
        categories = []
        
        total_sales_amount = 0.0
        
        for i, row in enumerate(data):
            customer_name = row['customer_name']
            total_amount = row['total_amount']
            num_sales = row['num_sales']
            
            table_data.append([customer_name, f"${total_amount:.2f}", num_sales])
            
            # Add to chart data (top 10 only)
            if i < 10:
                bar_set.append(total_amount)
                categories.append(customer_name)
            
            # Update totals
            total_sales_amount += total_amount
        
        # Create table model and set data
        model = ReportTableModel(table_data, headers)
        self.result_table.setModel(model)
        
        # Create chart
        self._update_chart("Top 10 clientes por ventas", categories, [bar_set])
        
        # Update summary with basic data available from this report
        self.total_sales_value.setText(f"${total_sales_amount:.2f}")
        self.total_sales_count.setText(str(sum(row['num_sales'] for row in data)))
    
    def _generate_top_products_report(self, start_datetime, end_datetime):
        """Generate top products report."""
        # Get data from reporting service
        data = self.reporting_service.get_top_selling_products(
            start_datetime, end_datetime, 50  # Get top 50 products
        )
        
        if not data:
            QMessageBox.information(self, "Sin datos", "No hay datos para el período seleccionado.")
            return
        
        # Update table with data
        headers = ["Código", "Descripción", "Cantidad Vendida", "Total Vendido"]
        table_data = []
        
        # Create bar chart data (limit to top 10 for better display)
        bar_set = QBarSet("Unidades vendidas")
        bar_set2 = QBarSet("Ventas $")
        categories = []
        
        total_quantity = 0.0
        total_amount = 0.0
        
        for i, row in enumerate(data):
            code = row['product_code']
            description = row['product_description']
            quantity = row['quantity_sold']
            amount = row['total_amount']
            
            table_data.append([code, description, quantity, f"${amount:.2f}"])
            
            # Add to chart data (top 10 only)
            if i < 10:
                bar_set.append(quantity)
                bar_set2.append(amount / 100)  # Scale down for dual axis
                categories.append(code)
            
            # Update totals
            total_quantity += quantity
            total_amount += amount
        
        # Create table model and set data
        model = ReportTableModel(table_data, headers)
        self.result_table.setModel(model)
        
        # Create chart with dual series
        self._update_chart("Top 10 productos", categories, [bar_set, bar_set2])
        
        # Update summary
        self.total_sales_value.setText(f"${total_amount:.2f}")
        self.total_sales_count.setText(f"{int(total_quantity)} unidades")
    
    def _generate_profit_analysis_report(self, start_datetime, end_datetime):
        """Generate profit analysis report."""
        # Get profit data
        profit_data = self.reporting_service.calculate_profit_for_period(
            start_datetime, end_datetime
        )
        
        if not profit_data:
            QMessageBox.information(self, "Sin datos", "No hay datos para el período seleccionado.")
            return
        
        # Create a more detailed table for profit analysis
        headers = ["Métrica", "Valor"]
        table_data = [
            ["Ventas Totales", f"${profit_data.get('total_revenue', 0.0):.2f}"],
            ["Costo de Productos", f"${profit_data.get('total_cost', 0.0):.2f}"],
            ["Ganancia Bruta", f"${profit_data.get('total_profit', 0.0):.2f}"],
            ["Margen de Ganancia", f"{profit_data.get('profit_margin', 0.0) * 100:.2f}%"]
        ]
        
        # Get sales by payment type for additional analysis
        payment_data = self.reporting_service.get_sales_by_payment_type(
            start_datetime, end_datetime
        )
        
        # Add payment type breakdown to the table
        for row in payment_data:
            payment_type = row['payment_type']
            amount = row['total_amount']
            table_data.append([f"Ventas por {payment_type}", f"${amount:.2f}"])
        
        # Create table model and set data
        model = ReportTableModel(table_data, headers)
        self.result_table.setModel(model)
        
        # Create a bar chart showing revenue vs cost
        bar_set1 = QBarSet("Ventas")
        bar_set1.append(profit_data.get('total_revenue', 0.0))
        
        bar_set2 = QBarSet("Costo")
        bar_set2.append(profit_data.get('total_cost', 0.0))
        
        bar_set3 = QBarSet("Ganancia")
        bar_set3.append(profit_data.get('total_profit', 0.0))
        
        categories = ["Análisis de Ganancias"]
        
        self._update_chart("Análisis de Ganancias", categories, [bar_set1, bar_set2, bar_set3])
        
        # Update summary
        self.total_sales_value.setText(f"${profit_data.get('total_revenue', 0.0):.2f}")
        self.total_profit_value.setText(f"${profit_data.get('total_profit', 0.0):.2f}")
        self.profit_margin_value.setText(f"{profit_data.get('profit_margin', 0.0) * 100:.1f}%")
    
    def _update_chart(self, title, categories, bar_sets):
        """Update the chart with new data."""
        # Clear previous chart
        self.chart.removeAllSeries()
        
        # Create bar series and add bar sets
        bar_series = QBarSeries()
        for bar_set in bar_sets:
            bar_series.append(bar_set)
        
        self.chart.addSeries(bar_series)
        self.chart.setTitle(title)
        
        # Set up axes
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        self.chart.addAxis(axis_x, Qt.AlignBottom)
        bar_series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        self.chart.addAxis(axis_y, Qt.AlignLeft)
        bar_series.attachAxis(axis_y)
        
        # Set Y-axis range with some padding
        # Fix: QBarSet is not directly iterable, use loop to find max value
        max_value = 0
        for bar_set in bar_sets:
            for i in range(bar_set.count()):
                max_value = max(max_value, bar_set.at(i))
        
        # Add 10% padding to max value
        axis_y.setRange(0, max_value * 1.1)
        
        # Customize the chart
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignBottom)