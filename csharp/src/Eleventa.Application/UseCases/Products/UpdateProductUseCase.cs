using Eleventa.Application.DTOs;
using Eleventa.Application.Interfaces;

namespace Eleventa.Application.UseCases.Products;

/// <summary>
/// Use case for updating an existing product.
/// </summary>
public class UpdateProductUseCase
{
    private readonly IProductService _productService;

    /// <summary>
    /// Initializes a new instance of the <see cref="UpdateProductUseCase"/> class.
    /// </summary>
    /// <param name="productService">Product service.</param>
    public UpdateProductUseCase(IProductService productService)
    {
        _productService = productService ?? throw new ArgumentNullException(nameof(productService));
    }

    /// <summary>
    /// Executes the use case to update an existing product.
    /// </summary>
    /// <param name="updateProductDto">Product update data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The updated product DTO.</returns>
    /// <exception cref="ArgumentNullException">Thrown when updateProductDto is null.</exception>
    /// <exception cref="InvalidOperationException">Thrown when product is not found or code already exists.</exception>
    public async Task<ProductDto> ExecuteAsync(UpdateProductDto updateProductDto, CancellationToken cancellationToken = default)
    {
        if (updateProductDto == null)
            throw new ArgumentNullException(nameof(updateProductDto));

        // Verify product exists
        var existingProduct = await _productService.GetProductByIdAsync(updateProductDto.Id, cancellationToken);
        if (existingProduct == null)
        {
            throw new InvalidOperationException($"Product with ID {updateProductDto.Id} not found.");
        }

        // If code is being updated, validate it's unique
        if (!string.IsNullOrWhiteSpace(updateProductDto.Code) &&
            updateProductDto.Code != existingProduct.Code)
        {
            if (await _productService.ProductCodeExistsAsync(updateProductDto.Code, updateProductDto.Id, cancellationToken))
            {
                throw new InvalidOperationException($"Product with code '{updateProductDto.Code}' already exists.");
            }
        }

        // Update the product
        var result = await _productService.UpdateProductAsync(updateProductDto, cancellationToken);

        return result;
    }
}
