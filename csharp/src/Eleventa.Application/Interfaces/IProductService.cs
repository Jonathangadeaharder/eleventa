using Eleventa.Application.DTOs;

namespace Eleventa.Application.Interfaces;

/// <summary>
/// Interface for product service operations.
/// </summary>
public interface IProductService
{
    /// <summary>
    /// Creates a new product.
    /// </summary>
    /// <param name="createProductDto">Product creation data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The created product DTO.</returns>
    Task<ProductDto> CreateProductAsync(CreateProductDto createProductDto, CancellationToken cancellationToken = default);

    /// <summary>
    /// Updates an existing product.
    /// </summary>
    /// <param name="updateProductDto">Product update data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The updated product DTO.</returns>
    Task<ProductDto> UpdateProductAsync(UpdateProductDto updateProductDto, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets a product by ID.
    /// </summary>
    /// <param name="id">Product ID.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The product DTO, or null if not found.</returns>
    Task<ProductDto?> GetProductByIdAsync(int id, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets a product by code.
    /// </summary>
    /// <param name="code">Product code.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The product DTO, or null if not found.</returns>
    Task<ProductDto?> GetProductByCodeAsync(string code, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets a product by barcode.
    /// </summary>
    /// <param name="barcode">Product barcode.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The product DTO, or null if not found.</returns>
    Task<ProductDto?> GetProductByBarcodeAsync(string barcode, CancellationToken cancellationToken = default);

    /// <summary>
    /// Lists all products.
    /// </summary>
    /// <param name="includeInactive">Whether to include inactive products.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of product DTOs.</returns>
    Task<IEnumerable<ProductDto>> ListProductsAsync(bool includeInactive = false, CancellationToken cancellationToken = default);

    /// <summary>
    /// Lists products that need restock.
    /// </summary>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of product DTOs that need restock.</returns>
    Task<IEnumerable<ProductDto>> ListProductsNeedingRestockAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Deletes a product.
    /// </summary>
    /// <param name="id">Product ID.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>True if deleted successfully, false otherwise.</returns>
    Task<bool> DeleteProductAsync(int id, CancellationToken cancellationToken = default);

    /// <summary>
    /// Checks if a product code already exists.
    /// </summary>
    /// <param name="code">Product code to check.</param>
    /// <param name="excludeId">Product ID to exclude from check (for updates).</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>True if code exists, false otherwise.</returns>
    Task<bool> ProductCodeExistsAsync(string code, int? excludeId = null, CancellationToken cancellationToken = default);
}
