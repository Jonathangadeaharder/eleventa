"""
UI tests for the login dialog.

These tests verify that the LoginDialog handles user authentication correctly.
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
from PySide6.QtWidgets import QDialog, QMessageBox

# Import the actual LoginDialog class
from ui.dialogs.login_dialog import LoginDialog


@pytest.fixture
def mock_user_service():
    """Create a mock user service for testing login."""
    service = MagicMock()
    # Default to authentication failing
    service.authenticate.return_value = None
    return service


def test_login_dialog_accepts_valid_credentials(qtbot, mock_user_service):
    """Test that the login dialog accepts valid credentials."""
    # Create a mock user object for successful authentication
    mock_user = MagicMock()
    mock_user.username = "admin"
    mock_user_service.authenticate.return_value = mock_user

    # Patch QIcon to prevent crashes with missing resources
    with patch("PySide6.QtGui.QIcon", return_value=MagicMock()):
        with patch(
            "PySide6.QtWidgets.QMessageBox.warning", return_value=QMessageBox.Ok
        ):
            # Create the login dialog
            dialog = LoginDialog(mock_user_service)
            qtbot.addWidget(dialog)

            # Enter valid credentials
            qtbot.keyClicks(dialog.username_input, "admin")
            qtbot.keyClicks(dialog.password_input, "password")

            # Click the login button
            qtbot.mouseClick(dialog.login_button, Qt.LeftButton)

            # Verify that the dialog is accepted and user is logged in
            assert dialog.result() == QDialog.Accepted
            assert dialog.logged_in_user == mock_user

            # Verify that the user service was called with correct credentials
            mock_user_service.authenticate.assert_called_with("admin", "password")


def test_login_dialog_rejects_invalid_credentials(qtbot, mock_user_service):
    """Test that the login dialog rejects invalid credentials."""
    # Configure the mock to return None for authentication (invalid credentials)
    mock_user_service.authenticate.return_value = None

    # Patch QIcon and QMessageBox to prevent crashes
    with patch("PySide6.QtGui.QIcon", return_value=MagicMock()):
        with patch(
            "PySide6.QtWidgets.QMessageBox.warning", return_value=QMessageBox.Ok
        ) as mock_warning:
            # Create the login dialog
            dialog = LoginDialog(mock_user_service)
            qtbot.addWidget(dialog)

            # Enter invalid credentials
            qtbot.keyClicks(dialog.username_input, "admin")
            qtbot.keyClicks(dialog.password_input, "wrong")

            # Click the login button
            qtbot.mouseClick(dialog.login_button, Qt.LeftButton)

            # Verify that the dialog is not accepted
            assert dialog.result() != QDialog.Accepted
            assert dialog.logged_in_user is None

            # Verify that an error message was shown
            mock_warning.assert_called_once()

            # Verify that the user service was called with the entered credentials
            mock_user_service.authenticate.assert_called_with("admin", "wrong")


def test_login_dialog_handles_empty_credentials(qtbot, mock_user_service):
    """Test that the login dialog handles empty credentials."""
    # Patch QIcon and QMessageBox to prevent crashes
    with patch("PySide6.QtGui.QIcon", return_value=MagicMock()):
        with patch(
            "PySide6.QtWidgets.QMessageBox.warning", return_value=QMessageBox.Ok
        ) as mock_warning:
            # Create the login dialog
            dialog = LoginDialog(mock_user_service)
            qtbot.addWidget(dialog)

            # Click the login button without entering credentials
            qtbot.mouseClick(dialog.login_button, Qt.LeftButton)

            # Verify that the dialog is not accepted
            assert dialog.result() != QDialog.Accepted
            assert dialog.logged_in_user is None

            # Verify that an error message was shown
            mock_warning.assert_called_once()

            # Verify that the user service was not called
            mock_user_service.authenticate.assert_not_called()


def test_login_dialog_cancel_button(qtbot, mock_user_service):
    """Test that the cancel button rejects the dialog."""
    # Patch QIcon to prevent crashes
    with patch("PySide6.QtGui.QIcon", return_value=MagicMock()):
        # Create the login dialog
        dialog = LoginDialog(mock_user_service)
        qtbot.addWidget(dialog)

        # Click the cancel button
        qtbot.mouseClick(dialog.cancel_button, Qt.LeftButton)

        # Verify that the dialog is rejected
        assert dialog.result() == QDialog.Rejected
        assert dialog.logged_in_user is None

        # Verify that the user service was not called
        mock_user_service.authenticate.assert_not_called()
