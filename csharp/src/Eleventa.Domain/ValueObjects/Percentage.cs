namespace Eleventa.Domain.ValueObjects;

/// <summary>
/// Represents a percentage value (0-100).
/// Provides percentage calculations and operations.
/// </summary>
public sealed class Percentage : ValueObject
{
    public decimal Value { get; }

    private Percentage(decimal value)
    {
        Value = value;
    }

    /// <summary>
    /// Creates a new Percentage instance.
    /// </summary>
    public static Percentage Create(decimal value)
    {
        if (value < 0)
            throw new ValidationException("Percentage cannot be negative", nameof(value));

        if (value > 100)
            throw new ValidationException("Percentage cannot exceed 100", nameof(value));

        return new Percentage(value);
    }

    /// <summary>
    /// Creates a percentage from a decimal (0.0-1.0).
    /// </summary>
    public static Percentage FromDecimal(decimal decimalValue)
    {
        return Create(decimalValue * 100);
    }

    /// <summary>
    /// Creates a percentage from a ratio (e.g., 1/4 = 25%).
    /// </summary>
    public static Percentage FromRatio(decimal numerator, decimal denominator)
    {
        if (denominator == 0)
            throw new DivideByZeroException("Denominator cannot be zero");

        return FromDecimal(numerator / denominator);
    }

    /// <summary>
    /// Converts to decimal representation (0.0-1.0).
    /// </summary>
    public decimal AsDecimal() => Value / 100;

    /// <summary>
    /// Calculates percentage of an amount.
    /// </summary>
    public decimal Of(decimal amount) => amount * AsDecimal();

    /// <summary>
    /// Adds percentage to an amount.
    /// </summary>
    public decimal AddTo(decimal amount) => amount + Of(amount);

    /// <summary>
    /// Subtracts percentage from an amount.
    /// </summary>
    public decimal SubtractFrom(decimal amount) => amount - Of(amount);

    /// <summary>
    /// Adds two percentages.
    /// </summary>
    public Percentage Add(Percentage other)
    {
        return Create(Value + other.Value);
    }

    /// <summary>
    /// Multiplies by a scalar.
    /// </summary>
    public Percentage Multiply(decimal multiplier)
    {
        return Create(Value * multiplier);
    }

    /// <summary>
    /// Checks if percentage is zero.
    /// </summary>
    public bool IsZero() => Value == 0;

    /// <summary>
    /// Checks if percentage is 100%.
    /// </summary>
    public bool IsFull() => Value == 100;

    public static Percentage Zero => new(0);
    public static Percentage Full => new(100);

    // Operators
    public static Percentage operator +(Percentage left, Percentage right) => left.Add(right);
    public static Percentage operator *(Percentage percentage, decimal multiplier) => percentage.Multiply(multiplier);

    protected override IEnumerable<object?> GetEqualityComponents()
    {
        yield return Value;
    }

    public override string ToString() => $"{Value:F2}%";
}
