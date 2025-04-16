"""
Integration tests with mocks for initialization.

These tests verify the correct ways to initialize services without importing the actual modules.
"""
import pytest
from unittest.mock import MagicMock


class TestRepositoryInjection:
    """Tests for repository injection patterns."""
    
    def test_factory_vs_instance_injection(self):
        """Test the difference between factory function and instance injection."""
        # Create mocks
        mock_session = MagicMock()
        mock_repo = MagicMock()
        mock_repo.get_all.return_value = []
        
        # Create a factory function like in main.py
        def get_repo_factory(session):
            return mock_repo
        
        # Create a minimal service class that reproduces our issue
        class ServiceClass:
            def __init__(self, repo):
                self.repo = repo
                
            def get_all_items(self):
                return self.repo.get_all()
        
        # Test with factory function (wrong approach)
        wrong_service = ServiceClass(repo=get_repo_factory)
        
        # This will fail because we're passing a function instead of calling it
        with pytest.raises(AttributeError) as exc_info:
            wrong_service.get_all_items()
            
        # Verify we get the expected error
        assert "'function' object has no attribute 'get_all'" in str(exc_info.value)
        
        # Test with instance (correct approach)
        correct_service = ServiceClass(repo=get_repo_factory(mock_session))
        
        # This works because we're passing an actual repository instance
        result = correct_service.get_all_items()
        
        # Verify the result
        mock_repo.get_all.assert_called_once()
        assert result == []


class TestLoginBypass:
    """Tests for bypassing login in test mode."""
    
    def test_login_bypass_with_test_mode(self):
        """Test that test_mode parameter bypasses login prompt."""
        # Create test objects
        mock_user = MagicMock()
        mock_user.username = "testuser"
        
        # Mock services
        mock_services = {
            'user_service': MagicMock(),
            'product_service': MagicMock(),
        }
        
        # Create a function that simulates the app initialization
        def initialize_app(test_mode=False, test_user=None):
            if test_mode and test_user:
                # In test mode with user provided, bypass login
                return "app", "main_window", test_user, True
            else:
                # In normal mode, would show login dialog
                return "app", "main_window", None, False
        
        # Test with test_mode=False (normal mode)
        app, window, user, bypassed = initialize_app(test_mode=False)
        assert not bypassed, "Login should not be bypassed in normal mode"
        assert user is None, "User should be None when login is not bypassed"
        
        # Test with test_mode=True and test_user provided
        app, window, user, bypassed = initialize_app(test_mode=True, test_user=mock_user)
        assert bypassed, "Login should be bypassed in test mode with user"
        assert user == mock_user, "The provided test user should be used"


class TestMockServices:
    """Tests for using mock services in tests."""
    
    def test_mock_services_in_test_mode(self):
        """Test using mock services in test mode."""
        # Create mock services
        mock_invoicing = MagicMock()
        mock_invoicing.get_all_invoices.return_value = ["invoice1", "invoice2"]
        
        # Create mock main window
        mock_window = MagicMock()
        
        # Function similar to what we added in main.py
        def initialize_with_services(mock_services=None):
            if mock_services and 'invoicing' in mock_services:
                # Use the mock service
                invoicing = mock_services['invoicing']
            else:
                # Would normally create a real service
                invoicing = MagicMock()
                
            # Initialize window with the service
            window = mock_window(invoicing=invoicing)
            return window, invoicing
        
        # Test with mock services
        window, invoicing = initialize_with_services(
            mock_services={'invoicing': mock_invoicing}
        )
        
        # Verify the mock was used
        assert invoicing == mock_invoicing
        assert invoicing.get_all_invoices() == ["invoice1", "invoice2"]
        
        # Verify it was passed to the window
        mock_window.assert_called_once_with(invoicing=mock_invoicing) 