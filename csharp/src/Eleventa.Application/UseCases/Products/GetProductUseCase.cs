using Eleventa.Application.DTOs;
using Eleventa.Application.Interfaces;

namespace Eleventa.Application.UseCases.Products;

/// <summary>
/// Use case for retrieving a product.
/// </summary>
public class GetProductUseCase
{
    private readonly IProductService _productService;

    /// <summary>
    /// Initializes a new instance of the <see cref="GetProductUseCase"/> class.
    /// </summary>
    /// <param name="productService">Product service.</param>
    public GetProductUseCase(IProductService productService)
    {
        _productService = productService ?? throw new ArgumentNullException(nameof(productService));
    }

    /// <summary>
    /// Executes the use case to get a product by ID.
    /// </summary>
    /// <param name="id">Product ID.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The product DTO, or null if not found.</returns>
    public async Task<ProductDto?> ExecuteByIdAsync(int id, CancellationToken cancellationToken = default)
    {
        if (id <= 0)
            throw new ArgumentException("Product ID must be greater than 0.", nameof(id));

        return await _productService.GetProductByIdAsync(id, cancellationToken);
    }

    /// <summary>
    /// Executes the use case to get a product by code.
    /// </summary>
    /// <param name="code">Product code.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The product DTO, or null if not found.</returns>
    public async Task<ProductDto?> ExecuteByCodeAsync(string code, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(code))
            throw new ArgumentException("Product code cannot be empty.", nameof(code));

        return await _productService.GetProductByCodeAsync(code, cancellationToken);
    }

    /// <summary>
    /// Executes the use case to get a product by barcode.
    /// </summary>
    /// <param name="barcode">Product barcode.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The product DTO, or null if not found.</returns>
    public async Task<ProductDto?> ExecuteByBarcodeAsync(string barcode, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(barcode))
            throw new ArgumentException("Product barcode cannot be empty.", nameof(barcode));

        return await _productService.GetProductByBarcodeAsync(barcode, cancellationToken);
    }
}
