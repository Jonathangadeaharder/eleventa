from decimal import Decimal
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any

from core.models.cash_drawer import CashDrawerEntry, CashDrawerEntryType
from core.interfaces.repository_interfaces import ICashDrawerRepository


class CashDrawerService:
    """Service for cash drawer operations."""
    
    def __init__(self, cash_drawer_repository: ICashDrawerRepository):
        self.repository = cash_drawer_repository
        
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
        # Validate that the drawer is not already open
        if self.repository.is_drawer_open(drawer_id):
            raise ValueError("Cash drawer is already open")
            
        # Validate initial amount
        if initial_amount < 0:
            raise ValueError("Initial amount cannot be negative")
            
        # Create the entry
        entry = CashDrawerEntry(
            timestamp=datetime.now(),
            entry_type=CashDrawerEntryType.START,
            amount=initial_amount,
            description=description,
            user_id=user_id,
            drawer_id=drawer_id
        )
        
        # Add to repository
        return self.repository.add_entry(entry)
        
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
        # Validate that the drawer is open
        if not self.repository.is_drawer_open(drawer_id):
            raise ValueError("Cash drawer is not open")
            
        # Validate amount
        if amount <= 0:
            raise ValueError("Amount must be positive")
            
        # Create the entry
        entry = CashDrawerEntry(
            timestamp=datetime.now(),
            entry_type=CashDrawerEntryType.IN,
            amount=amount,
            description=description,
            user_id=user_id,
            drawer_id=drawer_id
        )
        
        # Add to repository
        return self.repository.add_entry(entry)
        
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
        # Validate that the drawer is open
        if not self.repository.is_drawer_open(drawer_id):
            raise ValueError("Cash drawer is not open")
            
        # Validate amount
        if amount <= 0:
            raise ValueError("Amount must be positive")
            
        # Check if there's enough cash in the drawer
        current_balance = self.repository.get_current_balance(drawer_id)
        if amount > current_balance:
            raise ValueError(f"Insufficient cash in drawer. Current balance: {current_balance}")
            
        # Create the entry (using negative amount for removals)
        entry = CashDrawerEntry(
            timestamp=datetime.now(),
            entry_type=CashDrawerEntryType.OUT,
            amount=-amount,  # Store as negative to properly calculate balance
            description=description,
            user_id=user_id,
            drawer_id=drawer_id
        )
        
        # Add to repository
        return self.repository.add_entry(entry)
        
    def get_drawer_summary(self, drawer_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get a summary of the drawer's status.
        
        Args:
            drawer_id: Optional drawer ID for multi-drawer support
            
        Returns:
            A dictionary with drawer summary information
        """
        # Get drawer status
        is_open = self.repository.is_drawer_open(drawer_id)
        
        # Get entries for today
        entries_today = self.repository.get_today_entries(drawer_id)
        
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
        current_balance = self.repository.get_current_balance(drawer_id)
        
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