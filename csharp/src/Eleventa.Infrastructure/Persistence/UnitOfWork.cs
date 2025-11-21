using Eleventa.Domain.Repositories;
using Eleventa.Infrastructure.Repositories;
using Microsoft.EntityFrameworkCore.Storage;

namespace Eleventa.Infrastructure.Persistence;

/// <summary>
/// Unit of Work implementation for managing transactions and coordinating repositories.
/// </summary>
public class UnitOfWork : IUnitOfWork
{
    private readonly EleventaDbContext _context;
    private IDbContextTransaction? _transaction;

    // Lazy-loaded repositories
    private IProductRepository? _products;
    private ISaleRepository? _sales;
    private ICustomerRepository? _customers;
    private IUserRepository? _users;
    private IInventoryMovementRepository? _inventoryMovements;
    private IDepartmentRepository? _departments;
    private ICashDrawerSessionRepository? _cashDrawerSessions;

    /// <summary>
    /// Initializes a new instance of the UnitOfWork class.
    /// </summary>
    /// <param name="context">The database context.</param>
    public UnitOfWork(EleventaDbContext context)
    {
        _context = context ?? throw new ArgumentNullException(nameof(context));
    }

    /// <inheritdoc/>
    public IProductRepository Products =>
        _products ??= new ProductRepository(_context);

    /// <inheritdoc/>
    public ISaleRepository Sales =>
        _sales ??= new SaleRepository(_context);

    /// <inheritdoc/>
    public ICustomerRepository Customers =>
        _customers ??= new CustomerRepository(_context);

    /// <inheritdoc/>
    public IUserRepository Users =>
        _users ??= new UserRepository(_context);

    /// <inheritdoc/>
    public IInventoryMovementRepository InventoryMovements =>
        _inventoryMovements ??= new InventoryMovementRepository(_context);

    /// <inheritdoc/>
    public IDepartmentRepository Departments =>
        _departments ??= new DepartmentRepository(_context);

    /// <inheritdoc/>
    public ICashDrawerSessionRepository CashDrawerSessions =>
        _cashDrawerSessions ??= new CashDrawerSessionRepository(_context);

    /// <inheritdoc/>
    public async Task<int> CommitAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            return await _context.SaveChangesAsync(cancellationToken);
        }
        catch (Exception ex)
        {
            throw new InvalidOperationException("Error committing transaction", ex);
        }
    }

    /// <inheritdoc/>
    public async Task BeginTransactionAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            if (_transaction != null)
                throw new InvalidOperationException("A transaction is already in progress.");

            _transaction = await _context.Database.BeginTransactionAsync(cancellationToken);
        }
        catch (Exception ex) when (ex is not InvalidOperationException)
        {
            throw new InvalidOperationException("Error beginning transaction", ex);
        }
    }

    /// <inheritdoc/>
    public async Task CommitTransactionAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            if (_transaction == null)
                throw new InvalidOperationException("No transaction in progress.");

            await _transaction.CommitAsync(cancellationToken);
        }
        catch (Exception ex) when (ex is not InvalidOperationException)
        {
            throw new InvalidOperationException("Error committing transaction", ex);
        }
        finally
        {
            if (_transaction != null)
            {
                await _transaction.DisposeAsync();
                _transaction = null;
            }
        }
    }

    /// <inheritdoc/>
    public async Task RollbackTransactionAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            if (_transaction == null)
                throw new InvalidOperationException("No transaction in progress.");

            await _transaction.RollbackAsync(cancellationToken);
        }
        catch (Exception ex) when (ex is not InvalidOperationException)
        {
            throw new InvalidOperationException("Error rolling back transaction", ex);
        }
        finally
        {
            if (_transaction != null)
            {
                await _transaction.DisposeAsync();
                _transaction = null;
            }
        }
    }

    /// <summary>
    /// Disposes the Unit of Work and underlying resources.
    /// </summary>
    public void Dispose()
    {
        Dispose(true);
        GC.SuppressFinalize(this);
    }

    /// <summary>
    /// Disposes the Unit of Work and underlying resources.
    /// </summary>
    /// <param name="disposing">Whether to dispose managed resources.</param>
    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            _transaction?.Dispose();
            // Don't dispose the context as it's managed by DI container
        }
    }
}
