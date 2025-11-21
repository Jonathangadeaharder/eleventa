using System.ComponentModel.DataAnnotations;

namespace Eleventa.Application.DTOs;

/// <summary>
/// Data transfer object for updating an existing product.
/// </summary>
public class UpdateProductDto
{
    /// <summary>
    /// Product ID (required for updates).
    /// </summary>
    [Required]
    [Range(1, int.MaxValue, ErrorMessage = "Product ID must be greater than 0")]
    public int Id { get; set; }

    /// <summary>
    /// Product code.
    /// </summary>
    [StringLength(50, ErrorMessage = "Product code cannot exceed 50 characters")]
    public string? Code { get; set; }

    /// <summary>
    /// Product description.
    /// </summary>
    [StringLength(200, ErrorMessage = "Product description cannot exceed 200 characters")]
    public string? Description { get; set; }

    /// <summary>
    /// Cost price.
    /// </summary>
    [Range(0, double.MaxValue, ErrorMessage = "Cost price must be a positive value")]
    public decimal? CostPrice { get; set; }

    /// <summary>
    /// Selling price.
    /// </summary>
    [Range(0, double.MaxValue, ErrorMessage = "Sell price must be a positive value")]
    public decimal? SellPrice { get; set; }

    /// <summary>
    /// Wholesale price (Price 2).
    /// </summary>
    [Range(0, double.MaxValue, ErrorMessage = "Wholesale price must be a positive value")]
    public decimal? WholesalePrice { get; set; }

    /// <summary>
    /// Special price (Price 3).
    /// </summary>
    [Range(0, double.MaxValue, ErrorMessage = "Special price must be a positive value")]
    public decimal? SpecialPrice { get; set; }

    /// <summary>
    /// Department ID.
    /// </summary>
    public int? DepartmentId { get; set; }

    /// <summary>
    /// Unit of measurement.
    /// </summary>
    [StringLength(50, ErrorMessage = "Unit cannot exceed 50 characters")]
    public string? Unit { get; set; }

    /// <summary>
    /// Product barcode.
    /// </summary>
    [StringLength(50, ErrorMessage = "Barcode cannot exceed 50 characters")]
    public string? Barcode { get; set; }

    /// <summary>
    /// Product brand.
    /// </summary>
    [StringLength(100, ErrorMessage = "Brand cannot exceed 100 characters")]
    public string? Brand { get; set; }

    /// <summary>
    /// Product model.
    /// </summary>
    [StringLength(100, ErrorMessage = "Model cannot exceed 100 characters")]
    public string? Model { get; set; }

    /// <summary>
    /// Additional notes.
    /// </summary>
    [StringLength(500, ErrorMessage = "Notes cannot exceed 500 characters")]
    public string? Notes { get; set; }

    /// <summary>
    /// Minimum stock level.
    /// </summary>
    [Range(0, double.MaxValue, ErrorMessage = "Minimum stock must be a positive value")]
    public decimal? MinStock { get; set; }

    /// <summary>
    /// Maximum stock level.
    /// </summary>
    [Range(0, double.MaxValue, ErrorMessage = "Maximum stock must be a positive value")]
    public decimal? MaxStock { get; set; }

    /// <summary>
    /// Whether the product uses inventory tracking.
    /// </summary>
    public bool? UsesInventory { get; set; }

    /// <summary>
    /// Whether the product is a service.
    /// </summary>
    public bool? IsService { get; set; }

    /// <summary>
    /// Whether the product is active.
    /// </summary>
    public bool? IsActive { get; set; }
}
