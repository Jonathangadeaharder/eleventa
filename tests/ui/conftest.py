import importlib.util
import os
import sys
import pytest
from unittest.mock import MagicMock

# Fix the path to properly include the project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
sys.path.insert(0, project_root)

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

def pytest_configure(config):
    config.ui_test_dir = config.getoption("--ui-test-dir")
