using Eleventa.Domain.Repositories;
using Eleventa.Infrastructure.Persistence;
using Eleventa.Infrastructure.Repositories;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace Eleventa.Infrastructure;

/// <summary>
/// Extension methods for registering infrastructure services with dependency injection.
/// </summary>
public static class DependencyInjection
{
    /// <summary>
    /// Adds infrastructure services to the service collection.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="configuration">The application configuration.</param>
    /// <returns>The service collection for chaining.</returns>
    public static IServiceCollection AddInfrastructure(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        // Register DbContext
        var connectionString = configuration.GetConnectionString("DefaultConnection")
            ?? "Data Source=eleventa.db";

        services.AddDbContext<EleventaDbContext>(options =>
        {
            options.UseSqlite(connectionString);

            // Enable sensitive data logging in development
            if (configuration.GetValue<bool>("Logging:EnableSensitiveDataLogging"))
            {
                options.EnableSensitiveDataLogging();
            }

            // Enable detailed errors in development
            if (configuration.GetValue<bool>("Logging:EnableDetailedErrors"))
            {
                options.EnableDetailedErrors();
            }
        });

        // Register repositories
        services.AddScoped<IProductRepository, ProductRepository>();
        services.AddScoped<ISaleRepository, SaleRepository>();
        services.AddScoped<ICustomerRepository, CustomerRepository>();
        services.AddScoped<IDepartmentRepository, DepartmentRepository>();
        services.AddScoped<IUserRepository, UserRepository>();
        services.AddScoped<IInventoryMovementRepository, InventoryMovementRepository>();
        services.AddScoped<ICashDrawerSessionRepository, CashDrawerSessionRepository>();

        // Register generic aggregate repository
        services.AddScoped(typeof(IAggregateRepository<,>), typeof(InMemoryAggregateRepository<,>));

        return services;
    }

    /// <summary>
    /// Adds infrastructure services for testing with in-memory database.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="databaseName">The name of the in-memory database.</param>
    /// <returns>The service collection for chaining.</returns>
    public static IServiceCollection AddInfrastructureForTesting(
        this IServiceCollection services,
        string? databaseName = null)
    {
        var dbName = databaseName ?? Guid.NewGuid().ToString();

        // Register DbContext with in-memory database
        services.AddDbContext<EleventaDbContext>(options =>
        {
            options.UseInMemoryDatabase(dbName);
            options.EnableSensitiveDataLogging();
            options.EnableDetailedErrors();
        });

        // Register repositories
        services.AddScoped<IProductRepository, ProductRepository>();
        services.AddScoped<ISaleRepository, SaleRepository>();
        services.AddScoped<ICustomerRepository, CustomerRepository>();
        services.AddScoped<IDepartmentRepository, DepartmentRepository>();
        services.AddScoped<IUserRepository, UserRepository>();
        services.AddScoped<IInventoryMovementRepository, InventoryMovementRepository>();
        services.AddScoped<ICashDrawerSessionRepository, CashDrawerSessionRepository>();

        // Register generic aggregate repository
        services.AddScoped(typeof(IAggregateRepository<,>), typeof(InMemoryAggregateRepository<,>));

        return services;
    }
}
