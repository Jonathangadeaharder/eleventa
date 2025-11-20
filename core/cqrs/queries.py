"""
Queries - Read Operations

Queries represent requests for data and never modify state.
They are questions (GetProduct, FindCustomers) and always succeed.

Key Principles:
- Queries never modify state
- Queries use read models (denormalized views)
- Queries can be cached
- Queries are optimized for specific use cases
- Queries may return stale data (eventual consistency)

Usage:
    query = GetProductByCodeQuery(code="LAPTOP001")
    result = query_handler.handle(query)

    if result:
        product = result  # ProductReadModel
    else:
        # Not found (queries return None, not errors)
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import UUID
from datetime import datetime
from abc import ABC


class Query(ABC):
    """
    Base class for all queries.

    Queries represent requests for data and are named as questions
    (Get, Find, Search, List).
    """
    pass


# Product Queries

@dataclass(frozen=True)
class GetProductByIdQuery(Query):
    """
    Query to get a single product by ID.

    Returns: ProductReadModel or None
    """
    product_id: UUID


@dataclass(frozen=True)
class GetProductByCodeQuery(Query):
    """
    Query to get a single product by code.

    Returns: ProductReadModel or None
    """
    code: str


@dataclass(frozen=True)
class SearchProductsQuery(Query):
    """
    Query to search products with filters.

    Returns: List[ProductListItemReadModel]

    This query can be optimized with:
    - Full-text search on code/description
    - Indexed filters
    - Denormalized department names
    """
    search_term: Optional[str] = None
    department_id: Optional[UUID] = None
    in_stock_only: bool = False
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    limit: int = 100
    offset: int = 0


@dataclass(frozen=True)
class GetLowStockProductsQuery(Query):
    """
    Query to get products with low stock.

    Returns: List[ProductListItemReadModel]

    Optimized with:
    - Pre-calculated low stock flags
    - Indexed quantity fields
    """
    department_id: Optional[UUID] = None


@dataclass(frozen=True)
class GetProductsWithPriceChangesQuery(Query):
    """
    Query to get products with recent price changes.

    Returns: List[ProductPriceHistoryReadModel]

    This uses a denormalized price history view.
    """
    days: int = 7
    department_id: Optional[UUID] = None


@dataclass(frozen=True)
class GetProductInventoryValueQuery(Query):
    """
    Query to calculate total inventory value.

    Returns: InventoryValueReadModel

    Optimized with:
    - Pre-calculated stock values
    - Aggregated by department
    """
    department_id: Optional[UUID] = None


# Sale Queries

@dataclass(frozen=True)
class GetSaleByIdQuery(Query):
    """
    Query to get sale details by ID.

    Returns: SaleReadModel or None
    """
    sale_id: UUID


@dataclass(frozen=True)
class GetSalesByDateRangeQuery(Query):
    """
    Query to get sales within a date range.

    Returns: List[SaleSummaryReadModel]

    Optimized for reporting with denormalized data.
    """
    start_date: datetime
    end_date: datetime
    customer_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    payment_type: Optional[str] = None


@dataclass(frozen=True)
class GetSalesSummaryQuery(Query):
    """
    Query to get aggregated sales summary.

    Returns: SalesSummaryReadModel

    Includes:
    - Total sales amount
    - Number of transactions
    - Average transaction value
    - By payment type
    - By time period
    """
    start_date: datetime
    end_date: datetime
    group_by: str = "day"  # day, week, month


@dataclass(frozen=True)
class GetTopSellingProductsQuery(Query):
    """
    Query to get best-selling products.

    Returns: List[TopProductReadModel]

    Uses denormalized sales data aggregated by product.
    """
    start_date: datetime
    end_date: datetime
    limit: int = 10
    department_id: Optional[UUID] = None


# Customer Queries

@dataclass(frozen=True)
class GetCustomerByIdQuery(Query):
    """
    Query to get customer details.

    Returns: CustomerReadModel or None
    """
    customer_id: UUID


@dataclass(frozen=True)
class SearchCustomersQuery(Query):
    """
    Query to search customers.

    Returns: List[CustomerListItemReadModel]
    """
    search_term: Optional[str] = None
    has_balance: Optional[bool] = None
    limit: int = 100
    offset: int = 0


@dataclass(frozen=True)
class GetCustomersWithCreditQuery(Query):
    """
    Query to get customers with outstanding credit.

    Returns: List[CustomerCreditReadModel]

    Optimized for credit management.
    """
    min_balance: Optional[Decimal] = None
    over_limit: bool = False


@dataclass(frozen=True)
class GetCustomerPurchaseHistoryQuery(Query):
    """
    Query to get customer purchase history.

    Returns: CustomerPurchaseHistoryReadModel

    Includes:
    - Recent purchases
    - Total spent
    - Favorite products
    """
    customer_id: UUID
    limit: int = 50


# Dashboard/Analytics Queries

@dataclass(frozen=True)
class GetDashboardSummaryQuery(Query):
    """
    Query to get dashboard summary data.

    Returns: DashboardSummaryReadModel

    Includes:
    - Today's sales
    - Low stock alerts
    - Recent transactions
    - Key metrics

    This is heavily cached and uses denormalized views.
    """
    date: Optional[datetime] = None


@dataclass(frozen=True)
class GetInventoryReportQuery(Query):
    """
    Query to get comprehensive inventory report.

    Returns: InventoryReportReadModel

    Includes:
    - Stock levels by product/department
    - Inventory value
    - Low stock items
    - Fast/slow movers
    """
    department_id: Optional[UUID] = None
    include_zero_stock: bool = False


@dataclass(frozen=True)
class GetSalesReportQuery(Query):
    """
    Query to get comprehensive sales report.

    Returns: SalesReportReadModel

    Includes:
    - Sales by period
    - Sales by product/department
    - Payment types breakdown
    - User performance
    """
    start_date: datetime
    end_date: datetime
    group_by: str = "day"
    department_id: Optional[UUID] = None
