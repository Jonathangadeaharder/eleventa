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
# from core.models.supplier import Supplier # Removed
# from core.models.purchase import PurchaseOrder, PurchaseOrderItem # Removed
from core.models.cash_drawer import CashDrawerEntry, CashDrawerEntryType

# Mock Product class until TASK-004 is properly integrated
@dataclass
class Product:
    id: int
    code: str
    description: str
    cost_price: float
    sell_price: float
    department_id: Optional[int] = None
    department: Optional['Department'] = None
    quantity_in_stock: float = 0.0
    min_stock: float = 0.0
    uses_inventory: bool = True
    unit: str = "U"

# Add mock Department class for completeness
@dataclass
class Department:
    id: Optional[int] = None
    name: str = ""

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
                return f"{product.sell_price:.2f}" if product.sell_price is not None else "N/A"
            elif column == 3:
                return f"{product.quantity_in_stock:.2f}" if product.uses_inventory else "N/A"
            elif column == 4:
                return f"{product.min_stock:.2f}" if product.uses_inventory else "N/A"
            elif column == 5:
                # Check for department object first
                if hasattr(product, 'department') and product.department is not None:
                    return product.department.name
                # Fall back to department_id if department_name doesn't exist
                if hasattr(product, 'department_id') and product.department_id is not None:
                    return f"Depto #{product.department_id}"
                return "-"
            elif column == 6:
                return f"{product.cost_price:.2f}" if product.cost_price is not None else "N/A"

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if column in [2, 3, 4, 6]: # Price/Stock columns
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        elif role == Qt.ItemDataRole.ForegroundRole:
            if product.uses_inventory and product.min_stock is not None and product.quantity_in_stock < product.min_stock:
                return QColor("red") # Low stock highlighting
            # No need to return None here - will fallthrough to other conditions

        elif role == Qt.ItemDataRole.BackgroundRole:
            # Add subtle background color for alternating rows
            if index.row() % 2 == 0:
                return QBrush(QColor(248, 249, 250))  # Light gray for even rows
            # Odd rows will use the default background from stylesheet

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

    def get_item_at_row(self, row: int) -> Optional[SaleItem]:
         """Gets the SaleItem object at a specific model row."""
         if 0 <= row < len(self._items):
             return self._items[row]
         return None

    def clear(self):
         """Clears all items from the model."""
         self.beginResetModel()
         self._items = []
         self.endResetModel()

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
                return customer.phone
            elif column == 2:
                return customer.email
            elif column == 3:
                return customer.address
            elif column == 4:
                # Format as currency
                return locale.currency(customer.credit_balance, grouping=True) if customer.credit_balance is not None else "N/A"
            elif column == 5:
                return locale.currency(customer.credit_limit, grouping=True) if customer.credit_limit is not None else "N/A"

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if column in [4, 5]: # Numeric columns
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        elif role == Qt.ItemDataRole.UserRole: # Custom role to get the full Customer object
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
        self._customers = sorted(customers, key=lambda c: c.name) # Sort by name
        self.endResetModel()

    def get_customer_at_row(self, row: int) -> Optional[Customer]:
        """Gets the customer object at a specific model row."""
        if 0 <= row < len(self._customers):
            return self._customers[row]
        return None

# class SupplierTableModel(QAbstractTableModel):
#     HEADERS = ["Nombre", "Teléfono", "Email", "CUIT", "Activo"]
# 
#     def __init__(self, data: List[Supplier] = [], parent=None):
#         super().__init__(parent)
#         self._suppliers: List[Supplier] = data
# 
#     def rowCount(self, parent=QModelIndex()) -> int:
#         return len(self._suppliers)
# 
#     def columnCount(self, parent=QModelIndex()) -> int:
#         return len(self.HEADERS)
# 
#     def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
#         if not index.isValid():
#             return None
# 
#         supplier = self._suppliers[index.row()]
#         column = index.column()
# 
#         if role == Qt.ItemDataRole.DisplayRole:
#             if column == 0:
#                 return supplier.name
#             elif column == 1:
#                 return supplier.phone
#             elif column == 2:
#                 return supplier.email
#             elif column == 3:
#                 return supplier.cuit
#             elif column == 4:
#                 return "Sí" if supplier.is_active else "No"
# 
#         elif role == Qt.ItemDataRole.TextAlignmentRole:
#             if column == 4: # Activo
#                 return Qt.AlignmentFlag.AlignCenter
#             return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
# 
#         elif role == Qt.ItemDataRole.UserRole:
#             return supplier
#         return None
# 
#     def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Any:
#         if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
#             return self.HEADERS[section]
#         return None
# 
#     def update_data(self, data: List[Supplier]):
#         self.beginResetModel()
#         self._suppliers = sorted(data, key=lambda s: s.name)
#         self.endResetModel()
# 
#     def get_supplier(self, row: int) -> Optional[Supplier]:
#         if 0 <= row < len(self._suppliers):
#             return self._suppliers[row]
#         return None
# 
# class PurchaseOrderTableModel(QAbstractTableModel):
#     HEADERS = ["ID", "Proveedor", "Fecha Pedido", "Fecha Entrega", "Estado", "Total"]
# 
#     def __init__(self, data: List[PurchaseOrder] = [], parent=None):
#         super().__init__(parent)
#         self._orders: List[PurchaseOrder] = data
#         # You might want to fetch supplier names or have them denormalized in PurchaseOrder
# 
#     # Implement rowCount, columnCount, data, headerData as needed
#     # Example data method (simplified):
#     def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Any:
#         if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
#             return self.HEADERS[section]
#         return None
#     def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
#         # Basic implementation, expand as needed
#         if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
#             return None
#         order = self._orders[index.row()]
#         column = index.column()
#         if column == 0: return order.id
#         if column == 1: return order.supplier_id # Or supplier name if available
#         if column == 2: return order.order_date.strftime("%Y-%m-%d") if order.order_date else "N/A"
#         # Add other columns
#         return None
# 
# class PurchaseOrderItemTableModel(QAbstractTableModel):
#     HEADERS = ["Producto", "Cantidad Pedida", "Costo Unit.", "Cantidad Recibida"]
# 
#     def __init__(self, data: List[PurchaseOrderItem] = [], parent=None):
#         super().__init__(parent)
#         self._items: List[PurchaseOrderItem] = data
# 
#     # Implement methods similarly to above
#     def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Any:
#         if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
#             return self.HEADERS[section]
#         return None
#     def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
#         if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
#             return None
#         item = self._items[index.row()]
#         column = index.column()
#         if column == 0: return item.product_description # Or product code
#         # Add other columns
#         return None

class InvoiceTableModel(QAbstractTableModel):
    """Model for displaying invoices in a QTableView."""
    HEADERS = [
        "Número", "Fecha", "Cliente", "Tipo", "Total", "CAE"
    ]

    def __init__(self):
        super().__init__()
        self._invoices: List[Invoice] = [] # Initialize with Invoice type

    def rowCount(self, parent=QModelIndex()):
        return len(self._invoices)

    def columnCount(self, parent=QModelIndex()):
        return len(self.HEADERS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        invoice = self._invoices[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == 0:
                return invoice.invoice_number
            elif col == 1:
                return invoice.invoice_date.strftime("%d/%m/%Y") if invoice.invoice_date else ""
            elif col == 2:
                # Assuming customer_details is a dict with a 'name' key
                return invoice.customer_details.get("name", "N/A") if invoice.customer_details else "N/A"
            elif col == 3:
                return invoice.invoice_type
            elif col == 4:
                return f"{invoice.total:.2f}" # Format as currency
            elif col == 5:
                return invoice.cae if invoice.cae else "N/A"
        
        elif role == Qt.TextAlignmentRole:
            if col == 4: # Total
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter
            
        elif role == Qt.UserRole: # To get the full Invoice object
            return invoice
            
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.HEADERS[section]
        return None

    def update_data(self, invoices):
        self.beginResetModel()
        self._invoices = sorted(invoices, key=lambda inv: inv.invoice_date, reverse=True)
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
        return None
        
    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._entries)):
            return None
            
        entry = self._entries[index.row()]
        col = index.column()
        
        if role == Qt.DisplayRole:
            if col == 0:  # ID
                # Check if entry is a dict or an object
                if isinstance(entry, dict):
                    return str(entry.get('id', ''))
                else:
                    return str(getattr(entry, 'id', ''))
            elif col == 1:  # Timestamp
                if isinstance(entry, dict):
                    timestamp = entry.get('timestamp')
                else:
                    timestamp = getattr(entry, 'timestamp', None)
                    
                if timestamp:
                    return timestamp.strftime("%d/%m/%Y %H:%M")
                return ''
            elif col == 2:  # Type
                type_labels = {
                    CashDrawerEntryType.START: "Apertura",
                    CashDrawerEntryType.IN: "Ingreso",
                    CashDrawerEntryType.OUT: "Retiro"
                }
                
                if isinstance(entry, dict):
                    entry_type = entry.get('entry_type')
                else:
                    entry_type = getattr(entry, 'entry_type', None)
                    
                return type_labels.get(entry_type, str(entry_type))
            elif col == 3:  # Amount
                # Handle both dict and object formats
                if isinstance(entry, dict):
                    # If it's already a formatted string
                    if isinstance(entry.get('amount'), str):
                        return entry.get('amount', "$0.00")
                    # If it's a number, format it
                    amount = entry.get('amount', 0)
                else:
                    # If it's an object
                    if hasattr(entry, 'amount'):
                        amount = entry.amount
                    else:
                        amount = 0
                
                # Format the amount if it's not already a string
                if not isinstance(amount, str):
                    return f"${float(amount):,.2f}"
                return amount
            elif col == 4:  # Description
                if isinstance(entry, dict):
                    return entry.get('description', "")
                else:
                    return getattr(entry, 'description', "")
            elif col == 5:  # User ID
                if isinstance(entry, dict):
                    return str(entry.get('user_id', ""))
                else:
                    return str(getattr(entry, 'user_id', ""))
        
        elif role == Qt.BackgroundRole:
            # Get entry_type properly based on type
            if isinstance(entry, dict):
                entry_type = entry.get('entry_type')
            else:
                entry_type = getattr(entry, 'entry_type', None)
                
            # Color based on entry type
            if entry_type == CashDrawerEntryType.START:
                return QBrush(QColor(230, 230, 250))  # Light lavender
            elif entry_type == CashDrawerEntryType.IN:
                return QBrush(QColor(240, 255, 240))  # Light green
            elif entry_type == CashDrawerEntryType.OUT:
                return QBrush(QColor(255, 240, 240))  # Light red
                
        elif role == Qt.TextAlignmentRole:
            if col == 3:  # Amount
                return Qt.AlignRight | Qt.AlignVCenter
            elif col == 0:  # ID
                return Qt.AlignCenter
            return Qt.AlignLeft | Qt.AlignVCenter
                
        return None
        
    def update_entries(self, entries: List[CashDrawerEntry]):
        """Update the model with new entries using granular signals."""
        old_row_count = len(self._entries)
        new_row_count = len(entries)

        # Signal removal of old rows if any existed
        if old_row_count > 0:
            self.beginRemoveRows(QModelIndex(), 0, old_row_count - 1)
            self._entries = [] # Clear existing entries internally before signaling end
            self.endRemoveRows()

        # Update internal data
        self._entries = entries

        # Signal insertion of new rows if any exist
        if new_row_count > 0:
            self.beginInsertRows(QModelIndex(), 0, new_row_count - 1)
            self.endInsertRows()
        
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
