"""
Utilities for database session management.
"""
from contextlib import contextmanager
from typing import Optional, Callable, Any, Generator
import logging

class SessionScopeProvider:
    """
    Provider for the session factory to be used with the session_scope context manager.
    This allows different parts of the application to use different session factories.
    """
    def __init__(self):
        self._default_session_factory = None
        self._current_session_factory = None
    
    def set_default_session_factory(self, session_factory: Callable) -> None:
        """
        Set the default session factory.
        
        Args:
            session_factory: A callable that returns a new session
        """
        self._default_session_factory = session_factory
    
    def set_session_factory(self, session_factory: Optional[Callable]) -> None:
        """
        Set the current session factory.
        
        Args:
            session_factory: A callable that returns a new session, or None to use the default
        """
        self._current_session_factory = session_factory
    
    def get_session_factory(self) -> Callable:
        """
        Get the current session factory, or the default if no current factory is set.
        
        Returns:
            A callable that returns a new session
        """
        return self._current_session_factory or self._default_session_factory
    
    def get_session(self) -> Any:
        """
        Get a new session using the current factory.
        
        Returns:
            A new session
        """
        session_factory = self.get_session_factory()
        if session_factory is None:
            raise ValueError("No session factory has been set. Make sure to call set_default_session_factory or set_session_factory first.")
        return session_factory()

# Global session scope provider
session_scope_provider = SessionScopeProvider()

@contextmanager
def session_scope(*, session=None) -> Generator[Any, None, None]:
    """
    Provide a transactional scope around a series of operations.
    
    This function can be used in two ways:
    1. With no parameters: creates and manages a new session
       Example: with session_scope() as session: ...
    
    2. With an existing session: uses the provided session without managing it
       Example: with session_scope(existing_session) as session: ...
    
    Args:
        session: Optional existing session to use. If provided, this function
                will NOT commit, rollback, or close the session.
    
    Yields:
        A session to use for database operations
    """
    # Determine whether we're managing the session lifecycle
    managing_session = session is None
    
    # If no session provided, create a new one
    if managing_session:
        session = session_scope_provider.get_session()
    
    try:
        yield session
        # Only commit if we're managing the session
        if managing_session:
            session.commit()
    except Exception as e:
        # Only rollback if we're managing the session
        if managing_session:
            logging.error(f"Error during session: {e}. Rolling back.")
            session.rollback()
        raise
    finally:
        # Only close if we're managing the session
        if managing_session:
            session.close()