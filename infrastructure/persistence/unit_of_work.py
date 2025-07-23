"""Unit of Work pattern implementation for managing database transactions.

This module provides a centralized way to manage database sessions and repositories
within a single transactional context, ensuring data consistency across multiple
repository operations.
"""

from typing import Optional
from contextlib import contextmanager
import logging

from .utils import session_scope_provider
from .sqlite.repositories import (
    SqliteDepartmentRepository,
    SqliteProductRepository,
    SqliteInventoryRepository,
    SqliteSaleRepository,
    SqliteCustomerRepository,
    SqliteInvoiceRepository,
    SqliteCreditPaymentRepository,
    SqliteUserRepository,
    SqliteCashDrawerRepository,
    SqliteUnitRepository
)


class UnitOfWork:
    """Unit of Work implementation for managing database transactions.
    
    This class provides a centralized way to manage database sessions and
    repositories within a single transactional context. It ensures that all
    repository operations within the same unit of work share the same database
    session and are committed or rolled back together.
    
    Usage:
        with UnitOfWork() as uow:
            product = uow.products.get_by_id(1)
            product.price = 100
            uow.products.update(product)
            # Transaction is automatically committed on successful exit
    """
    
    def __init__(self):
        """Initialize the Unit of Work."""
        self.session_factory = session_scope_provider.get_session_factory()
        self.session = None
        
        # Repository instances (initialized in __enter__)
        self.departments: Optional[SqliteDepartmentRepository] = None
        self.products: Optional[SqliteProductRepository] = None
        self.inventory: Optional[SqliteInventoryRepository] = None
        self.sales: Optional[SqliteSaleRepository] = None
        self.customers: Optional[SqliteCustomerRepository] = None
        self.invoices: Optional[SqliteInvoiceRepository] = None
        self.credit_payments: Optional[SqliteCreditPaymentRepository] = None
        self.users: Optional[SqliteUserRepository] = None
        self.cash_drawer: Optional[SqliteCashDrawerRepository] = None
        self.units: Optional[SqliteUnitRepository] = None
    
    def __enter__(self):
        """Enter the Unit of Work context.
        
        Creates a new database session and initializes all repositories
        with the shared session.
        
        Returns:
            UnitOfWork: The Unit of Work instance with initialized repositories.
        """
        if self.session_factory is None:
            raise ValueError(
                "No session factory has been set. Make sure to call "
                "session_scope_provider.set_default_session_factory() first."
            )
        
        try:
            # Check if we're in a test environment where get_session should be used instead
            # This allows tests to provide a pre-configured session with proper isolation
            try:
                self.session = session_scope_provider.get_session()
                self._session_created_by_factory = False  # Test session, don't close it
                logging.debug("Using test session from session_scope_provider")
            except Exception as e:
                # Fallback to session factory if get_session doesn't work
                logging.debug(f"get_session failed with {type(e).__name__}: {e}, falling back to session factory")
                self.session = self.session_factory()
                self._session_created_by_factory = True  # We created it, we should close it
        except Exception as e:
            logging.error(f"Failed to create database session: {e}")
            raise ValueError(f"Database connection error: {e}") from e
        
        # Initialize all repositories with the shared session
        self.departments = SqliteDepartmentRepository(self.session)
        self.products = SqliteProductRepository(self.session)
        self.inventory = SqliteInventoryRepository(self.session)
        self.sales = SqliteSaleRepository(self.session)
        self.customers = SqliteCustomerRepository(self.session)
        self.invoices = SqliteInvoiceRepository(self.session)
        self.credit_payments = SqliteCreditPaymentRepository(self.session)
        self.users = SqliteUserRepository(self.session)
        # Note: SQLiteCashDrawerRepository has a different interface and uses _session internally
        self.cash_drawer = SqliteCashDrawerRepository(self.session)
        self.units = SqliteUnitRepository(self.session)
        
        return self
    
    def __exit__(self, exc_type, exc_val, traceback):
        """Exit the Unit of Work context.
        
        Handles transaction commit/rollback and session cleanup.
        
        Args:
            exc_type: Exception type if an exception occurred.
            exc_val: Exception value if an exception occurred.
            traceback: Exception traceback if an exception occurred.
        """
        if self.session is None:
            return
        
        try:
            if exc_type is not None:
                # An exception occurred, rollback the transaction
                logging.warning(f"Exception in UnitOfWork, rolling back: {exc_val}")
                self.session.rollback()
            else:
                # No exception, commit the transaction
                # Always commit to ensure data persists across UnitOfWork instances
                self.session.commit()
        except Exception as e:
            # Error during commit/rollback
            logging.error(f"Error during transaction finalization: {e}")
            try:
                self.session.rollback()
            except Exception as rollback_error:
                logging.error(f"Additional error during rollback: {rollback_error}")
            raise
        finally:
            # Don't close the session if it came from session_scope_provider (test environment)
            # In test environments, the session is managed by the test framework
            if getattr(self, '_session_created_by_factory', True):
                try:
                    self.session.close()
                except Exception as close_error:
                    logging.error(f"Error closing session: {close_error}")
            
            # Always clear references
            self.session = None
            # Clear repository references
            self.departments = None
            self.products = None
            self.inventory = None
            self.sales = None
            self.customers = None
            self.invoices = None
            self.credit_payments = None
            self.users = None
            self.cash_drawer = None
            self.units = None
    
    def commit(self):
        """Manually commit the current transaction.
        
        This method allows for explicit transaction commits within
        the Unit of Work context. Use with caution as it may affect
        the atomicity of operations.
        
        Raises:
            ValueError: If no active session exists.
        """
        if self.session is None:
            raise ValueError("No active session to commit")
        
        try:
            self.session.commit()
            logging.debug("Transaction committed manually")
        except Exception as e:
            logging.error(f"Error during manual commit: {e}")
            self.session.rollback()
            raise ValueError(f"Database commit error: {e}") from e
    
    def rollback(self):
        """Manually rollback the current transaction.
        
        This method allows for explicit transaction rollbacks within
        the Unit of Work context.
        
        Raises:
            ValueError: If no active session exists.
        """
        if self.session is None:
            raise ValueError("No active session to rollback")
        
        try:
            self.session.rollback()
            logging.debug("Transaction rolled back manually")
        except Exception as e:
            logging.error(f"Error during manual rollback: {e}")
            raise ValueError(f"Database rollback error: {e}") from e


@contextmanager
def unit_of_work():
    """Context manager for creating a Unit of Work.
    
    This is a convenience function that provides a more concise way
    to use the Unit of Work pattern.
    
    Usage:
        with unit_of_work() as uow:
            product = uow.products.get_by_id(1)
            uow.products.update(product)
    
    Yields:
        UnitOfWork: A configured Unit of Work instance.
    """
    with UnitOfWork() as uow:
        yield uow