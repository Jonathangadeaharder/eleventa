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
    sales_view, mock_product_service, _, _, _ = sales_view_fixture

    product1 = Product(id=1, code="P001", description="Test Product 1", sell_price=Decimal("10.00"), quantity_in_stock=Decimal("5.00"))
    product2 = Product(id=2, code="P002", description="Another Test Product", sell_price=Decimal("20.50"), quantity_in_stock=Decimal("3.00"))
    mock_products = [product1, product2]
    mock_product_service.find_product.return_value = mock_products

    product_combo = sales_view.product_combo

    search_term = "Test"
    product_combo.lineEdit().setText(search_term)
    product_combo.lineEdit().textEdited.emit(search_term)

    qtbot.waitUntil(lambda: mock_product_service.find_product.called)

    mock_product_service.find_product.assert_called_once_with(search_term)
    assert product_combo.count() == len(mock_products)
    for i, product in enumerate(mock_products):
        expected_text = f"{product.code} - {product.description} (Stock: {product.quantity_in_stock:.2f})"
        assert product_combo.itemText(i) == expected_text
        assert product_combo.itemData(i) == product


def test_search_clears_suggestions_on_short_text(sales_view_fixture, qtbot):
    """Test that suggestions are cleared or not searched for short text."""
    sales_view, mock_product_service, _, _, _ = sales_view_fixture  # Fixed unpacking
    
    product_combo = sales_view.product_combo
    
    # Pre-populate combo to ensure it's cleared
    product_combo.addItem("Some existing item", Product(id=10, code="P100", description="Prev", sell_price=1, quantity_in_stock=1))
    
    # Set initial text in line edit, which should be restored
    initial_lineEdit_text = "T"
    product_combo.lineEdit().setText(initial_lineEdit_text)

    # Action: Emit textEdited with a short search term (which is also the lineEdit's current text here)
    short_search_term = "T"
    product_combo.lineEdit().textEdited.emit(short_search_term)

    mock_product_service.find_product.assert_not_called()
    assert product_combo.count() == 0 
    # The _search_and_suggest_products method restores the current line edit text after clearing.
    assert product_combo.lineEdit().text() == initial_lineEdit_text


def test_search_no_results_populates_empty(sales_view_fixture, qtbot):
    """Test that QComboBox is empty if find_product returns no results."""
    sales_view, mock_product_service, _, _, _ = sales_view_fixture  # Fixed unpacking
    
    mock_product_service.find_product.return_value = [] # No products found
    
    product_combo = sales_view.product_combo
    search_term = "UnknownProduct"
    
    product_combo.lineEdit().setText(search_term)
    product_combo.lineEdit().textEdited.emit(search_term)

    qtbot.waitUntil(lambda: mock_product_service.find_product.called)

    mock_product_service.find_product.assert_called_once_with(search_term)
    assert product_combo.count() == 0
    assert product_combo.lineEdit().text() == search_term # Line edit text should persist


def test_search_suggests_products_with_multiple_results(sales_view_fixture, qtbot):
    """Test that multiple products are suggested when there are multiple matches."""
    sales_view, mock_product_service, _, _, _ = sales_view_fixture  # Fixed unpacking

    # 1. Setup: Define mock products to be returned by the service
    product1 = Product(id=1, code="P001", description="Test Product 1", sell_price=Decimal("10.00"), quantity_in_stock=Decimal("5"))
    product2 = Product(id=2, code="P002", description="Another Test Product", sell_price=Decimal("20.50"), quantity_in_stock=Decimal("3"))
    product3 = Product(id=3, code="P003", description="Yet Another Test Product", sell_price=Decimal("15.00"), quantity_in_stock=Decimal("2"))
    mock_products = [product1, product2, product3]
    mock_product_service.find_product.return_value = mock_products

    product_combo = sales_view.product_combo
    assert isinstance(product_combo, QComboBox)

    # 2. Action: Simulate typing text into the combo box's lineEdit
    # The `textEdited` signal is connected, so this should trigger `_search_and_suggest_products`
    search_term = "Test"
    product_combo.lineEdit().setText(search_term) # Sets text
    product_combo.lineEdit().textEdited.emit(search_term) # Manually emit if setText doesn't trigger it for tests

    # 3. Assertions
    # Verify product_service.find_product was called
    mock_product_service.find_product.assert_called_once_with(search_term)

    # Verify the QComboBox is populated
    assert product_combo.count() == len(mock_products)
    for i, product in enumerate(mock_products):
        expected_text = f"{product.code} - {product.description} (Stock: {product.quantity_in_stock:.2f})"
        assert product_combo.itemText(i) == expected_text
        assert product_combo.itemData(i) == product


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
    """Test that no products are suggested when the search text is empty."""
    sales_view, mock_product_service, _, _, _ = sales_view_fixture  # Fixed unpacking

    # 1. Setup: Define mock products to be returned by the service
    product1 = Product(id=1, code="P001", description="Test Product 1", sell_price=Decimal("10.00"), quantity_in_stock=Decimal("5"))
    product2 = Product(id=2, code="P002", description="Another Test Product", sell_price=Decimal("20.50"), quantity_in_stock=Decimal("3"))
    mock_products = [product1, product2]
    mock_product_service.find_product.return_value = mock_products

    product_combo = sales_view.product_combo
    assert isinstance(product_combo, QComboBox)

    # 2. Action: Simulate typing text into the combo box's lineEdit
    search_term = ""
    product_combo.lineEdit().setText(search_term)
    product_combo.lineEdit().textEdited.emit(search_term)

    # 3. Assertions
    # Verify product_service.find_product was called
    mock_product_service.find_product.assert_called_once_with(search_term)

    # Verify the QComboBox is populated
    assert product_combo.count() == len(mock_products)
    for i, product in enumerate(mock_products):
        expected_text = f"{product.code} - {product.description} (Stock: {product.quantity_in_stock:.2f})"
        assert product_combo.itemText(i) == expected_text
        assert product_combo.itemData(i) == product


def test_search_suggests_products_with_case_insensitive_search(sales_view_fixture, qtbot):
    """Test that products are suggested regardless of case."""
    sales_view, mock_product_service, _, _, _ = sales_view_fixture  # Fixed unpacking

    # 1. Setup: Define mock products to be returned by the service
    product1 = Product(id=1, code="P001", description="Test Product 1", sell_price=Decimal("10.00"), quantity_in_stock=Decimal("5"))
    product2 = Product(id=2, code="P002", description="Another Test Product", sell_price=Decimal("20.50"), quantity_in_stock=Decimal("3"))
    mock_products = [product1, product2]
    mock_product_service.find_product.return_value = mock_products

    product_combo = sales_view.product_combo
    assert isinstance(product_combo, QComboBox)

    # 2. Action: Simulate typing text into the combo box's lineEdit with lowercase
    search_term = "test"
    product_combo.lineEdit().setText(search_term)
    product_combo.lineEdit().textEdited.emit(search_term)

    # 3. Assertions
    # Verify product_service.find_product was called
    mock_product_service.find_product.assert_called_once_with(search_term)

    # Verify the QComboBox is populated
    assert product_combo.count() == len(mock_products)
    for i, product in enumerate(mock_products):
        expected_text = f"{product.code} - {product.description} (Stock: {product.quantity_in_stock:.2f})"
        assert product_combo.itemText(i) == expected_text
        assert product_combo.itemData(i) == product


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
 