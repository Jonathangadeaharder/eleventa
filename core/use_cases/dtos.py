"""
Data Transfer Objects (DTOs) for Use Cases

DTOs are simple data containers used to transfer data between layers.
They decouple the presentation layer from domain models.

Benefits:
- Validation at the boundary
- Clear API contract
- Version tolerance
- Transformation flexibility
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from datetime import datetime


# Product Use Case DTOs


@dataclass
class CreateProductRequest:
    """Request to create a new product."""

    code: str
    description: str
    sell_price: Decimal
    cost_price: Optional[Decimal] = None
    department_id: Optional[UUID] = None
    uses_inventory: bool = True
    quantity_in_stock: Decimal = Decimal("0")
    min_stock: Optional[Decimal] = None
    max_stock: Optional[Decimal] = None
    unit_id: Optional[UUID] = None
    user_id: Optional[UUID] = None

    def to_domain(self):
        """Convert to domain Product model."""
        from core.models.product import Product

        return Product(
            code=self.code,
            description=self.description,
            sell_price=self.sell_price,
            cost_price=self.cost_price,
            department_id=self.department_id,
            uses_inventory=self.uses_inventory,
            quantity_in_stock=self.quantity_in_stock,
            min_stock=self.min_stock,
            max_stock=self.max_stock,
            unit_id=self.unit_id,
        )


@dataclass
class UpdateProductRequest:
    """Request to update an existing product."""

    product_id: UUID
    code: Optional[str] = None
    description: Optional[str] = None
    sell_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    department_id: Optional[UUID] = None
    user_id: Optional[UUID] = None


@dataclass
class ProductResponse:
    """Response containing product data."""

    id: UUID
    code: str
    description: str
    sell_price: Decimal
    cost_price: Optional[Decimal]
    quantity_in_stock: Decimal
    department_id: Optional[UUID]
    created_at: Optional[datetime] = None

    @classmethod
    def from_domain(cls, product):
        """Create from domain Product model."""
        return cls(
            id=product.id,
            code=product.code,
            description=product.description,
            sell_price=product.sell_price,
            cost_price=product.cost_price,
            quantity_in_stock=product.quantity_in_stock,
            department_id=product.department_id,
        )


# Sale Use Case DTOs


@dataclass
class SaleItemRequest:
    """Request to add an item to a sale."""

    product_code: str
    quantity: Decimal
    unit_price: Optional[Decimal] = None  # None = use product's current price


@dataclass
class ProcessSaleRequest:
    """Request to process a complete sale transaction."""

    items: List[SaleItemRequest]
    customer_id: Optional[UUID] = None
    payment_type: str = "cash"  # cash, credit, card
    paid_amount: Decimal = Decimal("0")
    notes: Optional[str] = None
    user_id: Optional[UUID] = None


@dataclass
class SaleResponse:
    """Response containing sale data."""

    sale_id: UUID
    total_amount: Decimal
    payment_type: str
    paid_amount: Decimal
    change_amount: Decimal
    customer_id: Optional[UUID]
    created_at: datetime
    receipt_number: Optional[str] = None

    @classmethod
    def from_domain(cls, sale):
        """Create from domain Sale model."""
        return cls(
            sale_id=sale.id,
            total_amount=sale.total,
            payment_type=sale.payment_type,
            paid_amount=sale.paid_amount,
            change_amount=sale.change_amount,
            customer_id=sale.customer_id,
            created_at=sale.created_at,
            receipt_number=getattr(sale, "receipt_number", None),
        )


# Inventory Use Case DTOs


@dataclass
class AdjustInventoryRequest:
    """Request to adjust product inventory."""

    product_id: UUID
    adjustment_quantity: Decimal  # Positive = increase, negative = decrease
    reason: str
    user_id: Optional[UUID] = None


@dataclass
class InventoryResponse:
    """Response containing inventory data."""

    product_id: UUID
    product_code: str
    old_quantity: Decimal
    new_quantity: Decimal
    adjustment_quantity: Decimal


# Customer Use Case DTOs


@dataclass
class CreateCustomerRequest:
    """Request to create a new customer."""

    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    credit_limit: Decimal = Decimal("0")
    user_id: Optional[UUID] = None

    def to_domain(self):
        """Convert to domain Customer model."""
        from core.models.customer import Customer

        return Customer(
            name=self.name,
            email=self.email,
            phone=self.phone,
            address=self.address,
            credit_limit=self.credit_limit,
        )


@dataclass
class CustomerResponse:
    """Response containing customer data."""

    id: UUID
    name: str
    email: Optional[str]
    phone: Optional[str]
    balance: Decimal
    credit_limit: Decimal

    @classmethod
    def from_domain(cls, customer):
        """Create from domain Customer model."""
        return cls(
            id=customer.id,
            name=customer.name,
            email=customer.email,
            phone=customer.phone,
            balance=customer.balance,
            credit_limit=customer.credit_limit,
        )


# Query DTOs (for read operations)


@dataclass
class GetProductByCodeRequest:
    """Request to get a product by code."""

    code: str


@dataclass
class SearchProductsRequest:
    """Request to search products."""

    search_term: Optional[str] = None
    department_id: Optional[UUID] = None
    in_stock_only: bool = False


@dataclass
class GetLowStockProductsRequest:
    """Request to get products with low stock."""

    department_id: Optional[UUID] = None


@dataclass
class ProductListResponse:
    """Response containing list of products."""

    products: List[ProductResponse]
    total_count: int


# Bulk Operation DTOs


@dataclass
class BulkPriceUpdateRequest:
    """Request to update prices for multiple products."""

    percentage: Decimal
    department_id: Optional[UUID] = None
    user_id: Optional[UUID] = None


@dataclass
class BulkPriceUpdateResponse:
    """Response for bulk price update."""

    updated_count: int
    failed_products: List[str]  # List of product codes that failed
