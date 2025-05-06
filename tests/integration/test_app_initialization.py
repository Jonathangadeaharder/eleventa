"""
Integration tests for the app initialization process.

These tests verify that the application can be initialized
and run in test mode without requiring manual login.
"""
import os
import sys

import pytest
from unittest.mock import patch, MagicMock
import PySide6.QtWidgets

# Add project root to path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from main import main
# Import process_events from qt_test_utils
sys.path.insert(0, os.path.join(project_root, "tests", "ui"))
from qt_test_utils import process_events

@pytest.fixture(autouse=True)
def mock_qapplication(monkeypatch):
    # Always destroy any existing QApplication instance before creating a new one
    if hasattr(PySide6.QtWidgets.QApplication, 'instance'):
        app = PySide6.QtWidgets.QApplication.instance()
        if app is not None:
            app.quit()
            del app
    monkeypatch.setattr(PySide6.QtWidgets, "QApplication", MagicMock())
    import main
    monkeypatch.setattr(main, "QApplication", MagicMock())


@pytest.mark.integration
class TestAppInitialization:
    """Tests for application initialization in test mode."""
    
    def test_app_initialization_with_test_user(self, test_user, mock_services):
        """Test that the app can be initialized in test mode with a pre-authenticated user."""
        app = None
        main_window = None
        
        try:
            # Run the application in test mode
            app, main_window = main(test_mode=True, test_user=test_user, mock_services=mock_services)
            
            # Verify that the application initialized correctly
            assert app is not None, "App should not be None"
            assert main_window is not None, "Main window should not be None"
            
            # Verify the user was passed to the main window
            assert main_window.current_user == test_user, "Incorrect user passed to main window"
            
        except Exception as e:
            pytest.fail(f"Test failed with exception: {str(e)}")
        finally:
            # Ensure cleanup happens properly, even if assertions fail
            if main_window is not None:
                try:
                    main_window.close()
                    process_events()
                    main_window.deleteLater()
                    process_events()
                except Exception as e:
                    # Log but don't fail the test on cleanup errors
                    print(f"Warning: Cleanup error: {str(e)}")
            
            if app is not None:
                try:
                    app.quit()
                except Exception as e:
                    print(f"Warning: App cleanup error: {str(e)}")
        
    def test_app_initialization_with_real_services(self, test_user):
        """Test app initialization with real services but still in test mode."""
        # Mock MainWindow to capture the passed services
        mock_window = MagicMock()
        mock_window_instance = MagicMock()
        mock_window.return_value = mock_window_instance
        from unittest.mock import patch
        with patch("ui.main_window.MainWindow", mock_window):
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
    
    def test_invoicing_service_in_test_mode(self, test_user):
        """
        Test the invoicing service in the main application.
        
        This test would previously require manual login, but now
        uses test_mode to bypass the login dialog.
        """
        # Mock MainWindow to capture the invoicing_service
        mock_window = MagicMock()
        with patch("ui.main_window.MainWindow", mock_window):
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