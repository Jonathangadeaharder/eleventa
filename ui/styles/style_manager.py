from typing import Optional
from PySide6.QtWidgets import QWidget
from . import STYLES, apply_style


class StyleManager:
    """Manager for applying styles to UI components."""
    
    # Style mappings for different component types
    STYLE_MAPPINGS = {
        'dialog': 'group_box',
        'button_primary': 'button_primary',
        'button_secondary': 'button_secondary',
        'text_input': 'text_input',
        'dropdown': 'dropdown',
        'table': 'table_view',
        'group_box': 'group_box'
    }
    
    @classmethod
    def apply_style(cls, widget: QWidget, style_type: str) -> None:
        """Apply a style to a widget.
        
        Args:
            widget: The widget to style
            style_type: The type of style to apply
            
        Raises:
            ValueError: If the style type is not found
        """
        try:
            # Map the style type to the actual style name
            style_name = cls.STYLE_MAPPINGS.get(style_type, style_type)
            
            if style_name in STYLES:
                apply_style(widget, style_name)
            else:
                # If no specific style found, apply a basic style
                cls._apply_basic_style(widget)
        except Exception:
            # Silently fail if styling doesn't work
            pass
    
    @classmethod
    def _apply_basic_style(cls, widget: QWidget) -> None:
        """Apply a basic style to a widget."""
        basic_style = """
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 10pt;
            }
            QLabel {
                color: #333333;
            }
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                background-color: white;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
            }
        """
        widget.setStyleSheet(basic_style)
    
    @classmethod
    def get_color(cls, color_name: str) -> str:
        """Get a color value by name.
        
        Args:
            color_name: The name of the color
            
        Returns:
            The color value as a string
        """
        from . import COLORS
        return COLORS.get(color_name, '#000000')
    
    @classmethod
    def get_font_style(cls, font_type: str) -> str:
        """Get a font style by type.
        
        Args:
            font_type: The type of font (regular, heading, label, button)
            
        Returns:
            CSS font style string
        """
        from . import FONTS
        font_config = FONTS.get(font_type, FONTS['regular'])
        
        style = f"font-family: {font_config['family']}; font-size: {font_config['size']}pt;"
        
        if 'weight' in font_config:
            style += f" font-weight: {font_config['weight']};"
            
        return style