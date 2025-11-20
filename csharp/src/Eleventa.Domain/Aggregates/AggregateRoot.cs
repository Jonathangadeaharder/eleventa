using Eleventa.Domain.Events;

namespace Eleventa.Domain.Aggregates;

/// <summary>
/// Base class for aggregate roots.
/// Aggregates are consistency boundaries that encapsulate entities and value objects.
/// </summary>
public abstract class AggregateRoot<TId> : Entity<TId>
    where TId : notnull
{
    private readonly List<IDomainEvent> _domainEvents = new();

    public int Version { get; private set; }

    protected AggregateRoot(TId id) : base(id)
    {
        Version = 0;
    }

    /// <summary>
    /// Gets all domain events raised by this aggregate.
    /// </summary>
    public IReadOnlyCollection<IDomainEvent> DomainEvents => _domainEvents.AsReadOnly();

    /// <summary>
    /// Checks if this aggregate has any domain events.
    /// </summary>
    public bool HasDomainEvents => _domainEvents.Any();

    /// <summary>
    /// Adds a domain event to the aggregate.
    /// </summary>
    protected void AddDomainEvent(IDomainEvent domainEvent)
    {
        _domainEvents.Add(domainEvent);
    }

    /// <summary>
    /// Clears all domain events from the aggregate.
    /// </summary>
    public void ClearDomainEvents()
    {
        _domainEvents.Clear();
    }

    /// <summary>
    /// Increments the aggregate version.
    /// Should be called after persisting.
    /// </summary>
    public void IncrementVersion()
    {
        Version++;
    }
}
