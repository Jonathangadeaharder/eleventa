namespace Eleventa.Domain.Entities;

/// <summary>
/// Represents a product in the POS system.
/// </summary>
public class Product
{
    public int Id { get; set; }
    public string Code { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;

    // Pricing
    public decimal CostPrice { get; set; }
    public decimal SellPrice { get; set; }
    public decimal? WholesalePrice { get; set; }  // Price 2
    public decimal? SpecialPrice { get; set; }     // Price 3

    // Department relationship
    public int? DepartmentId { get; set; }
    public Department? Department { get; set; }

    // Product details
    public string Unit { get; set; } = "Unidad";
    public string? Barcode { get; set; }
    public string? Brand { get; set; }
    public string? Model { get; set; }
    public string? Notes { get; set; }

    // Timestamps
    public DateTime? CreatedAt { get; set; }
    public DateTime? UpdatedAt { get; set; }
    public DateTime? LastUpdated { get; set; }

    // Status
    public bool IsActive { get; set; } = true;

    // Inventory
    public decimal QuantityInStock { get; set; }
    public decimal MinStock { get; set; }
    public decimal? MaxStock { get; set; }
    public bool UsesInventory { get; set; } = true;
    public bool IsService { get; set; } = false;

    // Navigation properties
    public ICollection<SaleItem> SaleItems { get; set; } = new List<SaleItem>();
    public ICollection<InventoryMovement> InventoryMovements { get; set; } = new List<InventoryMovement>();

    /// <summary>
    /// Checks if product needs restock based on minimum stock level.
    /// </summary>
    public bool NeedsRestock()
    {
        return UsesInventory && QuantityInStock <= MinStock;
    }

    /// <summary>
    /// Checks if product is in stock.
    /// </summary>
    public bool IsInStock()
    {
        return !UsesInventory || QuantityInStock > 0;
    }

    /// <summary>
    /// Gets the effective selling price based on price type.
    /// </summary>
    public decimal GetPrice(PriceType priceType = PriceType.Regular)
    {
        return priceType switch
        {
            PriceType.Regular => SellPrice,
            PriceType.Wholesale => WholesalePrice ?? SellPrice,
            PriceType.Special => SpecialPrice ?? SellPrice,
            _ => SellPrice
        };
    }
}

public enum PriceType
{
    Regular,
    Wholesale,
    Special
}
