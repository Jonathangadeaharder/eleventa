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

class StandardUnitType(str, Enum):
    """Standard unit types for products."""
    UNIDAD = "Unidad"
    KILOGRAMO = "Kilogramo"
    GRAMO = "Gramo"
    LITRO = "Litro"
    MILILITRO = "Mililitro"
    METRO = "Metro"
    CENTIMETRO = "Centímetro"
    CAJA = "Caja"
    PAQUETE = "Paquete"
    DOCENA = "Docena"
    PAR = "Par"
    ROLLO = "Rollo"
    BOTELLA = "Botella"
    LATA = "Lata"
    BOLSA = "Bolsa"
