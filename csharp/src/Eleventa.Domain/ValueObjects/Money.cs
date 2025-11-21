namespace Eleventa.Domain.ValueObjects;

/// <summary>
/// Represents a monetary value with currency.
/// Immutable value object with arithmetic operations.
/// </summary>
public sealed class Money : ValueObject
{
    public decimal Amount { get; }
    public string Currency { get; }

    private Money(decimal amount, string currency)
    {
        Amount = amount;
        Currency = currency;
    }

    /// <summary>
    /// Creates a new Money instance.
    /// </summary>
    public static Money Create(decimal amount, string currency)
    {
        if (string.IsNullOrWhiteSpace(currency))
            throw new ValidationException("Currency is required", nameof(currency));

        if (currency.Length != 3)
            throw new ValidationException("Currency must be 3 characters (ISO 4217)", nameof(currency));

        return new Money(amount, currency.ToUpperInvariant());
    }

    /// <summary>
    /// Creates zero money in the specified currency.
    /// </summary>
    public static Money Zero(string currency) => Create(0, currency);

    /// <summary>
    /// Adds two money values.
    /// </summary>
    public Money Add(Money other)
    {
        AssertSameCurrency(other);
        return new Money(Amount + other.Amount, Currency);
    }

    /// <summary>
    /// Subtracts another money value.
    /// </summary>
    public Money Subtract(Money other)
    {
        AssertSameCurrency(other);
        return new Money(Amount - other.Amount, Currency);
    }

    /// <summary>
    /// Multiplies by a scalar value.
    /// </summary>
    public Money Multiply(decimal multiplier)
    {
        return new Money(Amount * multiplier, Currency);
    }

    /// <summary>
    /// Divides by a scalar value.
    /// </summary>
    public Money Divide(decimal divisor)
    {
        if (divisor == 0)
            throw new DivideByZeroException("Cannot divide money by zero");

        return new Money(Amount / divisor, Currency);
    }

    /// <summary>
    /// Rounds to specified decimal places.
    /// </summary>
    public Money Round(int decimals = 2)
    {
        return new Money(Math.Round(Amount, decimals), Currency);
    }

    /// <summary>
    /// Allocates money according to ratios without losing cents to rounding.
    /// </summary>
    public IReadOnlyList<Money> Allocate(params decimal[] ratios)
    {
        if (ratios.Length == 0)
            throw new ArgumentException("At least one ratio required", nameof(ratios));

        decimal totalRatio = ratios.Sum();
        if (totalRatio == 0)
            throw new ArgumentException("Sum of ratios must be greater than zero", nameof(ratios));

        var results = new List<Money>();
        decimal allocatedSoFar = 0;

        for (int i = 0; i < ratios.Length; i++)
        {
            decimal share;
            if (i == ratios.Length - 1)
            {
                // Last allocation gets the remainder to avoid rounding errors
                share = Amount - allocatedSoFar;
            }
            else
            {
                share = Math.Floor((Amount * ratios[i] / totalRatio) * 100) / 100;
                allocatedSoFar += share;
            }

            results.Add(new Money(share, Currency));
        }

        return results;
    }

    /// <summary>
    /// Checks if the amount is zero.
    /// </summary>
    public bool IsZero() => Amount == 0;

    /// <summary>
    /// Checks if the amount is positive.
    /// </summary>
    public bool IsPositive() => Amount > 0;

    /// <summary>
    /// Checks if the amount is negative.
    /// </summary>
    public bool IsNegative() => Amount < 0;

    /// <summary>
    /// Returns the absolute value.
    /// </summary>
    public Money Abs() => new Money(Math.Abs(Amount), Currency);

    /// <summary>
    /// Negates the amount.
    /// </summary>
    public Money Negate() => new Money(-Amount, Currency);

    private void AssertSameCurrency(Money other)
    {
        if (Currency != other.Currency)
            throw new InvalidOperationException(
                $"Cannot operate on different currencies: {Currency} and {other.Currency}");
    }

    // Operators
    public static Money operator +(Money left, Money right) => left.Add(right);
    public static Money operator -(Money left, Money right) => left.Subtract(right);
    public static Money operator *(Money money, decimal multiplier) => money.Multiply(multiplier);
    public static Money operator /(Money money, decimal divisor) => money.Divide(divisor);
    public static Money operator -(Money money) => money.Negate();

    // Comparison operators
    public static bool operator >(Money left, Money right)
    {
        left.AssertSameCurrency(right);
        return left.Amount > right.Amount;
    }

    public static bool operator <(Money left, Money right)
    {
        left.AssertSameCurrency(right);
        return left.Amount < right.Amount;
    }

    public static bool operator >=(Money left, Money right)
    {
        left.AssertSameCurrency(right);
        return left.Amount >= right.Amount;
    }

    public static bool operator <=(Money left, Money right)
    {
        left.AssertSameCurrency(right);
        return left.Amount <= right.Amount;
    }

    protected override IEnumerable<object?> GetEqualityComponents()
    {
        yield return Amount;
        yield return Currency;
    }

    public override string ToString() => $"{Amount:F2} {Currency}";
}
