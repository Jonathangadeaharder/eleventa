using Eleventa.Application.DTOs;
using Eleventa.Application.Interfaces;

namespace Eleventa.Application.UseCases.Sales;

/// <summary>
/// Use case for retrieving a sale.
/// </summary>
public class GetSaleUseCase
{
    private readonly ISaleService _saleService;

    /// <summary>
    /// Initializes a new instance of the <see cref="GetSaleUseCase"/> class.
    /// </summary>
    /// <param name="saleService">Sale service.</param>
    public GetSaleUseCase(ISaleService saleService)
    {
        _saleService = saleService ?? throw new ArgumentNullException(nameof(saleService));
    }

    /// <summary>
    /// Executes the use case to get a sale by ID.
    /// </summary>
    /// <param name="id">Sale ID.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The sale DTO, or null if not found.</returns>
    public async Task<SaleDto?> ExecuteAsync(int id, CancellationToken cancellationToken = default)
    {
        if (id <= 0)
            throw new ArgumentException("Sale ID must be greater than 0.", nameof(id));

        return await _saleService.GetSaleByIdAsync(id, cancellationToken);
    }
}
