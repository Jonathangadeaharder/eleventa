namespace Eleventa.Domain.Events;

/// <summary>
/// Interface for handling domain events.
/// </summary>
public interface IDomainEventHandler<in TEvent> where TEvent : IDomainEvent
{
    /// <summary>
    /// Handles the domain event.
    /// </summary>
    Task HandleAsync(TEvent domainEvent, CancellationToken cancellationToken = default);
}
