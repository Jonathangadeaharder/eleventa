from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox, QDialogButtonBox,
    QHBoxLayout, QFrame, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from ui.utils import (
    style_text_input, style_primary_button, style_secondary_button, 
    apply_standard_form_style, style_heading_label
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
        self.setModal(True) # Make sure user interacts with this first
        self.setFixedSize(400, 240)  # Set fixed size for login dialog

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

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
        main_layout.addSpacing(10)
        
        # Form container with border
        form_container = QFrame()
        form_container.setFrameShape(QFrame.Shape.StyledPanel)
        form_container.setFrameShadow(QFrame.Shadow.Sunken)
        form_container.setStyleSheet("QFrame { background-color: #f8f8f8; border-radius: 6px; }")
        
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(15, 15, 15, 15)
        form_layout.setSpacing(10)

        self.username_label = QLabel("Usuario:")
        self.username_input = QLineEdit()
        style_text_input(self.username_input)
        
        self.password_label = QLabel("Contraseña:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        style_text_input(self.password_input)

        form_layout.addWidget(self.username_label)
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(self.password_label)
        form_layout.addWidget(self.password_input)
        
        main_layout.addWidget(form_container)
        
        # Buttons in horizontal layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.cancel_button = QPushButton("Cancelar")
        style_secondary_button(self.cancel_button)
        self.cancel_button.setIcon(QIcon(":/icons/icons/cancel.png"))
        
        self.login_button = QPushButton("Ingresar")
        style_primary_button(self.login_button)
        self.login_button.setIcon(QIcon(":/icons/icons/save.png"))
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.login_button)
        
        main_layout.addLayout(button_layout)

        # Connect signals
        self.login_button.clicked.connect(self.handle_login)
        self.cancel_button.clicked.connect(self.reject)
        self.username_input.returnPressed.connect(self.password_input.setFocus)
        self.password_input.returnPressed.connect(self.handle_login)

        # Set focus
        self.username_input.setFocus()

    def handle_login(self):
        """
        Handles the login attempt when the OK button is clicked.
        """
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Error de Ingreso", "Por favor ingrese usuario y contraseña.")
            return

        try:
            # Assuming authenticate_user returns the User object on success, None otherwise
            user = self.user_service.authenticate_user(username, password)
            if user:
                self.logged_in_user = user
                self.accept() # Close the dialog successfully
            else:
                QMessageBox.warning(self, "Error de Ingreso", "Usuario o contraseña incorrectos.")
                # Optionally clear password field
                self.password_input.clear()
        except Exception as e:
            # Catch potential errors during authentication (e.g., DB issues)
            QMessageBox.critical(self, "Error", f"Ocurrió un error durante la autenticación: {e}")
            # Log the error properly in a real application
            print(f"Authentication error: {e}")

    def get_logged_in_user(self):
        """
        Returns the authenticated user object if login was successful.
        """
        return self.logged_in_user
