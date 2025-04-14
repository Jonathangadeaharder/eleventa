from typing import List, Optional, Dict, Any, Callable, Union
from datetime import datetime, date, timedelta
from decimal import Decimal
from functools import wraps

from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, select

from core.interfaces.repository_interfaces import CashDrawerRepository
from core.models.cash_drawer import CashDrawerEntry, CashDrawerEntryType
from infrastructure.persistence.sqlite.models_mapping import CashDrawerEntryOrm
from infrastructure.persistence.sqlite.base_repository import BaseRepository

class SQLiteCashDrawerRepository(CashDrawerRepository):
    """SQLite implementation of the CashDrawerRepository."""
    
    def __init__(self, session_or_factory: Union[Session, Callable[[], Session]]):
        """
        Initialize the repository with either a session or session factory.
        
        Args:
            session_or_factory: Either a SQLAlchemy session or a callable that returns a session
        """
        self._session = None
        self._session_factory = None
        
        if callable(session_or_factory):
            self._session_factory = session_or_factory
        else:
            self._session = session_or_factory
    
    def _get_session(self):
        """Get the session to use for database operations."""
        return self._session
    
    def _session_wrapper(self, func):
        """Wrapper to handle session management."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            if self._session_factory:
                with self._session_factory() as session:
                    return func(session, *args, **kwargs)
            else:
                return func(self._session, *args, **kwargs)
        return wrapper
    
    def add_entry(self, entry: CashDrawerEntry) -> CashDrawerEntry:
        """Add a new cash drawer entry."""
        @self._session_wrapper
        def _add_entry(session, entry):
            # Create ORM model from domain model
            entry_orm = CashDrawerEntryOrm(
                timestamp=entry.timestamp,
                entry_type=entry.entry_type.value if isinstance(entry.entry_type, CashDrawerEntryType) else entry.entry_type,
                amount=entry.amount,
                description=entry.description,
                user_id=entry.user_id,
                drawer_id=entry.drawer_id
            )
            
            # Add to session
            session.add(entry_orm)
            session.commit()
            
            # Update domain model with generated ID
            entry.id = entry_orm.id
            
            return entry
        return _add_entry(entry)
            
    def get_entry_by_id(self, entry_id: int) -> Optional[CashDrawerEntry]:
        """Get a cash drawer entry by ID."""
        @self._session_wrapper
        def _get_entry_by_id(session, entry_id):
            entry_orm = session.query(CashDrawerEntryOrm).filter(
                CashDrawerEntryOrm.id == entry_id
            ).first()
            
            if not entry_orm:
                return None
                
            return self._map_to_domain_model(entry_orm)
        return _get_entry_by_id(entry_id)
            
    def get_entries_by_date_range(self, start_date: date, end_date: date, drawer_id: Optional[int] = None) -> List[CashDrawerEntry]:
        """Get cash drawer entries within a date range."""
        @self._session_wrapper
        def _get_entries_by_date_range(session, start_date, end_date, drawer_id):
            # Convert date objects to datetime objects for inclusive range
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            query = session.query(CashDrawerEntryOrm).filter(
                CashDrawerEntryOrm.timestamp >= start_datetime,
                CashDrawerEntryOrm.timestamp <= end_datetime
            )
            
            # Apply drawer_id filter if specified
            if drawer_id is not None:
                query = query.filter(CashDrawerEntryOrm.drawer_id == drawer_id)
                
            # Order by timestamp
            query = query.order_by(CashDrawerEntryOrm.timestamp)
            
            entries_orm = query.all()
            
            return [self._map_to_domain_model(entry_orm) for entry_orm in entries_orm]
        return _get_entries_by_date_range(start_date, end_date, drawer_id)
            
    def get_entries_by_drawer_id(self, drawer_id: int) -> List[CashDrawerEntry]:
        """Get all entries for a specific drawer."""
        @self._session_wrapper
        def _get_entries_by_drawer_id(session, drawer_id):
            entries_orm = session.query(CashDrawerEntryOrm).filter(
                CashDrawerEntryOrm.drawer_id == drawer_id
            ).order_by(CashDrawerEntryOrm.timestamp).all()
            
            return [self._map_to_domain_model(entry_orm) for entry_orm in entries_orm]
        return _get_entries_by_drawer_id(drawer_id)
            
    def get_current_balance(self, drawer_id: Optional[int] = None) -> Decimal:
        """Get the current balance of the drawer."""
        @self._session_wrapper
        def _get_current_balance(session, drawer_id):
            query = session.query(func.sum(CashDrawerEntryOrm.amount).label("balance"))
            
            # Apply drawer_id filter if specified
            if drawer_id is not None:
                query = query.filter(CashDrawerEntryOrm.drawer_id == drawer_id)
                
            result = query.first()
            balance = result.balance if result and result.balance is not None else Decimal('0.00')
            
            return Decimal(str(balance))
        return _get_current_balance(drawer_id)
            
    def is_drawer_open(self, drawer_id: Optional[int] = None) -> bool:
        """Check if the drawer is currently open."""
        @self._session_wrapper
        def _is_drawer_open(session, drawer_id):
            # Get the most recent entry of type START
            start_type = CashDrawerEntryType.START.value
            close_type = CashDrawerEntryType.CLOSE.value
            
            query = session.query(CashDrawerEntryOrm).filter(
                CashDrawerEntryOrm.entry_type == start_type
            )
            
            # Apply drawer_id filter if specified
            if drawer_id is not None:
                query = query.filter(CashDrawerEntryOrm.drawer_id == drawer_id)
                
            # Order by timestamp descending to get the most recent
            start_entry = query.order_by(desc(CashDrawerEntryOrm.timestamp)).first()
            
            if not start_entry:
                return False
            
            # Check if there's a CLOSE entry after the most recent START entry
            close_query = session.query(CashDrawerEntryOrm).filter(
                CashDrawerEntryOrm.entry_type == close_type,
                CashDrawerEntryOrm.timestamp > start_entry.timestamp
            )
            
            if drawer_id is not None:
                close_query = close_query.filter(CashDrawerEntryOrm.drawer_id == drawer_id)
            
            close_entry = close_query.order_by(desc(CashDrawerEntryOrm.timestamp)).first()
            
            # The drawer is open if there's a START entry and no CLOSE entries after it
            return close_entry is None
        return _is_drawer_open(drawer_id)
            
    def get_today_entries(self, drawer_id: Optional[int] = None) -> List[CashDrawerEntry]:
        """Get entries for today."""
        today = date.today()
        return self.get_entries_by_date_range(today, today, drawer_id)
            
    def _map_to_domain_model(self, entry_orm: CashDrawerEntryOrm) -> CashDrawerEntry:
        """Map ORM model to domain model."""
        entry_type = CashDrawerEntryType(entry_orm.entry_type) if isinstance(entry_orm.entry_type, str) else entry_orm.entry_type
        return CashDrawerEntry(
            timestamp=entry_orm.timestamp,
            entry_type=entry_type,
            amount=Decimal(str(entry_orm.amount)),
            description=entry_orm.description,
            user_id=entry_orm.user_id,
            drawer_id=entry_orm.drawer_id,
            id=entry_orm.id
        )