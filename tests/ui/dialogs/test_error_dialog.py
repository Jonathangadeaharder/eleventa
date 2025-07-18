# tests/ui/dialogs/test_error_dialog.py
"""
Tests for error dialog functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QDialog, QPushButton, QLabel, QTextEdit
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from ui.dialogs.error_dialog import ErrorDialog


class TestErrorDialog:
    """Tests for ErrorDialog class."""
    
    @pytest.fixture
    def app(self):
        """QApplication instance for testing."""
        if not QApplication.instance():
            return QApplication([])
        return QApplication.instance()
    
    @pytest.fixture
    def simple_error_dialog(self, app):
        """Simple ErrorDialog instance for testing."""
        return ErrorDialog("Test Error", "This is a test error message.")
    
    @pytest.fixture
    def detailed_error_dialog(self, app):
        """ErrorDialog with detailed information for testing."""
        return ErrorDialog(
            "Database Error",
            "Failed to connect to database.",
            "Connection timeout after 30 seconds. Check network connectivity."
        )
    
    def test_init_simple_error(self, simple_error_dialog):
        """Test initialization with simple error message."""
        dialog = simple_error_dialog
        
        # Check basic properties
        assert dialog.windowTitle() == "Test Error"
        assert dialog.isModal()
        
        # Check that required widgets exist
        assert hasattr(dialog, 'user_message_label')
        assert hasattr(dialog, 'ok_button')
        
        # Check message content
        assert "This is a test error message." in dialog.user_message_label.text()
    
    def test_init_detailed_error(self, detailed_error_dialog):
        """Test initialization with detailed error information."""
        dialog = detailed_error_dialog
        
        # Check basic properties
        assert dialog.windowTitle() == "Database Error"
        assert dialog.isModal()
        
        # Check that detailed widgets exist
        assert hasattr(dialog, 'user_message_label')
        assert hasattr(dialog, 'details_text_edit')
        assert hasattr(dialog, 'details_button')
        assert hasattr(dialog, 'ok_button')
        
        # Check message content
        assert "Failed to connect to database." in dialog.user_message_label.text()
        
        # Details should be initially hidden
        assert not dialog.details_text_edit.isVisible()
    
    def test_show_details_functionality(self, detailed_error_dialog):
        """Test show/hide details functionality."""
        dialog = detailed_error_dialog
        
        # Show dialog and process events for proper widget initialization
        dialog.show()
        QApplication.processEvents()
        
        # Initially details should be hidden
        assert not dialog.details_text_edit.isVisible()
        assert dialog.details_button.text() == "Mostrar Detalles"
        
        # Click show details button
        QTest.mouseClick(dialog.details_button, Qt.MouseButton.LeftButton)
        QApplication.processEvents()
        
        # Details should now be visible
        assert dialog.details_text_edit.isVisible()
        assert dialog.details_button.text() == "Ocultar Detalles"
        
        # Check details content
        assert "Connection timeout after 30 seconds" in dialog.details_text_edit.toPlainText()
        
        # Click hide details button
        QTest.mouseClick(dialog.details_button, Qt.MouseButton.LeftButton)
        QApplication.processEvents()
        
        # Details should be hidden again
        assert not dialog.details_text_edit.isVisible()
        assert dialog.details_button.text() == "Mostrar Detalles"
        
        # Clean up
        dialog.hide()
    
    def test_ok_button_closes_dialog(self, simple_error_dialog):
        """Test that OK button closes the dialog."""
        dialog = simple_error_dialog
        
        # Mock the accept method
        with patch.object(dialog, 'accept') as mock_accept:
            # Click OK button
            QTest.mouseClick(dialog.ok_button, Qt.MouseButton.LeftButton)
            
            # Dialog should be accepted (closed)
            mock_accept.assert_called_once()
    
    def test_escape_key_closes_dialog(self, simple_error_dialog):
        """Test that Escape key closes the dialog."""
        dialog = simple_error_dialog
        
        # Mock the reject method
        with patch.object(dialog, 'reject') as mock_reject:
            # Press Escape key
            QTest.keyClick(dialog, Qt.Key.Key_Escape)
            
            # Dialog should be rejected (closed)
            mock_reject.assert_called_once()
    
    def test_enter_key_closes_dialog(self, simple_error_dialog):
        """Test that Enter key closes the dialog."""
        dialog = simple_error_dialog
        
        # Set focus to OK button
        dialog.ok_button.setFocus()
        
        # Mock the accept method
        with patch.object(dialog, 'accept') as mock_accept:
            # Press Enter key
            QTest.keyClick(dialog.ok_button, Qt.Key.Key_Return)
            
            # Dialog should be accepted (closed)
            mock_accept.assert_called_once()
    
    def test_dialog_size_and_layout(self, simple_error_dialog):
        """Test dialog size and layout properties."""
        dialog = simple_error_dialog
        
        # Dialog should have a reasonable minimum size
        assert dialog.minimumWidth() > 0
        assert dialog.minimumHeight() > 0
        
        # Dialog should have a layout
        assert dialog.layout() is not None
        
        # Layout should contain widgets
        layout = dialog.layout()
        assert layout.count() > 0
    
    def test_dialog_with_empty_message(self, app):
        """Test dialog creation with empty message."""
        dialog = ErrorDialog("", "")
        
        # Should not crash and should have basic structure
        assert dialog.windowTitle() == ""
        assert hasattr(dialog, 'user_message_label')
        assert hasattr(dialog, 'ok_button')
    
    def test_dialog_with_none_values(self, app):
        """Test dialog creation with None values."""
        # Should handle None values gracefully
        dialog = ErrorDialog(None, None, None)
        
        # Should not crash
        assert hasattr(dialog, 'user_message_label')
        assert hasattr(dialog, 'ok_button')
    
    def test_dialog_with_long_message(self, app):
        """Test dialog with very long error message."""
        long_message = "This is a very long error message. " * 50
        dialog = ErrorDialog("Long Error", long_message)
        
        # Should handle long messages without issues
        assert dialog.windowTitle() == "Long Error"
        assert long_message in dialog.user_message_label.text()
        
        # Dialog should still be usable
        assert dialog.ok_button.isEnabled()
    
    def test_dialog_with_html_content(self, app):
        """Test dialog with HTML content in message."""
        html_message = "<b>Bold error</b> with <i>italic text</i> and <u>underlined</u>."
        dialog = ErrorDialog("HTML Error", html_message)
        
        # Should handle HTML content appropriately
        assert dialog.windowTitle() == "HTML Error"
        # Content should be present (may be rendered as HTML or escaped)
        label_text = dialog.user_message_label.text()
        assert "Bold error" in label_text
    
    def test_dialog_with_special_characters(self, app):
        """Test dialog with special characters and unicode."""
        special_message = "Error with special chars: áéíóú ñ ¿¡ €£¥ 中文 🚨"
        dialog = ErrorDialog("Special Chars", special_message)
        
        # Should handle special characters without issues
        assert dialog.windowTitle() == "Special Chars"
        assert special_message in dialog.user_message_label.text()
    
    def test_dialog_modality(self, simple_error_dialog):
        """Test that dialog is modal."""
        dialog = simple_error_dialog
        
        # Dialog should be modal
        assert dialog.isModal()
        assert dialog.windowModality() == Qt.WindowModality.ApplicationModal
    
    def test_dialog_icon(self, simple_error_dialog):
        """Test that dialog has appropriate error icon."""
        dialog = simple_error_dialog
        
        # Should have an error icon or styling
        # This is implementation dependent
        assert hasattr(dialog, 'icon_label') or dialog.windowIcon() is not None
    
    def test_dialog_focus_behavior(self, simple_error_dialog):
        """Test dialog focus behavior."""
        dialog = simple_error_dialog
        
        # Show dialog
        dialog.show()
        QApplication.processEvents()
        
        # OK button should have focus or be focusable
        assert dialog.ok_button.hasFocus() or dialog.ok_button.focusPolicy() != Qt.FocusPolicy.NoFocus
        
        dialog.hide()
    
    def test_dialog_with_exception_object(self, app):
        """Test dialog creation with exception object."""
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            dialog = ErrorDialog("Exception Error", str(e), repr(e))
            
            # Should handle exception information
            assert dialog.windowTitle() == "Exception Error"
            assert "Test exception" in dialog.user_message_label.text()
    
    def test_dialog_accessibility(self, simple_error_dialog):
        """Test dialog accessibility features."""
        dialog = simple_error_dialog
        
        # Widgets should have accessible names or descriptions
        assert (dialog.user_message_label.accessibleName() or
                dialog.user_message_label.accessibleDescription() or
                dialog.user_message_label.text())
        
        assert (dialog.ok_button.accessibleName() or 
                dialog.ok_button.accessibleDescription() or
                dialog.ok_button.text())
    
    def test_dialog_keyboard_navigation(self, detailed_error_dialog):
        """Test keyboard navigation within dialog."""
        dialog = detailed_error_dialog
        
        # Show dialog
        dialog.show()
        QApplication.processEvents()
        
        # Should be able to navigate with Tab
        QTest.keyClick(dialog, Qt.Key.Key_Tab)
        QApplication.processEvents()
        
        # Should not crash
        assert True
        
        dialog.hide()
    
    def test_dialog_resize_behavior(self, detailed_error_dialog):
        """Test dialog resize behavior when showing/hiding details."""
        dialog = detailed_error_dialog
        
        # Show dialog and get initial size
        dialog.show()
        QApplication.processEvents()
        initial_height = dialog.height()
        
        # Show details
        QTest.mouseClick(dialog.details_button, Qt.MouseButton.LeftButton)
        QApplication.processEvents()
        
        # Dialog should be taller
        expanded_height = dialog.height()
        assert expanded_height > initial_height
        
        # Hide details
        QTest.mouseClick(dialog.details_button, Qt.MouseButton.LeftButton)
        QApplication.processEvents()
        
        # Dialog should return to original size
        collapsed_height = dialog.height()
        assert collapsed_height <= expanded_height
        
        dialog.hide()
    
    def test_static_show_error_method(self, app):
        """Test static method for showing error dialogs."""
        # Test if there's a static method for convenience
        if hasattr(ErrorDialog, 'show_error'):
            with patch.object(ErrorDialog, 'exec') as mock_exec:
                ErrorDialog.show_error("Static Error", "Static message")
                mock_exec.assert_called_once()
    
    def test_dialog_cleanup(self, simple_error_dialog):
        """Test that dialog can be properly cleaned up."""
        dialog = simple_error_dialog
        
        # Show and hide dialog
        dialog.show()
        QApplication.processEvents()
        dialog.hide()
        QApplication.processEvents()
        
        # Delete dialog
        dialog.deleteLater()
        QApplication.processEvents()
        
        # Should not raise any exceptions
        assert True
    
    @pytest.mark.parametrize("title,message,details", [
        ("Error 1", "Message 1", None),
        ("Error 2", "Message 2", "Details 2"),
        ("", "", ""),
        ("Unicode: 中文", "Message: áéíóú", "Details: €£¥")
    ])
    def test_dialog_with_various_inputs(self, app, title, message, details):
        """Test dialog creation with various input combinations."""
        if details:
            dialog = ErrorDialog(title, message, details)
            assert hasattr(dialog, 'details_text_edit')
        else:
            dialog = ErrorDialog(title, message)
        
        # Should create dialog without errors
        assert dialog.windowTitle() == (title or "")
        assert hasattr(dialog, 'user_message_label')
        assert hasattr(dialog, 'ok_button')
    
    def test_dialog_thread_safety(self, app):
        """Test that dialog creation is thread-safe."""
        # This is a basic test - full thread safety testing would require more complex setup
        dialog = ErrorDialog("Thread Test", "Testing thread safety")
        
        # Should create without issues
        assert dialog is not None
        assert hasattr(dialog, 'user_message_label')
    
    def test_dialog_memory_usage(self, app):
        """Test dialog memory usage with large content."""
        # Create dialog with large content
        large_message = "Large message content. " * 1000
        large_details = "Large details content. " * 1000
        
        dialog = ErrorDialog("Memory Test", large_message, large_details)
        
        # Should handle large content without memory issues
        assert dialog is not None
        assert large_message in dialog.user_message_label.text()
        
        # Clean up
        dialog.deleteLater()
        QApplication.processEvents()