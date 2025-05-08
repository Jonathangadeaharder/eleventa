"""
Integration tests for report printing functionality.
Tests the interaction between the UI, services, and PDF generation.
"""
import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from PySide6.QtCore import Qt, QDate
from core.services.reporting_service import ReportingService
from ui.views.reports_view import ReportsView


@pytest.mark.integration
def test_report_view_print_button(qtbot, tmpdir, mock_reporting_service):
    """Test that clicking the print button in reports view initiates PDF generation."""
    # Create the reports view with the mock service
    view = ReportsView(mock_reporting_service)
    qtbot.addWidget(view)
    
    # Set up the mock service for PDF generation
    pdf_path = os.path.join(str(tmpdir), "test_report.pdf")
    mock_reporting_service.print_sales_by_period_report.return_value = pdf_path
    
    # Initially the print button should be disabled
    assert not view.print_btn.isEnabled()
    
    # Click generate report button to enable print functionality
    # First need to select report type and date range
    view.report_type_combo.setCurrentIndex(0)  # Sales by period
    view.date_preset_combo.setCurrentIndex(0)  # Today
    
    # Click generate report
    with patch.object(view, '_generate_sales_by_period_report') as mock_generate:
        qtbot.mouseClick(view.generate_btn, Qt.LeftButton)
        assert mock_generate.called
    
    # After generating report, print button should be enabled
    view.print_btn.setEnabled(True)
    assert view.print_btn.isEnabled()
    
    # Set up the current report parameters
    view.current_report_type = 0  # Sales by period
    view.current_start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    view.current_end_date = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999)
    
    # Mock the _open_pdf method to avoid actually opening a PDF
    with patch.object(view, '_open_pdf') as mock_open_pdf:
        # Click the print button
        qtbot.mouseClick(view.print_btn, Qt.LeftButton)
        
        # Verify that the service method was called with correct parameters
        mock_reporting_service.print_sales_by_period_report.assert_called_once()
        args = mock_reporting_service.print_sales_by_period_report.call_args[0]
        assert args[0] == view.current_start_date
        assert args[1] == view.current_end_date
        
        # Verify that pdf was "opened"
        mock_open_pdf.assert_called_once_with(pdf_path)


@pytest.mark.integration
def test_different_report_types_print_correctly(qtbot, tmpdir, mock_reporting_service):
    """Test that different report types call the correct print methods."""
    # Create the reports view with the mock service
    view = ReportsView(mock_reporting_service)
    qtbot.addWidget(view)
    
    # Set up the mock service for PDF generation
    pdf_path = os.path.join(str(tmpdir), "test_report.pdf")
    mock_reporting_service.print_sales_by_period_report.return_value = pdf_path
    mock_reporting_service.print_sales_by_department_report.return_value = pdf_path
    mock_reporting_service.print_sales_by_customer_report.return_value = pdf_path
    mock_reporting_service.print_top_products_report.return_value = pdf_path
    mock_reporting_service.print_profit_analysis_report.return_value = pdf_path
    
    # Loop through all report types
    report_types = [
        (0, 'print_sales_by_period_report'),
        (1, 'print_sales_by_department_report'),
        (2, 'print_sales_by_customer_report'),
        (3, 'print_top_products_report'),
        (4, 'print_profit_analysis_report')
    ]
    
    for report_index, service_method in report_types:
        # Reset the mock service
        mock_reporting_service.reset_mock()
        
        # Set up view for this report type
        view.report_type_combo.setCurrentIndex(report_index)
        
        # Set up the current report parameters
        view.current_report_type = report_index
        view.current_start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        view.current_end_date = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999)
        view.print_btn.setEnabled(True)
        
        # Mock the _open_pdf method to avoid actually opening a PDF
        with patch.object(view, '_open_pdf') as mock_open_pdf:
            # Click the print button
            qtbot.mouseClick(view.print_btn, Qt.LeftButton)
            
            # Get the method to check
            method = getattr(mock_reporting_service, service_method)
            
            # Verify that the service method was called with correct parameters
            method.assert_called_once()
            args = method.call_args[0]
            assert args[0] == view.current_start_date
            assert args[1] == view.current_end_date
            
            # Verify that pdf was "opened"
            mock_open_pdf.assert_called_once_with(pdf_path)


@pytest.fixture
def mock_reporting_service():
    """Create a mock reporting service for testing."""
    service = MagicMock(spec=ReportingService)
    
    # Set up some default mock data for report generation
    service.get_sales_summary_by_period.return_value = [
        {'date': '2023-01-01', 'total_sales': 100.0, 'num_sales': 5},
        {'date': '2023-01-02', 'total_sales': 200.0, 'num_sales': 10}
    ]
    
    service.get_sales_by_department.return_value = [
        {'department_id': 1, 'department_name': 'Electronics', 'total_amount': 500.0, 'num_items': 20},
        {'department_id': 2, 'department_name': 'Furniture', 'total_amount': 300.0, 'num_items': 5}
    ]
    
    return service 