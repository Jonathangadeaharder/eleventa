from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any

from core.models.cash_drawer import CashDrawerEntry, CashDrawerEntryType
from core.services.service_base import ServiceBase
from infrastructure.persistence.unit_of_work import UnitOfWork, unit_of_work


class CashDrawerService(ServiceBase):
    """Service for cash drawer operations."""
    
    def __init__(self):
        """
        Initialize the service.
        """
        super().__init__()  # Initialize base class with default logger
        
    def open_drawer(self, initial_amount: Decimal, description: str, user_id: int, drawer_id: Optional[int] = None) -> CashDrawerEntry:
        """
        Open a cash drawer with an initial amount.
        
        Args:
            initial_amount: The opening balance
            description: Optional description for the opening
            user_id: ID of the user opening the drawer
            drawer_id: Optional drawer ID for multi-drawer support
            
        Returns:
            The created cash drawer entry
            
        Raises:
            ValueError: If the drawer is already open or if the initial amount is invalid
        """
        with unit_of_work() as uow:
            # Validate that the drawer is not already open
            if uow.cash_drawer.is_drawer_open(drawer_id):
                raise ValueError("Cash drawer is already open")
                
            # Validate initial amount
            if initial_amount < 0:
                raise ValueError("Initial amount cannot be negative")
                
            # Round amount to 2 decimal places
            rounded_initial_amount = initial_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Create the entry
            entry = CashDrawerEntry(
                timestamp=datetime.now(),
                entry_type=CashDrawerEntryType.START,
                amount=rounded_initial_amount,
                description=description,
                user_id=user_id,
                drawer_id=drawer_id
            )
            
            # Add to repository
            return uow.cash_drawer.add_entry(entry)
        
    def add_cash(self, amount: Decimal, description: str, user_id: int, drawer_id: Optional[int] = None) -> CashDrawerEntry:
        """
        Add cash to the drawer.
        
        Args:
            amount: The amount to add
            description: Description for the addition
            user_id: ID of the user adding cash
            drawer_id: Optional drawer ID for multi-drawer support
            
        Returns:
            The created cash drawer entry
            
        Raises:
            ValueError: If the drawer is not open or if the amount is invalid
        """
        with unit_of_work() as uow:
            # Validate that the drawer is open
            if not uow.cash_drawer.is_drawer_open(drawer_id):
                raise ValueError("Cash drawer is not open")
                
            # Validate amount
            if amount <= 0:
                raise ValueError("Amount must be positive")
                
            # Round amount to 2 decimal places
            rounded_amount = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Create the entry
            entry = CashDrawerEntry(
                timestamp=datetime.now(),
                entry_type=CashDrawerEntryType.IN,
                amount=rounded_amount,
                description=description,
                user_id=user_id,
                drawer_id=drawer_id
            )
            
            # Add to repository
            return uow.cash_drawer.add_entry(entry)
        
    def remove_cash(self, amount: Decimal, description: str, user_id: int, drawer_id: Optional[int] = None) -> CashDrawerEntry:
        """
        Remove cash from the drawer.
        
        Args:
            amount: The amount to remove (must be positive)
            description: Description for the removal
            user_id: ID of the user removing cash
            drawer_id: Optional drawer ID for multi-drawer support
            
        Returns:
            The created cash drawer entry
            
        Raises:
            ValueError: If the drawer is not open, if the amount is invalid, or if there's insufficient cash
        """
        with unit_of_work() as uow:
            # Validate that the drawer is open
            if not uow.cash_drawer.is_drawer_open(drawer_id):
                raise ValueError("Cash drawer is not open")
                
            # Validate amount
            if amount <= 0:
                raise ValueError("Amount must be positive")
                
            # Check if there's enough cash in the drawer
            current_balance = uow.cash_drawer.get_current_balance(drawer_id)
            if amount > current_balance:
                raise ValueError(f"Insufficient cash in drawer. Current balance: {current_balance}")
                
            # Round amount to 2 decimal places before negating
            rounded_amount = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Create the entry (using negative amount for removals)
            entry = CashDrawerEntry(
                timestamp=datetime.now(),
                entry_type=CashDrawerEntryType.OUT,
                amount=-rounded_amount,  # Store as negative to properly calculate balance
                description=description,
                user_id=user_id,
                drawer_id=drawer_id
            )
            
            # Add to repository
            return uow.cash_drawer.add_entry(entry)
        
    def get_drawer_summary(self, drawer_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get a summary of the drawer's status.
        
        Args:
            drawer_id: Optional drawer ID for multi-drawer support
            
        Returns:
            A dictionary with drawer summary information
        """
        with unit_of_work() as uow:
            # Get drawer status
            is_open = uow.cash_drawer.is_drawer_open(drawer_id)
            
            # Get entries for today
            entries_today = uow.cash_drawer.get_today_entries(drawer_id)
            
            # Calculate initial amount (from START entry)
            initial_amount = Decimal('0.00')
            opened_at = None
            opened_by = None
            
            for entry in entries_today:
                if entry.entry_type == CashDrawerEntryType.START:
                    initial_amount = entry.amount
                    opened_at = entry.timestamp
                    opened_by = entry.user_id
                    break
                    
            # Calculate totals
            current_balance = uow.cash_drawer.get_current_balance(drawer_id)
            
            total_in = sum([entry.amount for entry in entries_today 
                            if entry.entry_type == CashDrawerEntryType.IN], Decimal('0.00'))
                            
            total_out = sum([abs(entry.amount) for entry in entries_today 
                             if entry.entry_type == CashDrawerEntryType.OUT], Decimal('0.00'))
            
            # Build and return summary
            return {
                'is_open': is_open,
                'current_balance': current_balance,
                'initial_amount': initial_amount,
                'total_in': total_in,
                'total_out': total_out,
                'entries_today': entries_today,
                'opened_at': opened_at,
                'opened_by': opened_by
            }

    def close_drawer(self, actual_amount: Decimal, description: str, user_id: int, drawer_id: Optional[int] = None) -> CashDrawerEntry:
        """
        Close the cash drawer with the actual counted amount.

        Args:
            actual_amount: The actual amount counted in the drawer.
            description: Description for the closing entry.
            user_id: ID of the user closing the drawer.
            drawer_id: Optional drawer ID for multi-drawer support.

        Returns:
            The created cash drawer entry for the closing.

        Raises:
            ValueError: If the drawer is not open or if the actual amount is invalid.
        """
        with unit_of_work() as uow:
            if not uow.cash_drawer.is_drawer_open(drawer_id):
                raise ValueError("Cash drawer is not open. Cannot perform closing.")

            if actual_amount < 0:
                raise ValueError("Actual amount cannot be negative.")

            rounded_actual_amount = actual_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            entry = CashDrawerEntry(
                timestamp=datetime.now(),
                entry_type=CashDrawerEntryType.CLOSE,
                amount=rounded_actual_amount,  # This is the counted amount
                description=description,
                user_id=user_id,
                drawer_id=drawer_id
            )

            return uow.cash_drawer.add_entry(entry)