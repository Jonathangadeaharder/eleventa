import os
import sys
import pytest
import platform

# Ensure the project root directory is in the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added project root to sys.path: {project_root}")

# Set up Qt environment before any imports of PySide6
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(sys.prefix, 'Lib', 'site-packages', 'PySide6', 'plugins', 'platforms')
os.environ['QT_LOGGING_RULES'] = '*.debug=false;qt.qpa.*=false'
os.environ['QT_FORCE_STDERR_LOGGING'] = '1'
os.environ['QT_QPA_ENABLE_HIGHDPI_SCALING'] = '0'
os.environ['QT_SCALE_FACTOR'] = '1'
os.environ["PYTEST_QT_API"] = "pyside6"

# Import PySide6 only when needed
# Avoided here to prevent import errors during collection

from pathlib import Path

# Load UI resources only when UI tests are run
def import_ui_resources():
    try:
        # Make sure the ui directory is properly added to Python's path
        ui_path = os.path.join(project_root, "ui")
        resources_path = os.path.join(ui_path, "resources")
        
        if os.path.exists(resources_path) and ui_path not in sys.path:
            sys.path.insert(0, ui_path)
            print(f"Added ui path to sys.path: {ui_path}")
        
        # Try to import the resources module
        import ui.resources
        import ui.resources.resources
        print("Successfully imported ui.resources.resources")
        return True
    except ImportError as e:
        print(f"Warning: Could not import Qt resources (ui.resources.resources): {e}")
        print(f"Current sys.path: {sys.path}")
        return False
    except Exception as e:
        print(f"Unexpected error importing resources: {e}")
        return False
    return False

@pytest.fixture(scope="session", autouse=True)
def initialize_sqlalchemy_session():
    """Initialize SQLAlchemy ORM models once per test session."""
    print("Initializing SQLAlchemy models for test session...")
    try:
        # Import models to ensure they are properly registered
        from infrastructure.persistence.sqlite.database import Base
        from infrastructure.persistence.sqlite.models_mapping import (
            UserOrm, DepartmentOrm, ProductOrm, InventoryMovementOrm, 
            SaleOrm, SaleItemOrm, CustomerOrm, CreditPaymentOrm,
            InvoiceOrm, CashDrawerEntryOrm, ensure_all_models_mapped
        )
        # Make sure all models are properly mapped
        ensure_all_models_mapped()
        print("SQLAlchemy initialization complete.")
    except ImportError as e:
        print(f"Error during SQLAlchemy initialization: {e}")
        pytest.fail(f"Failed to initialize SQLAlchemy: {e}", pytrace=False)
    except Exception as e:
        print(f"Unexpected error during SQLAlchemy initialization: {e}")
        pytest.fail(f"Unexpected error during SQLAlchemy initialization: {e}", pytrace=False)

def pytest_configure(config):
    """Set up the test environment"""
    # Add markers
    config.addinivalue_line("markers", "unit: mark a test as a unit test")
    config.addinivalue_line("markers", "integration: mark a test as an integration test")
    config.addinivalue_line("markers", "ui: mark a test as a UI test that requires Qt")
    config.addinivalue_line("markers", "alembic: marks tests that involve alembic migrations")
    config.addinivalue_line("markers", "smoke: marks smoke tests that verify basic functionality")
    
    # Register ui option as a marker instead (we can use -m ui instead of --ui)
    config.addinivalue_line("markers", "ui: run UI tests (may require specific environment)")

@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle UI tests properly.
    Marks tests in tests/ui with 'ui' and ensures resources are loaded if UI tests are collected.
    UI tests are run by default unless explicitly deselected (e.g., via -m "not ui" or -k)."""
    
    ui_tests_present_in_collection = False
    # Mark all tests in the UI directory with the 'ui' marker
    for item in items:
        if "tests/ui" in str(item.fspath):
            item.add_marker(pytest.mark.ui)
            ui_tests_present_in_collection = True
    
    # If UI tests are present in the collection, attempt to import Qt resources.
    # Pytest will handle actual execution/skipping based on command-line arguments like -k or -m.
    if ui_tests_present_in_collection:
        print("UI tests were found in the collection. Attempting to import UI resources from conftest.py.")
        resources_loaded = import_ui_resources()
        if resources_loaded:
            try:
                # This import is mainly a check that PySide6 is installed and basically works.
                # The actual QApplication instance is managed by pytest-qt or the qapp fixture.
                from PySide6.QtWidgets import QApplication
                print("PySide6.QtWidgets.QApplication import check successful in conftest.py.")
            except ImportError:
                print("WARNING (from conftest.py): Could not import PySide6.QtWidgets.QApplication. UI tests might fail or be skipped by pytest-qt if Qt is not properly set up.")
        else:
            print("WARNING (from conftest.py): UI resources failed to load. UI tests might have issues.")

    # No more automatic skipping of UI tests here.
    # `pytest` will run them by default if they are collected and not deselected by other filters.
    # Users can use `pytest -m "not ui"` or `pytest -k "some_name"` to skip/select tests.

@pytest.fixture(scope="session")
def qapp_args():
    """Provide custom args for QApplication for pytest-qt to use offscreen platform."""
    return ["-platform", "offscreen"]

@pytest.fixture(scope="session")
def qapp(qapp_args):
    """Session-scoped QApplication instance."""
    # Import only when the fixture is actually used
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(qapp_args or [])
    yield app
