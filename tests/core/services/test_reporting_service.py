import pytest
from unittest.mock import MagicMock, PropertyMock
from core.services.reporting_service import ReportingService
from datetime import datetime, timedelta  # Import datetime

class TestReportingService:
    @pytest.fixture(autouse=True)
    def setup_service(self):
        # Patch the repository factory to return a mock repo
        self.mock_repo = MagicMock()
        # Simulate context manager if factory returns one
        self.mock_context_manager = MagicMock()
        self.mock_context_manager.__enter__.return_value = self.mock_repo
        self.mock_context_manager.__exit__.return_value = None
        self.service = ReportingService(lambda: self.mock_context_manager)  # Adapt factory for context manager

        # Define sample date range for tests
        self.start_time = datetime(2024, 1, 1)
        self.end_time = datetime(2024, 1, 31, 23, 59, 59)

    def test_get_sales_summary_by_period(self):
        # Define expected return value from repo
        expected_repo_return = [
            {"date": "2024-01-01", "total_sales": 100.0, "num_sales": 2}
        ]
        self.mock_repo.get_sales_summary_by_period.return_value = expected_repo_return

        # Call service method with required args
        result = self.service.get_sales_summary_by_period(
            self.start_time, self.end_time, group_by="day"
        )

        # Assert repo was called correctly
        self.mock_repo.get_sales_summary_by_period.assert_called_once_with(
            self.start_time, self.end_time, "day"
        )
        # Assert result matches expected repo return
        assert result == expected_repo_return

    def test_get_sales_by_payment_type(self):
        expected_repo_return = [
            {"payment_type": "Efectivo", "total_amount": 200.0, "num_sales": 5}  # Use correct keys from repo interface
        ]
        self.mock_repo.get_sales_by_payment_type.return_value = expected_repo_return
        result = self.service.get_sales_by_payment_type(self.start_time, self.end_time)  # Add args
        self.mock_repo.get_sales_by_payment_type.assert_called_once_with(self.start_time, self.end_time)
        assert result == expected_repo_return  # Assert against expected structure

    def test_get_sales_by_department(self):
        expected_repo_return = [
            {"department_id": 1, "department_name": "Dept1", "total_amount": 300.0, "num_items": 10}  # Use correct keys
        ]
        self.mock_repo.get_sales_by_department.return_value = expected_repo_return
        result = self.service.get_sales_by_department(self.start_time, self.end_time)  # Add args
        self.mock_repo.get_sales_by_department.assert_called_once_with(self.start_time, self.end_time)
        assert result == expected_repo_return

    def test_get_sales_by_customer(self):
        expected_repo_return = [
            {"customer_id": 1, "customer_name": "Cust1", "total_amount": 400.0, "num_sales": 3}  # Use correct keys
        ]
        self.mock_repo.get_sales_by_customer.return_value = expected_repo_return
        result = self.service.get_sales_by_customer(self.start_time, self.end_time, limit=5)  # Add args
        self.mock_repo.get_sales_by_customer.assert_called_once_with(self.start_time, self.end_time, 5)
        assert result == expected_repo_return

    def test_get_top_selling_products(self):
        expected_repo_return = [
            {"product_id": 1, "product_code": "P001", "product_description": "Prod1", "quantity_sold": 10, "total_amount": 150.0}  # Use correct keys
        ]
        self.mock_repo.get_top_selling_products.return_value = expected_repo_return
        result = self.service.get_top_selling_products(self.start_time, self.end_time, limit=3)  # Add args
        self.mock_repo.get_top_selling_products.assert_called_once_with(self.start_time, self.end_time, 3)
        assert result == expected_repo_return

    def test_calculate_profit_for_period(self):
        expected_repo_return = {
            "total_revenue": 500.0, "total_cost": 300.0, "total_profit": 200.0, "profit_margin": 0.4
        }
        self.mock_repo.calculate_profit_for_period.return_value = expected_repo_return
        result = self.service.calculate_profit_for_period(self.start_time, self.end_time)  # Add datetime objects
        self.mock_repo.calculate_profit_for_period.assert_called_once_with(self.start_time, self.end_time)
        assert result == expected_repo_return  # Assert against expected structure

    def test_get_daily_sales_report(self):
        # Mock all repository calls used in get_daily_sales_report
        self.mock_repo.calculate_profit_for_period.return_value = {
            "total_revenue": 1000.0,
            "total_cost": 600.0,
            "total_profit": 400.0,
            "profit_margin": 0.4
        }
        self.mock_repo.get_sales_by_payment_type.return_value = [
            {"payment_type": "Efectivo", "num_sales": 2, "total_amount": 500.0}  # Add total_amount
        ]
        self.mock_repo.get_top_selling_products.return_value = [
            {"product_id": 1, "product_code": "P001", "product_description": "Prod1", "quantity_sold": 5, "total_amount": 100.0}
        ]
        self.mock_repo.get_sales_by_department.return_value = [
            {"department_id": 1, "department_name": "Dept1", "total_amount": 300.0, "num_items": 10}
        ]

        date = datetime(2024, 1, 1)
        result = self.service.get_daily_sales_report(date)

        # Verify calls were made with correct date ranges
        start_time = datetime.combine(date, datetime.min.time())
        end_time = datetime.combine(date, datetime.max.time())
        self.mock_repo.calculate_profit_for_period.assert_called_once_with(start_time, end_time)
        self.mock_repo.get_sales_by_payment_type.assert_called_once_with(start_time, end_time)
        self.mock_repo.get_top_selling_products.assert_called_once_with(start_time, end_time, 5)
        self.mock_repo.get_sales_by_department.assert_called_once_with(start_time, end_time)

        assert result["date"] == "2024-01-01"
        assert result["total_revenue"] == 1000.0
        assert result["total_cost"] == 600.0
        assert result["total_profit"] == 400.0
        assert result["profit_margin"] == 0.4
        assert result["sales_count"] == 2
        assert isinstance(result["payment_types"], list)
        assert isinstance(result["top_products"], list)
        assert isinstance(result["sales_by_department"], list)

    def test_get_sales_trend(self):
        # Mock get_sales_summary_by_period for daily trend
        self.mock_repo.get_sales_summary_by_period.return_value = [
            {"date": "2024-01-01", "total_sales": 100.0, "num_sales": 2},
            {"date": "2024-01-03", "total_sales": 200.0, "num_sales": 3}
        ]
        
        start_time = datetime(2024, 1, 1)
        end_time = datetime(2024, 1, 3)
        result = self.service.get_sales_trend(start_time, end_time, trend_type="daily")
        
        # Verify repo call was made correctly
        self.mock_repo.get_sales_summary_by_period.assert_called_once_with(start_time, end_time, "day")
        
        # Should fill in missing date (2024-01-02) with zeros
        assert result[0]["date"] == "2024-01-01"
        assert result[1]["date"] == "2024-01-02"
        assert result[1]["total_sales"] == 0.0
        assert result[2]["date"] == "2024-01-03"
        assert result[2]["total_sales"] == 200.0

    def test_get_comparative_report(self):
        # Mock all repository calls used in get_comparative_report
        self.mock_repo.calculate_profit_for_period.side_effect = [
            {"total_revenue": 1000.0, "total_cost": 600.0, "total_profit": 400.0, "profit_margin": 0.4},
            {"total_revenue": 800.0, "total_cost": 550.0, "total_profit": 250.0, "profit_margin": 0.31}
        ]
        self.mock_repo.get_top_selling_products.side_effect = [
            [{"product_id": 1, "product_code": "P001", "product_description": "Prod1", "quantity_sold": 5, "total_amount": 100.0}],
            [{"product_id": 2, "product_code": "P002", "product_description": "Prod2", "quantity_sold": 3, "total_amount": 60.0}]
        ]
        self.mock_repo.get_sales_by_payment_type.side_effect = [
            [{"payment_type": "Efectivo", "total_amount": 600.0, "num_sales": 4}],
            [{"payment_type": "Tarjeta", "total_amount": 200.0, "num_sales": 2}]
        ]
        
        current_start = datetime(2024, 1, 1)
        current_end = datetime(2024, 1, 31)
        prev_start = datetime(2023, 12, 1)
        prev_end = datetime(2023, 12, 31)
        
        result = self.service.get_comparative_report(current_start, current_end, prev_start, prev_end)
        
        # Verify repo calls were made correctly
        assert self.mock_repo.calculate_profit_for_period.call_count == 2
        assert self.mock_repo.get_top_selling_products.call_count == 2
        assert self.mock_repo.get_sales_by_payment_type.call_count == 2
        
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
