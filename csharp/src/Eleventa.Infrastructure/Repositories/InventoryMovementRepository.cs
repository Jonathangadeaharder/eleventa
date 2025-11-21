using Eleventa.Domain.Entities;
using Eleventa.Domain.Repositories;
using Eleventa.Infrastructure.Persistence;
using Microsoft.EntityFrameworkCore;

namespace Eleventa.Infrastructure.Repositories;

/// <summary>
/// Entity Framework Core implementation of the InventoryMovement repository.
/// </summary>
public class InventoryMovementRepository : IInventoryMovementRepository
{
    private readonly EleventaDbContext _context;

    public InventoryMovementRepository(EleventaDbContext context)
    {
        _context = context ?? throw new ArgumentNullException(nameof(context));
    }

    public async Task<InventoryMovement?> GetByIdAsync(int id, CancellationToken cancellationToken = default)
    {
        return await _context.InventoryMovements
            .Include(im => im.Product)
            .Include(im => im.User)
            .FirstOrDefaultAsync(im => im.Id == id, cancellationToken);
    }

    public async Task<IEnumerable<InventoryMovement>> GetAllAsync(CancellationToken cancellationToken = default)
    {
        return await _context.InventoryMovements
            .Include(im => im.Product)
            .Include(im => im.User)
            .OrderByDescending(im => im.Timestamp)
            .ToListAsync(cancellationToken);
    }

    public async Task<IEnumerable<InventoryMovement>> GetByProductAsync(int productId, CancellationToken cancellationToken = default)
    {
        return await _context.InventoryMovements
            .Include(im => im.Product)
            .Include(im => im.User)
            .Where(im => im.ProductId == productId)
            .OrderByDescending(im => im.Timestamp)
            .ToListAsync(cancellationToken);
    }

    public async Task<IEnumerable<InventoryMovement>> GetByDateRangeAsync(DateTime startDate, DateTime endDate, CancellationToken cancellationToken = default)
    {
        return await _context.InventoryMovements
            .Include(im => im.Product)
            .Include(im => im.User)
            .Where(im => im.Timestamp >= startDate && im.Timestamp <= endDate)
            .OrderByDescending(im => im.Timestamp)
            .ToListAsync(cancellationToken);
    }

    public async Task AddAsync(InventoryMovement movement, CancellationToken cancellationToken = default)
    {
        await _context.InventoryMovements.AddAsync(movement, cancellationToken);
    }

    public async Task<int> SaveChangesAsync(CancellationToken cancellationToken = default)
    {
        return await _context.SaveChangesAsync(cancellationToken);
    }
}
