"""
Global pytest configuration.

This file contains shared fixtures and configuration settings for pytest.
"""

import sys
import pytest
sys.path.append(".")

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from infrastructure.persistence.sqlite.database import SessionLocal
import sqlalchemy.pool
from unittest.mock import MagicMock
import importlib.util
import os
from PySide6.QtWidgets import QApplication
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import necessary modules from the project
from infrastructure.persistence.sqlite.database import Base
from infrastructure.persistence.sqlite.models_mapping import ensure_all_models_mapped

# Force use of in-memory database for tests
TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def test_engine():
    """Create an engine connected to an in-memory database for testing."""
    # Use in-memory SQLite database to avoid touching any real database
    if "TEST_DB_URL" in os.environ:
        # Allow override for CI environments
        db_url = os.environ["TEST_DB_URL"]
        if "test" not in db_url.lower() and "memory" not in db_url.lower():
            pytest.skip(f"Refusing to connect to non-test database: {db_url}")
    else:
        db_url = TEST_DB_URL
        
    engine = create_engine(db_url, echo=False)
    
    # Ensure models are mapped
    ensure_all_models_mapped()
    
    # Create all tables in the engine
    Base.metadata.create_all(engine)
    
    # Return engine for use in tests
    yield engine
    
    # Cleanup after all tests
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def test_db_session(test_engine):
    """Create a new database session for a test."""
    # Connect to the database and create a session
    connection = test_engine.connect()
    transaction = connection.begin()
    
    # Create a session bound to the connection
    Session = sessionmaker(bind=connection)
    session = Session()
    
    # Return session for the test to use
    yield session
    
    # Cleanup after test
    session.close()
    
    # Check if transaction is still active before attempting to roll it back
    # This is the correct way to check transaction state in SQLAlchemy
    if transaction.is_active:
        transaction.rollback()
    
    connection.close()

@pytest.fixture(scope="session", autouse=True)
def verify_test_database():
    """Verify that we are not connecting to a production database."""
    # Check if we're using a test database
    db_url = os.environ.get("DATABASE_URL", TEST_DB_URL)
    if "test" not in db_url.lower() and "memory" not in db_url.lower():
        pytest.skip(f"Tests must use a test database. Current DB URL: {db_url}")
    return True

def pytest_configure(config):
    """Register custom pytest marks."""
    config.addinivalue_line("markers", "smoke: mark a test as a smoke test for critical workflows")
    config.addinivalue_line("markers", "unit: mark a test as a unit test")
    config.addinivalue_line("markers", "integration: mark a test as an integration test")
    config.addinivalue_line("markers", "ui: mark a test as a ui test")

# Common fixtures that can be used across all tests

import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_print_manager():
    mock_pm = MagicMock()
    mock_pm.print.return_value = True
    return mock_pm
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
