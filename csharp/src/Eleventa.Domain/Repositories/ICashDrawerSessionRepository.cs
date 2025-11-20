using Eleventa.Domain.Entities;

namespace Eleventa.Domain.Repositories;

/// <summary>
/// Repository interface for CashDrawerSession entities.
/// </summary>
public interface ICashDrawerSessionRepository
{
    /// <summary>
    /// Gets a cash drawer session by ID.
    /// </summary>
    Task<CashDrawerSession?> GetByIdAsync(int id, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets a cash drawer session by ID with entries included.
    /// </summary>
    Task<CashDrawerSession?> GetByIdWithEntriesAsync(int id, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets all cash drawer sessions.
    /// </summary>
    Task<IEnumerable<CashDrawerSession>> GetAllAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets the current open session.
    /// </summary>
    Task<CashDrawerSession?> GetCurrentOpenSessionAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets sessions by user.
    /// </summary>
    Task<IEnumerable<CashDrawerSession>> GetByUserAsync(int userId, CancellationToken cancellationToken = default);

    /// <summary>
    /// Adds a new cash drawer session.
    /// </summary>
    Task AddAsync(CashDrawerSession session, CancellationToken cancellationToken = default);

    /// <summary>
    /// Updates an existing cash drawer session.
    /// </summary>
    Task UpdateAsync(CashDrawerSession session, CancellationToken cancellationToken = default);

    /// <summary>
    /// Saves changes to the database.
    /// </summary>
    Task<int> SaveChangesAsync(CancellationToken cancellationToken = default);
}
