"""
UI tests for the login dialog.

These tests verify that the login dialog works correctly
using pytest-qt to simulate user interactions.
"""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Add project root to path if needed (before other imports)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PySide6.QtCore import Qt

# ruff: noqa: E402 - imports after sys.path manipulation
from PySide6.QtWidgets import QLineEdit, QPushButton, QDialog, QMessageBox

# Import the actual LoginDialog class
from ui.dialogs.login_dialog import LoginDialog


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

    # Patch QIcon to prevent crashes with missing resources
    with patch("PySide6.QtGui.QIcon", return_value=MagicMock()):
        # Create the login dialog
        dialog = LoginDialog(mock_service)
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
        assert (
            password_input.echoMode() == QLineEdit.EchoMode.Password
        ), "Password input should hide text"


def test_login_success(qtbot, mock_user_service):
    """Test successful login flow."""
    # Create a test user object
    test_user = MagicMock()
    test_user.username = "admin"

    # Configure mock to return a user for successful authentication
    mock_user_service.authenticate.return_value = test_user

    # Patch QIcon and QMessageBox to prevent crashes
    with patch("PySide6.QtGui.QIcon", return_value=MagicMock()):
        with patch(
            "PySide6.QtWidgets.QMessageBox.warning", return_value=QMessageBox.Ok
        ):
            # Create login dialog
            dialog = LoginDialog(mock_user_service)
            qtbot.addWidget(dialog)

            # Fill in the form
            qtbot.keyClicks(dialog.username_input, "admin")
            qtbot.keyClicks(dialog.password_input, "12345")

            # Click the login button
            qtbot.mouseClick(dialog.login_button, Qt.LeftButton)

            # Verify the service was called correctly
            mock_user_service.authenticate.assert_called_once_with("admin", "12345")

            # Verify dialog result and user
            assert dialog.result() == QDialog.Accepted
            assert dialog.get_logged_in_user() == test_user


def test_login_failure(qtbot, mock_user_service):
    """Test failed login attempt."""
    # Configure mock to return None for failed authentication
    mock_user_service.authenticate.return_value = None

    # Patch QIcon and QMessageBox to prevent crashes
    with patch("PySide6.QtGui.QIcon", return_value=MagicMock()):
        with patch(
            "PySide6.QtWidgets.QMessageBox.warning", return_value=QMessageBox.Ok
        ) as mock_warning:
            # Create login dialog
            dialog = LoginDialog(mock_user_service)
            qtbot.addWidget(dialog)

            # Fill in the form with invalid credentials
            qtbot.keyClicks(dialog.username_input, "admin")
            qtbot.keyClicks(dialog.password_input, "wrong_password")

            # Click the login button
            qtbot.mouseClick(dialog.login_button, Qt.LeftButton)

            # Verify the service was called correctly
            mock_user_service.authenticate.assert_called_once_with(
                "admin", "wrong_password"
            )

            # Verify error is shown
            mock_warning.assert_called_once()
            assert (
                dialog.property("error_shown") is True
            ), "Error property should be set for failed login"


def test_cancel_login(qtbot, mock_user_service):
    """Test cancelling the login dialog."""
    # Patch QIcon to prevent crashes
    with patch("PySide6.QtGui.QIcon", return_value=MagicMock()):
        # Create login dialog
        dialog = LoginDialog(mock_user_service)
        qtbot.addWidget(dialog)

        # Click the cancel button
        qtbot.mouseClick(dialog.cancel_button, Qt.LeftButton)

        # Verify dialog result
        assert dialog.result() == QDialog.Rejected
        assert dialog.get_logged_in_user() is None
