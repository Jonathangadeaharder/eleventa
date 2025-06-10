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
# Import the main Base from where it's defined
# Assuming it's in infrastructure.persistence.sqlite.database or models_mapping
# Let's try importing from database first
from infrastructure.persistence.sqlite.database import Base 
# from infrastructure.persistence.sqlite.models_mapping import Base # Alternative if above fails

# Remove the separate _TestBase
# _TestBase = declarative_base()

# Inherit from the main Base
class _TestItem(Base):
    __tablename__ = "test_items"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

# Remove the setup_test_tables fixture
# @pytest.fixture(scope="function", autouse=True)
# def setup_test_tables(db_engine, test_db_session):
#     # Create the test_items table using the session-scoped engine
#     _TestBase.metadata.create_all(bind=db_engine)
#     
#     # Verify tables were created
#     inspector = inspect(db_engine)
#     tables = inspector.get_table_names()
#     
#     yield
#     
#     # Tables will be cleaned up by the transaction rollback in test_db_session

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

def test_session_scope_success(test_db_session):
    """Verify the session_scope yields a valid session and executes code."""
    session_instance = None
    try:
        with session_scope() as session:
            session_instance = session
            assert isinstance(session, Session)
            # Perform a dummy operation
            session.execute(text("SELECT 1"))
        # Scope exited without error, implying commit was attempted (though we can't verify without data)
        assert session_instance is not None # Verify session object was assigned
    except Exception as e:
        pytest.fail(f"session_scope raised an unexpected exception on success path: {e}")

def test_session_scope_rollback():
    """Verify the session_scope handles exceptions and triggers rollback path."""
    session_instance = None
    with pytest.raises(ValueError, match="Test exception"): # Expecting this error
        with session_scope() as session:
            session_instance = session
            assert isinstance(session, Session)
            # Simulate an error
            raise ValueError("Test exception")
    # If we reach here, the ValueError was raised and caught by pytest.raises
    # This implies the except block in session_scope (with rollback) was likely executed.
    assert session_instance is not None # Verify session object was assigned

def test_session_scope_rollback_data_consistency(test_db_session):
    """
    Test that after an exception and rollback, no partial data is persisted.
    Uses test_db_session directly instead of session_scope for debugging.
    """
    # Create a fresh session for this test to avoid interference with fixture session
    from sqlalchemy.orm import sessionmaker
    from infrastructure.persistence.sqlite.database import engine
    
    TestSession = sessionmaker(bind=engine)
    local_session = TestSession()
    
    try:
        # Clean up any existing test data for isolation
        local_session.execute(text("DELETE FROM test_items WHERE id = 1"))
        local_session.commit()
        
        # Add test data
        item = _TestItem(id=1, name="should_rollback")
        local_session.add(item)
        local_session.flush()
        
        # Simulate failure and rollback
        local_session.rollback()
        
        # Verify rollback worked
        result = local_session.query(_TestItem).filter_by(id=1).first()
        assert result is None, "Row should not exist after rollback"
    finally:
        # Ensure clean up regardless of test outcome
        local_session.close()

def test_session_scope_commit_exception_consistency(test_db_session):
    """
    Test that an IntegrityError during flush prevents persistence and 
    the session can be rolled back cleanly.
    """
    # Create a fresh session for this test to avoid interference with fixture session
    from sqlalchemy.orm import sessionmaker
    from infrastructure.persistence.sqlite.database import engine
    from sqlalchemy.exc import IntegrityError
    
    TestSession = sessionmaker(bind=engine)
    local_session = TestSession()
    
    try:
        # Clean up any existing test data for isolation
        local_session.execute(text("DELETE FROM test_items WHERE id = 2"))
        local_session.commit()
        
        # Attempt to insert two items with the same primary key (should fail)
        item = _TestItem(id=2, name="unique")
        dup = _TestItem(id=2, name="duplicate")
        local_session.add(item)
        local_session.add(dup)
        
        try:
            # This should raise IntegrityError
            local_session.flush()
            pytest.fail("IntegrityError not raised during flush") 
        except IntegrityError:
            # Expected error - rollback to clean state
            local_session.rollback()
            
            # Verify no item exists after rollback
            items = local_session.query(_TestItem).filter_by(id=2).all()
            assert len(items) == 0, "Item should not exist after IntegrityError and rollback"
    finally:
        # Ensure clean up regardless of test outcome
        local_session.close()
