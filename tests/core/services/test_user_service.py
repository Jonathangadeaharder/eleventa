"""
Tests for the UserService class.

This test suite verifies all functionality related to user management:
- User creation with proper password hashing
- Authentication with username/password
- User retrieval by ID and username
- Error cases and validation checks

Coverage goals:
- 100% coverage of UserService public methods
- All validation error scenarios
- Edge cases for authentication

Test dependencies:
- Mock UserRepository for isolation
- bcrypt for password hashing verification
"""
import pytest
from unittest.mock import MagicMock, patch
import bcrypt

# Adjust path
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.services.user_service import UserService
from core.models.user import User
from core.interfaces.repository_interfaces import IUserRepository

# Helper function (outside of any class/fixture)
def _hash_password(password: str) -> str:
    """Helper to hash password for tests."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

@pytest.fixture
def mock_user_repo():
    """Create a mock user repository for testing."""
    return MagicMock(spec=IUserRepository)

@pytest.fixture
def user_service(mock_user_repo):
    """Create a UserService with a mock repository."""
    return UserService(mock_user_repo)

def test_add_user_with_valid_data_succeeds(user_service, mock_user_repo):
    """
    Test that adding a user with valid data succeeds.
    
    This test verifies:
    1. The user is properly persisted with the repository
    2. The password is securely hashed (not stored in plain text)
    3. The returned user has the expected properties
    4. The repository is called with the correct parameters
    """
    username = "newuser"
    password = "password123"
    
    # Mock repo behavior
    mock_user_repo.get_by_username.return_value = None # No existing user
    # Mock the add method to return a user with an ID
    def mock_add(user):
        user.id = 1 # Simulate ID assignment
        return user
    mock_user_repo.add.side_effect = mock_add

    created_user = user_service.add_user(username, password)

    mock_user_repo.get_by_username.assert_called_once_with(username)
    mock_user_repo.add.assert_called_once()
    
    # Get the user object passed to repo.add
    added_user_arg = mock_user_repo.add.call_args[0][0]
    
    assert added_user_arg.username == username
    assert bcrypt.checkpw(password.encode('utf-8'), added_user_arg.password_hash.encode('utf-8'))
    assert added_user_arg.is_active
    
    # Check the returned user has an ID
    assert created_user.id == 1
    assert created_user.username == username

def test_add_user_with_existing_username_raises_error(user_service, mock_user_repo):
    """
    Test that adding a user with an existing username raises an error.
    
    This test verifies:
    1. An appropriate ValueError is raised with a descriptive message
    2. The user is not added to the repository
    3. The repository is queried correctly to check for existing users
    """
    username = "existinguser"
    password = "password123"
    
    # Mock repo to return an existing user
    existing_user = User(id=1, username=username, password_hash="some_hash")
    mock_user_repo.get_by_username.return_value = existing_user

    with pytest.raises(ValueError, match=f"Username '{username}' already exists."):
        user_service.add_user(username, password)
        
    mock_user_repo.get_by_username.assert_called_once_with(username)
    mock_user_repo.add.assert_not_called()

def test_add_user_with_empty_username_raises_error(user_service, mock_user_repo):
    """
    Test that adding a user with an empty username raises an error.
    
    This is a validation test that ensures users must have valid usernames.
    The repository should not be called to add a user in this case.
    """
    with pytest.raises(ValueError, match="Username cannot be empty."):
        user_service.add_user("", "password123")
    mock_user_repo.add.assert_not_called()

def test_add_user_with_empty_password_raises_error(user_service, mock_user_repo):
    """
    Test that adding a user with an empty password raises an error.
    
    This test verifies password validation logic and ensures that
    empty passwords are rejected before any repository calls.
    """
    mock_user_repo.get_by_username.return_value = None
    with pytest.raises(ValueError, match="Password cannot be empty."):
        user_service.add_user("testuser", "")
    mock_user_repo.add.assert_not_called()

def test_authenticate_with_valid_credentials_succeeds(user_service, mock_user_repo):
    """
    Test that authentication succeeds with valid credentials.
    
    This test verifies:
    1. Authentication returns the correct user when credentials match
    2. The password hash comparison works correctly
    3. The repository is called with the correct parameters
    """
    username = "authuser"
    password = "correctpassword"
    hashed_password = _hash_password(password)
    
    mock_user = User(id=5, username=username, password_hash=hashed_password, is_active=True)
    mock_user_repo.get_by_username.return_value = mock_user

    authenticated_user = user_service.authenticate_user(username, password)

    mock_user_repo.get_by_username.assert_called_once_with(username)
    assert authenticated_user is not None
    assert authenticated_user.id == 5
    assert authenticated_user.username == username

def test_authenticate_with_incorrect_password_returns_none(user_service, mock_user_repo):
    """Test that authentication with incorrect password returns None."""
    username = "authuser"
    correct_password = "correctpassword"
    incorrect_password = "wrongpassword"
    hashed_password = _hash_password(correct_password)
    
    mock_user = User(id=5, username=username, password_hash=hashed_password, is_active=True)
    mock_user_repo.get_by_username.return_value = mock_user

    authenticated_user = user_service.authenticate_user(username, incorrect_password)

    mock_user_repo.get_by_username.assert_called_once_with(username)
    assert authenticated_user is None

def test_authenticate_with_nonexistent_user_returns_none(user_service, mock_user_repo):
    """Test that authentication with nonexistent user returns None."""
    username = "nosuchuser"
    password = "password123"
    
    mock_user_repo.get_by_username.return_value = None

    authenticated_user = user_service.authenticate_user(username, password)

    mock_user_repo.get_by_username.assert_called_once_with(username)
    assert authenticated_user is None

def test_authenticate_with_inactive_user_returns_none(user_service, mock_user_repo):
    """Test that authentication with inactive user returns None."""
    username = "inactiveuser"
    password = "password123"
    hashed_password = _hash_password(password)
    
    mock_user = User(id=6, username=username, password_hash=hashed_password, is_active=False)
    mock_user_repo.get_by_username.return_value = mock_user

    authenticated_user = user_service.authenticate_user(username, password)

    mock_user_repo.get_by_username.assert_called_once_with(username)
    assert authenticated_user is None

def test_authenticate_with_empty_credentials_returns_none(user_service, mock_user_repo):
    """Test that authentication with empty credentials returns None."""
    assert user_service.authenticate_user("", "password") is None
    assert user_service.authenticate_user("user", "") is None
    assert user_service.authenticate_user("", "") is None
    mock_user_repo.get_by_username.assert_not_called()

def test_get_user_by_id_returns_user_when_exists(user_service, mock_user_repo):
    """Test that getting a user by ID returns the user when it exists."""
    user_id = 10
    mock_user = User(id=user_id, username="test", password_hash="hash")
    mock_user_repo.get_by_id.return_value = mock_user

    user = user_service.get_user(user_id)

    mock_user_repo.get_by_id.assert_called_once_with(user_id)
    assert user == mock_user

def test_get_user_by_username_returns_user_when_exists(user_service, mock_user_repo):
    """Test that getting a user by username returns the user when it exists."""
    username = "testuser"
    mock_user = User(id=11, username=username, password_hash="hash")
    mock_user_repo.get_by_username.return_value = mock_user

    user = user_service.get_user_by_username(username)

    mock_user_repo.get_by_username.assert_called_once_with(username)
    assert user == mock_user
