import importlib.util
import os
import sys
import pytest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication

# Fix the path to properly include the project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
sys.path.insert(0, project_root)

# Remove 'ui' from sys.argv to prevent conditional skips
if 'ui' in sys.argv:
    sys.argv.remove('ui')

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

@pytest.fixture(scope="session")
def qt_module_loader():
    def _load_module(module_path):
        # Use absolute path from project root
        abs_path = os.path.join(project_root, module_path)
        spec = importlib.util.spec_from_file_location(
            os.path.basename(module_path), abs_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return _load_module

@pytest.fixture
def qt_widget_fixture(qt_module_loader):
    # Example fixture using dynamic import
    widget_module = qt_module_loader("ui/widgets/my_widget.py")
    return widget_module.MyWidget()

def pytest_addoption(parser):
    parser.addoption(
        "--ui-test-dir",
        action="store",
        default="ui",
        help="Directory containing UI modules to test"
    )
    parser.addoption(
        "--run-skipped-ui-tests",
        action="store_true",
        default=True,
        help="Run UI tests that would normally be skipped"
    )

def pytest_configure(config):
    config.ui_test_dir = config.getoption("--ui-test-dir")
    
    # If run-skipped-ui-tests is enabled, manipulate sys.argv to ensure 
    # conditional skips based on "ui" in sys.argv don't trigger
    if config.getoption("--run-skipped-ui-tests"):
        if 'ui' in sys.argv:
            sys.argv.remove('ui')

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
