using System.ComponentModel.DataAnnotations;

namespace Eleventa.Application.DTOs;

/// <summary>
/// Data transfer object for Customer entity.
/// </summary>
public class CustomerDto
{
    /// <summary>
    /// Customer unique identifier.
    /// </summary>
    public int Id { get; set; }

    /// <summary>
    /// Customer name.
    /// </summary>
    [Required]
    [StringLength(200)]
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// Customer phone number.
    /// </summary>
    [Phone]
    [StringLength(50)]
    public string? Phone { get; set; }

    /// <summary>
    /// Customer email address.
    /// </summary>
    [EmailAddress]
    [StringLength(100)]
    public string? Email { get; set; }

    /// <summary>
    /// Customer address.
    /// </summary>
    [StringLength(500)]
    public string? Address { get; set; }

    /// <summary>
    /// Tax ID (CUIT) for invoicing.
    /// </summary>
    [StringLength(20)]
    public string? CUIT { get; set; }

    /// <summary>
    /// IVA/Tax condition for invoicing.
    /// </summary>
    [StringLength(50)]
    public string? IVACondition { get; set; }

    /// <summary>
    /// Credit limit.
    /// </summary>
    [Range(0, double.MaxValue)]
    public decimal CreditLimit { get; set; }

    /// <summary>
    /// Current credit balance (positive means customer owes money).
    /// </summary>
    public decimal CreditBalance { get; set; }

    /// <summary>
    /// Available credit remaining.
    /// </summary>
    public decimal AvailableCredit { get; set; }

    /// <summary>
    /// Whether the customer is active.
    /// </summary>
    public bool IsActive { get; set; } = true;

    /// <summary>
    /// Creation timestamp.
    /// </summary>
    public DateTime? CreatedAt { get; set; }

    /// <summary>
    /// Last update timestamp.
    /// </summary>
    public DateTime? UpdatedAt { get; set; }
}
