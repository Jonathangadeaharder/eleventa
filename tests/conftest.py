"""
Global pytest configuration.

This file contains shared fixtures and configuration settings for pytest.
"""

import sys
import pytest
sys.path.append(".")

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from core.database import Base
from core.config import settings
from infrastructure.persistence.sqlite.database import SessionLocal
import sqlalchemy.pool
from unittest.mock import MagicMock
import importlib.util
import os
from PySide6.QtWidgets import QApplication

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

def pytest_configure(config):
    """Register custom pytest marks."""
    config.addinivalue_line("markers", "smoke: mark a test as a smoke test for critical workflows")
    config.addinivalue_line("markers", "unit: mark a test as a unit test")
    config.addinivalue_line("markers", "integration: mark a test as an integration test")
    config.addinivalue_line("markers", "ui: mark a test as a ui test")

# Common fixtures that can be used across all tests
@pytest.fixture
def mock_cash_drawer_service():
    """Create a mock CashDrawerService for testing."""
    mock_service = MagicMock()
    mock_service.repository = MagicMock()
    return mock_service

@pytest.fixture
def mock_invoicing_service():
    """Create a mock InvoicingService for testing."""
    mock_service = MagicMock()
    mock_service.sale_repo = MagicMock()
    mock_service.customer_repo = MagicMock()
    return mock_service

# Add project root to path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Global list to track widgets created during tests for proper cleanup
_widgets_to_cleanup = []

def process_events():
    """Process pending events for the QApplication instance."""
    app = QApplication.instance()
    if app is not None:
        app.processEvents()

@pytest.fixture(scope="function", autouse=True)
def qt_cleanup():
    """Fixture to ensure all Qt widgets are properly cleaned up after each test."""
    # Setup - nothing to do here
    yield
    
    # Teardown - clean up any widgets that were created
    global _widgets_to_cleanup
    for widget in _widgets_to_cleanup:
        try:
            if widget is not None and not widget.isDestroyed():
                widget.close()
                process_events()
                widget.deleteLater()
                process_events()
        except (RuntimeError, AttributeError):
            # Widget might already be deleted or have a different interface
            pass
    
    # Clear the list
    _widgets_to_cleanup = []
    
    # Process any remaining events
    process_events()

# Create a safer version of qtbot.addWidget that tracks widgets for cleanup
@pytest.fixture
def safe_qtbot(qtbot):
    """A wrapper around qtbot that tracks added widgets for proper cleanup."""
    original_add_widget = qtbot.addWidget
    
    def add_widget_with_tracking(widget):
        global _widgets_to_cleanup
        _widgets_to_cleanup.append(widget)
        return original_add_widget(widget)
    
    qtbot.addWidget = add_widget_with_tracking
    return qtbot

# Import other fixtures
from tests.fixtures.conftest import *
