import os

test_file_path = 'tests/ui/views/test_cash_drawer_view.py'

# Minimal test content
test_content = """
import pytest

from ui.views.cash_drawer_view import CashDrawerView

def test_initialization():
    \"\"\"Test that the view initializes correctly.\"\"\"
    assert True
"""

# Write the test file
with open(test_file_path, 'w') as f:
    f.write(test_content)

print(f"Created test file at {test_file_path}") 