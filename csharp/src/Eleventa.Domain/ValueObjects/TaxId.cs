using System.Text.RegularExpressions;

namespace Eleventa.Domain.ValueObjects;

/// <summary>
/// Represents a tax identification number (CUIT for Argentina).
/// Format: XX-XXXXXXXX-X (11 digits with check digit).
/// </summary>
public sealed class TaxId : ValueObject
{
    public string Value { get; }

    private TaxId(string value)
    {
        Value = value;
    }

    /// <summary>
    /// Creates a new TaxId instance.
    /// </summary>
    public static TaxId Create(string taxId)
    {
        if (string.IsNullOrWhiteSpace(taxId))
            throw new ValidationException("Tax ID is required", nameof(taxId));

        // Remove dashes and whitespace
        var digitsOnly = Regex.Replace(taxId.Trim(), @"[\s\-]", "");

        if (digitsOnly.Length != 11 || !Regex.IsMatch(digitsOnly, @"^\d{11}$"))
            throw new ValidationException(
                "Tax ID must be 11 digits",
                nameof(taxId));

        if (!ValidateCheckDigit(digitsOnly))
            throw new ValidationException(
                $"Invalid tax ID check digit: '{taxId}'",
                nameof(taxId));

        return new TaxId(digitsOnly);
    }

    /// <summary>
    /// Validates CUIT check digit using official algorithm.
    /// </summary>
    private static bool ValidateCheckDigit(string cuit)
    {
        if (cuit.Length != 11)
            return false;

        // CUIT validation multipliers
        int[] multipliers = { 5, 4, 3, 2, 7, 6, 5, 4, 3, 2 };

        // Calculate sum
        int total = 0;
        for (int i = 0; i < 10; i++)
        {
            total += (cuit[i] - '0') * multipliers[i];
        }

        // Calculate check digit
        int remainder = total % 11;
        int checkDigit = 11 - remainder;

        if (checkDigit == 11)
            checkDigit = 0;
        else if (checkDigit == 10)
            checkDigit = 9;

        // Compare with provided check digit
        return (cuit[10] - '0') == checkDigit;
    }

    /// <summary>
    /// Gets the tax ID as digits only.
    /// </summary>
    public string Digits => Value;

    /// <summary>
    /// Gets the type code (first 2 digits).
    /// Type codes: 20=male, 23=company, 27=female, etc.
    /// </summary>
    public string TypeCode => Value.Length >= 2 ? Value[..2] : string.Empty;

    /// <summary>
    /// Formats the tax ID with dashes.
    /// </summary>
    public string Format()
    {
        if (Value.Length != 11)
            return Value;

        return $"{Value[..2]}-{Value.Substring(2, 8)}-{Value[10]}";
    }

    protected override IEnumerable<object?> GetEqualityComponents()
    {
        yield return Value;
    }

    public override string ToString() => Format();

    public static implicit operator string(TaxId taxId) => taxId.Value;
}
