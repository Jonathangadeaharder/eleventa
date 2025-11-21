using Eleventa.Application.DTOs;
using Eleventa.Application.Interfaces;

namespace Eleventa.Application.UseCases.Products;

/// <summary>
/// Use case for listing products.
/// </summary>
public class ListProductsUseCase
{
    private readonly IProductService _productService;

    /// <summary>
    /// Initializes a new instance of the <see cref="ListProductsUseCase"/> class.
    /// </summary>
    /// <param name="productService">Product service.</param>
    public ListProductsUseCase(IProductService productService)
    {
        _productService = productService ?? throw new ArgumentNullException(nameof(productService));
    }

    /// <summary>
    /// Executes the use case to list all products.
    /// </summary>
    /// <param name="includeInactive">Whether to include inactive products.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of product DTOs.</returns>
    public async Task<IEnumerable<ProductDto>> ExecuteAsync(bool includeInactive = false, CancellationToken cancellationToken = default)
    {
        return await _productService.ListProductsAsync(includeInactive, cancellationToken);
    }

    /// <summary>
    /// Executes the use case to list products that need restock.
    /// </summary>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of product DTOs that need restock.</returns>
    public async Task<IEnumerable<ProductDto>> ExecuteNeedingRestockAsync(CancellationToken cancellationToken = default)
    {
        return await _productService.ListProductsNeedingRestockAsync(cancellationToken);
    }
}
