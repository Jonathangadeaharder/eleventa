using Eleventa.Infrastructure.Persistence;
using Eleventa.Tests.Helpers;

namespace Eleventa.Tests.Integration;

/// <summary>
/// Base class for integration tests that need database access.
/// </summary>
public abstract class IntegrationTestBase : IDisposable
{
    protected readonly EleventaDbContext _context;

    protected IntegrationTestBase()
    {
        // Create a unique database for each test
        _context = TestDbContextFactory.CreateInMemoryDbContext();
    }

    protected IntegrationTestBase(bool seedData)
    {
        // Create a unique database for each test with optional seed data
        _context = seedData
            ? TestDbContextFactory.CreateInMemoryDbContextWithData()
            : TestDbContextFactory.CreateInMemoryDbContext();
    }

    /// <summary>
    /// Disposes the database context.
    /// </summary>
    public void Dispose()
    {
        Dispose(true);
        GC.SuppressFinalize(this);
    }

    /// <summary>
    /// Disposes the database context.
    /// </summary>
    /// <param name="disposing">Whether to dispose managed resources.</param>
    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            _context?.Dispose();
        }
    }
}
