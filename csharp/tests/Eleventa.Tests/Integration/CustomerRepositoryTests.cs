using Eleventa.Domain.Entities;
using Eleventa.Infrastructure.Repositories;

namespace Eleventa.Tests.Integration;

/// <summary>
/// Integration tests for CustomerRepository.
/// </summary>
public class CustomerRepositoryTests : IntegrationTestBase
{
    private readonly CustomerRepository _repository;

    public CustomerRepositoryTests() : base(seedData: true)
    {
        _repository = new CustomerRepository(_context);
    }

    [Fact]
    public async Task GetByIdAsync_WhenCustomerExists_ReturnsCustomer()
    {
        // Arrange
        const int customerId = 1;

        // Act
        var result = await _repository.GetByIdAsync(customerId);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(customerId, result.Id);
        Assert.Equal("John Doe", result.Name);
    }

    [Fact]
    public async Task GetByIdAsync_WhenCustomerDoesNotExist_ReturnsNull()
    {
        // Arrange
        const int nonExistentId = 999;

        // Act
        var result = await _repository.GetByIdAsync(nonExistentId);

        // Assert
        Assert.Null(result);
    }

    [Fact]
    public async Task GetByEmailAsync_WhenCustomerExists_ReturnsCustomer()
    {
        // Arrange
        const string email = "john.doe@email.com";

        // Act
        var result = await _repository.GetByEmailAsync(email);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(email, result.Email);
        Assert.Equal("John Doe", result.Name);
    }

    [Fact]
    public async Task GetByEmailAsync_WhenCustomerDoesNotExist_ReturnsNull()
    {
        // Arrange
        const string nonExistentEmail = "nonexistent@email.com";

        // Act
        var result = await _repository.GetByEmailAsync(nonExistentEmail);

        // Assert
        Assert.Null(result);
    }

    [Fact]
    public async Task GetAllAsync_ReturnsAllActiveCustomers()
    {
        // Act
        var results = await _repository.GetAllAsync();
        var customerList = results.ToList();

        // Assert
        Assert.NotEmpty(customerList);
        Assert.Equal(2, customerList.Count);
        Assert.All(customerList, c => Assert.True(c.IsActive));
    }

    [Fact]
    public async Task SearchByNameAsync_ReturnsMatchingCustomers()
    {
        // Arrange
        const string searchTerm = "John";

        // Act
        var results = await _repository.SearchByNameAsync(searchTerm);
        var customerList = results.ToList();

        // Assert
        Assert.Single(customerList);
        Assert.Contains("John", customerList[0].Name);
    }

    [Fact]
    public async Task GetWithCreditBalanceAsync_ReturnsCustomersWithBalance()
    {
        // Act
        var results = await _repository.GetWithCreditBalanceAsync();
        var customerList = results.ToList();

        // Assert
        Assert.Single(customerList);
        Assert.Equal("Jane Smith", customerList[0].Name);
        Assert.True(customerList[0].CreditBalance > 0);
    }

    [Fact]
    public async Task AddAsync_AddsNewCustomer()
    {
        // Arrange
        var newCustomer = new Customer
        {
            Name = "Test Customer",
            Phone = "555-9999",
            Email = "test@email.com",
            Address = "789 Test St",
            CUIT = "20-11111111-1",
            IVACondition = "Responsable Inscripto",
            CreditLimit = 1000.00m,
            CreditBalance = 0.00m,
            IsActive = true,
            CreatedAt = DateTime.UtcNow
        };

        // Act
        await _repository.AddAsync(newCustomer);
        await _repository.SaveChangesAsync();

        // Assert
        var savedCustomer = await _repository.GetByEmailAsync("test@email.com");
        Assert.NotNull(savedCustomer);
        Assert.Equal("Test Customer", savedCustomer.Name);
    }

    [Fact]
    public async Task UpdateAsync_UpdatesExistingCustomer()
    {
        // Arrange
        var customer = await _repository.GetByIdAsync(1);
        Assert.NotNull(customer);

        const string updatedPhone = "555-0000";
        customer.Phone = updatedPhone;

        // Act
        await _repository.UpdateAsync(customer);
        await _repository.SaveChangesAsync();

        // Assert
        var updatedCustomer = await _repository.GetByIdAsync(1);
        Assert.NotNull(updatedCustomer);
        Assert.Equal(updatedPhone, updatedCustomer.Phone);
    }

    [Fact]
    public async Task DeleteAsync_RemovesCustomer()
    {
        // Arrange
        const int customerId = 2;

        // Act
        await _repository.DeleteAsync(customerId);
        await _repository.SaveChangesAsync();

        // Assert
        var deletedCustomer = await _repository.GetByIdAsync(customerId);
        Assert.Null(deletedCustomer);
    }

    [Fact]
    public async Task ExistsByEmailAsync_WhenCustomerExists_ReturnsTrue()
    {
        // Arrange
        const string existingEmail = "john.doe@email.com";

        // Act
        var result = await _repository.ExistsByEmailAsync(existingEmail);

        // Assert
        Assert.True(result);
    }

    [Fact]
    public async Task ExistsByEmailAsync_WhenCustomerDoesNotExist_ReturnsFalse()
    {
        // Arrange
        const string nonExistentEmail = "nonexistent@email.com";

        // Act
        var result = await _repository.ExistsByEmailAsync(nonExistentEmail);

        // Assert
        Assert.False(result);
    }
}
