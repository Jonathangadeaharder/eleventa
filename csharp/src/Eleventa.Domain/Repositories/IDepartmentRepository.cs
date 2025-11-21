using Eleventa.Domain.Entities;

namespace Eleventa.Domain.Repositories;

/// <summary>
/// Repository interface for Department entities.
/// </summary>
public interface IDepartmentRepository
{
    /// <summary>
    /// Gets a department by ID.
    /// </summary>
    Task<Department?> GetByIdAsync(int id, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets all departments.
    /// </summary>
    Task<IEnumerable<Department>> GetAllAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Adds a new department.
    /// </summary>
    Task AddAsync(Department department, CancellationToken cancellationToken = default);

    /// <summary>
    /// Updates an existing department.
    /// </summary>
    Task UpdateAsync(Department department, CancellationToken cancellationToken = default);

    /// <summary>
    /// Deletes a department.
    /// </summary>
    Task DeleteAsync(int id, CancellationToken cancellationToken = default);

    /// <summary>
    /// Saves changes to the database.
    /// </summary>
    Task<int> SaveChangesAsync(CancellationToken cancellationToken = default);
}
