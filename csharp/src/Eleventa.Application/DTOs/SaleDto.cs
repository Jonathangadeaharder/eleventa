using System.ComponentModel.DataAnnotations;
using Eleventa.Domain.Entities;

namespace Eleventa.Application.DTOs;

/// <summary>
/// Data transfer object for Sale entity.
/// </summary>
public class SaleDto
{
    /// <summary>
    /// Sale unique identifier.
    /// </summary>
    public int Id { get; set; }

    /// <summary>
    /// Sale timestamp.
    /// </summary>
    [Required]
    public DateTime Timestamp { get; set; }

    /// <summary>
    /// Customer ID.
    /// </summary>
    public int? CustomerId { get; set; }

    /// <summary>
    /// User ID who made the sale.
    /// </summary>
    public int? UserId { get; set; }

    /// <summary>
    /// Whether this is a credit sale.
    /// </summary>
    public bool IsCreditSale { get; set; }

    /// <summary>
    /// Payment type.
    /// </summary>
    public PaymentType? PaymentType { get; set; }

    /// <summary>
    /// Sale status.
    /// </summary>
    [StringLength(50)]
    public string? Status { get; set; }

    /// <summary>
    /// Sale items.
    /// </summary>
    [Required]
    [MinLength(1, ErrorMessage = "A sale must have at least one item")]
    public List<SaleItemDto> Items { get; set; } = new();

    /// <summary>
    /// Total amount of the sale.
    /// </summary>
    [Range(0, double.MaxValue)]
    public decimal Total { get; set; }

    /// <summary>
    /// Total number of items in the sale.
    /// </summary>
    public int ItemCount { get; set; }

    /// <summary>
    /// Customer name (for display).
    /// </summary>
    public string? CustomerName { get; set; }

    /// <summary>
    /// User name (for display).
    /// </summary>
    public string? UserName { get; set; }
}

/// <summary>
/// Data transfer object for SaleItem entity.
/// </summary>
public class SaleItemDto
{
    /// <summary>
    /// Sale item unique identifier.
    /// </summary>
    public int Id { get; set; }

    /// <summary>
    /// Sale ID.
    /// </summary>
    public int? SaleId { get; set; }

    /// <summary>
    /// Product ID.
    /// </summary>
    [Required]
    public int ProductId { get; set; }

    /// <summary>
    /// Product code (denormalized).
    /// </summary>
    [Required]
    [StringLength(50)]
    public string ProductCode { get; set; } = string.Empty;

    /// <summary>
    /// Product description (denormalized).
    /// </summary>
    [Required]
    [StringLength(200)]
    public string ProductDescription { get; set; } = string.Empty;

    /// <summary>
    /// Product unit (denormalized).
    /// </summary>
    [StringLength(50)]
    public string ProductUnit { get; set; } = "Unidad";

    /// <summary>
    /// Quantity.
    /// </summary>
    [Required]
    [Range(0.01, double.MaxValue, ErrorMessage = "Quantity must be greater than 0")]
    public decimal Quantity { get; set; }

    /// <summary>
    /// Unit price.
    /// </summary>
    [Required]
    [Range(0, double.MaxValue)]
    public decimal UnitPrice { get; set; }

    /// <summary>
    /// Subtotal (quantity * unit price).
    /// </summary>
    public decimal Subtotal { get; set; }
}
