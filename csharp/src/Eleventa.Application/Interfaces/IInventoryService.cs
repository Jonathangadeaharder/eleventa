using Eleventa.Domain.Entities;

namespace Eleventa.Application.Interfaces;

/// <summary>
/// Interface for inventory service operations.
/// </summary>
public interface IInventoryService
{
    /// <summary>
    /// Adjusts product inventory.
    /// </summary>
    /// <param name="productId">Product ID.</param>
    /// <param name="quantity">Quantity to adjust (positive for increase, negative for decrease).</param>
    /// <param name="movementType">Type of inventory movement.</param>
    /// <param name="reason">Reason for adjustment.</param>
    /// <param name="reference">Reference to related document/transaction.</param>
    /// <param name="userId">User making the adjustment.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The inventory movement record.</returns>
    Task<InventoryMovement> AdjustInventoryAsync(
        int productId,
        decimal quantity,
        InventoryMovementType movementType,
        string? reason = null,
        string? reference = null,
        int? userId = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Checks if product has sufficient inventory.
    /// </summary>
    /// <param name="productId">Product ID.</param>
    /// <param name="quantity">Quantity needed.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>True if sufficient inventory, false otherwise.</returns>
    Task<bool> HasSufficientInventoryAsync(int productId, decimal quantity, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets inventory movements for a product.
    /// </summary>
    /// <param name="productId">Product ID.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of inventory movements.</returns>
    Task<IEnumerable<InventoryMovement>> GetProductMovementsAsync(int productId, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets inventory movements within a date range.
    /// </summary>
    /// <param name="startDate">Start date.</param>
    /// <param name="endDate">End date.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of inventory movements.</returns>
    Task<IEnumerable<InventoryMovement>> GetMovementsByDateRangeAsync(
        DateTime startDate,
        DateTime endDate,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Reserves inventory for a sale (decreases stock).
    /// </summary>
    /// <param name="productId">Product ID.</param>
    /// <param name="quantity">Quantity to reserve.</param>
    /// <param name="saleReference">Reference to the sale.</param>
    /// <param name="userId">User making the sale.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The inventory movement record.</returns>
    Task<InventoryMovement> ReserveInventoryAsync(
        int productId,
        decimal quantity,
        string saleReference,
        int? userId = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Restores inventory (increases stock, e.g., for cancelled sales).
    /// </summary>
    /// <param name="productId">Product ID.</param>
    /// <param name="quantity">Quantity to restore.</param>
    /// <param name="reason">Reason for restoration.</param>
    /// <param name="reference">Reference to related transaction.</param>
    /// <param name="userId">User making the restoration.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The inventory movement record.</returns>
    Task<InventoryMovement> RestoreInventoryAsync(
        int productId,
        decimal quantity,
        string reason,
        string? reference = null,
        int? userId = null,
        CancellationToken cancellationToken = default);
}
