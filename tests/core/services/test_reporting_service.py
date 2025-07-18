import pytest
import os
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from core.models.enums import PaymentType
from core.services.reporting_service import ReportingService

class TestReportingService:
    @pytest.fixture(autouse=True)
    def setup_service(self):
        # Create service with Unit of Work pattern
        self.service = ReportingService()
        
        # Define sample date range for tests
        self.start_time = datetime(2024, 1, 1)
        self.end_time = datetime(2024, 1, 31, 23, 59, 59)

    @patch('core.services.reporting_service.unit_of_work')
    def test_get_sales_summary_by_period(self, mock_uow):
        # Define expected return value from repo
        expected_repo_return = [
            {"date": "2024-01-01", "total_sales": 100.0, "num_sales": 2}
        ]
        
        # Set up Unit of Work mock
        mock_context = MagicMock()
        mock_uow.return_value.__enter__.return_value = mock_context
        mock_context.sales.get_sales_summary_by_period.return_value = expected_repo_return

        # Call service method with required args
        result = self.service.get_sales_summary_by_period(
            self.start_time, self.end_time, group_by="day"
        )

        # Assert repo was called correctly
        mock_context.sales.get_sales_summary_by_period.assert_called_once_with(
            self.start_time, self.end_time, "day"
        )
        # Assert result matches expected repo return
        assert result == expected_repo_return

    @patch('core.services.reporting_service.unit_of_work')
    def test_get_sales_by_payment_type(self, mock_uow):
        expected_repo_return = [
            {"payment_type": PaymentType.EFECTIVO.value, "total_amount": 200.0, "num_sales": 5}  # Use correct keys from repo interface
        ]
        
        # Set up Unit of Work mock
        mock_context = MagicMock()
        mock_uow.return_value.__enter__.return_value = mock_context
        mock_context.sales.get_sales_by_payment_type.return_value = expected_repo_return
        
        result = self.service.get_sales_by_payment_type(self.start_time, self.end_time)  # Add args
        mock_context.sales.get_sales_by_payment_type.assert_called_once_with(self.start_time, self.end_time)
        assert result == expected_repo_return  # Assert against expected structure

    @patch('core.services.reporting_service.unit_of_work')
    def test_get_sales_by_department(self, mock_uow):
        expected_repo_return = [
            {"department_id": 1, "department_name": "Dept1", "total_amount": 300.0, "num_items": 10}  # Use correct keys
        ]
        
        # Set up Unit of Work mock
        mock_context = MagicMock()
        mock_uow.return_value.__enter__.return_value = mock_context
        mock_context.sales.get_sales_by_department.return_value = expected_repo_return
        
        result = self.service.get_sales_by_department(self.start_time, self.end_time)  # Add args
        mock_context.sales.get_sales_by_department.assert_called_once_with(self.start_time, self.end_time)
        assert result == expected_repo_return

    @patch('core.services.reporting_service.unit_of_work')
    def test_get_sales_by_customer(self, mock_uow):
        expected_repo_return = [
            {"customer_id": 1, "customer_name": "Cust1", "total_amount": 400.0, "num_sales": 3}  # Use correct keys
        ]
        
        # Set up Unit of Work mock
        mock_context = MagicMock()
        mock_uow.return_value.__enter__.return_value = mock_context
        mock_context.sales.get_sales_by_customer.return_value = expected_repo_return
        
        result = self.service.get_sales_by_customer(self.start_time, self.end_time, limit=5)  # Add args
        mock_context.sales.get_sales_by_customer.assert_called_once_with(self.start_time, self.end_time, 5)
        assert result == expected_repo_return

    @patch('core.services.reporting_service.unit_of_work')
    def test_get_top_selling_products(self, mock_uow):
        expected_repo_return = [
            {"product_id": 1, "product_code": "P001", "product_description": "Prod1", "quantity_sold": 10, "total_amount": 150.0}  # Use correct keys
        ]
        
        # Set up Unit of Work mock
        mock_context = MagicMock()
        mock_uow.return_value.__enter__.return_value = mock_context
        mock_context.sales.get_top_selling_products.return_value = expected_repo_return
        
        result = self.service.get_top_selling_products(self.start_time, self.end_time, limit=3)  # Add args
        mock_context.sales.get_top_selling_products.assert_called_once_with(self.start_time, self.end_time, 3)
        assert result == expected_repo_return

    @patch('core.services.reporting_service.unit_of_work')
    def test_calculate_profit_for_period(self, mock_uow):
        expected_repo_return = {
            "total_revenue": 500.0, "total_cost": 300.0, "total_profit": 200.0, "profit_margin": 0.4
        }
        
        # Set up Unit of Work mock
        mock_context = MagicMock()
        mock_uow.return_value.__enter__.return_value = mock_context
        mock_context.sales.calculate_profit_for_period.return_value = expected_repo_return
        
        result = self.service.calculate_profit_for_period(self.start_time, self.end_time)  # Add datetime objects
        mock_context.sales.calculate_profit_for_period.assert_called_once_with(self.start_time, self.end_time)
        assert result == expected_repo_return  # Assert against expected structure

    @patch('core.services.reporting_service.unit_of_work')
    def test_get_daily_sales_report(self, mock_uow):
        # Set up Unit of Work mock
        mock_context = MagicMock()
        mock_uow.return_value.__enter__.return_value = mock_context
        
        # Mock all repository calls used in get_daily_sales_report
        mock_context.sales.calculate_profit_for_period.return_value = {
            "total_revenue": 1000.0,
            "total_cost": 600.0,
            "total_profit": 400.0,
            "profit_margin": 0.4
        }
        mock_context.sales.get_sales_by_payment_type.return_value = [
            {"payment_type": "Efectivo", "num_sales": 2, "total_amount": 500.0}  # Add total_amount
        ]
        mock_context.sales.get_top_selling_products.return_value = [
            {"product_id": 1, "product_code": "P001", "product_description": "Prod1", "quantity_sold": 5, "total_amount": 100.0}
        ]
        mock_context.sales.get_sales_by_department.return_value = [
            {"department_id": 1, "department_name": "Dept1", "total_amount": 300.0, "num_items": 10}
        ]

        date = datetime(2024, 1, 1)
        result = self.service.get_daily_sales_report(date)

        # Verify calls were made with correct date ranges
        start_time = datetime.combine(date, datetime.min.time())
        end_time = datetime.combine(date, datetime.max.time())
        mock_context.sales.calculate_profit_for_period.assert_called_once_with(start_time, end_time)
        mock_context.sales.get_sales_by_payment_type.assert_called_once_with(start_time, end_time)
        mock_context.sales.get_top_selling_products.assert_called_once_with(start_time, end_time, 5)
        mock_context.sales.get_sales_by_department.assert_called_once_with(start_time, end_time)

        assert result["date"] == "2024-01-01"
        assert result["total_revenue"] == 1000.0
        assert result["total_cost"] == 600.0
        assert result["total_profit"] == 400.0
        assert result["profit_margin"] == 0.4
        assert result["sales_count"] == 2
        assert isinstance(result["payment_types"], list)
        assert isinstance(result["top_products"], list)
        assert isinstance(result["sales_by_department"], list)

    @patch('core.services.reporting_service.unit_of_work')
    def test_get_sales_trend(self, mock_uow):
        # Set up Unit of Work mock
        mock_context = MagicMock()
        mock_uow.return_value.__enter__.return_value = mock_context
        
        # Mock get_sales_summary_by_period for daily trend
        mock_context.sales.get_sales_summary_by_period.return_value = [
            {"date": "2024-01-01", "total_sales": 100.0, "num_sales": 2},
            {"date": "2024-01-03", "total_sales": 200.0, "num_sales": 3}
        ]
        
        start_time = datetime(2024, 1, 1)
        end_time = datetime(2024, 1, 3)
        result = self.service.get_sales_trend(start_time, end_time, trend_type="daily")
        
        # Verify repo call was made correctly
        mock_context.sales.get_sales_summary_by_period.assert_called_once_with(start_time, end_time, "day")
        
        # Should fill in missing date (2024-01-02) with zeros
        assert result[0]["date"] == "2024-01-01"
        assert result[1]["date"] == "2024-01-02"
        assert result[1]["total_sales"] == 0.0
        assert result[2]["date"] == "2024-01-03"
        assert result[2]["total_sales"] == 200.0

    @patch('core.services.reporting_service.unit_of_work')
    def test_get_comparative_report(self, mock_uow):
        # Set up Unit of Work mock
        mock_context = MagicMock()
        mock_uow.return_value.__enter__.return_value = mock_context
        
        # Mock all repository calls used in get_comparative_report
        mock_context.sales.calculate_profit_for_period.side_effect = [
            {"total_revenue": 1000.0, "total_cost": 600.0, "total_profit": 400.0, "profit_margin": 0.4},
            {"total_revenue": 800.0, "total_cost": 550.0, "total_profit": 250.0, "profit_margin": 0.31}
        ]
        mock_context.sales.get_top_selling_products.side_effect = [
            [{"product_id": 1, "product_code": "P001", "product_description": "Prod1", "quantity_sold": 5, "total_amount": 100.0}],
            [{"product_id": 2, "product_code": "P002", "product_description": "Prod2", "quantity_sold": 3, "total_amount": 60.0}]
        ]
        mock_context.sales.get_sales_by_payment_type.side_effect = [
            [{"payment_type": "Efectivo", "total_amount": 600.0, "num_sales": 4}],
            [{"payment_type": "Tarjeta", "total_amount": 200.0, "num_sales": 2}]
        ]
        
        current_start = datetime(2024, 1, 1)
        current_end = datetime(2024, 1, 31)
        prev_start = datetime(2023, 12, 1)
        prev_end = datetime(2023, 12, 31)
        
        result = self.service.get_comparative_report(current_start, current_end, prev_start, prev_end)
        
        # Verify repo calls were made correctly
        assert mock_context.sales.calculate_profit_for_period.call_count == 2
        assert mock_context.sales.get_top_selling_products.call_count == 2
        assert mock_context.sales.get_sales_by_payment_type.call_count == 2
        
        # Assert result contains expected values
        assert result["current_period_revenue"] == 1000.0
        assert result["previous_period_revenue"] == 800.0
        assert result["current_period_profit"] == 400.0
        assert result["previous_period_profit"] == 250.0
        assert "revenue_percent_change" in result  # Check key exists
        assert "profit_percent_change" in result  # Check key exists
        assert isinstance(result["current_period_products"], list)
        assert isinstance(result["previous_period_products"], list)
        assert isinstance(result["current_payment_types"], list)
        assert isinstance(result["previous_payment_types"], list)

# Add PDF generation tests
@pytest.mark.parametrize('method_name,report_type', [
    ('print_sales_by_period_report', 'ventas_por_periodo'),
    ('print_sales_by_department_report', 'ventas_por_departamento'),
    ('print_sales_by_customer_report', 'ventas_por_cliente'),
    ('print_top_products_report', 'top_productos'),
    ('print_profit_analysis_report', 'analisis_ganancias')
])
@patch('core.services.reporting_service.unit_of_work')
def test_print_report_methods(mock_uow, method_name, report_type, tmpdir):
    """Test that all print report methods generate PDF files correctly."""
    # Set up Unit of Work mock
    mock_context = MagicMock()
    mock_uow.return_value.__enter__.return_value = mock_context
    
    # Set up mock returns for different method calls
    if 'period' in method_name:
        mock_context.sales.get_sales_summary_by_period.return_value = [
            {'date': '2023-01-01', 'total_sales': Decimal('100.00'), 'num_sales': 5},
            {'date': '2023-01-02', 'total_sales': Decimal('200.00'), 'num_sales': 10}
        ]
    elif 'department' in method_name:
        mock_context.sales.get_sales_by_department.return_value = [
            {'department_id': 1, 'department_name': 'Electronics', 'total_amount': Decimal('500.00'), 'num_items': 20},
            {'department_id': 2, 'department_name': 'Furniture', 'total_amount': Decimal('300.00'), 'num_items': 5}
        ]
    elif 'customer' in method_name:
        mock_context.sales.get_sales_by_customer.return_value = [
            {'customer_id': 1, 'customer_name': 'John Doe', 'total_amount': Decimal('800.00'), 'num_sales': 4},
            {'customer_id': 2, 'customer_name': 'Jane Smith', 'total_amount': Decimal('200.00'), 'num_sales': 1}
        ]
    elif 'product' in method_name:
        mock_context.sales.get_top_selling_products.return_value = [
            {'product_id': 101, 'product_code': 'P001', 'product_description': 'Smartphone', 
             'quantity_sold': 10, 'total_amount': Decimal('5000.00')},
            {'product_id': 102, 'product_code': 'P002', 'product_description': 'Tablet', 
             'quantity_sold': 5, 'total_amount': Decimal('2500.00')}
        ]
    elif 'profit' in method_name:
        mock_context.sales.calculate_profit_for_period.return_value = {
            'total_revenue': Decimal('1000.00'),
            'total_cost': Decimal('600.00'),
            'total_profit': Decimal('400.00'),
            'profit_margin': Decimal('0.40')
        }
        mock_context.sales.get_sales_by_department.return_value = [
            {'department_id': 1, 'department_name': 'Electronics', 'total_amount': Decimal('500.00'), 'num_items': 20},
            {'department_id': 2, 'department_name': 'Furniture', 'total_amount': Decimal('300.00'), 'num_items': 5}
        ]
    
    # Create the service with Unit of Work pattern
    service = ReportingService()
    
    # Create a temporary file path for the PDF
    pdf_path = os.path.join(str(tmpdir), f"{report_type}_test.pdf")
    
    # Set test dates
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 1, 31)
    
    # Create patch for ReportBuilder to avoid actually generating PDFs in the test
    with patch('infrastructure.reporting.report_builder.ReportBuilder') as mock_builder_class:
        # Setup the mock to return a successful result
        mock_builder = MagicMock()
        mock_builder.generate_report_pdf.return_value = True
        mock_builder_class.return_value = mock_builder
        
        # Call the appropriate method
        method = getattr(service, method_name)
        
        # Call with appropriate parameters
        if method_name == 'print_sales_by_period_report':
            result = method(start_date, end_date, 'day', pdf_path)
        elif method_name in ['print_sales_by_customer_report', 'print_top_products_report']:
            result = method(start_date, end_date, 20, pdf_path)
        else:
            result = method(start_date, end_date, pdf_path)
        
        # Check that the result is the PDF path
        assert result == pdf_path
        
        # Verify ReportBuilder was called with correct parameters
        mock_builder.generate_report_pdf.assert_called_once()
        
        # Check that the title and filename were passed correctly
        call_args = mock_builder.generate_report_pdf.call_args[1]
        assert 'report_title' in call_args
        assert 'filename' in call_args
        assert call_args['filename'] == pdf_path
        
        # Check that the report data was populated based on the report type
        assert 'report_data' in call_args
        report_data = call_args['report_data']
        assert 'start_date' in report_data
        assert 'end_date' in report_data
        
        # Check specific data for each report type
        if 'period' in method_name:
            assert 'sales_by_period' in report_data
        elif 'department' in method_name:
            assert 'sales_by_department' in report_data
        elif 'customer' in method_name:
            assert 'sales_by_customer' in report_data
        elif 'product' in method_name:
            assert 'top_products' in report_data
        elif 'profit' in method_name:
            assert 'total_profit' in report_data
            assert 'profit_margin' in report_data


@patch('core.services.reporting_service.unit_of_work')
def test_print_report_failure(mock_uow, tmpdir):
    """Test that a RuntimeError is raised when PDF generation fails."""
    # Set up Unit of Work mock
    mock_context = MagicMock()
    mock_uow.return_value.__enter__.return_value = mock_context
    mock_context.sales.get_sales_summary_by_period.return_value = []
    
    # Create the service with Unit of Work pattern
    service = ReportingService()
    
    # Create a temporary file path for the PDF
    pdf_path = os.path.join(str(tmpdir), "failed_report.pdf")
    
    # Set test dates
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 1, 31)
    
    # Create patch for ReportBuilder to simulate a failure
    with patch('infrastructure.reporting.report_builder.ReportBuilder') as mock_builder_class:
        # Setup the mock to return a failed result
        mock_builder = MagicMock()
        mock_builder.generate_report_pdf.return_value = False
        mock_builder_class.return_value = mock_builder
        
        # Call the method and check that it raises a RuntimeError
        with pytest.raises(RuntimeError) as excinfo:
            service.print_sales_by_period_report(start_date, end_date, 'day', pdf_path)
        
        # Check error message
        assert "Error generating" in str(excinfo.value)
        
        # Verify ReportBuilder was called
        mock_builder.generate_report_pdf.assert_called_once()
