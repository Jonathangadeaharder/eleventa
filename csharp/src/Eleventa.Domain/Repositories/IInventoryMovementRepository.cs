using Eleventa.Domain.Entities;

namespace Eleventa.Domain.Repositories;

/// <summary>
/// Repository interface for InventoryMovement entities.
/// </summary>
public interface IInventoryMovementRepository
{
    /// <summary>
    /// Gets an inventory movement by ID.
    /// </summary>
    Task<InventoryMovement?> GetByIdAsync(int id, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets all inventory movements.
    /// </summary>
    Task<IEnumerable<InventoryMovement>> GetAllAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets inventory movements by product.
    /// </summary>
    Task<IEnumerable<InventoryMovement>> GetByProductAsync(int productId, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets inventory movements by date range.
    /// </summary>
    Task<IEnumerable<InventoryMovement>> GetByDateRangeAsync(DateTime startDate, DateTime endDate, CancellationToken cancellationToken = default);

    /// <summary>
    /// Adds a new inventory movement.
    /// </summary>
    Task AddAsync(InventoryMovement movement, CancellationToken cancellationToken = default);

    /// <summary>
    /// Saves changes to the database.
    /// </summary>
    Task<int> SaveChangesAsync(CancellationToken cancellationToken = default);
}
