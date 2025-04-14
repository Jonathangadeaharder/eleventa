from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any

@dataclass
class Invoice:
    """
    Represents an invoice generated from a sale, following Argentina's invoice requirements.
    """
    # Required fields (without defaults)
    sale_id: int
    
    # Fields with defaults
    id: Optional[int] = None
    customer_id: Optional[int] = None
    invoice_number: Optional[str] = None  # Format may follow Argentina's requirements
    invoice_date: datetime = field(default_factory=datetime.now)
    invoice_type: str = "B"  # Default to "B" (could be "A", "B", "C", etc. per Argentina's types)
    
    # Customer details stored as snapshot at invoice time
    customer_details: Dict[str, Any] = field(default_factory=dict)  # name, cuit, address, etc.
    
    # Financial data
    subtotal: Decimal = Decimal("0.00")
    iva_amount: Decimal = Decimal("0.00")
    total: Decimal = Decimal("0.00")
    
    # IVA/VAT condition (Argentina-specific)
    iva_condition: str = "Consumidor Final"  # Default
    
    # Electronic invoice data (CAE/AFIP)
    cae: Optional[str] = None  # CAE number issued by AFIP
    cae_due_date: Optional[datetime] = None  # CAE expiration date
    
    # Other fields
    notes: Optional[str] = None
    is_active: bool = True