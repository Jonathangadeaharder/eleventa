# UI Style constants and helper functions

# Color constants
COLORS = {
    'primary': '#2980b9',
    'primary_dark': '#1c638f',
    'secondary': '#27ae60', 
    'secondary_dark': '#1e8449',
    'background': '#f5f5f5',
    'border': '#d0d0d0',
    'text': '#333333',
    'text_light': '#777777',
    'error': '#e74c3c',
    'warning': '#f39c12',
    'success': '#2ecc71',
    'highlight': '#f1c40f',
}

# Fonts
FONTS = {
    'regular': {
        'family': 'Segoe UI, Arial, sans-serif',
        'size': 10,
    },
    'heading': {
        'family': 'Segoe UI, Arial, sans-serif',
        'size': 12,
        'weight': 'bold',
    },
    'label': {
        'family': 'Segoe UI, Arial, sans-serif',
        'size': 10,
        'weight': 'normal',
    },
    'button': {
        'family': 'Segoe UI, Arial, sans-serif',
        'size': 10,
        'weight': 'normal',
    },
}

# Styling for specific widgets
STYLES = {
    'button_primary': f"""
        QPushButton {{
            background-color: {COLORS['primary']};
            color: white;
            border: 1px solid {COLORS['primary_dark']};
            border-radius: 4px;
            padding: 6px 12px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {COLORS['primary_dark']};
        }}
        QPushButton:pressed {{
            background-color: {COLORS['primary_dark']};
            border: 1px solid {COLORS['primary']};
        }}
        QPushButton:disabled {{
            background-color: #cccccc;
            color: #666666;
            border: 1px solid #bbbbbb;
        }}
    """,
    
    'button_secondary': f"""
        QPushButton {{
            background-color: white;
            color: {COLORS['text']};
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            padding: 6px 12px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['background']};
        }}
        QPushButton:pressed {{
            background-color: {COLORS['background']};
            border: 1px solid {COLORS['primary']};
        }}
        QPushButton:disabled {{
            background-color: #f8f8f8;
            color: #aaaaaa;
            border: 1px solid #dddddd;
        }}
    """,
    
    'text_input': f"""
        QLineEdit, QTextEdit, QPlainTextEdit {{
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            padding: 4px;
            background-color: white;
        }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 1px solid {COLORS['primary']};
        }}
    """,
    
    'dropdown': f"""
        QComboBox {{
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            padding: 4px;
            background-color: white;
        }}
        QComboBox:focus {{
            border: 1px solid {COLORS['primary']};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
    """,
    
    'table_view': f"""
        QTableView {{
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            gridline-color: {COLORS['border']};
            selection-background-color: {COLORS['primary']};
            selection-color: white;
        }}
        QTableView::item:hover {{
            background-color: #e6f2ff;
        }}
        QHeaderView::section {{
            background-color: {COLORS['background']};
            border: 1px solid {COLORS['border']};
            padding: 4px;
            font-weight: bold;
        }}
    """,
    
    'group_box': f"""
        QGroupBox {{
            font-weight: bold;
            border: 1px solid {COLORS['border']};
            border-radius: 6px;
            margin-top: 6px;
            padding-top: 10px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 10px;
            padding: 0 3px;
        }}
    """,
}

def apply_style(widget, style_name):
    """Apply a predefined style to a widget."""
    if style_name in STYLES:
        widget.setStyleSheet(STYLES[style_name])
    else:
        raise ValueError(f"Style '{style_name}' not found") 