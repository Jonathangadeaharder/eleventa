from tests.ui.qt_test_utils import import_widget_safely
from tests.ui.mock_factories import mock_db_connection_factory

def test_add_inventory_dialog():
    AddInventoryDialog = import_widget_safely("ui/dialogs/add_inventory_dialog.py").AddInventoryDialog
    mock_db = mock_db_connection_factory()
    
    dialog = AddInventoryDialog()
    dialog.show()
    dialog.populate_products(mock_db)
    assert dialog.product_count() > 0
