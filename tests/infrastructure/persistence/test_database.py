import pytest
import os
from sqlalchemy import text, Column, Integer, String, inspect
from sqlalchemy.orm import Session, DeclarativeBase, sessionmaker
from sqlalchemy.exc import OperationalError, ResourceClosedError, InvalidRequestError

# Adjust path to import from the project root
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from infrastructure.persistence.utils import session_scope
from infrastructure.persistence.sqlite.database import Base

class _TestItem(Base):
    __tablename__ = "test_items"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

def test_database_connection(test_engine):
    """Verify that engine.connect() successfully establishes a connection."""
    try:
        connection = test_engine.connect()
        assert connection is not None
        # Optional: Execute a simple query
        result = connection.execute(text("SELECT 1"))
        assert result.scalar_one() == 1
        connection.close()
    except OperationalError as e:
        pytest.fail(f"Database connection failed: {e}")

def test_session_scope_success(clean_db):
    """Verify the session_scope yields a valid session and executes code."""
    session, _ = clean_db
    # The clean_db fixture patches the provider, so session_scope will now work correctly.
    try:
        with session_scope() as s:
            # The session from session_scope will be a new one from the factory,
            # not the same instance as `session` from clean_db.
            assert isinstance(s, Session)
            result = s.execute(text("SELECT 1")).scalar()
            assert result == 1
    except Exception as e:
        pytest.fail(f"session_scope raised an unexpected exception on success path: {e}")

def test_session_scope_rollback(clean_db):
    """Verify the session_scope handles exceptions and triggers rollback path."""
    session, _ = clean_db
    with pytest.raises(ValueError, match="Test exception"): # Expecting this error
        with session_scope() as s:
            assert isinstance(s, Session)
            # Simulate an error
            raise ValueError("Test exception")

def test_session_scope_rollback_data_consistency(clean_db):
    """
    Test that after an exception and rollback, no partial data is persisted.
    """
    session, _ = clean_db
    
    with pytest.raises(ValueError, match="Test exception"):
        with session_scope() as s:
            item = _TestItem(id=1, name="should_rollback")
            s.add(item)
            s.flush() # Make it pending in the transaction
            raise ValueError("Test exception")

    # Use a new session to verify the data is not there
    with session_scope() as s:
        result = s.query(_TestItem).filter_by(id=1).first()
        assert result is None, "Row should not exist after rollback"

def test_session_scope_commit_exception_consistency(clean_db):
    """
    Test that an IntegrityError during commit is properly handled by session_scope.
    """
    session, _ = clean_db
    
    # Add an item using the provided session to establish the constraint
    session.add(_TestItem(id=2, name="unique"))
    session.commit()
    
    # Now try to add a duplicate item within the same session_scope, which should fail
    # The session_scope wraps IntegrityError in ValueError, so we expect ValueError
    with pytest.raises(ValueError, match=r"Database commit error.*UNIQUE constraint failed"):
        with session_scope() as s:
            s.add(_TestItem(id=2, name="duplicate"))
            # The commit will fail here inside session_scope
    
    # The test demonstrates that session_scope properly handles commit exceptions
    # and wraps them in ValueError as expected. The actual data persistence
    # is managed by the transactional test fixture.
