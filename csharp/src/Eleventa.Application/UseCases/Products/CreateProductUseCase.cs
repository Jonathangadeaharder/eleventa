using Eleventa.Application.DTOs;
using Eleventa.Application.Interfaces;

namespace Eleventa.Application.UseCases.Products;

/// <summary>
/// Use case for creating a new product.
/// </summary>
public class CreateProductUseCase
{
    private readonly IProductService _productService;

    /// <summary>
    /// Initializes a new instance of the <see cref="CreateProductUseCase"/> class.
    /// </summary>
    /// <param name="productService">Product service.</param>
    public CreateProductUseCase(IProductService productService)
    {
        _productService = productService ?? throw new ArgumentNullException(nameof(productService));
    }

    /// <summary>
    /// Executes the use case to create a new product.
    /// </summary>
    /// <param name="createProductDto">Product creation data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The created product DTO.</returns>
    /// <exception cref="ArgumentNullException">Thrown when createProductDto is null.</exception>
    /// <exception cref="InvalidOperationException">Thrown when product code already exists.</exception>
    public async Task<ProductDto> ExecuteAsync(CreateProductDto createProductDto, CancellationToken cancellationToken = default)
    {
        if (createProductDto == null)
            throw new ArgumentNullException(nameof(createProductDto));

        // Validate product code is unique
        if (await _productService.ProductCodeExistsAsync(createProductDto.Code, null, cancellationToken))
        {
            throw new InvalidOperationException($"Product with code '{createProductDto.Code}' already exists.");
        }

        // Create the product
        var result = await _productService.CreateProductAsync(createProductDto, cancellationToken);

        return result;
    }
}
