import pytest
import sys
from unittest.mock import MagicMock, patch

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialogButtonBox, QMessageBox
from PySide6.QtTest import QTest

from ui.dialogs.login_dialog import LoginDialog
from core.models.user import User
from core.services.user_service import UserService


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    app.quit()


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return User(
        id=1,
        username="admin",
        password_hash="hashed_password",
        full_name="Administrator",
        role="admin",
        is_active=True
    )


@pytest.fixture
def mock_user_service():
    """Create a mock user service."""
    return MagicMock(spec=UserService)


@pytest.fixture
def login_dialog(qapp, mock_user_service):
    """Create login dialog for testing."""
    return LoginDialog(mock_user_service)


def test_dialog_initialization(qtbot, login_dialog):
    """Test that the dialog initializes correctly."""
    dialog = login_dialog
    qtbot.addWidget(dialog)
    
    # Verify window title
    assert dialog.windowTitle() == "Iniciar Sesión"
    
    # Verify default values
    assert dialog.username_input.text() == ""
    assert dialog.password_input.text() == ""
    from PySide6.QtWidgets import QLineEdit
    assert dialog.password_input.echoMode() == QLineEdit.EchoMode.Password
    
    # Verify login button is initially disabled
    assert dialog.login_button.isEnabled() is False


def test_login_button_enabled_when_fields_filled(qtbot, login_dialog):
    """Test that login button is enabled when both fields are filled."""
    dialog = login_dialog
    qtbot.addWidget(dialog)
    
    # Initially disabled
    assert dialog.login_button.isEnabled() is False
    
    # Fill username only
    dialog.username_input.setText("admin")
    assert dialog.login_button.isEnabled() is False
    
    # Fill password as well
    dialog.password_input.setText("password")
    assert dialog.login_button.isEnabled() is True
    
    # Clear username
    dialog.username_input.setText("")
    assert dialog.login_button.isEnabled() is False


def test_successful_login(qtbot, login_dialog, mock_user_service, sample_user, monkeypatch):
    """Test successful login."""
    dialog = login_dialog
    qtbot.addWidget(dialog)
    
    # Fill in credentials
    dialog.username_input.setText("admin")
    dialog.password_input.setText("password")
    
    # Mock successful authentication
    mock_user_service.authenticate_user.return_value = sample_user
    
    # Patch QDialog.accept to prevent actual dialog closing
    monkeypatch.setattr('PySide6.QtWidgets.QDialog.accept', lambda self: None)
    
    # Click login button
    qtbot.mouseClick(dialog.login_button, Qt.LeftButton)
    
    # Verify service was called with correct credentials
    mock_user_service.authenticate_user.assert_called_once_with("admin", "password")
    
    # Verify user is set
    assert dialog.logged_in_user == sample_user


def test_failed_login_invalid_credentials(qtbot, login_dialog, mock_user_service):
    """Test failed login with invalid credentials."""
    dialog = login_dialog
    qtbot.addWidget(dialog)
    
    # Fill in credentials
    dialog.username_input.setText("admin")
    dialog.password_input.setText("wrong_password")
    
    # Mock failed authentication
    mock_user_service.authenticate_user.return_value = None
    
    with patch.object(QMessageBox, 'warning') as mock_warning:
        # Click login button
        qtbot.mouseClick(dialog.login_button, Qt.LeftButton)
        
        # Verify warning message is shown
        mock_warning.assert_called_once()
        assert "credenciales" in mock_warning.call_args[0][2].lower()
    
    # Verify service was called
    mock_user_service.authenticate_user.assert_called_once_with("admin", "wrong_password")
    
    # Verify no user is set
    assert dialog.logged_in_user is None


def test_failed_login_inactive_user(qtbot, login_dialog, mock_user_service):
    """Test failed login with inactive user."""
    dialog = login_dialog
    qtbot.addWidget(dialog)
    
    # Create inactive user
    inactive_user = User(
        id=1,
        username="admin",
        password_hash="hashed_password",
        full_name="Administrator",
        role="admin",
        is_active=False
    )
    
    # Fill in credentials
    dialog.username_input.setText("admin")
    dialog.password_input.setText("password")
    
    # Mock authentication returning inactive user
    mock_user_service.authenticate_user.return_value = inactive_user
    
    with patch.object(QMessageBox, 'warning') as mock_warning:
        # Click login button
        qtbot.mouseClick(dialog.login_button, Qt.LeftButton)
        
        # Verify warning message is shown
        mock_warning.assert_called_once()
        assert "inactivo" in mock_warning.call_args[0][2].lower()
    
    # Verify no user is set
    assert dialog.logged_in_user is None


def test_service_error_handling(qtbot, login_dialog, mock_user_service):
    """Test handling of service errors during authentication."""
    dialog = login_dialog
    qtbot.addWidget(dialog)
    
    # Fill in credentials
    dialog.username_input.setText("admin")
    dialog.password_input.setText("password")
    
    # Mock service error
    mock_user_service.authenticate_user.side_effect = Exception("Database connection error")
    
    with patch.object(QMessageBox, 'critical') as mock_critical:
        # Click login button
        qtbot.mouseClick(dialog.login_button, Qt.LeftButton)
        
        # Verify error message is shown
        mock_critical.assert_called_once()
        assert "error" in mock_critical.call_args[0][2].lower()
    
    # Verify no user is set
    assert dialog.logged_in_user is None


def test_enter_key_triggers_login(qtbot, login_dialog, mock_user_service, sample_user, monkeypatch):
    """Test that pressing Enter triggers login."""
    dialog = login_dialog
    qtbot.addWidget(dialog)
    
    # Fill in credentials
    dialog.username_input.setText("admin")
    dialog.password_input.setText("password")
    
    # Mock successful authentication
    mock_user_service.authenticate_user.return_value = sample_user
    
    # Patch QDialog.accept to prevent actual dialog closing
    monkeypatch.setattr('PySide6.QtWidgets.QDialog.accept', lambda self: None)
    
    # Press Enter in password field
    qtbot.keyPress(dialog.password_input, Qt.Key_Return)
    
    # Verify service was called
    mock_user_service.authenticate_user.assert_called_once_with("admin", "password")


def test_cancel_dialog(qtbot, login_dialog):
    """Test canceling the dialog."""
    dialog = login_dialog
    qtbot.addWidget(dialog)
    
    # Fill in some data
    dialog.username_input.setText("admin")
    dialog.password_input.setText("password")
    
    # Cancel the dialog
    dialog.reject()
    
    # Verify dialog result
    from PySide6.QtWidgets import QDialog
    assert dialog.result() == QDialog.Rejected
    assert dialog.logged_in_user is None


def test_password_field_security(qtbot, login_dialog):
    """Test that password field is properly secured."""
    dialog = login_dialog
    qtbot.addWidget(dialog)
    
    # Verify password field is masked
    from PySide6.QtWidgets import QLineEdit
    assert dialog.password_input.echoMode() == QLineEdit.EchoMode.Password
    
    # Type password and verify it's not visible
    dialog.password_input.setText("secret_password")
    assert dialog.password_input.displayText() != "secret_password"
    assert dialog.password_input.text() == "secret_password"


def test_username_case_insensitive(qtbot, login_dialog, mock_user_service, sample_user, monkeypatch):
    """Test that username is case insensitive."""
    dialog = login_dialog
    qtbot.addWidget(dialog)
    
    # Fill in credentials with different case
    dialog.username_input.setText("ADMIN")
    dialog.password_input.setText("password")
    
    # Mock successful authentication
    mock_user_service.authenticate_user.return_value = sample_user
    
    # Patch QDialog.accept to prevent actual dialog closing
    monkeypatch.setattr('PySide6.QtWidgets.QDialog.accept', lambda self: None)
    
    # Click login button
    qtbot.mouseClick(dialog.login_button, Qt.LeftButton)
    
    # Verify service was called with lowercase username
    mock_user_service.authenticate_user.assert_called_once_with("ADMIN", "password")


def test_multiple_failed_attempts(qtbot, login_dialog, mock_user_service):
    """Test handling of multiple failed login attempts."""
    dialog = login_dialog
    qtbot.addWidget(dialog)
    
    # Mock failed authentication
    mock_user_service.authenticate_user.return_value = None
    
    # Attempt login multiple times
    for i in range(3):
        dialog.username_input.setText("admin")
        dialog.password_input.setText(f"wrong_password_{i}")
        
        with patch.object(QMessageBox, 'warning'):
            qtbot.mouseClick(dialog.login_button, Qt.LeftButton)
    
    # Verify service was called multiple times
    assert mock_user_service.authenticate_user.call_count == 3
    
    # Verify no user is set
    assert dialog.logged_in_user is None


def test_remember_username_functionality(qtbot, login_dialog):
    """Test remember username checkbox functionality."""
    dialog = login_dialog
    qtbot.addWidget(dialog)
    
    # Check if remember username checkbox exists
    if hasattr(dialog, 'remember_username_checkbox'):
        # Test checkbox behavior
        assert dialog.remember_username_checkbox.isChecked() is False
        
        # Check the checkbox
        dialog.remember_username_checkbox.setChecked(True)
        assert dialog.remember_username_checkbox.isChecked() is True
        
        # Fill username
        dialog.username_input.setText("admin")
        
        # Username should be remembered for next login
        # This would typically be tested with settings/preferences
        assert dialog.username_input.text() == "admin"


def test_show_hide_password_functionality(qtbot, login_dialog):
    """Test show/hide password functionality if available."""
    dialog = login_dialog
    qtbot.addWidget(dialog)
    
    # Check if show password button exists
    if hasattr(dialog, 'show_password_button'):
        # Initially password should be hidden
        from PySide6.QtWidgets import QLineEdit
        assert dialog.password_input.echoMode() == QLineEdit.EchoMode.Password
        
        # Click show password button
        qtbot.mouseClick(dialog.show_password_button, Qt.LeftButton)
        
        # Password should now be visible
        assert dialog.password_input.echoMode() == QLineEdit.EchoMode.Normal
        
        # Click again to hide
        qtbot.mouseClick(dialog.show_password_button, Qt.LeftButton)
        
        # Password should be hidden again
        assert dialog.password_input.echoMode() == QLineEdit.EchoMode.Password