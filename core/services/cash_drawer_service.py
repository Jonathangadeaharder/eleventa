from decimal import Decimal
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Callable
from sqlalchemy.orm import Session

from core.models.cash_drawer import CashDrawerEntry, CashDrawerEntryType
from core.interfaces.repository_interfaces import ICashDrawerRepository
from core.services.service_base import ServiceBase
from infrastructure.persistence.utils import session_scope
from decimal import Decimal, ROUND_HALF_UP


class CashDrawerService(ServiceBase):
    """Service for cash drawer operations."""
    
    def __init__(self, cash_drawer_repo_factory: Callable[[Session], ICashDrawerRepository]):
        """
        Initialize the service with a repository factory.
        
        Args:
            cash_drawer_repo_factory: Factory function to create cash drawer repository
        """
        super().__init__()  # Initialize base class with default logger
        self.cash_drawer_repo_factory = cash_drawer_repo_factory
        
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
        def _open_drawer(session, initial_amount, description, user_id, drawer_id):
            repository = self._get_repository(self.cash_drawer_repo_factory, session)
            
            # Validate that the drawer is not already open
            if repository.is_drawer_open(drawer_id):
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
            return repository.add_entry(entry)
            
        return self._with_session(_open_drawer, initial_amount, description, user_id, drawer_id)
        
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
        def _add_cash(session, amount, description, user_id, drawer_id):
            repository = self._get_repository(self.cash_drawer_repo_factory, session)
            
            # Validate that the drawer is open
            if not repository.is_drawer_open(drawer_id):
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
            return repository.add_entry(entry)
            
        return self._with_session(_add_cash, amount, description, user_id, drawer_id)
        
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
        def _remove_cash(session, amount, description, user_id, drawer_id):
            repository = self._get_repository(self.cash_drawer_repo_factory, session)
            
            # Validate that the drawer is open
            if not repository.is_drawer_open(drawer_id):
                raise ValueError("Cash drawer is not open")
                
            # Validate amount
            if amount <= 0:
                raise ValueError("Amount must be positive")
                
            # Check if there's enough cash in the drawer
            current_balance = repository.get_current_balance(drawer_id)
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
            return repository.add_entry(entry)
            
        return self._with_session(_remove_cash, amount, description, user_id, drawer_id)
        
    def get_drawer_summary(self, drawer_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get a summary of the drawer's status.
        
        Args:
            drawer_id: Optional drawer ID for multi-drawer support
            
        Returns:
            A dictionary with drawer summary information
        """
        def _get_drawer_summary(session, drawer_id):
            repository = self._get_repository(self.cash_drawer_repo_factory, session)
            
            # Get drawer status
            is_open = repository.is_drawer_open(drawer_id)
            
            # Get entries for today
            entries_today = repository.get_today_entries(drawer_id)
            
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
            current_balance = repository.get_current_balance(drawer_id)
            
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
            
        return self._with_session(_get_drawer_summary, drawer_id)