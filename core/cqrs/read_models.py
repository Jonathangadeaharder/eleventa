"""
Read Models - Denormalized Views

Read models are denormalized data structures optimized for queries.
They may contain data from multiple aggregates and are designed for
specific read use cases.

Key Principles:
- Read models are immutable (frozen dataclasses)
- Read models may be stale (eventual consistency)
- Read models can be cached aggressively
- Read models are optimized for display
- Read models may contain computed/aggregated data

Benefits:
- Fast queries (no joins needed)
- Simple query logic
- Easy to cache
- Optimized for specific UIs

Usage:
    # Query returns read model
    product = query_handler.handle(GetProductByIdQuery(id))

    # Display in UI
    print(f"{product.code}: {product.description}")
    print(f"Price: ${product.sell_price}")
    print(f"In Stock: {product.in_stock}")
    print(f"Department: {product.department_name}")  # Denormalized!
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from datetime import datetime


# Product Read Models

@dataclass(frozen=True)
class ProductReadModel:
    """
    Complete product read model for detail views.

    This is a denormalized view that includes:
    - Product data
    - Department name (denormalized)
    - Stock status (computed)
    - Unit name (denormalized)
    """
    id: UUID
    code: str
    description: str
    sell_price: Decimal
    cost_price: Optional[Decimal]
    quantity_in_stock: Decimal
    min_stock: Optional[Decimal]
    max_stock: Optional[Decimal]
    uses_inventory: bool

    # Denormalized fields
    department_id: Optional[UUID]
    department_name: Optional[str]  # Denormalized from Department
    unit_id: Optional[UUID]
    unit_name: Optional[str]  # Denormalized from Unit

    # Computed fields
    in_stock: bool  # quantity_in_stock > 0
    is_low_stock: bool  # quantity_in_stock < min_stock
    stock_value: Decimal  # quantity_in_stock * cost_price

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass(frozen=True)
class ProductListItemReadModel:
    """
    Lightweight product read model for list views.

    Optimized for displaying lists with minimal data.
    """
    id: UUID
    code: str
    description: str
    sell_price: Decimal
    quantity_in_stock: Decimal
    department_name: Optional[str]
    in_stock: bool
    is_low_stock: bool


@dataclass(frozen=True)
class ProductPriceHistoryReadModel:
    """
    Read model for product price history.

    Denormalized view from price change events.
    """
    product_id: UUID
    product_code: str
    product_description: str
    old_price: Decimal
    new_price: Decimal
    price_change_percent: Decimal
    changed_at: datetime
    changed_by_user_id: UUID
    changed_by_user_name: str  # Denormalized


# Sale Read Models

@dataclass(frozen=True)
class SaleItemReadModel:
    """Read model for a sale item."""
    product_id: UUID
    product_code: str
    product_description: str
    quantity: Decimal
    unit_price: Decimal
    subtotal: Decimal


@dataclass(frozen=True)
class SaleReadModel:
    """
    Complete sale read model for detail views.

    Denormalized with customer and user information.
    """
    id: UUID
    sale_number: Optional[str]  # Human-readable sale number
    total: Decimal
    payment_type: str
    paid_amount: Decimal
    change_amount: Decimal
    created_at: datetime

    # Denormalized customer data
    customer_id: Optional[UUID]
    customer_name: Optional[str]  # Denormalized from Customer

    # Denormalized user data
    user_id: Optional[UUID]
    user_name: Optional[str]  # Denormalized from User

    # Items
    items: List[SaleItemReadModel]

    # Computed
    item_count: int  # len(items)
    is_credit_sale: bool  # payment_type == 'credit'


@dataclass(frozen=True)
class SaleSummaryReadModel:
    """
    Lightweight sale read model for lists and reports.

    Excludes items for performance.
    """
    id: UUID
    sale_number: Optional[str]
    total: Decimal
    payment_type: str
    created_at: datetime
    customer_name: Optional[str]
    user_name: Optional[str]
    item_count: int


@dataclass(frozen=True)
class TopProductReadModel:
    """
    Read model for top-selling products.

    Aggregated from sales data.
    """
    product_id: UUID
    product_code: str
    product_description: str
    total_quantity_sold: Decimal
    total_revenue: Decimal
    number_of_sales: int
    average_sale_quantity: Decimal


# Customer Read Models

@dataclass(frozen=True)
class CustomerReadModel:
    """
    Complete customer read model.

    Includes purchase statistics.
    """
    id: UUID
    name: str
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    balance: Decimal
    credit_limit: Decimal

    # Computed
    available_credit: Decimal  # credit_limit - balance
    over_limit: bool  # balance > credit_limit

    # Statistics (denormalized)
    total_purchases: Decimal
    purchase_count: int
    last_purchase_date: Optional[datetime]

    # Metadata
    created_at: Optional[datetime] = None


@dataclass(frozen=True)
class CustomerListItemReadModel:
    """Lightweight customer read model for lists."""
    id: UUID
    name: str
    phone: Optional[str]
    balance: Decimal
    credit_limit: Decimal
    over_limit: bool


@dataclass(frozen=True)
class CustomerCreditReadModel:
    """
    Read model for customer credit management.

    Optimized for accounts receivable.
    """
    customer_id: UUID
    customer_name: str
    customer_phone: Optional[str]
    balance: Decimal
    credit_limit: Decimal
    available_credit: Decimal
    days_outstanding: Optional[int]
    last_payment_date: Optional[datetime]


# Dashboard/Analytics Read Models

@dataclass(frozen=True)
class DashboardSummaryReadModel:
    """
    Dashboard summary with key metrics.

    Heavily cached, updated periodically.
    """
    # Today's metrics
    today_sales_total: Decimal
    today_sales_count: int
    today_avg_sale: Decimal

    # This week
    week_sales_total: Decimal
    week_sales_count: int

    # This month
    month_sales_total: Decimal
    month_sales_count: int

    # Inventory
    low_stock_product_count: int
    total_inventory_value: Decimal

    # Recent sales (last 10)
    recent_sales: List[SaleSummaryReadModel]

    # Alerts
    low_stock_products: List[ProductListItemReadModel]
    customers_over_limit: List[CustomerCreditReadModel]


@dataclass(frozen=True)
class InventoryValueReadModel:
    """
    Inventory value aggregation.

    Can be broken down by department.
    """
    total_products: int
    total_quantity: Decimal
    total_value: Decimal
    department_id: Optional[UUID] = None
    department_name: Optional[str] = None


@dataclass(frozen=True)
class SalesSummaryReadModel:
    """
    Aggregated sales summary for a time period.
    """
    period: str  # "2024-01-15" or "2024-W03" or "2024-01"
    total_sales: Decimal
    sales_count: int
    average_sale: Decimal
    cash_sales: Decimal
    credit_sales: Decimal
    card_sales: Decimal


@dataclass(frozen=True)
class InventoryReportReadModel:
    """
    Comprehensive inventory report.
    """
    total_products: int
    total_inventory_value: Decimal
    low_stock_items: List[ProductListItemReadModel]
    by_department: List[InventoryValueReadModel]
    fast_movers: List[TopProductReadModel]  # High turnover
    slow_movers: List[ProductListItemReadModel]  # Low turnover


@dataclass(frozen=True)
class SalesReportReadModel:
    """
    Comprehensive sales report.
    """
    start_date: datetime
    end_date: datetime
    total_sales: Decimal
    sales_count: int
    average_sale: Decimal
    by_period: List[SalesSummaryReadModel]
    by_payment_type: dict  # {payment_type: total}
    top_products: List[TopProductReadModel]


@dataclass(frozen=True)
class CustomerPurchaseHistoryReadModel:
    """
    Customer purchase history.
    """
    customer_id: UUID
    customer_name: str
    total_spent: Decimal
    purchase_count: int
    average_purchase: Decimal
    first_purchase_date: Optional[datetime]
    last_purchase_date: Optional[datetime]
    recent_purchases: List[SaleSummaryReadModel]
    favorite_products: List[TopProductReadModel]  # Most frequently purchased
