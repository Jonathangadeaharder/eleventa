"""
Integration tests for the app initialization process.

These tests verify that the application can be initialized
and run in test mode without requiring manual login.
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from main import main


class TestAppInitialization:
    """Tests for application initialization in test mode."""
    
    def test_app_initialization_with_test_user(self, test_user, mock_services, monkeypatch):
        """Test that the app can be initialized in test mode with a pre-authenticated user."""
        # Mock QApplication to prevent GUI creation
        mock_app = MagicMock()
        monkeypatch.setattr("PySide6.QtWidgets.QApplication", lambda *args: mock_app)
        
        # Run the application in test mode
        app, main_window = main(test_mode=True, test_user=test_user, mock_services=mock_services)
        
        # Verify that the application initialized correctly
        assert app is mock_app
        assert main_window is not None
        
        # Verify the user was passed to the main window
        # This assumes that MainWindow stores the user in self.current_user
        assert main_window.current_user == test_user
        
    def test_app_initialization_with_real_services(self, test_user, monkeypatch):
        """Test app initialization with real services but still in test mode."""
        # Mock QApplication to prevent GUI creation
        mock_app = MagicMock()
        monkeypatch.setattr("PySide6.QtWidgets.QApplication", lambda *args: mock_app)
        
        # Mock MainWindow to capture the passed services
        mock_window = MagicMock()
        mock_window_instance = MagicMock()
        mock_window.return_value = mock_window_instance
        monkeypatch.setattr("ui.main_window.MainWindow", mock_window)
        
        # Run the application in test mode without mock services
        app, main_window = main(test_mode=True, test_user=test_user)
        
        # Verify MainWindow was called with all expected services
        # We're just checking that the services were passed, not their exact types
        called_args = mock_window.call_args[1]
        
        assert 'logged_in_user' in called_args
        assert called_args['logged_in_user'] == test_user
        
        # Check all required services were passed
        required_services = [
            'product_service',
            'inventory_service',
            'sale_service',
            'customer_service',
            'purchase_service',
            'invoicing_service',
            'corte_service',
            'reporting_service'
        ]
        
        for service_name in required_services:
            assert service_name in called_args, f"Missing service: {service_name}"
            assert called_args[service_name] is not None, f"Service is None: {service_name}"


class TestIntegrationWithoutLoginPrompt:
    """Test running integration tests that would previously require login."""
    
    def test_invoicing_service_in_test_mode(self, test_user, monkeypatch):
        """
        Test the invoicing service in the main application.
        
        This test would previously require manual login, but now
        uses test_mode to bypass the login dialog.
        """
        # Mock QApplication to prevent GUI creation
        mock_app = MagicMock()
        monkeypatch.setattr("PySide6.QtWidgets.QApplication", lambda *args: mock_app)
        
        # Mock MainWindow to capture the invoicing_service
        mock_window = MagicMock()
        monkeypatch.setattr("ui.main_window.MainWindow", mock_window)
        
        # Create mock invoicing service with testable behavior
        mock_invoicing_service = MagicMock()
        mock_invoicing_service.get_all_invoices.return_value = []
        
        # Prepare mock services
        mock_services = {
            'product_service': MagicMock(),
            'inventory_service': MagicMock(),
            'sale_service': MagicMock(),
            'customer_service': MagicMock(),
            'purchase_service': MagicMock(),
            'invoicing_service': mock_invoicing_service,
            'corte_service': MagicMock(),
            'reporting_service': MagicMock(),
            'user_service': MagicMock()
        }
        
        # Run app in test mode
        app, main_window = main(test_mode=True, test_user=test_user, mock_services=mock_services)
        
        # Verify MainWindow was called with our mock invoicing service
        called_kwargs = mock_window.call_args[1]
        assert 'invoicing_service' in called_kwargs
        assert called_kwargs['invoicing_service'] == mock_invoicing_service
        
        # Call the get_all_invoices method to verify it works
        # (This is what would have failed with the original 'function' object error)
        invoicing_service = called_kwargs['invoicing_service']
        result = invoicing_service.get_all_invoices()
        
        # Verify the mock was called and returned expected value
        mock_invoicing_service.get_all_invoices.assert_called_once()
        assert result == [] 