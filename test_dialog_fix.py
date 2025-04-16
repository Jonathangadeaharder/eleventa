import sys
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog, QVBoxLayout, QPushButton
from PySide6.QtCore import Qt

# Convert TestDialog from a test class to a regular class to avoid pytest collection warning
class DialogForTesting(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Dialog")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # Add a button that will show a message box
        self.button = QPushButton("Show MessageBox")
        self.button.clicked.connect(self.show_message)
        self.layout.addWidget(self.button)
        
        # Add a button that will accept the dialog
        self.accept_button = QPushButton("Accept")
        self.accept_button.clicked.connect(self.accept)
        self.layout.addWidget(self.accept_button)
        
    def show_message(self):
        QMessageBox.information(self, "Test", "This should not block in tests")

# Patch QMessageBox for testing
def patch_message_box():
    print("Patching QMessageBox.exec")
    old_exec = QMessageBox.exec
    QMessageBox.exec = lambda *args, **kwargs: QMessageBox.Ok
    return old_exec

# Patch QDialog.exec
def patch_dialog_exec():
    print("Patching QDialog.exec")
    old_exec = QDialog.exec
    def patched_exec(self, *args, **kwargs):
        print(f"Dialog.exec called for {self.__class__.__name__}")
        return QDialog.Accepted
    QDialog.exec = patched_exec
    return old_exec

def main():
    # Set up application
    app = QApplication(sys.argv)
    
    # First test without patching
    print("\n--- Testing without patches ---")
    dialog = DialogForTesting()
    if len(sys.argv) > 1 and sys.argv[1] == '--no-patch':
        # This will block until user interaction
        print("Running without patches (will block)")
        result = dialog.exec()
        print(f"Dialog result: {result}")
    else:
        # Apply patches
        print("\n--- Testing with patches ---")
        old_msg_exec = patch_message_box()
        old_dialog_exec = patch_dialog_exec()
        
        # Now test with patching
        try:
            dialog = DialogForTesting()
            print("Executing dialog (should not block)")
            result = dialog.exec()
            print(f"Dialog result: {result}")
            
            # Try with a message box directly
            print("Showing message box (should not block)")
            result = QMessageBox.information(None, "Test", "This should not block")
            print(f"MessageBox result: {result}")
        finally:
            # Restore original methods
            QMessageBox.exec = old_msg_exec
            QDialog.exec = old_dialog_exec
    
    if len(sys.argv) > 1 and sys.argv[1] == '--app':
        # Run the event loop
        sys.exit(app.exec())

if __name__ == "__main__":
    main() 