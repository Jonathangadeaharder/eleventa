from dataclasses import dataclass, field
from typing import Optional, List
import datetime

@dataclass
class Department:
    id: Optional[int] = None
    name: str = ""

@dataclass
class Product:
    id: Optional[int] = None
    code: str = ""
    description: str = ""
    cost_price: float = 0.0
    sell_price: float = 0.0
    wholesale_price: Optional[float] = None # Price 2
    special_price: Optional[float] = None # Price 3
    department_id: Optional[int] = None
    department: Optional[Department] = None # Can hold the loaded Department object
    unit: str = "Unidad" # Default unit
    uses_inventory: bool = True
    quantity_in_stock: float = 0.0
    min_stock: Optional[float] = 0.0
    max_stock: Optional[float] = None
    last_updated: Optional[datetime.datetime] = None
    notes: Optional[str] = None
    is_active: bool = True
    # Consider adding fields like:
    # tax_rate: float = 0.0
    # image_path: Optional[str] = None
    # created_at: Optional[datetime.datetime] = None 