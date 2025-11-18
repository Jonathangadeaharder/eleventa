from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
import datetime
from decimal import Decimal

# Assuming Department will also be a Pydantic model or dataclass
from .department import Department


class Product(BaseModel):
    id: Optional[int] = None
    code: str = Field(
        default="", max_length=50
    )  # Empty string default to match test expectations
    description: str = Field(
        default="", max_length=255
    )  # Empty string default to match test expectations
    cost_price: Decimal = Field(
        default=Decimal("0.0"), max_digits=15, decimal_places=2
    )  # Increased max_digits for tests
    sell_price: Optional[Decimal] = Field(
        default=Decimal("0.0"), max_digits=15, decimal_places=2
    )  # Increased max_digits for tests
    wholesale_price: Optional[Decimal] = Field(
        default=None, max_digits=15, decimal_places=2
    )  # Price 2
    special_price: Optional[Decimal] = Field(
        default=None, max_digits=15, decimal_places=2
    )  # Price 3
    department_id: Optional[int] = None
    department: Optional[Department] = None  # Domain model for Department
    unit: str = Field(
        default="Unidad", max_length=50
    )  # Added to match test expectations
    barcode: Optional[str] = Field(default=None, max_length=50)
    brand: Optional[str] = Field(default=None, max_length=50)
    model: Optional[str] = Field(default=None, max_length=50)
    notes: Optional[str] = Field(default=None, max_length=500)
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    last_updated: Optional[datetime.datetime] = None  # Added to match test expectations
    is_active: bool = True
    quantity_in_stock: Decimal = Field(
        default=Decimal("0.0"), max_digits=15, decimal_places=3
    )  # Increased max_digits for tests
    min_stock: Optional[Decimal] = Field(
        default=Decimal("0.0"), max_digits=15, decimal_places=3
    )  # Made optional to allow None values
    max_stock: Optional[Decimal] = Field(
        default=None, max_digits=15, decimal_places=3
    )  # Renamed from max_stock_level
    uses_inventory: bool = True  # Whether the product is tracked in inventory
    is_service: bool = False  # Service products don't have inventory

    @field_validator(
        "cost_price",
        "sell_price",
        "wholesale_price",
        "special_price",
        "quantity_in_stock",
        "min_stock",
        "max_stock",
        mode="before",
    )
    @classmethod
    def convert_to_decimal(cls, v):
        if v is None:
            return None
        if isinstance(v, float) or isinstance(v, int):
            return Decimal(str(v))
        return v

    def __eq__(self, other):
        if isinstance(other, Product):
            return super().__eq__(other)
        return NotImplemented

    # Keep Decimal types for proper arithmetic operations
    def __getattribute__(self, name: str) -> Any:
        attr = super().__getattribute__(name)
        return attr

    model_config = ConfigDict(from_attributes=True)
