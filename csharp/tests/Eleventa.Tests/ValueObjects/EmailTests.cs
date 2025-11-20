using Eleventa.Domain.ValueObjects;
using Xunit;

namespace Eleventa.Tests.ValueObjects;

public class EmailTests
{
    [Fact]
    public void Create_ValidEmail_Success()
    {
        // Act
        var email = Email.Create("test@example.com");

        // Assert
        Assert.Equal("test@example.com", email.Value);
    }

    [Fact]
    public void Create_UppercaseEmail_NormalizedToLowercase()
    {
        // Act
        var email = Email.Create("TEST@EXAMPLE.COM");

        // Assert
        Assert.Equal("test@example.com", email.Value);
    }

    [Fact]
    public void Create_EmptyEmail_ThrowsException()
    {
        // Act & Assert
        Assert.Throws<ValidationException>(() => Email.Create(""));
    }

    [Fact]
    public void Create_InvalidFormat_ThrowsException()
    {
        // Act & Assert
        Assert.Throws<ValidationException>(() => Email.Create("invalid-email"));
    }

    [Fact]
    public void Create_TooLong_ThrowsException()
    {
        // Arrange
        var longEmail = new string('a', 250) + "@test.com";

        // Act & Assert
        Assert.Throws<ValidationException>(() => Email.Create(longEmail));
    }

    [Fact]
    public void Domain_ValidEmail_ExtractsDomain()
    {
        // Arrange
        var email = Email.Create("john@example.com");

        // Act
        var domain = email.Domain;

        // Assert
        Assert.Equal("example.com", domain);
    }

    [Fact]
    public void LocalPart_ValidEmail_ExtractsLocalPart()
    {
        // Arrange
        var email = Email.Create("john.doe@example.com");

        // Act
        var localPart = email.LocalPart;

        // Assert
        Assert.Equal("john.doe", localPart);
    }

    [Fact]
    public void IsFromDomain_SameDomain_ReturnsTrue()
    {
        // Arrange
        var email = Email.Create("test@example.com");

        // Act & Assert
        Assert.True(email.IsFromDomain("example.com"));
    }

    [Fact]
    public void IsFromDomain_DifferentDomain_ReturnsFalse()
    {
        // Arrange
        var email = Email.Create("test@example.com");

        // Act & Assert
        Assert.False(email.IsFromDomain("other.com"));
    }

    [Fact]
    public void Obfuscate_ValidEmail_ObfuscatesCorrectly()
    {
        // Arrange
        var email = Email.Create("john@example.com");

        // Act
        var obfuscated = email.Obfuscate();

        // Assert
        Assert.Equal("j***n@example.com", obfuscated);
    }

    [Fact]
    public void Obfuscate_ShortEmail_ObfuscatesCorrectly()
    {
        // Arrange
        var email = Email.Create("ab@example.com");

        // Act
        var obfuscated = email.Obfuscate();

        // Assert
        Assert.Equal("*@example.com", obfuscated);
    }

    [Fact]
    public void Equality_SameEmail_ReturnsTrue()
    {
        // Arrange
        var email1 = Email.Create("test@example.com");
        var email2 = Email.Create("test@example.com");

        // Act & Assert
        Assert.Equal(email1, email2);
    }

    [Fact]
    public void ImplicitConversion_ToStringWorks()
    {
        // Arrange
        var email = Email.Create("test@example.com");

        // Act
        string emailString = email;

        // Assert
        Assert.Equal("test@example.com", emailString);
    }
}
