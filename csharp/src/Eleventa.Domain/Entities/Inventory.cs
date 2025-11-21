namespace Eleventa.Domain.Entities;

/// <summary>
/// Represents an inventory movement record.
/// </summary>
public class InventoryMovement
{
    public int Id { get; set; }
    public int ProductId { get; set; }
    public InventoryMovementType MovementType { get; set; }
    public decimal Quantity { get; set; }
    public decimal? UnitCost { get; set; }
    public string? Reason { get; set; }
    public string? Reference { get; set; }  // Reference to sale, purchase order, etc.
    public int? UserId { get; set; }
    public DateTime Timestamp { get; set; } = DateTime.Now;
    public decimal? PreviousStock { get; set; }
    public decimal? NewStock { get; set; }

    // Navigation properties
    public Product? Product { get; set; }
    public User? User { get; set; }
}
