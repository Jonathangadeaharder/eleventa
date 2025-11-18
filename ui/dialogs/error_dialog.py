from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QApplication,
    QHBoxLayout,
    QSpacerItem,
    QSizePolicy,
)
import traceback


class ErrorDialog(QDialog):
    def __init__(self, title: str, user_message: str, details: str = "", parent=None):
        super().__init__(parent)

        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        self.setModal(True)  # Make dialog modal
        # self.setMinimumHeight(300) # Auto-adjust height based on content

        layout = QVBoxLayout(self)

        # User-friendly message
        self.user_message_label = QLabel(user_message)
        self.user_message_label.setWordWrap(True)
        layout.addWidget(self.user_message_label)

        # Collapsible details section (initially hidden)
        self.details_button = QPushButton("Mostrar Detalles")
        self.details_button.setCheckable(True)
        self.details_button.setChecked(False)
        self.details_button.clicked.connect(self.toggle_details_visibility)
        self.details_text_edit = QTextEdit()
        self.details_text_edit.setPlainText(details)
        self.details_text_edit.setReadOnly(True)
        self.details_text_edit.setVisible(False)  # Initially hidden
        self.details_text_edit.setFontFamily("monospace")  # Good for tracebacks
        # Set a reasonable initial height for the details text edit, but allow expansion
        self.details_text_edit.setFixedHeight(150)

        # Only show details button and add widgets if there are details to show
        if details:
            layout.addWidget(self.details_button)
            layout.addWidget(self.details_text_edit)
        else:
            self.details_button.setVisible(False)

        # Advice/Next steps (placeholder)
        self.advice_label = QLabel(
            "Se recomienda guardar su trabajo y reiniciar la aplicación. Si el problema persiste, contacte a soporte."
        )
        self.advice_label.setWordWrap(True)
        layout.addWidget(self.advice_label)

        layout.addSpacerItem(
            QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

        # Buttons
        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch()
        self.ok_button = QPushButton("Aceptar")
        self.ok_button.clicked.connect(self.accept)
        self.button_layout.addWidget(self.ok_button)

        # Optional: Copy details to clipboard button
        self.copy_button = QPushButton("Copiar Detalles")
        self.copy_button.clicked.connect(self.copy_details_to_clipboard)
        self.button_layout.addWidget(self.copy_button)
        self.copy_button.setVisible(False)  # Initially hidden, shown with details

        layout.addLayout(self.button_layout)

        self.setLayout(layout)
        self.adjustSize()  # Adjust dialog size to content

    def toggle_details_visibility(self):
        is_visible = self.details_text_edit.isVisible()
        new_visibility = not is_visible
        self.details_text_edit.setVisible(new_visibility)
        self.copy_button.setVisible(new_visibility)
        self.details_button.setText(
            "Ocultar Detalles" if new_visibility else "Mostrar Detalles"
        )
        self.adjustSize()  # Re-adjust dialog size

    def copy_details_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.details_text_edit.toPlainText())
        # Optionally, give feedback like changing button text for a moment
        # self.copy_button.setText("¡Copiado!")
        # QTimer.singleShot(2000, lambda: self.copy_button.setText("Copiar Detalles"))


if __name__ == "__main__":
    import sys

    # Example usage
    app = QApplication(sys.argv)
    try:
        # Simulate an error
        x = 1 / 0
    except Exception:
        # Format traceback
        exc_type, exc_value, exc_tb = sys.exc_info()
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
        details_text = "".join(tb_lines)

        dialog = ErrorDialog(
            title="Error Crítico",
            user_message="Ha ocurrido un error crítico durante la ejecución.",
            details=details_text,
        )
        dialog.exec()
    sys.exit(app.exec())
