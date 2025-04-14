import pytest
import os
from sqlalchemy import text, Column, Integer, String, inspect
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy.exc import OperationalError, ResourceClosedError, InvalidRequestError
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker

# Adjust path to import from the project root
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from infrastructure.persistence.sqlite.database import engine, SessionLocal, DATABASE_URL
from infrastructure.persistence.utils import session_scope

# Create a separate Base for test models to avoid conflicts with the main Base
_TestBase = declarative_base()

# Use a specific test database file to avoid conflicts with other tests
TEST_DATABASE_URL = "sqlite:///:memory:"  # Use in-memory database for tests

# Create a test engine and session
test_engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

class _TestItem(_TestBase):
    __tablename__ = "test_items"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

# Ensure test tables are created before tests run
@pytest.fixture(scope="function", autouse=True)
def setup_test_tables():
    # Create the test_items table
    _TestBase.metadata.create_all(bind=test_engine)
    
    # Verify tables were created
    inspector = inspect(test_engine)
    tables = inspector.get_table_names()
    print(f"Tables in database after setup: {tables}")
    
    # Register the test session factory
    from infrastructure.persistence.utils import session_scope_provider
    original_factory = session_scope_provider.get_session_factory()
    session_scope_provider.set_session_factory(TestSessionLocal)
    
    # Yield control to the tests
    yield
    
    # Restore the original session factory
    session_scope_provider.set_session_factory(original_factory)
    
    # Clean up after tests
    _TestBase.metadata.drop_all(bind=test_engine)
    print("Test tables dropped")

# Remove database file check since we're using in-memory database
# if os.path.exists(DATABASE_URL.split("///")[1]):
#     try:
#         os.remove(DATABASE_URL.split("///")[1])
#     except OSError as e:
#         print(f"Warning: Could not remove test database file before test: {e}")

def test_database_connection():
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

def test_session_scope_success():
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

def test_session_scope_rollback_data_consistency():
    """
    Test that after an exception and rollback, no partial data is persisted.
    """
    # Insert a row, then raise an exception to trigger rollback
    with pytest.raises(RuntimeError, match="Simulated failure"):
        with session_scope() as session:
            item = _TestItem(id=1, name="should_rollback")
            session.add(item)
            raise RuntimeError("Simulated failure")

    # Verify that the row was not persisted
    with session_scope() as session:
        result = session.query(_TestItem).filter_by(id=1).first()
        assert result is None, "Row should not exist after rollback"

def test_session_scope_commit_exception_consistency():
    """
    Test that a commit failure (e.g., due to unique constraint) triggers rollback and leaves DB consistent.
    """
    # Insert a valid row
    with session_scope() as session:
        item = _TestItem(id=2, name="unique")
        session.add(item)

    # Attempt to insert a duplicate primary key to force IntegrityError
    from sqlalchemy.exc import IntegrityError
    with pytest.raises(IntegrityError):
        with session_scope() as session:
            dup = _TestItem(id=2, name="duplicate")
            session.add(dup)
            # Commit will be attempted on context exit, should raise IntegrityError

    # Verify only the original row exists
    with session_scope() as session:
        items = session.query(_TestItem).filter_by(id=2).all()
        assert len(items) == 1
        assert items[0].name == "unique"

# Clean up fixture is not needed since we're using in-memory database
# @pytest.fixture(scope="session", autouse=True)
# def cleanup_db_file():
#     yield
#     # Teardown: remove the database file
#     db_path = DATABASE_URL.split("///")[1]
#     if os.path.exists(db_path):
#         try:
#             # Ensure all connections are closed before removing
#             engine.dispose()
#             os.remove(db_path)
#             print(f"\nCleaned up test database file: {db_path}")
#         except OSError as e:
#             print(f"Warning: Could not remove test database file after test: {e}")
