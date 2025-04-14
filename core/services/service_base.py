"""
Base service class providing common functionality for all services.
"""
import logging
from typing import Type, TypeVar, Callable, Any, Optional
from sqlalchemy.orm import Session

from infrastructure.persistence.utils import session_scope

# Type for repository factories
RepositoryFactory = Callable[[Session], Any]

class ServiceBase:
    """Base class for all services, providing standard logging and repository handling."""
    
    def __init__(self, logger_name=None):
        """
        Initialize the service with a logger.
        
        Args:
            logger_name: Name for the logger. Defaults to class name.
        """
        if logger_name is None:
            logger_name = self.__class__.__name__
        
        self.logger = logging.getLogger(logger_name)
        
    def _with_session(self, func, *args, **kwargs):
        """
        Execute a function within a session context.
        
        This helper method ensures all operations happen in a transaction.
        
        Args:
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            The result of func
        """
        with session_scope() as session:
            return func(session, *args, **kwargs)
            
    def _get_repository(self, factory: RepositoryFactory, session: Session):
        """
        Get a repository instance from a factory and session.
        
        Args:
            factory: The repository factory function
            session: The active database session
            
        Returns:
            The repository instance
        """
        return factory(session) 