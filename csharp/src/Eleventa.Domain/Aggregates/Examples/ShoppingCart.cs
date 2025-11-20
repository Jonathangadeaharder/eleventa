namespace Eleventa.Domain.Aggregates.Examples;

/// <summary>
/// Shopping cart aggregate root.
/// Manages cart items before checkout.
/// </summary>
public class ShoppingCart : AggregateRoot<Guid>
{
    private readonly List<CartItem> _items = new();

    public IReadOnlyCollection<CartItem> Items => _items.AsReadOnly();

    public ShoppingCart(Guid id) : base(id)
    {
    }

    /// <summary>
    /// Adds an item to the cart.
    /// </summary>
    public void AddItem(Guid productId, int quantity = 1)
    {
        if (quantity <= 0)
            throw new DomainException("Quantity must be positive");

        var existingItem = _items.FirstOrDefault(i => i.ProductId == productId);
        if (existingItem != null)
        {
            _items.Remove(existingItem);
            quantity += existingItem.Quantity;
        }

        _items.Add(new CartItem(productId, quantity));
    }

    /// <summary>
    /// Removes an item from the cart.
    /// </summary>
    public void RemoveItem(Guid productId)
    {
        var item = _items.FirstOrDefault(i => i.ProductId == productId);
        if (item != null)
        {
            _items.Remove(item);
        }
    }

    /// <summary>
    /// Updates item quantity.
    /// </summary>
    public void UpdateQuantity(Guid productId, int quantity)
    {
        if (quantity <= 0)
            throw new DomainException("Quantity must be positive");

        var item = _items.FirstOrDefault(i => i.ProductId == productId);
        if (item != null)
        {
            _items.Remove(item);
            _items.Add(item with { Quantity = quantity });
        }
    }

    /// <summary>
    /// Clears all items from the cart.
    /// </summary>
    public void Clear()
    {
        _items.Clear();
    }

    /// <summary>
    /// Gets total item count.
    /// </summary>
    public int ItemCount => _items.Sum(i => i.Quantity);
}

public record CartItem(Guid ProductId, int Quantity);
