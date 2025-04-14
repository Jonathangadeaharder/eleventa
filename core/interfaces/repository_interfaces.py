from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal
from core.models.user import User # Moved User import outside try/except

# Adjust path if necessary to import core models
try:
    from ..models.product import Product, Department
    from ..models.inventory import InventoryMovement
    from ..models.sale import Sale, SaleItem
    from ..models.customer import Customer
    from ..models.credit import CreditPayment
    from ..models.supplier import Supplier
    from ..models.purchase import PurchaseOrder, PurchaseOrderItem
    from ..models.invoice import Invoice # Add Invoice model import
    from ..models.cash_drawer import CashDrawerEntry
except ImportError:
    # Fallback for different import contexts
    from core.models.product import Product, Department
    from core.models.inventory import InventoryMovement
    from core.models.sale import Sale, SaleItem
    from core.models.customer import Customer
    from core.models.credit import CreditPayment
    from core.models.supplier import Supplier
    from core.models.purchase import PurchaseOrder, PurchaseOrderItem
    from core.models.invoice import Invoice # Add Invoice model import
    from core.models.cash_drawer import CashDrawerEntry
    # Removed User import from here

class IDepartmentRepository(ABC):
    """Interface for department data access operations."""

    @abstractmethod
    def add(self, department: Department) -> Department:
        """Adds a new department to the repository."""
        pass

    @abstractmethod
    def get_by_id(self, department_id: uuid.UUID) -> Optional[Department]:
        """Retrieves a department by its unique ID."""
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Department]:
        """Retrieves a department by its name."""
        pass

    @abstractmethod
    def get_all(self) -> List[Department]:
        """Retrieves all departments, typically ordered by name."""
        pass

    @abstractmethod
    def update(self, department: Department) -> Optional[Department]:
        """Updates an existing department."""
        pass

    @abstractmethod
    def delete(self, department_id: uuid.UUID) -> bool:
        """Deletes a department by its ID."""
        pass


class IProductRepository(ABC):
    """Interface for product data access operations."""

    @abstractmethod
    def add(self, product: Product) -> Product:
        """Adds a new product to the repository."""
        pass

    @abstractmethod
    def get_by_id(self, product_id: uuid.UUID) -> Optional[Product]:
        """Retrieves a product by its unique ID."""
        pass

    @abstractmethod
    def get_by_code(self, code: str) -> Optional[Product]:
        """Retrieves a product by its code."""
        pass

    @abstractmethod
    def get_all(self) -> List[Product]:
        """Retrieves all products, typically ordered."""
        pass

    @abstractmethod
    def update(self, product: Product) -> Optional[Product]:
        """Updates an existing product."""
        pass

    @abstractmethod
    def delete(self, product_id: uuid.UUID) -> bool:
        """Deletes a product by its ID."""
        pass

    @abstractmethod
    def search(self, query: str) -> List[Product]:
        """Searches for products based on a term (e.g., code or description)."""
        pass

    @abstractmethod
    def get_low_stock(self, limit: int = 50) -> List[Product]:
        """Retrieves products that are below their minimum stock level or a given threshold."""
        pass

    @abstractmethod
    def update_stock(self, product_id: uuid.UUID, quantity_change: float, cost_price: Optional[float] = None) -> Optional[Product]:
        """Updates only the stock quantity of a specific product."""
        pass

# Define other repository interfaces here as needed (e.g., ISaleRepository, IUserRepository)

class IInventoryRepository(ABC):
    """Interface for inventory movement data access operations."""

    @abstractmethod
    def add_movement(self, movement: InventoryMovement) -> InventoryMovement:
        """Adds a new inventory movement record."""
        pass

    @abstractmethod
    def get_movements_for_product(self, product_id: uuid.UUID, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[InventoryMovement]:
        """Retrieves all inventory movements for a specific product, typically ordered by timestamp."""
        pass

    @abstractmethod
    def get_all_movements(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[InventoryMovement]:
        """Retrieves all inventory movements."""
        pass

# --- Add Sale Repository Interface ---

class ISaleRepository(ABC):
    """Interface for sale data access operations."""

    @abstractmethod
    def add_sale(self, sale: Sale) -> Sale:
        """Adds a new sale (including its items) to the repository."""
        pass
    
    @abstractmethod
    def get_sales_by_period(self, start_time: datetime, end_time: datetime) -> List[Sale]:
        """
        Retrieves all sales within the specified time period.
        
        Args:
            start_time: The start of the period
            end_time: The end of the period
            
        Returns:
            List of Sale objects within the time period
        """
        pass
    
    @abstractmethod
    def get_sale_by_id(self, sale_id: int) -> Optional[Sale]:
        """
        Retrieves a single sale by its ID.
        
        Args:
            sale_id: The ID of the sale to retrieve
            
        Returns:
            The requested Sale object or None if not found
        """
        pass
    
    @abstractmethod
    def get_sales_summary_by_period(self, start_time: datetime, end_time: datetime, 
                                   group_by: str = 'day') -> List[Dict[str, Any]]:
        """
        Retrieves aggregated sales data grouped by a time period.
        
        Args:
            start_time: The start of the period
            end_time: The end of the period
            group_by: Time grouping ('day', 'week', 'month')
            
        Returns:
            List of dictionaries with aggregated sales data
            Example: [{'date': '2023-01-01', 'total_sales': 1500.0, 'num_sales': 5}, ...]
        """
        pass
    
    @abstractmethod
    def get_sales_by_payment_type(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """
        Retrieves sales data aggregated by payment type for a period.
        
        Args:
            start_time: The start of the period
            end_time: The end of the period
            
        Returns:
            List of dictionaries with payment type data
            Example: [{'payment_type': 'Cash', 'total_amount': 1200.0, 'num_sales': 4}, ...]
        """
        pass
    
    @abstractmethod
    def get_sales_by_department(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """
        Retrieves sales data aggregated by product department for a period.
        
        Args:
            start_time: The start of the period
            end_time: The end of the period
            
        Returns:
            List of dictionaries with department sales data
            Example: [{'department_id': 1, 'department_name': 'Electronics', 'total_amount': 2500.0, 'num_items': 10}, ...]
        """
        pass
    
    @abstractmethod
    def get_sales_by_customer(self, start_time: datetime, end_time: datetime, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieves sales data aggregated by customer for a period.
        
        Args:
            start_time: The start of the period
            end_time: The end of the period
            limit: Maximum number of customers to return (top customers by sales)
            
        Returns:
            List of dictionaries with customer sales data
            Example: [{'customer_id': 1, 'customer_name': 'John Doe', 'total_amount': 1500.0, 'num_sales': 3}, ...]
        """
        pass
        
    @abstractmethod
    def get_top_selling_products(self, start_time: datetime, end_time: datetime, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieves the top selling products for a period.
        
        Args:
            start_time: The start of the period
            end_time: The end of the period
            limit: Maximum number of products to return
            
        Returns:
            List of dictionaries with product sales data
            Example: [{'product_id': 1, 'product_code': 'P001', 'product_description': 'TV 42"', 'quantity_sold': 5, 'total_amount': 2500.0}, ...]
        """
        pass
        
    @abstractmethod
    def calculate_profit_for_period(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """
        Calculates the total profit for a period (revenue - cost).
        
        Args:
            start_time: The start of the period
            end_time: The end of the period
            
        Returns:
            Dictionary with profit data
            Example: {'total_revenue': 5000.0, 'total_cost': 3000.0, 'total_profit': 2000.0, 'profit_margin': 0.4}
        """
        pass

# --- Customer Repository ---

class ICustomerRepository(ABC):
    """Interface for customer data access operations."""

    @abstractmethod
    def add(self, customer: Customer) -> Customer:
        """Adds a new customer to the repository."""
        pass

    @abstractmethod
    def get_by_id(self, customer_id: uuid.UUID) -> Optional[Customer]:
        """Retrieves a customer by their unique ID."""
        pass

    @abstractmethod
    def get_all(self) -> List[Customer]:
        """Retrieves all customers."""
        pass

    @abstractmethod
    def update(self, customer: Customer) -> Optional[Customer]:
        """Updates an existing customer's details."""
        pass

    @abstractmethod
    def delete(self, customer_id: uuid.UUID) -> bool:
        """Deletes a customer by their ID. Returns True if successful, False otherwise."""
        pass

    @abstractmethod
    def search(self, search_term: str) -> List[Customer]:
        """Searches for customers by name (case-insensitive partial match)."""
        pass

    @abstractmethod
    def get_by_cuit(self, cuit: str) -> Optional[Customer]:
        """Retrieves a customer by their CUIT."""
        pass

    @abstractmethod
    def update_balance(self, customer_id: int, new_balance: float) -> bool:
        """Updates only the credit balance for a customer."""
        pass

# New interface for Credit Payments
class ICreditPaymentRepository(ABC):
    @abstractmethod
    def add(self, payment: CreditPayment) -> CreditPayment:
        """Adds a new credit payment record."""
        pass

    @abstractmethod
    def get_by_id(self, payment_id: int) -> Optional[CreditPayment]:
        """Gets a credit payment by its ID."""
        pass

    @abstractmethod
    def get_for_customer(self, customer_id: int) -> List[CreditPayment]:
        """Gets all credit payments for a specific customer."""
        pass

# Potentially add other repositories here (User, Invoice, etc.) 

class ISupplierRepository(ABC):
    @abstractmethod
    def add(self, supplier: Supplier) -> Supplier:
        pass

    @abstractmethod
    def get_by_id(self, supplier_id: int) -> Optional[Supplier]:
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Supplier]:
        pass

    @abstractmethod
    def get_by_cuit(self, cuit: str) -> Optional[Supplier]:
        pass

    @abstractmethod
    def get_all(self) -> List[Supplier]:
        pass

    @abstractmethod
    def update(self, supplier: Supplier) -> Optional[Supplier]:
        pass

    @abstractmethod
    def delete(self, supplier_id: int) -> bool:
        pass

    @abstractmethod
    def search(self, query: str) -> List[Supplier]:
        pass


class IPurchaseOrderRepository(ABC):
    @abstractmethod
    def add(self, purchase_order: PurchaseOrder) -> PurchaseOrder:
        pass

    @abstractmethod
    def get_by_id(self, po_id: int) -> Optional[PurchaseOrder]:
        pass

    @abstractmethod
    def get_all(self, status: str | None = None, supplier_id: int | None = None) -> List[PurchaseOrder]:
        pass

    @abstractmethod
    def update_status(self, po_id: int, status: str) -> bool:
        pass

    @abstractmethod
    def get_items(self, po_id: int) -> List[PurchaseOrderItem]:
        pass

    # Potentially add methods to update items, delete POs etc. later


# --- User Repository ---
class IUserRepository(ABC):
    """Interface for user data access operations."""

    @abstractmethod
    def add(self, user: User) -> User:
        """Adds a new user."""
        pass

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Retrieves a user by their ID."""
        pass

    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]:
        """Retrieves a user by their username."""
        pass

    @abstractmethod
    def update(self, user: User) -> Optional[User]:
        """Updates an existing user."""
        pass

    @abstractmethod
    def delete(self, user_id: int) -> bool:
        """Deletes a user by ID."""
        pass

    @abstractmethod
    def get_all(self) -> List[User]:
        """Retrieves all users."""
        pass

# --- Invoice Repository Interface ---
class IInvoiceRepository(ABC):
    """Interface for invoice data access operations."""
    
    @abstractmethod
    def add(self, invoice: Invoice) -> Invoice:
        """Adds a new invoice to the repository."""
        pass
        
    @abstractmethod
    def get_by_id(self, invoice_id: int) -> Optional[Invoice]:
        """Retrieves an invoice by its unique ID."""
        pass
        
    @abstractmethod
    def get_by_sale_id(self, sale_id: int) -> Optional[Invoice]:
        """Retrieves an invoice by its associated sale ID."""
        pass
        
    @abstractmethod
    def get_all(self) -> List[Invoice]:
        """Retrieves all invoices."""
        pass

# --- Cash Drawer Repository Interface ---
class ICashDrawerRepository(ABC):
    """Repository interface for cash drawer operations."""

    @abstractmethod
    def add_entry(self, entry: CashDrawerEntry) -> CashDrawerEntry:
        """Adds a new cash drawer entry."""
        pass

    @abstractmethod
    def get_entries_by_date_range(self, start_date: datetime, end_date: datetime) -> List[CashDrawerEntry]:
        """Retrieves cash drawer entries within a date range."""
        pass

    @abstractmethod
    def get_entries_by_type(self, entry_type: str, start_date: Optional[datetime] = None, 
                            end_date: Optional[datetime] = None) -> List[CashDrawerEntry]:
        """Retrieves cash drawer entries of a specific type."""
        pass
        
    @abstractmethod
    def get_last_start_entry(self, drawer_id: Optional[int] = None) -> Optional[CashDrawerEntry]:
        """Gets the most recent START entry for the drawer."""
        pass
        
    @abstractmethod
    def get_entry_by_id(self, entry_id: int) -> Optional[CashDrawerEntry]:
        """Gets a cash drawer entry by its ID."""
        pass
