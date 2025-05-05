from tests.ui.qt_test_utils import import_widget_safely
from tests.ui.mock_factories import mock_db_connection_factory

def test_products_view():
    ProductsView = import_widget_safely("ui/views/products_view.py").ProductsView
    mock_db = mock_db_connection_factory()
    
    view = ProductsView()
    view.show()
    view.load_products(mock_db)
    assert len(view.product_list) > 0
