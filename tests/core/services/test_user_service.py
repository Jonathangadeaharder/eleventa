import unittest
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

class TestUserService(unittest.TestCase):

    def setUp(self):
        """Set up a mock repository and the service."""
        self.mock_user_repo = MagicMock(spec=IUserRepository)
        self.user_service = UserService(self.mock_user_repo)

    def _hash_password(self, password: str) -> str:
        """Helper to hash password for tests."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def test_add_user_success(self):
        """Test adding a user successfully."""
        username = "newuser"
        password = "password123"
        
        # Mock repo behavior
        self.mock_user_repo.get_by_username.return_value = None # No existing user
        # Mock the add method to return a user with an ID
        def mock_add(user):
            user.id = 1 # Simulate ID assignment
            return user
        self.mock_user_repo.add.side_effect = mock_add

        created_user = self.user_service.add_user(username, password)

        self.mock_user_repo.get_by_username.assert_called_once_with(username)
        self.mock_user_repo.add.assert_called_once()
        
        # Get the user object passed to repo.add
        added_user_arg = self.mock_user_repo.add.call_args[0][0]
        
        self.assertEqual(added_user_arg.username, username)
        self.assertTrue(bcrypt.checkpw(password.encode('utf-8'), added_user_arg.password_hash.encode('utf-8')))
        self.assertTrue(added_user_arg.is_active)
        
        # Check the returned user has an ID
        self.assertEqual(created_user.id, 1)
        self.assertEqual(created_user.username, username)

    def test_add_user_duplicate_username(self):
        """Test adding a user with an existing username raises ValueError."""
        username = "existinguser"
        password = "password123"
        
        # Mock repo to return an existing user
        existing_user = User(id=1, username=username, password_hash="some_hash")
        self.mock_user_repo.get_by_username.return_value = existing_user

        with self.assertRaisesRegex(ValueError, f"Username '{username}' already exists."):
            self.user_service.add_user(username, password)
            
        self.mock_user_repo.get_by_username.assert_called_once_with(username)
        self.mock_user_repo.add.assert_not_called()

    def test_add_user_empty_username(self):
        """Test adding a user with an empty username raises ValueError."""
        with self.assertRaisesRegex(ValueError, "Username cannot be empty."):
            self.user_service.add_user("", "password123")
        self.mock_user_repo.add.assert_not_called()

    def test_add_user_empty_password(self):
        """Test adding a user with an empty password raises ValueError."""
        self.mock_user_repo.get_by_username.return_value = None
        with self.assertRaisesRegex(ValueError, "Password cannot be empty."):
            self.user_service.add_user("testuser", "")
        self.mock_user_repo.add.assert_not_called()

    def test_authenticate_user_success(self):
        """Test successful user authentication."""
        username = "authuser"
        password = "correctpassword"
        hashed_password = self._hash_password(password)
        
        mock_user = User(id=5, username=username, password_hash=hashed_password, is_active=True)
        self.mock_user_repo.get_by_username.return_value = mock_user

        authenticated_user = self.user_service.authenticate_user(username, password)

        self.mock_user_repo.get_by_username.assert_called_once_with(username)
        self.assertIsNotNone(authenticated_user)
        self.assertEqual(authenticated_user.id, 5)
        self.assertEqual(authenticated_user.username, username)

    def test_authenticate_user_incorrect_password(self):
        """Test authentication failure due to incorrect password."""
        username = "authuser"
        correct_password = "correctpassword"
        incorrect_password = "wrongpassword"
        hashed_password = self._hash_password(correct_password)
        
        mock_user = User(id=5, username=username, password_hash=hashed_password, is_active=True)
        self.mock_user_repo.get_by_username.return_value = mock_user

        authenticated_user = self.user_service.authenticate_user(username, incorrect_password)

        self.mock_user_repo.get_by_username.assert_called_once_with(username)
        self.assertIsNone(authenticated_user)

    def test_authenticate_user_not_found(self):
        """Test authentication failure due to user not found."""
        username = "nosuchuser"
        password = "password123"
        
        self.mock_user_repo.get_by_username.return_value = None

        authenticated_user = self.user_service.authenticate_user(username, password)

        self.mock_user_repo.get_by_username.assert_called_once_with(username)
        self.assertIsNone(authenticated_user)

    def test_authenticate_user_inactive(self):
        """Test authentication failure due to inactive user."""
        username = "inactiveuser"
        password = "password123"
        hashed_password = self._hash_password(password)
        
        mock_user = User(id=6, username=username, password_hash=hashed_password, is_active=False)
        self.mock_user_repo.get_by_username.return_value = mock_user

        authenticated_user = self.user_service.authenticate_user(username, password)

        self.mock_user_repo.get_by_username.assert_called_once_with(username)
        self.assertIsNone(authenticated_user)

    def test_authenticate_user_empty_credentials(self):
        """Test authentication failure with empty username or password."""
        self.assertIsNone(self.user_service.authenticate_user("", "password"))
        self.assertIsNone(self.user_service.authenticate_user("user", ""))
        self.assertIsNone(self.user_service.authenticate_user("", ""))
        self.mock_user_repo.get_by_username.assert_not_called()

    def test_get_user_by_id(self):
        """Test getting user by ID delegates to repository."""
        user_id = 10
        mock_user = User(id=user_id, username="test", password_hash="hash")
        self.mock_user_repo.get_by_id.return_value = mock_user

        user = self.user_service.get_user(user_id)

        self.mock_user_repo.get_by_id.assert_called_once_with(user_id)
        self.assertEqual(user, mock_user)

    def test_get_user_by_username(self):
        """Test getting user by username delegates to repository."""
        username = "testuser"
        mock_user = User(id=11, username=username, password_hash="hash")
        self.mock_user_repo.get_by_username.return_value = mock_user

        user = self.user_service.get_user_by_username(username)

        self.mock_user_repo.get_by_username.assert_called_once_with(username)
        self.assertEqual(user, mock_user)

if __name__ == '__main__':
    unittest.main()
