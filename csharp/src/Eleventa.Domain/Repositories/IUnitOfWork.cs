namespace Eleventa.Domain.Repositories;

/// <summary>
/// Unit of Work interface for managing transactions and coordinating repository operations.
/// </summary>
public interface IUnitOfWork : IDisposable
{
    /// <summary>
    /// Gets the Product repository.
    /// </summary>
    IProductRepository Products { get; }

    /// <summary>
    /// Gets the Sale repository.
    /// </summary>
    ISaleRepository Sales { get; }

    /// <summary>
    /// Gets the Customer repository.
    /// </summary>
    ICustomerRepository Customers { get; }

    /// <summary>
    /// Gets the User repository.
    /// </summary>
    IUserRepository Users { get; }

    /// <summary>
    /// Gets the InventoryMovement repository.
    /// </summary>
    IInventoryMovementRepository InventoryMovements { get; }

    /// <summary>
    /// Gets the Department repository.
    /// </summary>
    IDepartmentRepository Departments { get; }

    /// <summary>
    /// Gets the CashDrawerSession repository.
    /// </summary>
    ICashDrawerSessionRepository CashDrawerSessions { get; }

    /// <summary>
    /// Commits all changes to the database as a single transaction.
    /// </summary>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The number of state entries written to the database.</returns>
    Task<int> CommitAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Begins a new database transaction.
    /// </summary>
    /// <param name="cancellationToken">Cancellation token.</param>
    Task BeginTransactionAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Commits the current transaction.
    /// </summary>
    /// <param name="cancellationToken">Cancellation token.</param>
    Task CommitTransactionAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Rolls back the current transaction.
    /// </summary>
    /// <param name="cancellationToken">Cancellation token.</param>
    Task RollbackTransactionAsync(CancellationToken cancellationToken = default);
}
