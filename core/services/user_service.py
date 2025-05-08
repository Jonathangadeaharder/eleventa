import bcrypt
from typing import Optional, Callable
from sqlalchemy.orm import Session

from core.services.service_base import ServiceBase
from core.interfaces.repository_interfaces import IUserRepository
from core.models.user import User
from infrastructure.persistence.utils import session_scope

class UserService(ServiceBase):
    """Handles business logic related to users."""

    def __init__(self, user_repo_factory: Callable[[Session], IUserRepository]):
        """
        Initialize the service with a repository factory.
        
        Args:
            user_repo_factory: Factory function to create user repository
        """
        super().__init__()  # Initialize base class with default logger
        self.user_repo_factory = user_repo_factory

    def _hash_password(self, password: str) -> str:
        """Hashes a plain text password using bcrypt."""
        if not password:
            raise ValueError("Password cannot be empty.")
        # Encode password to bytes, generate salt, hash, then decode back to string for storage
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_bytes = bcrypt.hashpw(password_bytes, salt)
        return hashed_bytes.decode('utf-8')

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifies a plain text password against a stored bcrypt hash."""
        if not plain_password or not hashed_password:
            return False
        plain_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain_bytes, hashed_bytes)

    def add_user(self, username: str, password: str) -> Optional[User]:
        """Adds a new user with a hashed password."""
        def _add_user(session, username, password):
            user_repo = self._get_repository(self.user_repo_factory, session)
            
            if not username:
                raise ValueError("Username cannot be empty.")
                
            # Check if username already exists
            existing_user = user_repo.get_by_username(username)
            if existing_user:
                self.logger.info(f"Username '{username}' already exists.")
                raise ValueError(f"Username '{username}' already exists.")

            hashed_password = self._hash_password(password)
            new_user = User(username=username, password_hash=hashed_password, is_active=True)
            
            # The repository's add method should handle the actual saving
            # and return the user with an assigned ID.
            self.logger.info(f"Creating new user: {username}")
            return user_repo.add(new_user)
            
        return self._with_session(_add_user, username, password)

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Gets a user by their ID."""
        def _get_user_by_id(session, user_id):
            user_repo = self._get_repository(self.user_repo_factory, session)
            return user_repo.get_by_id(user_id)
            
        return self._with_session(_get_user_by_id, user_id)

    def get_user(self, user_id: int) -> Optional[User]:
        """Gets a user by their ID (alias for get_user_by_id)."""
        return self.get_user_by_id(user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Gets a user by their username."""
        def _get_user_by_username(session, username):
            user_repo = self._get_repository(self.user_repo_factory, session)
            return user_repo.get_by_username(username)
            
        return self._with_session(_get_user_by_username, username)

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticates a user by username and password."""
        def _authenticate_user(session, username, password):
            if not username or not password:
                return None
                
            user_repo = self._get_repository(self.user_repo_factory, session)
            user = user_repo.get_by_username(username)
            
            if not user or not user.is_active:
                self.logger.info(f"Authentication failed for username '{username}': user not found or inactive")
                return None # User not found or inactive

            if self._verify_password(password, user.password_hash):
                self.logger.info(f"Authentication successful for user: {username}")
                return user # Authentication successful
            else:
                self.logger.info(f"Authentication failed for username '{username}': incorrect password")
                return None # Password incorrect
                
        return self._with_session(_authenticate_user, username, password)

    # Add update/delete methods later if needed, handling password changes carefully
