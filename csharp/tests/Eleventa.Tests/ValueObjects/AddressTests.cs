using Eleventa.Domain.ValueObjects;
using Xunit;

namespace Eleventa.Tests.ValueObjects;

public class AddressTests
{
    [Fact]
    public void Create_ValidAddress_Success()
    {
        // Act
        var address = Address.Create("123 Main St", "Springfield", "62701", "USA");

        // Assert
        Assert.Equal("123 Main St", address.Street);
        Assert.Equal("Springfield", address.City);
        Assert.Equal("62701", address.PostalCode);
        Assert.Equal("USA", address.Country);
    }

    [Fact]
    public void Create_WithStateAndInfo_Success()
    {
        // Act
        var address = Address.Create(
            "123 Main St",
            "Springfield",
            "62701",
            "USA",
            "IL",
            "Apt 4B");

        // Assert
        Assert.Equal("IL", address.State);
        Assert.Equal("Apt 4B", address.AdditionalInfo);
    }

    [Fact]
    public void Create_EmptyStreet_ThrowsException()
    {
        // Act & Assert
        Assert.Throws<ValidationException>(() =>
            Address.Create("", "City", "12345", "USA"));
    }

    [Fact]
    public void Create_EmptyCity_ThrowsException()
    {
        // Act & Assert
        Assert.Throws<ValidationException>(() =>
            Address.Create("Street", "", "12345", "USA"));
    }

    [Fact]
    public void Create_EmptyPostalCode_ThrowsException()
    {
        // Act & Assert
        Assert.Throws<ValidationException>(() =>
            Address.Create("Street", "City", "", "USA"));
    }

    [Fact]
    public void Create_EmptyCountry_ThrowsException()
    {
        // Act & Assert
        Assert.Throws<ValidationException>(() =>
            Address.Create("Street", "City", "12345", ""));
    }

    [Fact]
    public void IsInCountry_SameCountry_ReturnsTrue()
    {
        // Arrange
        var address = Address.Create("123 Main St", "Springfield", "62701", "USA");

        // Act & Assert
        Assert.True(address.IsInCountry("USA"));
        Assert.True(address.IsInCountry("usa")); // Case insensitive
    }

    [Fact]
    public void IsInCountry_DifferentCountry_ReturnsFalse()
    {
        // Arrange
        var address = Address.Create("123 Main St", "Springfield", "62701", "USA");

        // Act & Assert
        Assert.False(address.IsInCountry("Canada"));
    }

    [Fact]
    public void ToSingleLine_WithoutState_FormatsCorrectly()
    {
        // Arrange
        var address = Address.Create("123 Main St", "Springfield", "62701", "USA");

        // Act
        var singleLine = address.ToSingleLine();

        // Assert
        Assert.Equal("123 Main St, Springfield, 62701, USA", singleLine);
    }

    [Fact]
    public void ToSingleLine_WithState_FormatsCorrectly()
    {
        // Arrange
        var address = Address.Create("123 Main St", "Springfield", "62701", "USA", "IL");

        // Act
        var singleLine = address.ToSingleLine();

        // Assert
        Assert.Equal("123 Main St, Springfield, IL, 62701, USA", singleLine);
    }

    [Fact]
    public void ToMultiLine_WithoutAdditionalInfo_FormatsCorrectly()
    {
        // Arrange
        var address = Address.Create("123 Main St", "Springfield", "62701", "USA", "IL");

        // Act
        var multiLine = address.ToMultiLine();

        // Assert
        var lines = multiLine.Split(Environment.NewLine);
        Assert.Equal(3, lines.Length);
        Assert.Equal("123 Main St", lines[0]);
        Assert.Equal("Springfield, IL 62701", lines[1]);
        Assert.Equal("USA", lines[2]);
    }

    [Fact]
    public void ToMultiLine_WithAdditionalInfo_FormatsCorrectly()
    {
        // Arrange
        var address = Address.Create(
            "123 Main St",
            "Springfield",
            "62701",
            "USA",
            "IL",
            "Apt 4B");

        // Act
        var multiLine = address.ToMultiLine();

        // Assert
        var lines = multiLine.Split(Environment.NewLine);
        Assert.Equal(4, lines.Length);
        Assert.Equal("123 Main St", lines[0]);
        Assert.Equal("Apt 4B", lines[1]);
        Assert.Contains("Springfield", lines[2]);
    }

    [Fact]
    public void ToString_CallsToSingleLine()
    {
        // Arrange
        var address = Address.Create("123 Main St", "Springfield", "62701", "USA");

        // Act
        var result = address.ToString();

        // Assert
        Assert.Equal(address.ToSingleLine(), result);
    }

    [Fact]
    public void Equality_SameAddresses_ReturnsTrue()
    {
        // Arrange
        var address1 = Address.Create("123 Main St", "Springfield", "62701", "USA");
        var address2 = Address.Create("123 Main St", "Springfield", "62701", "USA");

        // Act & Assert
        Assert.Equal(address1, address2);
    }

    [Fact]
    public void Equality_DifferentAddresses_ReturnsFalse()
    {
        // Arrange
        var address1 = Address.Create("123 Main St", "Springfield", "62701", "USA");
        var address2 = Address.Create("456 Oak Ave", "Springfield", "62701", "USA");

        // Act & Assert
        Assert.NotEqual(address1, address2);
    }
}
