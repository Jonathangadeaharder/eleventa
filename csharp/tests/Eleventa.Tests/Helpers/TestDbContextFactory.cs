using Eleventa.Infrastructure.Persistence;
using Microsoft.EntityFrameworkCore;

namespace Eleventa.Tests.Helpers;

/// <summary>
/// Factory for creating test database contexts.
/// </summary>
public static class TestDbContextFactory
{
    /// <summary>
    /// Creates an in-memory database context for testing.
    /// </summary>
    /// <param name="databaseName">Optional database name. If not provided, a unique name is generated.</param>
    /// <returns>A new instance of EleventaDbContext configured for in-memory testing.</returns>
    public static EleventaDbContext CreateInMemoryDbContext(string? databaseName = null)
    {
        var dbName = databaseName ?? Guid.NewGuid().ToString();

        var options = new DbContextOptionsBuilder<EleventaDbContext>()
            .UseInMemoryDatabase(databaseName: dbName)
            .EnableSensitiveDataLogging()
            .EnableDetailedErrors()
            .Options;

        var context = new EleventaDbContext(options);

        // Ensure the database is created
        context.Database.EnsureCreated();

        return context;
    }

    /// <summary>
    /// Creates an in-memory database context with seeded test data.
    /// </summary>
    /// <param name="databaseName">Optional database name. If not provided, a unique name is generated.</param>
    /// <returns>A new instance of EleventaDbContext with test data.</returns>
    public static EleventaDbContext CreateInMemoryDbContextWithData(string? databaseName = null)
    {
        var context = CreateInMemoryDbContext(databaseName);
        TestDataSeeder.SeedTestData(context);
        return context;
    }
}
