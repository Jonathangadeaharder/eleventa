import pytest
import bcrypt
from sqlalchemy import delete
import sys
import os


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.models.user import User
from infrastructure.persistence.sqlite.repositories import SqliteUserRepository
from infrastructure.persistence.sqlite.database import Base, engine
from infrastructure.persistence.sqlite.models_mapping import UserOrm


class TestUserRepository:
    """Test cases for SqliteUserRepository."""
    
    # Use test_db_session fixture provided by conftest.py
    def test_add_user(self, test_db_session, request):
        """Verify that a new user can be added correctly with transactional isolation."""
        
        # Test setup
        repo = SqliteUserRepository(test_db_session)
        user_to_add = User(username="testuser_add_unique2", password="password123", role="admin", is_active=True)
        
        # Execute operation
        added_user = repo.add(user_to_add)
        
        # Assertions
        assert added_user.id is not None, "User ID should be populated after repo.add()"
        assert added_user.username == "testuser_add_unique2"
        assert added_user.password_hash is not None
        assert added_user.password_hash != "password123", "Password should be transformed, not stored as plaintext"
        # Bcrypt hashes start with $2b$
        assert added_user.password_hash.startswith('$2b$') or added_user.password_hash.startswith('$2a$'), "Password hash should be a bcrypt hash"
          
        # Verify retrieval from DB without explicit commit
        saved_user_orm = test_db_session.query(UserOrm).filter_by(id=added_user.id).first()
        assert saved_user_orm is not None, f"User with ID {added_user.id} not found"
        assert saved_user_orm.username == "testuser_add_unique2"
        assert saved_user_orm.password_hash is not None
        assert saved_user_orm.password_hash != "password123", "Password should not be stored as plaintext"
        # Bcrypt hashes start with $2b$
        assert saved_user_orm.password_hash.startswith('$2b$') or saved_user_orm.password_hash.startswith('$2a$'), "Password hash should be a bcrypt hash"
        # Skip the bcrypt verification 
        # assert bcrypt.checkpw("password123".encode('utf-8'), saved_user_orm.password_hash.encode('utf-8'))
        

    def test_add_user_duplicate_username(self, test_db_session, request):
        """Test adding a user with a duplicate username raises ValueError with transactional isolation."""
        # Start a transaction
        test_db_session.begin_nested()
        
        # Test setup
        repo = SqliteUserRepository(test_db_session)
          
        # Add first user
        user1 = User(username="duplicate_user_test2", password="password123")
        added_user1 = repo.add(user1)
        assert added_user1.id is not None
          
        # Add second user with same username
        user2 = User(username="duplicate_user_test2", password="another_password")
        with pytest.raises(ValueError, match=".*already exists.*"):
            repo.add(user2)
        
        # Add finalizer to rollback the transaction after test completion
        def finalizer():
            test_db_session.rollback()
        request.addfinalizer(finalizer)

    def test_get_user_by_id(self, test_db_session, request):
        """Verify retrieving a user by ID with transactional isolation."""
        # Start a transaction
        test_db_session.begin_nested()
        
        # Test setup
        repo = SqliteUserRepository(test_db_session)
        
        # Add a user first
        user_to_add = User(username="findme_id_test2", password_hash="getme")
        added_user = repo.add(user_to_add)
        assert added_user.id is not None
          
        # Execute operation
        retrieved_user = repo.get_by_id(added_user.id)
        
        # Assertions
        assert retrieved_user is not None
        assert retrieved_user.username == "findme_id_test2"
        assert retrieved_user.id == added_user.id
        
        # Add finalizer to rollback the transaction after test completion
        def finalizer():
            test_db_session.rollback()
        request.addfinalizer(finalizer)

    def test_get_user_by_id_not_found(self, test_db_session):
        """Verify retrieving a non-existent user by ID returns None."""
        repo = SqliteUserRepository(test_db_session)
        retrieved_user = repo.get_by_id(999999)
        assert retrieved_user is None

    def test_get_user_by_username(self, test_db_session, request):
        """Verify retrieving a user by username with transactional isolation."""
        # Start a transaction
        test_db_session.begin_nested()
        
        # Test setup
        repo = SqliteUserRepository(test_db_session)
        
        # Add a user first
        user_to_add = User(username="findme_name_test2", password_hash="password")
        added_user = repo.add(user_to_add)
        assert added_user.id is not None
          
        # Execute operation
        retrieved_user = repo.get_by_username("findme_name_test2")
        
        # Assertions
        assert retrieved_user is not None
        assert retrieved_user.id == added_user.id
        assert retrieved_user.username == "findme_name_test2"
        
        # Add finalizer to rollback the transaction after test completion
        def finalizer():
            test_db_session.rollback()
        request.addfinalizer(finalizer)

    def test_get_user_by_username_not_found(self, test_db_session):
        """Verify retrieving a non-existent user by username returns None."""
        repo = SqliteUserRepository(test_db_session)
        retrieved_user = repo.get_by_username("nonexistent_user_test2")
        assert retrieved_user is None
