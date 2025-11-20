using Eleventa.Domain.Entities;

namespace Eleventa.Domain.Repositories;

/// <summary>
/// Repository interface for Sale entities.
/// </summary>
public interface ISaleRepository
{
    /// <summary>
    /// Gets a sale by ID.
    /// </summary>
    Task<Sale?> GetByIdAsync(int id, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets a sale by ID with items included.
    /// </summary>
    Task<Sale?> GetByIdWithItemsAsync(int id, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets all sales.
    /// </summary>
    Task<IEnumerable<Sale>> GetAllAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets sales by customer.
    /// </summary>
    Task<IEnumerable<Sale>> GetByCustomerAsync(int customerId, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets sales by date range.
    /// </summary>
    Task<IEnumerable<Sale>> GetByDateRangeAsync(DateTime startDate, DateTime endDate, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets sales by status.
    /// </summary>
    Task<IEnumerable<Sale>> GetByStatusAsync(string status, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets sales by user.
    /// </summary>
    Task<IEnumerable<Sale>> GetByUserAsync(int userId, CancellationToken cancellationToken = default);

    /// <summary>
    /// Adds a new sale.
    /// </summary>
    Task AddAsync(Sale sale, CancellationToken cancellationToken = default);

    /// <summary>
    /// Updates an existing sale.
    /// </summary>
    Task UpdateAsync(Sale sale, CancellationToken cancellationToken = default);

    /// <summary>
    /// Deletes a sale.
    /// </summary>
    Task DeleteAsync(int id, CancellationToken cancellationToken = default);

    /// <summary>
    /// Saves changes to the database.
    /// </summary>
    Task<int> SaveChangesAsync(CancellationToken cancellationToken = default);
}
