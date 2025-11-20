using Eleventa.Domain.Aggregates;
using Eleventa.Domain.Aggregates.Examples;
using Eleventa.Domain.ValueObjects;
using Xunit;

namespace Eleventa.Tests.Aggregates;

public class OrderTests
{
    [Fact]
    public void Create_ValidOrder_Success()
    {
        // Act
        var order = new Order(Guid.NewGuid(), "USD");

        // Assert
        Assert.Equal(OrderStatus.Draft, order.Status);
        Assert.Empty(order.Items);
        Assert.True(order.HasDomainEvents);
    }

    [Fact]
    public void AddItem_ValidItem_Success()
    {
        // Arrange
        var order = new Order(Guid.NewGuid(), "USD");
        var productId = Guid.NewGuid();
        var unitPrice = Money.Create(10, "USD");

        // Act
        order.AddItem(productId, "Widget", 2, unitPrice);

        // Assert
        Assert.Single(order.Items);
        Assert.Equal(2, order.Items.First().Quantity);
    }

    [Fact]
    public void AddItem_NegativeQuantity_ThrowsException()
    {
        // Arrange
        var order = new Order(Guid.NewGuid(), "USD");
        var unitPrice = Money.Create(10, "USD");

        // Act & Assert
        Assert.Throws<DomainException>(() =>
            order.AddItem(Guid.NewGuid(), "Widget", -1, unitPrice));
    }

    [Fact]
    public void AddItem_WrongCurrency_ThrowsException()
    {
        // Arrange
        var order = new Order(Guid.NewGuid(), "USD");
        var unitPrice = Money.Create(10, "EUR");

        // Act & Assert
        Assert.Throws<DomainException>(() =>
            order.AddItem(Guid.NewGuid(), "Widget", 1, unitPrice));
    }

    [Fact]
    public void CalculateTotal_MultipleItems_CorrectSum()
    {
        // Arrange
        var order = new Order(Guid.NewGuid(), "USD");
        order.AddItem(Guid.NewGuid(), "Widget", 2, Money.Create(10, "USD"));
        order.AddItem(Guid.NewGuid(), "Gadget", 3, Money.Create(5, "USD"));

        // Act
        var total = order.Total;

        // Assert
        Assert.Equal(35m, total.Amount); // (2*10) + (3*5) = 35
        Assert.Equal("USD", total.Currency);
    }

    [Fact]
    public void Submit_ValidOrder_StatusChanged()
    {
        // Arrange
        var order = new Order(Guid.NewGuid(), "USD");
        order.AddItem(Guid.NewGuid(), "Widget", 1, Money.Create(10, "USD"));

        // Act
        order.Submit();

        // Assert
        Assert.Equal(OrderStatus.Submitted, order.Status);
        Assert.True(order.DomainEvents.Any(e => e is OrderSubmittedEvent));
    }

    [Fact]
    public void Submit_EmptyOrder_ThrowsException()
    {
        // Arrange
        var order = new Order(Guid.NewGuid(), "USD");

        // Act & Assert
        Assert.Throws<DomainException>(() => order.Submit());
    }

    [Fact]
    public void RemoveItem_ExistingItem_Success()
    {
        // Arrange
        var order = new Order(Guid.NewGuid(), "USD");
        var productId = Guid.NewGuid();
        order.AddItem(productId, "Widget", 1, Money.Create(10, "USD"));

        // Act
        order.RemoveItem(productId);

        // Assert
        Assert.Empty(order.Items);
    }

    [Fact]
    public void Cancel_ValidOrder_StatusChanged()
    {
        // Arrange
        var order = new Order(Guid.NewGuid(), "USD");
        order.AddItem(Guid.NewGuid(), "Widget", 1, Money.Create(10, "USD"));

        // Act
        order.Cancel("Customer request");

        // Assert
        Assert.Equal(OrderStatus.Cancelled, order.Status);
    }

    [Fact]
    public void AddItem_AfterSubmit_ThrowsException()
    {
        // Arrange
        var order = new Order(Guid.NewGuid(), "USD");
        order.AddItem(Guid.NewGuid(), "Widget", 1, Money.Create(10, "USD"));
        order.Submit();

        // Act & Assert
        Assert.Throws<DomainException>(() =>
            order.AddItem(Guid.NewGuid(), "Gadget", 1, Money.Create(5, "USD")));
    }
}
