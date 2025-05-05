from tests.ui.qt_test_utils import import_widget_safely
from tests.ui.mock_factories import mock_db_connection_factory

def test_product_dialog():
    ProductDialog = import_widget_safely("ui/dialogs/product_dialog.py").ProductDialog
    mock_db = mock_db_connection_factory()
    
    dialog = ProductDialog()
    dialog.show()
    dialog.populate_products(mock_db)
    assert len(dialog.products) > 0
