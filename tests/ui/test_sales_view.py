from tests.ui.qt_test_utils import import_widget_safely
from tests.ui.mock_factories import mock_db_connection_factory

def test_sales_view():
    SalesView = import_widget_safely("ui/views/sales_view.py").SalesView
    mock_db = mock_db_connection_factory()
    
    view = SalesView()
    view.show()
    view.load_sales(mock_db)
    assert len(view.sales_list) > 0