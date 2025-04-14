from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfgen import canvas
import os
from datetime import datetime
import locale
from decimal import Decimal
from typing import Dict, Any, List, Optional

# Set locale for date and currency formatting
try:
    locale.setlocale(locale.LC_ALL, 'es_AR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')  # Fallback
    except:
        locale.setlocale(locale.LC_ALL, '')  # Use default locale

class InvoiceBuilder:
    """Class to generate Argentinian-style invoice PDFs."""

    def __init__(self, store_info: Dict[str, str]):
        """
        Initialize with store information.
        
        Args:
            store_info: Dictionary containing store details like name, address, CUIT, etc.
        """
        self.store_info = store_info
        self.styles = getSampleStyleSheet()
        
        # Define custom styles
        self.styles.add(ParagraphStyle(
            name='InvoiceTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            alignment=1,  # Centered
        ))
        
        self.styles.add(ParagraphStyle(
            name='InvoiceInfo',
            parent=self.styles['Normal'],
            fontSize=10,
        ))
        
        self.styles.add(ParagraphStyle(
            name='ItemsTableHeader',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
        ))

    def generate_invoice_pdf(
        self, 
        invoice_data: Dict[str, Any], 
        sale_items: List[Dict[str, Any]], 
        filename: str
    ) -> bool:
        """
        Generate a PDF invoice with Argentinian format.
        
        Args:
            invoice_data: Invoice details (number, date, customer info, etc.)
            sale_items: List of dictionaries with item details (code, desc, qty, price, etc.)
            filename: Path where to save the PDF
            
        Returns:
            bool: True if PDF generation was successful, False otherwise
        """
        try:
            # Create the PDF document
            doc = SimpleDocTemplate(
                filename,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Initialize elements list for the PDF content
            elements = []
            
            # Add invoice header
            elements.extend(self._create_header(invoice_data))
            
            # Add customer information
            elements.extend(self._create_customer_section(invoice_data))
            
            # Add items table
            elements.extend(self._create_items_table(sale_items))
            
            # Add totals
            elements.extend(self._create_totals(invoice_data))
            
            # Add footer with legal text
            elements.extend(self._create_footer(invoice_data))
            
            # Build the PDF
            doc.build(elements)
            return True
            
        except Exception as e:
            print(f"Error generating invoice PDF: {e}")
            return False
    
    def _create_header(self, invoice_data: Dict[str, Any]) -> List:
        """Create the invoice header section."""
        elements = []
        
        # Store name and logo would go here if available
        header_text = f"<b>{self.store_info.get('name', 'EMPRESA')}</b>"
        elements.append(Paragraph(header_text, self.styles['InvoiceTitle']))
        
        # Add store info
        store_info = [
            f"<b>Domicilio:</b> {self.store_info.get('address', '')}",
            f"<b>CUIT:</b> {self.store_info.get('cuit', '')}",
            f"<b>Condición IVA:</b> {self.store_info.get('iva_condition', 'Responsable Inscripto')}"
        ]
        
        for line in store_info:
            elements.append(Paragraph(line, self.styles['InvoiceInfo']))
        
        # Add invoice type and number
        invoice_type = invoice_data.get('invoice_type', 'B')
        elements.append(Spacer(1, 0.5*cm))
        
        invoice_title = f"FACTURA {invoice_type}"
        elements.append(Paragraph(invoice_title, self.styles['InvoiceTitle']))
        
        number_text = f"N°: {invoice_data.get('invoice_number', '')}"
        elements.append(Paragraph(number_text, self.styles['InvoiceInfo']))
        
        # Add invoice date
        date_str = invoice_data.get('invoice_date', datetime.now()).strftime('%d/%m/%Y')
        date_text = f"Fecha: {date_str}"
        elements.append(Paragraph(date_text, self.styles['InvoiceInfo']))
        
        elements.append(Spacer(1, 1*cm))
        return elements
    
    def _create_customer_section(self, invoice_data: Dict[str, Any]) -> List:
        """Create the customer information section."""
        elements = []
        
        # Get customer details from invoice data
        customer_details = invoice_data.get('customer_details', {})
        
        # Create customer info section
        customer_section = [
            ["Cliente:", customer_details.get('name', '')],
            ["CUIT:", customer_details.get('cuit', '')],
            ["Domicilio:", customer_details.get('address', '')],
            ["Condición frente al IVA:", customer_details.get('iva_condition', 'Consumidor Final')]
        ]
        
        # Create table for customer info
        customer_table = Table(customer_section, colWidths=[100, 350])
        customer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(customer_table)
        elements.append(Spacer(1, 1*cm))
        return elements
    
    def _create_items_table(self, sale_items: List[Dict[str, Any]]) -> List:
        """Create the invoice items table."""
        elements = []
        
        # Define column headers and widths
        headers = ["Código", "Descripción", "Cantidad", "Precio Unit.", "Subtotal"]
        col_widths = [80, 220, 60, 80, 80]
        
        # Create data rows from sale items
        data = [headers]
        
        for item in sale_items:
            qty = item.get('quantity', 0)
            unit_price = item.get('unit_price', Decimal('0'))
            subtotal = qty * unit_price
            
            row = [
                item.get('code', ''),
                item.get('description', ''),
                f"{qty:.2f}",
                f"${unit_price:.2f}",
                f"${subtotal:.2f}"
            ]
            data.append(row)
        
        # Create the table
        items_table = Table(data, colWidths=col_widths)
        
        # Apply table styles
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ]))
        
        elements.append(items_table)
        elements.append(Spacer(1, 0.5*cm))
        return elements
    
    def _create_totals(self, invoice_data: Dict[str, Any]) -> List:
        """Create the totals section of the invoice."""
        elements = []
        
        # Get financial data
        subtotal = invoice_data.get('subtotal', Decimal('0'))
        iva_amount = invoice_data.get('iva_amount', Decimal('0'))
        total = invoice_data.get('total', Decimal('0'))
        
        # Create totals rows
        totals_data = []
        
        # For Type A invoices, show IVA separately
        if invoice_data.get('invoice_type') == 'A':
            totals_data = [
                ["", "", "", "Subtotal:", f"${subtotal:.2f}"],
                ["", "", "", "IVA (21%):", f"${iva_amount:.2f}"],
                ["", "", "", "TOTAL:", f"${total:.2f}"]
            ]
        else:
            # For Type B/C, only show the total
            totals_data = [
                ["", "", "", "TOTAL:", f"${total:.2f}"]
            ]
        
        # Create the table with same column widths as items table
        totals_table = Table(totals_data, colWidths=[80, 220, 60, 80, 80])
        
        # Apply styles
        totals_table.setStyle(TableStyle([
            ('FONTNAME', (3, 0), (3, -1), 'Helvetica-Bold'),
            ('FONTNAME', (4, -1), (4, -1), 'Helvetica-Bold'),  # Make the final total bold
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (3, 0), (4, -1), 'RIGHT'),
            ('LINEABOVE', (3, -1), (4, -1), 1, colors.black),  # Line above final total
        ]))
        
        elements.append(totals_table)
        elements.append(Spacer(1, 1*cm))
        return elements
    
    def _create_footer(self, invoice_data: Dict[str, Any]) -> List:
        """Create the invoice footer with legal information."""
        elements = []
        
        # Add CAE information if available
        cae = invoice_data.get('cae')
        cae_due_date = invoice_data.get('cae_due_date')
        
        if cae and cae_due_date:
            cae_text = f"CAE N°: {cae}"
            elements.append(Paragraph(cae_text, self.styles['InvoiceInfo']))
            
            due_date_str = cae_due_date.strftime('%d/%m/%Y')
            due_date_text = f"Fecha de Vto. de CAE: {due_date_str}"
            elements.append(Paragraph(due_date_text, self.styles['InvoiceInfo']))
        
        # Add generic footer text
        elements.append(Spacer(1, 0.5*cm))
        footer_text = "Documento no válido como factura"
        if invoice_data.get('is_active', True):
            footer_text = "Documento válido como factura"
            
        elements.append(Paragraph(footer_text, self.styles['InvoiceInfo']))
        
        return elements