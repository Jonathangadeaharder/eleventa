"""
Central printing utility for all printing tasks in the application.
This handles printing to PDF files, real printers, and print previews.
"""
import os
import platform
import subprocess
from enum import Enum
from typing import Dict, Any, Optional, Callable, Union

# Import existing report builders
from infrastructure.reporting.report_builder import ReportBuilder
from infrastructure.reporting.receipt_builder import generate_receipt_pdf
from infrastructure.reporting.invoice_builder import InvoiceBuilder

# Class to represent different print outputs
class PrintDestination(Enum):
    PDF_FILE = "pdf_file"  # Save to PDF file
    PRINTER = "printer"    # Send directly to printer
    PREVIEW = "preview"    # Open in PDF viewer

class PrintType(Enum):
    REPORT = "report"      # Business reports
    RECEIPT = "receipt"    # Sales receipts
    INVOICE = "invoice"    # Customer invoices
    CASH_DRAWER = "cash_drawer"  # Cash drawer reports

class PrintManager:
    """
    Centralized print management for the application.
    Handles printing to different destinations and manages
    document generation.
    """
    
    def __init__(self):
        """Initialize the print manager with default settings."""
        self.default_pdf_dir = "pdfs"
        self.receipt_dir = "receipts"
        
        # Ensure directories exist
        os.makedirs(self.default_pdf_dir, exist_ok=True)
        os.makedirs(self.receipt_dir, exist_ok=True)
        
        # Initialize store info (used by report builders)
        self.store_info = None
        
        # Initialize report builders
        self.report_builder = ReportBuilder()
        # Invoice builder requires store info
        self._get_store_info()  # This populates self.store_info
        self.invoice_builder = InvoiceBuilder(self.store_info)
    
    def _get_store_info(self) -> Dict[str, Any]:
        """Get store information for reports and receipts."""
        if self.store_info is None:
            from config import Config
            self.store_info = {
                "name": Config.STORE_NAME or "Eleventa Demo Store",
                "address": Config.STORE_ADDRESS or "123 Main St, Buenos Aires, Argentina",
                "phone": Config.STORE_PHONE or "555-1234",
                "tax_id": Config.STORE_CUIT or "30-12345678-9",
                "iva_condition": Config.STORE_IVA_CONDITION or "Responsable Inscripto",
            }
        return self.store_info
    
    def print(
        self,
        print_type: PrintType,
        data: Dict[str, Any],
        destination: PrintDestination = PrintDestination.PDF_FILE,
        filename: Optional[str] = None,
        printer_name: Optional[str] = None,
        callback: Optional[Callable[[str, bool], None]] = None
    ) -> Union[str, bool]:
        """
        Print a document based on the specified type and destination.
        
        Args:
            print_type: Type of document to print (report, receipt, etc.)
            data: Document data needed for generation
            destination: Where to send the output
            filename: Custom filename (optional)
            printer_name: Name of printer to use (optional)
            callback: Function to call after printing (optional)
            
        Returns:
            String with file path if saved to PDF, or boolean for other destinations
        """
        try:
            # Generate the appropriate document based on type
            if print_type == PrintType.REPORT:
                pdf_path = self._generate_report(data, filename)
            elif print_type == PrintType.RECEIPT:
                pdf_path = self._generate_receipt(data, filename)
            elif print_type == PrintType.INVOICE:
                pdf_path = self._generate_invoice(data, filename)
            elif print_type == PrintType.CASH_DRAWER:
                pdf_path = self._generate_cash_drawer_report(data, filename)
            else:
                raise ValueError(f"Unsupported print type: {print_type}")
            
            # Handle the output based on destination
            if destination == PrintDestination.PDF_FILE:
                # Just return the path
                result = pdf_path
            elif destination == PrintDestination.PREVIEW:
                # Open the PDF in the default viewer
                result = self._open_pdf(pdf_path)
            elif destination == PrintDestination.PRINTER:
                # Send to printer
                result = self._print_to_printer(pdf_path, printer_name)
            else:
                raise ValueError(f"Unsupported print destination: {destination}")
            
            # Call the callback if provided
            if callback:
                callback(pdf_path, result is True or isinstance(result, str))
                
            return result
            
        except Exception as e:
            print(f"Error in print operation: {e}")
            # Call the callback with failure if provided
            if callback:
                callback("", False)
            return False
    
    def _generate_report(self, data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Generate a business report PDF."""
        # Extract report parameters from data
        report_title = data.get('title', 'Business Report')
        is_landscape = data.get('is_landscape', False)
        
        # Generate filename if not provided
        if not filename:
            timestamp = data.get('timestamp', '').replace(' ', '_').replace('/', '-')
            report_type = data.get('report_type', 'report')
            filename = f"{self.default_pdf_dir}/{report_type}_{timestamp}.pdf"
        
        # Generate the report using the report builder
        success = self.report_builder.generate_report_pdf(
            report_title=report_title,
            report_data=data,
            filename=filename,
            is_landscape=is_landscape
        )
        
        if not success:
            raise RuntimeError(f"Failed to generate report: {report_title}")
            
        return filename
    
    def _generate_receipt(self, data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Generate a sales receipt PDF."""
        # Get sale and store info
        sale = data.get('sale')
        store_info = self._get_store_info()
        
        # Generate filename if not provided
        if not filename:
            sale_id = getattr(sale, 'id', 'unknown')
            timestamp = getattr(sale, 'timestamp', '').strftime('%Y%m%d_%H%M%S')
            filename = f"{self.receipt_dir}/receipt_{sale_id}_{timestamp}.pdf"
        
        # Generate the receipt
        return generate_receipt_pdf(sale, store_info, filename)
    
    def _generate_invoice(self, data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Generate a customer invoice PDF."""
        # Extract invoice parameters
        invoice = data.get('invoice')
        
        # Generate filename if not provided
        if not filename:
            invoice_id = getattr(invoice, 'id', 'unknown')
            timestamp = data.get('timestamp', '').replace(' ', '_').replace('/', '-')
            filename = f"{self.default_pdf_dir}/invoice_{invoice_id}_{timestamp}.pdf"
        
        # Generate the invoice using the invoice builder
        return self.invoice_builder.generate_invoice_pdf(invoice, filename)
    
    def _generate_cash_drawer_report(self, data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Generate a cash drawer report PDF."""
        # Extract drawer data
        drawer_id = data.get('drawer_id')
        drawer_data = data.get('drawer_data', {})
        report_title = data.get('title', 'Cash Drawer Report')
        
        # Generate filename if not provided
        if not filename:
            timestamp = data.get('timestamp', '').replace(' ', '_').replace('/', '-')
            filename = f"{self.default_pdf_dir}/cash_drawer_{drawer_id}_{timestamp}.pdf"
        
        # Prepare report data in the format expected by report builder
        report_data = {
            'drawer_id': drawer_id,
            'is_open': drawer_data.get('is_open', False),
            'current_balance': drawer_data.get('current_balance', 0),
            'initial_amount': drawer_data.get('initial_amount', 0),
            'total_in': drawer_data.get('total_in', 0),
            'total_out': drawer_data.get('total_out', 0),
            'opened_at': drawer_data.get('opened_at', ''),
            'opened_by': drawer_data.get('opened_by', ''),
            'entries': drawer_data.get('entries_today', [])
        }
        
        # Generate the report using the report builder
        success = self.report_builder.generate_report_pdf(
            report_title=report_title,
            report_data=report_data,
            filename=filename
        )
        
        if not success:
            raise RuntimeError(f"Failed to generate cash drawer report")
            
        return filename
    
    def _open_pdf(self, pdf_path: str) -> bool:
        """Open a PDF file with the system's default PDF viewer."""
        try:
            system = platform.system()
            
            if system == 'Windows':
                os.startfile(pdf_path)
            elif system == 'Darwin':  # macOS
                subprocess.run(['open', pdf_path], check=True)
            else:  # Linux
                subprocess.run(['xdg-open', pdf_path], check=True)
                
            return True
        except Exception as e:
            print(f"Error opening PDF: {e}")
            return False
    
    def _print_to_printer(self, pdf_path: str, printer_name: Optional[str] = None) -> bool:
        """Print a PDF file to a printer."""
        try:
            system = platform.system()
            
            if system == 'Windows':
                if printer_name:
                    # Print to specific printer
                    subprocess.run(['SumatraPDF', '-print-to', printer_name, pdf_path], check=True)
                else:
                    # Print to default printer
                    subprocess.run(['SumatraPDF', '-print-to-default', pdf_path], check=True)
            elif system == 'Darwin':  # macOS
                if printer_name:
                    subprocess.run(['lpr', '-P', printer_name, pdf_path], check=True)
                else:
                    subprocess.run(['lpr', pdf_path], check=True)
            else:  # Linux
                if printer_name:
                    subprocess.run(['lpr', '-P', printer_name, pdf_path], check=True)
                else:
                    subprocess.run(['lpr', pdf_path], check=True)
                    
            return True
        except Exception as e:
            print(f"Error printing to printer: {e}")
            return False

# Create a singleton instance
print_manager = PrintManager() 