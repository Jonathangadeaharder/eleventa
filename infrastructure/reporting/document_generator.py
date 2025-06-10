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
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
import logging # Added import

from config import Config # For store_info defaults

# Set locale for date and currency formatting
try:
    locale.setlocale(locale.LC_ALL, 'es_AR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')  # Fallback
    except:
        locale.setlocale(locale.LC_ALL, '')  # Use default locale

class DocumentPdfGenerator:
    """Class to generate various transactional documents like invoices, receipts, etc."""

    def __init__(self, store_info: Optional[Dict[str, str]] = None):
        """
        Initialize with store information.
        
        Args:
            store_info: Dictionary containing store details like name, address, CUIT, etc.
                       If None, it will try to load from Config.
        """
        self.logger = logging.getLogger(self.__class__.__name__) # Added logger
        if store_info is None:
            # Get values from Config, but use defaults if Config values are None
            store_name = getattr(Config, 'STORE_NAME', None)
            store_address = getattr(Config, 'STORE_ADDRESS', None)
            store_phone = getattr(Config, 'STORE_PHONE', None)
            store_cuit = getattr(Config, 'STORE_CUIT', None)
            store_iva_condition = getattr(Config, 'STORE_IVA_CONDITION', None)
            store_logo_path = getattr(Config, 'STORE_LOGO_PATH', None)
            
            self.store_info = {
                "name": store_name if store_name is not None else "Eleventa Demo Store",
                "address": store_address if store_address is not None else "123 Main St, Buenos Aires, Argentina",
                "phone": store_phone if store_phone is not None else "555-1234",
                "cuit": store_cuit if store_cuit is not None else "30-12345678-9",
                "iva_condition": store_iva_condition if store_iva_condition is not None else "Responsable Inscripto",
                "logo_path": store_logo_path
            }
        else:
            self.store_info = store_info
            
        self.styles = getSampleStyleSheet()
        
        # Define custom styles (can be expanded or made more generic)
        self.styles.add(ParagraphStyle(
            name='DocTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            alignment=1,  # Centered
        ))
        
        self.styles.add(ParagraphStyle(
            name='DocInfo',
            parent=self.styles['Normal'],
            fontSize=10,
        ))
        
        self.styles.add(ParagraphStyle(
            name='ItemsTableHeader',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
        ))
        self.styles.add(ParagraphStyle(
            name='RightAlign',
            parent=self.styles['Normal'],
            alignment=TA_RIGHT, # type: ignore
        ))
        self.styles.add(ParagraphStyle(
            name='BoldRightAlign',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            alignment=TA_RIGHT, # type: ignore
        ))


    def _ensure_directory_exists(self, filename: str):
        """Ensure the directory for the given filename exists."""
        try:
            abs_filename = os.path.abspath(filename)
            output_dir = os.path.dirname(abs_filename)
            
            # Validate the path - check if it's a reasonable path
            if not filename or len(filename.strip()) == 0:
                raise OSError("Invalid filename: empty or whitespace only")
            
            # Check for invalid characters or patterns that would make directory creation fail
            if os.name == 'nt':  # Windows
                invalid_chars = '<>"|?*'
                # For Windows, we need to be more careful about colons - they're valid in drive letters
                # Check for invalid chars, but skip the drive letter colon
                path_to_check = output_dir
                if len(output_dir) > 1 and output_dir[1] == ':':
                    # Skip the drive letter part (e.g., "C:")
                    path_to_check = output_dir[2:]
                
                if any(char in path_to_check for char in invalid_chars):
                    raise OSError(f"Invalid characters in path: {output_dir}")
            
            os.makedirs(output_dir, exist_ok=True)
        except (OSError, PermissionError) as e:
            self.logger.error(f"Cannot create directory for {filename}: {e}")
            raise

    # --- Invoice Generation Methods (Adapted from InvoiceBuilder) ---

    def generate_invoice_pdf(
        self, 
        invoice_data: Dict[str, Any], 
        sale_items: List[Dict[str, Any]], 
        filename: str
    ) -> bool:
        """
        Generate a PDF invoice.
        
        Args:
            invoice_data: Invoice details (number, date, customer info, etc.)
            sale_items: List of dictionaries with item details (code, desc, qty, price, etc.)
            filename: Absolute path where to save the PDF. Directory will be created if it doesn't exist.
            
        Returns:
            bool: True if PDF generation was successful, False otherwise
        """
        try:
            # Validate input data
            if not invoice_data:
                self.logger.error("Invoice data cannot be empty")
                return False
                
            # Check for required fields
            required_fields = ['invoice_number', 'total']
            for field in required_fields:
                if field not in invoice_data:
                    self.logger.error(f"Missing required field: {field}")
                    return False
            
            # Check for customer information (either 'customer' or 'customer_details')
            if 'customer' not in invoice_data and 'customer_details' not in invoice_data:
                self.logger.error("Missing required field: customer information")
                return False
            
            self._ensure_directory_exists(filename)
            
            doc = SimpleDocTemplate(
                filename,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            elements = []
            elements.extend(self._create_invoice_header(invoice_data))
            elements.extend(self._create_invoice_customer_section(invoice_data))
            elements.extend(self._create_invoice_items_table(sale_items))
            elements.extend(self._create_invoice_totals(invoice_data))
            elements.extend(self._create_invoice_footer(invoice_data))
            
            doc.build(elements)
            return True
            
        except Exception as e:
            # Consider logging here instead of print
            self.logger.error(f"Error generating invoice PDF: {e}") # Changed from print
            return False
    
    def _create_invoice_header(self, invoice_data: Dict[str, Any]) -> List:
        elements = []
        
        # Store name and logo
        if self.store_info.get("logo_path") and os.path.exists(self.store_info["logo_path"]):
            try:
                logo = Image(self.store_info["logo_path"], width=1.5*inch, height=0.75*inch) # Adjust size as needed
                logo.hAlign = 'LEFT'
                elements.append(logo)
            except Exception as e:
                self.logger.warning(f"Could not load logo: {e}") # Changed from print, non-critical
        
        header_text = f"<b>{self.store_info.get('name', 'EMPRESA')}</b>"
        elements.append(Paragraph(header_text, self.styles['DocTitle']))
        
        store_info_lines = [
            f"<b>Domicilio:</b> {self.store_info.get('address', '')}",
            f"<b>CUIT:</b> {self.store_info.get('cuit', '')}",
            f"<b>Condición IVA:</b> {self.store_info.get('iva_condition', 'Responsable Inscripto')}"
        ]
        for line in store_info_lines:
            elements.append(Paragraph(line, self.styles['DocInfo']))
        
        invoice_type = invoice_data.get('invoice_type', 'B')
        elements.append(Spacer(1, 0.5*cm))
        
        invoice_title = f"FACTURA {invoice_type}"
        elements.append(Paragraph(invoice_title, self.styles['DocTitle']))
        
        number_text = f"N°: {invoice_data.get('invoice_number', '')}"
        elements.append(Paragraph(number_text, self.styles['DocInfo']))
        
        invoice_date_obj = invoice_data.get('invoice_date', datetime.now())
        if isinstance(invoice_date_obj, str):
            try:
                invoice_date_obj = datetime.fromisoformat(invoice_date_obj)
            except ValueError: # Fallback for other string formats if necessary
                pass # Keep as string if parsing fails

        date_str = invoice_date_obj.strftime('%d/%m/%Y') if isinstance(invoice_date_obj, datetime) else str(invoice_date_obj)
        date_text = f"Fecha: {date_str}"
        elements.append(Paragraph(date_text, self.styles['DocInfo']))
        
        elements.append(Spacer(1, 1*cm))
        return elements
    
    def _create_invoice_customer_section(self, invoice_data: Dict[str, Any]) -> List:
        elements = []
        customer_details = invoice_data.get('customer_details', {})
        
        customer_section_data = [
            [Paragraph("<b>Cliente:</b>", self.styles['DocInfo']), Paragraph(customer_details.get('name', ''), self.styles['DocInfo'])],
            [Paragraph("<b>CUIT:</b>", self.styles['DocInfo']), Paragraph(customer_details.get('cuit', ''), self.styles['DocInfo'])],
            [Paragraph("<b>Domicilio:</b>", self.styles['DocInfo']), Paragraph(customer_details.get('address', ''), self.styles['DocInfo'])],
            [Paragraph("<b>Condición frente al IVA:</b>", self.styles['DocInfo']), Paragraph(customer_details.get('iva_condition', 'Consumidor Final'), self.styles['DocInfo'])]
        ]
        
        customer_table = Table(customer_section_data, colWidths=[2.5*cm, None]) # Adjust first col width
        customer_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2), # Reduced padding
        ]))
        
        elements.append(customer_table)
        elements.append(Spacer(1, 0.5*cm)) # Reduced spacer
        return elements
    
    def _create_invoice_items_table(self, sale_items: List[Dict[str, Any]]) -> List:
        elements = []
        headers = ["Código", "Descripción", "Cantidad", "Precio Unit.", "Subtotal"]
        
        data = [[Paragraph(h, self.styles['ItemsTableHeader']) for h in headers]]
        
        for item in sale_items:
            qty = Decimal(str(item.get('quantity', 0)))
            unit_price = Decimal(str(item.get('unit_price', '0')))
            subtotal = qty * unit_price
            
            row = [
                Paragraph(str(item.get('product_code', '')), self.styles['DocInfo']), # Was item.get('code', '')
                Paragraph(str(item.get('product_description', '')), self.styles['DocInfo']), # Was item.get('description', '')
                Paragraph(f"{qty:.2f}", self.styles['RightAlign']),
                Paragraph(f"${unit_price:.2f}", self.styles['RightAlign']),
                Paragraph(f"${subtotal:.2f}", self.styles['RightAlign'])
            ]
            data.append(row)
        
        items_table = Table(data, colWidths=[1.5*cm, 6*cm, 2*cm, 2.5*cm, 2.5*cm]) # Adjusted widths
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9), # Reduced font size
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6), # Reduced padding
            ('TOPPADDING', (0, 0), (-1, 0), 6), # Reduced padding
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        
        elements.append(items_table)
        elements.append(Spacer(1, 0.5*cm))
        return elements
    
    def _create_invoice_totals(self, invoice_data: Dict[str, Any]) -> List:
        elements = []
        
        subtotal = Decimal(str(invoice_data.get('subtotal', '0')))
        iva_amount = Decimal(str(invoice_data.get('iva_amount', '0')))
        total = Decimal(str(invoice_data.get('total', '0')))
        
        totals_data = []
        col_widths = [1.5*cm, 6*cm, 2*cm, 2.5*cm, 2.5*cm] # Match items table

        # For Type A invoices, show IVA separately
        if invoice_data.get('invoice_type') == 'A':
            totals_data = [
                ['', '', '', Paragraph("Subtotal:", self.styles['BoldRightAlign']), Paragraph(f"${subtotal:.2f}", self.styles['RightAlign'])],
                ['', '', '', Paragraph("IVA (21%):", self.styles['BoldRightAlign']), Paragraph(f"${iva_amount:.2f}", self.styles['RightAlign'])],
                ['', '', '', Paragraph("TOTAL:", self.styles['BoldRightAlign']), Paragraph(f"${total:.2f}", self.styles['BoldRightAlign'])]
            ]
        else: # For Type B/C, only show the total
            totals_data = [
                ['', '', '', Paragraph("TOTAL:", self.styles['BoldRightAlign']), Paragraph(f"${total:.2f}", self.styles['BoldRightAlign'])]
            ]
        
        totals_table = Table(totals_data, colWidths=col_widths)
        style_commands = [
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('TOPPADDING', (0,0), (-1,-1), 2),
        ]
        # Span the empty cells in each row of totals
        for i in range(len(totals_data)):
            style_commands.append(('SPAN', (0, i), (2, i)))
            # Align text in the descriptor cells (e.g., "Subtotal:") to the right
            style_commands.append(('ALIGN', (3,i), (3,i), 'RIGHT'))
            # Align text in the value cells (e.g., "$100.00") to the right
            style_commands.append(('ALIGN', (4,i), (4,i), 'RIGHT'))

        totals_table.setStyle(TableStyle(style_commands))
        
        elements.append(totals_table)
        elements.append(Spacer(1, 0.5*cm))
        return elements

    def _create_invoice_footer(self, invoice_data: Dict[str, Any]) -> List:
        elements = []
        # Placeholder for CAE, Vto, etc. for Argentinian invoices
        # This can be expanded based on specific requirements
        footer_text_lines = [
            "Comprobante autorizado",
            # "CAE N°: XXXXXXXXXXXXXX",
            # "Fecha de Vto. de CAE: DD/MM/AAAA",
        ]
        for line in footer_text_lines:
            elements.append(Paragraph(line, self.styles['DocInfo']))
        
        elements.append(Spacer(1, 1*cm))
        # AFIP QR Code could be added here if required
        # afip_qr_text = invoice_data.get('afip_qr_data', None)
        # if afip_qr_text:
        #     try:
        #         import qrcode # type: ignore
        #         from reportlab.graphics.shapes import Image as ReportLabImage # Renamed to avoid conflict
        #         from io import BytesIO

        #         qr_img = qrcode.make(afip_qr_text)
        #         img_buffer = BytesIO()
        #         qr_img.save(img_buffer, format='PNG')
        #         img_buffer.seek(0)
                
        #         # Convert PIL Image to ReportLab Image
        #         # Need to use a flowable image for ReportLab
        #         # The Image class from reportlab.platypus is what we need
        #         reportlab_qr_image = Image(img_buffer, width=2*cm, height=2*cm)
        #         elements.append(reportlab_qr_image)
        #     except ImportError:
        #         elements.append(Paragraph("QR Code (qrcode library not installed)", self.styles['DocInfo']))
        #     except Exception as e:
        #         elements.append(Paragraph(f"Error generating QR: {e}", self.styles['DocInfo']))

        return elements

    # --- Receipt Generation Methods (Adapted from receipt_builder.py and SaleService) ---
    def _format_currency_receipt(self, amount_value: Any) -> str:
        amount = Decimal(str(amount_value)) if not isinstance(amount_value, Decimal) else amount_value
        if amount < 0:
            return "-${:,.2f}".format(abs(amount))
        return "${:,.2f}".format(amount)

    def _format_sale_date_receipt(self, date_obj: Any) -> str:
        if isinstance(date_obj, str):
            try: # Attempt to parse if it's a string, e.g. from Pydantic model
                dt = datetime.fromisoformat(date_obj)
                return dt.strftime("%d/%m/%Y %H:%M:%S")
            except ValueError:
                return date_obj # Return as is if not a parseable ISO format
        elif isinstance(date_obj, datetime):
            return date_obj.strftime("%d/%m/%Y %H:%M:%S")
        return str(date_obj) # Fallback

    def _format_item_row_receipt(self, item: Dict[str, Any]) -> List[Any]:
        # Ensure quantity and unit_price are Decimals for consistent formatting
        quantity = Decimal(str(item.get('quantity', 0)))
        unit_price = Decimal(str(item.get('unit_price', 0)))
        subtotal = Decimal(str(item.get('subtotal', 0)))

        # Handle potentially missing product_code or product_description
        product_code = str(item.get('product_code', 'N/A'))
        product_description = str(item.get('product_description', 'N/A'))[:30] # Truncate

        return [
            Paragraph(product_code, self.styles['DocInfo']),
            Paragraph(product_description, self.styles['DocInfo']),
            Paragraph(f"{quantity:.0f}" if quantity == quantity.to_integral_value() else f"{quantity:.2f}", self.styles['RightAlign']),
            Paragraph(self._format_currency_receipt(unit_price), self.styles['RightAlign']),
            Paragraph(self._format_currency_receipt(subtotal), self.styles['RightAlign'])
        ]

    def generate_receipt(self, sale_data: Dict[str, Any], filename: str) -> bool:
        """
        Generate a PDF receipt for a sale.
        
        Args:
            sale_data: Dictionary containing sale data (id, timestamp, items, total, etc.)
                       Expected keys for items: 'product_code', 'product_description', 'quantity', 'unit_price', 'subtotal'
            filename: Absolute path where to save the PDF.
            
        Returns:
            str: Path to the generated PDF file, or None if failed.
        """
        try:
            # Validate input data
            if not sale_data:
                self.logger.error("Sale data cannot be empty")
                return False
                
            self._ensure_directory_exists(filename)
            
            doc = SimpleDocTemplate(
                filename,
                pagesize=letter,
                rightMargin=0.5*inch, leftMargin=0.5*inch,
                topMargin=0.5*inch, bottomMargin=0.5*inch
            )
            
            elements = []
            
            # Store information
            elements.append(Paragraph(self.store_info.get('name', 'Store Name'), self.styles['DocTitle'])) # Use DocTitle
            elements.append(Paragraph(f"Dirección: {self.store_info.get('address', '')}", self.styles['DocInfo']))
            elements.append(Paragraph(f"Teléfono: {self.store_info.get('phone', '')}", self.styles['DocInfo']))
            if self.store_info.get('cuit'):
                elements.append(Paragraph(f"CUIT: {self.store_info['cuit']}", self.styles['DocInfo']))
            
            elements.append(Spacer(1, 0.1*inch))
            # Use a more generic title, or make it configurable if needed
            elements.append(Paragraph("COMPROBANTE DE VENTA", self.styles.get('ReceiptTitle', self.styles['Heading2']))) 
            elements.append(Spacer(1, 0.1*inch))
            
            # Sale information
            elements.append(Paragraph(f"Venta #: {sale_data.get('id', 'N/A')}", self.styles['DocInfo']))
            elements.append(Paragraph(f"Fecha: {self._format_sale_date_receipt(sale_data.get('timestamp'))}", self.styles['DocInfo']))
            if sale_data.get('user_name'): # Assuming user_name might be added to sale_data by the service
                elements.append(Paragraph(f"Atendido por: {sale_data['user_name']}", self.styles['DocInfo']))
            elements.append(Paragraph(f"Forma de pago: {sale_data.get('payment_type', 'N/A')}", self.styles['DocInfo']))
            if sale_data.get('customer_name'): # Assuming customer_name might be added
                elements.append(Paragraph(f"Cliente: {sale_data['customer_name']}", self.styles['DocInfo']))
                
            elements.append(Spacer(1, 0.2*inch))
            
            # Items table
            headers = ["Código", "Descripción", "Cant.", "Precio", "Importe"]
            table_data = [[Paragraph(h, self.styles['ItemsTableHeader']) for h in headers]]
            
            sale_items = sale_data.get('items', [])
            if not isinstance(sale_items, list):
                self.logger.warning(f"Warning: sale_items is not a list in sale_data: {sale_items}. Skipping items table.") # Changed from print
                sale_items = [] # Default to empty list to avoid further errors

            for item_dict in sale_items:
                # Ensure each item is a dictionary
                if not isinstance(item_dict, dict):
                    self.logger.warning(f"Warning: item in sale_items is not a dict: {item_dict}. Skipping this item.") # Changed from print
                    continue # Skip this item
                
                formatted_row = self._format_item_row_receipt(item_dict)
                table_data.append(formatted_row)

            col_widths = [0.8*inch, 2.5*inch, 0.6*inch, 1.0*inch, 1.0*inch] # Adjusted for Paragraphs
            item_table = Table(table_data, colWidths=col_widths)
            item_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), #Already in ItemsTableHeader style
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.black)
            ]))
            elements.append(item_table)
            elements.append(Spacer(1, 0.2*inch))
            
            # Total
            total_amount_val = sale_data.get('total', Decimal('0')) # Prefer 'total' from Sale model
            if not total_amount_val and sale_items: # Fallback to sum items if total is not directly available
                calculated_total = sum(Decimal(str(it.get('subtotal', '0'))) for it in sale_items if isinstance(it, dict))
                total_amount_val = calculated_total
            
            total_str = self._format_currency_receipt(total_amount_val)
            elements.append(Paragraph(f"TOTAL: {total_str}", self.styles.get('Total', self.styles['BoldRightAlign']))) # Use BoldRightAlign
            
            elements.append(Spacer(1, 0.3*inch))
            elements.append(Paragraph("¡Gracias por su compra!", self.styles['DocInfo']))
            
            doc.build(elements)
            return True
        except Exception as e:
            self.logger.error(f"Error generating receipt PDF: {e}") # Changed from print
            return False

    # --- Presupuesto Generation Methods (Adapted from SaleService) ---
    def _create_presupuesto_header_footer(self, elements: List, presupuesto_id: Optional[str], user_name: Optional[str], customer_name: Optional[str]):
        """Helper to add header and footer common to presupuesto."""
        # Header part
        elements.append(Paragraph(self.store_info.get('name', 'SU NEGOCIO'), self.styles['DocTitle']))
        elements.append(Paragraph(f"Dirección: {self.store_info.get('address', '')}", self.styles['DocInfo']))
        elements.append(Paragraph(f"Teléfono: {self.store_info.get('phone', '')}", self.styles['DocInfo']))
        if self.store_info.get('cuit'):
            elements.append(Paragraph(f"CUIT: {self.store_info.get('cuit', '')}", self.styles['DocInfo']))
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph("PRESUPUESTO / COTIZACIÓN", self.styles['Heading2']))
        elements.append(Spacer(1, 0.2*inch))

        if presupuesto_id:
            elements.append(Paragraph(f"Presupuesto N°: {presupuesto_id}", self.styles['DocInfo']))
        elements.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", self.styles['DocInfo']))
        if user_name:
            elements.append(Paragraph(f"Atendido por: {user_name}", self.styles['DocInfo']))
        if customer_name:
            elements.append(Paragraph(f"Cliente: {customer_name}", self.styles['DocInfo']))
        elements.append(Spacer(1, 0.2*inch))

    def generate_presupuesto(
        self, 
        items_data: List[Dict[str, Any]], 
        total_amount: Decimal, 
        filename: str, 
        customer_name: Optional[str] = None, 
        user_name: Optional[str] = None, 
        presupuesto_id: Optional[str] = None
    ) -> bool:
        """
        Generate a PDF for a 'Presupuesto' (Quote).

        Args:
            items_data: List of item dictionaries (expected: product_description, quantity, unit_price, subtotal).
            total_amount: The total amount for the presupuesto.
            filename: Absolute path where to save the PDF.
            customer_name: Optional name of the customer.
            user_name: Optional name of the user preparing the quote.
            presupuesto_id: Optional ID for the presupuesto.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Validate input data
            if not items_data:
                self.logger.error("Items data cannot be empty")
                return False
                
            if total_amount is None:
                self.logger.error("Total amount cannot be None")
                return False
                
            self._ensure_directory_exists(filename)
            doc = SimpleDocTemplate(filename, pagesize=letter,
                                    rightMargin=0.75*inch, leftMargin=0.75*inch,
                                    topMargin=0.75*inch, bottomMargin=0.75*inch)
            elements: List[Any] = []

            self._create_presupuesto_header_footer(elements, presupuesto_id, user_name, customer_name)

            # Items Table
            headers = ["Descripción", "Cant.", "Precio Unit.", "Importe"]
            table_items_data = [[Paragraph(h, self.styles['ItemsTableHeader']) for h in headers]]

            for item_dict in items_data:
                desc = str(item_dict.get('product_description', '') or item_dict.get('description', 'N/A'))
                qty = Decimal(str(item_dict.get('quantity', 0)))
                unit_price_val = Decimal(str(item_dict.get('unit_price', 0)))
                subtotal_val = Decimal(str(item_dict.get('subtotal', qty * unit_price_val)))

                table_items_data.append([
                    Paragraph(desc, self.styles['DocInfo']),
                    Paragraph(f"{qty:.2f}", self.styles['RightAlign']),
                    Paragraph(self._format_currency_receipt(unit_price_val), self.styles['RightAlign']),
                    Paragraph(self._format_currency_receipt(subtotal_val), self.styles['RightAlign'])
                ])

            item_table = Table(table_items_data, colWidths=[3.5*inch, 0.8*inch, 1.2*inch, 1.2*inch])
            item_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.black),
                ('ALIGN', (0,0), (-1,0), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 8),
                ('GRID', (0,0), (-1,-1), 0.25, colors.black)
            ]))
            elements.append(item_table)
            elements.append(Spacer(1, 0.2*inch))

            # Total
            total_amount_decimal = Decimal(str(total_amount))
            elements.append(Paragraph(f"TOTAL PRESUPUESTADO: {self._format_currency_receipt(total_amount_decimal)}", 
                                      self.styles.get('Total', self.styles['BoldRightAlign'])))
            elements.append(Spacer(1, 0.3*inch))
            elements.append(Paragraph("Precios sujetos a cambio sin previo aviso.", self.styles['DocInfo']))
            elements.append(Paragraph("Este presupuesto tiene una validez de 7 días.", self.styles['DocInfo']))

            doc.build(elements)
            return True
        except Exception as e:
            self.logger.error(f"Error generating presupuesto PDF: {e}") # Changed from print
            return False

# Example Usage (for testing, can be removed later)
if __name__ == '__main__':
    # Sample Data (mimicking what services would provide)
    sample_store_info = {
        "name": "Mi Tienda SRL",
        "address": "Av. Corrientes 1234, CABA",
        "phone": "011-4555-6789",
        "cuit": "30-70123456-7",
        "iva_condition": "Responsable Inscripto",
        "logo_path": None # "path/to/your/logo.png" # Optional
    }

    sample_invoice_data = {
        "invoice_number": "0001-00001234",
        "invoice_date": datetime.now(),
        "invoice_type": "A", # or "B"
        "customer_details": {
            "name": "Cliente de Prueba SA",
            "address": "Defensa 500, CABA",
            "cuit": "30-98765432-1",
            "iva_condition": "Responsable Inscripto"
        },
        "subtotal": Decimal("1000.00"),
        "iva_amount": Decimal("210.00"),
        "total": Decimal("1210.00")
        # "afip_qr_data": "URL_o_datos_para_QR_AFIP" # Optional
    }

    sample_sale_items = [
        {"product_code": "P001", "product_description": "Producto Alfa", "quantity": Decimal("2.00"), "unit_price": Decimal("300.00")},
        {"product_code": "P002", "product_description": "Producto Beta Largo Nombre", "quantity": Decimal("1.00"), "unit_price": Decimal("400.00")},
    ]

    generator = DocumentPdfGenerator(store_info=sample_store_info)
    
    # Ensure 'test_outputs' directory exists
    if not os.path.exists("test_outputs"):
        os.makedirs("test_outputs")

    # Test Invoice
    invoice_filename = "test_outputs/sample_invoice.pdf"
    if generator.generate_invoice_pdf(sample_invoice_data, sample_sale_items, invoice_filename):
        print(f"Sample invoice generated: {invoice_filename}")
    else:
        print(f"Failed to generate sample invoice.")

    # Sample Data for Presupuesto    
    sample_presupuesto_items = [
        {"product_description": "Servicio de Consultoría", "quantity": Decimal("10.0"), "unit_price": Decimal("50.00")},
        {"product_description": "Licencia Software XYZ (Anual)", "quantity": Decimal("1.0"), "unit_price": Decimal("250.00")},
    ]
    presupuesto_total = sum(it['quantity'] * it['unit_price'] for it in sample_presupuesto_items)

    # Test Presupuesto
    presupuesto_filename = "test_outputs/sample_presupuesto.pdf"
    if generator.generate_presupuesto(
        items_data=sample_presupuesto_items, 
        total_amount=presupuesto_total, 
        filename=presupuesto_filename,
        customer_name="Empresa Prospecto SRL",
        user_name="Juan Pérez",
        presupuesto_id="PRE-2024-001"
    ):
        print(f"Sample presupuesto generated: {presupuesto_filename}")
    else:
        print(f"Failed to generate sample presupuesto.")

    # Sample Data for Receipt
    sample_sale_data_receipt = {
        "id": "S000123",
        "timestamp": datetime.now(),
        "user_name": "Cajero Uno",
        "payment_type": "Efectivo",
        "customer_name": "Cliente Contado",
        "items": [
            {"product_code": "P001", "product_description": "Producto Alfa", "quantity": Decimal("2.00"), "unit_price": Decimal("300.00"), "subtotal": Decimal("600.00")},
            {"product_code": "P002", "product_description": "Producto Beta", "quantity": Decimal("1.00"), "unit_price": Decimal("400.00"), "subtotal": Decimal("400.00")},
        ],
        "total": Decimal("1000.00")
    }

    # Test Receipt
    receipt_filename = "test_outputs/sample_receipt.pdf"
    # Note: The generate_receipt method was added above, so this replaces the old generate_receipt_pdf placeholder call
    if generator.generate_receipt(sale_data=sample_sale_data_receipt, filename=receipt_filename):
        print(f"Sample receipt generated: {receipt_filename}")
    else:
        print(f"Failed to generate sample receipt.")