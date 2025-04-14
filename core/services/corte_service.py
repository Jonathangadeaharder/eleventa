from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any

from core.interfaces.repository_interfaces import ISaleRepository, ICashDrawerRepository
from core.models.cash_drawer import CashDrawerEntryType, CashDrawerEntry


class CorteService:
    """
    Service for generating end-of-day/shift (Corte) reports.
    Calculates financial summaries based on sales and cash drawer entries.
    """

    def __init__(self, sale_repository: ISaleRepository, cash_drawer_repository: ICashDrawerRepository):
        """
        Initialize the CorteService with required repositories.
        
        Args:
            sale_repository: Repository for accessing sales data
            cash_drawer_repository: Repository for accessing cash drawer entries
        """
        self.sale_repository = sale_repository
        self.cash_drawer_repository = cash_drawer_repository

    def calculate_corte_data(self, start_time: datetime, end_time: datetime, drawer_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Calculates the data needed for a Corte report within the specified time period.
        
        Args:
            start_time: The start time for the report period
            end_time: The end time for the report period
            drawer_id: Optional drawer ID to filter by specific cash drawer
            
        Returns:
            Dictionary containing all the calculated data for the Corte report
        """
        if end_time < start_time:
            raise ValueError("End time must not be before start time")
        # Get the starting balance (from last START entry before start_time)
        starting_balance = self._calculate_starting_balance(start_time, drawer_id)
        
        # Get all sales within the period
        sales = self.sale_repository.get_sales_by_period(start_time, end_time)
        
        # Calculate sales totals by payment type
        sales_by_payment_type = self._calculate_sales_by_payment_type(sales)
        
        # Get cash drawer entries within the period
        cash_entries = self.cash_drawer_repository.get_entries_by_date_range(start_time, end_time)
        
        # Split entries by type
        cash_in_entries = [entry for entry in cash_entries if entry.entry_type == CashDrawerEntryType.IN]
        cash_out_entries = [entry for entry in cash_entries if entry.entry_type == CashDrawerEntryType.OUT]
        
        # Calculate cash in/out totals
        cash_in_total = sum(entry.amount for entry in cash_in_entries)
        cash_out_total = sum(entry.amount for entry in cash_out_entries)
        
        # Calculate expected cash in drawer
        cash_sales = sales_by_payment_type.get("Efectivo", Decimal("0.00"))
        expected_cash = starting_balance + cash_sales + cash_in_total - cash_out_total
        
        # Total sales across all payment types
        total_sales = sum(sales_by_payment_type.values())
        
        # Build and return the full report data
        return {
            "period_start": start_time,
            "period_end": end_time,
            "starting_balance": starting_balance,
            "sales_by_payment_type": sales_by_payment_type,
            "total_sales": total_sales,
            "cash_in_entries": cash_in_entries,
            "cash_out_entries": cash_out_entries,
            "cash_in_total": cash_in_total,
            "cash_out_total": cash_out_total,
            "expected_cash_in_drawer": expected_cash,
            "sale_count": len(sales)
        }

    def _calculate_starting_balance(self, start_time: datetime, drawer_id: Optional[int] = None) -> Decimal:
        """
        Calculate the starting balance for the period by finding the most recent START entry
        before the period start time.
        
        Args:
            start_time: The start time of the period
            drawer_id: Optional drawer ID to filter by specific cash drawer
            
        Returns:
            The starting balance as a Decimal
        """
        last_start_entry = self.cash_drawer_repository.get_last_start_entry(drawer_id)
        
        if last_start_entry and last_start_entry.timestamp < start_time:
            return last_start_entry.amount
        
        # If no previous opening entry found, default to zero
        return Decimal("0.00")

    def _calculate_sales_by_payment_type(self, sales: List[Any]) -> Dict[str, Decimal]:
        """
        Group and sum sales by payment type.
        
        Args:
            sales: List of Sale objects
            
        Returns:
            Dictionary with payment types as keys and total amounts as values
        """
        result = {}
        
        for sale in sales:
            payment_type = sale.payment_type or "Sin especificar"
            if payment_type not in result:
                result[payment_type] = Decimal("0.00")
            result[payment_type] += sale.total
            
        return result

    def register_closing_balance(self, drawer_id: Optional[int], actual_amount: Decimal, 
                                description: str, user_id: int) -> CashDrawerEntry:
        """
        Register a closing balance entry in the cash drawer.
        
        Args:
            drawer_id: Optional drawer ID
            actual_amount: The actual counted cash amount
            description: Description of the closing entry
            user_id: ID of the user making the entry
            
        Returns:
            The created CashDrawerEntry
        """
        closing_entry = CashDrawerEntry(
            timestamp=datetime.now(),
            entry_type=CashDrawerEntryType.CLOSE,
            amount=actual_amount,
            description=description,
            user_id=user_id,
            drawer_id=drawer_id
        )
        
        return self.cash_drawer_repository.add_entry(closing_entry)