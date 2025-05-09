import pytest
from unittest.mock import MagicMock, call, ANY, patch
from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox

# Models and Services to be mocked or used
from core.models.product import Product
from core.models.user import User
from core.models.sale import SaleItem
from ui.views.sales_view import SalesView
from core.services.product_service import ProductService  # Added import for spec

# SaleItemTableModel is created internally by SalesView

@pytest.fixture
def sales_view_fixture(qtbot):
    # Use spec=ProductService to make mock stricter and provide better error messages
    mock_product_service = MagicMock(spec=ProductService)
    mock_sale_service = MagicMock()
    mock_customer_service = MagicMock()
    mock_current_user = MagicMock(spec=User)
    mock_current_user.id = 1 # Example user ID

    # Patch show_error_message within the ui.views.sales_view module
    with patch('ui.views.sales_view.show_error_message') as mock_show_error_message:
        view = SalesView(
            product_service=mock_product_service,
            sale_service=mock_sale_service,
            customer_service=mock_customer_service,
            current_user=mock_current_user
        )
        qtbot.addWidget(view)

        view.sale_item_model.add_item = MagicMock()
        view.sale_item_model.clear = MagicMock()
        view.sale_item_model.get_all_items = MagicMock(return_value=[])
        view.update_total = MagicMock() # Mock update_total as it's called by add_item
        
        yield view, mock_product_service, mock_sale_service, view.sale_item_model, mock_show_error_message
        
        view.close()


def test_search_suggests_products(sales_view_fixture, qtbot):
    """Test that typing in the product combo box triggers search and populates suggestions."""
    sales_view, mock_product_service, _, sale_item_model, _ = sales_view_fixture # Correctly unpack if needed

    product1 = Product(id=1, code="P001", description="Test Product 1", sell_price=Decimal("10.00"), quantity_in_stock=Decimal("5.00"))
    product2 = Product(id=2, code="P002", description="Another Test Product", sell_price=Decimal("20.50"), quantity_in_stock=Decimal("3.00"))
    mock_products_list = [product1, product2]
    mock_product_service.find_product.return_value = mock_products_list

    product_combo = sales_view.product_combo

    search_term = "Test"
    product_combo.lineEdit().setText(search_term)
    product_combo.lineEdit().textEdited.emit(search_term)

    # Wait until the suggestion model has been populated or find_product has been called
    # Giving a timeout for waitUntil is good practice.
    qtbot.waitUntil(lambda: sales_view._suggestion_model.rowCount() == len(mock_products_list) or mock_product_service.find_product.called, timeout=1000)

    mock_product_service.find_product.assert_called_once_with(search_term)

    # Assert that the suggestion model (used by QCompleter) is populated correctly
    assert sales_view._suggestion_model.rowCount() == len(mock_products_list)
    
    # Verify the content of the suggestion model and the display map
    suggestion_strings = sales_view._suggestion_model.stringList()
    for i, product in enumerate(mock_products_list):
        expected_display_string = f"{product.code} – {product.description} (Stock: {product.quantity_in_stock:.2f})"
        assert expected_display_string in suggestion_strings
        # Check that the product object is correctly stored in the display_map for this suggestion string
        assert sales_view._display_map[expected_display_string] == product


def test_search_clears_suggestions_on_short_text(sales_view_fixture, qtbot):
    """Test that completer suggestions and display_map are cleared for short text.""" # Clarified docstring
    sales_view, mock_product_service, _, _, _ = sales_view_fixture  # Fixed unpacking
    
    product_combo = sales_view.product_combo
    suggestion_model = sales_view._suggestion_model

    # Simulate a state where suggestions were previously populated
    mock_initial_product = Product(id=10, code="P100", description="Previous Product", sell_price=Decimal("1.00"), quantity_in_stock=Decimal("1"))
    initial_display_string = f"{mock_initial_product.code} – {mock_initial_product.description} (Stock: {mock_initial_product.quantity_in_stock:.2f})"
    suggestion_model.setStringList([initial_display_string])
    sales_view._display_map = {initial_display_string: mock_initial_product} # Mirror what SalesView does
    assert suggestion_model.rowCount() == 1, "Suggestion model should have 1 item initially"
    assert sales_view._display_map, "Display map should have 1 item initially"
    
    # Set initial text in line edit, which should be restored
    initial_lineEdit_text = "T"
    product_combo.lineEdit().setText(initial_lineEdit_text)

    # Action: Emit textEdited with a short search term (which is also the lineEdit's current text here)
    short_search_term = "T" # Length 1, less than min 2 chars
    product_combo.lineEdit().textEdited.emit(short_search_term)

    mock_product_service.find_product.assert_not_called()
    assert suggestion_model.rowCount() == 0, "Suggestion model should be empty after short search term"
    assert not sales_view._display_map, "Display map should be empty after short search term"
    assert product_combo.lineEdit().text() == initial_lineEdit_text


def test_search_no_results_populates_empty(sales_view_fixture, qtbot):
    """Test that completer suggestions and display_map are empty if find_product returns no results.""" # Clarified docstring
    sales_view, mock_product_service, _, _, _ = sales_view_fixture  # Fixed unpacking
    
    mock_product_service.find_product.return_value = [] # No products found
    
    product_combo = sales_view.product_combo
    suggestion_model = sales_view._suggestion_model
    search_term = "UnknownProduct"
    
    product_combo.lineEdit().setText(search_term)
    product_combo.lineEdit().textEdited.emit(search_term)

    # Wait until find_product is called. Timeout for safety.
    qtbot.waitUntil(lambda: mock_product_service.find_product.called, timeout=1000)

    mock_product_service.find_product.assert_called_once_with(search_term)
    assert suggestion_model.rowCount() == 0, "Suggestion model should be empty when no products found"
    assert not sales_view._display_map, "Display map should be empty when no products found"
    assert product_combo.lineEdit().text() == search_term # Line edit text should persist


def test_search_suggests_products_with_multiple_results(sales_view_fixture, qtbot):
    """Test that multiple products are suggested when there are multiple matches."""
    sales_view, mock_product_service, _, sale_item_model, _ = sales_view_fixture # Unpack consistently

    # 1. Setup: Define mock products to be returned by the service
    product1 = Product(id=1, code="P001", description="Test Product 1", sell_price=Decimal("10.00"), quantity_in_stock=Decimal("5"))
    product2 = Product(id=2, code="P002", description="Another Test Product", sell_price=Decimal("20.50"), quantity_in_stock=Decimal("3"))
    product3 = Product(id=3, code="P003", description="Yet Another Test Product", sell_price=Decimal("15.00"), quantity_in_stock=Decimal("2"))
    mock_products_list = [product1, product2, product3]
    mock_product_service.find_product.return_value = mock_products_list

    product_combo = sales_view.product_combo
    suggestion_model = sales_view._suggestion_model
    assert isinstance(product_combo, QComboBox)

    # 2. Action: Simulate typing text into the combo box's lineEdit
    # The `textEdited` signal is connected, so this should trigger `_search_and_suggest_products`
    search_term = "Test"
    product_combo.lineEdit().setText(search_term) # Sets text
    product_combo.lineEdit().textEdited.emit(search_term) # Manually emit if setText doesn't trigger it for tests

    # Wait for find_product to be called or model to be populated
    qtbot.waitUntil(lambda: suggestion_model.rowCount() == len(mock_products_list) or mock_product_service.find_product.called, timeout=1000)

    # 3. Assertions
    # Verify product_service.find_product was called
    mock_product_service.find_product.assert_called_once_with(search_term)

    # Verify the suggestion model is populated correctly
    assert suggestion_model.rowCount() == len(mock_products_list)
    suggestion_strings = suggestion_model.stringList()
    for product in mock_products_list: # Iterate through original product list for checking
        expected_display_string = f"{product.code} – {product.description} (Stock: {product.quantity_in_stock:.2f})"
        assert expected_display_string in suggestion_strings
        assert sales_view._display_map[expected_display_string] == product


def test_search_suggests_products_with_no_results(sales_view_fixture, qtbot):
    """Test that no products are suggested when there are no matches."""
    sales_view, mock_product_service, _, _, _ = sales_view_fixture  # Fixed unpacking

    # 1. Setup: Define mock products to be returned by the service
    mock_product_service.find_product.return_value = [] # No products found

    product_combo = sales_view.product_combo
    assert isinstance(product_combo, QComboBox)

    # 2. Action: Simulate typing text into the combo box's lineEdit
    search_term = "Unknown"
    product_combo.lineEdit().setText(search_term)
    product_combo.lineEdit().textEdited.emit(search_term)

    # 3. Assertions
    # Verify product_service.find_product was called
    mock_product_service.find_product.assert_called_once_with(search_term)

    # Verify the QComboBox is empty
    assert product_combo.count() == 0


def test_search_suggests_products_with_empty_text(sales_view_fixture, qtbot):
    """Test that find_product is not called and suggestions are empty when search text is empty."""
    sales_view, mock_product_service, _, _, _ = sales_view_fixture  # Fixed unpacking
    
    # 1. Setup: Define mock products (though they shouldn't be used if find_product isn't called)
    product1 = Product(id=1, code="P001", description="Test Product 1", sell_price=Decimal("10.00"), quantity_in_stock=Decimal("5"))
    product2 = Product(id=2, code="P002", description="Another Test Product", sell_price=Decimal("20.50"), quantity_in_stock=Decimal("3"))
    # mock_product_service.find_product shouldn't be called, so its return_value is less critical here,
    # but setting it up doesn't hurt if a different logic path was taken by mistake.
    mock_product_service.find_product.return_value = [product1, product2] 
 
    product_combo = sales_view.product_combo
    suggestion_model = sales_view._suggestion_model
    assert isinstance(product_combo, QComboBox)
 
    # 2. Action: Simulate typing text into the combo box's lineEdit
    search_term = ""
    product_combo.lineEdit().setText(search_term)
    product_combo.lineEdit().textEdited.emit(search_term)
 
    # 3. Assertions for empty search term
    # Verify product_service.find_product was NOT called
    mock_product_service.find_product.assert_not_called()
 
    # Verify the suggestion model and display map are empty
    assert suggestion_model.rowCount() == 0, "Suggestion model should be empty for empty search term"
    assert not sales_view._display_map, "Display map should be empty for empty search term"
    assert product_combo.lineEdit().text() == search_term # Line edit should retain the empty text


def test_search_suggests_products_with_case_insensitive_search(sales_view_fixture, qtbot):
    """Test that products are suggested regardless of case."""
    sales_view, mock_product_service, _, sale_item_model, _ = sales_view_fixture # Unpack consistently
 
    # 1. Setup: Define mock products
    product1 = Product(id=1, code="P001", description="Test Product One", sell_price=Decimal("10.00"), quantity_in_stock=Decimal("5"))
    product2 = Product(id=2, code="P002", description="Test Product Two", sell_price=Decimal("20.50"), quantity_in_stock=Decimal("3"))
    mock_products = [product1, product2] # Keep original name for clarity in this test's context
    # The service is assumed to handle case-insensitivity if required, or SalesView might lowercase. Test the outcome.
    mock_product_service.find_product.return_value = mock_products
 
    product_combo = sales_view.product_combo
    suggestion_model = sales_view._suggestion_model
    assert isinstance(product_combo, QComboBox)
 
    # 2. Action: Simulate typing text in uppercase
    search_term_simulated_typing = "TEST PRODUCT"
 
    product_combo.lineEdit().setText(search_term_simulated_typing)
    product_combo.lineEdit().textEdited.emit(search_term_simulated_typing)
 
    # Wait for find_product to be called or model to be populated
    qtbot.waitUntil(lambda: suggestion_model.rowCount() == len(mock_products) or mock_product_service.find_product.called, timeout=1000)
 
    # 3. Assertions
    # Verify product_service.find_product was called with the text as typed
    mock_product_service.find_product.assert_called_once_with(search_term_simulated_typing)
 
    # Verify the suggestion model is populated correctly
    assert suggestion_model.rowCount() == len(mock_products)
    suggestion_strings = suggestion_model.stringList()
    for product in mock_products:
        expected_display_string = f"{product.code} – {product.description} (Stock: {product.quantity_in_stock:.2f})"
        assert expected_display_string in suggestion_strings
        assert sales_view._display_map[expected_display_string] == product


def test_product_selected_from_combo_adds_to_sale(sales_view_fixture, qtbot):
    """Test that selecting a product from the dropdown immediately adds it to the sale."""
    sales_view, mock_product_service, _, sale_item_model, _ = sales_view_fixture

    # Setup a product
    product = Product(id=1, code="P001", description="Test Product", sell_price=Decimal("10.00"), quantity_in_stock=Decimal("5.00"))
    
    # Add the product to the ComboBox
    sales_view.product_combo.addItem(f"{product.code} - {product.description}", product)
    
    # Simulate selecting this item from the dropdown
    sales_view.product_combo.setCurrentIndex(0)
    sales_view._product_selected_from_combo(0)
    
    # Check that add_item was called with the correct product
    sale_item_model.add_item.assert_called_once()
    args, _ = sale_item_model.add_item.call_args
    sale_item = args[0]
    
    # Verify the SaleItem has the correct data
    assert sale_item.product_id == product.id
    assert sale_item.product_code == product.code
    assert sale_item.product_description == product.description
    assert sale_item.unit_price == product.sell_price