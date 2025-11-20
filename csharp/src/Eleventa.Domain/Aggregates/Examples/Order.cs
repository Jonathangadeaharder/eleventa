using Eleventa.Domain.ValueObjects;

namespace Eleventa.Domain.Aggregates.Examples;

/// <summary>
/// Order aggregate root.
/// Manages order items and enforces business rules.
/// </summary>
public class Order : AggregateRoot<Guid>
{
    private readonly List<OrderItem> _items = new();
    private OrderStatus _status;

    public IReadOnlyCollection<OrderItem> Items => _items.AsReadOnly();
    public OrderStatus Status => _status;
    public string Currency { get; private set; }

    public Order(Guid id, string currency = "USD") : base(id)
    {
        Currency = currency;
        _status = OrderStatus.Draft;
        AddDomainEvent(new OrderCreatedEvent(id, currency));
    }

    /// <summary>
    /// Adds an item to the order.
    /// </summary>
    public void AddItem(Guid productId, string productName, int quantity, Money unitPrice)
    {
        if (_status != OrderStatus.Draft)
            throw new DomainException("Cannot add items to a submitted order");

        if (quantity <= 0)
            throw new DomainException("Quantity must be positive");

        if (unitPrice.Currency != Currency)
            throw new DomainException($"Unit price currency ({unitPrice.Currency}) doesn't match order currency ({Currency})");

        var existingItem = _items.FirstOrDefault(i => i.ProductId == productId);
        if (existingItem != null)
        {
            // Update quantity if item already exists
            _items.Remove(existingItem);
            quantity += existingItem.Quantity;
        }

        var item = new OrderItem(productId, productName, quantity, unitPrice);
        _items.Add(item);

        AddDomainEvent(new OrderItemAddedEvent(Id, productId, productName, quantity, unitPrice.Amount));
    }

    /// <summary>
    /// Removes an item from the order.
    /// </summary>
    public void RemoveItem(Guid productId)
    {
        if (_status != OrderStatus.Draft)
            throw new DomainException("Cannot remove items from a submitted order");

        var item = _items.FirstOrDefault(i => i.ProductId == productId);
        if (item == null)
            throw new DomainException($"Item {productId} not found in order");

        _items.Remove(item);
        AddDomainEvent(new OrderItemRemovedEvent(Id, productId));
    }

    /// <summary>
    /// Changes the quantity of an item.
    /// </summary>
    public void ChangeItemQuantity(Guid productId, int newQuantity)
    {
        if (_status != OrderStatus.Draft)
            throw new DomainException("Cannot change items in a submitted order");

        if (newQuantity <= 0)
            throw new DomainException("Quantity must be positive");

        var item = _items.FirstOrDefault(i => i.ProductId == productId);
        if (item == null)
            throw new DomainException($"Item {productId} not found in order");

        _items.Remove(item);
        _items.Add(item with { Quantity = newQuantity });
    }

    /// <summary>
    /// Submits the order.
    /// </summary>
    public void Submit()
    {
        if (_status != OrderStatus.Draft)
            throw new DomainException("Order has already been submitted");

        if (!_items.Any())
            throw new DomainException("Cannot submit an empty order");

        _status = OrderStatus.Submitted;
        AddDomainEvent(new OrderSubmittedEvent(Id, Total.Amount));
    }

    /// <summary>
    /// Cancels the order.
    /// </summary>
    public void Cancel(string reason)
    {
        if (_status == OrderStatus.Cancelled)
            throw new DomainException("Order is already cancelled");

        _status = OrderStatus.Cancelled;
        AddDomainEvent(new OrderCancelledEvent(Id, reason));
    }

    /// <summary>
    /// Calculates the order total.
    /// </summary>
    public Money Total
    {
        get
        {
            if (!_items.Any())
                return Money.Zero(Currency);

            return _items
                .Select(item => item.Subtotal)
                .Aggregate((acc, money) => acc.Add(money));
        }
    }
}

/// <summary>
/// Order item entity.
/// </summary>
public record OrderItem
{
    public Guid ProductId { get; init; }
    public string ProductName { get; init; }
    public int Quantity { get; init; }
    public Money UnitPrice { get; init; }

    public OrderItem(Guid productId, string productName, int quantity, Money unitPrice)
    {
        ProductId = productId;
        ProductName = productName;
        Quantity = quantity;
        UnitPrice = unitPrice;
    }

    public Money Subtotal => UnitPrice.Multiply(Quantity);
}

public enum OrderStatus
{
    Draft,
    Submitted,
    Cancelled
}
