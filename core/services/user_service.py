import bcrypt
from typing import Optional

# Adjust path if necessary
try:
    from ..interfaces.repository_interfaces import IUserRepository
    from ..models.user import User
except ImportError:
    # Fallback for different import contexts
    from core.interfaces.repository_interfaces import IUserRepository
    from core.models.user import User

class UserService:
    """Handles business logic related to users."""

    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository

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

    def add_user(self, username: str, password: str) -> User:
        """Adds a new user with a hashed password."""
        if not username:
            raise ValueError("Username cannot be empty.")
        # Check if username already exists
        existing_user = self.user_repository.get_by_username(username)
        if existing_user:
            raise ValueError(f"Username '{username}' already exists.")

        hashed_password = self._hash_password(password)
        new_user = User(username=username, password_hash=hashed_password, is_active=True)
        
        # The repository's add method should handle the actual saving
        # and return the user with an assigned ID.
        created_user = self.user_repository.add(new_user)
        return created_user

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Gets a user by their ID."""
        return self.user_repository.get_by_id(user_id)

    def get_user(self, user_id: int) -> Optional[User]:
        """Gets a user by their ID (alias for get_user_by_id)."""
        return self.get_user_by_id(user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Gets a user by their username."""
        return self.user_repository.get_by_username(username)

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticates a user by username and password."""
        if not username or not password:
            return None # Or raise ValueError? Returning None is common for auth failures.

        user = self.user_repository.get_by_username(username)
        if not user or not user.is_active:
            return None # User not found or inactive

        if self._verify_password(password, user.password_hash):
            return user # Authentication successful
        else:
            return None # Password incorrect

    # Add update/delete methods later if needed, handling password changes carefully
