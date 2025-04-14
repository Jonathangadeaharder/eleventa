from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Supplier:
    """Represents a supplier of products."""
    id: Optional[int] = None
    name: str = ""
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    cuit: Optional[str] = None # Clave Única de Identificación Tributaria (Argentina)
    notes: Optional[str] = None
