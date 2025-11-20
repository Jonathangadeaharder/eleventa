using Eleventa.Application.Services;
using Eleventa.Domain.Entities;
using Eleventa.Infrastructure.Repositories;
using Eleventa.Tests.Helpers;

namespace Eleventa.Tests.Application;

/// <summary>
/// Unit tests for ProductService.
/// </summary>
public class ProductServiceTests : IDisposable
{
    private readonly ProductService _service;
    private readonly ProductRepository _repository;
    private readonly Infrastructure.Persistence.EleventaDbContext _context;

    public ProductServiceTests()
    {
        _context = TestDbContextFactory.CreateInMemoryDbContextWithData();
        _repository = new ProductRepository(_context);
        _service = new ProductService(_repository);
    }

    [Fact]
    public async Task GetProductByIdAsync_WhenProductExists_ReturnsProduct()
    {
        // Arrange
        const int productId = 1;

        // Act
        var result = await _service.GetProductByIdAsync(productId);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(productId, result.Id);
        Assert.Equal("Laptop Computer", result.Description);
    }

    [Fact]
    public async Task GetProductByCodeAsync_WithValidCode_ReturnsProduct()
    {
        // Arrange
        const string productCode = "PROD001";

        // Act
        var result = await _service.GetProductByCodeAsync(productCode);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(productCode, result.Code);
    }

    [Fact]
    public async Task GetProductByCodeAsync_WithEmptyCode_ThrowsArgumentException()
    {
        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(() =>
            _service.GetProductByCodeAsync(string.Empty));
    }

    [Fact]
    public async Task GetAllProductsAsync_ReturnsAllActiveProducts()
    {
        // Act
        var results = await _service.GetAllProductsAsync();
        var productList = results.ToList();

        // Assert
        Assert.NotEmpty(productList);
        Assert.Equal(3, productList.Count);
    }

    [Fact]
    public async Task GetLowStockProductsAsync_ReturnsProductsBelowMinStock()
    {
        // Act
        var results = await _service.GetLowStockProductsAsync();
        var productList = results.ToList();

        // Assert
        Assert.Single(productList);
        Assert.Equal("PROD003", productList[0].Code);
    }

    [Fact]
    public async Task CreateProductAsync_WithValidProduct_CreatesProduct()
    {
        // Arrange
        var newProduct = new Product
        {
            Code = "NEWPROD",
            Description = "New Test Product",
            CostPrice = 50.00m,
            SellPrice = 100.00m,
            QuantityInStock = 10.000m,
            MinStock = 5.000m,
            MaxStock = 100.000m,
            Unit = "Unit",
            DepartmentId = 1
        };

        // Act
        var result = await _service.CreateProductAsync(newProduct);

        // Assert
        Assert.NotNull(result);
        Assert.True(result.Id > 0);
        Assert.Equal("NEWPROD", result.Code);
        Assert.True(result.IsActive);
        Assert.True(result.CreatedAt > DateTime.MinValue);
    }

    [Fact]
    public async Task CreateProductAsync_WithDuplicateCode_ThrowsInvalidOperationException()
    {
        // Arrange
        var duplicateProduct = new Product
        {
            Code = "PROD001", // Existing code
            Description = "Duplicate Product",
            CostPrice = 50.00m,
            SellPrice = 100.00m,
            QuantityInStock = 10.000m,
            MinStock = 5.000m,
            MaxStock = 100.000m,
            Unit = "Unit",
            DepartmentId = 1
        };

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(() =>
            _service.CreateProductAsync(duplicateProduct));
    }

    [Fact]
    public async Task CreateProductAsync_WithNullProduct_ThrowsArgumentNullException()
    {
        // Act & Assert
        await Assert.ThrowsAsync<ArgumentNullException>(() =>
            _service.CreateProductAsync(null!));
    }

    [Fact]
    public async Task UpdateProductAsync_WithValidProduct_UpdatesProduct()
    {
        // Arrange
        var product = await _service.GetProductByIdAsync(1);
        Assert.NotNull(product);

        product.Description = "Updated Description";

        // Act
        var result = await _service.UpdateProductAsync(product);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("Updated Description", result.Description);

        var updatedProduct = await _service.GetProductByIdAsync(1);
        Assert.Equal("Updated Description", updatedProduct!.Description);
    }

    [Fact]
    public async Task UpdateProductAsync_WithNonExistentProduct_ThrowsInvalidOperationException()
    {
        // Arrange
        var nonExistentProduct = new Product
        {
            Id = 9999,
            Code = "NONEXISTENT",
            Description = "Non-existent Product",
            CostPrice = 50.00m,
            SellPrice = 100.00m,
            QuantityInStock = 10.000m,
            MinStock = 5.000m,
            MaxStock = 100.000m,
            Unit = "Unit",
            DepartmentId = 1
        };

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(() =>
            _service.UpdateProductAsync(nonExistentProduct));
    }

    [Fact]
    public async Task DeleteProductAsync_WithValidId_DeletesProduct()
    {
        // Arrange
        const int productId = 2;

        // Act
        await _service.DeleteProductAsync(productId);

        // Assert
        var deletedProduct = await _service.GetProductByIdAsync(productId);
        Assert.Null(deletedProduct);
    }

    [Fact]
    public async Task DeleteProductAsync_WithNonExistentId_ThrowsInvalidOperationException()
    {
        // Arrange
        const int nonExistentId = 9999;

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(() =>
            _service.DeleteProductAsync(nonExistentId));
    }

    [Fact]
    public async Task AdjustStockAsync_IncreasesStock()
    {
        // Arrange
        const int productId = 1;
        var product = await _service.GetProductByIdAsync(productId);
        var initialStock = product!.QuantityInStock;
        const decimal adjustment = 10.000m;

        // Act
        await _service.AdjustStockAsync(productId, adjustment, "Test adjustment");

        // Assert
        var updatedProduct = await _service.GetProductByIdAsync(productId);
        Assert.Equal(initialStock + adjustment, updatedProduct!.QuantityInStock);
    }

    [Fact]
    public async Task AdjustStockAsync_DecreasesStock()
    {
        // Arrange
        const int productId = 1;
        var product = await _service.GetProductByIdAsync(productId);
        var initialStock = product!.QuantityInStock;
        const decimal adjustment = -5.000m;

        // Act
        await _service.AdjustStockAsync(productId, adjustment, "Test reduction");

        // Assert
        var updatedProduct = await _service.GetProductByIdAsync(productId);
        Assert.Equal(initialStock + adjustment, updatedProduct!.QuantityInStock);
    }

    [Fact]
    public async Task AdjustStockAsync_WithNonExistentProduct_ThrowsInvalidOperationException()
    {
        // Arrange
        const int nonExistentId = 9999;

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(() =>
            _service.AdjustStockAsync(nonExistentId, 10.000m, "Test"));
    }

    public void Dispose()
    {
        _context?.Dispose();
        GC.SuppressFinalize(this);
    }
}
