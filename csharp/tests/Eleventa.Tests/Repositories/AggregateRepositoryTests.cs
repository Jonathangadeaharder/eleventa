using Eleventa.Domain.Aggregates.Examples;
using Eleventa.Domain.ValueObjects;
using Eleventa.Infrastructure.Repositories;
using Xunit;

namespace Eleventa.Tests.Repositories;

public class AggregateRepositoryTests
{
    [Fact]
    public async Task SaveAndGet_ValidAggregate_Success()
    {
        // Arrange
        var eventPublisher = new InMemoryEventPublisher();
        var repository = new InMemoryAggregateRepository<Order, Guid>(eventPublisher);
        var order = new Order(Guid.NewGuid(), "USD");
        order.AddItem(Guid.NewGuid(), "Widget", 1, Money.Create(10, "USD"));

        // Act
        await repository.SaveAsync(order);
        var retrieved = await repository.GetByIdAsync(order.Id);

        // Assert
        Assert.NotNull(retrieved);
        Assert.Equal(order.Id, retrieved.Id);
        Assert.Single(retrieved.Items);
    }

    [Fact]
    public async Task Save_WithDomainEvents_EventsPublished()
    {
        // Arrange
        var eventPublisher = new InMemoryEventPublisher();
        var repository = new InMemoryAggregateRepository<Order, Guid>(eventPublisher);
        var order = new Order(Guid.NewGuid(), "USD");

        // Act
        await repository.SaveAsync(order);

        // Assert
        Assert.NotEmpty(eventPublisher.PublishedEvents);
        Assert.Contains(eventPublisher.PublishedEvents, e => e is OrderCreatedEvent);
    }

    [Fact]
    public async Task Save_IncreasesVersion()
    {
        // Arrange
        var repository = new InMemoryAggregateRepository<Order, Guid>();
        var order = new Order(Guid.NewGuid(), "USD");
        Assert.Equal(0, order.Version);

        // Act
        await repository.SaveAsync(order);

        // Assert
        Assert.Equal(1, order.Version);
    }

    [Fact]
    public async Task Delete_ExistingAggregate_Success()
    {
        // Arrange
        var repository = new InMemoryAggregateRepository<Order, Guid>();
        var order = new Order(Guid.NewGuid(), "USD");
        await repository.SaveAsync(order);

        // Act
        await repository.DeleteAsync(order.Id);
        var retrieved = await repository.GetByIdAsync(order.Id);

        // Assert
        Assert.Null(retrieved);
    }

    [Fact]
    public async Task Exists_ExistingAggregate_ReturnsTrue()
    {
        // Arrange
        var repository = new InMemoryAggregateRepository<Order, Guid>();
        var order = new Order(Guid.NewGuid(), "USD");
        await repository.SaveAsync(order);

        // Act
        var exists = await repository.ExistsAsync(order.Id);

        // Assert
        Assert.True(exists);
    }

    [Fact]
    public async Task GetAll_MultipleAggregates_ReturnsAll()
    {
        // Arrange
        var repository = new InMemoryAggregateRepository<Order, Guid>();
        var order1 = new Order(Guid.NewGuid(), "USD");
        var order2 = new Order(Guid.NewGuid(), "USD");
        await repository.SaveAsync(order1);
        await repository.SaveAsync(order2);

        // Act
        var all = await repository.GetAllAsync();

        // Assert
        Assert.Equal(2, all.Count());
    }
}
