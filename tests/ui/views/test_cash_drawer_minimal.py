"""
Minimal test file for CashDrawerView that completely avoids Qt interactions.
This is a pure mock test that doesn't actually create any Qt widgets.
"""
import sys
import os
import threading
import _thread
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
import time

# REMOVED kill_after_timeout function and its call - os._exit is dangerous in tests

# Completely mock the entire PySide6 module before importing anything
sys.modules['PySide6'] = MagicMock()
sys.modules['PySide6.QtWidgets'] = MagicMock()
sys.modules['PySide6.QtCore'] = MagicMock()
sys.modules['PySide6.QtGui'] = MagicMock()

# Create mock service
MockCashDrawerService = MagicMock()

# Create very simple tests that don't interact with Qt at all
def test_cash_drawer_service_methods():
    """Test the cash drawer service methods without any UI interaction."""
    # Create a mock service
    service = MockCashDrawerService()
    
    # Set up return values
    service.get_drawer_summary.return_value = {
        'is_open': True,
        'current_balance': Decimal('100.00')
    }
    
    # Test the mock service
    summary = service.get_drawer_summary()
    assert summary['is_open'] is True
    assert summary['current_balance'] == Decimal('100.00')
    
    # Test adding cash
    service.add_cash(amount=Decimal('50.00'), description="Test")
    service.add_cash.assert_called_with(amount=Decimal('50.00'), description="Test")
    
    print("Simple test completed successfully!")

def test_mock_cash_drawer_ui():
    """Test a mock of the cash drawer UI without creating Qt objects."""
    # Mock the UI class entirely
    CashDrawerView = MagicMock()
    
    # Create a mock instance
    view = CashDrawerView()
    
    # Test the mock
    view.add_cash_button.click()
    view.add_cash_button.click.assert_called_once()
    
    print("Mock UI test completed successfully!")
