using Eleventa.Domain.Aggregates;
using Eleventa.Domain.Aggregates.Examples;
using Xunit;

namespace Eleventa.Tests.Aggregates;

public class ShoppingCartTests
{
    [Fact]
    public void Create_ValidCart_Success()
    {
        // Act
        var cart = new ShoppingCart(Guid.NewGuid());

        // Assert
        Assert.Empty(cart.Items);
        Assert.Equal(0, cart.ItemCount);
    }

    [Fact]
    public void AddItem_NewItem_AddsToCart()
    {
        // Arrange
        var cart = new ShoppingCart(Guid.NewGuid());
        var productId = Guid.NewGuid();

        // Act
        cart.AddItem(productId, 2);

        // Assert
        Assert.Single(cart.Items);
        Assert.Equal(2, cart.Items.First().Quantity);
        Assert.Equal(2, cart.ItemCount);
    }

    [Fact]
    public void AddItem_ExistingItem_UpdatesQuantity()
    {
        // Arrange
        var cart = new ShoppingCart(Guid.NewGuid());
        var productId = Guid.NewGuid();
        cart.AddItem(productId, 2);

        // Act
        cart.AddItem(productId, 3);

        // Assert
        Assert.Single(cart.Items);
        Assert.Equal(5, cart.Items.First().Quantity); // 2 + 3
        Assert.Equal(5, cart.ItemCount);
    }

    [Fact]
    public void AddItem_ZeroQuantity_ThrowsException()
    {
        // Arrange
        var cart = new ShoppingCart(Guid.NewGuid());

        // Act & Assert
        Assert.Throws<DomainException>(() => cart.AddItem(Guid.NewGuid(), 0));
    }

    [Fact]
    public void AddItem_NegativeQuantity_ThrowsException()
    {
        // Arrange
        var cart = new ShoppingCart(Guid.NewGuid());

        // Act & Assert
        Assert.Throws<DomainException>(() => cart.AddItem(Guid.NewGuid(), -1));
    }

    [Fact]
    public void RemoveItem_ExistingItem_RemovesFromCart()
    {
        // Arrange
        var cart = new ShoppingCart(Guid.NewGuid());
        var productId = Guid.NewGuid();
        cart.AddItem(productId, 2);

        // Act
        cart.RemoveItem(productId);

        // Assert
        Assert.Empty(cart.Items);
        Assert.Equal(0, cart.ItemCount);
    }

    [Fact]
    public void RemoveItem_NonExistingItem_DoesNothing()
    {
        // Arrange
        var cart = new ShoppingCart(Guid.NewGuid());
        var productId1 = Guid.NewGuid();
        var productId2 = Guid.NewGuid();
        cart.AddItem(productId1, 2);

        // Act
        cart.RemoveItem(productId2);

        // Assert
        Assert.Single(cart.Items);
    }

    [Fact]
    public void UpdateQuantity_ExistingItem_UpdatesCorrectly()
    {
        // Arrange
        var cart = new ShoppingCart(Guid.NewGuid());
        var productId = Guid.NewGuid();
        cart.AddItem(productId, 2);

        // Act
        cart.UpdateQuantity(productId, 5);

        // Assert
        Assert.Single(cart.Items);
        Assert.Equal(5, cart.Items.First().Quantity);
    }

    [Fact]
    public void UpdateQuantity_ZeroQuantity_ThrowsException()
    {
        // Arrange
        var cart = new ShoppingCart(Guid.NewGuid());
        var productId = Guid.NewGuid();
        cart.AddItem(productId, 2);

        // Act & Assert
        Assert.Throws<DomainException>(() => cart.UpdateQuantity(productId, 0));
    }

    [Fact]
    public void UpdateQuantity_NonExistingItem_DoesNothing()
    {
        // Arrange
        var cart = new ShoppingCart(Guid.NewGuid());

        // Act
        cart.UpdateQuantity(Guid.NewGuid(), 5);

        // Assert
        Assert.Empty(cart.Items);
    }

    [Fact]
    public void Clear_WithItems_RemovesAllItems()
    {
        // Arrange
        var cart = new ShoppingCart(Guid.NewGuid());
        cart.AddItem(Guid.NewGuid(), 2);
        cart.AddItem(Guid.NewGuid(), 3);

        // Act
        cart.Clear();

        // Assert
        Assert.Empty(cart.Items);
        Assert.Equal(0, cart.ItemCount);
    }

    [Fact]
    public void ItemCount_MultipleItems_ReturnsSum()
    {
        // Arrange
        var cart = new ShoppingCart(Guid.NewGuid());
        cart.AddItem(Guid.NewGuid(), 2);
        cart.AddItem(Guid.NewGuid(), 3);
        cart.AddItem(Guid.NewGuid(), 5);

        // Act
        var count = cart.ItemCount;

        // Assert
        Assert.Equal(10, count); // 2 + 3 + 5
    }
}
