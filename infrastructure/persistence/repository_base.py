"""
Base class for repositories to standardize session management.
"""

from sqlalchemy.orm import Session
from typing import TypeVar, Generic, Optional

T = TypeVar("T")


class RepositoryBase(Generic[T]):
    """Base class for all repositories, providing standard session handling."""

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize with a session or None.

        If session is None, operations requiring it will fail.
        This allows for repository instantiation in places that will receive
        sessions later (like service layer factories).
        """
        self._session = session

    @property
    def session(self) -> Session:
        """
        Get the current session.

        Raises:
            RuntimeError: If session is not set
        """
        if self._session is None:
            raise RuntimeError(
                "Repository session not set. Use with session_scope or set session explicitly."
            )
        return self._session

    def set_session(self, session: Session) -> None:
        """Set the session for this repository instance."""
        self._session = session

    def _entity_to_domain(self, entity) -> T:
        """
        Convert an ORM entity to a domain model.

        Must be implemented by subclasses.
        """
        raise NotImplementedError

    def _domain_to_entity(self, domain_model: T):
        """
        Convert a domain model to an ORM entity.

        Must be implemented by subclasses.
        """
        raise NotImplementedError
