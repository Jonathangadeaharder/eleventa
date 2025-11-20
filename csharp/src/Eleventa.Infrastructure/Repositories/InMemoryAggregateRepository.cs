using Eleventa.Domain.Aggregates;
using Eleventa.Domain.Events;
using Eleventa.Domain.Repositories;
using Eleventa.Domain.Specifications;

namespace Eleventa.Infrastructure.Repositories;

/// <summary>
/// In-memory implementation of aggregate repository for testing.
/// </summary>
public class InMemoryAggregateRepository<TAggregate, TId> : IAggregateRepository<TAggregate, TId>
    where TAggregate : AggregateRoot<TId>
    where TId : notnull
{
    private readonly Dictionary<TId, TAggregate> _storage = new();
    private readonly IDomainEventPublisher _eventPublisher;

    public InMemoryAggregateRepository(IDomainEventPublisher? eventPublisher = null)
    {
        _eventPublisher = eventPublisher ?? new InMemoryEventPublisher();
    }

    public Task<TAggregate?> GetByIdAsync(TId id, CancellationToken cancellationToken = default)
    {
        _storage.TryGetValue(id, out var aggregate);
        return Task.FromResult(aggregate);
    }

    public Task<IEnumerable<TAggregate>> GetAllAsync(CancellationToken cancellationToken = default)
    {
        return Task.FromResult<IEnumerable<TAggregate>>(_storage.Values.ToList());
    }

    public Task<IEnumerable<TAggregate>> FindAsync(
        ISpecification<TAggregate> specification,
        CancellationToken cancellationToken = default)
    {
        var results = _storage.Values.Where(specification.IsSatisfiedBy).ToList();
        return Task.FromResult<IEnumerable<TAggregate>>(results);
    }

    public Task SaveAsync(TAggregate aggregate, CancellationToken cancellationToken = default)
    {
        _storage[aggregate.Id] = aggregate;

        // Publish domain events
        if (aggregate.HasDomainEvents)
        {
            var events = aggregate.DomainEvents.ToList();
            _eventPublisher.PublishBatch(events);
            aggregate.ClearDomainEvents();
        }

        // Increment version
        aggregate.IncrementVersion();

        return Task.CompletedTask;
    }

    public Task DeleteAsync(TId id, CancellationToken cancellationToken = default)
    {
        _storage.Remove(id);
        return Task.CompletedTask;
    }

    public Task<bool> ExistsAsync(TId id, CancellationToken cancellationToken = default)
    {
        return Task.FromResult(_storage.ContainsKey(id));
    }
}

/// <summary>
/// In-memory event publisher for testing.
/// </summary>
public class InMemoryEventPublisher : IDomainEventPublisher
{
    private readonly List<IDomainEvent> _publishedEvents = new();

    public IReadOnlyList<IDomainEvent> PublishedEvents => _publishedEvents.AsReadOnly();

    public void Publish(IDomainEvent domainEvent)
    {
        _publishedEvents.Add(domainEvent);
    }

    public void PublishBatch(IEnumerable<IDomainEvent> domainEvents)
    {
        _publishedEvents.AddRange(domainEvents);
    }

    public void Clear()
    {
        _publishedEvents.Clear();
    }
}
