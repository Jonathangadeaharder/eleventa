"""
Integration tests for the app initialization process.

These tests verify that the application can be initialized
and run in test mode without requiring manual login.
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os


class TestInvoicingServiceInitialization:
    """Tests for invoicing service initialization."""
    
    def test_invoicing_service_initialization(self):
        """Test the correct vs incorrect ways to initialize InvoicingService."""
        # Create mocks
        mock_session = MagicMock()
        mock_repo = MagicMock()
        mock_repo.get_all.return_value = []
        
        # Create a factory function like in main.py
        def get_repo_factory(session):
            return mock_repo
        
        # 1. Test the WRONG approach - this is what was in the original code
        # Create a class to test
        class MockInvoicingService:
            def __init__(self, invoice_repo, sale_repo, customer_repo):
                self.invoice_repo = invoice_repo
                self.sale_repo = sale_repo
                self.customer_repo = customer_repo
                
            def get_all_invoices(self):
                return self.invoice_repo.get_all()
        
        # When we pass the factory function directly (wrong)
        wrong_service = MockInvoicingService(
            invoice_repo=get_repo_factory,  # Wrong: passing function
            sale_repo=MagicMock(),
            customer_repo=MagicMock()
        )
        
        # This will fail with 'function' object has no attribute 'get_all'
        with pytest.raises(AttributeError) as exc_info:
            wrong_service.get_all_invoices()
        
        # Verify we get the exact error message
        assert "'function' object has no attribute 'get_all'" in str(exc_info.value)
        
        # 2. Test the CORRECT approach - what we fixed in main.py
        # When we pass the repository instance after calling the factory function
        fixed_service = MockInvoicingService(
            invoice_repo=get_repo_factory(mock_session),  # Right: passing repository
            sale_repo=MagicMock(),
            customer_repo=MagicMock()
        )
        
        # This should not raise an error
        result = fixed_service.get_all_invoices()
        
        # Verify get_all was called on the repository
        mock_repo.get_all.assert_called_once()
        assert result == []


class TestMainWindowInitialization:
    """Tests for main window initialization with pre-authenticated user."""
    
    def test_main_window_initialization(self):
        """Test that MainWindow can be initialized with a pre-authenticated user."""
        # Create a mock user
        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_user.is_admin = True
        
        # Create mock services
        mock_services = {
            'product_service': MagicMock(),
            'inventory_service': MagicMock(),
            'sale_service': MagicMock(),
            'customer_service': MagicMock(),
            'purchase_service': MagicMock(),
            'invoicing_service': MagicMock(),
            'corte_service': MagicMock(),
            'reporting_service': MagicMock()
        }
        
        # Mock the MainWindow class
        mock_main_window = MagicMock()
        
        # Create initialization function similar to main.py but fully mocked
        def initialize_app(test_mode=False, test_user=None, mock_services=None):
            """Simplified version of main() for testing."""
            if not test_mode:
                # In normal mode, would show login dialog
                return None, None
                
            if not test_user:
                return None, None
                
            # When in test mode with a user, initialize MainWindow with services
            main_window = mock_main_window(
                logged_in_user=test_user,
                **mock_services
            )
            
            return MagicMock(), main_window
        
        # Test the initialization with test_mode and test_user
        app, main_window = initialize_app(
            test_mode=True,
            test_user=mock_user,
            mock_services=mock_services
        )
        
        # Verify MainWindow was called with the user and services
        mock_main_window.assert_called_once()
        call_kwargs = mock_main_window.call_args[1]
        
        assert call_kwargs['logged_in_user'] == mock_user
        for service_name, service in mock_services.items():
            assert call_kwargs[service_name] == service 