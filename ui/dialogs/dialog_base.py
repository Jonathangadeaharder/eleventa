from PySide6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QFrame, QLabel
from PySide6.QtCore import Qt

from ui.utils import show_error_message

class DialogBase(QDialog):
    """Base class for all dialogs in the application to ensure consistent behavior and style."""
    
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setMinimumWidth(400)
        self.setSizeGripEnabled(True)
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(10)
        
        # Content area - to be filled by subclasses
        self.content_frame = QFrame()
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.content_frame)
        
        # Standard buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        self.main_layout.addWidget(self.button_box)
        
    def add_form_row(self, label_text, widget):
        """Add a row with label and widget to the content layout."""
        row_layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setMinimumWidth(120)
        row_layout.addWidget(label)
        row_layout.addWidget(widget, 1)  # 1 = stretch factor
        self.content_layout.addLayout(row_layout)
        return row_layout
    
    def validate_and_accept(self):
        """Validate input before accepting the dialog."""
        try:
            if self.validate():
                self.accept()
        except ValueError as e:
            show_error_message(self, "Error de validación", str(e))
    
    def validate(self):
        """
        Validate dialog input. Should be overridden by subclasses.
        
        Returns:
            bool: True if validation passes
            
        Raises:
            ValueError: If validation fails
        """
        return True  # Default implementation passes validation
        
    def get_ok_button(self):
        """Get the OK button from the button box."""
        return self.button_box.button(QDialogButtonBox.StandardButton.Ok)
    
    def get_cancel_button(self):
        """Get the Cancel button from the button box."""
        return self.button_box.button(QDialogButtonBox.StandardButton.Cancel)
    
    def set_button_text(self, button_type, text):
        """Set the text of a standard button."""
        button = self.button_box.button(button_type)
        if button:
            button.setText(text) 