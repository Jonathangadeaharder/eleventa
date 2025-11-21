using Eleventa.Application.DTOs;
using Eleventa.Application.Interfaces;

namespace Eleventa.Application.UseCases.Customers;

/// <summary>
/// Use case for creating a new customer.
/// </summary>
public class CreateCustomerUseCase
{
    private readonly ICustomerService _customerService;

    /// <summary>
    /// Initializes a new instance of the <see cref="CreateCustomerUseCase"/> class.
    /// </summary>
    /// <param name="customerService">Customer service.</param>
    public CreateCustomerUseCase(ICustomerService customerService)
    {
        _customerService = customerService ?? throw new ArgumentNullException(nameof(customerService));
    }

    /// <summary>
    /// Executes the use case to create a new customer.
    /// </summary>
    /// <param name="customerDto">Customer data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The created customer DTO.</returns>
    /// <exception cref="ArgumentNullException">Thrown when customerDto is null.</exception>
    /// <exception cref="InvalidOperationException">Thrown when validation fails.</exception>
    public async Task<CustomerDto> ExecuteAsync(CustomerDto customerDto, CancellationToken cancellationToken = default)
    {
        if (customerDto == null)
            throw new ArgumentNullException(nameof(customerDto));

        if (string.IsNullOrWhiteSpace(customerDto.Name))
            throw new InvalidOperationException("Customer name is required.");

        // If CUIT is provided, check it's unique
        if (!string.IsNullOrWhiteSpace(customerDto.CUIT))
        {
            var existingCustomer = await _customerService.GetCustomerByCUITAsync(customerDto.CUIT, cancellationToken);
            if (existingCustomer != null)
            {
                throw new InvalidOperationException($"Customer with CUIT '{customerDto.CUIT}' already exists.");
            }
        }

        // Create the customer
        var result = await _customerService.CreateCustomerAsync(customerDto, cancellationToken);

        return result;
    }
}
