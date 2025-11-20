namespace Eleventa.Domain.Entities;

/// <summary>
/// Represents a customer in the POS system.
/// </summary>
public class Customer
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string? Phone { get; set; }
    public string? Email { get; set; }
    public string? Address { get; set; }
    public string? CUIT { get; set; }  // Tax ID for invoicing
    public string? IVACondition { get; set; }  // Tax condition for invoicing
    public decimal CreditLimit { get; set; }
    public decimal CreditBalance { get; set; }  // Positive means customer owes money
    public bool IsActive { get; set; } = true;
    public DateTime? CreatedAt { get; set; }
    public DateTime? UpdatedAt { get; set; }

    // Navigation properties
    public ICollection<Sale> Sales { get; set; } = new List<Sale>();

    /// <summary>
    /// Checks if customer has available credit.
    /// </summary>
    public bool HasAvailableCredit(decimal amount)
    {
        return CreditBalance + amount <= CreditLimit;
    }

    /// <summary>
    /// Gets the remaining credit available.
    /// </summary>
    public decimal AvailableCredit => Math.Max(0, CreditLimit - CreditBalance);
}
