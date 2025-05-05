from tests.ui.qt_test_utils import import_widget_safely
from tests.ui.mock_factories import mock_db_connection_factory

def test_department_dialog():
    DepartmentDialog = import_widget_safely("ui/dialogs/department_dialog.py").DepartmentDialog
    mock_db = mock_db_connection_factory()
    
    dialog = DepartmentDialog()
    dialog.show()
    dialog.load_departments(mock_db)
    assert len(dialog.department_list) > 0
