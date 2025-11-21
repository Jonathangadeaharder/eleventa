using System.ComponentModel.DataAnnotations;

namespace Eleventa.Application.DTOs;

/// <summary>
/// Data transfer object for Product entity.
/// </summary>
public class ProductDto
{
    /// <summary>
    /// Product unique identifier.
    /// </summary>
    public int Id { get; set; }

    /// <summary>
    /// Product code.
    /// </summary>
    [Required]
    [StringLength(50)]
    public string Code { get; set; } = string.Empty;

    /// <summary>
    /// Product description.
    /// </summary>
    [Required]
    [StringLength(200)]
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// Cost price.
    /// </summary>
    [Range(0, double.MaxValue)]
    public decimal CostPrice { get; set; }

    /// <summary>
    /// Selling price.
    /// </summary>
    [Range(0, double.MaxValue)]
    public decimal SellPrice { get; set; }

    /// <summary>
    /// Wholesale price (Price 2).
    /// </summary>
    public decimal? WholesalePrice { get; set; }

    /// <summary>
    /// Special price (Price 3).
    /// </summary>
    public decimal? SpecialPrice { get; set; }

    /// <summary>
    /// Department ID.
    /// </summary>
    public int? DepartmentId { get; set; }

    /// <summary>
    /// Unit of measurement.
    /// </summary>
    [StringLength(50)]
    public string Unit { get; set; } = "Unidad";

    /// <summary>
    /// Product barcode.
    /// </summary>
    [StringLength(50)]
    public string? Barcode { get; set; }

    /// <summary>
    /// Product brand.
    /// </summary>
    [StringLength(100)]
    public string? Brand { get; set; }

    /// <summary>
    /// Product model.
    /// </summary>
    [StringLength(100)]
    public string? Model { get; set; }

    /// <summary>
    /// Additional notes.
    /// </summary>
    [StringLength(500)]
    public string? Notes { get; set; }

    /// <summary>
    /// Creation timestamp.
    /// </summary>
    public DateTime? CreatedAt { get; set; }

    /// <summary>
    /// Last update timestamp.
    /// </summary>
    public DateTime? UpdatedAt { get; set; }

    /// <summary>
    /// Active status.
    /// </summary>
    public bool IsActive { get; set; } = true;

    /// <summary>
    /// Current quantity in stock.
    /// </summary>
    [Range(0, double.MaxValue)]
    public decimal QuantityInStock { get; set; }

    /// <summary>
    /// Minimum stock level.
    /// </summary>
    [Range(0, double.MaxValue)]
    public decimal MinStock { get; set; }

    /// <summary>
    /// Maximum stock level.
    /// </summary>
    public decimal? MaxStock { get; set; }

    /// <summary>
    /// Whether the product uses inventory tracking.
    /// </summary>
    public bool UsesInventory { get; set; } = true;

    /// <summary>
    /// Whether the product is a service.
    /// </summary>
    public bool IsService { get; set; } = false;

    /// <summary>
    /// Whether the product needs restock.
    /// </summary>
    public bool NeedsRestock { get; set; }

    /// <summary>
    /// Whether the product is in stock.
    /// </summary>
    public bool IsInStock { get; set; }
}
