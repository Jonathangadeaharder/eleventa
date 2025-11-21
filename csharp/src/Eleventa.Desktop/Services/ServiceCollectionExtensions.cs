using Microsoft.Extensions.DependencyInjection;

namespace Eleventa.Desktop.Services;

/// <summary>
/// Extension methods for configuring services in the dependency injection container.
/// </summary>
public static class ServiceCollectionExtensions
{
    /// <summary>
    /// Adds all Eleventa services to the dependency injection container.
    /// </summary>
    /// <param name="services">The service collection to configure.</param>
    /// <returns>The configured service collection.</returns>
    public static IServiceCollection AddEleventa(this IServiceCollection services)
    {
        // Register Domain Services
        // TODO: Add domain services when they are ready
        // services.AddScoped<IProductRepository, ProductRepository>();
        // services.AddScoped<ICustomerRepository, CustomerRepository>();
        // services.AddScoped<ISaleRepository, SaleRepository>();

        // Register Application Services
        // TODO: Add application services when they are ready
        // services.AddScoped<IProductService, ProductService>();
        // services.AddScoped<ICustomerService, CustomerService>();
        // services.AddScoped<ISalesService, SalesService>();
        // services.AddScoped<IInventoryService, InventoryService>();

        // Register Infrastructure Services
        // TODO: Add infrastructure services when they are ready
        // services.AddDbContext<EleventaDbContext>(options =>
        // {
        //     options.UseSqlite("Data Source=eleventa.db");
        // });

        // Register ViewModels
        // ViewModels are typically created on-demand with parameters,
        // so we don't register them here. They are instantiated directly
        // in the views or navigation service.

        return services;
    }
}
