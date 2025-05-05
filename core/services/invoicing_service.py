from typing import Optional, Dict, Any, Callable
from decimal import Decimal
import json
from datetime import datetime
import os

from core.interfaces.repository_interfaces import IInvoiceRepository, ISaleRepository, ICustomerRepository
from core.models.invoice import Invoice
from core.models.sale import Sale
from core.models.customer import Customer
from config import Config
from infrastructure.persistence.utils import session_scope

class InvoicingService:
    """Service to handle invoice creation and management."""
    
    def __init__(self, invoice_repo_factory: Callable[[], IInvoiceRepository], 
                 sale_repo_factory: Callable[[], ISaleRepository], 
                 customer_repo_factory: Callable[[], ICustomerRepository]):
        """Initialize with repository factories."""
        self.invoice_repo_factory = invoice_repo_factory
        self.sale_repo_factory = sale_repo_factory
        self.customer_repo_factory = customer_repo_factory
    
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
        with session_scope() as session:
            invoice_repo = self.invoice_repo_factory(session)
            sale_repo = self.sale_repo_factory(session)
            customer_repo = self.customer_repo_factory(session)
            
            # Check if sale exists
            sale = self._get_sale(sale_id, sale_repo)
            if not sale:
                raise ValueError(f"Sale with ID {sale_id} not found")
                
            # Check if sale already has an invoice - this needs to be checked twice
            # for race conditions in concurrent scenarios
            existing_invoice = invoice_repo.get_by_sale_id(sale_id)
            if existing_invoice:
                raise ValueError(f"Sale with ID {sale_id} already has an invoice")
                
            # Check if sale has a customer (required for invoicing)
            if not sale.customer_id:
                raise ValueError(f"Sale with ID {sale_id} has no associated customer. A customer is required for invoicing.")
                
            # Get customer data
            customer = self._get_customer(sale.customer_id, customer_repo)
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
            invoice_number = self._generate_next_invoice_number(invoice_repo)
            
            # Determine invoice type based on customer's IVA condition
            invoice_type = self._determine_invoice_type(customer.iva_condition)
            
            # Calculate financial amounts
            # For now, we'll use simple calculations; this can be expanded based on specific tax rules
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
                return invoice_repo.add(invoice)
            except ValueError as e:
                # This could happen if another thread created an invoice 
                # between our first check and the attempt to save
                msg = str(e).lower()
                if (
                    "already have an invoice" in msg or
                    "sale may already have an invoice" in msg or
                    "already exists" in msg or
                    "duplicate" in msg
                ):
                    # Do one more check to verify
                    double_check = invoice_repo.get_by_sale_id(sale_id)
                    if double_check:
                        raise ValueError(f"Sale with ID {sale_id} already has an invoice (duplicate)")
                # Re-raise any other errors
                raise ValueError(f"Invoice creation failed: {e}")
    
    def _get_sale(self, sale_id: int, sale_repo: ISaleRepository) -> Optional[Sale]:
        """Get a sale by ID, handling any exceptions."""
        try:
            return sale_repo.get_by_id(sale_id)
        except Exception as e:
            # Log the error
            print(f"Error retrieving sale: {e}")
            return None
    
    def _get_customer(self, customer_id: int, customer_repo: ICustomerRepository) -> Optional[Customer]:
        """Get a customer by ID, handling any exceptions."""
        try:
            return customer_repo.get_by_id(customer_id)
        except Exception as e:
            # Log the error
            print(f"Error retrieving customer: {e}")
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
            print(f"Error generating invoice number: {e}")
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
        with session_scope() as session:
            invoice_repo = self.invoice_repo_factory(session)
            return invoice_repo.get_by_id(invoice_id)
    
    def get_invoice_by_sale_id(self, sale_id: int) -> Optional[Invoice]:
        """Get an invoice by its associated sale ID."""
        with session_scope() as session:
            invoice_repo = self.invoice_repo_factory(session)
            return invoice_repo.get_by_sale_id(sale_id)
    
    def get_all_invoices(self):
        """Get all invoices."""
        with session_scope() as session:
            invoice_repo = self.invoice_repo_factory(session)
            return invoice_repo.get_all()
    
    def generate_invoice_pdf(self, invoice_id: int, filename: str = None, output_path: str = None, store_info: Dict[str, str] = None) -> str:
        """
        Generate a PDF file for an invoice.
        
        Args:
            invoice_id: The ID of the invoice to generate a PDF for
            filename: Optional custom filename (default: invoice_{invoice_id}.pdf)
            output_path: Path where to save the PDF (default: config PDF_OUTPUT_DIR)
            store_info: Dictionary with store information to include in the PDF
            
        Returns:
            The path to the generated PDF file
            
        Raises:
            ValueError: If the invoice is not found or PDF generation fails
        """
        with session_scope() as session:
            invoice_repo = self.invoice_repo_factory(session)
            sale_repo = self.sale_repo_factory(session)
            
            # Get the invoice
            invoice = invoice_repo.get_by_id(invoice_id)
            if not invoice:
                raise ValueError(f"Invoice with ID {invoice_id} not found")
            
            # Get the associated sale with items
            sale = sale_repo.get_by_id(invoice.sale_id)
            if not sale:
                raise ValueError(f"Sale with ID {invoice.sale_id} not found")
            
            # Determine output path and filename
            if not output_path:
                # Use the configured PDF output directory
                output_path = Config.PDF_OUTPUT_DIR
                
            # Ensure output directory exists
            os.makedirs(output_path, exist_ok=True)
                
            if not filename:
                filename = f"invoice_{invoice.invoice_number.replace('-', '_')}.pdf"
                
            full_path = os.path.join(output_path, filename)
            
            # Default store info
            default_store_info = {
                "name": "Eleventa Demo Store",
                "address": "123 Main St, Buenos Aires, Argentina",
                "phone": "555-1234",
                "email": "info@eleventa-demo.com",
                "website": "www.eleventa-demo.com",
                "tax_id": "30-12345678-9"
            }
            
            # Use provided store info or defaults
            store_info = store_info or default_store_info
            
            # TODO: Generate PDF logic here
            # For now, we'll just create a simple text file as a placeholder
            with open(full_path, "w") as f:
                f.write(f"INVOICE {invoice.invoice_number}\n")
                f.write(f"Date: {invoice.invoice_date}\n")
                f.write(f"Type: {invoice.invoice_type}\n\n")
                
                f.write("STORE INFORMATION\n")
                for key, value in store_info.items():
                    f.write(f"{key.capitalize()}: {value}\n")
                
                f.write("\nCUSTOMER INFORMATION\n")
                for key, value in invoice.customer_details.items():
                    if value:  # Only write non-empty values
                        f.write(f"{key.capitalize()}: {value}\n")
                
                f.write("\nITEMS\n")
                for item in sale.items:
                    f.write(f"{item.quantity} x {item.description} @ {item.unit_price} = {item.line_total}\n")
                
                f.write("\nSUMMARY\n")
                f.write(f"Subtotal: {invoice.subtotal}\n")
                f.write(f"IVA ({int(Decimal('0.21')*100)}%): {invoice.iva_amount}\n")
                f.write(f"Total: {invoice.total}\n")
            
            return full_path