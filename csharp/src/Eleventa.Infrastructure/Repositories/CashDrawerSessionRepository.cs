using Eleventa.Domain.Entities;
using Eleventa.Domain.Repositories;
using Eleventa.Infrastructure.Persistence;
using Microsoft.EntityFrameworkCore;

namespace Eleventa.Infrastructure.Repositories;

/// <summary>
/// Entity Framework Core implementation of the CashDrawerSession repository.
/// </summary>
public class CashDrawerSessionRepository : ICashDrawerSessionRepository
{
    private readonly EleventaDbContext _context;

    public CashDrawerSessionRepository(EleventaDbContext context)
    {
        _context = context ?? throw new ArgumentNullException(nameof(context));
    }

    public async Task<CashDrawerSession?> GetByIdAsync(int id, CancellationToken cancellationToken = default)
    {
        return await _context.CashDrawerSessions
            .Include(s => s.User)
            .FirstOrDefaultAsync(s => s.Id == id, cancellationToken);
    }

    public async Task<CashDrawerSession?> GetByIdWithEntriesAsync(int id, CancellationToken cancellationToken = default)
    {
        return await _context.CashDrawerSessions
            .Include(s => s.User)
            .Include(s => s.Entries)
                .ThenInclude(e => e.User)
            .FirstOrDefaultAsync(s => s.Id == id, cancellationToken);
    }

    public async Task<IEnumerable<CashDrawerSession>> GetAllAsync(CancellationToken cancellationToken = default)
    {
        return await _context.CashDrawerSessions
            .Include(s => s.User)
            .OrderByDescending(s => s.OpeningTime)
            .ToListAsync(cancellationToken);
    }

    public async Task<CashDrawerSession?> GetCurrentOpenSessionAsync(CancellationToken cancellationToken = default)
    {
        return await _context.CashDrawerSessions
            .Include(s => s.User)
            .FirstOrDefaultAsync(s => s.ClosingTime == null, cancellationToken);
    }

    public async Task<IEnumerable<CashDrawerSession>> GetByUserAsync(int userId, CancellationToken cancellationToken = default)
    {
        return await _context.CashDrawerSessions
            .Where(s => s.UserId == userId)
            .OrderByDescending(s => s.OpeningTime)
            .ToListAsync(cancellationToken);
    }

    public async Task AddAsync(CashDrawerSession session, CancellationToken cancellationToken = default)
    {
        await _context.CashDrawerSessions.AddAsync(session, cancellationToken);
    }

    public Task UpdateAsync(CashDrawerSession session, CancellationToken cancellationToken = default)
    {
        _context.CashDrawerSessions.Update(session);
        return Task.CompletedTask;
    }

    public async Task<int> SaveChangesAsync(CancellationToken cancellationToken = default)
    {
        return await _context.SaveChangesAsync(cancellationToken);
    }
}
