from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from core.interfaces.repository_interfaces import ISaleRepository
from ..models.sale import Sale

class ReportingService:
    """
    Service for generating advanced reports and analytics on sales and business performance.
    Provides methods to retrieve aggregated data by time periods, departments, customers, etc.
    """
    
    def __init__(self, sale_repository_factory):
        """
        Initialize with repository factories.
        
        Args:
            sale_repository_factory: Factory function that returns an ISaleRepository instance
        """
        self.sale_repo_factory = sale_repository_factory
    
    def get_sales_summary_by_period(
        self, 
        start_time: datetime, 
        end_time: datetime,
        group_by: str = 'day'
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
        with self.sale_repo_factory() as sale_repo:
            return sale_repo.get_sales_summary_by_period(start_time, end_time, group_by)
    
    def get_sales_by_payment_type(
        self, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Gets sales data aggregated by payment type.
        
        Args:
            start_time: Start of the reporting period
            end_time: End of the reporting period
            
        Returns:
            List of dictionaries with payment type, total amount, and number of sales
        """
        with self.sale_repo_factory() as sale_repo:
            return sale_repo.get_sales_by_payment_type(start_time, end_time)
    
    def get_sales_by_department(
        self, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Gets sales data aggregated by product department.
        
        Args:
            start_time: Start of the reporting period
            end_time: End of the reporting period
            
        Returns:
            List of dictionaries with department_id, department_name, total_amount, and num_items
        """
        with self.sale_repo_factory() as sale_repo:
            return sale_repo.get_sales_by_department(start_time, end_time)
    
    def get_sales_by_customer(
        self, 
        start_time: datetime, 
        end_time: datetime,
        limit: int = 10
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
        with self.sale_repo_factory() as sale_repo:
            return sale_repo.get_sales_by_customer(start_time, end_time, limit)
    
    def get_top_selling_products(
        self, 
        start_time: datetime, 
        end_time: datetime,
        limit: int = 10
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
        with self.sale_repo_factory() as sale_repo:
            return sale_repo.get_top_selling_products(start_time, end_time, limit)
    
    def calculate_profit_for_period(
        self, 
        start_time: datetime, 
        end_time: datetime
    ) -> Dict[str, Any]:
        """
        Calculates profit metrics (revenue, cost, profit, margin) for a period.
        
        Args:
            start_time: Start of the reporting period
            end_time: End of the reporting period
            
        Returns:
            Dictionary with total_revenue, total_cost, total_profit, and profit_margin
        """
        with self.sale_repo_factory() as sale_repo:
            return sale_repo.calculate_profit_for_period(start_time, end_time)
    
    def get_daily_sales_report(self, date: datetime) -> Dict[str, Any]:
        """
        Gets a comprehensive daily sales report for the specified date.
        
        Args:
            date: The specific date to report on
            
        Returns:
            Dictionary with various sales metrics for the day
        """
        # Set time to start and end of the specified date
        start_time = datetime.combine(date, datetime.min.time())
        end_time = datetime.combine(date, datetime.max.time())
        
        # Create comprehensive report using multiple repo calls
        with self.sale_repo_factory() as sale_repo:
            profit_data = sale_repo.calculate_profit_for_period(start_time, end_time)
            payment_data = sale_repo.get_sales_by_payment_type(start_time, end_time)
            top_products = sale_repo.get_top_selling_products(start_time, end_time, 5)
            department_data = sale_repo.get_sales_by_department(start_time, end_time)
            
            # Count total sales
            sales_count = sum(p['num_sales'] for p in payment_data) if payment_data else 0
            
            return {
                'date': date.strftime('%Y-%m-%d'),
                'total_revenue': profit_data.get('total_revenue', 0.0),
                'total_cost': profit_data.get('total_cost', 0.0),
                'total_profit': profit_data.get('total_profit', 0.0),
                'profit_margin': profit_data.get('profit_margin', 0.0),
                'sales_count': sales_count,
                'payment_types': payment_data,
                'top_products': top_products,
                'sales_by_department': department_data
            }
    
    def get_sales_trend(
        self, 
        start_time: datetime, 
        end_time: datetime, 
        trend_type: str = 'daily'
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
        # Map trend_type to appropriate group_by parameter
        group_by_mapping = {
            'daily': 'day',
            'weekly': 'week',
            'monthly': 'month'
        }
        group_by = group_by_mapping.get(trend_type, 'day')
        
        with self.sale_repo_factory() as sale_repo:
            trend_data = sale_repo.get_sales_summary_by_period(start_time, end_time, group_by)
            
            # Ensure complete date range (fill in missing dates with zero values)
            if trend_type == 'daily' and trend_data:
                complete_data = []
                current_date = start_time.date()
                end_date = end_time.date()
                
                # Create a date index for O(1) lookup
                date_index = {item['date']: item for item in trend_data}
                
                while current_date <= end_date:
                    date_str = current_date.strftime('%Y-%m-%d')
                    if date_str in date_index:
                        complete_data.append(date_index[date_str])
                    else:
                        complete_data.append({
                            'date': date_str,
                            'total_sales': 0.0,
                            'num_sales': 0
                        })
                    current_date += timedelta(days=1)
                
                return complete_data
            
            return trend_data
    
    def get_comparative_report(
        self, 
        current_period_start: datetime,
        current_period_end: datetime,
        previous_period_start: datetime,
        previous_period_end: datetime
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
        with self.sale_repo_factory() as sale_repo:
            current_profit = sale_repo.calculate_profit_for_period(
                current_period_start, current_period_end
            )
            previous_profit = sale_repo.calculate_profit_for_period(
                previous_period_start, previous_period_end
            )
            
            # Calculate percent changes
            current_revenue = current_profit.get('total_revenue', 0.0)
            previous_revenue = previous_profit.get('total_revenue', 0.0)
            revenue_change = self._calculate_percent_change(previous_revenue, current_revenue)
            
            current_profit_val = current_profit.get('total_profit', 0.0)
            previous_profit_val = previous_profit.get('total_profit', 0.0)
            profit_change = self._calculate_percent_change(previous_profit_val, current_profit_val)
            
            # Get top products from both periods for comparison
            current_top_products = sale_repo.get_top_selling_products(
                current_period_start, current_period_end, 10
            )
            previous_top_products = sale_repo.get_top_selling_products(
                previous_period_start, previous_period_end, 10
            )
            
            # Get current and previous sales by payment type
            current_payment_types = sale_repo.get_sales_by_payment_type(
                current_period_start, current_period_end
            )
            previous_payment_types = sale_repo.get_sales_by_payment_type(
                previous_period_start, previous_period_end
            )
            
            return {
                'current_period_revenue': current_revenue,
                'previous_period_revenue': previous_revenue,
                'revenue_percent_change': revenue_change,
                
                'current_period_profit': current_profit_val,
                'previous_period_profit': previous_profit_val,
                'profit_percent_change': profit_change,
                
                'current_period_products': current_top_products,
                'previous_period_products': previous_top_products,
                
                'current_payment_types': current_payment_types,
                'previous_payment_types': previous_payment_types
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
            return float('inf') if new_value > 0 else 0.0
        
        return (new_value - old_value) / abs(old_value)