"""
Tests for the LoginDialog UI component.
Focus: Dialog instantiation, user input, and authentication logic.
"""

import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog
from PySide6.QtCore import Qt
import sys

# Ensure QApplication exists
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

from ui.dialogs.login_dialog import LoginDialog

# Fixtures replace setUp/tearDown
@pytest.fixture
def login_dialog(qtbot):
    """Provide a LoginDialog instance with a mocked user service for testing."""
    mock_user_service = MagicMock()
    dialog = LoginDialog(mock_user_service)
    qtbot.add_widget(dialog)
    yield dialog, mock_user_service
    dialog.close()

def test_login_with_valid_credentials_succeeds(login_dialog, qtbot):
    """Test that login succeeds when valid credentials are provided."""
    dialog, mock_user_service = login_dialog
    
    # Mock user_service to return a user object
    mock_user = MagicMock()
    mock_user_service.authenticate.return_value = mock_user

    dialog.username_input.setText("testuser")
    dialog.password_input.setText("password123")
    qtbot.mouseClick(dialog.login_button, Qt.LeftButton)

    # Pytest-style assertions
    assert dialog.result() == QDialog.Accepted
    assert dialog.logged_in_user == mock_user

def test_login_with_invalid_credentials_shows_warning(login_dialog, qtbot):
    """Test that login shows warning when invalid credentials are provided."""
    dialog, mock_user_service = login_dialog
    
    # Mock user_service to return None (invalid credentials)
    mock_user_service.authenticate.return_value = None

    dialog.username_input.setText("wronguser")
    dialog.password_input.setText("wrongpass")
    
    with patch.object(QMessageBox, 'warning') as mock_warning:
        qtbot.mouseClick(dialog.login_button, Qt.LeftButton)
        
        # Pytest-style assertions
        assert dialog.result() == 0  # Not accepted
        assert dialog.logged_in_user is None
        mock_warning.assert_called_once()
        # Password field should be cleared
        assert dialog.password_input.text() == ""

def test_login_with_empty_fields_shows_warning(login_dialog, qtbot):
    """Test that login shows warning when empty fields are submitted."""
    dialog, _ = login_dialog
    
    dialog.username_input.setText("")
    dialog.password_input.setText("")
    
    with patch.object(QMessageBox, 'warning') as mock_warning:
        qtbot.mouseClick(dialog.login_button, Qt.LeftButton)
        
        mock_warning.assert_called_once()
        assert dialog.result() == 0
        assert dialog.logged_in_user is None

def test_login_when_authentication_fails_shows_critical_error(login_dialog, qtbot):
    """Test that login shows critical error when authentication throws exception."""
    dialog, mock_user_service = login_dialog
    
    # Mock user_service to raise an exception
    mock_user_service.authenticate.side_effect = Exception("DB error")
    
    dialog.username_input.setText("testuser")
    dialog.password_input.setText("password123")
    
    with patch.object(QMessageBox, 'critical') as mock_critical:
        qtbot.mouseClick(dialog.login_button, Qt.LeftButton)
        
        mock_critical.assert_called_once()
        assert dialog.result() == 0
        assert dialog.logged_in_user is None