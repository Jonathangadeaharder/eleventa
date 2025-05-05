from tests.ui.qt_test_utils import import_widget_safely
from tests.ui.mock_factories import mock_dialog_factory

def test_login_dialog():
    # Dynamically import the login dialog widget
    LoginDialog = import_widget_safely("ui/dialogs/login_dialog.py").LoginDialog
    mock_dialog = mock_dialog_factory()
    
    # Test the dialog functionality
    dialog = LoginDialog()
    dialog.show()
    assert dialog.exec_() is True