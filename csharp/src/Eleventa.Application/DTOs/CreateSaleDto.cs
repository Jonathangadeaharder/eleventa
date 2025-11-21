using System.ComponentModel.DataAnnotations;
using Eleventa.Domain.Entities;

namespace Eleventa.Application.DTOs;

/// <summary>
/// Data transfer object for creating a new sale.
/// </summary>
public class CreateSaleDto
{
    /// <summary>
    /// Customer ID (optional).
    /// </summary>
    public int? CustomerId { get; set; }

    /// <summary>
    /// User ID who is making the sale.
    /// </summary>
    public int? UserId { get; set; }

    /// <summary>
    /// Whether this is a credit sale.
    /// </summary>
    public bool IsCreditSale { get; set; }

    /// <summary>
    /// Payment type.
    /// </summary>
    [Required]
    public PaymentType PaymentType { get; set; }

    /// <summary>
    /// Sale items.
    /// </summary>
    [Required]
    [MinLength(1, ErrorMessage = "A sale must have at least one item")]
    public List<CreateSaleItemDto> Items { get; set; } = new();
}

/// <summary>
/// Data transfer object for creating a sale item.
/// </summary>
public class CreateSaleItemDto
{
    /// <summary>
    /// Product ID.
    /// </summary>
    [Required]
    [Range(1, int.MaxValue, ErrorMessage = "Product ID must be greater than 0")]
    public int ProductId { get; set; }

    /// <summary>
    /// Quantity to sell.
    /// </summary>
    [Required]
    [Range(0.01, double.MaxValue, ErrorMessage = "Quantity must be greater than 0")]
    public decimal Quantity { get; set; }

    /// <summary>
    /// Unit price (if not specified, will use product's default price).
    /// </summary>
    public decimal? UnitPrice { get; set; }
}
