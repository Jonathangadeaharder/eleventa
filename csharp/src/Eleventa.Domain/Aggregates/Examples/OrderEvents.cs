using Eleventa.Domain.Events;

namespace Eleventa.Domain.Aggregates.Examples;

public record OrderCreatedEvent(Guid OrderId, string Currency) : DomainEventBase;

public record OrderItemAddedEvent(Guid OrderId, Guid ProductId, string Name, int Quantity, decimal Price) : DomainEventBase;

public record OrderItemRemovedEvent(Guid OrderId, Guid ProductId) : DomainEventBase;

public record OrderSubmittedEvent(Guid OrderId, decimal TotalAmount) : DomainEventBase;

public record OrderCancelledEvent(Guid OrderId, string Reason) : DomainEventBase;
