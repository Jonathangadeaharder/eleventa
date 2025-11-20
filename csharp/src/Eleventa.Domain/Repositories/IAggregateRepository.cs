using Eleventa.Domain.Aggregates;
using Eleventa.Domain.Specifications;

namespace Eleventa.Domain.Repositories;

/// <summary>
/// Repository interface for aggregates.
/// </summary>
public interface IAggregateRepository<TAggregate, TId>
    where TAggregate : AggregateRoot<TId>
    where TId : notnull
{
    /// <summary>
    /// Gets an aggregate by ID.
    /// </summary>
    Task<TAggregate?> GetByIdAsync(TId id, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets all aggregates.
    /// </summary>
    Task<IEnumerable<TAggregate>> GetAllAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Finds aggregates by specification.
    /// </summary>
    Task<IEnumerable<TAggregate>> FindAsync(
        ISpecification<TAggregate> specification,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Saves an aggregate (insert or update).
    /// </summary>
    Task SaveAsync(TAggregate aggregate, CancellationToken cancellationToken = default);

    /// <summary>
    /// Deletes an aggregate.
    /// </summary>
    Task DeleteAsync(TId id, CancellationToken cancellationToken = default);

    /// <summary>
    /// Checks if an aggregate exists.
    /// </summary>
    Task<bool> ExistsAsync(TId id, CancellationToken cancellationToken = default);
}
