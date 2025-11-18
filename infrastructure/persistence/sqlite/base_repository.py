from typing import Callable


class BaseRepository:
    """Base repository class providing common functionality for SQLite repositories."""

    def __init__(self, session_factory: Callable):
        """
        Initialize the repository with a session factory.

        Args:
            session_factory: A callable that returns a SQLAlchemy session
        """
        self._session_factory = session_factory
