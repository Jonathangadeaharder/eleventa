using Eleventa.Application.DTOs;

namespace Eleventa.Application.Interfaces;

/// <summary>
/// Interface for sale service operations.
/// </summary>
public interface ISaleService
{
    /// <summary>
    /// Creates a new sale.
    /// </summary>
    /// <param name="createSaleDto">Sale creation data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The created sale DTO.</returns>
    Task<SaleDto> CreateSaleAsync(CreateSaleDto createSaleDto, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets a sale by ID.
    /// </summary>
    /// <param name="id">Sale ID.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The sale DTO, or null if not found.</returns>
    Task<SaleDto?> GetSaleByIdAsync(int id, CancellationToken cancellationToken = default);

    /// <summary>
    /// Lists all sales.
    /// </summary>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of sale DTOs.</returns>
    Task<IEnumerable<SaleDto>> ListSalesAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Lists sales for a specific customer.
    /// </summary>
    /// <param name="customerId">Customer ID.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of sale DTOs for the customer.</returns>
    Task<IEnumerable<SaleDto>> ListSalesByCustomerAsync(int customerId, CancellationToken cancellationToken = default);

    /// <summary>
    /// Lists sales within a date range.
    /// </summary>
    /// <param name="startDate">Start date.</param>
    /// <param name="endDate">End date.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of sale DTOs within the date range.</returns>
    Task<IEnumerable<SaleDto>> ListSalesByDateRangeAsync(DateTime startDate, DateTime endDate, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets total sales amount for a date range.
    /// </summary>
    /// <param name="startDate">Start date.</param>
    /// <param name="endDate">End date.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Total sales amount.</returns>
    Task<decimal> GetTotalSalesAmountAsync(DateTime startDate, DateTime endDate, CancellationToken cancellationToken = default);

    /// <summary>
    /// Cancels a sale.
    /// </summary>
    /// <param name="id">Sale ID.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>True if cancelled successfully, false otherwise.</returns>
    Task<bool> CancelSaleAsync(int id, CancellationToken cancellationToken = default);
}
