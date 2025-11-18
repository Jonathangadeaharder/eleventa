from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class Invoice:
    """Invoice model representing an invoice in the system."""

    sale_id: int
    id: Optional[int] = None
    customer_id: Optional[int] = None
    invoice_number: Optional[str] = None
    invoice_date: datetime = field(default_factory=datetime.utcnow)
    invoice_type: str = "B"  # A, B, or C
    customer_details: Dict = field(default_factory=dict)
    subtotal: Decimal = Decimal("0.00")
    iva_amount: Decimal = Decimal("0.00")
    total: Decimal = Decimal("0.00")
    iva_condition: str = "Consumidor Final"
    cae: Optional[str] = None
    cae_due_date: Optional[datetime] = None
    notes: Optional[str] = None
    is_active: bool = True
