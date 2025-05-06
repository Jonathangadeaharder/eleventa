"""
Tests for the DialogBase UI component.
Focus: Initialization, layout, button handling, validation, and error reporting.
"""

import sys
import pytest
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLineEdit, QLabel
from PySide6.QtCore import Qt
from unittest.mock import MagicMock, patch

from ui.dialogs.dialog_base import DialogBase
from tests.ui.qt_test_utils import process_events, safe_click_button

# Skip in general UI testing to avoid access violations
pytestmark = [
    pytest.mark.skipif("ui" in sys.argv, reason="Skip for general UI test runs to avoid access violations")
]

@pytest.fixture
def dialog(qtbot): # qtbot fixture is required for Qt widgets
    """Fixture to create a DialogBase instance."""
    dialog = DialogBase(title="Test Dialog")
    qtbot.addWidget(dialog)
    dialog.show()
    process_events()
    
    yield dialog
    
    dialog.hide()
    process_events()
    dialog.deleteLater()
    process_events()

def test_dialog_base_initialization(dialog, qtbot):
    """Test the initial state of the DialogBase."""
    assert dialog.windowTitle() == "Test Dialog"
    # Check if the help button flag is removed
    assert not (dialog.windowFlags() & Qt.WindowContextHelpButtonHint)
    assert dialog.minimumWidth() >= 400
    assert dialog.isSizeGripEnabled()
    assert dialog.main_layout is not None
    assert dialog.content_frame is not None
    assert dialog.content_layout is not None
    assert dialog.button_box is not None
    assert isinstance(dialog.button_box, QDialogButtonBox)
    # Check default buttons
    assert dialog.button_box.standardButtons() == (QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

def test_dialog_base_add_form_row(dialog, qtbot):
    """Test adding a form row."""
    test_label = "My Input:"
    test_widget = QLineEdit()
    dialog.add_form_row(test_label, test_widget)
    
    # Check if the layout was added to content_layout
    layout_item = dialog.content_layout.itemAt(dialog.content_layout.count() - 1)
    assert layout_item is not None
    row_layout = layout_item.layout()
    assert row_layout is not None
    
    # Check label and widget within the row layout
    label_widget = row_layout.itemAt(0).widget()
    input_widget = row_layout.itemAt(1).widget()
    assert isinstance(label_widget, QLabel)
    assert label_widget.text() == test_label
    assert label_widget.minimumWidth() >= 120 # Check minimum width set
    assert input_widget == test_widget

def test_dialog_base_get_buttons(dialog, qtbot):
    """Test getting the OK and Cancel buttons."""
    ok_button = dialog.get_ok_button()
    cancel_button = dialog.get_cancel_button()
    assert ok_button is not None
    assert ok_button == dialog.button_box.button(QDialogButtonBox.StandardButton.Ok)
    assert cancel_button is not None
    assert cancel_button == dialog.button_box.button(QDialogButtonBox.StandardButton.Cancel)

def test_dialog_base_set_button_text(dialog, qtbot):
    """Test setting the text of standard buttons."""
    new_ok_text = "Aceptar"
    new_cancel_text = "Cancelar"
    dialog.set_button_text(QDialogButtonBox.StandardButton.Ok, new_ok_text)
    dialog.set_button_text(QDialogButtonBox.StandardButton.Cancel, new_cancel_text)
    
    assert dialog.get_ok_button().text() == new_ok_text
    assert dialog.get_cancel_button().text() == new_cancel_text

def test_dialog_base_set_button_text_invalid_button(dialog, qtbot):
    """Test setting text for a button type not present."""
    # Attempt to set text for a 'Help' button which isn't there by default
    # This should not raise an error, just do nothing.
    try:
        dialog.set_button_text(QDialogButtonBox.StandardButton.Help, "Ayuda")
    except Exception as e:
        pytest.fail(f"set_button_text raised an unexpected exception: {e}")

# --- Tests for validate_and_accept --- 

def test_validate_and_accept_success(dialog, qtbot):
    """Test validate_and_accept when validation succeeds."""
    dialog.validate = MagicMock(return_value=True)
    dialog.accept = MagicMock()
    
    dialog.validate_and_accept()
    
    dialog.validate.assert_called_once()
    dialog.accept.assert_called_once()

def test_validate_and_accept_failure_returns_false(dialog, qtbot):
    """Test validate_and_accept when validation returns False."""
    dialog.validate = MagicMock(return_value=False)
    dialog.accept = MagicMock()
    
    dialog.validate_and_accept()
    
    dialog.validate.assert_called_once()
    dialog.accept.assert_not_called()

@patch('ui.dialogs.dialog_base.show_error_message')
def test_validate_and_accept_failure_raises_value_error(mock_show_error, dialog, qtbot):
    """Test validate_and_accept when validation raises ValueError."""
    error_message = "Invalid input!"
    dialog.validate = MagicMock(side_effect=ValueError(error_message))
    dialog.accept = MagicMock()
    
    dialog.validate_and_accept()
    
    dialog.validate.assert_called_once()
    dialog.accept.assert_not_called()
    mock_show_error.assert_called_once_with(dialog, "Error de validación", error_message)

def test_dialog_base_default_validate(dialog, qtbot):
    """Test the default validate method returns True."""
    assert dialog.validate() is True

def test_dialog_base_button_connections(dialog, qtbot):
    """Verify the button signals are connected correctly using direct signal calls.
    
    This is a safer approach than using mouse clicks, which can cause access violations.
    """
    # Mock the target methods
    dialog.validate_and_accept = MagicMock()
    dialog.reject = MagicMock()
    
    # Get the buttons
    ok_button = dialog.get_ok_button()
    cancel_button = dialog.get_cancel_button()
    
    # Directly trigger the clicked signals
    ok_button.clicked.emit()
    process_events()
    cancel_button.clicked.emit()
    process_events()
    
    # Assert the connected methods were called
    dialog.validate_and_accept.assert_called_once()
    dialog.reject.assert_called_once()
