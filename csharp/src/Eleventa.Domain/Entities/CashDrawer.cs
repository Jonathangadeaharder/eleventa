namespace Eleventa.Domain.Entities;

/// <summary>
/// Represents a cash drawer opening/closing session.
/// </summary>
public class CashDrawerSession
{
    public int Id { get; set; }
    public int UserId { get; set; }
    public DateTime OpenedAt { get; set; } = DateTime.Now;
    public DateTime? ClosedAt { get; set; }
    public decimal OpeningBalance { get; set; }
    public decimal? ClosingBalance { get; set; }
    public decimal? ExpectedBalance { get; set; }
    public decimal? Difference { get; set; }
    public string? Notes { get; set; }
    public bool IsClosed { get; set; }

    // Navigation properties
    public User? User { get; set; }
    public ICollection<CashDrawerEntry> Entries { get; set; } = new List<CashDrawerEntry>();

    /// <summary>
    /// Calculates the current balance based on entries.
    /// </summary>
    public decimal CurrentBalance
    {
        get
        {
            var entriesTotal = Entries?
                .Where(e => e.EntryType != CashDrawerEntryType.Close)
                .Sum(e => e.EntryType == CashDrawerEntryType.In ? e.Amount : -e.Amount) ?? 0;

            return OpeningBalance + entriesTotal;
        }
    }
}

/// <summary>
/// Represents a cash drawer entry (money in/out).
/// </summary>
public class CashDrawerEntry
{
    public int Id { get; set; }
    public int CashDrawerSessionId { get; set; }
    public CashDrawerEntryType EntryType { get; set; }
    public decimal Amount { get; set; }
    public string? Reason { get; set; }
    public string? Reference { get; set; }
    public DateTime Timestamp { get; set; } = DateTime.Now;
    public int? UserId { get; set; }

    // Navigation properties
    public CashDrawerSession? CashDrawerSession { get; set; }
    public User? User { get; set; }
}
