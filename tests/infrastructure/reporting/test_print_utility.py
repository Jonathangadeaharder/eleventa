"""
Unit tests for the PrintManager class in the print_utility module.
"""
import os
import pytest
import tempfile
from datetime import datetime
from unittest.mock import patch, MagicMock, call

from infrastructure.reporting.print_utility import (
    PrintManager, PrintType, PrintDestination, print_manager
)


@pytest.mark.unit
class TestPrintManager:
    """Test the PrintManager class functionality."""
    
    def setup_method(self):
        """Set up test data."""
        # Mock the Config module directly before PrintManager is instantiated
        with patch('config.Config') as mock_config:
            # Set up mock config values
            mock_config.STORE_NAME = "Test Store"
            mock_config.STORE_ADDRESS = "123 Test St"
            mock_config.STORE_PHONE = "555-1234"
            mock_config.STORE_CUIT = "30-12345678-9"
            mock_config.STORE_IVA_CONDITION = "Test Condition"
            
            # Also patch the builders to avoid constructor issues
            with patch('infrastructure.reporting.print_utility.ReportBuilder'), \
                 patch('infrastructure.reporting.print_utility.InvoiceBuilder'):
                
                # Create a test PrintManager instance with everything mocked
                self.print_manager = PrintManager()
                
                # Reset store_info to ensure tests don't depend on the Config values
                self.print_manager.store_info = None
        
        # Sample test data for different print types
        self.report_data = {
            'title': 'Test Report',
            'report_type': 'test_report',
            'timestamp': '2025-05-01_12-00-00',
            'start_date': '2025-05-01',
            'end_date': '2025-05-01',
            'total_sales': 1000.0,
            'num_sales': 10
        }
        
        self.receipt_data = {
            'sale': MagicMock(
                id=1001,
                timestamp=datetime(2025, 5, 1, 12, 0, 0),
                items=[],
                total_amount=500.0
            )
        }
        
        self.invoice_data = {
            'invoice': MagicMock(
                id=2001,
                timestamp=datetime(2025, 5, 1, 12, 0, 0),
                customer=MagicMock(name="Test Customer"),
                total_amount=750.0
            ),
            'timestamp': '2025-05-01_12-00-00'
        }
        
        self.cash_drawer_data = {
            'title': 'Cash Drawer Report',
            'drawer_id': 1,
            'drawer_data': {
                'is_open': True,
                'current_balance': 1000.0,
                'initial_amount': 500.0,
                'total_in': 700.0,
                'total_out': 200.0,
                'opened_at': '2025-05-01 09:00:00',
                'opened_by': 1,
                'entries_today': []
            },
            'timestamp': '2025-05-01_12-00-00'
        }
    
    def test_init(self):
        """Test that PrintManager initializes correctly."""
        # Mock the ReportBuilder and InvoiceBuilder constructors
        with patch('infrastructure.reporting.print_utility.ReportBuilder') as mock_report_builder, \
             patch('infrastructure.reporting.print_utility.InvoiceBuilder') as mock_invoice_builder, \
             patch('infrastructure.reporting.print_utility.os.makedirs') as mock_makedirs, \
             patch('config.Config') as mock_config:
            
            # Create a new PrintManager
            pm = PrintManager()
            
            # Test that the directories are created
            mock_makedirs.assert_any_call(pm.default_pdf_dir, exist_ok=True)
            mock_makedirs.assert_any_call(pm.receipt_dir, exist_ok=True)
            
            # Test that the report builders are initialized
            mock_report_builder.assert_called_once()
            mock_invoice_builder.assert_called_once()
            
            # Store info should have been initialized
            assert pm.store_info is not None
    
    def test_get_store_info(self):
        """Test the _get_store_info method."""
        with patch('config.Config') as mock_config:
            # Set up mock config values
            mock_config.STORE_NAME = "Test Store"
            mock_config.STORE_ADDRESS = "123 Test St"
            mock_config.STORE_PHONE = "555-1234"
            mock_config.STORE_CUIT = "30-12345678-9"
            mock_config.STORE_IVA_CONDITION = "Test Condition"
            
            # Call the method - this should populate the store_info cache
            store_info = self.print_manager._get_store_info()
            
            # Check the results
            assert store_info["name"] == "Test Store"
            assert store_info["address"] == "123 Test St"
            assert store_info["phone"] == "555-1234"
            assert store_info["tax_id"] == "30-12345678-9"
            assert store_info["iva_condition"] == "Test Condition"
            
            # Check that store_info is cached
            assert self.print_manager.store_info is store_info
    
    def test_generate_report(self):
        """Test the _generate_report method."""
        # Mock the report_builder
        self.print_manager.report_builder = MagicMock()
        self.print_manager.report_builder.generate_report_pdf.return_value = True
        
        # Test with provided filename
        test_filename = f"{self.print_manager.default_pdf_dir}/test_report.pdf"
        
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(test_filename), exist_ok=True)
        
        # Test with provided filename
        result = self.print_manager._generate_report(self.report_data, test_filename)
        
        # Check that the method returned the filename
        assert result == test_filename
        
        # Check that report_builder.generate_report_pdf was called correctly
        self.print_manager.report_builder.generate_report_pdf.assert_called_once_with(
            report_title=self.report_data['title'],
            report_data=self.report_data,
            filename=test_filename,
            is_landscape=False
        )
        
        # Reset the mock
        self.print_manager.report_builder.reset_mock()
        
        # Test with auto-generated filename
        result = self.print_manager._generate_report(self.report_data)
        
        # Check that a PDF filename was generated
        assert result.endswith('.pdf')
        assert 'test_report' in result
        assert self.report_data['timestamp'] in result
        
        # Check that report_builder.generate_report_pdf was called
        self.print_manager.report_builder.generate_report_pdf.assert_called_once()
        
        # Test with failure
        self.print_manager.report_builder.generate_report_pdf.return_value = False
        
        # Should raise RuntimeError
        with pytest.raises(RuntimeError):
            self.print_manager._generate_report(self.report_data)
    
    def test_generate_receipt(self):
        """Test the _generate_receipt method."""
        # Mock the receipt generation function
        with patch('infrastructure.reporting.print_utility.generate_receipt_pdf') as mock_generate:
            # Set up the mock to return the filename
            mock_generate.return_value = "test_receipt.pdf"
            
            # Mock the _get_store_info method
            self.print_manager._get_store_info = MagicMock(return_value={"name": "Test Store"})
            
            # Call the method with auto-generated filename
            result = self.print_manager._generate_receipt(self.receipt_data)
            
            # Check that the method returned the filename from generate_receipt_pdf
            assert result == "test_receipt.pdf"
            
            # Check that generate_receipt_pdf was called correctly
            mock_generate.assert_called_once_with(
                self.receipt_data['sale'],
                self.print_manager._get_store_info.return_value,
                mock_generate.call_args[0][2]  # The auto-generated filename
            )
            
            # Check the auto-generated filename format
            filename_arg = mock_generate.call_args[0][2]
            assert filename_arg.startswith(self.print_manager.receipt_dir)
            assert "receipt_" in filename_arg
            assert filename_arg.endswith(".pdf")
            
            # Reset the mock
            mock_generate.reset_mock()
            
            # Test with provided filename
            test_filename = "custom_receipt.pdf"
            result = self.print_manager._generate_receipt(self.receipt_data, test_filename)
            
            # Check that the method returned the filename
            assert result == "test_receipt.pdf"
            
            # Check that generate_receipt_pdf was called with the custom filename
            mock_generate.assert_called_once_with(
                self.receipt_data['sale'],
                self.print_manager._get_store_info.return_value,
                test_filename
            )
    
    def test_generate_invoice(self):
        """Test the _generate_invoice method."""
        # Mock the invoice_builder
        self.print_manager.invoice_builder = MagicMock()
        self.print_manager.invoice_builder.generate_invoice_pdf.return_value = "test_invoice.pdf"
        
        # Call the method with auto-generated filename
        result = self.print_manager._generate_invoice(self.invoice_data)
        
        # Check that the method returned the filename
        assert result == "test_invoice.pdf"
        
        # Check that invoice_builder.generate_invoice_pdf was called correctly
        self.print_manager.invoice_builder.generate_invoice_pdf.assert_called_once_with(
            self.invoice_data['invoice'],
            self.print_manager.invoice_builder.generate_invoice_pdf.call_args[0][1]  # The auto-generated filename
        )
        
        # Check the auto-generated filename format
        filename_arg = self.print_manager.invoice_builder.generate_invoice_pdf.call_args[0][1]
        assert filename_arg.startswith(self.print_manager.default_pdf_dir)
        assert "invoice_" in filename_arg
        assert self.invoice_data['timestamp'] in filename_arg
        assert filename_arg.endswith(".pdf")
        
        # Reset the mock
        self.print_manager.invoice_builder.reset_mock()
        
        # Test with provided filename
        test_filename = "custom_invoice.pdf"
        result = self.print_manager._generate_invoice(self.invoice_data, test_filename)
        
        # Check that the method returned the filename
        assert result == "test_invoice.pdf"
        
        # Check that invoice_builder.generate_invoice_pdf was called with the custom filename
        self.print_manager.invoice_builder.generate_invoice_pdf.assert_called_once_with(
            self.invoice_data['invoice'],
            test_filename
        )
    
    def test_generate_cash_drawer_report(self):
        """Test the _generate_cash_drawer_report method."""
        # Mock the report_builder
        self.print_manager.report_builder = MagicMock()
        self.print_manager.report_builder.generate_report_pdf.return_value = True
        
        # Call the method with auto-generated filename
        result = self.print_manager._generate_cash_drawer_report(self.cash_drawer_data)
        
        # Check that the method returned the auto-generated filename
        assert result is not None
        assert result.endswith(".pdf")
        
        # Check that report_builder.generate_report_pdf was called correctly
        self.print_manager.report_builder.generate_report_pdf.assert_called_once()
        args, kwargs = self.print_manager.report_builder.generate_report_pdf.call_args
        
        # Check the report title
        assert kwargs['report_title'] == self.cash_drawer_data['title']
        
        # Check that the report data was formatted correctly
        assert 'drawer_id' in kwargs['report_data']
        assert kwargs['report_data']['drawer_id'] == self.cash_drawer_data['drawer_id']
        assert kwargs['report_data']['is_open'] == self.cash_drawer_data['drawer_data']['is_open']
        
        # Check the auto-generated filename format
        filename_arg = kwargs['filename']
        assert filename_arg.startswith(self.print_manager.default_pdf_dir)
        assert "cash_drawer_" in filename_arg
        assert str(self.cash_drawer_data['drawer_id']) in filename_arg
        assert self.cash_drawer_data['timestamp'] in filename_arg
        assert filename_arg.endswith(".pdf")
        
        # Reset the mock
        self.print_manager.report_builder.reset_mock()
        
        # Test with provided filename
        test_filename = "custom_cash_drawer.pdf"
        result = self.print_manager._generate_cash_drawer_report(self.cash_drawer_data, test_filename)
        
        # Check that the method returned the filename
        assert result == test_filename
        
        # Check that report_builder.generate_report_pdf was called with the custom filename
        self.print_manager.report_builder.generate_report_pdf.assert_called_once()
        args, kwargs = self.print_manager.report_builder.generate_report_pdf.call_args
        assert kwargs['filename'] == test_filename
        
        # Test with failure
        self.print_manager.report_builder.generate_report_pdf.return_value = False
        
        # Should raise RuntimeError
        with pytest.raises(RuntimeError):
            self.print_manager._generate_cash_drawer_report(self.cash_drawer_data)
    
    def test_open_pdf(self):
        """Test the _open_pdf method."""
        # Create different patch objects for each platform
        with patch('infrastructure.reporting.print_utility.platform.system') as mock_system, \
             patch('infrastructure.reporting.print_utility.os.startfile') as mock_startfile, \
             patch('infrastructure.reporting.print_utility.subprocess.run') as mock_run:
            
            # Test Windows platform
            mock_system.return_value = 'Windows'
            
            # Call the method
            result = self.print_manager._open_pdf("test.pdf")
            
            # Check that the method returned True
            assert result is True
            
            # Check that os.startfile was called correctly
            mock_startfile.assert_called_once_with("test.pdf")
            mock_run.assert_not_called()
            
            # Reset mocks
            mock_startfile.reset_mock()
            mock_run.reset_mock()
            
            # Test macOS platform
            mock_system.return_value = 'Darwin'
            
            # Call the method
            result = self.print_manager._open_pdf("test.pdf")
            
            # Check that the method returned True
            assert result is True
            
            # Check that subprocess.run was called correctly
            mock_startfile.assert_not_called()
            mock_run.assert_called_once_with(['open', "test.pdf"], check=True)
            
            # Reset mocks
            mock_run.reset_mock()
            
            # Test Linux platform
            mock_system.return_value = 'Linux'
            
            # Call the method
            result = self.print_manager._open_pdf("test.pdf")
            
            # Check that the method returned True
            assert result is True
            
            # Check that subprocess.run was called correctly
            mock_run.assert_called_once_with(['xdg-open', "test.pdf"], check=True)
            
            # Test exception handling
            mock_run.side_effect = Exception("Test error")
            
            # Call the method
            result = self.print_manager._open_pdf("test.pdf")
            
            # Check that the method returned False
            assert result is False
    
    def test_print_to_printer(self):
        """Test the _print_to_printer method."""
        # Create different patch objects for each platform
        with patch('infrastructure.reporting.print_utility.platform.system') as mock_system, \
             patch('infrastructure.reporting.print_utility.subprocess.run') as mock_run:
            
            # Test Windows platform with default printer
            mock_system.return_value = 'Windows'
            
            # Call the method
            result = self.print_manager._print_to_printer("test.pdf")
            
            # Check that the method returned True
            assert result is True
            
            # Check that subprocess.run was called correctly for Windows default printer
            mock_run.assert_called_once_with(['SumatraPDF', '-print-to-default', "test.pdf"], check=True)
            
            # Reset mock
            mock_run.reset_mock()
            
            # Test Windows platform with specific printer
            result = self.print_manager._print_to_printer("test.pdf", "TestPrinter")
            
            # Check that the method returned True
            assert result is True
            
            # Check that subprocess.run was called correctly for Windows specific printer
            mock_run.assert_called_once_with(['SumatraPDF', '-print-to', "TestPrinter", "test.pdf"], check=True)
            
            # Reset mock
            mock_run.reset_mock()
            
            # Test macOS platform with default printer
            mock_system.return_value = 'Darwin'
            
            # Call the method
            result = self.print_manager._print_to_printer("test.pdf")
            
            # Check that the method returned True
            assert result is True
            
            # Check that subprocess.run was called correctly for macOS default printer
            mock_run.assert_called_once_with(['lpr', "test.pdf"], check=True)
            
            # Reset mock
            mock_run.reset_mock()
            
            # Test macOS platform with specific printer
            result = self.print_manager._print_to_printer("test.pdf", "TestPrinter")
            
            # Check that the method returned True
            assert result is True
            
            # Check that subprocess.run was called correctly for macOS specific printer
            mock_run.assert_called_once_with(['lpr', '-P', "TestPrinter", "test.pdf"], check=True)
            
            # Reset mock
            mock_run.reset_mock()
            
            # Test Linux platform
            mock_system.return_value = 'Linux'
            
            # Call the method with default printer
            result = self.print_manager._print_to_printer("test.pdf")
            
            # Check that the method returned True
            assert result is True
            
            # Check that subprocess.run was called correctly for Linux default printer
            mock_run.assert_called_once_with(['lpr', "test.pdf"], check=True)
            
            # Reset mock
            mock_run.reset_mock()
            
            # Call the method with specific printer
            result = self.print_manager._print_to_printer("test.pdf", "TestPrinter")
            
            # Check that the method returned True
            assert result is True
            
            # Check that subprocess.run was called correctly for Linux specific printer
            mock_run.assert_called_once_with(['lpr', '-P', "TestPrinter", "test.pdf"], check=True)
            
            # Test exception handling
            mock_run.side_effect = Exception("Test error")
            
            # Call the method
            result = self.print_manager._print_to_printer("test.pdf")
            
            # Check that the method returned False
            assert result is False
    
    def test_print_method(self):
        """Test the main print method."""
        with patch.object(self.print_manager, '_generate_report') as mock_generate_report, \
             patch.object(self.print_manager, '_generate_receipt') as mock_generate_receipt, \
             patch.object(self.print_manager, '_generate_invoice') as mock_generate_invoice, \
             patch.object(self.print_manager, '_generate_cash_drawer_report') as mock_generate_cash_drawer, \
             patch.object(self.print_manager, '_open_pdf') as mock_open_pdf, \
             patch.object(self.print_manager, '_print_to_printer') as mock_print_to_printer:
            
            # Set up mocks to return the test filename
            test_pdf_path = "test_output.pdf"
            mock_generate_report.return_value = test_pdf_path
            mock_generate_receipt.return_value = test_pdf_path
            mock_generate_invoice.return_value = test_pdf_path
            mock_generate_cash_drawer.return_value = test_pdf_path
            mock_open_pdf.return_value = True
            mock_print_to_printer.return_value = True
            
            # Test PrintType.REPORT with PrintDestination.PDF_FILE
            result = self.print_manager.print(
                print_type=PrintType.REPORT,
                data=self.report_data,
                destination=PrintDestination.PDF_FILE
            )
            
            # Check that the method returned the PDF path
            assert result == test_pdf_path
            
            # Check that the generate method was called
            mock_generate_report.assert_called_once_with(self.report_data, None)
            mock_open_pdf.assert_not_called()
            mock_print_to_printer.assert_not_called()
            
            # Reset mocks
            mock_generate_report.reset_mock()
            
            # Test PrintType.RECEIPT with PrintDestination.PREVIEW
            result = self.print_manager.print(
                print_type=PrintType.RECEIPT,
                data=self.receipt_data,
                destination=PrintDestination.PREVIEW
            )
            
            # Check that the method returned True
            assert result is True
            
            # Check that the generate and preview methods were called
            mock_generate_receipt.assert_called_once_with(self.receipt_data, None)
            mock_open_pdf.assert_called_once_with(test_pdf_path)
            mock_print_to_printer.assert_not_called()
            
            # Reset mocks
            mock_generate_receipt.reset_mock()
            mock_open_pdf.reset_mock()
            
            # Test PrintType.INVOICE with PrintDestination.PRINTER
            result = self.print_manager.print(
                print_type=PrintType.INVOICE,
                data=self.invoice_data,
                destination=PrintDestination.PRINTER,
                printer_name="TestPrinter"
            )
            
            # Check that the method returned True
            assert result is True
            
            # Check that the generate and print methods were called
            mock_generate_invoice.assert_called_once_with(self.invoice_data, None)
            mock_open_pdf.assert_not_called()
            mock_print_to_printer.assert_called_once_with(test_pdf_path, "TestPrinter")
            
            # Reset mocks
            mock_generate_invoice.reset_mock()
            mock_print_to_printer.reset_mock()
            
            # Test PrintType.CASH_DRAWER with PrintDestination.PDF_FILE and custom filename
            custom_filename = "custom_drawer_report.pdf"
            result = self.print_manager.print(
                print_type=PrintType.CASH_DRAWER,
                data=self.cash_drawer_data,
                destination=PrintDestination.PDF_FILE,
                filename=custom_filename
            )
            
            # Check that the method returned the PDF path
            assert result == test_pdf_path
            
            # Check that the generate method was called with the custom filename
            mock_generate_cash_drawer.assert_called_once_with(self.cash_drawer_data, custom_filename)
            
            # Test with invalid print type - by mocking the ValueError but catching it in print()
            # since the implementation catches all exceptions and returns False
            mock_generate_report.side_effect = ValueError("Invalid print type")
            
            # Call print method with an invalid type
            result = self.print_manager.print(
                print_type="INVALID_TYPE",
                data=self.report_data
            )
            
            # Check that the method returned False because the exception was caught
            assert result is False
            
            # Reset the mock and the side effect
            mock_generate_report.reset_mock()
            mock_generate_report.side_effect = None
            
            # Test with callback
            callback_mock = MagicMock()
            result = self.print_manager.print(
                print_type=PrintType.REPORT,
                data=self.report_data,
                destination=PrintDestination.PDF_FILE,
                callback=callback_mock
            )
            
            # Check that the callback was called with the correct arguments
            callback_mock.assert_called_once_with(test_pdf_path, True)
            
            # Test error handling
            mock_generate_report.side_effect = Exception("Test error")
            
            # Should not raise exception but return False
            result = self.print_manager.print(
                print_type=PrintType.REPORT,
                data=self.report_data
            )
            
            # Check that the method returned False
            assert result is False
            
            # Test callback on error
            callback_mock.reset_mock()
            result = self.print_manager.print(
                print_type=PrintType.REPORT,
                data=self.report_data,
                callback=callback_mock
            )
            
            # Check that the callback was called with empty path and False
            callback_mock.assert_called_once_with("", False)
    
    @patch('infrastructure.reporting.print_utility.ReportBuilder')
    @patch('infrastructure.reporting.print_utility.InvoiceBuilder')
    @patch('config.Config')
    def test_singleton_instance(self, mock_config, mock_invoice_builder, mock_report_builder):
        """Test that the singleton print_manager instance is created correctly."""
        from infrastructure.reporting.print_utility import print_manager
        
        # Check that print_manager is an instance of PrintManager
        assert isinstance(print_manager, PrintManager)
        
        # Ensure the directories exist
        assert os.path.exists(print_manager.default_pdf_dir)
        assert os.path.exists(print_manager.receipt_dir)


if __name__ == '__main__':
    pytest.main(['-xvs', __file__]) 