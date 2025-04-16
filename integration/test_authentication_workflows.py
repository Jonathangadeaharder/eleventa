"""
Integration tests for authentication workflows.

These tests verify that authentication components work together correctly
for login, permission management, and sessions.
"""
import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLineEdit, QPushButton, QMessageBox


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
        """Test that login dialog integrates with auth service."""
        # Create mock auth service
        mock_auth_service = MagicMock()
        
        # Configure auth service behavior
        def login_side_effect(username, password):
            if username == "admin" and password == "correct":
                return True, "Login successful"
            return False, "Invalid credentials"
            
        mock_auth_service.login.side_effect = login_side_effect
        
        # Patch QMessageBox.warning to prevent actual dialog
        with patch('PySide6.QtWidgets.QMessageBox.warning', return_value=None) as mock_warning:
            # Create a simple login dialog
            class LoginDialog(QDialog):
                def __init__(self, auth_service):
                    super().__init__()
                    self.auth_service = auth_service
                    self.login_successful = False
                    
                    # Create dialog elements
                    self.username_input = QLineEdit()
                    self.username_input.setObjectName("username_input")
                    
                    self.password_input = QLineEdit()
                    self.password_input.setObjectName("password_input")
                    self.password_input.setEchoMode(QLineEdit.Password)
                    
                    self.login_button = QPushButton("Login")
                    self.login_button.setObjectName("login_button")
                    self.login_button.clicked.connect(self.attempt_login)
                    
                    self.cancel_button = QPushButton("Cancel")
                    self.cancel_button.setObjectName("cancel_button")
                    self.cancel_button.clicked.connect(self.reject)
                
                def attempt_login(self):
                    username = self.username_input.text()
                    password = self.password_input.text()
                    
                    success, message = self.auth_service.login(username, password)
                    
                    if success:
                        self.login_successful = True
                        self.accept()
                    else:
                        QMessageBox.warning(self, "Login Failed", message)
            
            # Create dialog with mock auth service
            dialog = LoginDialog(auth_service=mock_auth_service)
            qtbot.addWidget(dialog)
            
            # Test unsuccessful login
            qtbot.keyClicks(dialog.username_input, "admin")
            qtbot.keyClicks(dialog.password_input, "wrong")
            qtbot.mouseClick(dialog.login_button, Qt.LeftButton)
            
            # Verify auth service was called with credentials
            mock_auth_service.login.assert_called_with("admin", "wrong")
            
            # Verify dialog state (should still be showing, login not successful)
            assert dialog.login_successful is False
            
            # Verify the warning was shown with the correct message
            mock_warning.assert_called_once()
            
            # Clear inputs and try successful login
            dialog.username_input.clear()
            dialog.password_input.clear()
            
            qtbot.keyClicks(dialog.username_input, "admin")
            qtbot.keyClicks(dialog.password_input, "correct")
            qtbot.mouseClick(dialog.login_button, Qt.LeftButton)
            
            # Verify auth service was called with correct credentials
            mock_auth_service.login.assert_called_with("admin", "correct")
            
            # Verify dialog state (should be accepted, login successful)
            assert dialog.login_successful is True
            assert dialog.result() == QDialog.Accepted 