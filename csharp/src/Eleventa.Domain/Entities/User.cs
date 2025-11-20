namespace Eleventa.Domain.Entities;

/// <summary>
/// Represents a system user.
/// </summary>
public class User
{
    public int Id { get; set; }
    public string Username { get; set; } = string.Empty;
    public string PasswordHash { get; set; } = string.Empty;
    public string FullName { get; set; } = string.Empty;
    public string? Email { get; set; }
    public string Role { get; set; } = "cashier";  // admin, cashier, manager
    public bool IsActive { get; set; } = true;
    public DateTime? LastLogin { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime? UpdatedAt { get; set; }

    // Navigation properties
    public ICollection<Sale> Sales { get; set; } = new List<Sale>();

    /// <summary>
    /// Checks if user has the specified role.
    /// </summary>
    public bool HasRole(string role)
    {
        return Role.Equals(role, StringComparison.OrdinalIgnoreCase);
    }

    /// <summary>
    /// Checks if user is an administrator.
    /// </summary>
    public bool IsAdmin => HasRole("admin");
}
