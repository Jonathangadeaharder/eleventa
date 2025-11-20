using Eleventa.Domain.ValueObjects;
using Xunit;

namespace Eleventa.Tests.ValueObjects;

public class PhoneNumberTests
{
    [Fact]
    public void Create_ValidE164_Success()
    {
        // Act
        var phone = PhoneNumber.Create("+15551234567");

        // Assert
        Assert.Equal("+15551234567", phone.Value);
    }

    [Fact]
    public void Create_WithSpaces_NormalizesCorrectly()
    {
        // Act
        var phone = PhoneNumber.Create("+1 555 123 4567");

        // Assert
        Assert.Equal("+15551234567", phone.Value);
    }

    [Fact]
    public void Create_WithDashes_NormalizesCorrectly()
    {
        // Act
        var phone = PhoneNumber.Create("+1-555-123-4567");

        // Assert
        Assert.Equal("+15551234567", phone.Value);
    }

    [Fact]
    public void Create_WithParentheses_NormalizesCorrectly()
    {
        // Act
        var phone = PhoneNumber.Create("+1 (555) 123-4567");

        // Assert
        Assert.Equal("+15551234567", phone.Value);
    }

    [Fact]
    public void Create_EmptyString_ThrowsException()
    {
        // Act & Assert
        Assert.Throws<ValidationException>(() => PhoneNumber.Create(""));
    }

    [Fact]
    public void Create_WithoutPlus_ThrowsException()
    {
        // Act & Assert
        Assert.Throws<ValidationException>(() => PhoneNumber.Create("15551234567"));
    }

    [Fact]
    public void Create_InvalidFormat_ThrowsException()
    {
        // Act & Assert
        Assert.Throws<ValidationException>(() => PhoneNumber.Create("+1"));
    }

    [Fact]
    public void FromParts_ValidParts_Success()
    {
        // Act
        var phone = PhoneNumber.FromParts("1", "555", "1234567");

        // Assert
        Assert.Equal("+15551234567", phone.Value);
    }

    [Fact]
    public void FromParts_EmptyCountryCode_ThrowsException()
    {
        // Act & Assert
        Assert.Throws<ArgumentException>(() =>
            PhoneNumber.FromParts("", "555", "1234567"));
    }

    [Fact]
    public void CountryCode_USNumber_ExtractsCorrectly()
    {
        // Arrange
        var phone = PhoneNumber.Create("+15551234567");

        // Act
        var countryCode = phone.CountryCode;

        // Assert
        Assert.Equal("1", countryCode);
    }

    [Fact]
    public void CountryCode_UKNumber_ExtractsCorrectly()
    {
        // Arrange
        var phone = PhoneNumber.Create("+442071234567");

        // Act
        var countryCode = phone.CountryCode;

        // Assert
        Assert.Equal("44", countryCode);
    }

    [Fact]
    public void Format_International_ReturnsFullNumber()
    {
        // Arrange
        var phone = PhoneNumber.Create("+15551234567");

        // Act
        var formatted = phone.Format("international");

        // Assert
        Assert.Equal("+15551234567", formatted);
    }

    [Fact]
    public void Format_National_RemovesPlus()
    {
        // Arrange
        var phone = PhoneNumber.Create("+15551234567");

        // Act
        var formatted = phone.Format("national");

        // Assert
        Assert.Equal("15551234567", formatted);
    }

    [Fact]
    public void ImplicitConversion_ToStringWorks()
    {
        // Arrange
        var phone = PhoneNumber.Create("+15551234567");

        // Act
        string phoneString = phone;

        // Assert
        Assert.Equal("+15551234567", phoneString);
    }

    [Fact]
    public void ToString_ReturnsValue()
    {
        // Arrange
        var phone = PhoneNumber.Create("+15551234567");

        // Act
        var result = phone.ToString();

        // Assert
        Assert.Equal("+15551234567", result);
    }

    [Fact]
    public void Equality_SameNumbers_ReturnsTrue()
    {
        // Arrange
        var phone1 = PhoneNumber.Create("+15551234567");
        var phone2 = PhoneNumber.Create("+1 555 123 4567"); // Normalized

        // Act & Assert
        Assert.Equal(phone1, phone2);
    }
}
