from enum import Enum

class PaymentType(Enum):
    EFECTIVO = "Efectivo"
    TARJETA = "Tarjeta"
    CREDITO = "Crédito"
    SIN_ESPECIFICAR = "Sin especificar"

class InventoryMovementType(str, Enum):
    """Types of inventory movements."""
    PURCHASE = "PURCHASE"
    SALE = "SALE"
    ADJUSTMENT = "ADJUSTMENT"
    INITIAL = "INITIAL"

class CashDrawerEntryType(str, Enum):
    """Types of cash drawer entries."""
    IN = "IN"
    OUT = "OUT"
    CLOSE = "CLOSE"
