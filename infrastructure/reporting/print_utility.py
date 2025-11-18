"""
Central printing utility for all printing tasks in the application.
This handles printing to PDF files, real printers, and print previews.
"""

import os
import platform
import subprocess
from enum import Enum
from typing import Dict, Any, Optional, Callable, Union
from datetime import datetime
import logging

# Import existing report builders
from infrastructure.reporting.report_builder import ReportBuilder
from infrastructure.reporting.receipt_builder import generate_receipt_pdf
from infrastructure.reporting.invoice_builder import InvoiceBuilder

# Configure basic logging (after imports to avoid E402)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s",
)


# Class to represent different print outputs
class PrintDestination(Enum):
    PDF_FILE = "pdf_file"  # Save to PDF file
    PRINTER = "printer"  # Send directly to printer
    PREVIEW = "preview"  # Open in PDF viewer


class PrintType(Enum):
    REPORT = "report"  # Business reports
    RECEIPT = "receipt"  # Sales receipts
    INVOICE = "invoice"  # Customer invoices
    CASH_DRAWER = "cash_drawer"  # Cash drawer reports


class PrintManager:
    """
    Centralized print management for the application.
    Handles printing to different destinations and manages
    document generation.
    """

    def __init__(self):
        """Initialize the print manager with default settings."""
        # Get the absolute path of the script's directory
        base_dir = os.path.abspath(os.path.dirname(__file__))
        # For robustness, ensure the script is in a known location relative to project root or use a dedicated project root function
        # Assuming this script is in infrastructure/reporting, to get project root:
        project_root = os.path.abspath(os.path.join(base_dir, "..", ".."))

        self.default_pdf_dir = os.path.join(project_root, "pdfs")
        self.receipt_dir = os.path.join(project_root, "receipts")

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
            from config import config

            self.store_info = {
                "name": config.STORE_NAME or "Eleventa Demo Store",
                "address": config.STORE_ADDRESS
                or "123 Main St, Buenos Aires, Argentina",
                "phone": config.STORE_PHONE or "555-1234",
                "tax_id": config.STORE_CUIT or "30-12345678-9",
                "iva_condition": config.STORE_IVA_CONDITION or "Responsable Inscripto",
            }
        return self.store_info

    def print(
        self,
        print_type: PrintType,
        data: Dict[str, Any],
        destination: PrintDestination = PrintDestination.PDF_FILE,
        filename: Optional[str] = None,
        printer_name: Optional[str] = None,
        callback: Optional[Callable[[str, bool], None]] = None,
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
        logging.debug(
            f"PrintManager.print called with type: {print_type}, dest: {destination}, filename: {filename}"
        )
        # Update store info if it's not set (can happen if settings are changed after init)
        self._get_store_info()
        self.invoice_builder.store_info = (
            self.store_info
        )  # Ensure invoice builder also gets updated store_info

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
                logging.error(f"Invalid print type: {print_type}")
                raise ValueError(f"Invalid print type: {print_type}")

            logging.debug(f"Generated pdf_path (should be absolute): {pdf_path}")

            # Handle the output based on destination
            if destination == PrintDestination.PDF_FILE:
                # Just return the path
                result = pdf_path
            elif destination == PrintDestination.PREVIEW:
                # Open the PDF for preview
                logging.debug(f"Attempting to open for preview: {pdf_path}")
                success = self._open_pdf(pdf_path)
                if callback:
                    user_friendly_path = (
                        os.path.relpath(pdf_path, self.default_pdf_dir)
                        if pdf_path.startswith(self.default_pdf_dir)
                        else pdf_path
                    )
                    callback(user_friendly_path, success)
                return success
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

    def _generate_report(
        self, data: Dict[str, Any], filename: Optional[str] = None
    ) -> str:
        """Generate a business report PDF."""
        logging.debug(f"_generate_report received filename: {filename}")
        # Extract report parameters from data
        report_title = data.get("title", "Business Report")
        is_landscape = data.get("is_landscape", False)

        # Generate filename if not provided
        if not filename:
            timestamp = data.get("timestamp", "").replace(" ", "_").replace("/", "-")
            report_type = data.get("report_type", "report")
            # Use absolute path for filename
            filename = os.path.join(
                self.default_pdf_dir, f"{report_type}_{timestamp}.pdf"
            )
            logging.debug(f"Auto-generated absolute filename: {filename}")
        elif not os.path.isabs(filename):
            original_filename_for_log = filename
            filename = os.path.join(self.default_pdf_dir, os.path.basename(filename))
            logging.debug(
                f"Converted relative filename '{original_filename_for_log}' to absolute: {filename}"
            )
        else:
            logging.debug(f"Using provided absolute filename: {filename}")

        # Generate the report using the report builder
        success = self.report_builder.generate_report_pdf(
            report_title=report_title,
            report_data=data,
            filename=filename,
            is_landscape=is_landscape,
        )

        if not success:
            raise RuntimeError(f"Failed to generate report: {report_title}")

        return filename

    def _generate_receipt(
        self, data: Dict[str, Any], filename: Optional[str] = None
    ) -> str:
        """Generate a sales receipt PDF."""
        # Get sale and store info
        sale = data.get("sale")
        store_info = self._get_store_info()

        # Generate filename if not provided
        if not filename:
            sale_id = getattr(sale, "id", "unknown")
            timestamp = (
                getattr(sale, "timestamp", datetime.now()).strftime("%Y%m%d_%H%M%S")
                if hasattr(getattr(sale, "timestamp", None), "strftime")
                else datetime.now().strftime("%Y%m%d_%H%M%S")
            )
            # Use absolute path for filename
            filename = os.path.join(
                self.receipt_dir, f"receipt_{sale_id}_{timestamp}.pdf"
            )
        elif not os.path.isabs(filename):
            filename = os.path.join(self.receipt_dir, os.path.basename(filename))

        # Generate the receipt
        return generate_receipt_pdf(sale, store_info, filename)

    def _generate_invoice(
        self, data: Dict[str, Any], filename: Optional[str] = None
    ) -> str:
        """Generate a customer invoice PDF."""
        # Extract invoice parameters
        invoice = data.get("invoice")

        # Generate filename if not provided
        if not filename:
            invoice_id = getattr(invoice, "id", "unknown")
            timestamp = (
                data.get("timestamp", datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
                .replace(" ", "_")
                .replace("/", "-")
            )
            # Use absolute path for filename
            filename = os.path.join(
                self.default_pdf_dir, f"invoice_{invoice_id}_{timestamp}.pdf"
            )
        elif not os.path.isabs(filename):
            filename = os.path.join(self.default_pdf_dir, os.path.basename(filename))

        # Generate the invoice using the invoice builder
        return self.invoice_builder.generate_invoice_pdf(invoice, filename)

    def _generate_cash_drawer_report(
        self, data: Dict[str, Any], filename: Optional[str] = None
    ) -> str:
        """Generate a cash drawer report PDF."""
        # Extract drawer data
        drawer_id = data.get("drawer_id")
        drawer_data = data.get("drawer_data", {})
        report_title = data.get("title", "Cash Drawer Report")

        # Generate filename if not provided
        if not filename:
            timestamp = (
                data.get("timestamp", datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
                .replace(" ", "_")
                .replace("/", "-")
            )
            # Use absolute path for filename
            filename = os.path.join(
                self.default_pdf_dir, f"cash_drawer_{drawer_id}_{timestamp}.pdf"
            )
        elif not os.path.isabs(filename):
            filename = os.path.join(self.default_pdf_dir, os.path.basename(filename))

        # Prepare report data in the format expected by report builder
        report_data = {
            "drawer_id": drawer_id,
            "is_open": drawer_data.get("is_open", False),
            "current_balance": drawer_data.get("current_balance", 0),
            "initial_amount": drawer_data.get("initial_amount", 0),
            "total_in": drawer_data.get("total_in", 0),
            "total_out": drawer_data.get("total_out", 0),
            "opened_at": drawer_data.get("opened_at", ""),
            "opened_by": drawer_data.get("opened_by", ""),
            "entries": drawer_data.get("entries_today", []),
        }

        # Generate the report using the report builder
        success = self.report_builder.generate_report_pdf(
            report_title=report_title, report_data=report_data, filename=filename
        )

        if not success:
            raise RuntimeError("Failed to generate cash drawer report")

        return filename

    def _open_pdf(self, pdf_path: str) -> bool:
        """Open a PDF file with the system's default PDF viewer."""
        logging.debug(
            f"_open_pdf received path: {pdf_path}, is_abs: {os.path.isabs(pdf_path)}"
        )
        try:
            system = platform.system()

            if not os.path.isabs(pdf_path):
                logging.warning(
                    f"_open_pdf received a relative path: {pdf_path}. This might lead to errors."
                )
                # Attempt to make it absolute assuming it's relative to CWD, though this is risky
                # pdf_path = os.path.abspath(pdf_path)
                # logging.warning(f"Attempted to convert to absolute: {pdf_path}")

            if system == "Windows":
                os.startfile(pdf_path)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", pdf_path], check=True)
            else:  # Linux
                subprocess.run(["xdg-open", pdf_path], check=True)

            return True
        except Exception as e:
            print(f"Error opening PDF: {e}")
            return False

    def _print_to_printer(
        self, pdf_path: str, printer_name: Optional[str] = None
    ) -> bool:
        """Print a PDF file to a printer."""
        try:
            system = platform.system()

            if system == "Windows":
                if printer_name:
                    # Print to specific printer
                    subprocess.run(
                        ["SumatraPDF", "-print-to", printer_name, pdf_path], check=True
                    )
                else:
                    # Print to default printer
                    subprocess.run(
                        ["SumatraPDF", "-print-to-default", pdf_path], check=True
                    )
            elif system == "Darwin":  # macOS
                if printer_name:
                    subprocess.run(["lpr", "-P", printer_name, pdf_path], check=True)
                else:
                    subprocess.run(["lpr", pdf_path], check=True)
            else:  # Linux
                if printer_name:
                    subprocess.run(["lpr", "-P", printer_name, pdf_path], check=True)
                else:
                    subprocess.run(["lpr", pdf_path], check=True)

            return True
        except Exception as e:
            print(f"Error printing to printer: {e}")
            return False


# Create a singleton instance
print_manager = PrintManager()
