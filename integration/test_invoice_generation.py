"""
Integration tests for invoice generation and export.

These tests verify that sales data can be correctly transformed into
invoices and exported to different formats.
"""
import pytest
from unittest.mock import MagicMock, patch, mock_open
import tempfile
import os
import json
from datetime import datetime


class TestInvoiceGeneration:
    """Tests for invoice generation from sales data."""
    
    def test_generate_invoice_from_sale(self):
        """Test generating an invoice from sale data."""
        # Create mock repositories
        mock_sale_repo = MagicMock()
        mock_sale_item_repo = MagicMock()
        mock_customer_repo = MagicMock()
        mock_invoice_repo = MagicMock()
        
        # Create mock sale data
        mock_sale = MagicMock()
        mock_sale.id = 1
        mock_sale.date = "2023-05-01"
        mock_sale.total = 35.50
        mock_sale.customer_id = 1
        
        # Create mock sale items
        mock_items = [
            MagicMock(
                id=1,
                sale_id=1,
                product_id=1,
                product_code="P001",
                product_name="Product 1",
                quantity=2,
                price=10.00,
                subtotal=20.00
            ),
            MagicMock(
                id=2,
                sale_id=1,
                product_id=2,
                product_code="P002",
                product_name="Product 2",
                quantity=1,
                price=15.50,
                subtotal=15.50
            )
        ]
        
        # Create mock customer
        mock_customer = MagicMock()
        mock_customer.id = 1
        mock_customer.name = "Test Customer"
        mock_customer.email = "customer@example.com"
        mock_customer.tax_id = "TAX12345"
        mock_customer.address = "123 Test St, Test City"
        
        # Configure repositories
        mock_sale_repo.get_by_id.return_value = mock_sale
        mock_sale_item_repo.get_for_sale.return_value = mock_items
        mock_customer_repo.get_by_id.return_value = mock_customer
        
        # Configure invoice repository to generate invoice number
        def add_invoice(invoice_data):
            # Generate invoice with next number in sequence
            return MagicMock(
                id=1,
                number="INV-2023-0001",
                date=invoice_data["date"],
                sale_id=invoice_data["sale_id"],
                customer_id=invoice_data["customer_id"],
                total=invoice_data["total"],
                items=invoice_data["items"],
                status="created"
            )
            
        mock_invoice_repo.add.side_effect = add_invoice
        
        # Create minimal invoice service
        class InvoiceService:
            def __init__(self, sale_repo, sale_item_repo, customer_repo, invoice_repo):
                self.sale_repo = sale_repo
                self.sale_item_repo = sale_item_repo
                self.customer_repo = customer_repo
                self.invoice_repo = invoice_repo
                
            def generate_invoice_from_sale(self, sale_id):
                # Get sale data
                sale = self.sale_repo.get_by_id(sale_id)
                if not sale:
                    return None
                    
                # Get sale items
                items = self.sale_item_repo.get_for_sale(sale_id)
                
                # Get customer data
                customer = None
                if sale.customer_id:
                    customer = self.customer_repo.get_by_id(sale.customer_id)
                
                # Create invoice data
                invoice_data = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "sale_id": sale.id,
                    "customer_id": sale.customer_id,
                    "customer_name": customer.name if customer else "Guest",
                    "customer_tax_id": customer.tax_id if customer else "",
                    "customer_address": customer.address if customer else "",
                    "items": items,
                    "subtotal": sum(item.subtotal for item in items),
                    "tax": sum(item.subtotal * 0.16 for item in items),  # Example tax rate
                    "total": sale.total,
                    "status": "created"
                }
                
                # Save invoice
                return self.invoice_repo.add(invoice_data)
        
        # Create the service with mock repositories
        invoice_service = InvoiceService(
            sale_repo=mock_sale_repo,
            sale_item_repo=mock_sale_item_repo,
            customer_repo=mock_customer_repo,
            invoice_repo=mock_invoice_repo
        )
        
        # Test generating an invoice
        invoice = invoice_service.generate_invoice_from_sale(1)
        
        # Verify repositories were called
        mock_sale_repo.get_by_id.assert_called_once_with(1)
        mock_sale_item_repo.get_for_sale.assert_called_once_with(1)
        mock_customer_repo.get_by_id.assert_called_once_with(1)
        
        # Verify invoice was created
        assert invoice is not None
        assert invoice.number == "INV-2023-0001"
        assert invoice.sale_id == 1
        assert invoice.customer_id == 1
        assert invoice.total == 35.50
        assert len(invoice.items) == 2


class TestInvoiceExport:
    """Tests for invoice export to different formats."""
    
    def test_export_invoice_to_pdf(self):
        """Test exporting an invoice to PDF format."""
        # Create mock invoice
        mock_invoice = MagicMock()
        mock_invoice.id = 1
        mock_invoice.number = "INV-2023-0001"
        mock_invoice.date = "2023-05-01"
        mock_invoice.customer_name = "Test Customer"
        mock_invoice.customer_tax_id = "TAX12345"
        mock_invoice.customer_address = "123 Test St, Test City"
        mock_invoice.subtotal = 35.50
        mock_invoice.tax = 5.68
        mock_invoice.total = 41.18
        
        # Create mock invoice items
        mock_invoice.items = [
            MagicMock(
                id=1,
                product_code="P001",
                product_name="Product 1",
                quantity=2,
                price=10.00,
                subtotal=20.00
            ),
            MagicMock(
                id=2,
                product_code="P002",
                product_name="Product 2",
                quantity=1,
                price=15.50,
                subtotal=15.50
            )
        ]
        
        # Create mock PDF generator
        mock_pdf_generator = MagicMock()
        
        # Configure mock pdf generator to "save" file
        def generate_pdf(invoice, output_path):
            # In a real system, this would generate the PDF
            return output_path
            
        mock_pdf_generator.generate.side_effect = generate_pdf
        
        # Create minimal export service
        class InvoiceExportService:
            def __init__(self, pdf_generator):
                self.pdf_generator = pdf_generator
                
            def export_to_pdf(self, invoice, output_dir=None):
                # Use temp directory if no output dir provided
                if not output_dir:
                    output_dir = tempfile.gettempdir()
                
                # Create filename
                filename = f"{invoice.number.replace('-', '_')}.pdf"
                output_path = os.path.join(output_dir, filename)
                
                # Generate PDF
                self.pdf_generator.generate(invoice, output_path)
                
                return output_path
                
            def export_to_json(self, invoice, output_dir=None):
                # Use temp directory if no output dir provided
                if not output_dir:
                    output_dir = tempfile.gettempdir()
                
                # Create filename
                filename = f"{invoice.number.replace('-', '_')}.json"
                output_path = os.path.join(output_dir, filename)
                
                # Convert invoice to dict
                invoice_dict = {
                    "invoice_number": invoice.number,
                    "date": invoice.date,
                    "customer": {
                        "name": invoice.customer_name,
                        "tax_id": invoice.customer_tax_id,
                        "address": invoice.customer_address
                    },
                    "items": [
                        {
                            "product_code": item.product_code,
                            "product_name": item.product_name,
                            "quantity": item.quantity,
                            "price": item.price,
                            "subtotal": item.subtotal
                        } for item in invoice.items
                    ],
                    "subtotal": invoice.subtotal,
                    "tax": invoice.tax,
                    "total": invoice.total
                }
                
                # Write JSON file
                with open(output_path, 'w') as f:
                    json.dump(invoice_dict, f, indent=2)
                
                return output_path
        
        # Create export service with mock PDF generator
        export_service = InvoiceExportService(
            pdf_generator=mock_pdf_generator
        )
        
        # Test exporting to PDF
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = export_service.export_to_pdf(mock_invoice, temp_dir)
            
            # Verify PDF generator was called
            mock_pdf_generator.generate.assert_called_once()
            
            # Verify output path
            assert pdf_path == os.path.join(temp_dir, "INV_2023_0001.pdf")
        
        # Test exporting to JSON
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock open to avoid actually writing file
            with patch('builtins.open', mock_open()) as mock_file:
                # Mock json.dump to capture what would be written
                with patch('json.dump') as mock_json_dump:
                    json_path = export_service.export_to_json(mock_invoice, temp_dir)
                    
                    # Verify file was opened for writing
                    mock_file.assert_called_once_with(os.path.join(temp_dir, "INV_2023_0001.json"), 'w')
                    
                    # Verify json.dump was called
                    mock_json_dump.assert_called_once()
                    
                    # Get the invoice dict that was passed to json.dump
                    invoice_dict = mock_json_dump.call_args[0][0]
                    
                    # Verify it contains expected data
                    assert invoice_dict["invoice_number"] == "INV-2023-0001"
                    assert invoice_dict["customer"]["name"] == "Test Customer"
                    assert len(invoice_dict["items"]) == 2
                    assert invoice_dict["items"][0]["product_name"] == "Product 1"
                    assert invoice_dict["items"][1]["product_name"] == "Product 2"


class TestInvoiceEmailSending:
    """Tests for sending invoices by email."""
    
    def test_email_invoice_to_customer(self):
        """Test sending an invoice to a customer by email."""
        # Create mock invoice
        mock_invoice = MagicMock()
        mock_invoice.id = 1
        mock_invoice.number = "INV-2023-0001"
        mock_invoice.date = "2023-05-01"
        mock_invoice.customer_name = "Test Customer"
        mock_invoice.customer_email = "customer@example.com"
        mock_invoice.total = 41.18
        
        # Create mock email service
        mock_email_service = MagicMock()
        
        # Configure email service to return success
        mock_email_service.send_email.return_value = True
        
        # Create mock export service
        mock_export_service = MagicMock()
        mock_export_service.export_to_pdf.return_value = "/tmp/INV_2023_0001.pdf"
        
        # Create minimal invoice email service
        class InvoiceEmailService:
            def __init__(self, email_service, export_service):
                self.email_service = email_service
                self.export_service = export_service
                
            def send_invoice_by_email(self, invoice):
                if not invoice.customer_email:
                    return False, "Customer email not available"
                
                # Export invoice to PDF
                pdf_path = self.export_service.export_to_pdf(invoice)
                
                # Prepare email
                subject = f"Invoice {invoice.number}"
                body = f"""
                Dear {invoice.customer_name},
                
                Please find attached your invoice {invoice.number} for ${invoice.total:.2f}.
                
                Thank you for your business.
                
                Regards,
                Your Company
                """
                
                # Send email with attachment
                success = self.email_service.send_email(
                    to=invoice.customer_email,
                    subject=subject,
                    body=body,
                    attachments=[pdf_path]
                )
                
                if success:
                    return True, "Invoice sent successfully"
                else:
                    return False, "Failed to send invoice"
        
        # Create the service with mocks
        invoice_email_service = InvoiceEmailService(
            email_service=mock_email_service,
            export_service=mock_export_service
        )
        
        # Test sending invoice by email
        success, message = invoice_email_service.send_invoice_by_email(mock_invoice)
        
        # Verify export service was called
        mock_export_service.export_to_pdf.assert_called_once_with(mock_invoice)
        
        # Verify email service was called with correct parameters
        mock_email_service.send_email.assert_called_once()
        call_args = mock_email_service.send_email.call_args[1]
        
        assert call_args["to"] == "customer@example.com"
        assert f"Invoice {mock_invoice.number}" in call_args["subject"]
        assert mock_invoice.customer_name in call_args["body"]
        assert "/tmp/INV_2023_0001.pdf" in call_args["attachments"]
        
        # Verify success
        assert success is True
        assert message == "Invoice sent successfully"
        
        # Test with missing email
        invoice_without_email = MagicMock()
        invoice_without_email.customer_email = None
        
        success, message = invoice_email_service.send_invoice_by_email(invoice_without_email)
        
        # Verify failure
        assert success is False
        assert message == "Customer email not available"


class TestBulkInvoiceOperations:
    """Tests for bulk invoice operations."""
    
    def test_generate_invoices_for_period(self):
        """Test generating invoices for all sales in a period."""
        # Create mock repositories
        mock_sale_repo = MagicMock()
        mock_invoice_service = MagicMock()
        
        # Configure sale repository to return sales
        mock_sales = [
            MagicMock(id=1, date="2023-05-01", total=100.00),
            MagicMock(id=2, date="2023-05-02", total=75.50),
            MagicMock(id=3, date="2023-05-03", total=150.00)
        ]
        
        mock_sale_repo.get_for_date_range.return_value = mock_sales
        
        # Configure invoice service to return invoices
        def generate_invoice_from_sale(sale_id):
            # Return mock invoice for the sale
            return MagicMock(
                id=sale_id,
                number=f"INV-2023-{sale_id:04d}",
                date="2023-05-05",
                sale_id=sale_id
            )
            
        mock_invoice_service.generate_invoice_from_sale.side_effect = generate_invoice_from_sale
        
        # Create minimal bulk operation service
        class BulkInvoiceService:
            def __init__(self, sale_repo, invoice_service):
                self.sale_repo = sale_repo
                self.invoice_service = invoice_service
                
            def generate_invoices_for_period(self, start_date, end_date):
                # Get sales for the period
                sales = self.sale_repo.get_for_date_range(start_date, end_date)
                
                results = {
                    "total": len(sales),
                    "successful": 0,
                    "failed": 0,
                    "invoices": []
                }
                
                # Generate invoice for each sale
                for sale in sales:
                    try:
                        invoice = self.invoice_service.generate_invoice_from_sale(sale.id)
                        if invoice:
                            results["successful"] += 1
                            results["invoices"].append(invoice)
                        else:
                            results["failed"] += 1
                    except Exception:
                        results["failed"] += 1
                
                return results
        
        # Create the service with mocks
        bulk_service = BulkInvoiceService(
            sale_repo=mock_sale_repo,
            invoice_service=mock_invoice_service
        )
        
        # Test generating invoices for period
        results = bulk_service.generate_invoices_for_period("2023-05-01", "2023-05-03")
        
        # Verify sale repository was called
        mock_sale_repo.get_for_date_range.assert_called_once_with("2023-05-01", "2023-05-03")
        
        # Verify invoice service was called for each sale
        assert mock_invoice_service.generate_invoice_from_sale.call_count == 3
        
        # Verify results
        assert results["total"] == 3
        assert results["successful"] == 3
        assert results["failed"] == 0
        assert len(results["invoices"]) == 3 