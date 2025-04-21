import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel, QLineEdit, QDialogButtonBox
from ui.dialogs.dialog_base import DialogBase


@pytest.fixture
def qapp():
    """Fixture providing QApplication instance"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # No clean up needed


@pytest.fixture
def mock_dialog_base(qapp):
    """Fixture that returns a DialogBase instance with mocked methods"""
    
    class ConcreteDialog(DialogBase):
        def __init__(self):
            super().__init__("Test Dialog")
            
            # Create a simple layout
            self.name_input = QLineEdit()
            self.add_form_row("Name:", self.name_input)
            
            # Add custom buttons
            self.ok_button = self.get_ok_button()
            self.cancel_button = self.get_cancel_button()
            
            # Set custom button text
            self.set_button_text(QDialogButtonBox.StandardButton.Ok, "Save")
            
        def setup_ui(self):
            """Implement abstract method"""
            pass
            
        def connect_signals(self):
            """Implement abstract method"""
            pass
            
        def validate(self):
            """Override validate method for testing"""
            if not self.name_input.text():
                raise ValueError("Name cannot be empty")
            return True
    
    # Create the dialog
    dialog = ConcreteDialog()
    
    # Mock methods to avoid actual execution
    dialog.exec = MagicMock(return_value=1)  # Return accepted (1)
    
    # Mock show_error_message to avoid actual dialog display
    with patch('ui.dialogs.dialog_base.show_error_message') as mock:
        dialog._error_mock = mock
        yield dialog


def test_dialog_initialization(mock_dialog_base):
    """Test initialization of DialogBase"""
    assert mock_dialog_base.windowTitle() == "Test Dialog"
    assert isinstance(mock_dialog_base.layout(), QVBoxLayout)
    assert len(mock_dialog_base.findChildren(QPushButton)) == 2


def test_dialog_accept(mock_dialog_base):
    """Test accept method"""
    # Setup spy for validate_and_accept method
    mock_dialog_base.validate_and_accept = MagicMock()
    
    # Add text to pass validation
    mock_dialog_base.name_input.setText("Test Name")
    
    # Simulate clicking OK button
    mock_dialog_base.ok_button.click()
    
    # Check if validate_and_accept was called
    mock_dialog_base.validate_and_accept.assert_called_once()


def test_dialog_reject(mock_dialog_base):
    """Test reject method"""
    # Setup spy for reject method
    original_reject = mock_dialog_base.reject
    mock_dialog_base.reject = MagicMock(wraps=original_reject)
    
    # Simulate clicking Cancel button
    mock_dialog_base.cancel_button.click()
    
    # Check if reject was called
    mock_dialog_base.reject.assert_called_once()


def test_exec_method(mock_dialog_base):
    """Test exec method"""
    result = mock_dialog_base.exec()
    assert result == 1  # Should return the mocked value
    mock_dialog_base.exec.assert_called_once()


def test_setup_ui_abstract(mock_dialog_base):
    """Test that the setup_ui method can be called"""
    mock_dialog_base.setup_ui()


def test_connect_signals_abstract(mock_dialog_base):
    """Test that the connect_signals method can be called"""
    mock_dialog_base.connect_signals()


def test_add_form_row(mock_dialog_base, qapp):
    """Test add_form_row method"""
    # Arrange
    test_label = "Test:"
    test_widget = QLineEdit()
    
    # Act
    row_layout = mock_dialog_base.add_form_row(test_label, test_widget)
    
    # Assert
    # Check that the row layout has 2 items (label and widget)
    assert row_layout.count() == 2
    
    # Check the label text
    label_item = row_layout.itemAt(0)
    assert isinstance(label_item.widget(), QLabel)
    assert label_item.widget().text() == test_label
    
    # Check the widget
    widget_item = row_layout.itemAt(1)
    assert widget_item.widget() == test_widget


def test_validate_and_accept_success(mock_dialog_base):
    """Test validate_and_accept with valid input"""
    # Arrange
    mock_dialog_base.validate = MagicMock(return_value=True)
    mock_dialog_base.accept = MagicMock()
    
    # Act
    mock_dialog_base.validate_and_accept()
    
    # Assert
    mock_dialog_base.validate.assert_called_once()
    mock_dialog_base.accept.assert_called_once()
    mock_dialog_base._error_mock.assert_not_called()


def test_validate_and_accept_failure(mock_dialog_base):
    """Test validate_and_accept with invalid input"""
    # Arrange
    error_message = "Validation error"
    mock_dialog_base.validate = MagicMock(side_effect=ValueError(error_message))
    mock_dialog_base.accept = MagicMock()
    
    # Act
    mock_dialog_base.validate_and_accept()
    
    # Assert
    mock_dialog_base.validate.assert_called_once()
    mock_dialog_base.accept.assert_not_called()
    mock_dialog_base._error_mock.assert_called_once()
    # Check error message is passed to the error dialog
    assert error_message in mock_dialog_base._error_mock.call_args[0][2]


def test_validate_default_implementation():
    """Test default validate implementation"""
    # Create a basic DialogBase instance without overriding validate
    class BasicDialog(DialogBase):
        def setup_ui(self):
            pass
            
        def connect_signals(self):
            pass
    
    base_dialog = BasicDialog("Base Dialog")
    
    # The base implementation should always return True
    assert base_dialog.validate() is True


def test_get_buttons(mock_dialog_base):
    """Test get_ok_button and get_cancel_button methods"""
    # Test get_ok_button
    ok_button = mock_dialog_base.get_ok_button()
    assert ok_button is not None
    assert ok_button.text() == "Save"  # We set this text in the fixture
    
    # Test get_cancel_button
    cancel_button = mock_dialog_base.get_cancel_button()
    assert cancel_button is not None
    assert cancel_button.text() == "Cancel"


def test_set_button_text(mock_dialog_base):
    """Test set_button_text method"""
    # Arrange
    new_text = "Custom Text"
    
    # Act - set new text for Cancel button
    mock_dialog_base.set_button_text(QDialogButtonBox.StandardButton.Cancel, new_text)
    
    # Assert
    cancel_button = mock_dialog_base.get_cancel_button()
    assert cancel_button.text() == new_text
    
    # Test with button that doesn't exist
    # This should not raise an error
    mock_dialog_base.set_button_text(QDialogButtonBox.StandardButton.Help, "Help Text")


def test_validation_integration(qapp):
    """Integration test for validation flow"""
    # Create a concrete dialog for this test
    class ValidationTestDialog(DialogBase):
        def __init__(self):
            super().__init__("Validation Test")
            self.input = QLineEdit()
            self.add_form_row("Field:", self.input)
            
        def validate(self):
            if not self.input.text():
                raise ValueError("Field cannot be empty")
            return True
    
    # Create dialog and mock error message
    dialog = ValidationTestDialog()
    with patch('ui.dialogs.dialog_base.show_error_message') as mock_error:
        # Empty input - should fail validation
        dialog.validate_and_accept()
        mock_error.assert_called_once()
        
        # Reset mock
        mock_error.reset_mock()
        
        # Valid input - should pass validation
        dialog.input.setText("Valid input")
        with patch.object(dialog, 'accept') as mock_accept:
            dialog.validate_and_accept()
            mock_accept.assert_called_once()
            mock_error.assert_not_called() 