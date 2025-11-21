using Eleventa.Domain.Entities;
using Eleventa.Infrastructure.Persistence;

namespace Eleventa.Tests.Helpers;

/// <summary>
/// Seeds test data into the database for testing purposes.
/// </summary>
public static class TestDataSeeder
{
    /// <summary>
    /// Seeds comprehensive test data into the database.
    /// </summary>
    /// <param name="context">The database context to seed.</param>
    public static void SeedTestData(EleventaDbContext context)
    {
        // Seed Departments
        var department1 = new Department
        {
            Id = 1,
            Name = "Electronics",
            Description = "Electronic products",
            IsActive = true,
            CreatedAt = DateTime.UtcNow
        };

        var department2 = new Department
        {
            Id = 2,
            Name = "Groceries",
            Description = "Grocery items",
            IsActive = true,
            CreatedAt = DateTime.UtcNow
        };

        context.Departments.AddRange(department1, department2);

        // Seed Users
        var user1 = new User
        {
            Id = 1,
            Username = "testuser1",
            PasswordHash = "$2a$11$TestHash1",
            FullName = "Test User 1",
            Email = "testuser1@test.com",
            Role = "cashier",
            IsActive = true,
            CreatedAt = DateTime.UtcNow
        };

        var user2 = new User
        {
            Id = 2,
            Username = "testadmin",
            PasswordHash = "$2a$11$TestHash2",
            FullName = "Test Admin",
            Email = "admin@test.com",
            Role = "admin",
            IsActive = true,
            CreatedAt = DateTime.UtcNow
        };

        context.Users.AddRange(user1, user2);

        // Seed Products
        var product1 = new Product
        {
            Id = 1,
            Code = "PROD001",
            Description = "Laptop Computer",
            CostPrice = 500.00m,
            SellPrice = 800.00m,
            WholesalePrice = 750.00m,
            SpecialPrice = 700.00m,
            QuantityInStock = 10.000m,
            MinStock = 2.000m,
            MaxStock = 50.000m,
            Unit = "Unit",
            Barcode = "1234567890123",
            Brand = "TechBrand",
            Model = "TB-2024",
            DepartmentId = 1,
            IsActive = true,
            CreatedAt = DateTime.UtcNow
        };

        var product2 = new Product
        {
            Id = 2,
            Code = "PROD002",
            Description = "Wireless Mouse",
            CostPrice = 10.00m,
            SellPrice = 20.00m,
            WholesalePrice = 18.00m,
            QuantityInStock = 50.000m,
            MinStock = 10.000m,
            MaxStock = 200.000m,
            Unit = "Unit",
            Barcode = "1234567890124",
            Brand = "TechBrand",
            Model = "WM-100",
            DepartmentId = 1,
            IsActive = true,
            CreatedAt = DateTime.UtcNow
        };

        var product3 = new Product
        {
            Id = 3,
            Code = "PROD003",
            Description = "Milk 1L",
            CostPrice = 1.50m,
            SellPrice = 2.50m,
            QuantityInStock = 5.000m, // Low stock
            MinStock = 20.000m,
            MaxStock = 100.000m,
            Unit = "Liter",
            Barcode = "9876543210123",
            DepartmentId = 2,
            IsActive = true,
            CreatedAt = DateTime.UtcNow
        };

        context.Products.AddRange(product1, product2, product3);

        // Seed Customers
        var customer1 = new Customer
        {
            Id = 1,
            Name = "John Doe",
            Phone = "555-1234",
            Email = "john.doe@email.com",
            Address = "123 Main St",
            CUIT = "20-12345678-9",
            IVACondition = "Responsable Inscripto",
            CreditLimit = 5000.00m,
            CreditBalance = 0.00m,
            IsActive = true,
            CreatedAt = DateTime.UtcNow
        };

        var customer2 = new Customer
        {
            Id = 2,
            Name = "Jane Smith",
            Phone = "555-5678",
            Email = "jane.smith@email.com",
            Address = "456 Oak Ave",
            CUIT = "27-98765432-1",
            IVACondition = "Monotributo",
            CreditLimit = 3000.00m,
            CreditBalance = 500.00m,
            IsActive = true,
            CreatedAt = DateTime.UtcNow
        };

        context.Customers.AddRange(customer1, customer2);

        // Seed Sales
        var sale1 = new Sale
        {
            Id = 1,
            Timestamp = DateTime.UtcNow.AddDays(-1),
            CustomerId = 1,
            UserId = 1,
            Status = "completed",
            CreatedAt = DateTime.UtcNow.AddDays(-1)
        };

        context.Sales.Add(sale1);

        // Seed Sale Items
        var saleItem1 = new SaleItem
        {
            Id = 1,
            SaleId = 1,
            ProductId = 1,
            ProductCode = "PROD001",
            ProductDescription = "Laptop Computer",
            ProductUnit = "Unit",
            Quantity = 1.000m,
            UnitPrice = 800.00m,
            CreatedAt = DateTime.UtcNow.AddDays(-1)
        };

        var saleItem2 = new SaleItem
        {
            Id = 2,
            SaleId = 1,
            ProductId = 2,
            ProductCode = "PROD002",
            ProductDescription = "Wireless Mouse",
            ProductUnit = "Unit",
            Quantity = 2.000m,
            UnitPrice = 20.00m,
            CreatedAt = DateTime.UtcNow.AddDays(-1)
        };

        context.SaleItems.AddRange(saleItem1, saleItem2);

        // Seed Inventory Movements
        var inventoryMovement1 = new InventoryMovement
        {
            Id = 1,
            ProductId = 1,
            Quantity = 10.000m,
            UnitCost = 500.00m,
            MovementType = "in",
            PreviousStock = 0.000m,
            NewStock = 10.000m,
            Reason = "Initial stock",
            Reference = "PO-001",
            UserId = 2,
            Timestamp = DateTime.UtcNow.AddDays(-7),
            CreatedAt = DateTime.UtcNow.AddDays(-7)
        };

        context.InventoryMovements.Add(inventoryMovement1);

        // Seed Cash Drawer Session
        var cashSession1 = new CashDrawerSession
        {
            Id = 1,
            UserId = 1,
            OpeningTime = DateTime.UtcNow.AddHours(-8),
            OpeningBalance = 100.00m,
            ClosingTime = DateTime.UtcNow.AddHours(-1),
            ClosingBalance = 940.00m,
            ExpectedBalance = 940.00m,
            Difference = 0.00m,
            Notes = "Normal shift",
            CreatedAt = DateTime.UtcNow.AddHours(-8)
        };

        context.CashDrawerSessions.Add(cashSession1);

        // Seed Cash Drawer Entries
        var cashEntry1 = new CashDrawerEntry
        {
            Id = 1,
            CashDrawerSessionId = 1,
            EntryType = "sale",
            Amount = 840.00m,
            Reason = "Sale #1",
            Reference = "SALE-001",
            UserId = 1,
            Timestamp = DateTime.UtcNow.AddHours(-2),
            CreatedAt = DateTime.UtcNow.AddHours(-2)
        };

        context.CashDrawerEntries.Add(cashEntry1);

        // Save all changes
        context.SaveChanges();
    }

    /// <summary>
    /// Clears all test data from the database.
    /// </summary>
    /// <param name="context">The database context to clear.</param>
    public static void ClearTestData(EleventaDbContext context)
    {
        context.CashDrawerEntries.RemoveRange(context.CashDrawerEntries);
        context.CashDrawerSessions.RemoveRange(context.CashDrawerSessions);
        context.InventoryMovements.RemoveRange(context.InventoryMovements);
        context.SaleItems.RemoveRange(context.SaleItems);
        context.Sales.RemoveRange(context.Sales);
        context.Customers.RemoveRange(context.Customers);
        context.Products.RemoveRange(context.Products);
        context.Users.RemoveRange(context.Users);
        context.Departments.RemoveRange(context.Departments);
        context.SaveChanges();
    }
}
