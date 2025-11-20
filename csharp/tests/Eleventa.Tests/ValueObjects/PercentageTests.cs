using Eleventa.Domain.ValueObjects;
using Xunit;

namespace Eleventa.Tests.ValueObjects;

public class PercentageTests
{
    [Fact]
    public void Create_ValidPercentage_Success()
    {
        // Act
        var percentage = Percentage.Create(25);

        // Assert
        Assert.Equal(25m, percentage.Value);
    }

    [Fact]
    public void Create_NegativeValue_ThrowsException()
    {
        // Act & Assert
        Assert.Throws<ValidationException>(() => Percentage.Create(-10));
    }

    [Fact]
    public void Create_OverHundred_ThrowsException()
    {
        // Act & Assert
        Assert.Throws<ValidationException>(() => Percentage.Create(101));
    }

    [Fact]
    public void FromDecimal_ValidDecimal_Success()
    {
        // Act
        var percentage = Percentage.FromDecimal(0.25m);

        // Assert
        Assert.Equal(25m, percentage.Value);
    }

    [Fact]
    public void FromRatio_ValidRatio_Success()
    {
        // Act
        var percentage = Percentage.FromRatio(1, 4);

        // Assert
        Assert.Equal(25m, percentage.Value);
    }

    [Fact]
    public void FromRatio_ZeroDenominator_ThrowsException()
    {
        // Act & Assert
        Assert.Throws<DivideByZeroException>(() => Percentage.FromRatio(1, 0));
    }

    [Fact]
    public void AsDecimal_ValidPercentage_ReturnsDecimal()
    {
        // Arrange
        var percentage = Percentage.Create(50);

        // Act
        var result = percentage.AsDecimal();

        // Assert
        Assert.Equal(0.5m, result);
    }

    [Fact]
    public void Of_ValidAmount_CalculatesCorrectly()
    {
        // Arrange
        var percentage = Percentage.Create(10);

        // Act
        var result = percentage.Of(100);

        // Assert
        Assert.Equal(10m, result);
    }

    [Fact]
    public void AddTo_ValidAmount_AddsCorrectly()
    {
        // Arrange
        var percentage = Percentage.Create(10);

        // Act
        var result = percentage.AddTo(100);

        // Assert
        Assert.Equal(110m, result);
    }

    [Fact]
    public void SubtractFrom_ValidAmount_SubtractsCorrectly()
    {
        // Arrange
        var percentage = Percentage.Create(10);

        // Act
        var result = percentage.SubtractFrom(100);

        // Assert
        Assert.Equal(90m, result);
    }

    [Fact]
    public void Add_TwoPercentages_Success()
    {
        // Arrange
        var p1 = Percentage.Create(10);
        var p2 = Percentage.Create(5);

        // Act
        var result = p1.Add(p2);

        // Assert
        Assert.Equal(15m, result.Value);
    }

    [Fact]
    public void Multiply_ByScalar_Success()
    {
        // Arrange
        var percentage = Percentage.Create(10);

        // Act
        var result = percentage.Multiply(2);

        // Assert
        Assert.Equal(20m, result.Value);
    }

    [Fact]
    public void IsZero_ZeroPercentage_ReturnsTrue()
    {
        // Arrange
        var percentage = Percentage.Zero;

        // Act & Assert
        Assert.True(percentage.IsZero());
    }

    [Fact]
    public void IsFull_HundredPercent_ReturnsTrue()
    {
        // Arrange
        var percentage = Percentage.Full;

        // Act & Assert
        Assert.True(percentage.IsFull());
    }

    [Fact]
    public void OperatorAdd_TwoPercentages_Success()
    {
        // Arrange
        var p1 = Percentage.Create(10);
        var p2 = Percentage.Create(5);

        // Act
        var result = p1 + p2;

        // Assert
        Assert.Equal(15m, result.Value);
    }

    [Fact]
    public void OperatorMultiply_ByScalar_Success()
    {
        // Arrange
        var percentage = Percentage.Create(10);

        // Act
        var result = percentage * 2;

        // Assert
        Assert.Equal(20m, result.Value);
    }

    [Fact]
    public void ToString_FormatsCorrectly()
    {
        // Arrange
        var percentage = Percentage.Create(25.5m);

        // Act
        var result = percentage.ToString();

        // Assert
        Assert.Equal("25.50%", result);
    }
}
