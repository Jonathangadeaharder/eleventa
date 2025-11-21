using System.Text.RegularExpressions;

namespace Eleventa.Domain.ValueObjects;

/// <summary>
/// Represents a product code (SKU, barcode, etc.).
/// </summary>
public sealed class ProductCode : ValueObject
{
    private static readonly Regex CodePattern = new(
        @"^[A-Z0-9\-]+$",
        RegexOptions.Compiled);

    public string Value { get; }

    private ProductCode(string value)
    {
        Value = value;
    }

    /// <summary>
    /// Creates a new ProductCode instance.
    /// </summary>
    public static ProductCode Create(string code)
    {
        if (string.IsNullOrWhiteSpace(code))
            throw new ValidationException("Product code is required", nameof(code));

        // Normalize to uppercase and trim
        code = code.Trim().ToUpperInvariant();

        if (!CodePattern.IsMatch(code))
            throw new ValidationException(
                "Product code can only contain letters, numbers, and hyphens",
                nameof(code));

        if (code.Length > 50)
            throw new ValidationException("Product code too long (max 50 characters)", nameof(code));

        return new ProductCode(code);
    }

    /// <summary>
    /// Gets the prefix (part before first hyphen).
    /// </summary>
    public string? Prefix
    {
        get
        {
            var index = Value.IndexOf('-');
            return index >= 0 ? Value[..index] : null;
        }
    }

    /// <summary>
    /// Gets the suffix (part after last hyphen).
    /// </summary>
    public string? Suffix
    {
        get
        {
            var index = Value.LastIndexOf('-');
            return index >= 0 ? Value[(index + 1)..] : null;
        }
    }

    /// <summary>
    /// Checks if code has the specified prefix.
    /// </summary>
    public bool HasPrefix(string prefix)
    {
        return Value.StartsWith(prefix, StringComparison.OrdinalIgnoreCase);
    }

    /// <summary>
    /// Generates a SKU from category and sequence number.
    /// </summary>
    public static ProductCode GenerateSku(string category, int sequenceNumber)
    {
        if (string.IsNullOrWhiteSpace(category))
            throw new ArgumentException("Category is required", nameof(category));

        if (sequenceNumber < 0)
            throw new ArgumentException("Sequence number must be non-negative", nameof(sequenceNumber));

        var code = $"{category.ToUpperInvariant()}-{sequenceNumber:D6}";
        return Create(code);
    }

    protected override IEnumerable<object?> GetEqualityComponents()
    {
        yield return Value;
    }

    public override string ToString() => Value;

    public static implicit operator string(ProductCode code) => code.Value;
}
