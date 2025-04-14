import pytest
from unittest.mock import MagicMock
import bcrypt
from typing import Optional, List

from core.models.user import User
from core.interfaces.repository_interfaces import IUserRepository

# Import application ORM and Repository
from infrastructure.persistence.sqlite.models_mapping import UserOrm
from infrastructure.persistence.sqlite.repositories import SqliteUserRepository, _map_user_orm_to_model # Import the real repo and potentially the mapper

# Remove imports from the now-cleaned conftest
# from tests.conftest import test_metadata, TestBase

class TestUserRepository:
    """Tests for the real SqliteUserRepository."""

    def _hash_password(self, password: str) -> str:
        """Generate a hash for testing."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def test_add_user(self, test_db_session):
        """Test adding a new user."""
        # Use the real repository
        user_repo = SqliteUserRepository(test_db_session)

        # Create test user
        hashed_pw = self._hash_password("password123")
        user_to_add = User(username="testuser", password_hash=hashed_pw)
        
        # Add the user
        added_user = user_repo.add(user_to_add)
        
        # Verify the user was added
        assert added_user.id is not None
        assert added_user.username == "testuser"

    def test_add_user_duplicate_username(self, test_db_session):
        """Test adding a user with a duplicate username raises ValueError."""
        # Use the real repository
        user_repo = SqliteUserRepository(test_db_session)

        # Add first user
        hashed_pw = self._hash_password("password123")
        user1 = User(username="duplicate", password_hash=hashed_pw)
        user_repo.add(user1)
        
        # Add second user with same username
        user2 = User(username="duplicate", password_hash=hashed_pw)
        with pytest.raises(ValueError, match=".*already exist.*"):
            user_repo.add(user2)

    def test_get_user_by_id(self, test_db_session):
        """Test retrieving a user by ID."""
        # Use the real repository
        user_repo = SqliteUserRepository(test_db_session)

        # Add test user
        hashed_pw = self._hash_password("getme")
        user_to_add = User(username="findme", password_hash=hashed_pw)
        added_user = user_repo.add(user_to_add)
        
        # Get the user by ID
        found_user = user_repo.get_by_id(added_user.id)
        
        # Verify the user was found
        assert found_user is not None
        assert found_user.username == "findme"

    def test_get_user_by_id_not_found(self, test_db_session):
        """Test retrieving a non-existent user by ID returns None."""
        # Use the real repository
        user_repo = SqliteUserRepository(test_db_session)

        # Try to get non-existent user
        found_user = user_repo.get_by_id(999)
        
        # Verify no user was found
        assert found_user is None

    def test_get_user_by_username(self, test_db_session):
        """Test retrieving a user by username."""
        # Use the real repository
        user_repo = SqliteUserRepository(test_db_session)

        # Add test user
        hashed_pw = self._hash_password("password")
        user_to_add = User(username="getbyname", password_hash=hashed_pw)
        added_user = user_repo.add(user_to_add)
        
        # Get the user by username
        found_user = user_repo.get_by_username("getbyname")
        
        # Verify the user was found
        assert found_user is not None
        assert found_user.id == added_user.id

    def test_get_user_by_username_not_found(self, test_db_session):
        """Test retrieving a non-existent user by username returns None."""
        # Use the real repository
        user_repo = SqliteUserRepository(test_db_session)

        # Try to get non-existent user
        found_user = user_repo.get_by_username("nosuchuser")
        
        # Verify no user was found
        assert found_user is None
