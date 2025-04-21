import pytest
from decimal import Decimal
from unittest.mock import MagicMock

def test_cash_formatting():
    amount = Decimal('123.45')
    formatted = f"${amount:.2f}"
    assert formatted == "$123.45"

def test_mock_service():
    service = MagicMock()
    service.get_value.return_value = 42
    assert service.get_value() == 42
