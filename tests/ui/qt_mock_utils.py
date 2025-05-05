from unittest.mock import MagicMock

def create_style_mocks():
    """Create standard mocks for styling functions."""
    style_mock = MagicMock()
    style_mock.get_stylesheet.return_value = "mocked_stylesheet"
    return style_mock

def create_dialog_mocks():
    """Create standard mocks for dialogs."""
    dialog_mock = MagicMock()
    dialog_mock.exec_.return_value = True
    return dialog_mock

def create_icon_mocks():
    """Create standard mocks for icons and resources."""
    icon_mock = MagicMock()
    icon_mock.pixmap.return_value = MagicMock()
    return icon_mock