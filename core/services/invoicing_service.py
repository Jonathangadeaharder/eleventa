from typing import Optional, Dict, Any
from decimal import Decimal
import json
from datetime import datetime
import os

from core.interfaces.repository_interfaces import IInvoiceRepository, ISaleRepository, ICustomerRepository
from core.models.invoice import Invoice
from core.models.sale import Sale
from core.models.customer import Customer
from config import Config

class InvoicingService:
    """Service to handle invoice creation and management."""
    
    def __init__(self, invoice_repo: IInvoiceRepository, sale_repo: ISaleRepository, customer_repo: ICustomerRepository):
        """Initialize with required repositories."""
        self.invoice_repo = invoice_repo
        self.sale_repo = sale_repo
        self.customer_repo = customer_repo
    
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
        # Check if sale exists
        sale = self._get_sale(sale_id)
        if not sale:
            raise ValueError(f"Sale with ID {sale_id} not found")
            
        # Check if sale already has an invoice - this needs to be checked twice
        # for race conditions in concurrent scenarios
        existing_invoice = self.invoice_repo.get_by_sale_id(sale_id)
        if existing_invoice:
            raise ValueError(f"Sale with ID {sale_id} already has an invoice")
            
        # Check if sale has a customer (required for invoicing)
        if not sale.customer_id:
            raise ValueError(f"Sale with ID {sale_id} has no associated customer. A customer is required for invoicing.")
            
        # Get customer data
        customer = self._get_customer(sale.customer_id)
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
        invoice_number = self._generate_next_invoice_number()
        
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
            iva_condition=customer.iva_condition or "Consumidor Final"
        )
        
        try:
            # Save to repository
            return self.invoice_repo.add(invoice)
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
                double_check = self.invoice_repo.get_by_sale_id(sale_id)
                if double_check:
                    raise ValueError(f"Sale with ID {sale_id} already has an invoice (duplicate)")
            # Re-raise any other errors
            raise ValueError(f"Invoice creation failed: {e}")
    
    def _get_sale(self, sale_id: int) -> Optional[Sale]:
        """Get a sale by ID, handling any exceptions."""
        try:
            # We assume sale_repo has a get_by_id method, add if not exists
            return self.sale_repo.get_by_id(sale_id)
        except Exception as e:
            # Log the error
            print(f"Error retrieving sale: {e}")
            return None
    
    def _get_customer(self, customer_id: int) -> Optional[Customer]:
        """Get a customer by ID, handling any exceptions."""
        try:
            return self.customer_repo.get_by_id(customer_id)
        except Exception as e:
            # Log the error
            print(f"Error retrieving customer: {e}")
            return None
    
    def _generate_next_invoice_number(self) -> str:
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
            all_invoices = self.invoice_repo.get_all()
            
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
        return self.invoice_repo.get_by_id(invoice_id)
    
    def get_invoice_by_sale_id(self, sale_id: int) -> Optional[Invoice]:
        """Get an invoice by its associated sale ID."""
        return self.invoice_repo.get_by_sale_id(sale_id)
    
    def get_all_invoices(self):
        """Get all invoices."""
        return self.invoice_repo.get_all()
    
    def generate_invoice_pdf(self, invoice_id: int, filename: str = None, store_info: Dict[str, str] = None) -> str:
        """
        Generate a PDF file for an invoice.
        
        Args:
            invoice_id: ID of the invoice to generate PDF for
            filename: Optional custom filename/path. If not provided, one will be generated
            store_info: Optional store information. If not provided, Config values will be used
            
        Returns:
            Path to the generated PDF file
            
        Raises:
            ValueError: If the invoice doesn't exist or other error occurs
        """
        from infrastructure.reporting.invoice_builder import InvoiceBuilder
        
        # Get invoice
        invoice = self.invoice_repo.get_by_id(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice with ID {invoice_id} not found")
            
        # Get sale with items
        sale = self._get_sale(invoice.sale_id)
        if not sale or not sale.items:
            raise ValueError(f"Sale data for invoice {invoice_id} not found or has no items")
            
        # Use provided store info or create from Config
        if not store_info:
            store_info = {
                'name': Config.STORE_NAME,
                'address': Config.STORE_ADDRESS,
                'cuit': Config.STORE_CUIT,
                'iva_condition': Config.STORE_IVA_CONDITION, 
                'phone': Config.STORE_PHONE
            }
            
        # Create filename if not provided
        if not filename:
            # Create directory if it doesn't exist
            os.makedirs('invoices', exist_ok=True)
            filename = f"invoices/factura_{invoice.invoice_number.replace('-', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
            
        # Convert invoice to dictionary for the builder
        invoice_data = {
            'id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'invoice_date': invoice.invoice_date,
            'invoice_type': invoice.invoice_type,
            'customer_details': invoice.customer_details,
            'subtotal': invoice.subtotal,
            'iva_amount': invoice.iva_amount,
            'total': invoice.total,
            'iva_condition': invoice.iva_condition,
            'cae': invoice.cae,
            'cae_due_date': invoice.cae_due_date,
            'is_active': invoice.is_active
        }
        
        # Convert sale items to list of dictionaries
        sale_items = []
        for item in sale.items:
            sale_items.append({
                'code': item.product_code,
                'description': item.product_description,
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'subtotal': item.subtotal
            })
            
        # Create PDF
        invoice_builder = InvoiceBuilder(store_info)
        success = invoice_builder.generate_invoice_pdf(
            invoice_data=invoice_data,
            sale_items=sale_items,
            filename=filename
        )
        
        if not success:
            raise ValueError(f"Failed to generate PDF for invoice {invoice_id}")
            
        return filename