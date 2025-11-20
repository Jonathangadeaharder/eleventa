namespace Eleventa.Domain.Events;

/// <summary>
/// Marker interface for domain events.
/// Domain events represent something that happened in the domain.
/// </summary>
public interface IDomainEvent
{
    /// <summary>
    /// Unique identifier for this event.
    /// </summary>
    Guid EventId { get; }

    /// <summary>
    /// When the event occurred.
    /// </summary>
    DateTime OccurredAt { get; }
}
