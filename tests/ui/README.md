# UI Test Migration Guide

## Mocking Examples

### Dialog Mocking
```python
from tests.ui.mock_factories import mock_dialog_factory

def test_dialog_usage():
    mock_dialog = mock_dialog_factory()
    # Use the mock dialog in the test
    assert mock_dialog.exec_() is True
```

### Icon Mocking
```python
from tests.ui.mock_factories import mock_icon_factory

def test_icon_usage():
    mock_icon = mock_icon_factory()
    pixmap = mock_icon.pixmap()
    assert pixmap is not None
```

### Database Connection Mocking
```python
from tests.ui.mock_factories import mock_db_connection_factory

def test_db_connection():
    mock_conn = mock_db_connection_factory()
    results = mock_conn.execute("SELECT * FROM table")
    assert results == []