using Microsoft.Extensions.DependencyInjection;

namespace Eleventa.Application;

/// <summary>
/// Extension methods for registering application services with dependency injection.
/// </summary>
public static class DependencyInjection
{
    /// <summary>
    /// Adds application services to the service collection.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <returns>The service collection for chaining.</returns>
    public static IServiceCollection AddApplication(this IServiceCollection services)
    {
        // Register application services
        services.AddScoped<Interfaces.IProductService, Services.ProductService>();
        services.AddScoped<Interfaces.ISaleService, Services.SaleService>();
        services.AddScoped<Interfaces.ICustomerService, Services.CustomerService>();
        services.AddScoped<Interfaces.IInventoryService, Services.InventoryService>();

        // Register use cases
        services.AddScoped<UseCases.Products.CreateProductUseCase>();
        services.AddScoped<UseCases.Products.UpdateProductUseCase>();
        services.AddScoped<UseCases.Products.GetProductUseCase>();
        services.AddScoped<UseCases.Products.ListProductsUseCase>();

        services.AddScoped<UseCases.Sales.CreateSaleUseCase>();
        services.AddScoped<UseCases.Sales.GetSaleUseCase>();

        services.AddScoped<UseCases.Customers.CreateCustomerUseCase>();
        services.AddScoped<UseCases.Customers.UpdateCustomerUseCase>();

        return services;
    }
}
