import faulthandler
faulthandler.enable()

"""
Integration tests for the app initialization process.

These tests verify that the application can be initialized
and run in test mode without requiring manual login.
"""
import os
import sys
from unittest.mock import MagicMock, patch
import pytest

# Import from the tests.ui subpackage
from tests.ui.qt_test_utils import process_events

# If 'main' is in the project root, this should work if project_root is in sys.path
from main import main

from ui.main_window import MainWindow

@pytest.mark.integration
@pytest.mark.ui
class TestIntegrationWithoutLoginPrompt:
    """Test running integration tests that would previously require login."""
    
    def test_invoicing_service_in_test_mode(self, test_user, qtbot):
        """
        Test the invoicing service in the main application.
        
        This test would previously require manual login, but now
        uses test_mode to bypass the login dialog.
        """
        # Mock MainWindow to capture the invoicing_service
        mock_window_class = MagicMock(name="MockMainWindowClassForInvoicing")
        mock_window_instance = MagicMock(name="MockMainWindowInstanceForInvoicing")
        mock_window_class.return_value = mock_window_instance

        # Ensure the mock instance has a close method
        mock_window_instance.close = MagicMock()
        mock_window_instance.deleteLater = MagicMock()

        with patch("ui.main_window.MainWindow", mock_window_class):
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
            app, main_window_mock_ref = main(test_mode=True, test_user=test_user, mock_services=mock_services)

            # Verify MainWindow was called with our mock invoicing service
            mock_window_class.assert_called_once()
            called_kwargs = mock_window_class.call_args[1]
            assert 'invoicing_service' in called_kwargs
            assert called_kwargs['invoicing_service'] == mock_invoicing_service
        
            # Call the get_all_invoices method to verify it works
            invoicing_service = called_kwargs['invoicing_service']
            result = invoicing_service.get_all_invoices()
        
            # Verify the mock was called and returned expected value
            mock_invoicing_service.get_all_invoices.assert_called_once()
            assert result == []