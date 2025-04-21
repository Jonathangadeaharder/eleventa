import pytest
import sys
from PySide6.QtWidgets import (
    QMessageBox, QDialog, QFileDialog, QInputDialog, 
    QColorDialog, QFontDialog, QDialogButtonBox
)
from PySide6.QtCore import QTimer, QObject, QEventLoop, QCoreApplication

# Store original implementations to restore if needed
_orig_methods = {}

# Re-enable global patching (disabling it didn't solve the core crash)
@pytest.fixture(scope="session", autouse=True) 
def patch_qt_dialogs():
    """
    Globally patch all Qt dialog classes to prevent them from blocking during tests.
    This ensures tests don't hang waiting for user interaction.
    """
    print("\n=== Patching all Qt dialogs to prevent test hanging ===")
    
    # Store original methods
    _orig_methods['QMessageBox.exec'] = QMessageBox.exec
    _orig_methods['QDialog.exec'] = QDialog.exec
    
    # Patch QDialog.exec - fundamental base class for all dialog windows
    def dialog_exec_patch(self, *args, **kwargs):
        print(f"Non-blocking exec called for {self.__class__.__name__}")
        return QDialog.Accepted  # Return accepted (1) by default
    
    # Patch QMessageBox static methods
    QMessageBox.information = lambda *args, **kwargs: QMessageBox.Ok
    QMessageBox.warning = lambda *args, **kwargs: QMessageBox.Ok
    QMessageBox.critical = lambda *args, **kwargs: QMessageBox.Ok
    QMessageBox.question = lambda *args, **kwargs: QMessageBox.Yes
    
    # Apply patches
    QMessageBox.exec = lambda *args, **kwargs: QMessageBox.Ok
    QDialog.exec = dialog_exec_patch
    
    # File dialog patches
    QFileDialog.getOpenFileName = lambda *args, **kwargs: ("test_file.txt", "")
    QFileDialog.getSaveFileName = lambda *args, **kwargs: ("test_file.txt", "")
    QFileDialog.getExistingDirectory = lambda *args, **kwargs: "/test/directory"
    
    print("=== Qt dialog patching complete ===")
    
    yield
    
    # No need to restore original methods at the end of test session

@pytest.fixture(autouse=True)
def ensure_no_hanging_tests(request):
    """Set a timeout for each test to prevent hanging indefinitely."""
    marker = request.node.get_closest_marker("timeout")
    if not marker:
        request.node.add_marker(pytest.mark.timeout(10))
