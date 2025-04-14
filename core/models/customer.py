from dataclasses import dataclass, field
from typing import Optional
import uuid

@dataclass
class Customer:
    # Non-default fields first
    name: str

    # Default fields follow
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    cuit: Optional[str] = None  # Added CUIT as mentioned later for invoicing
    iva_condition: Optional[str] = None # Added IVA condition for invoicing
    credit_limit: float = 0.0
    credit_balance: float = 0.0 # Positive means customer owes money
    is_active: bool = True 