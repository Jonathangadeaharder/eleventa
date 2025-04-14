import pytest
from decimal import Decimal
from ui.models.table_models import SaleItemTableModel, CustomerTableModel
from core.models.sale import SaleItem
from core.models.customer import Customer
from PySide6.QtCore import Qt, QModelIndex

def make_item(product_id, code, desc, qty, price):
    return SaleItem(
        product_id=product_id,
        quantity=Decimal(qty),
        unit_price=Decimal(price),
        product_code=code,
        product_description=desc
    )

def test_add_items_and_total():
    model = SaleItemTableModel()
    item1 = make_item(1, "A001", "Apple", "2", "1.50")
    item2 = make_item(2, "B002", "Banana", "3", "2.00")
    model.add_item(item1)
    model.add_item(item2)
    items = model.get_all_items()
    assert len(items) == 2
    assert items[0].product_code == "A001"
    assert items[1].product_code == "B002"
    expected_total = item1.subtotal + item2.subtotal
    total = sum(i.subtotal for i in items)
    assert total == expected_total

def test_add_duplicate_product_no_merge():
    model = SaleItemTableModel()
    item1 = make_item(1, "A001", "Apple", "1", "1.50")
    item2 = make_item(1, "A001", "Apple", "2", "1.50")
    model.add_item(item1)
    model.add_item(item2)
    items = model.get_all_items()
    # Since merging is not implemented, both items should be present as separate rows
    assert len(items) == 2
    assert items[0].quantity == Decimal("1")
    assert items[1].quantity == Decimal("2")
    total = sum(i.subtotal for i in items)
    assert total == Decimal("4.50")

def make_customer(name, phone=None, email=None, address=None, credit_limit=0.0, credit_balance=0.0):
    return Customer(
        name=name,
        phone=phone,
        email=email,
        address=address,
        credit_limit=credit_limit,
        credit_balance=credit_balance
    )

def test_customer_table_model_data_and_update():
    # Create two customers
    cust1 = make_customer("Alice", "123", "alice@example.com", "Street 1", 100.0, 50.0)
    cust2 = make_customer("Bob", None, None, None, 200.0, -10.0)
    model = CustomerTableModel()
    # Test update_data sorts by name
    model.update_data([cust2, cust1])
    assert model.rowCount() == 2
    # Should be sorted: Alice first, then Bob
    idx_alice = model.index(0, 0)
    idx_bob = model.index(1, 0)
    assert model.data(idx_alice, Qt.DisplayRole) == "Alice"
    assert model.data(idx_bob, Qt.DisplayRole) == "Bob"
    # Test all columns for Alice
    assert model.data(model.index(0, 0), Qt.DisplayRole) == "Alice"
    assert model.data(model.index(0, 1), Qt.DisplayRole) == "123"
    assert model.data(model.index(0, 2), Qt.DisplayRole) == "alice@example.com"
    assert model.data(model.index(0, 3), Qt.DisplayRole) == "Street 1"
    assert model.data(model.index(0, 4), Qt.DisplayRole) == "50.00"
    assert model.data(model.index(0, 5), Qt.DisplayRole) == "100.00"
    # Test all columns for Bob (with missing optional fields)
    assert model.data(model.index(1, 1), Qt.DisplayRole) == "-"
    assert model.data(model.index(1, 2), Qt.DisplayRole) == "-"
    assert model.data(model.index(1, 3), Qt.DisplayRole) == "-"
    assert model.data(model.index(1, 4), Qt.DisplayRole) == "-10.00"
    assert model.data(model.index(1, 5), Qt.DisplayRole) == "200.00"
    # Test alignment role for numeric columns
    assert model.data(model.index(0, 4), Qt.TextAlignmentRole) == (Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    assert model.data(model.index(0, 5), Qt.TextAlignmentRole) == (Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    # Test update_data replaces and sorts
    cust3 = make_customer("Charlie", credit_limit=50.0, credit_balance=5.0)
    model.update_data([cust3])
    assert model.rowCount() == 1
    assert model.data(model.index(0, 0), Qt.DisplayRole) == "Charlie"