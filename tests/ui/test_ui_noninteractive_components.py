import pytest
from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from ui.utils import (
    show_error_message,
    show_info_message,
    ask_confirmation,
    apply_standard_form_style,
)
from ui.models.base_table_model import BaseTableModel
from ui.models.table_models import (
    ProductTableModel,
    SaleItemTableModel,
    CustomerTableModel,
    CashDrawerEntryTableModel,
    ReportTableModel,
)
from core.models.sale import SaleItem


class DummyModel(BaseTableModel):
    HEADERS = ["A", "B", "C"]


def test_base_table_model_basic():
    model = DummyModel()
    assert model.rowCount() == 0
    assert model.columnCount() == 3
    # Header data
    assert model.headerData(0, Qt.Horizontal, Qt.ItemDataRole.DisplayRole) == "A"
    assert model.headerData(5, Qt.Horizontal, Qt.ItemDataRole.DisplayRole) is None
    # get_item_at_row empty
    assert model.get_item_at_row(0) is None
    # update_data
    data = [1, 2, 3]
    model.update_data(data)
    assert model.rowCount() == 3
    assert model.get_item_at_row(1) == 2


def test_product_table_model_display_and_alignment():
    from ui.models.table_models import Product
    model = ProductTableModel()
    p1 = Product(id=1, code="X", description="b", cost_price=1.1, sell_price=2.2,
                 department_id=5, department=None,
                 quantity_in_stock=1.0, min_stock=2.0, uses_inventory=True, unit="U")
    p2 = Product(id=2, code="Y", description="a", cost_price=3.3, sell_price=4.4,
                 department=None, department_id=None,
                 quantity_in_stock=0.0, min_stock=0.0, uses_inventory=False, unit="U")
    model.update_data([p1, p2])
    # sorted by description: a then b
    idx0 = model.index(0, 0)
    assert model.data(idx0, Qt.ItemDataRole.DisplayRole) == "Y"
    # price column
    idx_price = model.index(0, 2)
    assert model.data(idx_price, Qt.ItemDataRole.DisplayRole) == "4.40"
    # alignment for price
    assert model.data(idx_price, Qt.ItemDataRole.TextAlignmentRole) == (Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    # department column for p2
    idx_dept = model.index(0, 5)
    assert model.data(idx_dept, Qt.ItemDataRole.DisplayRole) == "-"
    # cost column of second row (p1)
    idx_cost = model.index(1, 6)
    assert model.data(idx_cost, Qt.ItemDataRole.DisplayRole) == "1.10"


def test_sale_item_table_model_operations():
    model = SaleItemTableModel()
    item1 = SaleItem(product_id=1, quantity=2, unit_price=3)
    item2 = SaleItem(product_id=2, quantity=5, unit_price=4)
    model.add_item(item1)
    model.add_item(item2)
    assert model.rowCount() == 2
    items = model.get_all_items()
    assert items == [item1, item2]
    assert model.get_item_at_row(1) == item2
    model.remove_item(0)
    assert model.rowCount() == 1
    assert model.get_all_items() == [item2]


def test_report_table_model():
    data = [["r1c1", "r1c2"], ["r2c1", "r2c2"]]
    headers = ["H1", "H2"]
    model = ReportTableModel(data, headers)
    assert model.rowCount() == 2
    assert model.columnCount() == 2
    # headerData horizontal
    assert model.headerData(0, Qt.Horizontal, Qt.DisplayRole) == "H1"
    # headerData vertical (row numbers)
    assert model.headerData(1, Qt.Vertical, Qt.DisplayRole) == 2
    # data display
    idx = model.index(1, 1)
    assert model.data(idx, Qt.DisplayRole) == "r2c2"
    # alignment for numeric column (>0)
    assert model.data(idx, Qt.TextAlignmentRole) == (Qt.AlignRight | Qt.AlignVCenter)


def test_ui_utils_message_boxes(monkeypatch):
    calls_warn = []
    calls_info = []
    monkeypatch.setattr(QMessageBox, 'warning', lambda p, t, m: calls_warn.append((p, t, m)))
    monkeypatch.setattr(QMessageBox, 'information', lambda p, t, m: calls_info.append((p, t, m)))
    show_error_message('parent', 'Title', 'Msg')
    show_info_message('parent2', 'Title2', 'Msg2')
    assert calls_warn == [('parent', 'Title', 'Msg')]
    assert calls_info == [('parent2', 'Title2', 'Msg2')]


def test_ask_confirmation(monkeypatch):
    # Yes
    monkeypatch.setattr(QMessageBox, 'question', lambda p, t, m, b, d: QMessageBox.StandardButton.Yes)
    assert ask_confirmation('p', 't', 'm') is True
    # No
    monkeypatch.setattr(QMessageBox, 'question', lambda p, t, m, b, d: QMessageBox.StandardButton.No)
    assert ask_confirmation('p', 't', 'm') is False


def test_apply_standard_form_style(qtbot):
    w = QWidget()
    layout = QVBoxLayout()
    w.setLayout(layout)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    apply_standard_form_style(w)
    assert layout.contentsMargins().left() == 10
    assert layout.spacing() == 10


def test_customer_table_model_display_alignment_and_foreground():
    from ui.models.table_models import CustomerTableModel
    from core.models.customer import Customer
    model = CustomerTableModel()
    c1 = Customer(name="Alice", phone="123", email=None, address=None, cuit=None, iva_condition=None, credit_limit=100.0, credit_balance=50.0)
    c2 = Customer(name="Bob", phone=None, email="bob@example.com", address="Somewhere", cuit=None, iva_condition=None, credit_limit=50.0, credit_balance=60.0)
    c3 = Customer(name="Carol", phone=None, email=None, address=None, cuit=None, iva_condition=None, credit_limit=100.0, credit_balance=-10.0)
    model.update_data([c1, c2, c3])
    assert model.rowCount() == 3
    assert model.columnCount() == 6
    # Header check
    assert model.headerData(0, Qt.Horizontal, Qt.ItemDataRole.DisplayRole) == "Nombre"
    # Display value for c1 balance
    idx = model.index(0, 4)
    assert model.data(idx, Qt.ItemDataRole.DisplayRole) == "50.00"
    # Alignment
    assert model.data(idx, Qt.ItemDataRole.TextAlignmentRole) == (Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    # No highlight for c1
    assert model.data(idx, Qt.ItemDataRole.ForegroundRole) is None
    # Exceeding limit highlight for c2
    idx2 = model.index(1, 4)
    assert model.data(idx2, Qt.ItemDataRole.ForegroundRole) == QColor("red")
    # Negative balance highlight for c3
    idx3 = model.index(2, 4)
    assert model.data(idx3, Qt.ItemDataRole.ForegroundRole) == QColor("orange")


def test_cash_drawer_entry_table_model_display_and_alignment():
    from ui.models.table_models import CashDrawerEntryTableModel
    from core.models.cash_drawer import CashDrawerEntry, CashDrawerEntryType
    from datetime import datetime
    from decimal import Decimal
    model = CashDrawerEntryTableModel()
    entry = CashDrawerEntry(timestamp=datetime(2025,4,21,19,30,15), entry_type=CashDrawerEntryType.IN, amount=Decimal("123.45"), description="TestDesc", user_id=7)
    model.update_data([entry])
    assert model.rowCount() == 1
    assert model.columnCount() == 4
    # Header data
    assert model.headerData(0, Qt.Horizontal, Qt.DisplayRole) == "Hora"
    # Display data
    idx0 = model.index(0, 0)
    assert model.data(idx0, Qt.DisplayRole) == "19:30:15"
    idx1 = model.index(0, 1)
    assert model.data(idx1, Qt.DisplayRole) == "TestDesc"
    idx2 = model.index(0, 2)
    assert model.data(idx2, Qt.DisplayRole) == "Usuario #7"
    idx3 = model.index(0, 3)
    assert model.data(idx3, Qt.DisplayRole) == "$123.45"
    # Alignment for amount
    assert model.data(idx3, Qt.TextAlignmentRole) == int(Qt.AlignRight | Qt.AlignVCenter)
