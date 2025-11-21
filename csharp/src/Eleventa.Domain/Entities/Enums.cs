namespace Eleventa.Domain.Entities;

/// <summary>
/// Types of payment methods.
/// </summary>
public enum PaymentType
{
    Efectivo,        // Cash
    Tarjeta,         // Card
    Credito,         // Credit
    SinEspecificar   // Unspecified
}

/// <summary>
/// Types of inventory movements.
/// </summary>
public enum InventoryMovementType
{
    Purchase,
    Sale,
    Adjustment,
    Initial
}

/// <summary>
/// Types of cash drawer entries.
/// </summary>
public enum CashDrawerEntryType
{
    In,
    Out,
    Close
}

/// <summary>
/// Standard unit types for products.
/// </summary>
public enum StandardUnitType
{
    Unidad,
    Kilogramo,
    Gramo,
    Litro,
    Mililitro,
    Metro,
    Centimetro,
    Caja,
    Paquete,
    Docena,
    Par,
    Rollo,
    Botella,
    Lata,
    Bolsa
}
