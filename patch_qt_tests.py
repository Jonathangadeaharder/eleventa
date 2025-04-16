"""
This script patches PySide6 dialog classes to prevent them from blocking during tests.
Import this module before running Qt-based tests.

Usage:
    import patch_qt_tests  # at the start of your test file
"""

from PySide6.QtWidgets import QMessageBox, QDialog, QFileDialog
import sys
import os

# Store original implementations
_orig_dialog_exec = QDialog.exec
_orig_msgbox_exec = QMessageBox.exec
_orig_msgbox_info = QMessageBox.information
_orig_msgbox_warn = QMessageBox.warning
_orig_msgbox_crit = QMessageBox.critical
_orig_msgbox_quest = QMessageBox.question

# Print patching information
print("=== Patching Qt dialogs to prevent blocking in tests ===")

# Replace QDialog.exec with non-blocking version
def _patched_dialog_exec(self, *args, **kwargs):
    print(f"[PATCH] Non-blocking exec called for {self.__class__.__name__}")
    return 1  # QDialog.Accepted

# Replace QMessageBox methods with non-blocking versions
def _patched_msgbox_info(*args, **kwargs):
    print("[PATCH] Non-blocking QMessageBox.information called")
    return QMessageBox.Ok

def _patched_msgbox_warn(*args, **kwargs):
    print("[PATCH] Non-blocking QMessageBox.warning called")
    return QMessageBox.Ok

def _patched_msgbox_crit(*args, **kwargs):
    print("[PATCH] Non-blocking QMessageBox.critical called")
    return QMessageBox.Ok

def _patched_msgbox_quest(*args, **kwargs):
    print("[PATCH] Non-blocking QMessageBox.question called")
    return QMessageBox.Yes

def _patched_msgbox_exec(*args, **kwargs):
    print("[PATCH] Non-blocking QMessageBox.exec called")
    return QMessageBox.Ok

# Apply patches
QDialog.exec = _patched_dialog_exec
QMessageBox.exec = _patched_msgbox_exec
QMessageBox.information = _patched_msgbox_info
QMessageBox.warning = _patched_msgbox_warn
QMessageBox.critical = _patched_msgbox_crit
QMessageBox.question = _patched_msgbox_quest

# File dialog patches
QFileDialog.getOpenFileName = lambda *args, **kwargs: ("test_file.txt", "")
QFileDialog.getSaveFileName = lambda *args, **kwargs: ("test_file.txt", "")
QFileDialog.getExistingDirectory = lambda *args, **kwargs: "/test/directory"

print("=== Qt dialog patching complete ===")

# Utility function to restore original behavior if needed
def restore_original_dialogs():
    """Restore original Qt dialog behavior"""
    QDialog.exec = _orig_dialog_exec
    QMessageBox.exec = _orig_msgbox_exec
    QMessageBox.information = _orig_msgbox_info
    QMessageBox.warning = _orig_msgbox_warn
    QMessageBox.critical = _orig_msgbox_crit
    QMessageBox.question = _orig_msgbox_quest
    print("=== Original Qt dialog behavior restored ===")

# Automatically apply this patch in pytest
if 'pytest' in sys.modules:
    # Make it work with pytest's assertion rewriting
    pytest = sys.modules['pytest']
    
    # Register a cleanup function to restore original behavior
    if hasattr(pytest, 'hookimpl'):
        @pytest.hookimpl(trylast=True)
        def pytest_sessionfinish(session, exitstatus):
            restore_original_dialogs() 