"""
Script to run Qt tests with patched dialog classes to prevent hanging.
"""
import sys
import os
import subprocess
from PySide6.QtWidgets import QMessageBox, QDialog, QFileDialog, QApplication

def patch_qt_classes():
    """Patch Qt dialog classes to prevent them from blocking."""
    # Store original methods for reference
    orig_dialog_exec = QDialog.exec
    orig_msgbox_exec = QMessageBox.exec
    
    # Replace with non-blocking versions
    QDialog.exec = lambda *args, **kwargs: 1  # Return Accepted
    QMessageBox.exec = lambda *args, **kwargs: QMessageBox.Ok
    QMessageBox.information = lambda *args, **kwargs: QMessageBox.Ok
    QMessageBox.warning = lambda *args, **kwargs: QMessageBox.Ok
    QMessageBox.critical = lambda *args, **kwargs: QMessageBox.Ok
    QMessageBox.question = lambda *args, **kwargs: QMessageBox.Yes
    
    # File dialog patches
    QFileDialog.getOpenFileName = lambda *args, **kwargs: ("test_file.txt", "")
    QFileDialog.getSaveFileName = lambda *args, **kwargs: ("test_file.txt", "")
    QFileDialog.getExistingDirectory = lambda *args, **kwargs: "/test/directory"
    
    print("=== Qt dialogs patched to non-blocking versions ===")
    return True

def main():
    """Run pytest with appropriate environment variables."""
    # Initialize Qt application
    app = QApplication([])
    
    # Apply patches
    patch_qt_classes()
    
    # Get command line arguments for pytest
    pytest_args = sys.argv[1:] if len(sys.argv) > 1 else ["tests/ui/"]
    
    # Add timeout flag if not already present
    for arg in pytest_args:
        if "--timeout" in arg:
            break
    else:
        pytest_args.append("--timeout=10")
        
    # Construct full pytest command
    cmd = ["python", "-m", "pytest"] + pytest_args + ["-v"]
    print(f"Running command: {' '.join(cmd)}")
    
    # Run pytest in a separate process
    result = subprocess.run(cmd, capture_output=False)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main() 