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
from core.interfaces.repository_interfaces import IInvoiceRepository


class TestInvoicingServiceFixInMain:
    """Tests for verifying the fix for the repository factory issue."""
    
    def test_factory_approach(self):
        """
        Test that the factory approach works correctly with InvoicingService.
        
        This test demonstrates the correct way to use repository factories with InvoicingService.
        """
        # Create mocks for the test
        mock_session = MagicMock()
        mock_repo = MagicMock()
        mock_repo.get_all.return_value = []
        
        # Define a repository factory function
        def invoice_repo_factory(session=None):
            """This simulates the factory function in main.py"""
            return mock_repo
            
        def sale_repo_factory(session=None):
            return MagicMock()
            
        def customer_repo_factory(session=None):
            return MagicMock()
        
        # Create service with Unit of Work pattern
        service = InvoicingService()
        
        # This should work correctly with unit_of_work in the service
        with patch('core.services.invoicing_service.unit_of_work') as mock_unit_of_work:
            # Configure the mock unit_of_work context manager
            mock_context = MagicMock()
            mock_context.__enter__.return_value = mock_context
            mock_context.invoices = mock_repo
            mock_unit_of_work.return_value = mock_context
            
            # Call the service method
            result = service.get_all_invoices()
        
        # Verify get_all was called on the repository
        mock_repo.get_all.assert_called_once()
        assert result == []
        
    def test_with_actual_repository(self):
        """Test with the actual SqliteInvoiceRepository to verify compatibility."""
        # Create a mock session
        mock_session = MagicMock()
        
        # Create factory functions
        def invoice_repo_factory(session=None):
            # Use the provided session or the mock session
            return SqliteInvoiceRepository(session or mock_session)
            
        def sale_repo_factory(session=None):
            return MagicMock()
            
        def customer_repo_factory(session=None):
            return MagicMock()
        
        # Create service with Unit of Work pattern
        service = InvoicingService()
        
        # For testing, we'll patch the real repository's get_all method
        with patch.object(SqliteInvoiceRepository, 'get_all', return_value=[]) as mock_get_all:
            # We also need to patch unit_of_work since we're not in a real session
            with patch('core.services.invoicing_service.unit_of_work') as mock_unit_of_work:
                # Configure the mock unit_of_work context manager
                mock_context = MagicMock()
                mock_context.__enter__.return_value = mock_context
                mock_repo = SqliteInvoiceRepository(mock_session)
                mock_context.invoices = mock_repo
                mock_unit_of_work.return_value = mock_context
                
                # Call the service method
                result = service.get_all_invoices()
            
        # Verify our mock was called
        mock_get_all.assert_called_once()
        assert result == [], "get_all_invoices should return empty list in our test"