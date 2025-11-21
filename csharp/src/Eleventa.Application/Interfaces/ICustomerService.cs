using Eleventa.Application.DTOs;

namespace Eleventa.Application.Interfaces;

/// <summary>
/// Interface for customer service operations.
/// </summary>
public interface ICustomerService
{
    /// <summary>
    /// Creates a new customer.
    /// </summary>
    /// <param name="customerDto">Customer data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The created customer DTO.</returns>
    Task<CustomerDto> CreateCustomerAsync(CustomerDto customerDto, CancellationToken cancellationToken = default);

    /// <summary>
    /// Updates an existing customer.
    /// </summary>
    /// <param name="customerDto">Customer update data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The updated customer DTO.</returns>
    Task<CustomerDto> UpdateCustomerAsync(CustomerDto customerDto, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets a customer by ID.
    /// </summary>
    /// <param name="id">Customer ID.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The customer DTO, or null if not found.</returns>
    Task<CustomerDto?> GetCustomerByIdAsync(int id, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets a customer by CUIT.
    /// </summary>
    /// <param name="cuit">Customer CUIT/Tax ID.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The customer DTO, or null if not found.</returns>
    Task<CustomerDto?> GetCustomerByCUITAsync(string cuit, CancellationToken cancellationToken = default);

    /// <summary>
    /// Lists all customers.
    /// </summary>
    /// <param name="includeInactive">Whether to include inactive customers.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of customer DTOs.</returns>
    Task<IEnumerable<CustomerDto>> ListCustomersAsync(bool includeInactive = false, CancellationToken cancellationToken = default);

    /// <summary>
    /// Searches customers by name.
    /// </summary>
    /// <param name="searchTerm">Search term.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of matching customer DTOs.</returns>
    Task<IEnumerable<CustomerDto>> SearchCustomersByNameAsync(string searchTerm, CancellationToken cancellationToken = default);

    /// <summary>
    /// Lists customers with outstanding credit balances.
    /// </summary>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of customer DTOs with credit balances.</returns>
    Task<IEnumerable<CustomerDto>> ListCustomersWithCreditBalanceAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Deletes a customer.
    /// </summary>
    /// <param name="id">Customer ID.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>True if deleted successfully, false otherwise.</returns>
    Task<bool> DeleteCustomerAsync(int id, CancellationToken cancellationToken = default);

    /// <summary>
    /// Updates customer credit balance.
    /// </summary>
    /// <param name="customerId">Customer ID.</param>
    /// <param name="amount">Amount to add (positive) or subtract (negative).</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The updated customer DTO.</returns>
    Task<CustomerDto> UpdateCreditBalanceAsync(int customerId, decimal amount, CancellationToken cancellationToken = default);
}
