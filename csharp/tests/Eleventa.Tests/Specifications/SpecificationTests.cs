using Eleventa.Domain.Specifications;
using System.Linq.Expressions;
using Xunit;

namespace Eleventa.Tests.Specifications;

// Test entity for specification tests
public class TestProduct
{
    public string Name { get; set; } = string.Empty;
    public decimal Price { get; set; }
    public bool IsActive { get; set; }
    public string Category { get; set; } = string.Empty;
}

// Concrete specification implementations for testing
public class ActiveProductSpec : Specification<TestProduct>
{
    public override Expression<Func<TestProduct, bool>> ToExpression()
    {
        return p => p.IsActive;
    }
}

public class PriceAboveSpec : Specification<TestProduct>
{
    private readonly decimal _minPrice;

    public PriceAboveSpec(decimal minPrice)
    {
        _minPrice = minPrice;
    }

    public override Expression<Func<TestProduct, bool>> ToExpression()
    {
        return p => p.Price > _minPrice;
    }
}

public class CategorySpec : Specification<TestProduct>
{
    private readonly string _category;

    public CategorySpec(string category)
    {
        _category = category;
    }

    public override Expression<Func<TestProduct, bool>> ToExpression()
    {
        return p => p.Category == _category;
    }
}

public class SpecificationTests
{
    [Fact]
    public void IsSatisfiedBy_MatchingProduct_ReturnsTrue()
    {
        // Arrange
        var spec = new ActiveProductSpec();
        var product = new TestProduct { IsActive = true };

        // Act
        var result = spec.IsSatisfiedBy(product);

        // Assert
        Assert.True(result);
    }

    [Fact]
    public void IsSatisfiedBy_NonMatchingProduct_ReturnsFalse()
    {
        // Arrange
        var spec = new ActiveProductSpec();
        var product = new TestProduct { IsActive = false };

        // Act
        var result = spec.IsSatisfiedBy(product);

        // Assert
        Assert.False(result);
    }

    [Fact]
    public void And_BothSpecificationsSatisfied_ReturnsTrue()
    {
        // Arrange
        var activeSpec = new ActiveProductSpec();
        var priceSpec = new PriceAboveSpec(50);
        var combined = activeSpec.And(priceSpec);

        var product = new TestProduct { IsActive = true, Price = 100 };

        // Act
        var result = combined.IsSatisfiedBy(product);

        // Assert
        Assert.True(result);
    }

    [Fact]
    public void And_OnlyOneSpecificationSatisfied_ReturnsFalse()
    {
        // Arrange
        var activeSpec = new ActiveProductSpec();
        var priceSpec = new PriceAboveSpec(50);
        var combined = activeSpec.And(priceSpec);

        var product = new TestProduct { IsActive = true, Price = 30 };

        // Act
        var result = combined.IsSatisfiedBy(product);

        // Assert
        Assert.False(result);
    }

    [Fact]
    public void Or_OneSpecificationSatisfied_ReturnsTrue()
    {
        // Arrange
        var activeSpec = new ActiveProductSpec();
        var priceSpec = new PriceAboveSpec(50);
        var combined = activeSpec.Or(priceSpec);

        var product = new TestProduct { IsActive = false, Price = 100 };

        // Act
        var result = combined.IsSatisfiedBy(product);

        // Assert
        Assert.True(result);
    }

    [Fact]
    public void Or_NeitherSpecificationSatisfied_ReturnsFalse()
    {
        // Arrange
        var activeSpec = new ActiveProductSpec();
        var priceSpec = new PriceAboveSpec(50);
        var combined = activeSpec.Or(priceSpec);

        var product = new TestProduct { IsActive = false, Price = 30 };

        // Act
        var result = combined.IsSatisfiedBy(product);

        // Assert
        Assert.False(result);
    }

    [Fact]
    public void Not_SpecificationSatisfied_ReturnsFalse()
    {
        // Arrange
        var activeSpec = new ActiveProductSpec();
        var notActive = activeSpec.Not();

        var product = new TestProduct { IsActive = true };

        // Act
        var result = notActive.IsSatisfiedBy(product);

        // Assert
        Assert.False(result);
    }

    [Fact]
    public void Not_SpecificationNotSatisfied_ReturnsTrue()
    {
        // Arrange
        var activeSpec = new ActiveProductSpec();
        var notActive = activeSpec.Not();

        var product = new TestProduct { IsActive = false };

        // Act
        var result = notActive.IsSatisfiedBy(product);

        // Assert
        Assert.True(result);
    }

    [Fact]
    public void ToExpression_CanBeUsedInLinq()
    {
        // Arrange
        var spec = new ActiveProductSpec();
        var products = new[]
        {
            new TestProduct { Name = "A", IsActive = true },
            new TestProduct { Name = "B", IsActive = false },
            new TestProduct { Name = "C", IsActive = true }
        };

        // Act
        var filtered = products.AsQueryable().Where(spec.ToExpression()).ToList();

        // Assert
        Assert.Equal(2, filtered.Count);
        Assert.All(filtered, p => Assert.True(p.IsActive));
    }

    [Fact]
    public void ComplexSpecification_AndOrNotCombination_WorksCorrectly()
    {
        // Arrange
        // (Active AND (Price > 50 OR Category = "Electronics"))
        var activeSpec = new ActiveProductSpec();
        var priceSpec = new PriceAboveSpec(50);
        var categorySpec = new CategorySpec("Electronics");

        var combined = activeSpec.And(priceSpec.Or(categorySpec));

        var product1 = new TestProduct
        {
            IsActive = true,
            Price = 100,
            Category = "Books"
        };
        var product2 = new TestProduct
        {
            IsActive = true,
            Price = 30,
            Category = "Electronics"
        };
        var product3 = new TestProduct
        {
            IsActive = false,
            Price = 100,
            Category = "Electronics"
        };

        // Act & Assert
        Assert.True(combined.IsSatisfiedBy(product1)); // Active and expensive
        Assert.True(combined.IsSatisfiedBy(product2)); // Active and electronics
        Assert.False(combined.IsSatisfiedBy(product3)); // Not active
    }

    [Fact]
    public void ImplicitConversion_ToExpression_Works()
    {
        // Arrange
        var spec = new ActiveProductSpec();
        var products = new[]
        {
            new TestProduct { IsActive = true },
            new TestProduct { IsActive = false }
        };

        // Act - use implicit conversion
        Expression<Func<TestProduct, bool>> expression = spec;
        var filtered = products.AsQueryable().Where(expression).ToList();

        // Assert
        Assert.Single(filtered);
        Assert.True(filtered[0].IsActive);
    }
}
