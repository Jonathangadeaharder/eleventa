using Eleventa.Domain.Entities;
using Eleventa.Infrastructure.Repositories;

namespace Eleventa.Tests.Integration;

/// <summary>
/// Integration tests for ProductRepository.
/// </summary>
public class ProductRepositoryTests : IntegrationTestBase
{
    private readonly ProductRepository _repository;

    public ProductRepositoryTests() : base(seedData: true)
    {
        _repository = new ProductRepository(_context);
    }

    [Fact]
    public async Task GetByIdAsync_WhenProductExists_ReturnsProduct()
    {
        // Arrange
        const int productId = 1;

        // Act
        var result = await _repository.GetByIdAsync(productId);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(productId, result.Id);
        Assert.Equal("PROD001", result.Code);
        Assert.Equal("Laptop Computer", result.Description);
    }

    [Fact]
    public async Task GetByIdAsync_WhenProductDoesNotExist_ReturnsNull()
    {
        // Arrange
        const int nonExistentId = 999;

        // Act
        var result = await _repository.GetByIdAsync(nonExistentId);

        // Assert
        Assert.Null(result);
    }

    [Fact]
    public async Task GetByCodeAsync_WhenProductExists_ReturnsProduct()
    {
        // Arrange
        const string productCode = "PROD001";

        // Act
        var result = await _repository.GetByCodeAsync(productCode);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(productCode, result.Code);
        Assert.Equal("Laptop Computer", result.Description);
    }

    [Fact]
    public async Task GetByBarcodeAsync_WhenProductExists_ReturnsProduct()
    {
        // Arrange
        const string barcode = "1234567890123";

        // Act
        var result = await _repository.GetByBarcodeAsync(barcode);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(barcode, result.Barcode);
        Assert.Equal("PROD001", result.Code);
    }

    [Fact]
    public async Task GetAllAsync_ReturnsAllActiveProducts()
    {
        // Act
        var results = await _repository.GetAllAsync();
        var productList = results.ToList();

        // Assert
        Assert.NotEmpty(productList);
        Assert.Equal(3, productList.Count);
        Assert.All(productList, p => Assert.True(p.IsActive));
    }

    [Fact]
    public async Task GetByDepartmentAsync_ReturnsProductsInDepartment()
    {
        // Arrange
        const int departmentId = 1; // Electronics

        // Act
        var results = await _repository.GetByDepartmentAsync(departmentId);
        var productList = results.ToList();

        // Assert
        Assert.NotEmpty(productList);
        Assert.Equal(2, productList.Count);
        Assert.All(productList, p => Assert.Equal(departmentId, p.DepartmentId));
    }

    [Fact]
    public async Task SearchByDescriptionAsync_ReturnsMatchingProducts()
    {
        // Arrange
        const string searchTerm = "Mouse";

        // Act
        var results = await _repository.SearchByDescriptionAsync(searchTerm);
        var productList = results.ToList();

        // Assert
        Assert.Single(productList);
        Assert.Contains("Mouse", productList[0].Description);
    }

    [Fact]
    public async Task GetLowStockProductsAsync_ReturnsProductsBelowMinStock()
    {
        // Act
        var results = await _repository.GetLowStockProductsAsync();
        var productList = results.ToList();

        // Assert
        Assert.Single(productList);
        Assert.Equal("PROD003", productList[0].Code); // Milk has low stock
        Assert.True(productList[0].QuantityInStock <= productList[0].MinStock);
    }

    [Fact]
    public async Task AddAsync_AddsNewProduct()
    {
        // Arrange
        var newProduct = new Product
        {
            Code = "PROD999",
            Description = "Test Product",
            CostPrice = 10.00m,
            SellPrice = 15.00m,
            QuantityInStock = 100.000m,
            MinStock = 10.000m,
            MaxStock = 500.000m,
            Unit = "Unit",
            DepartmentId = 1,
            IsActive = true,
            CreatedAt = DateTime.UtcNow
        };

        // Act
        await _repository.AddAsync(newProduct);
        await _repository.SaveChangesAsync();

        // Assert
        var savedProduct = await _repository.GetByCodeAsync("PROD999");
        Assert.NotNull(savedProduct);
        Assert.Equal("Test Product", savedProduct.Description);
    }

    [Fact]
    public async Task UpdateAsync_UpdatesExistingProduct()
    {
        // Arrange
        var product = await _repository.GetByIdAsync(1);
        Assert.NotNull(product);

        const string updatedDescription = "Updated Laptop Computer";
        product.Description = updatedDescription;

        // Act
        await _repository.UpdateAsync(product);
        await _repository.SaveChangesAsync();

        // Assert
        var updatedProduct = await _repository.GetByIdAsync(1);
        Assert.NotNull(updatedProduct);
        Assert.Equal(updatedDescription, updatedProduct.Description);
    }

    [Fact]
    public async Task DeleteAsync_RemovesProduct()
    {
        // Arrange
        const int productId = 2;

        // Act
        await _repository.DeleteAsync(productId);
        await _repository.SaveChangesAsync();

        // Assert
        var deletedProduct = await _repository.GetByIdAsync(productId);
        Assert.Null(deletedProduct);
    }

    [Fact]
    public async Task ExistsByCodeAsync_WhenProductExists_ReturnsTrue()
    {
        // Arrange
        const string existingCode = "PROD001";

        // Act
        var result = await _repository.ExistsByCodeAsync(existingCode);

        // Assert
        Assert.True(result);
    }

    [Fact]
    public async Task ExistsByCodeAsync_WhenProductDoesNotExist_ReturnsFalse()
    {
        // Arrange
        const string nonExistentCode = "NONEXISTENT";

        // Act
        var result = await _repository.ExistsByCodeAsync(nonExistentCode);

        // Assert
        Assert.False(result);
    }
}
