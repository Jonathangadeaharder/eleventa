from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QMessageBox,
    QHBoxLayout,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from ui.utils import (
    style_text_input,
    style_primary_button,
    style_secondary_button,
    style_heading_label,
)


class LoginDialog(QDialog):
    """
    A dialog for user login.
    """

    def __init__(self, user_service, parent=None):
        super().__init__(parent)
        self.user_service = user_service
        self.logged_in_user = None  # To store the user object upon successful login

        self.setWindowTitle("Iniciar Sesión")
        self.setModal(True)  # Make sure user interacts with this first
        self.setFixedSize(400, 280)  # Increased height to prevent cutoff

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 15, 25, 20)  # Reduced top margin
        main_layout.setSpacing(10)  # Reduced spacing

        # Add heading
        heading = QLabel("Bienvenido a Eleventa")
        style_heading_label(heading)
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(heading)

        # Add description
        description = QLabel("Ingrese sus credenciales para acceder al sistema")
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(description)

        # Add some space
        main_layout.addSpacing(15)

        # Username input
        self.username_input = QLineEdit()
        self.username_input.setObjectName("username_input")
        self.username_input.setPlaceholderText("Usuario")
        style_text_input(self.username_input)
        self.username_input.setMinimumHeight(32)
        main_layout.addWidget(self.username_input)

        # Add some space
        main_layout.addSpacing(8)

        # Password input
        self.password_input = QLineEdit()
        self.password_input.setObjectName("password_input")
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        style_text_input(self.password_input)
        self.password_input.setMinimumHeight(32)
        main_layout.addWidget(self.password_input)

        # Add some space
        main_layout.addSpacing(15)

        # Buttons in horizontal layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setObjectName("cancel_button")
        style_secondary_button(self.cancel_button)
        self.cancel_button.setIcon(QIcon(":/icons/icons/cancel.png"))  # Restore icon
        self.cancel_button.setIconSize(
            self.cancel_button.iconSize() * 0.8
        )  # Restore icon size

        self.login_button = QPushButton("Ingresar")
        self.login_button.setObjectName("login_button")
        style_primary_button(self.login_button)
        self.login_button.setIcon(QIcon(":/icons/icons/login.png"))  # Restore icon
        self.login_button.setIconSize(
            self.login_button.iconSize() * 0.8
        )  # Restore icon size
        self.login_button.clicked.connect(self.handle_login)

        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.login_button)

        main_layout.addLayout(button_layout)

        # Connect signals
        self.cancel_button.clicked.connect(self.reject)
        self.username_input.returnPressed.connect(self.password_input.setFocus)
        self.password_input.returnPressed.connect(self.handle_login)

        # Connect text change signals for validation
        self.username_input.textChanged.connect(self._validate_inputs)
        self.password_input.textChanged.connect(self._validate_inputs)

        # Initial validation
        self._validate_inputs()

        # Set focus
        self.username_input.setFocus()

        # Apply overall style to dialog
        self.setStyleSheet(
            """
            QDialog {
                background-color: white;
            }
            QLineEdit {
                padding-left: 8px;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QLineEdit:focus {
                border: 1px solid #2c6ba5;
            }
        """
        )

    def _validate_inputs(self):
        """Enable/disable login button based on input validation."""
        username = self.username_input.text().strip()
        password = self.password_input.text()

        # Enable login button only if both fields have content
        self.login_button.setEnabled(bool(username and password))

    def handle_login(self):
        """
        Handles the login attempt when the OK button is clicked.
        """
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(
                self, "Error de Ingreso", "Por favor ingrese usuario y contraseña."
            )
            self.setProperty("error_shown", True)
            return

        try:
            # Prefer authenticate; fallback to authenticate_user for backwards compatibility
            if hasattr(self.user_service, "authenticate"):
                user = self.user_service.authenticate(username, password)
            elif hasattr(self.user_service, "authenticate_user"):
                user = self.user_service.authenticate_user(username, password)
            else:
                raise AttributeError("User service has no authenticate methods")
            if user:
                # Check if user is active
                if hasattr(user, "is_active") and not user.is_active:
                    QMessageBox.warning(
                        self, "Error de Ingreso", "El usuario está inactivo."
                    )
                    self.password_input.clear()
                    self.setProperty("error_shown", True)
                    return

                self.logged_in_user = user
                self.setProperty("error_shown", False)
                self.accept()  # Close the dialog successfully
            else:
                QMessageBox.warning(
                    self, "Error de Ingreso", "Credenciales incorrectas."
                )
                # Optionally clear password field
                self.password_input.clear()
                self.setProperty("error_shown", True)
        except Exception as e:
            # Catch potential errors during authentication (e.g., DB issues)
            QMessageBox.critical(
                self, "Error", f"Ocurrió un error durante la autenticación: {e}"
            )
            # Log the error properly in a real application
            print(f"Authentication error: {e}")
            self.setProperty("error_shown", True)

    def get_logged_in_user(self):
        """
        Returns the authenticated user object if login was successful.
        """
        return self.logged_in_user
