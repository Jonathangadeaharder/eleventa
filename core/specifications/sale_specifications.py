"""
Sale Specifications

Concrete specifications for sale queries.
"""

from decimal import Decimal
from datetime import datetime
from uuid import UUID

from core.specifications.base import Specification, ParameterizedSpecification
from core.models.sale import Sale


class SaleByDateRangeSpecification(ParameterizedSpecification[Sale]):
    """
    Specification for sales within a date range.

    Usage:
        spec = SaleByDateRangeSpecification(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31)
        )
        january_sales = repository.find_by_specification(spec)
    """

    def __init__(self, start_date: datetime, end_date: datetime):
        """
        Initialize specification.

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
        """
        self.start_date = start_date
        self.end_date = end_date

    def is_satisfied_by(self, sale: Sale) -> bool:
        """Check if sale is within date range."""
        return self.start_date <= sale.created_at <= self.end_date

    def to_sqlalchemy_filter(self):
        """Convert to SQLAlchemy filter."""
        from infrastructure.persistence.sqlite.models_mapping import Sale as SaleOrm
        from sqlalchemy import and_

        return and_(
            SaleOrm.created_at >= self.start_date, SaleOrm.created_at <= self.end_date
        )

    def __repr__(self) -> str:
        return f"SaleByDateRange({self.start_date}, {self.end_date})"


class SaleByCustomerSpecification(ParameterizedSpecification[Sale]):
    """
    Specification for sales by a specific customer.

    Usage:
        spec = SaleByCustomerSpecification(customer_id)
        customer_sales = repository.find_by_specification(spec)
    """

    def __init__(self, customer_id: UUID):
        """
        Initialize specification.

        Args:
            customer_id: The customer ID to filter by
        """
        self.customer_id = customer_id

    def is_satisfied_by(self, sale: Sale) -> bool:
        """Check if sale is by the specified customer."""
        return sale.customer_id == self.customer_id

    def to_sqlalchemy_filter(self):
        """Convert to SQLAlchemy filter."""
        from infrastructure.persistence.sqlite.models_mapping import Sale as SaleOrm

        return SaleOrm.customer_id == self.customer_id

    def __repr__(self) -> str:
        return f"SaleByCustomer({self.customer_id})"


class SaleByPaymentTypeSpecification(ParameterizedSpecification[Sale]):
    """
    Specification for sales by payment type.

    Usage:
        spec = SaleByPaymentTypeSpecification("cash")
        cash_sales = repository.find_by_specification(spec)
    """

    def __init__(self, payment_type: str):
        """
        Initialize specification.

        Args:
            payment_type: Payment type (cash, credit, card, etc.)
        """
        self.payment_type = payment_type

    def is_satisfied_by(self, sale: Sale) -> bool:
        """Check if sale uses the specified payment type."""
        return sale.payment_type == self.payment_type

    def to_sqlalchemy_filter(self):
        """Convert to SQLAlchemy filter."""
        from infrastructure.persistence.sqlite.models_mapping import Sale as SaleOrm

        return SaleOrm.payment_type == self.payment_type

    def __repr__(self) -> str:
        return f"SaleByPaymentType('{self.payment_type}')"


class SaleAboveAmountSpecification(ParameterizedSpecification[Sale]):
    """
    Specification for sales above a certain amount.

    Usage:
        spec = SaleAboveAmountSpecification(Decimal('1000'))
        large_sales = repository.find_by_specification(spec)
    """

    def __init__(self, amount: Decimal):
        """
        Initialize specification.

        Args:
            amount: Minimum sale amount (exclusive)
        """
        self.amount = amount

    def is_satisfied_by(self, sale: Sale) -> bool:
        """Check if sale total is above amount."""
        return sale.total > self.amount

    def to_sqlalchemy_filter(self):
        """Convert to SQLAlchemy filter."""
        from infrastructure.persistence.sqlite.models_mapping import Sale as SaleOrm

        return SaleOrm.total > self.amount

    def __repr__(self) -> str:
        return f"SaleAboveAmount({self.amount})"


class SaleBelowAmountSpecification(ParameterizedSpecification[Sale]):
    """
    Specification for sales below a certain amount.

    Usage:
        spec = SaleBelowAmountSpecification(Decimal('50'))
        small_sales = repository.find_by_specification(spec)
    """

    def __init__(self, amount: Decimal):
        """
        Initialize specification.

        Args:
            amount: Maximum sale amount (exclusive)
        """
        self.amount = amount

    def is_satisfied_by(self, sale: Sale) -> bool:
        """Check if sale total is below amount."""
        return sale.total < self.amount

    def to_sqlalchemy_filter(self):
        """Convert to SQLAlchemy filter."""
        from infrastructure.persistence.sqlite.models_mapping import Sale as SaleOrm

        return SaleOrm.total < self.amount

    def __repr__(self) -> str:
        return f"SaleBelowAmount({self.amount})"


class SaleCreditSaleSpecification(Specification[Sale]):
    """
    Specification for credit sales.

    Satisfied when payment_type = 'credit'.

    Usage:
        spec = SaleCreditSaleSpecification()
        credit_sales = repository.find_by_specification(spec)
    """

    def is_satisfied_by(self, sale: Sale) -> bool:
        """Check if sale is a credit sale."""
        return sale.payment_type == "credit"

    def to_sqlalchemy_filter(self):
        """Convert to SQLAlchemy filter."""
        from infrastructure.persistence.sqlite.models_mapping import Sale as SaleOrm

        return SaleOrm.payment_type == "credit"

    def __repr__(self) -> str:
        return "SaleCreditSale"


class SaleByUserSpecification(ParameterizedSpecification[Sale]):
    """
    Specification for sales by a specific user.

    Usage:
        spec = SaleByUserSpecification(user_id)
        user_sales = repository.find_by_specification(spec)
    """

    def __init__(self, user_id: UUID):
        """
        Initialize specification.

        Args:
            user_id: The user ID to filter by
        """
        self.user_id = user_id

    def is_satisfied_by(self, sale: Sale) -> bool:
        """Check if sale was created by the specified user."""
        return sale.user_id == self.user_id

    def to_sqlalchemy_filter(self):
        """Convert to SQLAlchemy filter."""
        from infrastructure.persistence.sqlite.models_mapping import Sale as SaleOrm

        return SaleOrm.user_id == self.user_id

    def __repr__(self) -> str:
        return f"SaleByUser({self.user_id})"


# Convenience factory functions


def sales_by_date_range(
    start_date: datetime, end_date: datetime
) -> SaleByDateRangeSpecification:
    """Create specification for sales in date range."""
    return SaleByDateRangeSpecification(start_date, end_date)


def sales_by_customer(customer_id: UUID) -> SaleByCustomerSpecification:
    """Create specification for sales by customer."""
    return SaleByCustomerSpecification(customer_id)


def sales_by_payment_type(payment_type: str) -> SaleByPaymentTypeSpecification:
    """Create specification for sales by payment type."""
    return SaleByPaymentTypeSpecification(payment_type)


def sales_above_amount(amount: Decimal) -> SaleAboveAmountSpecification:
    """Create specification for sales above amount."""
    return SaleAboveAmountSpecification(amount)


def sales_below_amount(amount: Decimal) -> SaleBelowAmountSpecification:
    """Create specification for sales below amount."""
    return SaleBelowAmountSpecification(amount)


def credit_sales() -> SaleCreditSaleSpecification:
    """Create specification for credit sales."""
    return SaleCreditSaleSpecification()


def cash_sales() -> SaleByPaymentTypeSpecification:
    """Create specification for cash sales."""
    return SaleByPaymentTypeSpecification("cash")


def card_sales() -> SaleByPaymentTypeSpecification:
    """Create specification for card sales."""
    return SaleByPaymentTypeSpecification("card")
