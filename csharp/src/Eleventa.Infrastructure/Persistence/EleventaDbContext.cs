using Eleventa.Domain.Entities;
using Microsoft.EntityFrameworkCore;

namespace Eleventa.Infrastructure.Persistence;

/// <summary>
/// Entity Framework Core DbContext for Eleventa POS.
/// </summary>
public class EleventaDbContext : DbContext
{
    public EleventaDbContext(DbContextOptions<EleventaDbContext> options)
        : base(options)
    {
    }

    // DbSets
    public DbSet<Product> Products => Set<Product>();
    public DbSet<Department> Departments => Set<Department>();
    public DbSet<Sale> Sales => Set<Sale>();
    public DbSet<SaleItem> SaleItems => Set<SaleItem>();
    public DbSet<Customer> Customers => Set<Customer>();
    public DbSet<User> Users => Set<User>();
    public DbSet<InventoryMovement> InventoryMovements => Set<InventoryMovement>();
    public DbSet<CashDrawerSession> CashDrawerSessions => Set<CashDrawerSession>();
    public DbSet<CashDrawerEntry> CashDrawerEntries => Set<CashDrawerEntry>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // Product configuration
        modelBuilder.Entity<Product>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Code).HasMaxLength(50).IsRequired();
            entity.Property(e => e.Description).HasMaxLength(255).IsRequired();
            entity.Property(e => e.CostPrice).HasPrecision(15, 2);
            entity.Property(e => e.SellPrice).HasPrecision(15, 2);
            entity.Property(e => e.WholesalePrice).HasPrecision(15, 2);
            entity.Property(e => e.SpecialPrice).HasPrecision(15, 2);
            entity.Property(e => e.QuantityInStock).HasPrecision(15, 3);
            entity.Property(e => e.MinStock).HasPrecision(15, 3);
            entity.Property(e => e.MaxStock).HasPrecision(15, 3);
            entity.Property(e => e.Unit).HasMaxLength(50).HasDefaultValue("Unidad");
            entity.Property(e => e.Barcode).HasMaxLength(50);
            entity.Property(e => e.Brand).HasMaxLength(50);
            entity.Property(e => e.Model).HasMaxLength(50);
            entity.Property(e => e.Notes).HasMaxLength(500);

            entity.HasOne(e => e.Department)
                  .WithMany(d => d.Products)
                  .HasForeignKey(e => e.DepartmentId)
                  .OnDelete(DeleteBehavior.SetNull);

            entity.HasIndex(e => e.Code).IsUnique();
            entity.HasIndex(e => e.Barcode);
        });

        // Department configuration
        modelBuilder.Entity<Department>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Name).HasMaxLength(100).IsRequired();
            entity.Property(e => e.Description).HasMaxLength(500);
        });

        // Sale configuration
        modelBuilder.Entity<Sale>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Status).HasMaxLength(50);

            entity.HasOne(e => e.Customer)
                  .WithMany(c => c.Sales)
                  .HasForeignKey(e => e.CustomerId)
                  .OnDelete(DeleteBehavior.SetNull);

            entity.HasOne(e => e.User)
                  .WithMany(u => u.Sales)
                  .HasForeignKey(e => e.UserId)
                  .OnDelete(DeleteBehavior.SetNull);

            entity.HasIndex(e => e.Timestamp);
        });

        // SaleItem configuration
        modelBuilder.Entity<SaleItem>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.ProductCode).HasMaxLength(50).IsRequired();
            entity.Property(e => e.ProductDescription).HasMaxLength(255).IsRequired();
            entity.Property(e => e.ProductUnit).HasMaxLength(50).HasDefaultValue("Unidad");
            entity.Property(e => e.Quantity).HasPrecision(15, 3);
            entity.Property(e => e.UnitPrice).HasPrecision(15, 2);

            entity.HasOne(e => e.Sale)
                  .WithMany(s => s.Items)
                  .HasForeignKey(e => e.SaleId)
                  .OnDelete(DeleteBehavior.Cascade);

            entity.HasOne(e => e.Product)
                  .WithMany(p => p.SaleItems)
                  .HasForeignKey(e => e.ProductId)
                  .OnDelete(DeleteBehavior.Restrict);
        });

        // Customer configuration
        modelBuilder.Entity<Customer>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Name).HasMaxLength(200).IsRequired();
            entity.Property(e => e.Phone).HasMaxLength(50);
            entity.Property(e => e.Email).HasMaxLength(255);
            entity.Property(e => e.Address).HasMaxLength(500);
            entity.Property(e => e.CUIT).HasMaxLength(13);
            entity.Property(e => e.IVACondition).HasMaxLength(100);
            entity.Property(e => e.CreditLimit).HasPrecision(15, 2);
            entity.Property(e => e.CreditBalance).HasPrecision(15, 2);

            entity.HasIndex(e => e.Email);
        });

        // User configuration
        modelBuilder.Entity<User>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Username).HasMaxLength(50).IsRequired();
            entity.Property(e => e.PasswordHash).HasMaxLength(255).IsRequired();
            entity.Property(e => e.FullName).HasMaxLength(200).IsRequired();
            entity.Property(e => e.Email).HasMaxLength(255);
            entity.Property(e => e.Role).HasMaxLength(50).HasDefaultValue("cashier");

            entity.HasIndex(e => e.Username).IsUnique();
        });

        // InventoryMovement configuration
        modelBuilder.Entity<InventoryMovement>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Quantity).HasPrecision(15, 3);
            entity.Property(e => e.UnitCost).HasPrecision(15, 2);
            entity.Property(e => e.PreviousStock).HasPrecision(15, 3);
            entity.Property(e => e.NewStock).HasPrecision(15, 3);
            entity.Property(e => e.Reason).HasMaxLength(500);
            entity.Property(e => e.Reference).HasMaxLength(100);

            entity.HasOne(e => e.Product)
                  .WithMany(p => p.InventoryMovements)
                  .HasForeignKey(e => e.ProductId)
                  .OnDelete(DeleteBehavior.Cascade);

            entity.HasOne(e => e.User)
                  .WithMany()
                  .HasForeignKey(e => e.UserId)
                  .OnDelete(DeleteBehavior.SetNull);

            entity.HasIndex(e => e.Timestamp);
            entity.HasIndex(e => e.ProductId);
        });

        // CashDrawerSession configuration
        modelBuilder.Entity<CashDrawerSession>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.OpeningBalance).HasPrecision(15, 2);
            entity.Property(e => e.ClosingBalance).HasPrecision(15, 2);
            entity.Property(e => e.ExpectedBalance).HasPrecision(15, 2);
            entity.Property(e => e.Difference).HasPrecision(15, 2);
            entity.Property(e => e.Notes).HasMaxLength(1000);

            entity.HasOne(e => e.User)
                  .WithMany()
                  .HasForeignKey(e => e.UserId)
                  .OnDelete(DeleteBehavior.Restrict);
        });

        // CashDrawerEntry configuration
        modelBuilder.Entity<CashDrawerEntry>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Amount).HasPrecision(15, 2);
            entity.Property(e => e.Reason).HasMaxLength(500);
            entity.Property(e => e.Reference).HasMaxLength(100);

            entity.HasOne(e => e.CashDrawerSession)
                  .WithMany(s => s.Entries)
                  .HasForeignKey(e => e.CashDrawerSessionId)
                  .OnDelete(DeleteBehavior.Cascade);

            entity.HasOne(e => e.User)
                  .WithMany()
                  .HasForeignKey(e => e.UserId)
                  .OnDelete(DeleteBehavior.SetNull);
        });

        // Seed data
        SeedData(modelBuilder);
    }

    private void SeedData(ModelBuilder modelBuilder)
    {
        // Seed default admin user
        modelBuilder.Entity<User>().HasData(
            new User
            {
                Id = 1,
                Username = "admin",
                PasswordHash = "$2a$11$YourHashedPasswordHere",  // You'll need to hash this properly
                FullName = "Administrator",
                Email = "admin@eleventa.com",
                Role = "admin",
                IsActive = true,
                CreatedAt = DateTime.UtcNow
            }
        );

        // Seed default department
        modelBuilder.Entity<Department>().HasData(
            new Department
            {
                Id = 1,
                Name = "General",
                Description = "General products",
                IsActive = true,
                CreatedAt = DateTime.UtcNow
            }
        );
    }
}
