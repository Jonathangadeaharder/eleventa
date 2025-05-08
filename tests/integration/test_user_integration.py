"""
Integration tests for UserService and authentication workflows.

These tests verify integration between UserService and the SQLite persistence layer,
covering user creation and authentication scenarios.
"""

import pytest
from sqlalchemy.sql import text
import time

from core.services.user_service import UserService
from infrastructure.persistence.sqlite.repositories import SqliteUserRepository
from core.models.user import User
from infrastructure.persistence.sqlite.models_mapping import map_models, ensure_all_models_mapped

@pytest.fixture
def user_service(clean_db):
    """Provide a UserService backed by a clean in-memory SQLite database."""
    # Extract session from the clean_db tuple (session, test_user)
    session, _ = clean_db
    
    # Make sure to clean any users that might have been added by other tests
    session.execute(text("DELETE FROM users WHERE username IN ('johndoe', 'dupuser', 'authuser', 'authfail')"))
    session.commit()
    
    # Create a factory function instead of passing the repo instance directly
    def user_repo_factory(session):
        return SqliteUserRepository(session)
    
    service = UserService(user_repo_factory)
    return service

@pytest.mark.integration
class TestUserIntegration:
    """Integration tests for UserService and repository interactions."""

    @classmethod
    def setup_class(cls):
        """Ensure all models are mapped before running tests."""
        # This ensures the UserOrm and other tables are created properly
        map_models()
        ensure_all_models_mapped()
        
        print("All models mapped for TestUserIntegration tests")

    def test_add_user_valid_user_returns_user(self, user_service):
        """
        Test that adding a valid user returns a User object with an assigned ID
        and correct username and active status.
        """
        # Use timestamp to ensure unique username
        timestamp = int(time.time() * 1000)
        username = f"johndoe_{timestamp}"
        
        new_user = user_service.add_user(username, "password123")
        assert new_user.id is not None
        assert new_user.username == username
        assert new_user.is_active is True

        # Verify user is persisted
        fetched_user = user_service.get_user_by_id(new_user.id)
        assert fetched_user.username == username
        assert fetched_user.is_active is True

    def test_add_user_duplicate_username_raises_value_error(self, user_service):
        """
        Test that adding a user with a duplicate username raises a ValueError.
        """
        # Use timestamp to ensure unique username for first user
        timestamp = int(time.time() * 1000)
        username = f"dupuser_{timestamp}"
        
        user_service.add_user(username, "pass1")
        with pytest.raises(ValueError) as exc:
            user_service.add_user(username, "pass2")
        assert "already exists" in str(exc.value)

    def test_authenticate_user_valid_credentials_returns_user(self, user_service):
        """
        Test that authenticating with correct credentials returns the User.
        """
        # Use timestamp to ensure unique username
        timestamp = int(time.time() * 1000)
        username = f"authuser_{timestamp}"
        
        created_user = user_service.add_user(username, "secret")
        authenticated = user_service.authenticate_user(username, "secret")
        assert authenticated is not None
        assert authenticated.id == created_user.id
        assert authenticated.username == username

    def test_authenticate_user_invalid_credentials_returns_none(self, user_service):
        """
        Test that authentication with invalid credentials returns None.
        """
        # Use timestamp to ensure unique username
        timestamp = int(time.time() * 1000)
        username = f"authfail_{timestamp}"
        
        user_service.add_user(username, "goodpass")
        assert user_service.authenticate_user(username, "badpass") is None
        # Also test non-existent user
        assert user_service.authenticate_user("nope", "any") is None
