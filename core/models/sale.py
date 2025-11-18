from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from core.models.enums import PaymentType

# Assuming Product model is defined elsewhere or not needed directly for definition
# from core.models.product import Product


@dataclass
class SaleItem:
    # Fields without defaults first
    product_id: int
    quantity: Decimal  # This will be converted to Decimal if float
    unit_price: Decimal  # This will be converted to Decimal if float

    # Fields with defaults next
    id: Optional[int] = None
    sale_id: Optional[int] = None
    product_code: str = ""  # Denormalized for easy display
    product_description: str = ""  # Denormalized for easy display
    product_unit: str = "Unidad"  # Unit of measure for the product

    def __post_init__(self):
        # Ensure quantity and unit_price are always Decimal objects
        if not isinstance(self.quantity, Decimal):
            self.quantity = Decimal(str(self.quantity))
        if not isinstance(self.unit_price, Decimal):
            self.unit_price = Decimal(str(self.unit_price))

    @property
    def subtotal(self) -> Decimal:
        return (self.quantity * self.unit_price).quantize(Decimal("0.01"))

    # You might add product details here if needed, fetched separately or passed during creation


@dataclass
class Sale:
    id: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)
    items: List[SaleItem] = field(default_factory=list)
    customer_id: Optional[int] = None  # Added customer ID
    is_credit_sale: bool = False  # Added credit flag
    user_id: Optional[int] = None  # User who made the sale
    payment_type: Optional["PaymentType"] = (
        None  # e.g., 'Efectivo', 'Tarjeta', 'Crédito'
    )
    # status: str = "COMPLETED" # Example status

    @property
    def total(self) -> Decimal:
        if not self.items:
            return Decimal("0.00")
        return sum(item.subtotal for item in self.items).quantize(Decimal("0.01"))
