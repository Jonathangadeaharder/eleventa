using Eleventa.Domain.ValueObjects;
using Xunit;

namespace Eleventa.Tests.ValueObjects;

public class MoneyTests
{
    [Fact]
    public void Create_ValidMoney_Success()
    {
        // Arrange & Act
        var money = Money.Create(10.50m, "USD");

        // Assert
        Assert.Equal(10.50m, money.Amount);
        Assert.Equal("USD", money.Currency);
    }

    [Fact]
    public void Create_InvalidCurrency_ThrowsException()
    {
        // Act & Assert
        Assert.Throws<ValidationException>(() => Money.Create(10, "US"));
    }

    [Fact]
    public void Add_SameCurrency_Success()
    {
        // Arrange
        var money1 = Money.Create(10, "USD");
        var money2 = Money.Create(5, "USD");

        // Act
        var result = money1.Add(money2);

        // Assert
        Assert.Equal(15m, result.Amount);
        Assert.Equal("USD", result.Currency);
    }

    [Fact]
    public void Add_DifferentCurrency_ThrowsException()
    {
        // Arrange
        var money1 = Money.Create(10, "USD");
        var money2 = Money.Create(5, "EUR");

        // Act & Assert
        Assert.Throws<InvalidOperationException>(() => money1.Add(money2));
    }

    [Fact]
    public void Subtract_ValidAmount_Success()
    {
        // Arrange
        var money1 = Money.Create(10, "USD");
        var money2 = Money.Create(3, "USD");

        // Act
        var result = money1.Subtract(money2);

        // Assert
        Assert.Equal(7m, result.Amount);
    }

    [Fact]
    public void Multiply_ByScalar_Success()
    {
        // Arrange
        var money = Money.Create(10, "USD");

        // Act
        var result = money.Multiply(2.5m);

        // Assert
        Assert.Equal(25m, result.Amount);
    }

    [Fact]
    public void Divide_ByScalar_Success()
    {
        // Arrange
        var money = Money.Create(10, "USD");

        // Act
        var result = money.Divide(2);

        // Assert
        Assert.Equal(5m, result.Amount);
    }

    [Fact]
    public void Allocate_ProportionalRatios_NoRoundingErrors()
    {
        // Arrange
        var money = Money.Create(100, "USD");

        // Act
        var results = money.Allocate(1, 1, 1);

        // Assert
        Assert.Equal(3, results.Count);
        var total = results[0].Amount + results[1].Amount + results[2].Amount;
        Assert.Equal(100m, total);
    }

    [Fact]
    public void IsZero_ZeroAmount_ReturnsTrue()
    {
        // Arrange
        var money = Money.Zero("USD");

        // Act & Assert
        Assert.True(money.IsZero());
    }

    [Fact]
    public void IsPositive_PositiveAmount_ReturnsTrue()
    {
        // Arrange
        var money = Money.Create(10, "USD");

        // Act & Assert
        Assert.True(money.IsPositive());
    }

    [Fact]
    public void OperatorOverload_Add_Success()
    {
        // Arrange
        var money1 = Money.Create(10, "USD");
        var money2 = Money.Create(5, "USD");

        // Act
        var result = money1 + money2;

        // Assert
        Assert.Equal(15m, result.Amount);
    }

    [Fact]
    public void Equality_SameValues_ReturnsTrue()
    {
        // Arrange
        var money1 = Money.Create(10, "USD");
        var money2 = Money.Create(10, "USD");

        // Act & Assert
        Assert.Equal(money1, money2);
        Assert.True(money1 == money2);
    }

    [Fact]
    public void Comparison_GreaterThan_Success()
    {
        // Arrange
        var money1 = Money.Create(15, "USD");
        var money2 = Money.Create(10, "USD");

        // Act & Assert
        Assert.True(money1 > money2);
    }
}
