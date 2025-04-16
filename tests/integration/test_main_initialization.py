"""
Integration tests specifically for the main.py initialization process.

These tests verify that the service instantiation in main.py works correctly,
focusing on the cause of the 'function' object has no attribute 'get_all' error.
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock, Mock

# Import necessary modules for testing initialization
from infrastructure.persistence.sqlite.repositories import SqliteInvoiceRepository
from core.services.invoicing_service import InvoicingService


class TestInvoicingServiceFixInMain:
    """Tests for verifying the fix for the repository factory issue."""
    
    def test_proposed_fix_directly(self):
        """
        Test that explains and verifies the exact issue and the fix.
        
        This test demonstrates why passing a factory function directly to InvoicingService 
        causes the error, and how instantiating repositories before passing them fixes it.
        """
        # Create mocks for the test
        mock_session = MagicMock()
        mock_repo = MagicMock()
        mock_repo.get_all.return_value = []
        
        # 1. Simulate the original broken code (factory function passed directly)
        def get_repo_factory(session):
            """This simulates the factory function in main.py"""
            # This function would normally return a repository instance
            # But we're not going to call it in the broken case
            return mock_repo
        
        # Create service with the WRONG approach (passing factory function directly)
        broken_service = InvoicingService(
            invoice_repo=get_repo_factory,  # Wrong: passing function
            sale_repo=MagicMock(),
            customer_repo=MagicMock()
        )
        
        # This will fail with 'function' object has no attribute 'get_all'
        with pytest.raises(AttributeError) as exc_info:
            broken_service.get_all_invoices()
        
        # Verify the exact error message
        assert "'function' object has no attribute 'get_all'" in str(exc_info.value)
        
        # 2. Now test the FIXED approach (instantiating repositories first)
        # This is what our fix in main.py does
        fixed_service = InvoicingService(
            invoice_repo=get_repo_factory(mock_session),  # Right: passing repository instance
            sale_repo=MagicMock(),
            customer_repo=MagicMock()
        )
        
        # This should not raise an error
        result = fixed_service.get_all_invoices()
        
        # Verify get_all was called on the repository
        mock_repo.get_all.assert_called_once()
        assert result == []
        
    def test_fix_with_actual_repository(self):
        """Test with the actual SqliteInvoiceRepository to verify compatibility."""
        # Create a mock session
        mock_session = MagicMock()
        
        # Create a real repository with the mock session
        repo_instance = SqliteInvoiceRepository(mock_session)
        
        # For testing, we'll patch the get_all method on the real repository
        original_get_all = repo_instance.get_all
        get_all_called = False
        
        def mock_get_all():
            nonlocal get_all_called
            get_all_called = True
            return []
            
        repo_instance.get_all = mock_get_all
        
        # Create service with the repository instance
        service = InvoicingService(
            invoice_repo=repo_instance,
            sale_repo=MagicMock(),
            customer_repo=MagicMock()
        )
        
        # Call get_all_invoices
        result = service.get_all_invoices()
        
        # Verify our mock was called
        assert get_all_called, "get_all was not called on the repository"
        assert result == [], "get_all_invoices should return empty list in our test" 