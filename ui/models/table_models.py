from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PySide6.QtGui import QColor, QBrush
from typing import List, Any, Optional
from decimal import Decimal
from datetime import datetime
import locale

try:
    # Try to set the locale for consistent number/date formatting
    locale.setlocale(locale.LC_ALL, 'es_AR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')  # Fallback
    except:
        locale.setlocale(locale.LC_ALL, '')  # Use default locale

# Assuming core.models.product.Product exists, but we'll mock it for now
# from core.models.product import Product
from dataclasses import dataclass, field
from core.models.product import Product
from core.models.sale import SaleItem
from core.models.customer import Customer
from core.models.supplier import Supplier
from core.models.purchase import PurchaseOrder, PurchaseOrderItem
from core.models.cash_drawer import CashDrawerEntry, CashDrawerEntryType

# Mock Product class until TASK-004 is properly integrated
@dataclass
class Product:
    id: int
    code: str
    description: str
    cost_price: float
    sale_price: float
    department_id: Optional[int] = None
    department_name: Optional[str] = "-" # Usually joined/fetched separately
    quantity_in_stock: float = 0.0
    min_stock: float = 0.0
    uses_inventory: bool = True
    unit: str = "U"

class ProductTableModel(QAbstractTableModel):
    """Model for displaying products in a QTableView."""
    HEADERS = [
        "Código", "Descripción", "Precio Venta", "Stock", "Mínimo", "Depto.", "Costo"
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._products: List[Product] = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Returns the number of rows (products)."""
        return len(self._products)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Returns the number of columns."""
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Returns the data for a given index and role."""
        if not index.isValid():
            return None

        product = self._products[index.row()]
        column = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if column == 0:
                return product.code
            elif column == 1:
                return product.description
            elif column == 2:
                return f"{product.sale_price:.2f}" if product.sale_price is not None else "N/A"
            elif column == 3:
                return f"{product.quantity_in_stock:.2f}" if product.uses_inventory else "N/A"
            elif column == 4:
                return f"{product.min_stock:.2f}" if product.uses_inventory else "N/A"
            elif column == 5:
                return product.department_name if product.department_name else "-"
            elif column == 6:
                return f"{product.cost_price:.2f}" if product.cost_price is not None else "N/A"

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if column in [2, 3, 4, 6]: # Price/Stock columns
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        elif role == Qt.ItemDataRole.ForegroundRole:
            if product.uses_inventory and product.min_stock is not None and product.quantity_in_stock < product.min_stock:
                return QColor("red") # Low stock highlighting
            # Optional: Add highlighting for negative stock if allowed

        elif role == Qt.ItemDataRole.UserRole: # Custom role to get the full product object
            return product

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Returns the header data."""
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            try:
                return self.HEADERS[section]
            except IndexError:
                return None
        return None

    def update_data(self, products: List[Product]):
        """Updates the model's data and refreshes the view."""
        self.beginResetModel()
        self._products = sorted(products, key=lambda p: p.description) # Sort by description
        self.endResetModel()

    # Renamed from get_product for clarity
    def get_product_at_row(self, row: int) -> Optional[Product]:
        """Gets the product object at a specific model row."""
        if 0 <= row < len(self._products):
            return self._products[row]
        return None

class SaleItemTableModel(QAbstractTableModel):
    """Model for displaying sale items in a QTableView."""
    HEADERS = ["Código", "Descripción", "Cantidad", "Precio Unit.", "Subtotal"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: List[SaleItem] = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._items)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None

        item = self._items[index.row()]
        column = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if column == 0:
                return item.product_code
            elif column == 1:
                return item.product_description
            elif column == 2:
                # Format quantity appropriately (might need context for units)
                return str(item.quantity.normalize()) # Normalize to remove trailing zeros
            elif column == 3:
                return f"{item.unit_price:.2f}"
            elif column == 4:
                return f"{item.subtotal:.2f}"

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if column in [2, 3, 4]: # Numeric columns
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        elif role == Qt.ItemDataRole.UserRole: # Custom role to get the full SaleItem object
             return item

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            try:
                return self.HEADERS[section]
            except IndexError:
                return None
        return None

    def add_item(self, item: SaleItem):
        """Adds a new item to the end of the model."""
        # Check if product already exists, if so, increment quantity?
        # For simplicity now, just append. Add merge logic later if needed.
        row_count = self.rowCount()
        self.beginInsertRows(QModelIndex(), row_count, row_count)
        self._items.append(item)
        self.endInsertRows()

    def remove_item(self, row: int):
        """Removes the item at the given row."""
        if 0 <= row < self.rowCount():
            self.beginRemoveRows(QModelIndex(), row, row)
            del self._items[row]
            self.endRemoveRows()

    def get_all_items(self) -> List[SaleItem]:
        """Returns a copy of all items currently in the model."""
        return list(self._items) # Return a copy

    def clear(self):
        """Removes all items from the model."""
        self.beginResetModel()
        self._items = []
        self.endResetModel()

    def get_item_at_row(self, row: int) -> Optional[SaleItem]:
         """Gets the SaleItem object at a specific model row."""
         if 0 <= row < len(self._items):
             return self._items[row]
         return None 

# --- Add Customer Table Model ---

class CustomerTableModel(QAbstractTableModel):
    """Model for displaying customers in a QTableView."""
    HEADERS = [
        "Nombre", "Teléfono", "Email", "Dirección", "Saldo", "Límite Crédito"
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._customers: List[Customer] = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Returns the number of rows (customers)."""
        return len(self._customers)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Returns the number of columns."""
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Returns the data for a given index and role."""
        if not index.isValid():
            return None

        customer = self._customers[index.row()]
        column = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if column == 0:
                return customer.name
            elif column == 1:
                return customer.phone or "-"
            elif column == 2:
                return customer.email or "-"
            elif column == 3:
                return customer.address or "-"
            elif column == 4:
                # Format as currency
                balance = customer.credit_balance or 0.0
                return f"{balance:.2f}"
            elif column == 5:
                # Format as currency
                limit = customer.credit_limit or 0.0
                return f"{limit:.2f}"

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if column in [4, 5]: # Numeric/Currency columns
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        elif role == Qt.ItemDataRole.ForegroundRole:
            # Optional: Highlight customers with negative balance (debt)
            if customer.credit_balance is not None and customer.credit_balance < 0:
                 return QColor("orange") # Or another color
            # Optional: Highlight customers exceeding credit limit
            if customer.credit_limit is not None and customer.credit_balance is not None and \
               customer.credit_balance > customer.credit_limit and customer.credit_limit > 0: # Check limit > 0 to avoid highlighting if limit is 0
                 return QColor("red")

        elif role == Qt.ItemDataRole.UserRole: # Custom role to get the full customer object
            return customer

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Returns the header data."""
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            try:
                return self.HEADERS[section]
            except IndexError:
                return None
        return None

    def update_data(self, customers: List[Customer]):
        """Updates the model's data and refreshes the view."""
        self.beginResetModel()
        # Sort by name by default
        self._customers = sorted(customers, key=lambda c: c.name or "")
        self.endResetModel()

    def get_customer_at_row(self, row: int) -> Optional[Customer]:
        """Gets the customer object at a specific model row."""
        if 0 <= row < len(self._customers):
            return self._customers[row]
        return None 

class SupplierTableModel(QAbstractTableModel):
    def __init__(self, data: List[Supplier] = [], parent=None):
        super().__init__(parent)
        self._data = data
        self._headers = ["ID", "Nombre", "CUIT", "Contacto", "Teléfono", "Email", "Dirección"]

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()
        supplier = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return str(supplier.id)
            elif col == 1:
                return supplier.name
            elif col == 2:
                return supplier.cuit or ""
            elif col == 3:
                return supplier.contact_person or "" # Changed from contact_name
            elif col == 4:
                return supplier.phone or ""
            elif col == 5:
                return supplier.email or ""
            elif col == 6:
                return supplier.address or ""
            return None
        elif role == Qt.ItemDataRole.TextAlignmentRole:
             if col == 0:
                return Qt.AlignmentFlag.AlignCenter
             return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        # Add more roles if needed (e.g., background color)
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return None

    def update_data(self, data: List[Supplier]):
        self.beginResetModel()
        self._data = data
        self.endResetModel()

    def get_supplier(self, row: int) -> Optional[Supplier]:
        if 0 <= row < len(self._data):
            return self._data[row]
        return None 

class PurchaseOrderTableModel(QAbstractTableModel):
    def __init__(self, data: List[PurchaseOrder] = [], parent=None):
        super().__init__(parent)
        self._data = data
        self._headers = ["ID", "Proveedor", "Fecha Orden", "Fecha Est.", "Estado", "Total"]

    def rowCount(self, parent=QModelIndex()) -> int: return len(self._data)
    def columnCount(self, parent=QModelIndex()) -> int: return len(self._headers)
    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal: return self._headers[section]
        return None
    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole: return None
        po = self._data[index.row()]
        col = index.column()
        if col == 0: return str(po.id)
        if col == 1: return po.supplier.name if po.supplier else str(po.supplier_id)
        if col == 2: return po.order_date.strftime("%Y-%m-%d")
        if col == 3: return po.expected_delivery_date.strftime("%Y-%m-%d") if po.expected_delivery_date else ""
        if col == 4: return po.status
        if col == 5: return f"{po.total_amount:.2f}"
        return None
    def update_data(self, data: List[PurchaseOrder]): self.beginResetModel(); self._data = data; self.endResetModel()
    def get_purchase_order(self, row: int) -> PurchaseOrder | None: return self._data[row] if 0 <= row < len(self._data) else None

class PurchaseOrderItemTableModel(QAbstractTableModel):
    def __init__(self, data: List[PurchaseOrderItem] = [], parent=None):
        super().__init__(parent)
        self._data = data
        self._headers = ["ID", "Código", "Descripción", "Cantidad", "Costo Unit.", "Subtotal"]
    def rowCount(self, parent=QModelIndex()) -> int: return len(self._data)
    def columnCount(self, parent=QModelIndex()) -> int: return len(self._headers)
    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal: return self._headers[section]
        return None
    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole: return None
        item = self._data[index.row()]
        col = index.column()
        if col == 0: return str(item.id)
        if col == 1: return item.product_code
        if col == 2: return item.product_description
        if col == 3: return f"{item.quantity_ordered:.2f}" # Changed from quantity
        if col == 4: return f"{item.cost_price:.2f}"
        if col == 5: return f"{item.subtotal:.2f}"
        return None
    def update_data(self, data: List[PurchaseOrderItem]): self.beginResetModel(); self._data = data; self.endResetModel()
    def get_item(self, row: int) -> PurchaseOrderItem | None: return self._data[row] if 0 <= row < len(self._data) else None

class InvoiceTableModel(QAbstractTableModel):
    """Model for displaying invoices in a table view."""
    
    def __init__(self):
        super().__init__()
        self.invoices = []
        self.headers = ["Nro.", "Fecha", "Cliente", "Tipo", "Total", "Estado"]
    
    def rowCount(self, parent=QModelIndex()):
        """Return number of rows in the model."""
        return len(self.invoices)
    
    def columnCount(self, parent=QModelIndex()):
        """Return number of columns in the model."""
        return len(self.headers)
    
    def data(self, index, role=Qt.DisplayRole):
        """Return data for the given role at the specified index."""
        if not index.isValid() or not (0 <= index.row() < len(self.invoices)):
            return None
            
        invoice = self.invoices[index.row()]
        col = index.column()
        
        if role == Qt.DisplayRole:
            if col == 0:  # Invoice Number
                return invoice.invoice_number
            elif col == 1:  # Date
                return invoice.invoice_date.strftime('%d/%m/%Y')
            elif col == 2:  # Customer
                customer_name = ""
                if invoice.customer_details and 'name' in invoice.customer_details:
                    customer_name = invoice.customer_details['name']
                return customer_name
            elif col == 3:  # Type
                return f"Factura {invoice.invoice_type}"
            elif col == 4:  # Total
                return f"${invoice.total:.2f}"
            elif col == 5:  # Status
                return "Activa" if invoice.is_active else "Anulada"
        
        elif role == Qt.TextAlignmentRole:
            if col in [0, 1, 3, 5]:  # Number, Date, Type, Status
                return int(Qt.AlignCenter)
            elif col == 4:  # Total
                return int(Qt.AlignRight | Qt.AlignVCenter)
            else:
                return int(Qt.AlignLeft | Qt.AlignVCenter)
        
        elif role == Qt.ForegroundRole:
            if not invoice.is_active:
                return QBrush(QColor(150, 150, 150))  # Gray text for inactive invoices
        
        elif role == Qt.BackgroundRole:
            if invoice.invoice_type == 'A':
                return QBrush(QColor(240, 255, 240))  # Light green for Type A
            elif invoice.invoice_type == 'B':
                return QBrush(QColor(240, 240, 255))  # Light blue for Type B
        
        return None
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Return header data for the given role."""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None
    
    def update_data(self, invoices):
        """Update model with new invoice data."""
        self.beginResetModel()
        self.invoices = invoices
        self.endResetModel()

class CashDrawerTableModel(QAbstractTableModel):
    """Table model for displaying cash drawer entries."""
    
    def __init__(self, entries: List[CashDrawerEntry] = None):
        super().__init__()
        self._entries = entries or []
        self._headers = ['ID', 'Fecha/Hora', 'Tipo', 'Monto', 'Descripción', 'Usuario']
        # Configure locale for currency formatting
        locale.setlocale(locale.LC_ALL, '')
        
    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._entries)
        
    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)
        
    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._headers[section]
        return QVariant()
        
    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._entries)):
            return QVariant()
            
        entry = self._entries[index.row()]
        col = index.column()
        
        if role == Qt.DisplayRole:
            if col == 0:  # ID
                return str(entry.id)
            elif col == 1:  # Timestamp
                return entry.timestamp.strftime("%d/%m/%Y %H:%M")
            elif col == 2:  # Type
                type_labels = {
                    CashDrawerEntryType.START: "Apertura",
                    CashDrawerEntryType.IN: "Ingreso",
                    CashDrawerEntryType.OUT: "Retiro"
                }
                return type_labels.get(entry.entry_type, str(entry.entry_type))
            elif col == 3:  # Amount
                return locale.currency(float(entry.amount), grouping=True)
            elif col == 4:  # Description
                return entry.description or ""
            elif col == 5:  # User ID
                return str(entry.user_id or "")
        
        elif role == Qt.BackgroundRole:
            if entry.entry_type == CashDrawerEntryType.START:
                return QBrush(QColor(230, 230, 250))  # Light lavender
            elif entry.entry_type == CashDrawerEntryType.IN:
                return QBrush(QColor(240, 255, 240))  # Light green
            elif entry.entry_type == CashDrawerEntryType.OUT:
                return QBrush(QColor(255, 240, 240))  # Light red
                
        elif role == Qt.TextAlignmentRole:
            if col == 3:  # Amount
                return Qt.AlignRight | Qt.AlignVCenter
            elif col == 0:  # ID
                return Qt.AlignCenter
            return Qt.AlignLeft | Qt.AlignVCenter
                
        return QVariant()
        
    def update_entries(self, entries: List[CashDrawerEntry]):
        """Update the model with new entries."""
        self.beginResetModel()
        self._entries = entries
        self.endResetModel()
        
    def get_entry_at_row(self, row: int) -> Optional[CashDrawerEntry]:
        """Get the entry at the specified row."""
        if 0 <= row < len(self._entries):
            return self._entries[row]
        return None

class CashDrawerEntryTableModel(QAbstractTableModel):
    """Table model for displaying cash drawer entries in the Corte View."""
    
    def __init__(self):
        super().__init__()
        self.entries: List[CashDrawerEntry] = []
        self.headers = ["Hora", "Descripción", "Usuario", "Monto"]
    
    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.entries)
    
    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.headers)
    
    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole) -> Any:
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None
    
    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self.entries)):
            return None
        
        entry = self.entries[index.row()]
        column = index.column()
        
        if role == Qt.DisplayRole:
            if column == 0:  # Time
                return entry.timestamp.strftime("%H:%M:%S")
            elif column == 1:  # Description
                return entry.description
            elif column == 2:  # User
                return f"Usuario #{entry.user_id}"
            elif column == 3:  # Amount
                return f"${entry.amount:.2f}"
        
        elif role == Qt.TextAlignmentRole:
            if column == 3:  # Align amount to the right
                return int(Qt.AlignRight | Qt.AlignVCenter)
            return int(Qt.AlignLeft | Qt.AlignVCenter)
        
        return None
    
    def update_data(self, entries: List[CashDrawerEntry]):
        """Update the model with new data."""
        self.beginResetModel()
        self.entries = entries or []
        self.endResetModel()

class ReportTableModel(QAbstractTableModel):
    """Table model for displaying report data."""
    
    def __init__(self, data: List[List[Any]], headers: List[str], parent=None):
        super().__init__(parent)
        self._data = data or []
        self._headers = headers or []
    
    def rowCount(self, parent=QModelIndex()) -> int:
        """Return the number of rows in the model."""
        if parent.isValid():
            return 0
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()) -> int:
        """Return the number of columns in the model."""
        if parent.isValid():
            return 0
        return len(self._headers) if self._headers else 0
    
    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> Any:
        """Return the data at the specified index."""
        if not index.isValid() or not (0 <= index.row() < len(self._data)):
            return None
        
        row = index.row()
        col = index.column()
        
        if role == Qt.DisplayRole:
            return self._data[row][col]
        elif role == Qt.TextAlignmentRole:
            # Right-align columns that are likely to contain numeric values
            if col > 0:
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter
            
        return None
    
    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole) -> Any:
        """Return the header data for the specified section."""
        if role != Qt.DisplayRole:
            return None
        
        if orientation == Qt.Horizontal and 0 <= section < len(self._headers):
            return self._headers[section]
        
        # Row numbers for vertical headers
        if orientation == Qt.Vertical:
            return section + 1
        
        return None
