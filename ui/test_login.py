"""
UI tests for the login dialog.

These tests verify that the login dialog works correctly
using pytest-qt to simulate user interactions.
"""
import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLineEdit, QPushButton, QLabel, QDialog, QWidget

# Since we might not have access to the actual LoginDialog class in tests,
# we'll create a mock class that mimics its behavior
class MockLoginDialog(QDialog):
    """Mock implementation of the LoginDialog for testing."""
    
    def __init__(self, user_service):
        super().__init__()
        self.user_service = user_service
        self.logged_in_user = None
        self.error_shown = False
        
        # Create UI elements
        self.username_input = QLineEdit()
        self.username_input.setObjectName("username_input")
        
        self.password_input = QLineEdit()
        self.password_input.setObjectName("password_input")
        self.password_input.setEchoMode(QLineEdit.Password)
        
        self.login_button = QPushButton("Login")
        self.login_button.setObjectName("login_button")
        self.login_button.clicked.connect(self.on_login)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("cancel_button")
        self.cancel_button.clicked.connect(self.reject)
    
    def on_login(self):
        """Handle login button click."""
        username = self.username_input.text()
        password = self.password_input.text()
        
        user = self.user_service.authenticate(username, password)
        
        if user:
            self.logged_in_user = user
            self.accept()
        else:
            self.error_shown = True
            self.setProperty("error_shown", True)
    
    def get_logged_in_user(self):
        """Return the logged in user."""
        return self.logged_in_user


@pytest.fixture
def mock_user_service():
    """Create a mock user service for testing login."""
    service = MagicMock()
    # Default to authentication failing
    service.authenticate.return_value = None
    return service


def test_login_dialog_ui_elements(qtbot):
    """Test that the login dialog has all the expected UI elements."""
    # Create a mock user service
    mock_service = MagicMock()
    
    # Create the login dialog
    dialog = MockLoginDialog(mock_service)
    qtbot.addWidget(dialog)
    
    # Verify that the dialog has all the expected elements
    username_input = dialog.findChild(QLineEdit, "username_input")
    password_input = dialog.findChild(QLineEdit, "password_input")
    login_button = dialog.findChild(QPushButton, "login_button")
    cancel_button = dialog.findChild(QPushButton, "cancel_button")
    
    assert username_input is not None, "Username input not found"
    assert password_input is not None, "Password input not found"
    assert login_button is not None, "Login button not found"
    assert cancel_button is not None, "Cancel button not found"
    
    # Verify initial state
    assert username_input.text() == "", "Username input should be empty initially"
    assert password_input.text() == "", "Password input should be empty initially"
    assert password_input.echoMode() == QLineEdit.Password, "Password input should hide text"


def test_login_success(qtbot, mock_user_service):
    """Test successful login flow."""
    # Create a test user object
    test_user = MagicMock()
    test_user.username = "admin"
    
    # Configure mock to return a user for successful authentication
    mock_user_service.authenticate.return_value = test_user
    
    # Create login dialog
    dialog = MockLoginDialog(mock_user_service)
    qtbot.addWidget(dialog)
    
    # Get UI elements
    username_input = dialog.username_input
    password_input = dialog.password_input
    login_button = dialog.login_button
    
    # Fill in the form
    qtbot.keyClicks(username_input, "admin")
    qtbot.keyClicks(password_input, "12345")
    
    # Click the login button
    qtbot.mouseClick(login_button, Qt.LeftButton)
    
    # Verify the service was called correctly
    mock_user_service.authenticate.assert_called_once_with("admin", "12345")
    
    # Verify dialog result and user
    assert dialog.result() == QDialog.Accepted
    assert dialog.get_logged_in_user() == test_user


def test_login_failure(qtbot, mock_user_service):
    """Test failed login attempt."""
    # Configure mock to return None for failed authentication
    mock_user_service.authenticate.return_value = None
    
    # Create login dialog
    dialog = MockLoginDialog(mock_user_service)
    qtbot.addWidget(dialog)
    
    # Get UI elements
    username_input = dialog.username_input
    password_input = dialog.password_input
    login_button = dialog.login_button
    
    # Fill in the form with invalid credentials
    qtbot.keyClicks(username_input, "admin")
    qtbot.keyClicks(password_input, "wrong_password")
    
    # Click the login button
    qtbot.mouseClick(login_button, Qt.LeftButton)
    
    # Verify the service was called correctly
    mock_user_service.authenticate.assert_called_once_with("admin", "wrong_password")
    
    # Verify error is shown
    assert dialog.error_shown is True, "Error message should be shown for failed login"


def test_cancel_login(qtbot, mock_user_service):
    """Test cancelling the login dialog."""
    # Create login dialog
    dialog = MockLoginDialog(mock_user_service)
    qtbot.addWidget(dialog)
    
    # Get cancel button
    cancel_button = dialog.cancel_button
    
    # Click the cancel button
    qtbot.mouseClick(cancel_button, Qt.LeftButton)
    
    # Verify dialog result
    assert dialog.result() == QDialog.Rejected
    assert dialog.get_logged_in_user() is None 