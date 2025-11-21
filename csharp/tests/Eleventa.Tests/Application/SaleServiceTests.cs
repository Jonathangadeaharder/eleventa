using Eleventa.Application.Services;
using Eleventa.Domain.Entities;
using Eleventa.Infrastructure.Repositories;
using Eleventa.Tests.Helpers;

namespace Eleventa.Tests.Application;

/// <summary>
/// Unit tests for SaleService.
/// </summary>
public class SaleServiceTests : IDisposable
{
    private readonly SaleService _service;
    private readonly SaleRepository _repository;
    private readonly Infrastructure.Persistence.EleventaDbContext _context;

    public SaleServiceTests()
    {
        _context = TestDbContextFactory.CreateInMemoryDbContextWithData();
        _repository = new SaleRepository(_context);
        _service = new SaleService(_repository);
    }

    [Fact]
    public async Task GetSaleByIdAsync_WhenSaleExists_ReturnsSale()
    {
        // Arrange
        const int saleId = 1;

        // Act
        var result = await _service.GetSaleByIdAsync(saleId);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(saleId, result.Id);
    }

    [Fact]
    public async Task GetSaleWithItemsAsync_WhenSaleExists_ReturnsSaleWithItems()
    {
        // Arrange
        const int saleId = 1;

        // Act
        var result = await _service.GetSaleWithItemsAsync(saleId);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(saleId, result.Id);
        Assert.NotNull(result.Items);
        Assert.NotEmpty(result.Items);
    }

    [Fact]
    public async Task GetAllSalesAsync_ReturnsAllSales()
    {
        // Act
        var results = await _service.GetAllSalesAsync();
        var saleList = results.ToList();

        // Assert
        Assert.NotEmpty(saleList);
    }

    [Fact]
    public async Task GetSalesByDateRangeAsync_ReturnsSalesInRange()
    {
        // Arrange
        var startDate = DateTime.UtcNow.AddDays(-2);
        var endDate = DateTime.UtcNow;

        // Act
        var results = await _service.GetSalesByDateRangeAsync(startDate, endDate);
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
    public async Task CreateSaleAsync_WithValidSale_CreatesSale()
    {
        // Arrange
        var newSale = new Sale
        {
            CustomerId = 1,
            UserId = 1
        };

        // Act
        var result = await _service.CreateSaleAsync(newSale);

        // Assert
        Assert.NotNull(result);
        Assert.True(result.Id > 0);
        Assert.Equal("pending", result.Status);
        Assert.True(result.CreatedAt > DateTime.MinValue);
        Assert.True(result.Timestamp > DateTime.MinValue);
    }

    [Fact]
    public async Task CreateSaleAsync_WithNullSale_ThrowsArgumentNullException()
    {
        // Act & Assert
        await Assert.ThrowsAsync<ArgumentNullException>(() =>
            _service.CreateSaleAsync(null!));
    }

    [Fact]
    public async Task CompleteSaleAsync_WithPendingSale_CompletesSale()
    {
        // Arrange
        var sale = new Sale
        {
            CustomerId = 1,
            UserId = 1
        };
        var createdSale = await _service.CreateSaleAsync(sale);

        // Act
        await _service.CompleteSaleAsync(createdSale.Id);

        // Assert
        var completedSale = await _service.GetSaleByIdAsync(createdSale.Id);
        Assert.NotNull(completedSale);
        Assert.Equal("completed", completedSale.Status);
    }

    [Fact]
    public async Task CompleteSaleAsync_WithNonExistentSale_ThrowsInvalidOperationException()
    {
        // Arrange
        const int nonExistentId = 9999;

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(() =>
            _service.CompleteSaleAsync(nonExistentId));
    }

    [Fact]
    public async Task CompleteSaleAsync_WithAlreadyCompletedSale_ThrowsInvalidOperationException()
    {
        // Arrange
        const int saleId = 1;
        var sale = await _service.GetSaleByIdAsync(saleId);
        Assert.NotNull(sale);

        if (sale.Status != "completed")
        {
            await _service.CompleteSaleAsync(saleId);
        }

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(() =>
            _service.CompleteSaleAsync(saleId));
    }

    [Fact]
    public async Task CancelSaleAsync_WithPendingSale_CancelsSale()
    {
        // Arrange
        var sale = new Sale
        {
            CustomerId = 1,
            UserId = 1
        };
        var createdSale = await _service.CreateSaleAsync(sale);

        // Act
        await _service.CancelSaleAsync(createdSale.Id);

        // Assert
        var cancelledSale = await _service.GetSaleByIdAsync(createdSale.Id);
        Assert.NotNull(cancelledSale);
        Assert.Equal("cancelled", cancelledSale.Status);
    }

    [Fact]
    public async Task CancelSaleAsync_WithNonExistentSale_ThrowsInvalidOperationException()
    {
        // Arrange
        const int nonExistentId = 9999;

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(() =>
            _service.CancelSaleAsync(nonExistentId));
    }

    [Fact]
    public async Task CancelSaleAsync_WithCompletedSale_ThrowsInvalidOperationException()
    {
        // Arrange
        var sale = new Sale
        {
            CustomerId = 1,
            UserId = 1
        };
        var createdSale = await _service.CreateSaleAsync(sale);
        await _service.CompleteSaleAsync(createdSale.Id);

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(() =>
            _service.CancelSaleAsync(createdSale.Id));
    }

    [Fact]
    public async Task CalculateSaleTotalAsync_WithItems_ReturnsCorrectTotal()
    {
        // Arrange
        const int saleId = 1;

        // Act
        var total = await _service.CalculateSaleTotalAsync(saleId);

        // Assert
        // Sale 1 has: 1 Laptop (800) + 2 Mice (20 each) = 840
        Assert.Equal(840.00m, total);
    }

    [Fact]
    public async Task CalculateSaleTotalAsync_WithNonExistentSale_ThrowsInvalidOperationException()
    {
        // Arrange
        const int nonExistentId = 9999;

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(() =>
            _service.CalculateSaleTotalAsync(nonExistentId));
    }

    public void Dispose()
    {
        _context?.Dispose();
        GC.SuppressFinalize(this);
    }
}
