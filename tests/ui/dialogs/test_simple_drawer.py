"""
Tests for simple mocking of the CashDrawerTableModel in the dialogs context.
Focus: Ensures that mocks with a spec of the model can be created and validated.
"""

import pytest
from unittest.mock import MagicMock

from ui.models.cash_drawer_model import CashDrawerTableModel

def test_mock_with_spec():
    """Test that we can create a mock with a spec of CashDrawerTableModel."""
    mock_model_instance = MagicMock(spec=CashDrawerTableModel)
    assert isinstance(mock_model_instance, MagicMock)
    assert mock_model_instance._spec_class == CashDrawerTableModel
