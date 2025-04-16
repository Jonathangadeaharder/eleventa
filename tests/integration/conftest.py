"""
Pytest configuration file for integration tests.

This file contains fixtures specifically for integration tests,
including authenticated users and mock services.
"""
import pytest
from unittest.mock import MagicMock
import sys
import os

# Add project root to path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from infrastructure.persistence.sqlite.repositories import SqliteUserRepository
from core.services.user_service import UserService
from core.models.user import User


@pytest.fixture
def test_user():
    """
    Create a simple test user without hitting the database.
    
    This is useful for tests that just need a user object but don't need
    to verify database authentication logic.
    """
    return User(
        id=999,
        username="testuser",
        password_hash="$2b$12$test_hash_for_testing_only",
        is_admin=True
    )


@pytest.fixture
def authenticated_user(clean_db):
    """
    Provide a real authenticated user from the test database.
    
    Creates a test user if it doesn't exist, or retrieves an existing one.
    """
    session = clean_db
    user_repo = SqliteUserRepository(session)
    user_service = UserService(user_repo)
    
    # Try to get the test user
    test_user = user_service.get_by_username("testuser")
    if not test_user:
        # Create a new test user if one doesn't exist
        test_user = user_service.add_user("testuser", "password123")
    
    # Make sure the user is committed to the database
    session.commit()
    return test_user


@pytest.fixture
def mock_services():
    """
    Provide mock services for testing.
    
    This avoids hitting the database completely for pure unit tests.
    """
    services = {
        'product_service': MagicMock(),
        'inventory_service': MagicMock(),
        'sale_service': MagicMock(),
        'customer_service': MagicMock(),
        'purchase_service': MagicMock(),
        'invoicing_service': MagicMock(),
        'corte_service': MagicMock(),
        'reporting_service': MagicMock(),
        'user_service': MagicMock()
    }
    
    # Setup the user service mock to return a test user
    test_user = User(id=1, username="mockuser", password_hash="mock_hash", is_admin=True)
    services['user_service'].authenticate.return_value = test_user
    services['user_service'].get_by_username.return_value = test_user
    
    return services 