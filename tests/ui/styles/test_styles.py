"""
Tests for the UI Styles module.
Focus: Style constants, helper functions, and style application.

This test suite verifies the functionality of the UI Styles module, including:
- Color and font constants availability
- Style templates for different UI components
- Style application to widgets
- Error handling for missing styles
"""

# Standard library imports
import sys
import os

# Add root directory to path 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Testing frameworks
import pytest
from unittest.mock import MagicMock, patch

# Qt components
from PySide6.QtWidgets import QPushButton, QLineEdit, QTableView, QGroupBox, QComboBox, QApplication
from PySide6.QtCore import Qt

# Application components
from ui.styles import COLORS, FONTS, STYLES, apply_style

# Apply timeout to all tests to prevent hanging
pytestmark = pytest.mark.timeout(5)

# Mock classes for testing
class MockWidget:
    """Mock widget for testing style application."""
    
    def __init__(self):
        self.style_sheet = ""
        
    def setStyleSheet(self, style_sheet):
        self.style_sheet = style_sheet
        
    def styleSheet(self):
        return self.style_sheet

# INITIALIZATION TESTS

def test_colors_constants():
    """
    Test that color constants are properly defined.
    
    Verifies that all expected color constants exist and have correct values.
    """
    # Check that essential colors exist
    assert 'primary' in COLORS
    assert 'secondary' in COLORS
    assert 'background' in COLORS
    assert 'border' in COLORS
    assert 'text' in COLORS
    assert 'error' in COLORS
    assert 'warning' in COLORS
    assert 'success' in COLORS
    
    # Check some specific color values
    assert COLORS['primary'] == '#2980b9'
    assert COLORS['error'] == '#e74c3c'
    assert COLORS['background'] == '#f5f5f5'

def test_fonts_constants():
    """
    Test that font constants are properly defined.
    
    Verifies that all expected font constants exist and have correct properties.
    """
    # Check that essential font types exist
    assert 'regular' in FONTS
    assert 'heading' in FONTS
    assert 'label' in FONTS
    assert 'button' in FONTS
    
    # Check that font properties exist
    assert 'family' in FONTS['regular']
    assert 'size' in FONTS['regular']
    assert 'weight' in FONTS['heading']
    
    # Check some specific font values
    assert FONTS['heading']['size'] == 12
    assert FONTS['heading']['weight'] == 'bold'
    assert 'Segoe UI' in FONTS['regular']['family']

def test_styles_templates():
    """
    Test that style templates are properly defined.
    
    Verifies that all expected style templates exist and contain the right CSS properties.
    """
    # Check that essential style templates exist
    assert 'button_primary' in STYLES
    assert 'button_secondary' in STYLES
    assert 'text_input' in STYLES
    assert 'dropdown' in STYLES
    assert 'table_view' in STYLES
    assert 'group_box' in STYLES
    
    # Check that style templates contain expected CSS
    assert 'background-color' in STYLES['button_primary']
    assert 'color: white' in STYLES['button_primary']
    assert 'border-radius' in STYLES['text_input']
    assert 'selection-background-color' in STYLES['table_view']

# FUNCTIONALITY TESTS

def test_apply_style_to_button():
    """
    Test applying a style to a button.
    
    Verifies that the apply_style function correctly applies a style template to a button.
    """
    # Create a mock button
    button = MockWidget()
    
    # Apply primary button style
    apply_style(button, 'button_primary')
    
    # Check that style was applied
    assert button.style_sheet == STYLES['button_primary']
    assert 'background-color' in button.style_sheet
    assert COLORS['primary'] in button.style_sheet

def test_apply_style_to_text_input():
    """
    Test applying a style to a text input.
    
    Verifies that the apply_style function correctly applies a style template to a text input.
    """
    # Create a mock text input
    text_input = MockWidget()
    
    # Apply text input style
    apply_style(text_input, 'text_input')
    
    # Check that style was applied
    assert text_input.style_sheet == STYLES['text_input']
    assert 'border-radius: 4px' in text_input.style_sheet

# ERROR HANDLING TESTS

def test_apply_style_invalid_style():
    """
    Test applying an invalid style.
    
    Verifies that the apply_style function raises a ValueError when an invalid style is requested.
    """
    # Create a mock widget
    widget = MockWidget()
    
    # Apply an invalid style
    with pytest.raises(ValueError) as excinfo:
        apply_style(widget, 'non_existent_style')
    
    # Check the error message
    assert "Style 'non_existent_style' not found" in str(excinfo.value)

# INTEGRATION TESTS

def test_style_integration_with_real_widgets(qtbot):
    """
    Test style integration with real Qt widgets.
    
    Verifies that styles can be applied to actual Qt widgets without errors.
    """
    widgets = []
    try:
        # Create real widgets with proper event handling
        button = QPushButton("Test Button")
        line_edit = QLineEdit()
        combo_box = QComboBox()
        group_box = QGroupBox("Test Group")
        
        # Track widgets for cleanup
        widgets = [button, line_edit, combo_box, group_box]
        
        # Add widgets to qtbot for proper event handling
        for widget in widgets:
            qtbot.addWidget(widget)
        
        # Process events to ensure widgets are ready
        QApplication.processEvents()
        qtbot.wait(50)  # Short wait to process pending events
        
        # Apply styles to widgets
        apply_style(button, 'button_primary')
        apply_style(line_edit, 'text_input')
        apply_style(combo_box, 'dropdown')
        apply_style(group_box, 'group_box')
        
        # Process events after style changes
        QApplication.processEvents()
        qtbot.wait(50)
        
        # Check that styles were applied (just verify they don't raise exceptions)
        assert button.styleSheet() != ""
        assert line_edit.styleSheet() != ""
        assert combo_box.styleSheet() != ""
        assert group_box.styleSheet() != ""
    
    finally:
        # Clean up resources
        for widget in widgets:
            try:
                widget.deleteLater()
            except:
                pass
        
        # Force process events for cleanup
        QApplication.processEvents()

def test_colors_in_style_templates():
    """
    Test that color constants are properly used in style templates.
    
    Verifies that style templates incorporate color constants correctly.
    """
    # Check primary color usage in button_primary style
    assert COLORS['primary'] in STYLES['button_primary']
    assert COLORS['primary_dark'] in STYLES['button_primary']
    
    # Check text color usage in button_secondary style
    assert COLORS['text'] in STYLES['button_secondary']
    assert COLORS['border'] in STYLES['button_secondary']
    
    # Check border color usage in text_input style
    assert COLORS['border'] in STYLES['text_input']
    assert COLORS['primary'] in STYLES['text_input'] 