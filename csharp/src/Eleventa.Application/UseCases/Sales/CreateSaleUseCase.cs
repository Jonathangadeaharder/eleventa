using Eleventa.Application.DTOs;
using Eleventa.Application.Interfaces;

namespace Eleventa.Application.UseCases.Sales;

/// <summary>
/// Use case for creating a new sale.
/// </summary>
public class CreateSaleUseCase
{
    private readonly ISaleService _saleService;
    private readonly IProductService _productService;
    private readonly IInventoryService _inventoryService;
    private readonly ICustomerService _customerService;

    /// <summary>
    /// Initializes a new instance of the <see cref="CreateSaleUseCase"/> class.
    /// </summary>
    /// <param name="saleService">Sale service.</param>
    /// <param name="productService">Product service.</param>
    /// <param name="inventoryService">Inventory service.</param>
    /// <param name="customerService">Customer service.</param>
    public CreateSaleUseCase(
        ISaleService saleService,
        IProductService productService,
        IInventoryService inventoryService,
        ICustomerService customerService)
    {
        _saleService = saleService ?? throw new ArgumentNullException(nameof(saleService));
        _productService = productService ?? throw new ArgumentNullException(nameof(productService));
        _inventoryService = inventoryService ?? throw new ArgumentNullException(nameof(inventoryService));
        _customerService = customerService ?? throw new ArgumentNullException(nameof(customerService));
    }

    /// <summary>
    /// Executes the use case to create a new sale.
    /// </summary>
    /// <param name="createSaleDto">Sale creation data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The created sale DTO.</returns>
    /// <exception cref="ArgumentNullException">Thrown when createSaleDto is null.</exception>
    /// <exception cref="InvalidOperationException">Thrown when validation fails.</exception>
    public async Task<SaleDto> ExecuteAsync(CreateSaleDto createSaleDto, CancellationToken cancellationToken = default)
    {
        if (createSaleDto == null)
            throw new ArgumentNullException(nameof(createSaleDto));

        if (createSaleDto.Items == null || !createSaleDto.Items.Any())
            throw new InvalidOperationException("Sale must have at least one item.");

        // Validate customer if specified
        if (createSaleDto.CustomerId.HasValue)
        {
            var customer = await _customerService.GetCustomerByIdAsync(createSaleDto.CustomerId.Value, cancellationToken);
            if (customer == null)
            {
                throw new InvalidOperationException($"Customer with ID {createSaleDto.CustomerId.Value} not found.");
            }

            // If credit sale, check customer has available credit
            if (createSaleDto.IsCreditSale)
            {
                var total = 0m;
                foreach (var item in createSaleDto.Items)
                {
                    var product = await _productService.GetProductByIdAsync(item.ProductId, cancellationToken);
                    if (product == null)
                        throw new InvalidOperationException($"Product with ID {item.ProductId} not found.");

                    var price = item.UnitPrice ?? product.SellPrice;
                    total += item.Quantity * price;
                }

                if (!customer.AvailableCredit >= total)
                {
                    throw new InvalidOperationException($"Customer does not have sufficient credit. Available: {customer.AvailableCredit:C}, Required: {total:C}");
                }
            }
        }

        // Validate all products exist and have sufficient inventory
        foreach (var item in createSaleDto.Items)
        {
            var product = await _productService.GetProductByIdAsync(item.ProductId, cancellationToken);
            if (product == null)
            {
                throw new InvalidOperationException($"Product with ID {item.ProductId} not found.");
            }

            if (!product.IsActive)
            {
                throw new InvalidOperationException($"Product '{product.Description}' is not active.");
            }

            // Check inventory if product uses it
            if (product.UsesInventory)
            {
                var hasSufficientInventory = await _inventoryService.HasSufficientInventoryAsync(
                    item.ProductId,
                    item.Quantity,
                    cancellationToken);

                if (!hasSufficientInventory)
                {
                    throw new InvalidOperationException(
                        $"Insufficient inventory for product '{product.Description}'. " +
                        $"Available: {product.QuantityInStock}, Required: {item.Quantity}");
                }
            }
        }

        // Create the sale
        var sale = await _saleService.CreateSaleAsync(createSaleDto, cancellationToken);

        return sale;
    }
}
