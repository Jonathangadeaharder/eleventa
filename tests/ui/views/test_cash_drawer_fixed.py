
import pytest
from decimal import Decimal
from unittest.mock import MagicMock

def test_cash_formatting():
    """Test basic decimal formatting for cash values."""
    amount = Decimal('123.45')
    formatted = f"${amount:.2f}"
    assert formatted == "$123.45"

def test_cash_drawer_service_mocking():
    """Test that we can mock the cash drawer service."""
    service = MagicMock()
    service.get_drawer_summary.return_value = {
        'is_open': True,
        'current_balance': Decimal('100.00')
    }
    
    summary = service.get_drawer_summary()
    assert summary['is_open'] is True
    assert summary['current_balance'] == Decimal('100.00')
