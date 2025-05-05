"""
Integration tests for UserService and authentication workflows.

These tests verify integration between UserService and the SQLite persistence layer,
covering user creation and authentication scenarios.
"""

import pytest

from core.services.user_service import UserService
from infrastructure.persistence.sqlite.repositories import SqliteUserRepository
from core.models.user import User
from infrastructure.persistence.sqlite.models_mapping import map_models, ensure_all_models_mapped

@pytest.fixture
def user_service(clean_db):
    """Provide a UserService backed by a clean in-memory SQLite database."""
    # Extract session from the clean_db tuple (session, test_user)
    session, _ = clean_db
    repo = SqliteUserRepository(session)
    service = UserService(repo)
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
        new_user = user_service.add_user("johndoe", "password123")
        assert new_user.id is not None
        assert new_user.username == "johndoe"
        assert new_user.is_active is True

        # Verify user is persisted
        fetched_user = user_service.get_user_by_id(new_user.id)
        assert fetched_user.username == "johndoe"
        assert fetched_user.is_active is True

    def test_add_user_duplicate_username_raises_value_error(self, user_service):
        """
        Test that adding a user with a duplicate username raises a ValueError.
        """
        user_service.add_user("dupuser", "pass1")
        with pytest.raises(ValueError) as exc:
            user_service.add_user("dupuser", "pass2")
        assert "already exists" in str(exc.value)

    def test_authenticate_user_valid_credentials_returns_user(self, user_service):
        """
        Test that authenticating with correct credentials returns the User.
        """
        created_user = user_service.add_user("authuser", "secret")
        authenticated = user_service.authenticate_user("authuser", "secret")
        assert authenticated is not None
        assert authenticated.id == created_user.id
        assert authenticated.username == "authuser"

    def test_authenticate_user_invalid_credentials_returns_none(self, user_service):
        """
        Test that authentication with invalid credentials returns None.
        """
        user_service.add_user("authfail", "goodpass")
        assert user_service.authenticate_user("authfail", "badpass") is None
        # Also test non-existent user
        assert user_service.authenticate_user("nope", "any") is None
