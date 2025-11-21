namespace Eleventa.Domain.Events;

/// <summary>
/// Interface for publishing domain events.
/// </summary>
public interface IDomainEventPublisher
{
    /// <summary>
    /// Publishes a single domain event.
    /// </summary>
    void Publish(IDomainEvent domainEvent);

    /// <summary>
    /// Publishes multiple domain events.
    /// </summary>
    void PublishBatch(IEnumerable<IDomainEvent> domainEvents);
}
