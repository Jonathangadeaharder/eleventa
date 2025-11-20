namespace Eleventa.Domain.Entities;

/// <summary>
/// Represents a sale transaction.
/// </summary>
public class Sale
{
    public int Id { get; set; }
    public DateTime Timestamp { get; set; } = DateTime.Now;
    public int? CustomerId { get; set; }
    public int? UserId { get; set; }
    public bool IsCreditSale { get; set; }
    public PaymentType? PaymentType { get; set; }
    public string? Status { get; set; }

    // Navigation properties
    public Customer? Customer { get; set; }
    public User? User { get; set; }
    public ICollection<SaleItem> Items { get; set; } = new List<SaleItem>();

    /// <summary>
    /// Calculates the total amount of the sale.
    /// </summary>
    public decimal Total
    {
        get
        {
            if (Items == null || !Items.Any())
                return 0m;

            return Items.Sum(item => item.Subtotal);
        }
    }

    /// <summary>
    /// Gets the total number of items in the sale.
    /// </summary>
    public int ItemCount => Items?.Count ?? 0;

    /// <summary>
    /// Adds an item to the sale.
    /// </summary>
    public void AddItem(int productId, string productCode, string productDescription,
                       string productUnit, decimal quantity, decimal unitPrice)
    {
        var item = new SaleItem
        {
            ProductId = productId,
            ProductCode = productCode,
            ProductDescription = productDescription,
            ProductUnit = productUnit,
            Quantity = quantity,
            UnitPrice = unitPrice
        };

        Items.Add(item);
    }
}

/// <summary>
/// Represents an item within a sale.
/// </summary>
public class SaleItem
{
    public int Id { get; set; }
    public int? SaleId { get; set; }
    public int ProductId { get; set; }

    // Denormalized fields for display
    public string ProductCode { get; set; } = string.Empty;
    public string ProductDescription { get; set; } = string.Empty;
    public string ProductUnit { get; set; } = "Unidad";

    public decimal Quantity { get; set; }
    public decimal UnitPrice { get; set; }

    // Navigation properties
    public Sale? Sale { get; set; }
    public Product? Product { get; set; }

    /// <summary>
    /// Calculates the subtotal for this line item.
    /// </summary>
    public decimal Subtotal => Math.Round(Quantity * UnitPrice, 2);
}
