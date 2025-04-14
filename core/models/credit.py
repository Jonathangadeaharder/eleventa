from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional

@dataclass
class CreditPayment:
    """Represents a payment made towards a customer's credit account."""
    # Non-default fields first
    customer_id: int
    amount: Decimal # Amount paid

    # Default fields next
    id: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)
    notes: Optional[str] = None
    user_id: Optional[int] = None # Track which user processed the payment (added later)

    def __post_init__(self):
        if self.amount <= Decimal(0):
            raise ValueError("Payment amount must be positive.")
        # Ensure amount is Decimal
        if not isinstance(self.amount, Decimal):
             self.amount = Decimal(str(self.amount))
        self.amount = self.amount.quantize(Decimal("0.01")) 