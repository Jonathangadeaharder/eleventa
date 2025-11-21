using Eleventa.Domain.Entities;
using Eleventa.Infrastructure.Repositories;

namespace Eleventa.Tests.Integration;

/// <summary>
/// Integration tests for SaleRepository.
/// </summary>
public class SaleRepositoryTests : IntegrationTestBase
{
    private readonly SaleRepository _repository;

    public SaleRepositoryTests() : base(seedData: true)
    {
        _repository = new SaleRepository(_context);
    }

    [Fact]
    public async Task GetByIdAsync_WhenSaleExists_ReturnsSale()
    {
        // Arrange
        const int saleId = 1;

        // Act
        var result = await _repository.GetByIdAsync(saleId);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(saleId, result.Id);
        Assert.Equal("completed", result.Status);
    }

    [Fact]
    public async Task GetByIdAsync_WhenSaleDoesNotExist_ReturnsNull()
    {
        // Arrange
        const int nonExistentId = 999;

        // Act
        var result = await _repository.GetByIdAsync(nonExistentId);

        // Assert
        Assert.Null(result);
    }

    [Fact]
    public async Task GetByIdWithItemsAsync_WhenSaleExists_ReturnsSaleWithItems()
    {
        // Arrange
        const int saleId = 1;

        // Act
        var result = await _repository.GetByIdWithItemsAsync(saleId);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(saleId, result.Id);
        Assert.NotNull(result.Items);
        Assert.Equal(2, result.Items.Count);
    }

    [Fact]
    public async Task GetAllAsync_ReturnsAllSales()
    {
        // Act
        var results = await _repository.GetAllAsync();
        var saleList = results.ToList();

        // Assert
        Assert.NotEmpty(saleList);
        Assert.Single(saleList);
    }

    [Fact]
    public async Task GetByCustomerAsync_ReturnsSalesForCustomer()
    {
        // Arrange
        const int customerId = 1;

        // Act
        var results = await _repository.GetByCustomerAsync(customerId);
        var saleList = results.ToList();

        // Assert
        Assert.NotEmpty(saleList);
        Assert.All(saleList, s => Assert.Equal(customerId, s.CustomerId));
    }

    [Fact]
    public async Task GetByDateRangeAsync_ReturnsSalesInDateRange()
    {
        // Arrange
        var startDate = DateTime.UtcNow.AddDays(-2);
        var endDate = DateTime.UtcNow;

        // Act
        var results = await _repository.GetByDateRangeAsync(startDate, endDate);
        var saleList = results.ToList();

        // Assert
        Assert.NotEmpty(saleList);
        Assert.All(saleList, s =>
        {
            Assert.True(s.Timestamp >= startDate);
            Assert.True(s.Timestamp <= endDate);
        });
    }

    [Fact]
    public async Task GetByStatusAsync_ReturnsSalesWithStatus()
    {
        // Arrange
        const string status = "completed";

        // Act
        var results = await _repository.GetByStatusAsync(status);
        var saleList = results.ToList();

        // Assert
        Assert.NotEmpty(saleList);
        Assert.All(saleList, s => Assert.Equal(status, s.Status));
    }

    [Fact]
    public async Task GetByUserAsync_ReturnsSalesForUser()
    {
        // Arrange
        const int userId = 1;

        // Act
        var results = await _repository.GetByUserAsync(userId);
        var saleList = results.ToList();

        // Assert
        Assert.NotEmpty(saleList);
        Assert.All(saleList, s => Assert.Equal(userId, s.UserId));
    }

    [Fact]
    public async Task AddAsync_AddsNewSale()
    {
        // Arrange
        var newSale = new Sale
        {
            Timestamp = DateTime.UtcNow,
            CustomerId = 1,
            UserId = 1,
            Status = "pending",
            CreatedAt = DateTime.UtcNow
        };

        // Act
        await _repository.AddAsync(newSale);
        await _repository.SaveChangesAsync();

        // Assert
        var savedSale = await _repository.GetByIdAsync(newSale.Id);
        Assert.NotNull(savedSale);
        Assert.Equal("pending", savedSale.Status);
    }

    [Fact]
    public async Task UpdateAsync_UpdatesExistingSale()
    {
        // Arrange
        var sale = await _repository.GetByIdAsync(1);
        Assert.NotNull(sale);

        const string updatedStatus = "cancelled";
        sale.Status = updatedStatus;

        // Act
        await _repository.UpdateAsync(sale);
        await _repository.SaveChangesAsync();

        // Assert
        var updatedSale = await _repository.GetByIdAsync(1);
        Assert.NotNull(updatedSale);
        Assert.Equal(updatedStatus, updatedSale.Status);
    }

    [Fact]
    public async Task DeleteAsync_RemovesSale()
    {
        // Arrange
        const int saleId = 1;

        // Act
        await _repository.DeleteAsync(saleId);
        await _repository.SaveChangesAsync();

        // Assert
        var deletedSale = await _repository.GetByIdAsync(saleId);
        Assert.Null(deletedSale);
    }
}
