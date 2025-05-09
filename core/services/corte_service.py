from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Any, Callable
from sqlalchemy.orm import Session

from core.interfaces.repository_interfaces import ISaleRepository, ICashDrawerRepository
from core.models.cash_drawer import CashDrawerEntryType, CashDrawerEntry
from core.services.service_base import ServiceBase
from infrastructure.persistence.utils import session_scope


class CorteService(ServiceBase):
    """
    Service for generating end-of-day/shift (Corte) reports.
    Calculates financial summaries based on sales and cash drawer entries.
    """

    def __init__(self, sale_repo_factory: Callable[[Session], ISaleRepository], 
                 cash_drawer_repo_factory: Callable[[Session], ICashDrawerRepository]):
        """
        Initialize the CorteService with required repository factories.
        
        Args:
            sale_repo_factory: Factory function to create sale repository
            cash_drawer_repo_factory: Factory function to create cash drawer repository
        """
        super().__init__()  # Initialize base class with default logger
        self.sale_repo_factory = sale_repo_factory
        self.cash_drawer_repo_factory = cash_drawer_repo_factory

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
        def _calculate_corte_data(session, start_time, end_time, drawer_id):
            if end_time < start_time:
                raise ValueError("End time must not be before start time")
                
            # Get repositories from factories
            sale_repo = self._get_repository(self.sale_repo_factory, session)
            cash_drawer_repo = self._get_repository(self.cash_drawer_repo_factory, session)
                
            # Get the starting balance (from last START entry before start_time)
            starting_balance = self._calculate_starting_balance(session, start_time, drawer_id)
            
            # Get all sales within the period
            sales = sale_repo.get_sales_by_period(start_time, end_time)
            
            # Calculate sales totals by payment type
            sales_by_payment_type = self._calculate_sales_by_payment_type(sales)
            
            # Get cash drawer entries within the period
            cash_entries = cash_drawer_repo.get_entries_by_date_range(start_time, end_time, drawer_id)
            
            # Split entries by type
            cash_in_entries = [entry for entry in cash_entries if entry.entry_type == CashDrawerEntryType.IN]
            cash_out_entries = [entry for entry in cash_entries if entry.entry_type == CashDrawerEntryType.OUT]
            
            # Calculate cash in/out totals
            cash_in_total = sum(entry.amount for entry in cash_in_entries)
            cash_out_total = sum(abs(entry.amount) for entry in cash_out_entries)
            
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
            
        return self._with_session(_calculate_corte_data, start_time, end_time, drawer_id)

    def _calculate_starting_balance(self, session: Session, start_time: datetime, drawer_id: Optional[int] = None) -> Decimal:
        """
        Calculate the starting balance for the period by finding the most recent START entry
        before the period start time.
        
        Args:
            session: Database session
            start_time: The start time of the period
            drawer_id: Optional drawer ID to filter by specific cash drawer
            
        Returns:
            The starting balance as a Decimal
        """
        cash_drawer_repo = self._get_repository(self.cash_drawer_repo_factory, session)
        last_start_entry = cash_drawer_repo.get_last_start_entry(drawer_id)
        
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
        def _register_closing_balance(session, drawer_id, actual_amount, description, user_id):
            cash_drawer_repo = self._get_repository(self.cash_drawer_repo_factory, session)
            
            # Check if drawer is open
            if not cash_drawer_repo.is_drawer_open(drawer_id):
                raise ValueError("Cash drawer is not open, cannot register closing balance")
                
            # Round actual_amount to 2 decimal places
            rounded_actual_amount = actual_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            closing_entry = CashDrawerEntry(
                timestamp=datetime.now(),
                entry_type=CashDrawerEntryType.CLOSE,
                amount=rounded_actual_amount,
                description=description,
                user_id=user_id,
                drawer_id=drawer_id
            )
            
            return cash_drawer_repo.add_entry(closing_entry)
            
        return self._with_session(_register_closing_balance, drawer_id, actual_amount, description, user_id)