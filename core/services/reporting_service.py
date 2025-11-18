from typing import List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import os

from core.services.service_base import ServiceBase
from infrastructure.persistence.unit_of_work import unit_of_work


class ReportingService(ServiceBase):
    """
    Service for generating advanced reports and analytics on sales and business performance.
    Provides methods to retrieve aggregated data by time periods, departments, customers, etc.
    """

    def __init__(self):
        """
        Initialize the service.
        """
        super().__init__()  # Initialize base class with default logger

    def get_sales_summary_by_period(
        self, start_time: datetime, end_time: datetime, group_by: str = "day"
    ) -> List[Dict[str, Any]]:
        """
        Gets sales data summarized by time period (day/week/month).

        Args:
            start_time: Start of the reporting period
            end_time: End of the reporting period
            group_by: Grouping time period ('day', 'week', 'month')

        Returns:
            List of dictionaries with date and aggregated sales data
        """
        with unit_of_work() as uow:
            return uow.sales.get_sales_summary_by_period(start_time, end_time, group_by)

    def get_sales_by_payment_type(
        self, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Gets sales data aggregated by payment type.

        Args:
            start_time: Start of the reporting period
            end_time: End of the reporting period

        Returns:
            List of dictionaries with payment type, total amount, and number of sales
        """
        with unit_of_work() as uow:
            return uow.sales.get_sales_by_payment_type(start_time, end_time)

    def get_sales_by_department(
        self, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Gets sales data aggregated by product department.

        Args:
            start_time: Start of the reporting period
            end_time: End of the reporting period

        Returns:
            List of dictionaries with department_id, department_name, total_amount, and num_items
        """
        with unit_of_work() as uow:
            return uow.sales.get_sales_by_department(start_time, end_time)

    def get_sales_by_customer(
        self, start_time: datetime, end_time: datetime, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Gets top customers by sales amount for a period.

        Args:
            start_time: Start of the reporting period
            end_time: End of the reporting period
            limit: Maximum number of customers to return

        Returns:
            List of dictionaries with customer_id, customer_name, total_amount, and num_sales
        """
        with unit_of_work() as uow:
            return uow.sales.get_sales_by_customer(start_time, end_time, limit)

    def get_top_selling_products(
        self, start_time: datetime, end_time: datetime, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Gets the top selling products for a period.

        Args:
            start_time: Start of the reporting period
            end_time: End of the reporting period
            limit: Maximum number of products to return

        Returns:
            List of dictionaries with product_id, product_code, product_description,
            quantity_sold, and total_amount
        """
        with unit_of_work() as uow:
            return uow.sales.get_top_selling_products(start_time, end_time, limit)

    def calculate_profit_for_period(
        self, start_time: datetime, end_time: datetime
    ) -> Dict[str, Any]:
        """
        Calculates profit metrics (revenue, cost, profit, margin) for a period.

        Args:
            start_time: Start of the reporting period
            end_time: End of the reporting period

        Returns:
            Dictionary with total_revenue, total_cost, total_profit, and profit_margin
        """
        with unit_of_work() as uow:
            return uow.sales.calculate_profit_for_period(start_time, end_time)

    def get_daily_sales_report(self, date: datetime) -> Dict[str, Any]:
        """
        Gets a comprehensive daily sales report for the specified date.

        Args:
            date: The specific date to report on

        Returns:
            Dictionary with various sales metrics for the day
        """
        with unit_of_work() as uow:
            # Set time to start and end of the specified date
            start_time = datetime.combine(date, datetime.min.time())
            end_time = datetime.combine(date, datetime.max.time())

            # Gather data for the report
            profit_data = uow.sales.calculate_profit_for_period(start_time, end_time)
            payment_data = uow.sales.get_sales_by_payment_type(start_time, end_time)
            top_products = uow.sales.get_top_selling_products(start_time, end_time, 5)
            department_data = uow.sales.get_sales_by_department(start_time, end_time)

            # Count total sales
            sales_count = (
                sum(p["num_sales"] for p in payment_data) if payment_data else 0
            )

            return {
                "date": date.strftime("%Y-%m-%d"),
                "total_revenue": profit_data.get("total_revenue", 0.0),
                "total_cost": profit_data.get("total_cost", 0.0),
                "total_profit": profit_data.get("total_profit", 0.0),
                "profit_margin": profit_data.get("profit_margin", 0.0),
                "sales_count": sales_count,
                "payment_types": payment_data,
                "top_products": top_products,
                "sales_by_department": department_data,
            }

    def get_sales_trend(
        self, start_time: datetime, end_time: datetime, trend_type: str = "daily"
    ) -> List[Dict[str, Any]]:
        """
        Gets sales trend data over time for chart visualization.

        Args:
            start_time: Start of the reporting period
            end_time: End of the reporting period
            trend_type: Type of trend ('daily', 'weekly', 'monthly')

        Returns:
            List of dictionaries with date and sales data points
        """
        with unit_of_work() as uow:
            # Map trend_type to appropriate group_by parameter
            group_by_mapping = {"daily": "day", "weekly": "week", "monthly": "month"}
            group_by = group_by_mapping.get(trend_type, "day")

            trend_data = uow.sales.get_sales_summary_by_period(
                start_time, end_time, group_by
            )

            # Ensure complete date range (fill in missing dates with zero values)
            if trend_type == "daily" and trend_data:
                complete_data = []
                current_date = start_time.date()
                end_date = end_time.date()

                # Create a date index for O(1) lookup
                date_index = {item["date"]: item for item in trend_data}

                while current_date <= end_date:
                    date_str = current_date.strftime("%Y-%m-%d")
                    if date_str in date_index:
                        complete_data.append(date_index[date_str])
                    else:
                        complete_data.append(
                            {"date": date_str, "total_sales": 0.0, "num_sales": 0}
                        )
                    current_date += timedelta(days=1)

                return complete_data

            return trend_data

    def get_comparative_report(
        self,
        current_period_start: datetime,
        current_period_end: datetime,
        previous_period_start: datetime,
        previous_period_end: datetime,
    ) -> Dict[str, Any]:
        """
        Gets comparative data between two periods (e.g., this month vs last month).

        Args:
            current_period_start: Start of the current period
            current_period_end: End of the current period
            previous_period_start: Start of the previous period
            previous_period_end: End of the previous period

        Returns:
            Dictionary with comparative metrics and percentage changes
        """
        with unit_of_work() as uow:
            current_profit = uow.sales.calculate_profit_for_period(
                current_period_start, current_period_end
            )
            previous_profit = uow.sales.calculate_profit_for_period(
                previous_period_start, previous_period_end
            )

            # Calculate percent changes
            current_revenue = current_profit.get("total_revenue", 0.0)
            previous_revenue = previous_profit.get("total_revenue", 0.0)
            revenue_change = self._calculate_percent_change(
                previous_revenue, current_revenue
            )

            current_profit_val = current_profit.get("total_profit", 0.0)
            previous_profit_val = previous_profit.get("total_profit", 0.0)
            profit_change = self._calculate_percent_change(
                previous_profit_val, current_profit_val
            )

            # Get top products from both periods for comparison
            current_top_products = uow.sales.get_top_selling_products(
                current_period_start, current_period_end, 10
            )
            previous_top_products = uow.sales.get_top_selling_products(
                previous_period_start, previous_period_end, 10
            )

            # Get current and previous sales by payment type
            current_payment_types = uow.sales.get_sales_by_payment_type(
                current_period_start, current_period_end
            )
            previous_payment_types = uow.sales.get_sales_by_payment_type(
                previous_period_start, previous_period_end
            )

            return {
                "current_period_revenue": current_revenue,
                "previous_period_revenue": previous_revenue,
                "revenue_percent_change": revenue_change,
                "current_period_profit": current_profit_val,
                "previous_period_profit": previous_profit_val,
                "profit_percent_change": profit_change,
                "current_period_products": current_top_products,
                "previous_period_products": previous_top_products,
                "current_payment_types": current_payment_types,
                "previous_payment_types": previous_payment_types,
            }

    def _calculate_percent_change(self, old_value: float, new_value: float) -> float:
        """
        Calculate percentage change between two values.

        Args:
            old_value: The original value
            new_value: The new value

        Returns:
            Percentage change as a float (e.g., 0.25 for 25% increase)
        """
        if old_value == 0:
            return float("inf") if new_value > 0 else 0.0

        return (new_value - old_value) / abs(old_value)

    def print_sales_by_period_report(
        self,
        start_time: datetime,
        end_time: datetime,
        group_by: str = "day",
        filename: str = None,
    ) -> str:
        """
        Generate and print a PDF report for sales by period.

        Args:
            start_time: Start of the reporting period
            end_time: End of the reporting period
            group_by: Grouping time period ('day', 'week', 'month')
            filename: Optional custom filename for the PDF

        Returns:
            Path to the generated PDF file
        """
        from infrastructure.reporting.report_builder import ReportBuilder

        # Ensure the pdfs directory exists
        os.makedirs("pdfs", exist_ok=True)

        # Format dates for display and filename
        start_str = start_time.strftime("%Y-%m-%d")
        end_str = end_time.strftime("%Y-%m-%d")

        # Generate filename if not provided
        if not filename:
            filename = f"pdfs/ventas_por_periodo_{start_str}_a_{end_str}.pdf"

        # Get sales data
        sales_data = self.get_sales_summary_by_period(start_time, end_time, group_by)

        # Get totals
        total_revenue = sum(item.get("total_sales", 0) for item in sales_data)
        sales_count = sum(item.get("num_sales", 0) for item in sales_data)

        # Prepare report data
        report_data = {
            "start_date": start_str,
            "end_date": end_str,
            "total_revenue": total_revenue,
            "sales_count": sales_count,
            "sales_by_period": sales_data,
        }

        # Create and generate the report
        report_builder = ReportBuilder()
        success = report_builder.generate_report_pdf(
            report_title=f"Reporte de Ventas por Período - {start_str} a {end_str}",
            report_data=report_data,
            filename=filename,
        )

        if success:
            return os.path.abspath(filename)
        else:
            raise RuntimeError("Error generating sales by period report PDF")

    def print_sales_by_department_report(
        self, start_time: datetime, end_time: datetime, filename: str = None
    ) -> str:
        """
        Generate and print a PDF report for sales by department.

        Args:
            start_time: Start of the reporting period
            end_time: End of the reporting period
            filename: Optional custom filename for the PDF

        Returns:
            Path to the generated PDF file
        """
        from infrastructure.reporting.report_builder import ReportBuilder

        # Ensure the pdfs directory exists
        os.makedirs("pdfs", exist_ok=True)

        # Format dates for display and filename
        start_str = start_time.strftime("%Y-%m-%d")
        end_str = end_time.strftime("%Y-%m-%d")

        # Generate filename if not provided
        if not filename:
            filename = f"pdfs/ventas_por_departamento_{start_str}_a_{end_str}.pdf"

        # Get sales data
        dept_data = self.get_sales_by_department(start_time, end_time)

        # Calculate total for percentages
        total_revenue = sum(dept.get("total_amount", 0) for dept in dept_data)

        # Add percentage to each department
        for dept in dept_data:
            if total_revenue > 0:
                dept["percentage"] = (dept.get("total_amount", 0) / total_revenue) * 100
            else:
                dept["percentage"] = 0

        # Prepare report data
        report_data = {
            "start_date": start_str,
            "end_date": end_str,
            "total_revenue": total_revenue,
            "sales_by_department": dept_data,
        }

        # Create and generate the report
        report_builder = ReportBuilder()
        success = report_builder.generate_report_pdf(
            report_title=f"Reporte de Ventas por Departamento - {start_str} a {end_str}",
            report_data=report_data,
            filename=filename,
            is_landscape=True,
        )

        if success:
            return os.path.abspath(filename)
        else:
            raise RuntimeError("Error generating sales by department report PDF")

    def print_sales_by_customer_report(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 20,
        filename: str = None,
    ) -> str:
        """
        Generate and print a PDF report for sales by customer.

        Args:
            start_time: Start of the reporting period
            end_time: End of the reporting period
            limit: Maximum number of customers to include
            filename: Optional custom filename for the PDF

        Returns:
            Path to the generated PDF file
        """
        from infrastructure.reporting.report_builder import ReportBuilder

        # Ensure the pdfs directory exists
        os.makedirs("pdfs", exist_ok=True)

        # Format dates for display and filename
        start_str = start_time.strftime("%Y-%m-%d")
        end_str = end_time.strftime("%Y-%m-%d")

        # Generate filename if not provided
        if not filename:
            filename = f"pdfs/ventas_por_cliente_{start_str}_a_{end_str}.pdf"

        # Get sales data
        customer_data = self.get_sales_by_customer(start_time, end_time, limit)

        # Calculate total for percentages
        total_revenue = sum(cust.get("total_amount", 0) for cust in customer_data)

        # Add percentage to each customer
        for cust in customer_data:
            if total_revenue > 0:
                cust["percentage"] = (cust.get("total_amount", 0) / total_revenue) * 100
            else:
                cust["percentage"] = 0

        # Prepare report data
        report_data = {
            "start_date": start_str,
            "end_date": end_str,
            "total_revenue": total_revenue,
            "sales_by_customer": customer_data,
        }

        # Create and generate the report
        report_builder = ReportBuilder()
        success = report_builder.generate_report_pdf(
            report_title=f"Reporte de Ventas por Cliente - {start_str} a {end_str}",
            report_data=report_data,
            filename=filename,
        )

        if success:
            return os.path.abspath(filename)
        else:
            raise RuntimeError("Error generating sales by customer report PDF")

    def print_top_products_report(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 20,
        filename: str = None,
    ) -> str:
        """
        Generate and print a PDF report for top selling products.

        Args:
            start_time: Start of the reporting period
            end_time: End of the reporting period
            limit: Maximum number of products to include
            filename: Optional custom filename for the PDF

        Returns:
            Path to the generated PDF file
        """
        from infrastructure.reporting.report_builder import ReportBuilder

        # Ensure the pdfs directory exists
        os.makedirs("pdfs", exist_ok=True)

        # Format dates for display and filename
        start_str = start_time.strftime("%Y-%m-%d")
        end_str = end_time.strftime("%Y-%m-%d")

        # Generate filename if not provided
        if not filename:
            filename = f"pdfs/top_productos_{start_str}_a_{end_str}.pdf"

        # Get sales data
        products_data = self.get_top_selling_products(start_time, end_time, limit)

        # Calculate total for percentages
        total_revenue = sum(prod.get("total_amount", 0) for prod in products_data)

        # Add percentage to each product
        for prod in products_data:
            if total_revenue > 0:
                prod["percentage"] = (prod.get("total_amount", 0) / total_revenue) * 100
            else:
                prod["percentage"] = 0

        # Prepare report data
        report_data = {
            "start_date": start_str,
            "end_date": end_str,
            "total_revenue": total_revenue,
            "top_products": products_data,
        }

        # Create and generate the report
        report_builder = ReportBuilder()
        success = report_builder.generate_report_pdf(
            report_title=f"Reporte de Productos Más Vendidos - {start_str} a {end_str}",
            report_data=report_data,
            filename=filename,
            is_landscape=True,
        )

        if success:
            return os.path.abspath(filename)
        else:
            raise RuntimeError("Error generating top products report PDF")

    def print_profit_analysis_report(
        self, start_time: datetime, end_time: datetime, filename: str = None
    ) -> str:
        """
        Generate and print a PDF report for profit analysis.

        Args:
            start_time: Start of the reporting period
            end_time: End of the reporting period
            filename: Optional custom filename for the PDF

        Returns:
            Path to the generated PDF file
        """
        from infrastructure.reporting.report_builder import ReportBuilder

        # Ensure the pdfs directory exists
        os.makedirs("pdfs", exist_ok=True)

        # Format dates for display and filename
        start_str = start_time.strftime("%Y-%m-%d")
        end_str = end_time.strftime("%Y-%m-%d")

        # Generate filename if not provided
        if not filename:
            filename = f"pdfs/analisis_ganancias_{start_str}_a_{end_str}.pdf"

        # Get profit data
        profit_data = self.calculate_profit_for_period(start_time, end_time)

        # Get sales by department for department profit breakdown
        dept_data = self.get_sales_by_department(start_time, end_time)

        # Prepare report data
        report_data = {
            "start_date": start_str,
            "end_date": end_str,
            "total_revenue": profit_data.get("total_revenue", 0),
            "total_cost": profit_data.get("total_cost", 0),
            "total_profit": profit_data.get("total_profit", 0),
            "profit_margin": profit_data.get("profit_margin", 0)
            * 100,  # Convert to percentage
            "department_profit": [],
        }

        # Add department profit details if available
        if dept_data:
            for dept in dept_data:
                dept_profit = {
                    "department_name": dept.get("department_name", "Sin departamento"),
                    "revenue": dept.get("total_amount", 0),
                    "cost": 0,  # We would need to calculate this from the items
                    "profit": 0,
                    "margin": 0,
                }

                # Get department cost from sale items (simplified example)
                # In a real implementation, you would get actual costs from the database
                dept_profit["cost"] = dept_profit["revenue"] * Decimal(
                    "0.65"
                )  # Assuming 65% cost of goods
                dept_profit["profit"] = dept_profit["revenue"] - dept_profit["cost"]

                if dept_profit["revenue"] > 0:
                    dept_profit["margin"] = (
                        dept_profit["profit"] / dept_profit["revenue"]
                    ) * Decimal("100")

                report_data["department_profit"].append(dept_profit)

        # Create and generate the report
        report_builder = ReportBuilder()
        success = report_builder.generate_report_pdf(
            report_title=f"Análisis de Ganancias - {start_str} a {end_str}",
            report_data=report_data,
            filename=filename,
        )

        if success:
            return os.path.abspath(filename)
        else:
            raise RuntimeError("Error generating profit analysis report PDF")
