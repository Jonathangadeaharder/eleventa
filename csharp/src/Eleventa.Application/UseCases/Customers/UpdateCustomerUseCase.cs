using Eleventa.Application.DTOs;
using Eleventa.Application.Interfaces;

namespace Eleventa.Application.UseCases.Customers;

/// <summary>
/// Use case for updating an existing customer.
/// </summary>
public class UpdateCustomerUseCase
{
    private readonly ICustomerService _customerService;

    /// <summary>
    /// Initializes a new instance of the <see cref="UpdateCustomerUseCase"/> class.
    /// </summary>
    /// <param name="customerService">Customer service.</param>
    public UpdateCustomerUseCase(ICustomerService customerService)
    {
        _customerService = customerService ?? throw new ArgumentNullException(nameof(customerService));
    }

    /// <summary>
    /// Executes the use case to update an existing customer.
    /// </summary>
    /// <param name="customerDto">Customer update data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The updated customer DTO.</returns>
    /// <exception cref="ArgumentNullException">Thrown when customerDto is null.</exception>
    /// <exception cref="InvalidOperationException">Thrown when customer is not found or validation fails.</exception>
    public async Task<CustomerDto> ExecuteAsync(CustomerDto customerDto, CancellationToken cancellationToken = default)
    {
        if (customerDto == null)
            throw new ArgumentNullException(nameof(customerDto));

        if (customerDto.Id <= 0)
            throw new InvalidOperationException("Customer ID must be greater than 0.");

        // Verify customer exists
        var existingCustomer = await _customerService.GetCustomerByIdAsync(customerDto.Id, cancellationToken);
        if (existingCustomer == null)
        {
            throw new InvalidOperationException($"Customer with ID {customerDto.Id} not found.");
        }

        // If CUIT is being updated, validate it's unique
        if (!string.IsNullOrWhiteSpace(customerDto.CUIT) &&
            customerDto.CUIT != existingCustomer.CUIT)
        {
            var customerWithCUIT = await _customerService.GetCustomerByCUITAsync(customerDto.CUIT, cancellationToken);
            if (customerWithCUIT != null && customerWithCUIT.Id != customerDto.Id)
            {
                throw new InvalidOperationException($"Customer with CUIT '{customerDto.CUIT}' already exists.");
            }
        }

        // Update the customer
        var result = await _customerService.UpdateCustomerAsync(customerDto, cancellationToken);

        return result;
    }
}
