from typing import Optional, Dict, Any
from decimal import Decimal
import json
from datetime import datetime
import os
from sqlalchemy.exc import IntegrityError

# Required imports for PDF generation
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

from core.models.invoice import Invoice
from core.models.sale import Sale
from core.models.customer import Customer
from config import config
from core.exceptions import ResourceNotFoundError, ExternalServiceError
from core.services.service_base import ServiceBase
from core.interfaces.repository_interfaces import IInvoiceRepository
from infrastructure.persistence.unit_of_work import UnitOfWork, unit_of_work

class InvoicingService(ServiceBase):
    """Service to handle invoice creation and management."""
    
    def __init__(self):
        """
        Initialize the service.
        """
        super().__init__()  # Initialize base class with default logger
    
    def create_invoice_from_sale(self, sale_id: int) -> Invoice:
        """
        Create an invoice from an existing sale.
        
        Args:
            sale_id: The ID of the sale to generate an invoice for
            
        Returns:
            The created Invoice object
            
        Raises:
            ValueError: If the sale doesn't exist, already has an invoice, or lacks required customer data
        """
        with unit_of_work() as uow:
            # Check if sale exists
            sale = self._get_sale(sale_id, uow.sales)
            if not sale:
                raise ValueError(f"Sale with ID {sale_id} not found")
                
            # Check if sale already has an invoice
            existing_invoice = uow.invoices.get_by_sale_id(sale_id)
            if existing_invoice:
                raise ValueError(f"Sale with ID {sale_id} already has an invoice")
                
            # Check if sale has a customer (required for invoicing)
            if not sale.customer_id:
                raise ValueError(f"Sale with ID {sale_id} has no associated customer. A customer is required for invoicing.")
                
            # Get customer data
            customer = self._get_customer(sale.customer_id, uow.customers)
            if not customer:
                raise ValueError(f"Customer with ID {sale.customer_id} not found")
            
            # Generate customer details snapshot
            customer_details = {
                "name": customer.name,
                "address": customer.address,
                "cuit": customer.cuit,
                "iva_condition": customer.iva_condition,
                "email": customer.email,
                "phone": customer.phone
            }
            
            # Generate invoice number
            invoice_number = self._generate_next_invoice_number(uow.invoices)
            
            # Determine invoice type based on customer's IVA condition
            invoice_type = self._determine_invoice_type(customer.iva_condition)
            
            # Calculate financial amounts
            subtotal = Decimal(str(sale.total))
            iva_rate = self._get_iva_rate(invoice_type, customer.iva_condition)
            
            # Calculate IVA amount (if applicable)
            if iva_rate > 0:
                # IVA is calculated on pre-tax amount
                pre_tax_amount = subtotal / (Decimal('1') + iva_rate)
                iva_amount = subtotal - pre_tax_amount
            else:
                # No IVA
                iva_amount = Decimal('0')
                pre_tax_amount = subtotal
            
            # Quantize amounts to 2 decimals
            pre_tax_amount = pre_tax_amount.quantize(Decimal('0.01'))
            iva_amount = iva_amount.quantize(Decimal('0.01'))
            
            # Create invoice
            invoice = Invoice(
                sale_id=sale_id,
                customer_id=sale.customer_id,
                invoice_number=invoice_number,
                invoice_date=datetime.now(),
                invoice_type=invoice_type,
                customer_details=customer_details,
                subtotal=pre_tax_amount,
                iva_amount=iva_amount,
                total=subtotal,
                iva_condition=customer.iva_condition or 'Consumidor Final'
            )
            
            try:
                # Save to repository
                new_invoice = uow.invoices.add(invoice)
                uow.commit()
                return new_invoice
            except (ValueError, IntegrityError) as e: # Catch both ValueError and IntegrityError
                # Log the original error for debugging
                self.logger.warning(f"Caught error during invoice add for sale {sale_id}: {type(e).__name__} - {e}")
                
                error_msg_lower = str(e).lower()

                # Check for specific IntegrityError indicating sale_id uniqueness violation from the database
                is_db_sale_id_duplicate = (
                    isinstance(e, IntegrityError) and
                    (("unique constraint failed" in error_msg_lower and "invoices.sale_id" in error_msg_lower) or # SQLite
                     ("duplicate key value violates unique constraint" in error_msg_lower and "invoices_sale_id_key" in error_msg_lower)) # PostgreSQL
                )

                # Check for ValueError from repository's pre-emptive check (invoice_repo.add raises this before flush if get_by_sale_id finds one)
                # Also check for ValueErrors from the repository that signal a duplicate during its own add operation.
                is_repo_value_error_duplicate = (
                    isinstance(e, ValueError) and
                    ("already has an invoice" in error_msg_lower or \
                     "already exists" in error_msg_lower or \
                     "duplicate entry in db" in error_msg_lower # Handle mock repo's error for the test
                    ) 
                )
                
                if is_db_sale_id_duplicate or is_repo_value_error_duplicate:
                    # This directly addresses the duplicate sale invoice scenario.
                    # If it's an IntegrityError from the DB, the session is likely dirty, so no more reads.
                    raise ValueError(f"Sale with ID {sale_id} already has an invoice (duplicate)")
                
                # Handle other IntegrityErrors (e.g. invoice_number unique constraint)
                elif isinstance(e, IntegrityError):
                    is_invoice_number_constraint_violation = (
                        ("unique constraint failed" in error_msg_lower and "invoices.invoice_number" in error_msg_lower) or
                        ("duplicate key value violates unique constraint" in error_msg_lower and ("invoices_invoice_number_key" in error_msg_lower or "invoices_invoice_number_idx" in error_msg_lower))
                    )
                    if is_invoice_number_constraint_violation:
                        self.logger.error(f"Invoice number conflict for sale {sale_id}. Original error: {e}")
                        raise ValueError(f"Invoice number generation conflict for sale {sale_id}: {e}")
                    else:
                        self.logger.error(f"Unexpected IntegrityError during invoice creation for sale {sale_id}: {e}")
                        raise ValueError(f"Invoice creation failed due to an unexpected database integrity issue: {e}")
                
                # Handle other ValueErrors not caught above (e.g., customer not found, sale not found etc., which should be caught earlier but as a safeguard)
                elif isinstance(e, ValueError):
                     self.logger.error(f"Unexpected ValueError during invoice creation for sale {sale_id}: {e}")
                     # Re-raise the original ValueError if it's not one of the specific duplicate types handled above
                     # or other known ValueErrors that should have been caught by pre-checks.
                     raise 
                else: # Should not happen if only ValueError or IntegrityError are caught
                    self.logger.error(f"Unhandled error type {type(e).__name__} during invoice creation for sale {sale_id}: {e}")
                    raise ValueError(f"Invoice creation failed with an unexpected error: {e}")
    
    def _get_sale(self, sale_id: int, sale_repo) -> Optional[Sale]:
        """Get a sale by ID, handling any exceptions."""
        try:
            return sale_repo.get_by_id(sale_id)
        except Exception as e:
            # Log the error
            self.logger.error(f"Error retrieving sale: {e}")
            return None
    
    def _get_customer(self, customer_id: int, customer_repo) -> Optional[Customer]:
        """Get a customer by ID, handling any exceptions."""
        try:
            return customer_repo.get_by_id(customer_id)
        except Exception as e:
            # Log the error
            self.logger.error(f"Error retrieving customer: {e}")
            return None
    
    def _generate_next_invoice_number(self, invoice_repo: IInvoiceRepository) -> str:
        """
        Generate the next available invoice number.
        Format: 0001-00000001 (Point of Sale - Number)
        """
        # For now, use a simple approach: get the last invoice and increment
        # In a production system, this would need to be more robust and potentially
        # use a sequence or retrieve from a fiscal service
        
        # Default POS number (could be configurable)
        pos_number = "0001"
        
        try:
            # Get all invoices and find the highest number
            all_invoices = invoice_repo.get_all()
            
            if not all_invoices:
                # First invoice
                return f"{pos_number}-00000001"
            
            # Find highest invoice number
            highest_number = 0
            for invoice in all_invoices:
                if invoice.invoice_number:
                    parts = invoice.invoice_number.split('-')
                    if len(parts) == 2:
                        try:
                            number = int(parts[1])
                            if number > highest_number:
                                highest_number = number
                        except ValueError:
                            continue
            
            # Increment and format
            next_number = highest_number + 1
            return f"{pos_number}-{next_number:08d}"
            
        except Exception as e:
            # Log the error and use a fallback approach
            self.logger.error(f"Error generating invoice number: {e}")
            return f"{pos_number}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def _determine_invoice_type(self, iva_condition: Optional[str]) -> str:
        """
        Determine the invoice type based on customer's IVA condition.
        
        Args:
            iva_condition: The customer's IVA condition
            
        Returns:
            'A', 'B', or 'C' based on IVA rules
        """
        # Default to 'B' for most common case
        if not iva_condition:
            return "B"
            
        # Map IVA conditions to invoice types according to Argentina rules
        if iva_condition.upper() in ["RESPONSABLE INSCRIPTO", "RESPONSABLE INSCRIPTO"]:
            return "A"
        elif iva_condition.upper() in ["MONOTRIBUTISTA", "MONOTRIBUTO", "EXENTO", "CONSUMIDOR FINAL"]:
            return "B"
        else:
            return "B"  # Default for unknown cases
    
    def _get_iva_rate(self, invoice_type: str, iva_condition: Optional[str]) -> Decimal:
        """
        Get the IVA (VAT) rate based on invoice type and customer condition.
        
        Args:
            invoice_type: 'A', 'B', or 'C'
            iva_condition: Customer's IVA condition
            
        Returns:
            Decimal representing the IVA rate (e.g., 0.21 for 21%)
        """
        # Standard IVA rate in Argentina (21%)
        standard_rate = Decimal('0.21')
        
        # For type A invoices between registered taxpayers, IVA is itemized
        if invoice_type == "A" and iva_condition and "RESPONSABLE INSCRIPTO" in iva_condition.upper():
            return standard_rate
        # For type B invoices to end consumers, IVA is included in price
        elif invoice_type == "B":
            # Since IVA is already included in the total, we return 0 
            # because we don't need to add it to the sale total
            return Decimal('0')
        # For exempt entities
        elif iva_condition and "EXENTO" in iva_condition.upper():
            return Decimal('0')
        else:
            return standard_rate  # Default case
    
    def get_invoice_by_id(self, invoice_id: int) -> Optional[Invoice]:
        """Get an invoice by ID."""
        with unit_of_work() as uow:
            return uow.invoices.get_by_id(invoice_id)
    
    def get_invoice_by_sale_id(self, sale_id: int) -> Optional[Invoice]:
        """Get an invoice by its associated sale ID."""
        with unit_of_work() as uow:
            return uow.invoices.get_by_sale_id(sale_id)
    
    def get_all_invoices(self):
        """Get all invoices."""
        with unit_of_work() as uow:
            return uow.invoices.get_all()
    
    def generate_invoice_pdf(self, invoice_id: int, output_path: str = None, filename: str = None, store_info: dict = None) -> str:
        """
        Generates a PDF document for a given invoice ID.

        Args:
            invoice_id: The ID of the invoice to generate PDF for.
            output_path: Optional. Directory to save the PDF. Defaults to Config.PDF_OUTPUT_DIR.
            filename: Optional. Filename for the PDF. Defaults to "invoice_<number>.pdf".
            store_info: Optional. Dictionary containing store information to include in the PDF.

        Returns:
            str: The full path to the generated PDF file.

        Raises:
            ResourceNotFoundError: If the invoice or related sale/customer is not found.
            Exception: For errors during PDF generation.
        """
        with unit_of_work() as uow:
            # Retrieve invoice and sale
            invoice = uow.invoices.get_by_id(invoice_id)
            if not invoice:
                raise ResourceNotFoundError(f"Invoice with ID {invoice_id} not found")

            sale = uow.sales.get_by_id(invoice.sale_id)
            if not sale:
                raise ResourceNotFoundError(f"Sale with ID {invoice.sale_id} not found")

            # --- Determine Full Output Path Logic ---
            if output_path and not filename:
                # Assume output_path is the intended full file path
                full_pdf_path = output_path
                output_dir = os.path.dirname(full_pdf_path)
            elif output_path and filename:
                # Assume output_path is a directory
                output_dir = output_path
                full_pdf_path = os.path.join(output_dir, filename)
            else:
                # Default behavior: Use default dir and default/provided filename
                output_dir = config.PDF_OUTPUT_DIR
                if not filename:
                    filename = self._generate_pdf_filename(invoice.invoice_number)
                full_pdf_path = os.path.join(output_dir, filename)

            # Ensure the final output directory exists
            final_output_dir = os.path.dirname(full_pdf_path)
            if final_output_dir: # Avoid trying to create empty path
                os.makedirs(final_output_dir, exist_ok=True)

            self.logger.info(f"Generating PDF: {full_pdf_path}")

            # --- PDF Generation Logic (using ReportLab) ---
            try:
                # Default store info
                default_store_info = {
                    "name": "Eleventa Demo Store",
                    "address": "123 Main St, Buenos Aires, Argentina",
                    "phone": "555-1234",
                    "email": "info@eleventa-demo.com",
                    "website": "www.eleventa-demo.com",
                    "tax_id": "30-12345678-9",
                    "logo_path": None # Add logo path if available
                }
                store_info = store_info or default_store_info
                
                # Create PDF Document
                doc = SimpleDocTemplate(full_pdf_path, pagesize=letter)
                styles = getSampleStyleSheet()
                story = []

                # 1. Store Info & Logo
                if store_info.get("logo_path") and os.path.exists(store_info["logo_path"]):
                    # Add logo logic here if needed
                    pass 
                story.append(Paragraph(store_info.get("name", "Store Name"), styles['h1']))
                story.append(Paragraph(store_info.get("address", ""), styles['Normal']))
                story.append(Paragraph(f"Tel: {store_info.get('phone', '')}", styles['Normal']))
                story.append(Paragraph(f"CUIT: {store_info.get('tax_id', '')}", styles['Normal']))
                story.append(Paragraph(f"IVA: {store_info.get('iva_condition', '')}", styles['Normal']))
                story.append(Spacer(1, 0.2*inch))

                # 2. Invoice Header
                header_text = f"<b>FACTURA {invoice.invoice_type}</b> N° {invoice.invoice_number}"
                story.append(Paragraph(header_text, styles['h2']))
                story.append(Paragraph(f"Fecha: {invoice.invoice_date.strftime('%d/%m/%Y %H:%M:%S')}", styles['Normal']))
                story.append(Spacer(1, 0.2*inch))

                # 3. Customer Details
                story.append(Paragraph("<b>Cliente:</b>", styles['h3']))
                cust_details = invoice.customer_details or {}
                story.append(Paragraph(f"Nombre: {cust_details.get('name', 'Consumidor Final')}", styles['Normal']))
                story.append(Paragraph(f"Dirección: {cust_details.get('address', '-')}", styles['Normal']))
                story.append(Paragraph(f"CUIT: {cust_details.get('cuit', '-')}", styles['Normal']))
                story.append(Paragraph(f"Condición IVA: {cust_details.get('iva_condition', '-')}", styles['Normal']))
                story.append(Spacer(1, 0.3*inch))
                
                # 4. Sale Items Table
                story.append(Paragraph("<b>Detalle:</b>", styles['h3']))
                data = [['Código', 'Descripción', 'Cant.', 'P. Unit.', 'Subtotal']]
                for item in sale.items:
                    data.append([
                        item.product_code,
                        Paragraph(item.product_description, styles['Normal']), # Wrap long descriptions
                        f"{item.quantity:.2f}",
                        f"${item.unit_price:.2f}",
                        f"${item.subtotal:.2f}"
                    ])
                
                table_style = TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.grey),
                    ('TEXTCOLOR',(0,0),(-1,0), colors.whitesmoke),
                    ('ALIGN',(0,0),(-1,-1),'CENTER'),
                    ('ALIGN',(1,1),(1,-1),'LEFT'), # Align description left
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0,0), (-1,0), 12),
                    ('BACKGROUND',(0,1),(-1,-1),colors.beige),
                    ('GRID',(0,0),(-1,-1),1,colors.black),
                    ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                ])
                
                # Create table with specific column widths
                col_widths = [70, 260, 50, 70, 70] # Adjust as needed
                items_table = Table(data, colWidths=col_widths)
                items_table.setStyle(table_style)
                story.append(items_table)
                story.append(Spacer(1, 0.3*inch))

                # 5. Totals Section
                totals_data = [
                    ['Subtotal:', f"${invoice.subtotal:.2f}"],
                    [f"IVA:", f"${invoice.iva_amount:.2f}"] if invoice.iva_amount > 0 else None,
                    ['', ''], # Spacer
                    ['<b>Total:</b>', f"<b>${invoice.total:.2f}</b>"]
                ]
                # Filter out None rows (for cases with no IVA)
                totals_data = [row for row in totals_data if row is not None]

                totals_table = Table(totals_data, colWidths=[390, 130]) # Adjust colWidths
                totals_table.setStyle(TableStyle([
                    ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
                    ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'), # Bold total row
                    ('GRID',(0,0),(-1,-1), 1, colors.white), # No visible grid
                    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ]))
                story.append(totals_table)
                story.append(Spacer(1, 0.3*inch))
                
                # 6. CAE Information (if applicable)
                if invoice.cae and invoice.cae_due_date:
                    story.append(Paragraph(f"CAE N°: {invoice.cae}", styles['Normal']))
                    story.append(Paragraph(f"Fecha Vto. CAE: {invoice.cae_due_date.strftime('%d/%m/%Y')}", styles['Normal']))

                # Build the PDF
                doc.build(story)
                self.logger.info(f"Successfully generated PDF: {full_pdf_path}")
                return full_pdf_path

            except Exception as e:
                # Log the error
                self.logger.error(f"Error generating PDF for invoice {invoice_id}: {e}")
                # Raise a specific PDF generation error
                raise ExternalServiceError(f"Failed to generate PDF for invoice {invoice_id}") from e
    
    def _generate_pdf_filename(self, invoice_number: str) -> str:
        """Generate a PDF filename from an invoice number."""
        return f"invoice_{invoice_number.replace('-', '_')}.pdf"