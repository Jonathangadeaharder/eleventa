"""
Tests for cash utility functions used in cash drawer operations.
"""

import pytest
from decimal import Decimal
from unittest.mock import patch

# Set marker to timeout tests after 3 seconds
pytestmark = pytest.mark.timeout(3)

def test_format_currency():
    """Test currency formatting function."""
    from ui.views.cash_drawer_view import format_currency
    
    # Test with different values
    assert format_currency(Decimal('100.00')) == "$100.00"
    assert format_currency(Decimal('1234.56')) == "$1,234.56"
    assert format_currency(Decimal('0.50')) == "$0.50"
    assert format_currency(Decimal('-25.75')) == "-$25.75"

def test_parse_currency_input():
    """Test parsing currency input."""
    from ui.views.cash_drawer_view import parse_currency_input
    
    # Test valid inputs
    assert parse_currency_input("100") == Decimal('100.00')
    assert parse_currency_input("100.5") == Decimal('100.50')
    assert parse_currency_input("1,234.56") == Decimal('1234.56')
    
    # Test invalid inputs
    with pytest.raises(ValueError):
        parse_currency_input("abc")
    with pytest.raises(ValueError):
        parse_currency_input("")

def test_calculate_cash_difference():
    """Test calculating cash difference between expected and actual amounts."""
    from ui.views.cash_drawer_view import calculate_difference
    
    assert calculate_difference(Decimal('100.00'), Decimal('100.00')) == Decimal('0.00')
    assert calculate_difference(Decimal('150.00'), Decimal('100.00')) == Decimal('50.00')
    assert calculate_difference(Decimal('50.00'), Decimal('100.00')) == Decimal('-50.00') 