namespace Eleventa.Domain.Events;

/// <summary>
/// Base class for domain events.
/// </summary>
public abstract record DomainEventBase : IDomainEvent
{
    public Guid EventId { get; init; }
    public DateTime OccurredAt { get; init; }

    protected DomainEventBase()
    {
        EventId = Guid.NewGuid();
        OccurredAt = DateTime.UtcNow;
    }
}
