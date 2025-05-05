"""
Minimal test file to ensure the basic UI can be loaded and closed properly.
"""

import pytest
from unittest.mock import MagicMock, patch

pytestmark = pytest.mark.timeout(3)

def test_view_loads_and_closes(qtbot):
    """Test that the view can be instantiated and closed without errors."""
    # Removed setModel patch
    from ui.views.cash_drawer_view import CashDrawerView
    from core.services.cash_drawer_service import CashDrawerService
    
    # Create mock service
    mock_service = MagicMock(spec=CashDrawerService)
    # Provide a more complete summary, even if minimal, to avoid potential None errors in the view
    mock_service.get_drawer_summary.return_value = {
        'is_open': False, 
        'current_balance': 0,
        'initial_amount': 0,
        'total_in': 0,
        'total_out': 0,
        'entries_today': [],
        'opened_at': None,
        'opened_by': None
    }
    
    # Create view
    view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
    qtbot.addWidget(view)
    
    # Check that view was created
    assert view is not None
    assert hasattr(view, 'open_button')
    
    # Close view
    view.close()
    view.deleteLater()
