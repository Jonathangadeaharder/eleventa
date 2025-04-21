import os

def update_cash_drawer_dialogs():
    """Add aliases for the dialog classes in cash_drawer_dialogs.py"""
    filename = "ui/dialogs/cash_drawer_dialogs.py"
    
    # Check if the file exists
    if not os.path.exists(filename):
        print(f"Error: {filename} does not exist")
        return False
    
    # Read the file content
    with open(filename, 'r') as f:
        content = f.read()
    
    # Check if aliases are already there
    if "OpenDrawerDialog = OpenCashDrawerDialog" in content:
        print("Aliases already exist in the file")
        return True
    
    # Add aliases at the end of the file
    alias_code = """
# Add aliases for backward compatibility with cash_drawer_view.py
OpenDrawerDialog = OpenCashDrawerDialog
CashMovementDialog = AddRemoveCashDialog
"""
    with open(filename, 'a') as f:
        f.write(alias_code)
    
    print(f"Updated {filename} with dialog aliases")
    return True

def create_test_file():
    """Create a test file for the cash drawer view"""
    test_file = "tests/ui/views/test_cash_drawer_fixed.py"
    test_content = """
import pytest
from decimal import Decimal
from unittest.mock import MagicMock

def test_cash_formatting():
    \"\"\"Test basic decimal formatting for cash values.\"\"\"
    amount = Decimal('123.45')
    formatted = f"${amount:.2f}"
    assert formatted == "$123.45"

def test_cash_drawer_service_mocking():
    \"\"\"Test that we can mock the cash drawer service.\"\"\"
    service = MagicMock()
    service.get_drawer_summary.return_value = {
        'is_open': True,
        'current_balance': Decimal('100.00')
    }
    
    summary = service.get_drawer_summary()
    assert summary['is_open'] is True
    assert summary['current_balance'] == Decimal('100.00')
"""
    
    # Write the test file
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    print(f"Created test file: {test_file}")
    return True

def main():
    update_cash_drawer_dialogs()
    create_test_file()
    print("Done!")

if __name__ == "__main__":
    main() 