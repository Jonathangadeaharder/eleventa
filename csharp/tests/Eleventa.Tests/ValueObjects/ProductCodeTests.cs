using Eleventa.Domain.ValueObjects;
using Xunit;

namespace Eleventa.Tests.ValueObjects;

public class ProductCodeTests
{
    [Fact]
    public void Create_ValidCode_Success()
    {
        // Act
        var code = ProductCode.Create("ABC-123");

        // Assert
        Assert.Equal("ABC-123", code.Value);
    }

    [Fact]
    public void Create_LowercaseCode_NormalizedToUppercase()
    {
        // Act
        var code = ProductCode.Create("abc-123");

        // Assert
        Assert.Equal("ABC-123", code.Value);
    }

    [Fact]
    public void Create_EmptyCode_ThrowsException()
    {
        // Act & Assert
        Assert.Throws<ValidationException>(() => ProductCode.Create(""));
    }

    [Fact]
    public void Create_InvalidCharacters_ThrowsException()
    {
        // Act & Assert
        Assert.Throws<ValidationException>(() => ProductCode.Create("ABC@123"));
    }

    [Fact]
    public void Create_TooLong_ThrowsException()
    {
        // Arrange
        var longCode = new string('A', 51);

        // Act & Assert
        Assert.Throws<ValidationException>(() => ProductCode.Create(longCode));
    }

    [Fact]
    public void Prefix_CodeWithHyphen_ExtractsPrefix()
    {
        // Arrange
        var code = ProductCode.Create("CAT-123-456");

        // Act
        var prefix = code.Prefix;

        // Assert
        Assert.Equal("CAT", prefix);
    }

    [Fact]
    public void Prefix_CodeWithoutHyphen_ReturnsNull()
    {
        // Arrange
        var code = ProductCode.Create("ABC123");

        // Act
        var prefix = code.Prefix;

        // Assert
        Assert.Null(prefix);
    }

    [Fact]
    public void Suffix_CodeWithHyphen_ExtractsSuffix()
    {
        // Arrange
        var code = ProductCode.Create("CAT-123-456");

        // Act
        var suffix = code.Suffix;

        // Assert
        Assert.Equal("456", suffix);
    }

    [Fact]
    public void Suffix_CodeWithoutHyphen_ReturnsNull()
    {
        // Arrange
        var code = ProductCode.Create("ABC123");

        // Act
        var suffix = code.Suffix;

        // Assert
        Assert.Null(suffix);
    }

    [Fact]
    public void HasPrefix_MatchingPrefix_ReturnsTrue()
    {
        // Arrange
        var code = ProductCode.Create("CAT-123");

        // Act & Assert
        Assert.True(code.HasPrefix("CAT"));
        Assert.True(code.HasPrefix("cat")); // Case insensitive
    }

    [Fact]
    public void HasPrefix_NonMatchingPrefix_ReturnsFalse()
    {
        // Arrange
        var code = ProductCode.Create("CAT-123");

        // Act & Assert
        Assert.False(code.HasPrefix("DOG"));
    }

    [Fact]
    public void GenerateSku_ValidInputs_Success()
    {
        // Act
        var sku = ProductCode.GenerateSku("WIDGET", 42);

        // Assert
        Assert.Equal("WIDGET-000042", sku.Value);
    }

    [Fact]
    public void GenerateSku_EmptyCategory_ThrowsException()
    {
        // Act & Assert
        Assert.Throws<ArgumentException>(() => ProductCode.GenerateSku("", 123));
    }

    [Fact]
    public void GenerateSku_NegativeNumber_ThrowsException()
    {
        // Act & Assert
        Assert.Throws<ArgumentException>(() => ProductCode.GenerateSku("CAT", -1));
    }

    [Fact]
    public void ImplicitConversion_ToStringWorks()
    {
        // Arrange
        var code = ProductCode.Create("ABC-123");

        // Act
        string codeString = code;

        // Assert
        Assert.Equal("ABC-123", codeString);
    }

    [Fact]
    public void ToString_ReturnsValue()
    {
        // Arrange
        var code = ProductCode.Create("ABC-123");

        // Act
        var result = code.ToString();

        // Assert
        Assert.Equal("ABC-123", result);
    }

    [Fact]
    public void Equality_SameCodes_ReturnsTrue()
    {
        // Arrange
        var code1 = ProductCode.Create("ABC-123");
        var code2 = ProductCode.Create("abc-123"); // Will be normalized

        // Act & Assert
        Assert.Equal(code1, code2);
    }
}
