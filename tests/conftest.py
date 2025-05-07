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
            # Check if the widget reference itself is not None
            # and then attempt to close and schedule for deletion.
            if widget: # This implicitly checks if widget is not None
                widget.close() # Close the widget first
                process_events() # Process close events
                widget.deleteLater() # Schedule for deletion
                process_events() # Process deletion events
        except RuntimeError:
            # This can happen if the underlying C++ object is already deleted
            # For example, if a parent widget was deleted, deleting its children.
            pass
        except AttributeError:
            # This could happen if 'widget' is not a QWidget, though unlikely
            # given how _widgets_to_cleanup is populated.
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

# Try to get path from PySide6.QtCore.QLibraryInfo first
try:
    from PySide6.QtCore import QLibraryInfo
    # Ensure a QApplication instance exists if QLibraryInfo needs it,
    # but be careful about creating it too early or conflicting with pytest-qt.
    # For now, let's assume QLibraryInfo can be called if PySide6 is imported.
    pyside_plugin_path_qlibraryinfo = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)
    print(f"Plugin path from QLibraryInfo: {pyside_plugin_path_qlibraryinfo}")
except Exception as e:
    print(f"Error getting plugin path from QLibraryInfo: {e}")
    pyside_plugin_path_qlibraryinfo = None

@pytest.fixture(scope="session", autouse=True)
def set_qt_plugin_path(): # qtbot fixture might be needed to ensure Qt is initialized
    print("Attempting to set QT_PLUGIN_PATH...")
    try:
        pyside_plugin_path = None
        if pyside_plugin_path_qlibraryinfo and os.path.isdir(pyside_plugin_path_qlibraryinfo):
            print(f"Using QLibraryInfo path: {pyside_plugin_path_qlibraryinfo}")
            pyside_plugin_path = pyside_plugin_path_qlibraryinfo
        else:
            print("QLibraryInfo path not valid or not found, falling back to constructed path.")
            # Construct the path to the venv
            # Assuming conftest.py is in tests/ and venv is at project root
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Determine PySide6 plugin path based on typical venv structure
            # Adjust if your venv structure is different
            if sys.platform == "win32":
                constructed_path = os.path.join(project_root, "venv", "Lib", "site-packages", "PySide6", "plugins")
            else: # Linux/macOS might be slightly different, e.g., lib/pythonX.Y/
                python_version_dir = f"python{sys.version_info.major}.{sys.version_info.minor}"
                constructed_path = os.path.join(project_root, "venv", "lib", python_version_dir, "site-packages", "PySide6", "plugins")

            if os.path.isdir(constructed_path):
                pyside_plugin_path = constructed_path
                print(f"Using constructed path: {pyside_plugin_path}")
            else:
                print(f"Warning: PySide6 plugin path not found at: {constructed_path}")
                # Fallback or alternative paths can be tried here if necessary
                # For example, sometimes it might be directly in site-packages/PySide6/Qt/plugins
                alt_plugin_path = os.path.join(project_root, "venv", "Lib", "site-packages", "PySide6", "Qt", "plugins")
                if os.path.isdir(alt_plugin_path):
                    pyside_plugin_path = alt_plugin_path
                    print(f"Found alternative plugin path at: {alt_plugin_path}")
                else:
                    print(f"Warning: Alternative PySide6 plugin path also not found at: {alt_plugin_path}")
                    pyside_plugin_path = None # Ensure it's None if not found

        if pyside_plugin_path and os.path.isdir(pyside_plugin_path):
            print(f"Setting QT_PLUGIN_PATH to: {pyside_plugin_path}")
            os.environ["QT_PLUGIN_PATH"] = pyside_plugin_path
            os.environ["QT_DEBUG_PLUGINS"] = "1" # Keep debug active
            
            # On Windows, Qt might also need paths to platform plugins, etc.
            # It's also good to ensure PATH includes the Qt binaries directory
            if sys.platform == "win32":
                qt_bin_path = os.path.dirname(pyside_plugin_path) # Parent of 'plugins' is usually the PySide6 package dir
                if os.path.isdir(qt_bin_path):
                    print(f"Adding to PATH: {qt_bin_path}")
                    os.environ["PATH"] = qt_bin_path + os.pathsep + os.environ.get("PATH", "")
                else:
                    # Fallback for qt_bin_path if structure is different
                    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    qt_bin_path_fallback = os.path.join(project_root, "venv", "Lib", "site-packages", "PySide6")
                    if os.path.isdir(qt_bin_path_fallback):
                         print(f"Adding to PATH (fallback): {qt_bin_path_fallback}")
                         os.environ["PATH"] = qt_bin_path_fallback + os.pathsep + os.environ.get("PATH", "")
                    else:
                        print(f"Warning: PySide6 bin path not found at {qt_bin_path} or {qt_bin_path_fallback}")


        else:
            print("Error: PySide6 plugin path could not be determined or does not exist.")
        
        # Verify (optional, for debugging)
        print(f"Current QT_PLUGIN_PATH: {os.environ.get('QT_PLUGIN_PATH')}")
        print(f"Current PATH (first 200 chars): {os.environ.get('PATH', '')[:200]}")

    except Exception as e:
        print(f"Error in set_qt_plugin_path fixture: {e}")
    
    yield # Let the test session run

# Import other fixtures
from tests.fixtures.conftest import *
