from PySide6.QtWidgets import QMessageBox, QWidget, QPushButton, QLineEdit, QLabel, QComboBox
from PySide6.QtGui import QFont, QPalette, QColor

def show_error_message(parent, title, message):
    """Displays a warning message box."""
    QMessageBox.warning(parent, title, message)

def show_info_message(parent, title, message):
    """Displays an information message box."""
    QMessageBox.information(parent, title, message)

def ask_confirmation(parent, title, message):
    """Asks for confirmation (Yes/No) and returns True if Yes."""
    reply = QMessageBox.question(parent, title, message,
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                 QMessageBox.StandardButton.No) # Default to No
    return reply == QMessageBox.StandardButton.Yes 

# --- UI Style Utilities ---

def apply_standard_form_style(widget: QWidget):
    """Apply consistent form spacing and margins"""
    if hasattr(widget, 'layout') and widget.layout():
        widget.layout().setContentsMargins(10, 10, 10, 10)
        widget.layout().setSpacing(10)

def style_primary_button(button: QPushButton):
    """Style a button as a primary action button"""
    button.setMinimumHeight(32)
    button.setStyleSheet("""
        QPushButton {
            background-color: #2c6ba5;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #3880c4;
        }
        QPushButton:pressed {
            background-color: #1c5080;
        }
        QPushButton:disabled {
            background-color: #9eb8d0;
        }
    """)

def style_secondary_button(button: QPushButton):
    """Style a button as a secondary action button"""
    button.setMinimumHeight(30)
    button.setStyleSheet("""
        QPushButton {
            background-color: #f0f0f0;
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 6px 12px;
        }
        QPushButton:hover {
            background-color: #e0e0e0;
        }
        QPushButton:pressed {
            background-color: #d0d0d0;
        }
    """)

def style_text_input(input_widget: QLineEdit):
    """Apply consistent styling to text inputs"""
    input_widget.setMinimumHeight(28)
    input_widget.setStyleSheet("""
        QLineEdit {
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 4px 8px;
            background-color: white;
        }
        QLineEdit:focus {
            border: 1px solid #2c6ba5;
        }
    """)

def style_dropdown(combo: QComboBox):
    """Apply consistent styling to dropdown boxes"""
    combo.setMinimumHeight(28)
    combo.setStyleSheet("""
        QComboBox {
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 4px 8px;
            background-color: white;
        }
        QComboBox:focus {
            border: 1px solid #2c6ba5;
        }
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: center right;
            width: 20px;
            border-left: none;
        }
    """)

def style_heading_label(label: QLabel):
    """Style a label as a section heading"""
    font = label.font()
    font.setPointSize(12)
    font.setBold(True)
    label.setFont(font)
    label.setStyleSheet("color: #2c6ba5; margin-top: 8px; margin-bottom: 4px;")

def style_total_label(label: QLabel):
    """Style a label displaying a monetary total"""
    font = label.font()
    font.setPointSize(14)
    font.setBold(True)
    label.setFont(font)
    label.setStyleSheet("color: #2c6ba5;") 