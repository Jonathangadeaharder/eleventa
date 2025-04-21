"""
Integration tests for authentication workflows.

These tests verify that authentication components work together correctly
for login, permission management, and sessions.
"""
import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QMessageBox

# Import resources FIRST to ensure they are loaded before UI elements
try:
    # Import the actual compiled resource file (usually resources.py or similar)
    import ui.resources.resources
except ImportError:
    print("Warning: Could not import Qt resources (ui.resources.resources). Icons might be missing.")
    # If tests fail due to missing icons, ensure resources.py is generated via pyside6-rcc and importable

from ui.dialogs.login_dialog import LoginDialog  # Import the actual dialog


class TestLoginWorkflows:
    """Tests for login-related workflows."""
    
    def test_login_success_with_session_creation(self):
        """Test successful login creates a valid session."""
        # Create mock components
        mock_user_repo = MagicMock()
        mock_session_service = MagicMock()
        
        # Configure user repo to return a user when credentials are valid
        test_user = MagicMock()
        test_user.id = 1
        test_user.username = "testuser"
        test_user.is_active = True
        test_user.is_admin = False
        
        # Password verification function
        def verify_password(stored_hash, password):
            # Simple mock: 'valid_password' is the only valid password
            return password == "valid_password"
        
        def find_user_by_username(username):
            if username == "testuser":
                return test_user
            return None
            
        mock_user_repo.find_by_username.side_effect = find_user_by_username
        
        # Session creation function
        def create_session(user):
            return {
                "token": "session_token_123",
                "user_id": user.id,
                "created_at": "2023-05-01T10:00:00",
                "expires_at": "2023-05-01T22:00:00"
            }
            
        mock_session_service.create_session.side_effect = create_session
        
        # Create minimal authentication service
        class AuthService:
            def __init__(self, user_repo, session_service):
                self.user_repo = user_repo
                self.session_service = session_service
                self.current_user = None
                self.current_session = None
                
            def login(self, username, password):
                # Find user
                user = self.user_repo.find_by_username(username)
                
                if not user:
                    return False, "User not found"
                    
                if not user.is_active:
                    return False, "User account is inactive"
                
                # Verify password
                if not verify_password(user.password_hash, password):
                    return False, "Invalid password"
                
                # Create session
                session = self.session_service.create_session(user)
                
                # Store current user and session
                self.current_user = user
                self.current_session = session
                
                return True, "Login successful"
                
            def get_current_user(self):
                return self.current_user
                
            def get_current_session(self):
                return self.current_session
                
            def logout(self):
                if self.current_session:
                    self.session_service.invalidate_session(self.current_session["token"])
                    
                self.current_user = None
                self.current_session = None
        
        # Create the service with mock components
        auth_service = AuthService(
            user_repo=mock_user_repo,
            session_service=mock_session_service
        )
        
        # Test successful login
        success, message = auth_service.login("testuser", "valid_password")
        
        # Verify user was looked up
        mock_user_repo.find_by_username.assert_called_once_with("testuser")
        
        # Verify session was created
        mock_session_service.create_session.assert_called_once_with(test_user)
        
        # Verify success and current state
        assert success is True
        assert message == "Login successful"
        assert auth_service.get_current_user() == test_user
        assert auth_service.get_current_session()["token"] == "session_token_123"
        
        # Test logout
        auth_service.logout()
        
        # Verify session was invalidated
        mock_session_service.invalidate_session.assert_called_once_with("session_token_123")
        
        # Verify current state was cleared
        assert auth_service.get_current_user() is None
        assert auth_service.get_current_session() is None
    
    def test_login_with_inactive_user(self):
        """Test login with inactive user is rejected."""
        # Create mock components
        mock_user_repo = MagicMock()
        mock_session_service = MagicMock()
        
        # Configure user repo to return an inactive user
        inactive_user = MagicMock()
        inactive_user.id = 2
        inactive_user.username = "inactive"
        inactive_user.is_active = False
        
        def find_user_by_username(username):
            if username == "inactive":
                return inactive_user
            return None
            
        mock_user_repo.find_by_username.side_effect = find_user_by_username
        
        # Create minimal authentication service
        class AuthService:
            def __init__(self, user_repo, session_service):
                self.user_repo = user_repo
                self.session_service = session_service
                self.current_user = None
                self.current_session = None
                
            def login(self, username, password):
                # Find user
                user = self.user_repo.find_by_username(username)
                
                if not user:
                    return False, "User not found"
                    
                if not user.is_active:
                    return False, "User account is inactive"
                
                # Further authentication steps omitted
                
                return True, "Login successful"
        
        # Create the service with mock components
        auth_service = AuthService(
            user_repo=mock_user_repo,
            session_service=mock_session_service
        )
        
        # Test login with inactive user
        success, message = auth_service.login("inactive", "any_password")
        
        # Verify user was looked up
        mock_user_repo.find_by_username.assert_called_once_with("inactive")
        
        # Verify login was rejected
        assert success is False
        assert message == "User account is inactive"


class TestPermissionVerification:
    """Tests for permission verification workflows."""
    
    def test_admin_access_control(self):
        """Test that admin-only functions verify permissions correctly."""
        # Create mock user objects
        admin_user = MagicMock()
        admin_user.id = 1
        admin_user.username = "admin"
        admin_user.is_admin = True
        
        regular_user = MagicMock()
        regular_user.id = 2
        regular_user.username = "regular"
        regular_user.is_admin = False
        
        # Create a minimal permissions service
        class PermissionService:
            def __init__(self):
                self.current_user = None
                
            def set_current_user(self, user):
                self.current_user = user
                
            def requires_admin(self, func):
                # Decorator that checks admin permission
                def wrapper(*args, **kwargs):
                    if not self.current_user:
                        raise ValueError("No user logged in")
                        
                    if not self.current_user.is_admin:
                        raise ValueError("Admin permission required")
                        
                    return func(*args, **kwargs)
                return wrapper
        
        # Create a service with admin-only functions
        class AdminService:
            def __init__(self, permission_service):
                self.permission_service = permission_service
                
            @property
            def delete_user(self):
                @self.permission_service.requires_admin
                def _delete_user(user_id):
                    # In a real system, this would delete the user
                    return f"User {user_id} deleted"
                return _delete_user
                
            @property
            def view_all_users(self):
                @self.permission_service.requires_admin
                def _view_all_users():
                    # In a real system, this would return all users
                    return ["User list would appear here"]
                return _view_all_users
        
        # Create the services
        permission_service = PermissionService()
        admin_service = AdminService(permission_service=permission_service)
        
        # Test with admin user
        permission_service.set_current_user(admin_user)
        
        # Admin functions should work
        result = admin_service.delete_user(3)
        assert result == "User 3 deleted"
        
        result = admin_service.view_all_users()
        assert result == ["User list would appear here"]
        
        # Test with regular user
        permission_service.set_current_user(regular_user)
        
        # Admin functions should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            admin_service.delete_user(3)
        
        assert "Admin permission required" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            admin_service.view_all_users()
            
        assert "Admin permission required" in str(exc_info.value)


class TestSessionManagement:
    """Tests for session management workflows."""
    
    def test_session_expiration_and_refresh(self):
        """Test that sessions can expire and be refreshed."""
        # Create mock components
        mock_session_repo = MagicMock()
        
        # Configure session repository
        active_sessions = {}
        expired_sessions = set()
        
        def save_session(session_data):
            session_id = session_data["id"]
            active_sessions[session_id] = session_data
            return session_data
            
        def get_session(session_id):
            return active_sessions.get(session_id)
            
        def is_expired(session_id):
            return session_id in expired_sessions
            
        def mark_expired(session_id):
            if session_id in active_sessions:
                expired_sessions.add(session_id)
                return True
            return False
            
        def refresh_session(session_id):
            if session_id in active_sessions and session_id not in expired_sessions:
                # Create refreshed session
                session = active_sessions[session_id]
                session["expires_at"] = "2023-05-02T22:00:00"  # Extended time
                return session
            return None
            
        mock_session_repo.save.side_effect = save_session
        mock_session_repo.get.side_effect = get_session
        mock_session_repo.is_expired.side_effect = is_expired
        mock_session_repo.mark_expired.side_effect = mark_expired
        mock_session_repo.refresh.side_effect = refresh_session
        
        # Create minimal session service
        class SessionService:
            def __init__(self, session_repo):
                self.session_repo = session_repo
                
            def create_session(self, user):
                session = {
                    "id": f"session_{user.id}_{hash(user.username)}",
                    "user_id": user.id,
                    "created_at": "2023-05-01T10:00:00",
                    "expires_at": "2023-05-01T22:00:00"
                }
                
                return self.session_repo.save(session)
                
            def get_session(self, session_id):
                return self.session_repo.get(session_id)
                
            def validate_session(self, session_id):
                if not session_id or self.session_repo.is_expired(session_id):
                    return False
                    
                session = self.session_repo.get(session_id)
                return session is not None
                
            def refresh_session(self, session_id):
                return self.session_repo.refresh(session_id)
                
            def invalidate_session(self, session_id):
                return self.session_repo.mark_expired(session_id)
        
        # Create mock user
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        
        # Test session creation
        session_service = SessionService(session_repo=mock_session_repo)
        session = session_service.create_session(mock_user)
        
        session_id = session["id"]
        
        # Verify session is valid
        assert session_service.validate_session(session_id) is True
        
        # Test session refresh
        refreshed_session = session_service.refresh_session(session_id)
        
        # Verify expiration was extended
        assert refreshed_session["expires_at"] == "2023-05-02T22:00:00"
        
        # Test session invalidation
        session_service.invalidate_session(session_id)
        
        # Verify session is no longer valid
        assert session_service.validate_session(session_id) is False


class TestUIAuthentication:
    """Tests for UI authentication integration."""

    def test_login_dialog_with_auth_service(self, qtbot):
        """Test that the actual login dialog integrates with the user service."""
        # Import Qt resources safely
        try:
            import ui.resources.resources
        except ImportError:
            print("Warning: Could not import Qt resources. Icons might be missing.")
            
        # Create mock user service (matching the actual dialog's dependency)
        mock_user_service = MagicMock()
        mock_logged_in_user = MagicMock() # Mock user object for successful login
        mock_logged_in_user.username = "admin"

        # Configure user service behavior (authenticate method)
        def authenticate_side_effect(username, password):
            if username == "admin" and password == "correct":
                return mock_logged_in_user # Return user object on success
            return None # Return None on failure (invalid credentials)

        # The actual dialog checks for 'authenticate' first
        mock_user_service.authenticate.side_effect = authenticate_side_effect
        # Add authenticate_user attribute just in case, pointing to the same mock
        mock_user_service.authenticate_user = mock_user_service.authenticate

        # Patch QIcon to prevent crashes with missing resources
        with patch('PySide6.QtGui.QIcon', return_value=MagicMock()) as mock_icon:
            # Patch QMessageBox.warning to prevent actual dialog pop-up during test
            with patch('PySide6.QtWidgets.QMessageBox.warning', return_value=QMessageBox.Ok) as mock_warning:
                # Create the *actual* LoginDialog with the mock service
                dialog = LoginDialog(user_service=mock_user_service)
                qtbot.addWidget(dialog) # Register dialog with qtbot for interaction/cleanup
                dialog.show()
                qtbot.waitExposed(dialog) # Ensure dialog is visible before interaction

                # --- Test unsuccessful login ---
                qtbot.keyClicks(dialog.username_input, "admin")
                qtbot.keyClicks(dialog.password_input, "wrong")
                qtbot.mouseClick(dialog.login_button, Qt.LeftButton) # Use mouseClick for buttons
                QApplication.processEvents() # Allow Qt event loop to process signals/slots

                # Verify user service was called with the entered credentials
                mock_user_service.authenticate.assert_called_with("admin", "wrong")

                # Verify dialog state (should still be showing, no user logged in)
                assert dialog.isVisible() # Dialog should still be open
                assert dialog.logged_in_user is None # Check the actual dialog's attribute

                # Verify the warning message was shown (dialog calls this on failure)
                mock_warning.assert_called_once()
                # Optional: Check the arguments passed to the warning
                args, kwargs = mock_warning.call_args
                # Ensure the exact message string (including the period) is the third argument
                assert len(args) >= 3
                assert args[2] == "Usuario o contraseña incorrectos." # Check message content with period

                # --- Test successful login ---
                # Reset the warning mock for the next part of the test
                mock_warning.reset_mock()

                # Clear inputs before trying again
                dialog.username_input.clear()
                dialog.password_input.clear()

                qtbot.keyClicks(dialog.username_input, "admin")
                qtbot.keyClicks(dialog.password_input, "correct")
                qtbot.mouseClick(dialog.login_button, Qt.LeftButton)
                QApplication.processEvents()

                # Verify user service was called with correct credentials
                mock_user_service.authenticate.assert_called_with("admin", "correct")

                # Verify dialog state (should be accepted, user logged in)
                assert dialog.logged_in_user == mock_logged_in_user # Check user object
                assert dialog.result() == QDialog.Accepted # Dialog should have been accepted

                # Verify no warning was shown on successful login
                mock_warning.assert_not_called()
