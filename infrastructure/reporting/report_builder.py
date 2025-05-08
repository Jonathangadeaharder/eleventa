from typing import List, Dict, Any
from datetime import datetime
import os

# Required imports for PDF generation
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch

from config import Config


class ReportBuilder:
    """Class to generate reports in PDF format."""

    def __init__(self, store_info=None):
        """
        Initialize the report builder.
        
        Args:
            store_info: Dictionary with store information like name, address, etc.
        """
        self.store_info = store_info or {
            "name": Config.STORE_NAME or "Eleventa Demo Store",
            "address": Config.STORE_ADDRESS or "123 Main St, Buenos Aires, Argentina",
            "phone": Config.STORE_PHONE or "555-1234",
            "cuit": Config.STORE_CUIT or "30-12345678-9",
            "iva_condition": Config.STORE_IVA_CONDITION or "Responsable Inscripto",
            "logo_path": None  # Add logo path if available
        }

    def generate_report_pdf(
        self,
        report_title: str,
        report_data: Dict[str, Any],
        filename: str,
        is_landscape: bool = False
    ) -> bool:
        """
        Generate a PDF report.
        
        Args:
            report_title: Title of the report
            report_data: Dictionary containing the report data
            filename: Path where to save the PDF
            is_landscape: Whether to use landscape orientation
            
        Returns:
            bool: True if PDF generation was successful, False otherwise
        """
        try:
            # Create PDF directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
            
            # Set page orientation
            pagesize = landscape(letter) if is_landscape else letter
            
            # Create the PDF document
            doc = SimpleDocTemplate(
                filename,
                pagesize=pagesize,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Initialize elements list for the PDF content
            elements = []
            
            # Add report header
            elements.extend(self._create_header(report_title))
            
            # Different report sections based on report type
            if 'sales_by_period' in report_data:
                elements.extend(self._create_sales_by_period_report(report_data))
            elif 'sales_by_department' in report_data:
                elements.extend(self._create_sales_by_department_report(report_data))
            elif 'sales_by_customer' in report_data:
                elements.extend(self._create_sales_by_customer_report(report_data))
            elif 'top_products' in report_data:
                elements.extend(self._create_top_products_report(report_data))
            elif 'profit_analysis' in report_data:
                elements.extend(self._create_profit_analysis_report(report_data))
            elif 'drawer_id' in report_data:
                elements.extend(self._create_cash_drawer_report(report_data))
            elif 'report_type' in report_data and report_data['report_type'] == 'corte':
                elements.extend(self._create_corte_report(report_data))
            
            # Add footer
            elements.extend(self._create_footer())
            
            # Build the PDF
            doc.build(elements)
            return True
            
        except Exception as e:
            print(f"Error generating report PDF: {e}")
            return False

    def _create_header(self, report_title: str) -> List:
        """Create the header section with store info and report title."""
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'Title', 
            parent=styles['Heading1'], 
            fontSize=14,
            alignment=TA_CENTER
        )
        
        elements = []
        
        # Store info
        store_name = Paragraph(self.store_info.get("name", ""), styles['Heading1'])
        elements.append(store_name)
        
        # Store details
        store_address = Paragraph(self.store_info.get("address", ""), styles['Normal'])
        elements.append(store_address)
        store_phone = Paragraph(f"Tel: {self.store_info.get('phone', '')}", styles['Normal'])
        elements.append(store_phone)
        
        elements.append(Spacer(1, 0.25*inch))
        
        # Report title and date
        report_title_paragraph = Paragraph(report_title, title_style)
        elements.append(report_title_paragraph)
        
        date_text = f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        date_paragraph = Paragraph(date_text, styles['Normal'])
        elements.append(date_paragraph)
        
        elements.append(Spacer(1, 0.25*inch))
        
        return elements

    def _create_sales_by_period_report(self, report_data: Dict[str, Any]) -> List:
        """Create the sales by period report content."""
        styles = getSampleStyleSheet()
        elements = []
        
        # Report summary
        summary_text = f"""
        <b>Período:</b> {report_data.get('start_date', '')} al {report_data.get('end_date', '')}<br/>
        <b>Total ventas:</b> ${report_data.get('total_revenue', 0):.2f}<br/>
        <b>Número de ventas:</b> {report_data.get('sales_count', 0)}<br/>
        """
        summary = Paragraph(summary_text, styles['Normal'])
        elements.append(summary)
        elements.append(Spacer(1, 0.2*inch))
        
        # Sales table header
        elements.append(Paragraph("<b>Detalle de ventas por período:</b>", styles['Heading3']))
        
        # Sales table data
        data = [['Fecha', 'Total Ventas', 'Número de Ventas']]
        for sale in report_data.get('sales_by_period', []):
            data.append([
                sale.get('date', ''),
                f"${sale.get('total_sales', 0):.2f}",
                str(sale.get('num_sales', 0))
            ])
        
        # Add table to elements if there is data
        if len(data) > 1:
            table = self._create_table(data, [200, 150, 150])
            elements.append(table)
        else:
            elements.append(Paragraph("No hay datos disponibles para este período.", styles['Normal']))
        
        elements.append(Spacer(1, 0.3*inch))
        return elements

    def _create_sales_by_department_report(self, report_data: Dict[str, Any]) -> List:
        """Create the sales by department report content."""
        styles = getSampleStyleSheet()
        elements = []
        
        # Report summary
        summary_text = f"""
        <b>Período:</b> {report_data.get('start_date', '')} al {report_data.get('end_date', '')}<br/>
        <b>Total ventas:</b> ${report_data.get('total_revenue', 0):.2f}<br/>
        """
        summary = Paragraph(summary_text, styles['Normal'])
        elements.append(summary)
        elements.append(Spacer(1, 0.2*inch))
        
        # Sales by department table header
        elements.append(Paragraph("<b>Ventas por departamento:</b>", styles['Heading3']))
        
        # Sales by department table data
        data = [['Departamento', 'Total Ventas', 'Cantidad de Artículos', '% del Total']]
        for dept in report_data.get('sales_by_department', []):
            data.append([
                dept.get('department_name', 'Sin departamento'),
                f"${dept.get('total_amount', 0):.2f}",
                str(dept.get('num_items', 0)),
                f"{dept.get('percentage', 0):.2f}%"
            ])
        
        # Add table to elements if there is data
        if len(data) > 1:
            table = self._create_table(data, [200, 100, 100, 100])
            elements.append(table)
        else:
            elements.append(Paragraph("No hay datos disponibles para este período.", styles['Normal']))
        
        elements.append(Spacer(1, 0.3*inch))
        return elements

    def _create_sales_by_customer_report(self, report_data: Dict[str, Any]) -> List:
        """Create the sales by customer report content."""
        styles = getSampleStyleSheet()
        elements = []
        
        # Report summary
        summary_text = f"""
        <b>Período:</b> {report_data.get('start_date', '')} al {report_data.get('end_date', '')}<br/>
        <b>Total ventas:</b> ${report_data.get('total_revenue', 0):.2f}<br/>
        """
        summary = Paragraph(summary_text, styles['Normal'])
        elements.append(summary)
        elements.append(Spacer(1, 0.2*inch))
        
        # Sales by customer table header
        elements.append(Paragraph("<b>Ventas por cliente:</b>", styles['Heading3']))
        
        # Sales by customer table data
        data = [['Cliente', 'Total Ventas', 'Número de Ventas', '% del Total']]
        for customer in report_data.get('sales_by_customer', []):
            data.append([
                customer.get('customer_name', 'Consumidor Final'),
                f"${customer.get('total_amount', 0):.2f}",
                str(customer.get('num_sales', 0)),
                f"{customer.get('percentage', 0):.2f}%"
            ])
        
        # Add table to elements if there is data
        if len(data) > 1:
            table = self._create_table(data, [200, 100, 100, 100])
            elements.append(table)
        else:
            elements.append(Paragraph("No hay datos disponibles para este período.", styles['Normal']))
        
        elements.append(Spacer(1, 0.3*inch))
        return elements

    def _create_top_products_report(self, report_data: Dict[str, Any]) -> List:
        """Create the top products report content."""
        styles = getSampleStyleSheet()
        elements = []
        
        # Report summary
        summary_text = f"""
        <b>Período:</b> {report_data.get('start_date', '')} al {report_data.get('end_date', '')}<br/>
        <b>Total ventas:</b> ${report_data.get('total_revenue', 0):.2f}<br/>
        """
        summary = Paragraph(summary_text, styles['Normal'])
        elements.append(summary)
        elements.append(Spacer(1, 0.2*inch))
        
        # Top products table header
        elements.append(Paragraph("<b>Productos más vendidos:</b>", styles['Heading3']))
        
        # Top products table data
        data = [['Código', 'Descripción', 'Cantidad', 'Total', '% del Total']]
        for product in report_data.get('top_products', []):
            data.append([
                product.get('product_code', ''),
                product.get('product_description', ''),
                str(product.get('quantity_sold', 0)),
                f"${product.get('total_amount', 0):.2f}",
                f"{product.get('percentage', 0):.2f}%"
            ])
        
        # Add table to elements if there is data
        if len(data) > 1:
            table = self._create_table(data, [80, 220, 70, 80, 80])
            elements.append(table)
        else:
            elements.append(Paragraph("No hay datos disponibles para este período.", styles['Normal']))
        
        elements.append(Spacer(1, 0.3*inch))
        return elements

    def _create_profit_analysis_report(self, report_data: Dict[str, Any]) -> List:
        """Create the profit analysis report content."""
        styles = getSampleStyleSheet()
        elements = []
        
        # Report summary
        summary_text = f"""
        <b>Período:</b> {report_data.get('start_date', '')} al {report_data.get('end_date', '')}<br/>
        <b>Total ingresos:</b> ${report_data.get('total_revenue', 0):.2f}<br/>
        <b>Total costos:</b> ${report_data.get('total_cost', 0):.2f}<br/>
        <b>Ganancia:</b> ${report_data.get('total_profit', 0):.2f}<br/>
        <b>Margen de ganancia:</b> {report_data.get('profit_margin', 0):.2f}%<br/>
        """
        summary = Paragraph(summary_text, styles['Normal'])
        elements.append(summary)
        elements.append(Spacer(1, 0.3*inch))
        
        # Add department profit breakdown if available
        if 'department_profit' in report_data:
            elements.append(Paragraph("<b>Desglose por departamento:</b>", styles['Heading3']))
            dept_data = [['Departamento', 'Ingresos', 'Costos', 'Ganancia', 'Margen']]
            for dept in report_data.get('department_profit', []):
                dept_data.append([
                    dept.get('department_name', 'Sin departamento'),
                    f"${dept.get('revenue', 0):.2f}",
                    f"${dept.get('cost', 0):.2f}",
                    f"${dept.get('profit', 0):.2f}",
                    f"{dept.get('margin', 0):.2f}%"
                ])
            
            if len(dept_data) > 1:
                dept_table = self._create_table(dept_data, [160, 100, 100, 100, 80])
                elements.append(dept_table)
            
            elements.append(Spacer(1, 0.3*inch))
        
        return elements

    def _create_cash_drawer_report(self, report_data: Dict[str, Any]) -> List:
        """Create a cash drawer report document."""
        styles = getSampleStyleSheet()
        elements = []
        
        # Extract data
        drawer_id = report_data.get('drawer_id', 'N/A')
        is_open = report_data.get('is_open', False)
        current_balance = report_data.get('current_balance', 0)
        initial_amount = report_data.get('initial_amount', 0)
        total_in = report_data.get('total_in', 0)
        total_out = report_data.get('total_out', 0)
        opened_at = report_data.get('opened_at', '')
        opened_by = report_data.get('opened_by', '')
        entries = report_data.get('entries', [])
        
        # Format date if it's a datetime object
        if isinstance(opened_at, datetime):
            opened_at = opened_at.strftime('%d/%m/%Y %H:%M:%S')
        
        # Create summary section
        status_text = "Abierta" if is_open else "Cerrada"
        summary_text = f"""
        <b>ID de Caja:</b> {drawer_id}<br/>
        <b>Estado:</b> {status_text}<br/>
        <b>Fecha de Apertura:</b> {opened_at}<br/>
        <b>Abierta por Usuario:</b> {opened_by}<br/>
        <b>Monto Inicial:</b> ${initial_amount:.2f}<br/>
        <b>Total Ingresos:</b> ${total_in:.2f}<br/>
        <b>Total Retiros:</b> ${total_out:.2f}<br/>
        <b>Saldo Actual:</b> ${current_balance:.2f}<br/>
        """
        
        summary = Paragraph(summary_text, styles['Normal'])
        elements.append(summary)
        elements.append(Spacer(1, 0.2*inch))
        
        # Create entries table
        if entries:
            elements.append(Paragraph("<b>Movimientos de Caja:</b>", styles['Heading3']))
            
            # Table header
            data = [['ID', 'Fecha/Hora', 'Tipo', 'Monto', 'Descripción', 'Usuario']]
            
            # Format entry data for table
            for entry in entries:
                entry_id = entry.get('id', getattr(entry, 'id', ''))
                timestamp = entry.get('timestamp', getattr(entry, 'timestamp', ''))
                
                # Format timestamp if it's a datetime
                if isinstance(timestamp, datetime):
                    timestamp = timestamp.strftime('%d/%m/%Y %H:%M:%S')
                
                # Get entry type
                entry_type = entry.get('entry_type', getattr(entry, 'entry_type', ''))
                if hasattr(entry_type, 'name'):
                    entry_type = entry_type.name
                
                # Map entry type to human-readable format
                type_map = {
                    'START': 'Apertura',
                    'IN': 'Ingreso',
                    'OUT': 'Retiro'
                }
                entry_type_display = type_map.get(entry_type, entry_type)
                
                # Get amount and format it
                amount = entry.get('amount', getattr(entry, 'amount', 0))
                # Format amount as currency with 2 decimal places
                if isinstance(amount, (int, float)):
                    amount_display = f"${amount:.2f}"
                else:
                    amount_display = str(amount)
                
                # Get other fields
                description = entry.get('description', getattr(entry, 'description', ''))
                user_id = entry.get('user_id', getattr(entry, 'user_id', ''))
                
                # Add row to table
                data.append([
                    str(entry_id),
                    str(timestamp),
                    entry_type_display,
                    amount_display,
                    description,
                    str(user_id)
                ])
            
            # Create table with appropriate column widths
            table = self._create_table(data, [40, 150, 80, 80, 200, 60])
            elements.append(table)
        else:
            elements.append(Paragraph("No hay movimientos registrados.", styles['Normal']))
        
        elements.append(Spacer(1, 0.3*inch))
        return elements

    def _create_corte_report(self, report_data: Dict[str, Any]) -> List:
        """Create a cash register "corte" report."""
        styles = getSampleStyleSheet()
        elements = []
        
        # Add date range
        date_range_text = f"""
        <b>Período:</b> {report_data.get('start_date', '')} al {report_data.get('end_date', '')}<br/>
        """
        elements.append(Paragraph(date_range_text, styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Sales summary section
        elements.append(Paragraph("<b>Resumen de Ventas</b>", styles['Heading3']))
        
        # Create a table for sales summary
        data = [
            ['Total de ventas:', f"${report_data.get('total_sales', 0):.2f}"],
            ['Número de ventas:', str(report_data.get('num_sales', 0))]
        ]
        
        # Add payment type breakdown to the table
        elements.append(Paragraph("<b>Ventas por Forma de Pago</b>", styles['Heading3']))
        
        payment_types = report_data.get('sales_by_payment_type', {})
        for payment_type, amount in payment_types.items():
            data.append([f"{payment_type}:", f"${amount:.2f}"])
        
        table = Table(data, colWidths=[200, 150])
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Cash drawer section
        elements.append(Paragraph("<b>Caja</b>", styles['Heading3']))
        
        # Cash drawer summary table
        cash_data = [
            ['Saldo inicial:', f"${report_data.get('starting_balance', 0):.2f}"],
            ['Ventas en efectivo:', f"${report_data.get('cash_sales', 0):.2f}"],
            ['Entradas de efectivo:', f"${report_data.get('cash_in_total', 0):.2f}"],
            ['Salidas de efectivo:', f"${report_data.get('cash_out_total', 0):.2f}"],
            ['Efectivo esperado en caja:', f"${report_data.get('expected_cash', 0):.2f}"],
            ['Efectivo real en caja:', f"${report_data.get('actual_cash', 0):.2f}"],
            ['Diferencia:', f"${report_data.get('difference', 0):.2f}"]
        ]
        
        cash_table = Table(cash_data, colWidths=[200, 150])
        cash_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BACKGROUND', (0, 4), (0, 4), colors.lightgrey),  # Highlight expected cash row
            ('BACKGROUND', (1, 4), (1, 4), colors.lightgrey),
            ('TEXTCOLOR', (0, 6), (1, 6), 
                colors.red if report_data.get('difference', 0) < 0 else 
                colors.green if report_data.get('difference', 0) > 0 else 
                colors.black),  # Color difference based on value
        ]))
        elements.append(cash_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Cash movements sections
        if report_data.get('cash_in_entries'):
            elements.append(Paragraph("<b>Entradas de Efectivo</b>", styles['Heading3']))
            
            # Cash in entries table
            cash_in_header = ['Hora', 'Tipo', 'Monto', 'Descripción', 'Usuario']
            cash_in_data = [cash_in_header]
            
            for entry in report_data['cash_in_entries']:
                timestamp = entry.get('timestamp', '')
                if isinstance(timestamp, datetime):
                    timestamp = timestamp.strftime('%H:%M:%S')
                
                # Get entry type
                entry_type = entry.get('entry_type', '')
                if hasattr(entry_type, 'name'):
                    entry_type = entry_type.name
                
                # Map entry type to human-readable format
                type_map = {
                    'START': 'Apertura',
                    'IN': 'Ingreso',
                    'OUT': 'Retiro'
                }
                entry_type_display = type_map.get(entry_type, entry_type)
                
                # Get amount
                amount = entry.get('amount', 0)
                if isinstance(amount, (int, float)):
                    amount_display = f"${amount:.2f}"
                else:
                    amount_display = str(amount)
                
                cash_in_data.append([
                    str(timestamp),
                    entry_type_display,
                    amount_display,
                    entry.get('description', ''),
                    str(entry.get('user_id', ''))
                ])
            
            if len(cash_in_data) > 1:
                cash_in_table = Table(cash_in_data, colWidths=[80, 80, 80, 200, 60])
                cash_in_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
                    ('ALIGN', (2, 0), (2, -1), 'RIGHT'),  # Align amounts to right
                ]))
                elements.append(cash_in_table)
            else:
                elements.append(Paragraph("No hay entradas de efectivo registradas.", styles['Normal']))
            
            elements.append(Spacer(1, 0.2*inch))
        
        if report_data.get('cash_out_entries'):
            elements.append(Paragraph("<b>Salidas de Efectivo</b>", styles['Heading3']))
            
            # Cash out entries table
            cash_out_header = ['Hora', 'Tipo', 'Monto', 'Descripción', 'Usuario']
            cash_out_data = [cash_out_header]
            
            for entry in report_data['cash_out_entries']:
                timestamp = entry.get('timestamp', '')
                if isinstance(timestamp, datetime):
                    timestamp = timestamp.strftime('%H:%M:%S')
                
                # Get entry type
                entry_type = entry.get('entry_type', '')
                if hasattr(entry_type, 'name'):
                    entry_type = entry_type.name
                
                # Map entry type to human-readable format
                type_map = {
                    'START': 'Apertura',
                    'IN': 'Ingreso',
                    'OUT': 'Retiro'
                }
                entry_type_display = type_map.get(entry_type, entry_type)
                
                # Get amount
                amount = entry.get('amount', 0)
                if isinstance(amount, (int, float)):
                    amount_display = f"${abs(amount):.2f}"
                else:
                    amount_display = str(abs(float(amount)))
                
                cash_out_data.append([
                    str(timestamp),
                    entry_type_display,
                    amount_display,
                    entry.get('description', ''),
                    str(entry.get('user_id', ''))
                ])
            
            if len(cash_out_data) > 1:
                cash_out_table = Table(cash_out_data, colWidths=[80, 80, 80, 200, 60])
                cash_out_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
                    ('ALIGN', (2, 0), (2, -1), 'RIGHT'),  # Align amounts to right
                ]))
                elements.append(cash_out_table)
            else:
                elements.append(Paragraph("No hay salidas de efectivo registradas.", styles['Normal']))
        
        return elements

    def _create_table(self, data: List[List], col_widths: List[int]) -> Table:
        """Create a styled table with the provided data."""
        table = Table(data, colWidths=col_widths)
        
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),  # Left-align descriptions
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),  # Right-align numbers
        ])
        
        table.setStyle(table_style)
        return table

    def _create_footer(self) -> List:
        """Create a footer for the report."""
        styles = getSampleStyleSheet()
        elements = []
        
        elements.append(Spacer(1, 0.5*inch))
        
        footer_style = ParagraphStyle(
            'Footer', 
            parent=styles['Normal'], 
            fontSize=8,
            textColor=colors.gray,
            alignment=TA_CENTER
        )
        
        footer_text = f"Reporte generado por Eleventa - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        footer = Paragraph(footer_text, footer_style)
        elements.append(footer)
        
        return elements 