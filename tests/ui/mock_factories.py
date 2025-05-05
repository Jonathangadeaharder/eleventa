from unittest.mock import MagicMock

def mock_dialog_factory():
    mock = MagicMock()
    mock.exec_.return_value = True
    return mock

def mock_icon_factory():
    mock = MagicMock()
    mock.pixmap.return_value = MagicMock()
    return mock

def mock_db_connection_factory():
    mock = MagicMock()
    mock.connect.return_value = mock
    mock.execute.return_value = []
    return mock