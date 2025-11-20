using Eleventa.Domain.Aggregates;
using Eleventa.Domain.Aggregates.Examples;
using Eleventa.Domain.ValueObjects;
using Xunit;

namespace Eleventa.Tests.Aggregates;

public class CustomerTests
{
    [Fact]
    public void Create_ValidCustomer_Success()
    {
        // Arrange
        var email = Email.Create("john@example.com");

        // Act
        var customer = new Customer(Guid.NewGuid(), email, "John Doe");

        // Assert
        Assert.Equal(email, customer.Email);
        Assert.Equal("John Doe", customer.Name);
        Assert.Empty(customer.Addresses);
    }

    [Fact]
    public void Create_EmptyName_ThrowsException()
    {
        // Arrange
        var email = Email.Create("test@example.com");

        // Act & Assert
        Assert.Throws<DomainException>(() =>
            new Customer(Guid.NewGuid(), email, ""));
    }

    [Fact]
    public void UpdateName_ValidName_UpdatesSuccessfully()
    {
        // Arrange
        var email = Email.Create("john@example.com");
        var customer = new Customer(Guid.NewGuid(), email, "John Doe");

        // Act
        customer.UpdateName("Jane Doe");

        // Assert
        Assert.Equal("Jane Doe", customer.Name);
    }

    [Fact]
    public void UpdateName_EmptyName_ThrowsException()
    {
        // Arrange
        var email = Email.Create("john@example.com");
        var customer = new Customer(Guid.NewGuid(), email, "John Doe");

        // Act & Assert
        Assert.Throws<DomainException>(() => customer.UpdateName(""));
    }

    [Fact]
    public void UpdateEmail_ValidEmail_UpdatesSuccessfully()
    {
        // Arrange
        var email = Email.Create("john@example.com");
        var customer = new Customer(Guid.NewGuid(), email, "John Doe");
        var newEmail = Email.Create("jane@example.com");

        // Act
        customer.UpdateEmail(newEmail);

        // Assert
        Assert.Equal(newEmail, customer.Email);
    }

    [Fact]
    public void AddAddress_NewAddress_AddsToCollection()
    {
        // Arrange
        var email = Email.Create("john@example.com");
        var customer = new Customer(Guid.NewGuid(), email, "John Doe");
        var address = Address.Create("123 Main St", "Springfield", "62701", "USA");

        // Act
        customer.AddAddress(address);

        // Assert
        Assert.Single(customer.Addresses);
        Assert.Contains(address, customer.Addresses);
    }

    [Fact]
    public void AddAddress_DuplicateAddress_DoesNotAddAgain()
    {
        // Arrange
        var email = Email.Create("john@example.com");
        var customer = new Customer(Guid.NewGuid(), email, "John Doe");
        var address = Address.Create("123 Main St", "Springfield", "62701", "USA");

        // Act
        customer.AddAddress(address);
        customer.AddAddress(address); // Try to add same address again

        // Assert
        Assert.Single(customer.Addresses);
    }

    [Fact]
    public void AddAddress_MultipleAddresses_AllAdded()
    {
        // Arrange
        var email = Email.Create("john@example.com");
        var customer = new Customer(Guid.NewGuid(), email, "John Doe");
        var address1 = Address.Create("123 Main St", "Springfield", "62701", "USA");
        var address2 = Address.Create("456 Oak Ave", "Springfield", "62702", "USA");

        // Act
        customer.AddAddress(address1);
        customer.AddAddress(address2);

        // Assert
        Assert.Equal(2, customer.Addresses.Count);
    }

    [Fact]
    public void RemoveAddress_ExistingAddress_RemovesSuccessfully()
    {
        // Arrange
        var email = Email.Create("john@example.com");
        var customer = new Customer(Guid.NewGuid(), email, "John Doe");
        var address = Address.Create("123 Main St", "Springfield", "62701", "USA");
        customer.AddAddress(address);

        // Act
        customer.RemoveAddress(address);

        // Assert
        Assert.Empty(customer.Addresses);
    }

    [Fact]
    public void RemoveAddress_NonExistingAddress_DoesNothing()
    {
        // Arrange
        var email = Email.Create("john@example.com");
        var customer = new Customer(Guid.NewGuid(), email, "John Doe");
        var address1 = Address.Create("123 Main St", "Springfield", "62701", "USA");
        var address2 = Address.Create("456 Oak Ave", "Springfield", "62702", "USA");
        customer.AddAddress(address1);

        // Act
        customer.RemoveAddress(address2);

        // Assert
        Assert.Single(customer.Addresses);
        Assert.Contains(address1, customer.Addresses);
    }

    [Fact]
    public void GetDefaultAddress_WithAddresses_ReturnsFirst()
    {
        // Arrange
        var email = Email.Create("john@example.com");
        var customer = new Customer(Guid.NewGuid(), email, "John Doe");
        var address1 = Address.Create("123 Main St", "Springfield", "62701", "USA");
        var address2 = Address.Create("456 Oak Ave", "Springfield", "62702", "USA");
        customer.AddAddress(address1);
        customer.AddAddress(address2);

        // Act
        var defaultAddress = customer.GetDefaultAddress();

        // Assert
        Assert.Equal(address1, defaultAddress);
    }

    [Fact]
    public void GetDefaultAddress_NoAddresses_ReturnsNull()
    {
        // Arrange
        var email = Email.Create("john@example.com");
        var customer = new Customer(Guid.NewGuid(), email, "John Doe");

        // Act
        var defaultAddress = customer.GetDefaultAddress();

        // Assert
        Assert.Null(defaultAddress);
    }
}
