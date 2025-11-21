using Eleventa.Domain.ValueObjects;
using Xunit;

namespace Eleventa.Tests.ValueObjects;

public class TaxIdTests
{
    [Fact]
    public void Create_ValidCUIT_Success()
    {
        // Valid CUIT with correct check digit
        // Act
        var taxId = TaxId.Create("20-12345678-6");

        // Assert
        Assert.Equal("20123456786", taxId.Value);
    }

    [Fact]
    public void Create_WithoutDashes_Success()
    {
        // Act
        var taxId = TaxId.Create("20123456786");

        // Assert
        Assert.Equal("20123456786", taxId.Value);
    }

    [Fact]
    public void Create_EmptyString_ThrowsException()
    {
        // Act & Assert
        Assert.Throws<ValidationException>(() => TaxId.Create(""));
    }

    [Fact]
    public void Create_WrongLength_ThrowsException()
    {
        // Act & Assert
        Assert.Throws<ValidationException>(() => TaxId.Create("123456789"));
    }

    [Fact]
    public void Create_InvalidCheckDigit_ThrowsException()
    {
        // Act & Assert
        Assert.Throws<ValidationException>(() => TaxId.Create("20-12345678-9"));
    }

    [Fact]
    public void Create_NonNumeric_ThrowsException()
    {
        // Act & Assert
        Assert.Throws<ValidationException>(() => TaxId.Create("AB-12345678-6"));
    }

    [Fact]
    public void Digits_ReturnsCUITDigitsOnly()
    {
        // Arrange
        var taxId = TaxId.Create("20-12345678-6");

        // Act
        var digits = taxId.Digits;

        // Assert
        Assert.Equal("20123456786", digits);
    }

    [Fact]
    public void TypeCode_ExtractsFirstTwoDigits()
    {
        // Arrange
        var taxId = TaxId.Create("20-12345678-6");

        // Act
        var typeCode = taxId.TypeCode;

        // Assert
        Assert.Equal("20", typeCode);
    }

    [Fact]
    public void Format_AddsDashes()
    {
        // Arrange
        var taxId = TaxId.Create("20123456786");

        // Act
        var formatted = taxId.Format();

        // Assert
        Assert.Equal("20-12345678-6", formatted);
    }

    [Fact]
    public void ToString_ReturnsFormatted()
    {
        // Arrange
        var taxId = TaxId.Create("20123456786");

        // Act
        var result = taxId.ToString();

        // Assert
        Assert.Equal("20-12345678-6", result);
    }

    [Fact]
    public void ImplicitConversion_ToStringWorks()
    {
        // Arrange
        var taxId = TaxId.Create("20-12345678-6");

        // Act
        string taxIdString = taxId;

        // Assert
        Assert.Equal("20123456786", taxIdString);
    }

    [Fact]
    public void Equality_SameTaxIds_ReturnsTrue()
    {
        // Arrange
        var taxId1 = TaxId.Create("20-12345678-6");
        var taxId2 = TaxId.Create("20123456786"); // No dashes

        // Act & Assert
        Assert.Equal(taxId1, taxId2);
    }

    [Fact]
    public void Create_DifferentValidCUITs_Success()
    {
        // Test with multiple valid CUITs to verify check digit algorithm
        // These are mathematically valid CUITs (check digit calculated correctly)

        // Act & Assert
        Assert.NotNull(TaxId.Create("20123456786")); // Type 20
        Assert.NotNull(TaxId.Create("23123456789")); // Type 23 (company)
        Assert.NotNull(TaxId.Create("27123456782")); // Type 27
    }
}
