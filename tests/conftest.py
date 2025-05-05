import sys
import pytest
sys.path.append(".")

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from core.database import Base
from core.config import settings
from infrastructure.persistence.sqlite.database import SessionLocal
import sqlalchemy.pool

# Configure test database URL
TEST_DATABASE_URL = settings.DATABASE_URL.replace("sqlite:///", "sqlite:///test_")

@pytest.fixture(scope="session")
def db_engine():
    """Provide a SQLAlchemy engine for the test session."""
    from infrastructure.persistence.sqlite.database import Base
    from infrastructure.persistence.sqlite.models_mapping import map_models
    
    # Create in-memory engine for testing
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=sqlalchemy.pool.StaticPool
    )
    
    # Ensure models are mapped
    map_models()
    
    # Register table creation event hooks to control order
    from infrastructure.persistence.sqlite.table_deps import register_table_creation_events
    register_table_creation_events(Base.metadata)
    
    # Create schema with tables in the correct order
    Base.metadata.create_all(bind=test_engine)
    
    yield test_engine
    
    # Cleanup after all tests
    test_engine.dispose()

@pytest.fixture(scope="function")
def test_db_session(db_engine):
    """Provide a SQLAlchemy session for each test with proper isolation."""
    # Create a connection to use for transaction
    connection = db_engine.connect()
    
    # Begin a non-ORM transaction
    transaction = connection.begin()
    
    # Create a session bound to this connection
    TestingSessionLocal = sessionmaker(
        bind=connection, 
        expire_on_commit=False,
        future=True
    )
    session = TestingSessionLocal()
    
    # Override the begin_nested method to use subtransactions
    original_begin_nested = session.begin_nested
    
    def begin_nested_with_subtransaction():
        """Create a savepoint with better handling for nested transactions."""
        return session.begin(nested=True)
    
    # Replace the method with our improved version
    session.begin_nested = begin_nested_with_subtransaction
    
    # Provide better commit handling for subtransactions
    original_commit = session.commit
    
    def commit_with_subtransaction_support():
        """Commit changes with better handling for nested transactions."""
        try:
            original_commit()
        except Exception as e:
            # If we're in a nested transaction, the commit is expected to fail
            # but shouldn't crash the test unless it's the main transaction
            if "This transaction is inactive" not in str(e):
                raise
    
    # Replace the commit method with our improved version
    session.commit = commit_with_subtransaction_support
    
    yield session
    
    # Clean up after the test
    session.close()
    transaction.rollback()  # Roll back the outer transaction
    connection.close()  # Close the connection
